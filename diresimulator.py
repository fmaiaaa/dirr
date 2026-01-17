# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V2
=============================================================================
Fluxo Automatizado de Recomendação (Sequencial):
1. Etapa 1: Entrada de dados do cliente.
2. Etapa 2: Valor Potencial de Compra.
3. Etapa 3: Guia de Viabilidade.
4. Etapa 4: Fechamento Financeiro.

Versão: 15.4 (Resiliência de Dados & Diagnóstico de Acesso)
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from streamlit_gsheets import GSheetsConnection

# =============================================================================
# 0. CONSTANTES DE ACESSO (IDs DAS PLANILHAS REAIS)
# =============================================================================
ID_FINAN = "1wJD3tXe1e8FxL4mVEfNKGdtaS__Dl4V6-sm1G6qfL0s"
ID_RANKING = "1N00McOjO1O_MuKyQhp-CVhpAet_9Lfq-VqVm1FmPV00"
ID_ESTOQUE = "1VG-hgBkddyssN1OXgIA33CVsKGAdqT-5kwbgizxWDZQ"

# URLs oficiais para o conector
URL_FINAN = f"https://docs.google.com/spreadsheets/d/{ID_FINAN}/edit#gid=0"
URL_RANKING = f"https://docs.google.com/spreadsheets/d/{ID_RANKING}/edit#gid=0"
URL_ESTOQUE = f"https://docs.google.com/spreadsheets/d/{ID_ESTOQUE}/edit#gid=0"

# =============================================================================
# 1. CARREGAMENTO E TRATAMENTO DE DADOS
# =============================================================================

