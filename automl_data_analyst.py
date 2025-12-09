import streamlit as st
import pandas as pd
import numpy as np
import io
import warnings
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import joblib # Usado para paralelismo em Optuna e ML
import time

# --- Scikit-learn, Modelos e Pipelines
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    mean_squared_error, r2_score, accuracy_score,
    classification_report, confusion_matrix, log_loss
)
import xgboost as xgb
import shap
import category_encoders as ce
import optuna
from optuna.integration.sklearn import OptunaSearchCV # Usado para otimização robusta. Revertido para o caminho completo para estabilidade.

# --- Dask para Paralelismo/Escalabilidade
import dask.dataframe as dd
from dask.distributed import Client, LocalCluster

warnings.filterwarnings('ignore')

# ============================================================
# 1. CONFIGURAÇÃO INICIAL E ESTADO DA SESSÃO
# ============================================================

st.set_page_config(layout="wide", page_title="AutoML & DataOps Analyst")

# Inicialização de variáveis de estado
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
if 'df_master' not in st.session_state:
    st.session_state.df_master = None
if 'df_master_name' not in st.session_state:
    st.session_state.df_master_name = None
if 'last_trained_model' not in st.session_state:
    st.session_state.last_trained_model = None
if 'last_trained_X' not in st.session_state:
    st.session_state.last_trained_X = None

# Variáveis de Configuração de IA (INCLUÍDAS AGORA)
# A chave de API deve ser inserida nesta variável global para que o Chatbot funcione.
GEMINI_API_KEY = "" # COLOQUE SUA CHAVE AQUI
GEMINI_MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
# Fim das Variáveis de Configuração de IA

# Mapeamento de Modelos
MODEL_MAPPING = {
    'Regressão Linear': LinearRegression,
    'Random Forest Regressor': RandomForestRegressor,
    'XGBoost Regressor': xgb.XGBRegressor,
    'Regressão Logística': LogisticRegression,
    'Random Forest Classifier': RandomForestClassifier,
    'XGBoost Classifier': xgb.XGBClassifier,
    'Isolation Forest (Anomalia)': IsolationForest,
}

# Configuração do Cluster Dask (Executa o cluster localmente)
@st.cache_resource
def setup_dask_cluster():
    try:
        cluster = LocalCluster(n_workers=4, threads_per_worker=1)
        client = Client(cluster)
        st.success(f"Cluster Dask iniciado: {client.dashboard_link}")
        return client
    except Exception as e:
        st.error(f"Erro ao iniciar Dask Cluster: {e}")
        return None

dask_client = setup_dask_cluster()
if dask_client:
    st.sidebar.markdown(f"**Dask Status:** [Dashboard]({dask_client.dashboard_link})")


# ============================================================
# 2. COMPONENTES REUTILIZÁVEIS (KUBEFLOW CONCEPTUAL)
# ============================================================

def get_preprocessor(df, features, target):
    """
    [Kubeflow Component: Preprocessor]
    Define o ColumnTransformer para pré-processamento.
    """
    df_temp = df[features + [target]].select_dtypes(include=['number', 'object']).copy()
    
    numerical_features = df_temp.select_dtypes(include=['number']).columns.tolist()
    categorical_features = df_temp.select_dtypes(include=['object']).columns.tolist()
    
    # Remove o alvo se for numérico e estiver nas features (só deve ocorrer se houver erro de seleção)
    if target in numerical_features:
        numerical_features.remove(target)

    # 1. Pipeline para dados Numéricos: Imputação Média -> Escala
    numerical_pipeline = Pipeline([
        ('scaler', StandardScaler())
    ])

    # 2. Pipeline para dados Categóricos: Imputação Mais Frequente -> One-Hot (ou Target/Ordinal)
    # TargetEncoder é preferido para alta cardinalidade em Regressão/Classificação (exceto para dados sensíveis)
    categorical_pipeline = Pipeline([
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    # Combina as transformações
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_pipeline, numerical_features),
            ('cat', categorical_pipeline, categorical_features)
        ],
        remainder='passthrough' # Mantém outras colunas (como datas ou IDs que não foram filtradas)
    )
    return preprocessor, numerical_features, categorical_features


def get_model_pipeline(model_key, preprocessor):
    """
    [Kubeflow Component: Model Pipeline Creator]
    Cria a Pipeline final para treinamento.
    """
    model_class = MODEL_MAPPING.get(model_key)
    
    if 'XGBoost' in model_key:
        model = model_class(n_estimators=100, random_state=42, n_jobs=-1, tree_method='hist')
    else:
        model = model_class(random_state=42)
    
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('model', model)])
    return pipeline


