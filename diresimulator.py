# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V2
=============================================================================
Fluxo Automatizado de Recomendação:
1. Etapa 1: Entrada de dados do cliente.
2. Etapa 2: Resultados de Enquadramento e Oportunidades (Persistente).
3. Lógica de Poder de Compra: 2x Renda + Finan + FGTS + PS.
4. Recomendações por faixas: 100%, 90% e 75%.

Versão: 4.5 (Design Sequencial Vertical e Centralizado)
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# =============================================================================
# 1. CONFIGURAÇÕES E DADOS (MOCK - PREPARADO PARA DADOS REAIS)
# =============================================================================

def carregar_dados_sistema():
    # MOCK: TABELA FINANCIAMENTOS
    rendas = np.arange(1500, 12100, 100)
    data_finan = []
    for r in rendas:
        if r <= 4700:
            data_finan.append({
                'Renda': r,
                'F2_N_N': r * 54.1, 'F2_S_N': r * 54.1, 'F2_N_S': r * 58.2, 'F2_S_S': r * 58.2,
                'Subsidio': 55000 if r < 2000 else (20000 if r < 4000 else 2000)
            })
        else:
            data_finan.append({
                'Renda': r,
                'F2_N_N': r * 44.5, 'F2_S_N': r * 44.5, 'F2_N_S': r * 48.1, 'F2_S_S': r * 48.1,
                'Subsidio': 0
            })
    df_finan = pd.DataFrame(data_finan)

    # MOCK: BASE ESTOQUE
    data_estoque = {
        'Identificador': [f'BL{i:02d}-{j:03d}' for i in range(1, 11) for j in [101, 202, 303, 404]],
        'Empreendimento': [
            'Conquista Oceânica', 'Viva Vida Recanto Clube', 'Conquista Florianópolis', 
            'Direcional Conquista Max Norte', 'Conquista Norte Clube', 'Nova Caxias Up',
            'Residencial Jerivá', 'Conquista Itanhangá Green', 'Viva Vida Realengo', 'Vert Alcântara'
        ] * 4,
        'Valor de Venda': np.random.randint(190000, 340000, 40),
        'Status': ['Disponível'] * 35 + ['Reservado'] * 5
    }
    df_estoque = pd.DataFrame(data_estoque)
    
    # MOCK: POLÍTICAS PS
    df_politicas = pd.DataFrame({
        'CLASSIFICAÇÃO': ['EMCASH', 'DIAMANTE', 'OURO', 'PRATA', 'BRONZE', 'AÇO'],
        'PERC_PS': [0.25, 0.25, 0.20, 0.18, 0.15, 0.10],
        'PARCELAS': [66, 84, 84, 84, 80, 60]
    })
    
    return df_finan, df_estoque, df_politicas

# =============================================================================
# 2. MOTOR DE CÁLCULO
# =============================================================================

class MotorRecomendacao:
    def __init__(self, df_finan, df_estoque, df_politicas):
        self.df_finan = df_finan
        self.df_estoque = df_estoque
        self.df_politicas = df_politicas

    def obter_enquadramento(self, renda, social, cotista):
        idx = (self.df_finan['Renda'] - renda).abs().idxmin()
        row = self.df_finan.iloc[idx]
        col = f"F2_{'S' if social else 'N'}_{'S' if cotista else 'N'}"
        return float(row[col]), float(row.get('Subsidio', 0))

    def calcular_poder_compra(self, renda, finan, fgts_sub, perc_ps, valor_unidade):
        pro_soluto_unidade = valor_unidade * perc_ps
        poder = (2 * renda) + finan + fgts_sub + pro_soluto_unidade
        return poder, pro_soluto_unidade

    def filtrar_unidades_viaveis(self, renda, finan, fgts_sub, perc_ps):
        estoque_disp = self.df_estoque[self.df_estoque['Status'] == 'Disponível'].copy()
        estoque_disp['Poder_Compra'], estoque_disp['PS_Unidade'] = zip(*estoque_disp['Valor de Venda'].apply(
            lambda vv: self.calcular_poder_compra(renda, finan, fgts_sub, perc_ps, vv)
        ))
        estoque_disp['Viavel'] = estoque_disp['Valor de Venda'] <= estoque_disp['Poder_Compra']
        return estoque_disp[estoque_disp['Viavel']]

# =============================================================================
# 3. INTERFACE E DESIGN
# =============================================================================

