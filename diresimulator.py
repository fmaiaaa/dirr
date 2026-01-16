# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V2
=============================================================================
Fluxo Automatizado de Recomendação (Sequencial):
1. Etapa 1: Entrada de dados do cliente.
2. Etapa 2: Valor Potencial de Compra (Intervalo de Pro Soluto).
3. Etapa 3: Guia de Viabilidade (Visualização e Recomendações).
4. Etapa 4: Fechamento Financeiro (Seleção e Fluxo de Pagamento).

Versão: 15.0 (Conexão Privada GSheets - Mapeamento Direcional Completo)
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# =============================================================================
# 0. CONSTANTES DE ACESSO (IDs DAS PLANILHAS REAIS)
# =============================================================================
ID_PLANILHA_MESTRA = "1wJD3tXe1e8FxL4mVEfNKGdtaS__Dl4V6-sm1G6qfL0s" # Financiamento
ID_PLANILHA_RANKING = "1N00McOjO1O_MuKyQhp-CVhpAet_9Lfq-VqVm1FmPV00" # Ranking
ID_PLANILHA_ESTOQUE = "1VG-hgBkddyssN1OXgIA33CVsKGAdqT-5kwbgizxWDZQ" # Estoque Direcional

# URLs para o conector privado
URL_FINAN = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA_MESTRA}/edit#gid=0"
URL_RANKING = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA_RANKING}/edit#gid=0"
URL_ESTOQUE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA_ESTOQUE}/edit"

# =============================================================================
# 1. CARREGAMENTO E TRATAMENTO DE DADOS
# =============================================================================