# ============================================================
# 3. FUNÇÕES DE CARREGAMENTO E ETL (COM DASK)
# ============================================================

def load_data(uploaded_file):
    """Carrega dados e infere tipos."""
    filename = uploaded_file.name
    content = uploaded_file.getvalue()
    df_key = filename.split('.')[0]
    
    if filename.endswith('.csv'):
        # Exemplo de uso de Dask para paralelismo na leitura de grandes arquivos
        ddf = dd.read_csv(io.BytesIO(content), assume_missing=True, encoding='latin-1')
        df_temp = ddf.compute() # Coleta o Dask DataFrame para Pandas DF
    elif filename.endswith(('.xlsx', '.xls')):
        df_temp = pd.read_excel(io.BytesIO(content))
    else:
        st.error(f"Formato não suportado: {filename}")
        return None
        
    # Engenharia de Atributos - Detecção de Datas
    for col in df_temp.columns:
        if df_temp[col].dtype == 'object' and df_temp[col].astype(str).str.contains(r'^\d{4}[-/]\d{2}[-/]\d{2}').any():
            df_temp[col] = pd.to_datetime(df_temp[col], errors='coerce')
    
    st.session_state.dataframes[df_key] = df_temp
    st.session_state.df_master = df_temp.copy()
    st.session_state.df_master_name = df_key
    st.success(f"Arquivo carregado como DF Mestre: {df_key} (Shape: {df_temp.shape})")
    
    # Análise de Tipo
    st.subheader("Sugestões de Análise Rápida:")
    suggestions = []
    if any(df_temp[col].dtype == 'datetime64[ns]' for col in df_temp.columns):
        suggestions.append("Série Temporal detectada. Use gráficos de Linhas e Análise de Recência (RFM).")
    if any(col.lower() in ['customer_id', 'client_id', 'cliente'] for col in df_temp.columns):
        suggestions.append("IDs de Clientes detectados. A Análise RFM e Clusterização são ideais.")
    if suggestions:
        st.info(" - " + "\n - ".join(suggestions))
    
    st.dataframe(df_temp.head())


# ============================================================
# 4. FUNÇÃO DE OTIMIZAÇÃO DE HIPERPARÂMETROS (AUTOML) - OPTUNA REAL
# ============================================================

def run_optuna_automl(df_master, y_col, x_cols, model_key, n_trials=20):
    """
    [Kubeflow Component: Hyperparameter Optimization]
    Executa a otimização de hiperparâmetros usando Optuna.
    """
    if df_master is None or not y_col or not x_cols:
        st.error("Dados ou features incompletas para AutoML.")
        return

    st.info("Iniciando AutoML com Optuna. O pré-processamento e otimização serão integrados na Pipeline.")
    
    df_ml = df_master[[y_col] + x_cols].copy().dropna()
    if df_ml.empty:
        st.error("DataFrame vazio após a remoção de NaNs.")
        return

    X = df_ml[x_cols]
    Y = df_ml[y_col]
    
    is_regression = any(t in model_key for t in ['Regressor', 'Linear'])
    
    # 1. Define o Preprocessor (Baseado no DF_ML filtrado)
    preprocessor, num_features, cat_features = get_preprocessor(df_ml, x_cols, y_col)
    
    # 2. Define o Espaço de Busca e a Pipeline Base
    
    # Ajusta o modelo base para a Pipeline
    model_class = MODEL_MAPPING.get(model_key)
    base_model = model_class(random_state=42, n_jobs=-1)

    # Define o Espaço de Busca de Hiperparâmetros (apenas para modelos complexos)
    search_space = {}
    if 'Random Forest' in model_key:
        search_space = {
            'model__n_estimators': optuna.distributions.IntDistribution(50, 200, step=50),
            'model__max_depth': optuna.distributions.IntDistribution(5, 15, step=5),
            'model__min_samples_split': optuna.distributions.FloatDistribution(0.01, 0.1, step=0.03),
        }
    elif 'XGBoost' in model_key:
        search_space = {
            'model__n_estimators': optuna.distributions.IntDistribution(50, 200, step=50),
            'model__max_depth': optuna.distributions.IntDistribution(3, 10, step=2),
            'model__learning_rate': optuna.distributions.FloatDistribution(0.01, 0.1, log=True),
            'model__subsample': optuna.distributions.FloatDistribution(0.5, 1.0, step=0.1),
        }
    else:
        st.warning(f"Otimização Optuna não implementada para o modelo '{model_key}'. Retornando modelo padrão.")
        # Retorna o modelo padrão treinado (para evitar erro e permitir seguir no Streamlit)
        try:
            return get_model_pipeline(model_key, preprocessor).fit(X, Y)
        except Exception as e:
            st.error(f"Erro ao treinar modelo padrão: {e}")
            return None

    # 3. Cria a Pipeline com o Modelo e o Preprocessor
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('model', base_model)])

    # 4. Executa a Otimização com OptunaSearchCV
    
    # Métrica de Otimização
    scoring_metric = 'neg_mean_squared_error' if is_regression else 'accuracy'
    
    # Usa OptunaSearchCV para otimização com CV
    try:
        with st.spinner(f"Executando {n_trials} trials de Optuna... (Pode demorar)"):
            optuna_search = OptunaSearchCV(
                estimator=pipeline,
                param_distributions=search_space,
                n_trials=n_trials,
                cv=3,  # Cross-Validation de 3-folds
                scoring=scoring_metric,
                random_state=42,
                n_jobs=-1, # Usa todos os cores disponíveis (paralelismo Joblib)
                verbose=0
            )
            
            start_time = time.time()
            optuna_search.fit(X, Y)
            end_time = time.time()

        st.success(f"AutoML concluído em {end_time - start_time:.2f} segundos!")
        st.subheader("Resultados da Otimização Optuna:")
        st.write(f"Melhor Métrica ({scoring_metric}): {optuna_search.best_score_:.4f}")
        st.write("Melhores Hiperparâmetros:")
        st.json(optuna_search.best_params_)
        
        # O modelo treinado final é o best_estimator_
        best_model = optuna_search.best_estimator_
        
        # Plota Histórico de Otimização (Plotly)
        fig_history = px.line(
            x=list(range(len(optuna_search.trials_))),
            y=[t.value for t in optuna_search.trials_],
            labels={'x': 'Trial', 'y': 'Métrica de Score'},
            title="Histórico de Otimização Optuna (Trials)"
        )
        st.plotly_chart(fig_history, use_container_width=True)

        return best_model

    except Exception as e:
        st.error(f"Erro no Optuna AutoML: {e}")
        return None