def configurar_layout():
    st.set_page_config(page_title="Simulador Direcional", page_icon="🏠", layout="wide")
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .main { background-color: #f8fafc; }
        
        /* Layout Full Width */
        .block-container {
            max-width: 100% !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
            padding-top: 2rem !important;
        }

        .header-container { text-align: center; padding: 25px 0; background: #ffffff; border-bottom: 1px solid #e2e8f0; margin-bottom: 25px; border-radius: 0 0 15px 15px; width: 100%; }
        .header-title { color: #0f172a; font-size: 2.2rem; font-weight: 700; margin: 0; }
        
        .card { background: white; padding: 25px; border-radius: 18px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; width: 100%; }
        .recommendation-card { border-left: 5px solid #2563eb; background: #f8fafc; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
        .price-tag { color: #2563eb; font-weight: 700; font-size: 1.1rem; }
        
        .stButton button { border-radius: 10px !important; padding: 10px !important; font-weight: 600 !important; }
        
        .metric-label { color: #64748b; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; text-align: center; width: 100%; }
        .metric-value { color: #1e293b; font-size: 1.4rem; font-weight: 700; text-align: center; width: 100%; }
        
        /* Alinhamento de títulos */
        h1, h2, h3, h4 { text-align: center !important; width: 100%; }
        
        div[data-baseweb="tab-list"] { justify-content: center !important; border-bottom: none; width: 100%; }
        
        /* Tabelas e Dataframes ocupando largura total */
        .stDataFrame { width: 100% !important; }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 4. COMPONENTES DE INTERAÇÃO
# =============================================================================

def aba_simulador_automacao(df_finan, df_estoque, df_politicas):
    motor = MotorRecomendacao(df_finan, df_estoque, df_politicas)
    
    # Inicialização do estado de navegação
    if 'passo_simulacao' not in st.session_state:
        st.session_state.passo_simulacao = 'input'
    if 'dados_cliente' not in st.session_state:
        st.session_state.dados_cliente = {}

    # --- PASSO 1: ENTRADA DE DADOS ---
    if st.session_state.passo_simulacao == 'input':
        st.markdown("### 👤 Dados do Cliente e Crédito")
        
        # Colunas de centralização para o formulário
        _, col_center, _ = st.columns([1, 2, 1])
        
        with col_center:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            nome = st.text_input("Nome do Cliente", value=st.session_state.dados_cliente.get('nome', ""))
            renda = st.number_input("Renda Bruta Familiar (R$)", min_value=1500.0, value=st.session_state.dados_cliente.get('renda', 3500.0), step=100.0)
            ranking = st.selectbox("Ranking do Cliente", options=df_politicas['CLASSIFICAÇÃO'].unique(), index=2)
            politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"])
            
            # Toggles um embaixo do outro para ser sequencial
            social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False))
            cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True))
            
            st.write("")
            
            # Centralização do botão dentro do card
            btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
            with btn_col2:
                if st.button("🚀 Calcular Oportunidades", type="primary", use_container_width=True):
                    # Salva no estado
                    finan, fgts = motor.obter_enquadramento(renda, social, cotista)
                    
                    # Define percentual de PS
                    if politica_ps == "Emcash":
                        perc = df_politicas[df_politicas['CLASSIFICAÇÃO'] == 'EMCASH']['PERC_PS'].values[0]
                    else:
                        perc = df_politicas[df_politicas['CLASSIFICAÇÃO'] == ranking]['PERC_PS'].values[0]
                    
                    st.session_state.dados_cliente = {
                        'nome': nome, 'renda': renda, 'social': social, 'cotista': cotista,
                        'ranking': ranking, 'politica': politica_ps, 'perc_ps': perc,
                        'finan_estimado': finan, 'fgts_sub': fgts
                    }
                    st.session_state.passo_simulacao = 'results'
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # --- PASSO 2: RESULTADOS E RECOMENDAÇÃO ---
    else:
        d = st.session_state.dados_cliente
        
        # Header de Resumo
        st.markdown(f"### 🎯 Oportunidades para {d['nome'] or 'o Cliente'}")
        
        # Cards de Enquadramento
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="card"><p class="metric-label">Financiamento</p><p class="metric-value">R$ {d["finan_estimado"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="card"><p class="metric-label">FGTS + Subsídio</p><p class="metric-value">R$ {d["fgts_sub"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="card"><p class="metric-label">Teto PS ({d["ranking"]})</p><p class="metric-value">{d["perc_ps"]*100:.0f}%</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><p class="metric-label">Política</p><p class="metric-value">{d["politica"]}</p></div>', unsafe_allow_html=True)

        # Processamento das unidades
        df_viaveis = motor.filtrar_unidades_viaveis(d['renda'], d['finan_estimado'], d['fgts_sub'], d['perc_ps'])
        
        if df_viaveis.empty:
            st.error("❌ Não foram encontradas unidades compatíveis com este poder de compra.")
            if st.button("⬅️ Voltar e ajustar dados"):
                st.session_state.passo_simulacao = 'input'
                st.rerun()
        else:
            col_sel, col_rec = st.columns([1, 2])
            
            with col_sel:
                st.markdown("#### Escolha o Produto")
                empreendimentos = sorted(df_viaveis['Empreendimento'].unique())
                emp_escolhido = st.selectbox("Produtos Viáveis:", options=empreendimentos)
                
            with col_rec:
                unidades_emp = df_viaveis[df_viaveis['Empreendimento'] == emp_escolhido].sort_values('Valor de Venda', ascending=False)
                max_poder_neste_emp = unidades_emp['Poder_Compra'].max()

                def recomendar(percentual):
                    limite = max_poder_neste_emp * percentual
                    candidatos = unidades_emp[unidades_emp['Valor de Venda'] <= limite]
                    if candidatos.empty:
                        return unidades_emp.iloc[-1]
                    return candidatos.iloc[0]

                r100 = recomendar(1.0)
                r90 = recomendar(0.9)
                r75 = recomendar(0.75)

                st.markdown("#### Unidades Recomendadas")
                c_a, c_b, c_c = st.columns(3)
                
                with c_a:
                    st.markdown(f'<div class="recommendation-card" style="border-color:#2563eb;"><small>IDEAL (100%)</small><br><b>{r100["Identificador"]}</b><br><span class="price-tag">R$ {r100["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                with c_b:
                    st.markdown(f'<div class="recommendation-card" style="border-color:#f59e0b;"><small>SEGURA (90%)</small><br><b>{r90["Identificador"]}</b><br><span class="price-tag">R$ {r90["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                with c_c:
                    st.markdown(f'<div class="recommendation-card" style="border-color:#10b981;"><small>FACILITADA (75%)</small><br><b>{r75["Identificador"]}</b><br><span class="price-tag">R$ {r75["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("Lista Completa de Unidades Disponíveis")
            st.dataframe(unidades_emp[['Identificador', 'Valor de Venda', 'PS_Unidade', 'Poder_Compra']], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            col_back_space, col_back_btn, col_back_space2 = st.columns([1, 1, 1])
            with col_back_btn:
                if st.button("⬅️ Mudar Informações do Cliente", use_container_width=True):
                    st.session_state.passo_simulacao = 'input'
                    st.rerun()

def aba_estoque_geral(df_estoque):
    st.markdown("### 📋 Base de Estoque Total")
    
    # Filtros de Empreendimento e Ordenação
    c1, c2 = st.columns([2, 1])
    with c1:
        emp_opcoes = sorted(df_estoque['Empreendimento'].unique())
        emp_selecionados = st.multiselect("Filtrar por Empreendimento:", options=emp_opcoes)
    
    with c2:
        sort_option = st.selectbox("Ordenar por Valor de Venda:", ["Nenhum", "Menor Preço", "Maior Preço"])

    # Lógica de Filtro
    df_display_estoque = df_estoque.copy()
    if emp_selecionados:
        df_display_estoque = df_display_estoque[df_display_estoque['Empreendimento'].isin(emp_selecionados)]
    
    # Lógica de Ordenação
    if sort_option == "Menor Preço":
        df_display_estoque = df_display_estoque.sort_values(by='Valor de Venda', ascending=True)
    elif sort_option == "Maior Preço":
        df_display_estoque = df_display_estoque.sort_values(by='Valor de Venda', ascending=False)
        
    st.dataframe(df_display_estoque, use_container_width=True, hide_index=True)

# =============================================================================
# 5. MAIN
# =============================================================================

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()

    st.markdown("""
        <div class="header-container">
            <div class="header-title">SIMULADOR DIRECIONAL V2</div>
            <div class="header-subtitle">Automação de Vendas e Recomendação de Estoque</div>
        </div>
    """, unsafe_allow_html=True)

    # Removida a aba de Políticas de PS conforme solicitação
    tabs = st.tabs(["🎯 Simulação e Recomendação", "🏢 Base de Estoque"])

    with tabs[0]:
        aba_simulador_automacao(df_finan, df_estoque, df_politicas)

    with tabs[1]:
        aba_estoque_geral(df_estoque)

if __name__ == "__main__":
    main()