@st.cache_data(ttl=600) # Cache de 10 minutos para performance
def carregar_dados_sistema():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)

        # 1.1 Carregar Ranking
        df_politicas_raw = conn.read(spreadsheet=URL_RANKING)
        df_politicas = df_politicas_raw.rename(columns={
            'FAIXA RENDA': 'FAIXA_RENDA',
            'FX RENDA 1': 'FX_RENDA_1',
            'FX RENDA 2': 'FX_RENDA_2',
            'DT POLÍTICA': 'DT_POLITICA'
        })

        # Limpeza de Percentuais (ex: "25%" -> 0.25)
        def limpar_porcentagem(val):
            if isinstance(val, str):
                return float(val.replace('%', '').replace(',', '.')) / 100
            return val

        for col in ['PROSOLUTO', 'FX_RENDA_1', 'FX_RENDA_2']:
            if col in df_politicas.columns:
                df_politicas[col] = df_politicas[col].apply(limpar_porcentagem)

        # 1.2 Carregar Financiamento
        df_finan = conn.read(spreadsheet=URL_FINAN)

        # 1.3 Carregar Estoque e Mapear Colunas Direcional
        df_raw_estoque = conn.read(spreadsheet=URL_ESTOQUE)
        df_estoque = df_raw_estoque.rename(columns={
            'Nome do Empreendimento': 'Empreendimento',
            'VALOR DE VENDA': 'Valor de Venda',
            'Status da unidade': 'Status'
        })
        
        # Garantir que as colunas básicas existam
        if 'Bairro' not in df_estoque.columns:
            df_estoque['Bairro'] = "Não Informado"
        
        # Extração de Andar (Baseado no final do Identificador)
        df_estoque['Andar'] = df_estoque['Identificador'].apply(
            lambda x: int(str(x).split('-')[-1]) // 100 if '-' in str(x) else 0
        )
        
        return df_finan, df_estoque, df_politicas
    
    except Exception as e:
        st.error(f"Erro de Acesso: Verifique as credenciais nos Secrets.")
        st.info(f"Detalhes técnicos: {e}")
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
        if self.df_finan.empty: return 0, 0
        idx = (self.df_finan['Renda'] - renda).abs().idxmin()
        row = self.df_finan.iloc[idx]
        
        s_suf = 'Sim' if social else 'Nao'
        c_suf = 'Sim' if cotista else 'Nao'
        
        # Formato da planilha enviado pelo usuário: Finan_Social_Sim_Cotista_Sim
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
        .block-container { max-width: 1200px !important; padding-left: 1rem !important; padding-right: 1rem !important; margin: auto !important; }
        .header-container { text-align: center; padding: 25px 0; background: #ffffff; border-bottom: 1px solid #e2e8f0; margin-bottom: 25px; border-radius: 0 0 15px 15px; }
        .header-title { color: #0f172a; font-size: 2rem; font-weight: 700; margin: 0; }
        .card { background: white; padding: 20px; border-radius: 18px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; width: 100%; min-height: 120px; height: auto !important; display: flex; flex-direction: column; justify-content: center; overflow: visible; }
        .recommendation-card { background: #ffffff; padding: 20px; border: 1px solid #e2e8f0; border-top: 5px solid #2563eb; border-radius: 12px; margin-bottom: 15px; text-align: center; min-height: 160px; height: auto !important; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); overflow: visible; }
        .thin-card { background: white; padding: 12px 20px; border-radius: 10px; border: 1px solid #e2e8f0; border-left: 5px solid #64748b; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; width: 100%; }
        .price-tag { color: #2563eb; font-weight: 700; font-size: 1.1rem; }
        .metric-label { color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; text-align: center; width: 100%; }
        .metric-value { color: #1e293b; font-size: 1.2rem; font-weight: 700; text-align: center; width: 100%; }
        .stButton button { border-radius: 10px !important; padding: 10px !important; font-weight: 600 !important; }
        h1, h2, h3, h4 { text-align: center !important; width: 100%; }
        .fin-box { text-align: center; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; margin-bottom: 15px; width: 100%; height: auto !important; }
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
            ranking_options = [r for r in df_politicas['CLASSIFICAÇÃO'].unique() if r != 'EMCASH']
            ranking = st.selectbox("Ranking do Cliente", options=ranking_options, index=1)
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
        with m3: st.markdown(f'<div class="card"><p class="metric-label">PS (Estimado)</p><p class="metric-value">R$ {ps_min_total:,.0f}-{ps_max_total:,.0f}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><p class="metric-label">Capacidade Entrada</p><p class="metric-value">R$ {dobro_renda:,.2f}</p></div>', unsafe_allow_html=True)

        st.markdown(f"""
            <div class="card" style="border-top: 5px solid #2563eb; text-align: center; background: #f0f7ff; min-height: auto; padding: 30px;">
                <p class="metric-label" style="color: #2563eb; font-size: 1.1rem;">Valor Potencial de Compra Estimado</p>
                <p class="metric-value" style="font-size: 2.2rem; color: #0f172a; margin-bottom:5px;">R$ {pot_min:,.2f} a R$ {pot_max:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏢 Visualizar Produtos Viáveis", type="primary", use_container_width=True):
            st.session_state.passo_simulacao = 'guide'
            st.rerun()
        st.write("")
        if st.button("⬅️ Editar Dados", use_container_width=True):
            st.session_state.passo_simulacao = 'input'
            st.rerun()

    # --- ETAPA 3 ---
    elif st.session_state.passo_simulacao == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### 🔍 Etapa 3: Guia de Viabilidade")
        df_viaveis = motor.filtrar_unidades_viaveis(d['renda'], d['finan_estimado'], d['fgts_sub'], d['perc_ps'])
        
        if df_viaveis.empty:
            st.error("❌ Nenhuma unidade viável encontrada.")
            if st.button("⬅️ Voltar", use_container_width=True): st.session_state.passo_simulacao = 'potential'; st.rerun()
        else:
            with st.expander("🏢 Ver Empreendimentos Disponíveis", expanded=False):
                empreendimentos_unid = df_viaveis.groupby('Empreendimento').size().to_dict()
                for emp, qtd in empreendimentos_unid.items():
                    st.markdown(f'<div class="thin-card"><div><b>{emp}</b></div><div>{qtd} unidades</div></div>', unsafe_allow_html=True)

            tab_rec, tab_list = st.tabs(["⭐ Recomendações", "📋 Lista Completa"])
            with tab_rec:
                emp_rec = st.selectbox("Filtrar por Empreendimento:", options=["Todos"] + sorted(df_viaveis['Empreendimento'].unique().tolist()))
                df_rec = df_viaveis if emp_rec == "Todos" else df_viaveis[df_viaveis['Empreendimento'] == emp_rec]
                df_rec = df_rec.sort_values('Valor de Venda', ascending=False)
                if not df_rec.empty:
                    max_p = df_rec['Poder_Compra'].max()
                    def rec(pct):
                        lim = max_p * pct
                        cands = df_rec[df_rec['Valor de Venda'] <= lim]
                        return cands.iloc[0] if not cands.empty else df_rec.iloc[-1]
                    r100, r90, r75 = rec(1.0), rec(0.9), rec(0.75)
                    c_r1, c_r2, c_r3 = st.columns(3)
                    with c_r1: st.markdown(f'<div class="recommendation-card" style="border-top-color:#2563eb;"><b>IDEAL</b><br>{r100["Identificador"]}<br><span class="price-tag">R$ {r100["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c_r2: st.markdown(f'<div class="recommendation-card" style="border-top-color:#f59e0b;"><b>SEGURA</b><br>{r90["Identificador"]}<br><span class="price-tag">R$ {r90["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c_r3: st.markdown(f'<div class="recommendation-card" style="border-top-color:#10b981;"><b>FACILITADA</b><br>{r75["Identificador"]}<br><span class="price-tag">R$ {r75["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                
                st.markdown("---")
                if st.button("💰 Ir para Fechamento", type="primary", use_container_width=True):
                    st.session_state.passo_simulacao = 'payment_flow'; st.rerun()
                st.write("")
                if st.button("⬅️ Voltar ao Potencial", use_container_width=True): 
                    st.session_state.passo_simulacao = 'potential'; st.rerun()

            with tab_list:
                f1, f2, f3, f4, f5 = st.columns([1.2, 1, 0.8, 1, 0.8])
                with f1: f_emp = st.multiselect("Empreendimento:", options=sorted(df_viaveis['Empreendimento'].unique()))
                with f2: f_bairro = st.multiselect("Bairro:", options=sorted(df_viaveis['Bairro'].unique()))
                with f3: f_andar = st.multiselect("Andar:", options=sorted(df_viaveis['Andar'].unique()))
                with f4: f_ordem = st.selectbox("Ordenar:", ["Maior Preço", "Menor Preço"])
                with f5: f_pmax = st.number_input("Preço Máx:", value=float(df_viaveis['Valor de Venda'].max()))
                df_tab = df_viaveis.copy()
                if f_emp: df_tab = df_tab[df_tab['Empreendimento'].isin(f_emp)]
                if f_bairro: df_tab = df_tab[df_tab['Bairro'].isin(f_bairro)]
                if f_andar: df_tab = df_tab[df_tab['Andar'].isin(f_andar)]
                df_tab = df_tab[df_tab['Valor de Venda'] <= f_pmax]
                df_tab = df_tab.sort_values('Valor de Venda', ascending=(f_ordem == "Menor Preço"))
                st.dataframe(df_tab[['Identificador', 'Empreendimento', 'Bairro', 'Andar', 'Valor de Venda', 'PS_Unidade', 'Poder_Compra']], use_container_width=True, hide_index=True)

    # --- ETAPA 4 ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### 📑 Etapa 4: Fechamento Financeiro")
        emp_def = st.selectbox("Empreendimento Escolhido:", options=sorted(df_estoque['Empreendimento'].unique()))
        unidades_def = df_estoque[(df_estoque['Empreendimento'] == emp_def) & (df_estoque['Status'] == 'Disponível')]
        
        if not unidades_def.empty:
            uni_def = st.selectbox("Unidade definitiva:", options=unidades_def['Identificador'].unique())
            u = unidades_def[unidades_def['Identificador'] == uni_def].iloc[0]
            
            f_usado = st.number_input("Financiamento (R$)", value=float(d['finan_estimado']))
            st.markdown(f'<p class="inline-ref">Ref. (Aprovado): R$ {d["finan_estimado"]:,.2f}</p>', unsafe_allow_html=True)
            fgts_usado = st.number_input("FGTS + Subsídio (R$)", value=float(d['fgts_sub']))
            st.markdown(f'<p class="inline-ref">Ref. (Estimado): R$ {d["fgts_sub"]:,.2f}</p>', unsafe_allow_html=True)
            
            ps_max_real = u['Valor de Venda'] * d['perc_ps']
            ps_usado = st.number_input("Pro Soluto (R$)", value=float(ps_max_real))
            st.markdown(f'<p class="inline-ref">Ref. (Máx {int(d["perc_ps"]*100)}%): R$ {ps_max_real:,.2f}</p>', unsafe_allow_html=True)
            parc_ps = st.number_input("Parcelas PS", min_value=1, max_value=d['prazo_ps'], value=d['prazo_ps'])

            v_parc = ps_usado / parc_ps
            comp_renda = v_parc / d['renda']
            saldo_entrada = u['Valor de Venda'] - f_usado - fgts_usado - ps_usado
            
            st.markdown(f"""
                <div class="fin-box" style="border-top-color:#64748b;"><b>Imóvel:</b> R$ {u['Valor de Venda']:,.2f}</div>
                <div class="fin-box" style="background:#f8fafc; border-top-color:#2563eb;"><b>Parcela PS:</b> R$ {v_parc:,.2f} ({comp_renda*100:.1f}% da Renda)</div>
                <div class="fin-box" style="background:#fff1f2; border-top-color:#e11d48;"><b>Saldo Entrada:</b> R$ {max(0, saldo_entrada):,.2f}</div>
            """, unsafe_allow_html=True)
            
            if saldo_entrada > 0:
                st.markdown("#### 🖋️ Parcelamento da Entrada")
                st.number_input("Valor Ato (R$)", value=saldo_entrada/4, key="ato1")
                st.number_input("Ato 30d (R$)", value=saldo_entrada/4, key="ato2")
                st.number_input("Ato 60d (R$)", value=saldo_entrada/4, key="ato3")
                st.number_input("Ato 90d (R$)", value=saldo_entrada/4, key="ato4")
        
        st.markdown("---")
        if st.button("⬅️ Voltar para Guia", use_container_width=True): st.session_state.passo_simulacao = 'guide'; st.rerun()
        st.write("")
        if st.button("👤 Novo Cliente", use_container_width=True): st.session_state.passo_simulacao = 'input'; st.rerun()

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()
    if df_finan.empty or df_estoque.empty: st.stop()
    st.markdown('<div class="header-container"><div class="header-title">SIMULADOR DIRECIONAL V2</div></div>', unsafe_allow_html=True)
    aba_simulador_automacao(df_finan, df_estoque, df_politicas)

if __name__ == "__main__":
    main()