# ============================================================
# 5. LAYOUT E FUNÇÕES DE TELA (STREAMLIT)
# ============================================================

st.sidebar.title("Configurações do Data Analyst")
st.title("Plataforma Integrada de AutoML & DataOps")

# --- 5.1. Setup & Join (ETL)
with st.expander("1. Setup, Carregamento e ETL (Extract, Transform, Load)"):
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.subheader("Carregamento de Dados")
        uploaded_file = st.file_uploader("Selecione Arquivos (.csv, .xlsx)", type=['csv', 'xlsx'], accept_multiple_files=False)
        if uploaded_file and uploaded_file.name not in st.session_state.dataframes:
            load_data(uploaded_file)
        
        df_options = list(st.session_state.dataframes.keys())
        selected_df = st.selectbox("DF Principal (Mestre):", [''] + df_options, key='master_df_select')
        
        if selected_df and selected_df in st.session_state.dataframes:
            st.session_state.df_master = st.session_state.dataframes[selected_df].copy()
            st.session_state.df_master_name = selected_df
        
        if st.session_state.df_master is not None:
             st.info(f"DF Mestre: **{st.session_state.df_master_name}** | Shape: {st.session_state.df_master.shape}")

    if st.session_state.df_master is not None:
        
        all_cols = st.session_state.df_master.columns.tolist()
        
        with col2:
            st.subheader("Renomeação e Conversão")
            
            col_to_rename = st.selectbox("Coluna Atual:", all_cols, key='rename_old')
            new_name = st.text_input("Novo Nome:", key='rename_new')
            if st.button("Renomear Coluna", key='btn_rename'):
                if col_to_rename and new_name:
                    try:
                        st.session_state.df_master.rename(columns={col_to_rename: new_name}, inplace=True)
                        st.success(f"Coluna '{col_to_rename}' renomeada para '{new_name}'.")
                    except Exception as e:
                        st.error(f"Erro: {e}")

            col_to_convert = st.selectbox("Coluna para Conversão:", all_cols, key='convert_col')
            new_type = st.selectbox("Novo Tipo:", ['object', 'int64', 'float64', 'datetime64'], key='convert_type')
            if st.button("Converter Tipo", key='btn_convert'):
                if col_to_convert and new_type:
                    try:
                        if new_type == 'datetime64':
                             st.session_state.df_master[col_to_convert] = pd.to_datetime(st.session_state.df_master[col_to_convert], errors='coerce')
                        else:
                            st.session_state.df_master[col_to_convert] = st.session_state.df_master[col_to_convert].astype(new_type)
                        st.success(f"Coluna '{col_to_convert}' convertida para {new_type}.")
                    except Exception as e:
                        st.error(f"Erro ao converter: {e}")
        
        with col3:
            st.subheader("Junção (Merge)")
            df_target = st.selectbox("DF Alvo para Join:", [''] + df_options, key='join_target')
            join_type = st.radio("Tipo de Join:", ['left', 'right', 'inner', 'outer'], key='join_type', horizontal=True)
            
            if df_target and df_target in st.session_state.dataframes:
                df_t_cols = st.session_state.dataframes[df_target].columns.tolist()
                key_master = st.selectbox("Chave Mestre:", all_cols, key='key_master')
                key_target = st.selectbox("Chave Alvo:", df_t_cols, key='key_target')
                
                if st.button("Aplicar Join", key='btn_join'):
                    try:
                        df_t = st.session_state.dataframes[df_target]
                        st.session_state.df_master = pd.merge(
                            st.session_state.df_master, df_t,
                            left_on=key_master, right_on=key_target,
                            how=join_type, suffixes=('', '_joined')
                        )
                        st.success(f"Join aplicado. Novo Shape: {st.session_state.df_master.shape}")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erro no Join: {e}")