@st.cache_data(ttl=300)
def carregar_dados_sistema():
    try:
        if "connections" not in st.secrets:
            st.error("⚠️ Configuração de 'Secrets' não encontrada no painel do Streamlit Cloud.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        conn = st.connection("gsheets", type=GSheetsConnection)

        # 1.1 Carregar Ranking
        try:
            df_politicas_raw = conn.read(spreadsheet=URL_RANKING)
            df_politicas = df_politicas_raw.rename(columns={
                'FAIXA RENDA': 'FAIXA_RENDA',
                'FX RENDA 1': 'FX_RENDA_1',
                'FX RENDA 2': 'FX_RENDA_2'
            })

            def limpar_porcentagem(val):
                if isinstance(val, str):
                    v = val.replace('%', '').replace(',', '.').strip()
                    try:
                        num = float(v)
                        return num / 100 if num > 1 else num
                    except: return 0.0
                return val

            for col in ['PROSOLUTO', 'FX_RENDA_1', 'FX_RENDA_2']:
                if col in df_politicas.columns:
                    df_politicas[col] = df_politicas[col].apply(limpar_porcentagem)
        except Exception as e:
            st.error(f"Falha ao ler Tabela de Ranking: {e}")
            df_politicas = pd.DataFrame()

        # 1.2 Carregar Financiamento
        try:
            df_finan = conn.read(spreadsheet=URL_FINAN)
        except Exception as e:
            st.error(f"Falha ao ler Tabela de Financiamento: {e}")
            df_finan = pd.DataFrame()

        # 1.3 Carregar Estoque
        try:
            df_raw_estoque = conn.read(spreadsheet=URL_ESTOQUE)
            df_estoque = df_raw_estoque.rename(columns={
                'Nome do Empreendimento': 'Empreendimento',
                'VALOR DE VENDA': 'Valor de Venda',
                'Status da unidade': 'Status'
            })
            
            if 'Bairro' not in df_estoque.columns:
                df_estoque['Bairro'] = "Rio de Janeiro"
            if 'Identificador' not in df_estoque.columns:
                df_estoque['Identificador'] = df_estoque.index.astype(str)
                
            # FUNÇÃO ROBUSTA: Limpa '000B', 'Térreo' e outros textos
            def extrair_andar_seguro(id_unid):
                try:
                    val_str = str(id_unid)
                    # Se houver hífen, foca na parte da unidade (ex: BL01-1002 -> 1002)
                    if '-' in val_str:
                        val_str = val_str.split('-')[-1]
                    # Filtra apenas os números
                    nums = re.sub(r'\D', '', val_str)
                    if nums:
                        return int(nums) // 100
                    return 0
                except: return 0

            df_estoque['Andar'] = df_estoque['Identificador'].apply(extrair_andar_seguro)
        except Exception as e:
            st.error(f"Falha ao ler Tabela de Estoque: {e}")
            df_estoque = pd.DataFrame()
        
        return df_finan, df_estoque, df_politicas
    
    except Exception as e:
        st.error(f"🚨 Erro geral de conexão: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# =============================================================================
# 2. MOTOR DE CÁLCULO
# =============================================================================

class MotorRecomendacao:
    def __init__(self, df_finan, df_estoque, df_politicas):
        self.df_finan = df_finan
        self.df_estoque = df_estoque
        self.df_politicas = df_politicas

    def obter_enquadramento(self, renda, social, cotista):
        if self.df_finan.empty: return 0.0, 0.0
        # Força renda a ser numérica
        self.df_finan['Renda'] = pd.to_numeric(self.df_finan['Renda'], errors='coerce').fillna(0)
        idx = (self.df_finan['Renda'] - renda).abs().idxmin()
        row = self.df_finan.iloc[idx]
        
        s_suf = 'Sim' if social else 'Nao'
        c_suf = 'Sim' if cotista else 'Nao'
        
        c_finan = f"Finan_Social_{s_suf}_Cotista_{c_suf}"
        c_sub = f"Subsidio_Social_{s_suf}_Cotista_{c_suf}"
        
        return float(row.get(c_finan, 0)), float(row.get(c_sub, 0))

    def calcular_poder_compra(self, renda, finan, fgts_sub, perc_ps, valor_unidade):
        pro_soluto_unidade = valor_unidade * perc_ps
        poder = (2 * renda) + finan + fgts_sub + pro_soluto_unidade
        return poder, pro_soluto_unidade

    def filtrar_unidades_viaveis(self, renda, finan, fgts_sub, perc_ps):
        if self.df_estoque.empty: return pd.DataFrame()
        estoque_disp = self.df_estoque[self.df_estoque['Status'] == 'Disponível'].copy()
        
        # Converte Preço para número, removendo R$ e pontos se existirem
        def limpar_preco(val):
            if isinstance(val, str):
                val = val.replace('R$', '').replace('.', '').replace(',', '.').strip()
            try: return float(val)
            except: return 0.0

        estoque_disp['Valor de Venda'] = estoque_disp['Valor de Venda'].apply(limpar_preco)
        
        res = estoque_disp['Valor de Venda'].apply(lambda vv: self.calcular_poder_compra(renda, finan, fgts_sub, perc_ps, vv))
        estoque_disp['Poder_Compra'] = [x[0] for x in res]
        estoque_disp['PS_Unidade'] = [x[1] for x in res]
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
        .block-container { max-width: 1200px !important; padding: 1rem 1rem 5rem 1rem !important; margin: auto !important; }
        .header-container { text-align: center; padding: 25px 0; background: #ffffff; border-bottom: 1px solid #e2e8f0; margin-bottom: 25px; border-radius: 0 0 15px 15px; }
        .header-title { color: #0f172a; font-size: 2rem; font-weight: 700; margin: 0; }
        .card { background: white; padding: 20px; border-radius: 18px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; min-height: 120px; display: flex; flex-direction: column; justify-content: center; }
        .recommendation-card { background: #ffffff; padding: 20px; border: 1px solid #e2e8f0; border-top: 5px solid #2563eb; border-radius: 12px; margin-bottom: 15px; text-align: center; min-height: 160px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        .thin-card { background: white; padding: 12px 20px; border-radius: 10px; border: 1px solid #e2e8f0; border-left: 5px solid #64748b; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .price-tag { color: #2563eb; font-weight: 700; font-size: 1.1rem; }
        .metric-label { color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; text-align: center; }
        .metric-value { color: #1e293b; font-size: 1.2rem; font-weight: 700; text-align: center; }
        .stButton button { border-radius: 10px !important; padding: 10px !important; font-weight: 600 !important; }
        h1, h2, h3, h4 { text-align: center !important; width: 100%; }
        .fin-box { text-align: center; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; margin-bottom: 15px; width: 100%; }
        .inline-ref { font-size: 0.8rem; color: #64748b; margin-top: -12px; margin-bottom: 12px; font-weight: 500; text-align: left; }
        div[data-baseweb="tab-list"] { justify-content: center !important; display: flex !important; }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 4. COMPONENTES DE INTERAÇÃO
# =============================================================================

def aba_simulador_automacao(df_finan, df_estoque, df_politicas):
    motor = MotorRecomendacao(df_finan, df_estoque, df_politicas)
    
    if 'passo_simulacao' not in st.session_state:
        st.session_state.passo_simulacao = 'input'
    if 'dados_cliente' not in st.session_state:
        st.session_state.dados_cliente = {}

    # --- ETAPA 1 ---
    if st.session_state.passo_simulacao == 'input':
        st.markdown("### 👤 Etapa 1: Dados do Cliente")
        _, col_center, _ = st.columns([1, 2, 1])
        with col_center:
            nome = st.text_input("Nome do Cliente", value=st.session_state.dados_cliente.get('nome', ""))
            renda = st.number_input("Renda Bruta Familiar (R$)", min_value=1.0, value=st.session_state.dados_cliente.get('renda', 3500.0), step=100.0)
            ranking_options = df_politicas['CLASSIFICAÇÃO'].unique().tolist() if not df_politicas.empty else ["EMCASH"]
            ranking = st.selectbox("Ranking do Cliente", options=ranking_options, index=0)
            politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"])
            social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False))
            cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True))
            
            if st.button("🚀 Avançar para Visão Financeira", type="primary", use_container_width=True):
                finan, sub = motor.obter_enquadramento(renda, social, cotista)
                class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
                politica_row = df_politicas[df_politicas['CLASSIFICAÇÃO'] == class_b].iloc[0]
                limit_ps = politica_row['FX_RENDA_1'] if renda < politica_row['FAIXA_RENDA'] else politica_row['FX_RENDA_2']
                
                st.session_state.dados_cliente = {
                    'nome': nome, 'renda': renda, 'social': social, 'cotista': cotista,
                    'ranking': ranking, 'politica': politica_ps, 
                    'perc_ps': politica_row['PROSOLUTO'], 'prazo_ps': int(politica_row['PARCELAS']),
                    'limit_ps_renda': limit_ps, 'finan_estimado': finan, 'fgts_sub': sub
                }
                st.session_state.passo_simulacao = 'potential'
                st.rerun()

    # --- ETAPA 2 ---
    elif st.session_state.passo_simulacao == 'potential':
        d = st.session_state.dados_cliente
        st.markdown(f"### 💰 Etapa 2: Potencial de Compra - {d['nome'] or 'Cliente'}")
        
        # Garante que os preços do estoque são números para o cálculo
        precos_estoque = pd.to_numeric(df_estoque['Valor de Venda'], errors='coerce').dropna()
        ps_min_total = precos_estoque.min() * d['perc_ps']
        ps_max_total = precos_estoque.max() * d['perc_ps']
        dobro_renda = 2 * d['renda']
        pot_min = d['finan_estimado'] + d['fgts_sub'] + ps_min_total + dobro_renda
        pot_max = d['finan_estimado'] + d['fgts_sub'] + ps_max_total + dobro_renda
        
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="card"><p class="metric-label">Financiamento</p><p class="metric-value">R$ {d["finan_estimado"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="card"><p class="metric-label">FGTS + Subsídio</p><p class="metric-value">R$ {d["fgts_sub"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="card"><p class="metric-label">PS (Est.)</p><p class="metric-value">R$ {ps_min_total:,.0f}-{ps_max_total:,.0f}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><p class="metric-label">Capacidade Entrada</p><p class="metric-value">R$ {dobro_renda:,.2f}</p></div>', unsafe_allow_html=True)

        st.markdown(f"""
            <div class="card" style="border-top: 5px solid #2563eb; text-align: center; background: #f0f7ff; min-height: auto; padding: 30px;">
                <p class="metric-label" style="color: #2563eb; font-size: 1.1rem;">Valor Potencial de Compra Estimado</p>
                <p class="metric-value" style="font-size: 2.2rem; color: #0f172a; margin-bottom:5px;">R$ {pot_min:,.2f} a R$ {pot_max:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏢 Ver Produtos Viáveis", type="primary", use_container_width=True):
            st.session_state.passo_simulacao = 'guide'; st.rerun()
        st.write("")
        if st.button("⬅️ Editar Dados", use_container_width=True):
            st.session_state.passo_simulacao = 'input'; st.rerun()

    # --- ETAPA 3 ---
    elif st.session_state.passo_simulacao == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### 🔍 Etapa 3: Guia de Viabilidade")
        df_viaveis = motor.filtrar_unidades_viaveis(d['renda'], d['finan_estimado'], d['fgts_sub'], d['perc_ps'])
        
        if df_viaveis.empty:
            st.error("❌ Nenhuma unidade viável no estoque para este perfil.")
            if st.button("⬅️ Voltar", use_container_width=True): st.session_state.passo_simulacao = 'potential'; st.rerun()
        else:
            with st.expander("🏢 Empreendimentos Disponíveis", expanded=True):
                emp_counts = df_viaveis.groupby('Empreendimento').size().to_dict()
                for emp, qtd in emp_counts.items():
                    st.markdown(f'<div class="thin-card"><div><b>{emp}</b></div><div>{qtd} unid.</div></div>', unsafe_allow_html=True)

            tab_rec, tab_list = st.tabs(["⭐ Recomendações", "📋 Estoque Completo"])
            with tab_rec:
                emp_rec = st.selectbox("Filtrar por Empreendimento:", options=["Todos"] + sorted(df_viaveis['Empreendimento'].unique().tolist()))
                df_filt = df_viaveis if emp_rec == "Todos" else df_viaveis[df_viaveis['Empreendimento'] == emp_rec]
                df_filt = df_filt.sort_values('Valor de Venda', ascending=False)
                
                if not df_filt.empty:
                    def get_r(pct):
                        target = df_filt['Poder_Compra'].max() * pct
                        cand = df_filt[df_filt['Valor de Venda'] <= target]
                        return cand.iloc[0] if not cand.empty else df_filt.iloc[-1]
                    
                    r100, r90, r75 = get_r(1.0), get_r(0.9), get_r(0.75)
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(f'<div class="recommendation-card" style="border-top-color:#2563eb;"><b>IDEAL</b><br>{r100["Identificador"]}<br><span class="price-tag">R$ {r100["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="recommendation-card" style="border-top-color:#f59e0b;"><b>SEGURA</b><br>{r90["Identificador"]}<br><span class="price-tag">R$ {r90["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="recommendation-card" style="border-top-color:#10b981;"><b>FACILITADA</b><br>{r75["Identificador"]}<br><span class="price-tag">R$ {r75["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)

                st.markdown("---")
                if st.button("💰 Ir para Fechamento", type="primary", use_container_width=True):
                    st.session_state.passo_simulacao = 'payment_flow'; st.rerun()
                st.write("")
                if st.button("⬅️ Voltar ao Potencial", use_container_width=True): 
                    st.session_state.passo_simulacao = 'potential'; st.rerun()

            with tab_list:
                st.dataframe(df_viaveis[['Identificador', 'Empreendimento', 'Bairro', 'Valor de Venda', 'Poder_Compra']], use_container_width=True, hide_index=True)

    # --- ETAPA 4 ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### 📑 Etapa 4: Fechamento Financeiro")
        emp_def = st.selectbox("Escolha o Empreendimento:", options=sorted(df_estoque['Empreendimento'].unique()))
        unidades = df_estoque[(df_estoque['Empreendimento'] == emp_def) & (df_estoque['Status'] == 'Disponível')]
        
        if not unidades.empty:
            u_id = st.selectbox("Escolha a Unidade:", options=unidades['Identificador'].unique())
            u = unidades[unidades['Identificador'] == u_id].iloc[0]
            
            f_u = st.number_input("Financiamento (R$)", value=float(d['finan_estimado']))
            st.markdown(f'<p class="inline-ref">Ref. Aprovado: R$ {d["finan_estimado"]:,.2f}</p>', unsafe_allow_html=True)
            fgts_u = st.number_input("FGTS + Subsídio (R$)", value=float(d['fgts_sub']))
            st.markdown(f'<p class="inline-ref">Ref. Estimado: R$ {d["fgts_sub"]:,.2f}</p>', unsafe_allow_html=True)
            
            ps_max = u['Valor de Venda'] * d['perc_ps']
            ps_u = st.number_input("Pro Soluto (R$)", value=float(ps_max))
            st.markdown(f'<p class="inline-ref">Limite {int(d["perc_ps"]*100)}%: R$ {ps_max:,.2f}</p>', unsafe_allow_html=True)
            
            parc = st.number_input("Parcelas PS", min_value=1, max_value=d['prazo_ps'], value=d['prazo_ps'])
            v_parc = ps_u / parc
            comp = v_parc / d['renda']
            saldo = u['Valor de Venda'] - f_u - fgts_u - ps_u
            
            st.markdown(f"""
                <div class="fin-box" style="border-top: 5px solid #64748b;"><b>Imóvel:</b> R$ {u['Valor de Venda']:,.2f}</div>
                <div class="fin-box" style="background:#f8fafc; border-top: 5px solid #2563eb;"><b>Parcela PS:</b> R$ {v_parc:,.2f} ({comp*100:.1f}% da Renda)</div>
            """, unsafe_allow_html=True)
            
            if comp > d['limit_ps_renda']:
                st.warning(f"⚠️ Atenção: Parcela ultrapassa o limite de {d['limit_ps_renda']*100:.0f}% da renda.")

            st.markdown(f'<div class="fin-box" style="background:#fff1f2; border-top: 5px solid #e11d48;"><b>Saldo Entrada:</b> R$ {max(0, saldo):,.2f}</div>', unsafe_allow_html=True)
            
            if saldo > 0:
                st.markdown("#### 🖋️ Parcelamento da Entrada")
                st.number_input("Ato (R$)", value=saldo/4, key="a1")
                st.number_input("30 dias (R$)", value=saldo/4, key="a2")
                st.number_input("60 dias (R$)", value=saldo/4, key="a3")
                st.number_input("90 dias (R$)", value=saldo/4, key="a4")
        
        st.markdown("---")
        if st.button("⬅️ Voltar", use_container_width=True): st.session_state.passo_simulacao = 'guide'; st.rerun()
        if st.button("👤 Novo Cliente", use_container_width=True): st.session_state.passo_simulacao = 'input'; st.rerun()

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()
    
    if df_finan.empty or df_estoque.empty or df_politicas.empty:
        st.warning("⚠️ O sistema está a carregar dados privados. Se o erro persistir:")
        st.info("1. Verifique se ativou a 'Google Drive API' no Cloud Console.")
        st.info("2. Certifique-se de que partilhou as planilhas com o e-mail da Conta de Serviço.")
        st.stop()
        
    st.markdown('<div class="header-container"><div class="header-title">SIMULADOR DIRECIONAL V2</div></div>', unsafe_allow_html=True)
    aba_simulador_automacao(df_finan, df_estoque, df_politicas)

if __name__ == "__main__":
    main()@st.cache_data(ttl=300) # 5 minutos de cache
def carregar_dados_sistema():
    try:
        # Verifica se os segredos básicos existem no Streamlit Cloud
        if "connections" not in st.secrets:
            st.error("⚠️ Configuração de 'Secrets' não encontrada no painel do Streamlit.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        conn = st.connection("gsheets", type=GSheetsConnection)

        # 1.1 Carregar Ranking
        df_politicas_raw = conn.read(spreadsheet=URL_RANKING, worksheet="0")
        df_politicas = df_politicas_raw.rename(columns={
            'FAIXA RENDA': 'FAIXA_RENDA',
            'FX RENDA 1': 'FX_RENDA_1',
            'FX RENDA 2': 'FX_RENDA_2'
        })

        def limpar_porcentagem(val):
            if isinstance(val, str):
                v = val.replace('%', '').replace(',', '.').strip()
                try:
                    num = float(v)
                    return num / 100 if num > 1 else num
                except: return 0.0
            return val

        for col in ['PROSOLUTO', 'FX_RENDA_1', 'FX_RENDA_2']:
            if col in df_politicas.columns:
                df_politicas[col] = df_politicas[col].apply(limpar_porcentagem)

        # 1.2 Carregar Financiamento
        df_finan = conn.read(spreadsheet=URL_FINAN, worksheet="0")

        # 1.3 Carregar Estoque e Mapear Colunas Direcional
        df_raw_estoque = conn.read(spreadsheet=URL_ESTOQUE, worksheet="0")
        df_estoque = df_raw_estoque.rename(columns={
            'Nome do Empreendimento': 'Empreendimento',
            'VALOR DE VENDA': 'Valor de Venda',
            'Status da unidade': 'Status'
        })
        
        if 'Bairro' not in df_estoque.columns:
            df_estoque['Bairro'] = "Rio de Janeiro"
        if 'Identificador' not in df_estoque.columns:
            df_estoque['Identificador'] = df_estoque.index.astype(str)
            
        def extrair_andar(id_unid):
            try:
                return int(str(id_unid).split('-')[-1]) // 100
            except: return 0

        df_estoque['Andar'] = df_estoque['Identificador'].apply(extrair_andar)
        
        return df_finan, df_estoque, df_politicas
    
    except Exception as e:
        st.error(f"🚨 Erro crítico de conexão: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# =============================================================================
# 2. MOTOR DE CÁLCULO
# =============================================================================

class MotorRecomendacao:
    def __init__(self, df_finan, df_estoque, df_politicas):
        self.df_finan = df_finan
        self.df_estoque = df_estoque
        self.df_politicas = df_politicas

    def obter_enquadramento(self, renda, social, cotista):
        if self.df_finan.empty: return 0.0, 0.0
        idx = (self.df_finan['Renda'] - renda).abs().idxmin()
        row = self.df_finan.iloc[idx]
        s_suf = 'Sim' if social else 'Nao'
        c_suf = 'Sim' if cotista else 'Nao'
        c_finan = f"Finan_Social_{s_suf}_Cotista_{c_suf}"
        c_sub = f"Subsidio_Social_{s_suf}_Cotista_{c_suf}"
        return float(row.get(c_finan, 0)), float(row.get(c_sub, 0))

    def calcular_poder_compra(self, renda, finan, fgts_sub, perc_ps, valor_unidade):
        pro_soluto_unidade = valor_unidade * perc_ps
        poder = (2 * renda) + finan + fgts_sub + pro_soluto_unidade
        return poder, pro_soluto_unidade

    def filtrar_unidades_viaveis(self, renda, finan, fgts_sub, perc_ps):
        if self.df_estoque.empty: return pd.DataFrame()
        estoque_disp = self.df_estoque[self.df_estoque['Status'] == 'Disponível'].copy()
        estoque_disp['Valor de Venda'] = pd.to_numeric(estoque_disp['Valor de Venda'], errors='coerce').fillna(0)
        res = estoque_disp['Valor de Venda'].apply(lambda vv: self.calcular_poder_compra(renda, finan, fgts_sub, perc_ps, vv))
        estoque_disp['Poder_Compra'] = [x[0] for x in res]
        estoque_disp['PS_Unidade'] = [x[1] for x in res]
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
        .block-container { max-width: 1200px !important; padding: 1rem 1rem 5rem 1rem !important; margin: auto !important; }
        .header-container { text-align: center; padding: 25px 0; background: #ffffff; border-bottom: 1px solid #e2e8f0; margin-bottom: 25px; border-radius: 0 0 15px 15px; }
        .header-title { color: #0f172a; font-size: 2rem; font-weight: 700; margin: 0; }
        .card { background: white; padding: 20px; border-radius: 18px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; min-height: 120px; display: flex; flex-direction: column; justify-content: center; }
        .recommendation-card { background: #ffffff; padding: 20px; border: 1px solid #e2e8f0; border-top: 5px solid #2563eb; border-radius: 12px; margin-bottom: 15px; text-align: center; min-height: 160px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        .thin-card { background: white; padding: 12px 20px; border-radius: 10px; border: 1px solid #e2e8f0; border-left: 5px solid #64748b; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .price-tag { color: #2563eb; font-weight: 700; font-size: 1.1rem; }
        .metric-label { color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; text-align: center; }
        .metric-value { color: #1e293b; font-size: 1.2rem; font-weight: 700; text-align: center; }
        .stButton button { border-radius: 10px !important; padding: 10px !important; font-weight: 600 !important; }
        h1, h2, h3, h4 { text-align: center !important; width: 100%; }
        .fin-box { text-align: center; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; margin-bottom: 15px; width: 100%; }
        .inline-ref { font-size: 0.8rem; color: #64748b; margin-top: -12px; margin-bottom: 12px; font-weight: 500; text-align: left; }
        div[data-baseweb="tab-list"] { justify-content: center !important; display: flex !important; }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 4. COMPONENTES DE INTERAÇÃO
# =============================================================================

def aba_simulador_automacao(df_finan, df_estoque, df_politicas):
    motor = MotorRecomendacao(df_finan, df_estoque, df_politicas)
    
    if 'passo_simulacao' not in st.session_state:
        st.session_state.passo_simulacao = 'input'
    if 'dados_cliente' not in st.session_state:
        st.session_state.dados_cliente = {}

    # --- ETAPA 1 ---
    if st.session_state.passo_simulacao == 'input':
        st.markdown("### 👤 Etapa 1: Dados do Cliente")
        _, col_center, _ = st.columns([1, 2, 1])
        with col_center:
            nome = st.text_input("Nome do Cliente", value=st.session_state.dados_cliente.get('nome', ""))
            renda = st.number_input("Renda Bruta Familiar (R$)", min_value=1500.0, value=st.session_state.dados_cliente.get('renda', 3500.0), step=100.0)
            ranking_options = df_politicas['CLASSIFICAÇÃO'].unique().tolist()
            ranking = st.selectbox("Ranking do Cliente", options=ranking_options, index=0)
            politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"])
            social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False))
            cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True))
            
            if st.button("🚀 Avançar para Visão Financeira", type="primary", use_container_width=True):
                finan, sub = motor.obter_enquadramento(renda, social, cotista)
                class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
                politica_row = df_politicas[df_politicas['CLASSIFICAÇÃO'] == class_b].iloc[0]
                limit_ps = politica_row['FX_RENDA_1'] if renda < politica_row['FAIXA_RENDA'] else politica_row['FX_RENDA_2']
                
                st.session_state.dados_cliente = {
                    'nome': nome, 'renda': renda, 'social': social, 'cotista': cotista,
                    'ranking': ranking, 'politica': politica_ps, 
                    'perc_ps': politica_row['PROSOLUTO'], 'prazo_ps': int(politica_row['PARCELAS']),
                    'limit_ps_renda': limit_ps, 'finan_estimado': finan, 'fgts_sub': sub
                }
                st.session_state.passo_simulacao = 'potential'
                st.rerun()

    # --- ETAPA 2 ---
    elif st.session_state.passo_simulacao == 'potential':
        d = st.session_state.dados_cliente
        st.markdown(f"### 💰 Etapa 2: Potencial de Compra - {d['nome'] or 'Cliente'}")
        
        ps_min_total = df_estoque['Valor de Venda'].min() * d['perc_ps']
        ps_max_total = df_estoque['Valor de Venda'].max() * d['perc_ps']
        dobro_renda = 2 * d['renda']
        pot_min = d['finan_estimado'] + d['fgts_sub'] + ps_min_total + dobro_renda
        pot_max = d['finan_estimado'] + d['fgts_sub'] + ps_max_total + dobro_renda
        
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="card"><p class="metric-label">Financiamento</p><p class="metric-value">R$ {d["finan_estimado"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="card"><p class="metric-label">FGTS + Subsídio</p><p class="metric-value">R$ {d["fgts_sub"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="card"><p class="metric-label">PS (Est.)</p><p class="metric-value">R$ {ps_min_total:,.0f}-{ps_max_total:,.0f}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><p class="metric-label">Capacidade Entrada</p><p class="metric-value">R$ {dobro_renda:,.2f}</p></div>', unsafe_allow_html=True)

        st.markdown(f"""
            <div class="card" style="border-top: 5px solid #2563eb; text-align: center; background: #f0f7ff; min-height: auto; padding: 30px;">
                <p class="metric-label" style="color: #2563eb; font-size: 1.1rem;">Valor Potencial de Compra Estimado</p>
                <p class="metric-value" style="font-size: 2.2rem; color: #0f172a; margin-bottom:5px;">R$ {pot_min:,.2f} a R$ {pot_max:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏢 Ver Produtos Viáveis", type="primary", use_container_width=True):
            st.session_state.passo_simulacao = 'guide'; st.rerun()
        st.write("")
        if st.button("⬅️ Editar Dados", use_container_width=True):
            st.session_state.passo_simulacao = 'input'; st.rerun()

    # --- ETAPA 3 ---
    elif st.session_state.passo_simulacao == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### 🔍 Etapa 3: Guia de Viabilidade")
        df_viaveis = motor.filtrar_unidades_viaveis(d['renda'], d['finan_estimado'], d['fgts_sub'], d['perc_ps'])
        
        if df_viaveis.empty:
            st.error("❌ Nenhuma unidade viável no estoque para este perfil.")
            if st.button("⬅️ Voltar", use_container_width=True): st.session_state.passo_simulacao = 'potential'; st.rerun()
        else:
            with st.expander("🏢 Empreendimentos Disponíveis", expanded=True):
                emp_counts = df_viaveis.groupby('Empreendimento').size().to_dict()
                for emp, qtd in emp_counts.items():
                    st.markdown(f'<div class="thin-card"><div><b>{emp}</b></div><div>{qtd} unid.</div></div>', unsafe_allow_html=True)

            tab_rec, tab_list = st.tabs(["⭐ Recomendações", "📋 Estoque Completo"])
            with tab_rec:
                emp_rec = st.selectbox("Filtrar por Empreendimento:", options=["Todos"] + sorted(df_viaveis['Empreendimento'].unique().tolist()))
                df_filt = df_viaveis if emp_rec == "Todos" else df_viaveis[df_viaveis['Empreendimento'] == emp_rec]
                df_filt = df_filt.sort_values('Valor de Venda', ascending=False)
                
                if not df_filt.empty:
                    def get_r(pct):
                        target = df_filt['Poder_Compra'].max() * pct
                        cand = df_filt[df_filt['Valor de Venda'] <= target]
                        return cand.iloc[0] if not cand.empty else df_filt.iloc[-1]
                    
                    r100, r90, r75 = get_r(1.0), get_r(0.9), get_r(0.75)
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(f'<div class="recommendation-card" style="border-top-color:#2563eb;"><b>IDEAL</b><br>{r100["Identificador"]}<br><span class="price-tag">R$ {r100["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="recommendation-card" style="border-top-color:#f59e0b;"><b>SEGURA</b><br>{r90["Identificador"]}<br><span class="price-tag">R$ {r90["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="recommendation-card" style="border-top-color:#10b981;"><b>FACILITADA</b><br>{r75["Identificador"]}<br><span class="price-tag">R$ {r75["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)

                st.markdown("---")
                if st.button("💰 Ir para Fechamento", type="primary", use_container_width=True):
                    st.session_state.passo_simulacao = 'payment_flow'; st.rerun()
                st.write("")
                if st.button("⬅️ Voltar ao Potencial", use_container_width=True): 
                    st.session_state.passo_simulacao = 'potential'; st.rerun()

            with tab_list:
                st.dataframe(df_viaveis[['Identificador', 'Empreendimento', 'Bairro', 'Valor de Venda', 'Poder_Compra']], use_container_width=True, hide_index=True)

    # --- ETAPA 4 ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### 📑 Etapa 4: Fechamento Financeiro")
        emp_def = st.selectbox("Escolha o Empreendimento:", options=sorted(df_estoque['Empreendimento'].unique()))
        unidades = df_estoque[(df_estoque['Empreendimento'] == emp_def) & (df_estoque['Status'] == 'Disponível')]
        
        if not unidades.empty:
            u_id = st.selectbox("Escolha a Unidade:", options=unidades['Identificador'].unique())
            u = unidades[unidades['Identificador'] == u_id].iloc[0]
            
            f_u = st.number_input("Financiamento (R$)", value=float(d['finan_estimado']))
            st.markdown(f'<p class="inline-ref">Ref. Aprovado: R$ {d["finan_estimado"]:,.2f}</p>', unsafe_allow_html=True)
            fgts_u = st.number_input("FGTS + Subsídio (R$)", value=float(d['fgts_sub']))
            st.markdown(f'<p class="inline-ref">Ref. Estimado: R$ {d["fgts_sub"]:,.2f}</p>', unsafe_allow_html=True)
            
            ps_max = u['Valor de Venda'] * d['perc_ps']
            ps_u = st.number_input("Pro Soluto (R$)", value=float(ps_max))
            st.markdown(f'<p class="inline-ref">Limite {int(d["perc_ps"]*100)}%: R$ {ps_max:,.2f}</p>', unsafe_allow_html=True)
            
            parc = st.number_input("Parcelas PS", min_value=1, max_value=d['prazo_ps'], value=d['prazo_ps'])
            v_parc = ps_u / parc
            comp = v_parc / d['renda']
            saldo = u['Valor de Venda'] - f_u - fgts_u - ps_u
            
            st.markdown(f"""
                <div class="fin-box" style="border-top: 5px solid #64748b;"><b>Imóvel:</b> R$ {u['Valor de Venda']:,.2f}</div>
                <div class="fin-box" style="background:#f8fafc; border-top: 5px solid #2563eb;"><b>Parcela PS:</b> R$ {v_parc:,.2f} ({comp*100:.1f}% da Renda)</div>
            """, unsafe_allow_html=True)
            
            if comp > d['limit_ps_renda']:
                st.warning(f"⚠️ Atenção: Parcela ultrapassa o limite de {d['limit_ps_renda']*100:.0f}% da renda.")

            st.markdown(f'<div class="fin-box" style="background:#fff1f2; border-top: 5px solid #e11d48;"><b>Saldo Entrada:</b> R$ {max(0, saldo):,.2f}</div>', unsafe_allow_html=True)
            
            if saldo > 0:
                st.markdown("#### 🖋️ Parcelamento da Entrada")
                st.number_input("Ato (R$)", value=saldo/4, key="a1")
                st.number_input("30 dias (R$)", value=saldo/4, key="a2")
                st.number_input("60 dias (R$)", value=saldo/4, key="a3")
                st.number_input("90 dias (R$)", value=saldo/4, key="a4")
        
        st.markdown("---")
        if st.button("⬅️ Voltar", use_container_width=True): st.session_state.passo_simulacao = 'guide'; st.rerun()
        if st.button("👤 Novo Cliente", use_container_width=True): st.session_state.passo_simulacao = 'input'; st.rerun()

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()
    if df_finan.empty or df_estoque.empty:
        st.warning("⚠️ Aguardando permissão de acesso às planilhas. Verifique o guia de configuração.")
        st.stop()
    st.markdown('<div class="header-container"><div class="header-title">SIMULADOR DIRECIONAL V2</div></div>', unsafe_allow_html=True)
    aba_simulador_automacao(df_finan, df_estoque, df_politicas)

if __name__ == "__main__":
    main()