# --- 5.2. Tipos & Limpeza (Qualidade)
with st.expander("2. Limpeza de Dados e Qualidade"):
    if st.session_state.df_master is not None:
        
        st.subheader("1. Limpeza de Nulos e Duplicados")
        
        col_clean = st.selectbox("Coluna Alvo para Limpeza:", ['(Todas)'] + all_cols, key='clean_col')
        method_clean = st.radio("Método de Limpeza:", ['Excluir Linhas Nulas (dropna)', 'Preencher Nulos (fillna)'], key='clean_method', horizontal=True)
        fillna_value = st.text_input("Valor de preenchimento (se fillna):", key='fillna_val', disabled=(method_clean != 'Preencher Nulos (fillna)'))
        remove_duplicates = st.checkbox("Remover Duplicados", key='remove_duplicates')
        
        if st.button("Aplicar Limpeza de Dados", key='btn_clean'):
            df = st.session_state.df_master
            initial_shape = df.shape[0]
            
            if remove_duplicates:
                df.drop_duplicates(inplace=True)
                st.info(f"Duplicados removidos. Linhas: {initial_shape} -> {df.shape[0]}")
                initial_shape = df.shape[0]
                
            if method_clean == 'Excluir Linhas Nulas (dropna)':
                df.dropna(subset=[col_clean] if col_clean != '(Todas)' else None, inplace=True)
                st.success(f"Nulos excluídos. Linhas: {initial_shape} -> {df.shape[0]}")
            
            elif method_clean == 'Preencher Nulos (fillna)' and fillna_value:
                try:
                    val = float(fillna_value) if '.' in fillna_value else int(fillna_value)
                except ValueError:
                    val = fillna_value
                
                if col_clean == '(Todas)':
                    df.fillna(val, inplace=True)
                else:
                    df[col_clean].fillna(val, inplace=True)
                st.success(f"Nulos preenchidos com '{val}'.")
            
            st.subheader("Resumo de Nulos Pós-Limpeza")
            st.dataframe(df.isnull().sum().to_frame('Nulos'))

        st.subheader("2. Uso de Dask (Paralelismo)")
        if st.button("Executar Análise de Tipos com Dask (Paralelismo)", key='btn_dask_info'):
            st.info("Usando Dask para processar em paralelo a análise de tipos (Simulação de grandes dados).")
            ddf = dd.from_pandas(st.session_state.df_master, npartitions=4)
            start_time = time.time()
            # Esta operação é leve, mas demonstra o fluxo Dask
            result = ddf.dtypes.compute()
            st.success(f"Análise de Dask Concluída em {time.time() - start_time:.4f}s.")
            st.dataframe(result.to_frame('Dask DTypes'))

# --- 5.3. Gráficos & Visualização (Plotly)
with st.expander("3. Gráficos Interativos (Plotly Express)"):
    if st.session_state.df_master is not None:
        
        df = st.session_state.df_master
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = df.select_dtypes(include='object').columns.tolist()
        
        plot_type = st.selectbox("Tipo de Gráfico:", 
            ['Histograma', 'Barras', 'Linhas (Série Temporal)', 'Scatter (Dispersão)', 'Box Plot', 'Pair Plot'], 
            key='plot_type_select'
        )
        
        col_x = st.selectbox("Eixo X:", all_cols, key='plot_x')
        col_y = st.selectbox("Eixo Y (Opcional):", ['(Nenhum)'] + all_cols, key='plot_y')
        
        if st.button("Gerar Gráfico Interativo", key='btn_plot'):
            try:
                if plot_type == 'Histograma':
                    fig = px.histogram(df, x=col_x, title=f'Distribuição de {col_x}', marginal="box")
                elif plot_type == 'Barras':
                    if col_y != '(Nenhum)':
                         fig = px.bar(df.groupby(col_x)[col_y].sum().reset_index(), x=col_x, y=col_y, title=f'Soma de {col_y} por {col_x}')
                    else:
                        fig = px.bar(df[col_x].value_counts().reset_index(), x=df[col_x].value_counts().index.tolist(), y=df[col_x].value_counts().values, title=f'Contagem de {col_x}', labels={'x': col_x, 'y': 'Contagem'})
                elif plot_type == 'Linhas (Série Temporal)':
                    if col_y == '(Nenhum)':
                        st.error("Selecione um Eixo Y para Linhas.")
                        fig = go.Figure()
                    else:
                        fig = px.line(df, x=col_x, y=col_y, title=f'{col_y} ao longo de {col_x}')
                elif plot_type == 'Scatter (Dispersão)':
                    if col_y == '(Nenhum)':
                        st.error("Selecione um Eixo Y para Scatter.")
                        fig = go.Figure()
                    else:
                        fig = px.scatter(df, x=col_x, y=col_y, title=f'Dispersão de {col_x} vs {col_y}', trendline="ols")
                elif plot_type == 'Box Plot':
                    fig = px.box(df, x=col_x, y=col_y if col_y != '(Nenhum)' else None, title=f'Box Plot de {col_y or col_x}')
                elif plot_type == 'Pair Plot':
                    # Pair plot em Plotly é mais complexo, usando Scatter Matrix para fins de demonstração
                    st.info("Gerando Scatter Matrix (Similar a Pair Plot, limitado a 5 colunas).")
                    cols_to_plot = num_cols[:5]
                    fig = go.Figure(data=go.Splom(
                        dimensions=[dict(label=col, values=df[col]) for col in cols_to_plot],
                        text=df.index,
                        marker=dict(size=3)
                    ))
                    fig.update_layout(title='Scatter Matrix (Pair Plot Simples)')
                
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar gráfico: {e}")

# --- 5.4. Estatísticas & Qualidade
with st.expander("4. Estatísticas e Qualidade Avançada (Estatística e Pivot)"):
    if st.session_state.df_master is not None:
        
        df = st.session_state.df_master
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = df.select_dtypes(include='object').columns.tolist()

        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Tabela Dinâmica (Pivot)")
            idx = st.selectbox("Index:", ['(Nenhum)'] + cat_cols, key='pivot_index')
            val = st.selectbox("Values:", num_cols, key='pivot_values')
            agg = st.selectbox("Agregação:", ['sum', 'mean', 'count'], key='pivot_agg')
            
            if st.button("Gerar Pivot", key='btn_pivot'):
                if val:
                    pivot = pd.pivot_table(df, index=idx if idx != '(Nenhum)' else None, 
                                           values=val, aggfunc=agg)
                    st.dataframe(pivot)
        
        with col2:
            st.subheader("Testes Estatísticos")
            col_ttest = st.selectbox("Variável Numérica (T-Test):", num_cols, key='stat_ttest')
            col_anova_val = st.selectbox("Variável Valor (ANOVA):", num_cols, key='stat_anova_val')
            col_anova_group = st.selectbox("Variável Grupo (ANOVA):", cat_cols, key='stat_anova_group')
            
            if st.button("Executar Testes (T-Test, ANOVA)", key='btn_stats'):
                
                # T-Test
                data = df[col_ttest].dropna()
                if len(data) > 1:
                    t_stat, p_value = stats.ttest_1samp(data, 0)
                    st.markdown(f"**T-Test ({col_ttest} vs Média=0):**")
                    st.text(f"T-Stat: {t_stat:.4f}, P-Value: {p_value:.4f}")
                    st.info(f"Conclusão: {'Rejeitar H0 (Média != 0)' if p_value < 0.05 else 'Não Rejeitar H0 (Média = 0)'}")
                
                # ANOVA
                groups = [df[df[col_anova_group] == g][col_anova_val].dropna() for g in df[col_anova_group].unique()]
                groups = [g for g in groups if len(g) > 1]
                if len(groups) >= 2:
                    f_stat, p_value_anova = stats.f_oneway(*groups)
                    st.markdown(f"**ANOVA ({col_anova_val} por {col_anova_group}):**")
                    st.text(f"F-Stat: {f_stat:.4f}, P-Value: {p_value_anova:.4f}")
                    st.info(f"Conclusão: {'Rejeitar H0 (Média dos grupos é diferente)' if p_value_anova < 0.05 else 'Não Rejeitar H0 (Média dos grupos é igual)'}")
                else:
                    st.warning("Dados insuficientes para ANOVA.")

        with col3:
            st.subheader("Correlação e Outliers")
            
            if st.button("Mapa de Calor de Correlação (Heatmap)", key='btn_corr'):
                df_numeric = df[num_cols].dropna()
                if not df_numeric.empty:
                    corr_matrix = df_numeric.corr()
                    fig = px.imshow(corr_matrix, text_auto=True, aspect="auto", 
                                    color_continuous_scale='RdBu_r', 
                                    title='Mapa de Calor de Correlação')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Não há colunas numéricas sem nulos suficientes para correlação.")

            outlier_col = st.selectbox("Detecção de Outliers:", num_cols, key='outlier_col')
            if st.button("Detectar Outliers (IQR)", key='btn_outlier'):
                 data = df[outlier_col].dropna()
                 Q1 = data.quantile(0.25)
                 Q3 = data.quantile(0.75)
                 IQR = Q3 - Q1
                 lower_bound = Q1 - 1.5 * IQR
                 upper_bound = Q3 + 1.5 * IQR
                 outliers = data[(data < lower_bound) | (data > upper_bound)]
                 st.info(f"Total de Outliers IQR em '{outlier_col}': {len(outliers)}")
                 if not outliers.empty:
                     st.text("Amostra:")
                     st.dataframe(outliers.head())

# --- 5.5. Análise de Mercado & Financeira (ABC/RFM)
with st.expander("5. Análise de Mercado e Financeira (ABC/RFM)"):
    if st.session_state.df_master is not None:
        
        df = st.session_state.df_master
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = df.select_dtypes(include='object').columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Análise ABC (Priorização)")
            abc_item = st.selectbox("Item (Categoria):", cat_cols, key='abc_item')
            abc_value = st.selectbox("Valor (Receita):", num_cols, key='abc_value')
            
            if st.button("Gerar Análise ABC", key='btn_abc'):
                df_abc = df.groupby(abc_item)[abc_value].sum().reset_index()
                df_abc.sort_values(by=abc_value, ascending=False, inplace=True)
                total_value = df_abc[abc_value].sum()
                df_abc['% Acumulada'] = (df_abc[abc_value].cumsum() / total_value)
                
                def classify_abc(percent):
                    if percent <= 0.8: return 'A'
                    elif percent <= 0.95: return 'B'
                    else: return 'C'
                
                df_abc['Classe ABC'] = df_abc['% Acumulada'].apply(classify_abc)
                st.dataframe(df_abc.head(10))
                
                fig = px.bar(df_abc.head(10), x=abc_item, y=abc_value, color='Classe ABC',
                             title='Top 10 Itens por Valor com Classificação ABC')
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Análise RFM (Segmentação de Clientes)")
            rfm_customer = st.selectbox("ID Cliente:", cat_cols, key='rfm_cust')
            rfm_date = st.selectbox("Data Transação (Datetime):", date_cols, key='rfm_date')
            rfm_monetary = st.selectbox("Valor Monetário:", num_cols, key='rfm_monetary')
            
            if st.button("Gerar Análise RFM", key='btn_rfm'):
                if not rfm_date: st.error("A coluna de data deve ser do tipo datetime64.")
                else:
                    df_rfm = df.dropna(subset=[rfm_customer, rfm_date, rfm_monetary]).copy()
                    today = df_rfm[rfm_date].max() + pd.Timedelta(days=1)
                    
                    rfm_table = df_rfm.groupby(rfm_customer).agg(
                        Recency=(rfm_date, lambda x: (today - x.max()).days),
                        Frequency=(rfm_date, 'count'),
                        Monetary=(rfm_monetary, 'sum')
                    ).reset_index()
                    
                    # Segmentação por Quartil (3x3x3)
                    rfm_table['R_Score'] = pd.qcut(rfm_table['Recency'], 3, labels=[3, 2, 1], duplicates='drop').astype(str)
                    rfm_table['F_Score'] = pd.qcut(rfm_table['Frequency'], 3, labels=[1, 2, 3], duplicates='drop').astype(str)
                    rfm_table['M_Score'] = pd.qcut(rfm_table['Monetary'], 3, labels=[1, 2, 3], duplicates='drop').astype(str)
                    rfm_table['RFM_Score'] = rfm_table['R_Score'] + rfm_table['F_Score'] + rfm_table['M_Score']
                    
                    st.dataframe(rfm_table.head())
                    
                    fig = px.box(rfm_table, x='R_Score', y='Monetary', 
                                 title='Monetização por Score de Recência', color='R_Score')
                    st.plotly_chart(fig, use_container_width=True)

# --- 5.6. Machine Learning, Pipelines & AutoML
with st.expander("6. Machine Learning, Pipelines e AutoML (Optuna, SHAP)"):
    if st.session_state.df_master is not None:
        
        df = st.session_state.df_master
        all_cols = df.columns.tolist()
        
        st.subheader("Configuração do Pipeline ML")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            y_col = st.selectbox("Alvo (Y):", all_cols, key='ml_target')
            model_key = st.selectbox("Modelo Base:", list(MODEL_MAPPING.keys()), key='ml_model')
            train_size = st.slider("Tamanho do Treino (%):", 10, 90, 70, key='ml_train_size')
        
        with col2:
            x_cols = st.multiselect("Features (X):", [c for c in all_cols if c != y_col], 
                                     default=[c for c in all_cols if c != y_col and 'id' not in c.lower()][:5], key='ml_features')
            
            # Botão para o fluxo de treinamento padrão
            if st.button("Treinar Modelo (Pipeline)", key='btn_train'):
                if y_col and x_cols:
                    
                    # 1. Configuração de dados
                    df_ml = df[[y_col] + x_cols].copy().dropna()
                    X = df_ml[x_cols]
                    Y = df_ml[y_col]
                    
                    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=1-(train_size/100.0), random_state=42)
                    
                    # 2. Criação da Pipeline (Pré-processamento + Modelo)
                    preprocessor, _, _ = get_preprocessor(df_ml, x_cols, y_col)
                    pipeline = get_model_pipeline(model_key, preprocessor)

                    try:
                        with st.spinner(f"Treinando {model_key}..."):
                            pipeline.fit(X_train, Y_train)
                        
                        st.session_state.last_trained_model = pipeline
                        st.session_state.last_trained_X = X_test.copy()

                        # 3. Avaliação
                        Y_pred = pipeline.predict(X_test)
                        
                        st.subheader("Resultados da Avaliação")
                        if 'Regressor' in model_key:
                            rmse = np.sqrt(mean_squared_error(Y_test, Y_pred))
                            r2 = r2_score(Y_test, Y_pred)
                            st.metric("RMSE", f"{rmse:.4f}")
                            st.metric("R²", f"{r2:.4f}")
                        else: # Classifier
                            accuracy = accuracy_score(Y_test, Y_pred.round())
                            st.metric("Acurácia", f"{accuracy:.4f}")
                            st.text("Matriz de Confusão:")
                            cm = confusion_matrix(Y_test, Y_pred.round())
                            fig_cm = px.imshow(cm, text_auto=True, color_continuous_scale='Blues')
                            st.plotly_chart(fig_cm, use_container_width=True)

                        st.success("Modelo treinado e Pipeline salva na sessão!")

                    except Exception as e:
                        st.error(f"Erro no treinamento: {e}")

        with col3:
            st.subheader("AutoML e XAI")
            n_trials = st.number_input("Optuna Trials:", min_value=10, max_value=100, value=20, step=10, key='optuna_trials')
            
            # Botão para o fluxo AutoML (Optuna)
            if st.button("Executar AutoML (Optuna)", key='btn_automl'):
                if y_col and x_cols and ('Classifier' in model_key or 'Regressor' in model_key):
                    # Certifique-se de passar o DataFrame original (df) e não o df_ml
                    best_pipeline = run_optuna_automl(df, y_col, x_cols, model_key, n_trials)
                    if best_pipeline:
                        st.session_state.last_trained_model = best_pipeline
                        # Usa as colunas X originais para o SHAP, que serão transformadas pelo preprocessor da pipeline
                        st.session_state.last_trained_X = df[x_cols].copy().dropna()

            # Botão SHAP (Explicação)
            if st.button("Gerar Análise SHAP (XAI)", key='btn_shap'):
                if st.session_state.last_trained_model and st.session_state.last_trained_X is not None:
                    
                    pipeline = st.session_state.last_trained_model
                    model = pipeline.named_steps['model']
                    # Pega X_test (que são as colunas originais de entrada para a Pipeline)
                    X_input = st.session_state.last_trained_X
                    
                    st.info("Calculando valores SHAP... (Pode demorar)")
                    
                    try:
                        # 1. Transformação dos dados para SHAP (usando o preprocessor da pipeline)
                        preprocessor = pipeline.named_steps['preprocessor']
                        
                        # Obtém os nomes das features após a transformação
                        feature_names = preprocessor.get_feature_names_out(X_input.columns)
                        X_processed = preprocessor.transform(X_input)
                        X_processed_df = pd.DataFrame(X_processed, columns=feature_names)
                        
                        # Amostragem para performance SHAP (Importante para KernelExplainer)
                        sample_size = min(200, len(X_processed_df))
                        X_sample = X_processed_df.sample(sample_size, random_state=42)
                        
                        # 2. Inicializar Explainer
                        model_name = type(model).__name__
                        is_tree_model = any(name in model_name for name in ['XGB', 'RandomForest', 'DecisionTree', 'IsolationForest'])
                        
                        if is_tree_model:
                            explainer = shap.TreeExplainer(model)
                        else:
                            # Se for um modelo linear, usa KernelExplainer com uma amostra (mais lento)
                            explainer = shap.KernelExplainer(model.predict, X_sample)
                            st.warning("Usando KernelExplainer (mais lento) para modelos não-baseados em árvore.")

                        shap_values = explainer.shap_values(X_sample)
                        
                        if isinstance(shap_values, list):
                            shap_values = shap_values[1] # Para classificação binária (foco na classe 1)

                        st.subheader("Importância Global de Features (SHAP Summary)")
                        
                        # Plot SHAP (requer ajuste para Streamlit)
                        import matplotlib.pyplot as plt
                        plt.figure(figsize=(10, 8))
                        shap.summary_plot(shap_values, X_sample, show=False)
                        st.pyplot(plt.gcf(), bbox_inches='tight')
                        
                        st.success("Análise SHAP concluída!")

                    except Exception as e:
                        st.error(f"Erro ao gerar SHAP: {e}")
                        st.warning("Verifique se o modelo foi treinado e se os dados não contêm NaNs/Infinitos.")
                else:
                    st.warning("Treine um modelo primeiro para gerar a análise SHAP.")

# --- 5.7. IA - Insights Inteligentes (MOCK - Gemini API)
with st.expander("7. IA - Insights Inteligentes (Chatbot Gemini API)"):
    st.subheader("Chatbot - Pergunte ao seu DataFrame (Simulação de Gemini)")
    
    ai_question_text = st.text_area("Digite sua pergunta:", key='ai_question_area', 
                                    placeholder='Ex: Qual a correlação entre as duas maiores colunas numéricas? Qual o próximo passo recomendado?')
    
    if st.button("Perguntar ao DF (IA)", key='btn_ai_query'):
        if st.session_state.df_master is None:
            st.error("Nenhum DF Mestre selecionado.")
        elif not ai_question_text:
            st.warning("Por favor, digite sua pergunta.")
        else:
            # Esta seção simula o fluxo de chamada da API do Gemini
            # Em uma implementação real, você faria uma chamada POST com o contexto.
            
            # --- VERIFICAÇÃO DA CHAVE GEMINI (INCLUÍDA AGORA) ---
            if not GEMINI_API_KEY:
                 st.error("ERRO: Chave GEMINI_API_KEY não configurada. Por favor, adicione sua chave na variável global 'GEMINI_API_KEY'.")
                 st.warning("Exibindo resposta MOCK para demonstração.")
            # ----------------------------------------------------
            
            st.info("Simulando chamada à API do Gemini... (A API_KEY deve ser configurada para real)")
            
            df = st.session_state.df_master
            context = f"""
            Contexto do DataFrame (DF Mestre: {st.session_state.df_master_name}):
            - Shape: {df.shape}
            - Colunas (Head): {df.head().to_markdown()}
            - Estatísticas: {df.describe(include='all').to_markdown()}
            """
            
            # Simulação de resposta da IA
            mock_response = (
                f"**Análise Automática (AutoInsights) baseada na sua pergunta: '{ai_question_text}'**\n\n"
                f"1. **Correlação (Simulação):** A correlação entre as duas maiores colunas numéricas é de aproximadamente 0.78 (Se fosse uma regressão, este é um valor alto).\n"
                f"2. **Sugestão de Modelo:** A estrutura dos dados sugere um problema de Regressão. A IA recomenda o **XGBoost Regressor** na aba 'Machine Learning' para melhor performance.\n"
                f"3. **Próximo Passo:** Para insights de negócio, execute a Análise **RFM** (se datas e clientes existirem) ou **ABC** na aba 'Análise de Mercado' para segmentação de valor."
            )
            
            st.subheader("Resposta da IA (Gemini)")
            st.markdown(mock_response)
            
# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("Construído com Streamlit, Scikit-learn Pipelines, Optuna e Dask.")
