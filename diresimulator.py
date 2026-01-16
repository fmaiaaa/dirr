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

Versão: 8.4 (Design Full Width - Ocupando toda a lateralidade)
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
    bairros_mock = ['Recreio', 'Jacarepaguá', 'Campo Grande', 'São Gonçalo', 'Itaboraí', 'Niterói', 'Caxias', 'Nova Iguaçu', 'Bangu', 'Santa Cruz']
    data_estoque = {
        'Identificador': [f'BL{i:02d}-{j:03d}' for i in range(1, 11) for j in [101, 102, 201, 202, 301, 302, 401, 402]],
        'Empreendimento': [
            'Conquista Oceânica', 'Viva Vida Recanto Clube', 'Conquista Florianópolis', 
            'Direcional Conquista Max Norte', 'Conquista Norte Clube', 'Nova Caxias Up',
            'Residencial Jerivá', 'Conquista Itanhangá Green', 'Viva Vida Realengo', 'Vert Alcântara'
        ] * 8,
        'Bairro': bairros_mock * 8,
        'Valor de Venda': np.random.randint(195000, 345000, 80),
        'Status': ['Disponível'] * 75 + ['Reservado'] * 5
    }
    df_estoque = pd.DataFrame(data_estoque)
    df_estoque['Andar'] = df_estoque['Identificador'].apply(lambda x: int(x.split('-')[-1]) // 100)
    
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
        
        /* Ocupar toda a lateralidade */
        .block-container {
            max-width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-top: 1rem !important;
            margin: 0 !important;
        }

        .header-container { text-align: center; padding: 25px 0; background: #ffffff; border-bottom: 1px solid #e2e8f0; margin-bottom: 25px; border-radius: 0 0 15px 15px; width: 100%; }
        .header-title { color: #0f172a; font-size: 2rem; font-weight: 700; margin: 0; }
        
        .card { background: white; padding: 25px; border-radius: 18px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; width: 100%; }
        .recommendation-card { border-left: 5px solid #2563eb; background: #f8fafc; padding: 15px; border-radius: 12px; margin-bottom: 10px; text-align: center; width: 100%; }
        .price-tag { color: #2563eb; font-weight: 700; font-size: 1.1rem; }
        
        .metric-label { color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; text-align: center; width: 100%; }
        .metric-value { color: #1e293b; font-size: 1.2rem; font-weight: 700; text-align: center; width: 100%; }
        
        .emp-badge {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            padding: 8px 15px;
            border-radius: 30px;
            display: inline-block;
            margin: 5px;
            font-size: 0.9rem;
            color: #334155;
            font-weight: 500;
        }

        .stButton button { border-radius: 10px !important; padding: 12px !important; font-weight: 600 !important; width: 100%; }
        h1, h2, h3, h4 { text-align: center !important; width: 100%; }
        
        /* Box Financeiro Personalizado */
        .fin-box {
            text-align: center;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #e2e8f0;
            margin-bottom: 15px;
            width: 100%;
        }

        .inline-ref {
            font-size: 0.8rem;
            color: #64748b;
            margin-top: -12px;
            margin-bottom: 12px;
            font-weight: 500;
            text-align: left;
        }

        /* Centralização de Abas (Mantida para navegação) */
        div[data-baseweb="tab-list"] {
            justify-content: center !important;
            display: flex !important;
        }
        
        /* Forçar inputs a ocuparem largura total */
        div[data-testid="stForm"] { width: 100% !important; }
        .stTextInput, .stNumberInput, .stSelectbox, .stMultiSelect { width: 100% !important; }
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

    # --- PASSO 1: ENTRADA DE DADOS ---
    if st.session_state.passo_simulacao == 'input':
        st.markdown("### 👤 Etapa 1: Dados do Cliente")
        # Removido colunas laterais para ocupar toda a largura
        nome = st.text_input("Nome do Cliente", value=st.session_state.dados_cliente.get('nome', ""))
        renda = st.number_input("Renda Bruta Familiar (R$)", min_value=1500.0, value=st.session_state.dados_cliente.get('renda', 3500.0), step=100.0)
        
        ranking_options = [r for r in df_politicas['CLASSIFICAÇÃO'].unique() if r != 'EMCASH']
        ranking = st.selectbox("Ranking do Cliente", options=ranking_options, index=1)
        politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"])
        
        social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False))
        cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True))
        
        st.write("")
        if st.button("🚀 Avançar para Visão Financeira", type="primary"):
            finan, fgts = motor.obter_enquadramento(renda, social, cotista)
            perc = df_politicas.loc[df_politicas['CLASSIFICAÇÃO'] == ('EMCASH' if politica_ps == "Emcash" else ranking), 'PERC_PS'].values[0]
            
            st.session_state.dados_cliente = {
                'nome': nome, 'renda': renda, 'social': social, 'cotista': cotista,
                'ranking': ranking, 'politica': politica_ps, 'perc_ps': perc,
                'finan_estimado': finan, 'fgts_sub': fgts
            }
            st.session_state.passo_simulacao = 'potential'
            st.rerun()

    # --- PASSO 2: POTENCIAL DE COMPRA ---
    elif st.session_state.passo_simulacao == 'potential':
        d = st.session_state.dados_cliente
        st.markdown(f"### 💰 Etapa 2: Potencial de Compra - {d['nome'] or 'Cliente'}")
        
        ps_min_total = df_estoque['Valor de Venda'].min() * d['perc_ps']
        ps_max_total = df_estoque['Valor de Venda'].max() * d['perc_ps']
        dobro_renda = 2 * d['renda']
        
        pot_min = d['finan_estimado'] + d['fgts_sub'] + ps_min_total + dobro_renda
        pot_max = d['finan_estimado'] + d['fgts_sub'] + ps_max_total + dobro_renda
        
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="card"><p class="metric-label">Financiamento Aprovado</p><p class="metric-value">R$ {d["finan_estimado"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="card"><p class="metric-label">FGTS + Subsídio</p><p class="metric-value">R$ {d["fgts_sub"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="card"><p class="metric-label">Pro Soluto (Min - Max)</p><p class="metric-value">R$ {ps_min_total:,.0f} - {ps_max_total:,.0f}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><p class="metric-label">Dobro da Renda</p><p class="metric-value">R$ {dobro_renda:,.2f}</p></div>', unsafe_allow_html=True)

        # Ocupar toda a largura
        st.markdown(f"""
            <div class="card" style="border-top: 5px solid #2563eb; text-align: center; background: #f0f7ff;">
                <p class="metric-label" style="color: #2563eb; font-size: 1.1rem;">Valor Potencial de Compra</p>
                <p class="metric-value" style="font-size: 2.2rem; color: #0f172a; margin-bottom:5px;">R$ {pot_min:,.2f} a R$ {pot_max:,.2f}</p>
                <p style="margin:0; font-size:0.85rem; color:#475569;">O valor potencial varia de acordo com o preço da unidade escolhida.</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏢 Visualizar Produtos Viáveis", type="primary"):
            st.session_state.passo_simulacao = 'guide'
            st.rerun()
        st.write("")
        if st.button("⬅️ Editar Dados do Cliente"):
            st.session_state.passo_simulacao = 'input'
            st.rerun()

    # --- PASSO 3: GUIA DE VIABILIDADE ---
    elif st.session_state.passo_simulacao == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### 🔍 Etapa 3: Guia de Viabilidade")
        
        df_viaveis = motor.filtrar_unidades_viaveis(d['renda'], d['finan_estimado'], d['fgts_sub'], d['perc_ps'])
        
        if df_viaveis.empty:
            st.error("❌ Nenhuma unidade viável encontrada.")
            if st.button("⬅️ Voltar"): 
                st.session_state.passo_simulacao = 'potential'
                st.rerun()
        else:
            st.markdown("#### 🏢 Empreendimentos com unidades disponíveis para este perfil:")
            empreendimentos_unid = df_viaveis.groupby('Empreendimento').size().to_dict()
            badges_html = "".join([f'<div class="emp-badge">{emp} ({qtd} unid.)</div>' for emp, qtd in empreendimentos_unid.items()])
            st.markdown(f'<div style="text-align: center; margin-bottom: 20px;">{badges_html}</div>', unsafe_allow_html=True)

            tab_rec, tab_list = st.tabs(["⭐ Unidades Recomendadas", "📋 Lista Completa de Unidades"])

            with tab_rec:
                emp_opcoes = ["Todos"] + sorted(df_viaveis['Empreendimento'].unique().tolist())
                emp_rec = st.selectbox("Filtrar Recomendações:", options=emp_opcoes, key="sel_rec_3")
                
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
                    with c_r1: st.markdown(f'<div class="recommendation-card" style="border-color:#2563eb;"><small>IDEAL (100%)</small><br><b>{r100["Identificador"]}</b><br><small>{r100["Empreendimento"]}</small><br><span class="price-tag">R$ {r100["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c_r2: st.markdown(f'<div class="recommendation-card" style="border-color:#f59e0b;"><small>SEGURA (90%)</small><br><b>{r90["Identificador"]}</b><br><small>{r90["Empreendimento"]}</small><br><span class="price-tag">R$ {r90["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c_r3: st.markdown(f'<div class="recommendation-card" style="border-color:#10b981;"><small>FACILITADA (75%)</small><br><b>{r75["Identificador"]}</b><br><small>{r75["Empreendimento"]}</small><br><span class="price-tag">R$ {r75["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                
                st.write("")
                if st.button("💰 Prosseguir para Fechamento Financeiro", type="primary"):
                    st.session_state.passo_simulacao = 'payment_flow'
                    st.rerun()

            with tab_list:
                f1, f2, f3, f4, f5 = st.columns([1.2, 1, 0.8, 1, 0.8])
                with f1: f_emp = st.multiselect("Empreendimento:", options=sorted(df_viaveis['Empreendimento'].unique()), key="f3_emp")
                with f2: f_bairro = st.multiselect("Bairro:", options=sorted(df_viaveis['Bairro'].unique()), key="f3_bairro")
                with f3: f_andar = st.multiselect("Andar:", options=sorted(df_viaveis['Andar'].unique()), key="f3_andar")
                with f4: f_ordem = st.selectbox("Ordenar por Valor:", ["Maior Preço", "Menor Preço"], key="f3_ordem")
                with f5: f_pmax = st.number_input("Preço Máximo:", value=float(df_viaveis['Valor de Venda'].max()), key="f3_pmax")
                df_tab = df_viaveis.copy()
                if f_emp: df_tab = df_tab[df_tab['Empreendimento'].isin(f_emp)]
                if f_bairro: df_tab = df_tab[df_tab['Bairro'].isin(f_bairro)]
                if f_andar: df_tab = df_tab[df_tab['Andar'].isin(f_andar)]
                df_tab = df_tab[df_tab['Valor de Venda'] <= f_pmax]
                df_tab = df_tab.sort_values('Valor de Venda', ascending=(f_ordem == "Menor Preço"))
                st.dataframe(df_tab[['Identificador', 'Empreendimento', 'Bairro', 'Andar', 'Valor de Venda', 'PS_Unidade', 'Poder_Compra']], use_container_width=True, hide_index=True)

            st.write("")
            if st.button("⬅️ Voltar ao Potencial"): 
                st.session_state.passo_simulacao = 'potential'
                st.rerun()

    # --- PASSO 4: SELEÇÃO DEFINITIVA E FLUXO DE PAGAMENTO ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### 📑 Etapa 4: Detalhamento do Fluxo")
        
        st.subheader("✅ Seleção da Unidade")
        emp_def = st.selectbox("Empreendimento Escolhido:", options=sorted(df_estoque['Empreendimento'].unique()))
        unidades_def = df_estoque[(df_estoque['Empreendimento'] == emp_def) & (df_estoque['Status'] == 'Disponível')]
        uni_def = st.selectbox("Unidade definitiva:", options=unidades_def['Identificador'].unique())
        u = unidades_def[unidades_def['Identificador'] == uni_def].iloc[0]
        
        st.markdown("---")
        st.subheader("💰 Configuração Financeira")
        
        f_usado = st.number_input("Financiamento a utilizar (R$)", value=float(d['finan_estimado']))
        st.markdown(f'<p class="inline-ref">Ref. (Aprovado): R$ {d["finan_estimado"]:,.2f}</p>', unsafe_allow_html=True)
        
        fgts_usado = st.number_input("FGTS + Subsídio a utilizar (R$)", value=float(d['fgts_sub']))
        st.markdown(f'<p class="inline-ref">Ref. (Estimado): R$ {d["fgts_sub"]:,.2f}</p>', unsafe_allow_html=True)
        
        ps_max_real = u['Valor de Venda'] * d['perc_ps']
        ps_usado = st.number_input("Pro Soluto a utilizar (R$)", value=float(ps_max_real))
        st.markdown(f'<p class="inline-ref">Ref. (Máximo Permitido): R$ {ps_max_real:,.2f}</p>', unsafe_allow_html=True)
        
        parc_ps = st.number_input("Quantidade de Parcelas Pro Soluto", min_value=1, max_value=84, value=84)

        # Métricas Financeiras
        v_parc = ps_usado / parc_ps
        p_renda = (v_parc / d['renda']) * 100
        saldo_entrada = u['Valor de Venda'] - f_usado - fgts_usado - ps_usado
        
        st.write("")
        ci1, ci2, ci3 = st.columns(3)
        
        with ci1:
            st.markdown(f"""
                <div class="fin-box" style="background: #ffffff; border-top: 5px solid #64748b;">
                    <p class="metric-label" style="color: #64748b;">Valor do Imóvel</p>
                    <p class="metric-value" style="font-size: 1.2rem; margin-bottom: 0;">R$ {u['Valor de Venda']:,.2f}</p>
                    <p style="margin:0; font-size:0.8rem; font-weight:600; color:#94a3b8;">({u['Identificador']})</p>
                </div>
            """, unsafe_allow_html=True)

        with ci2:
            st.markdown(f"""
                <div class="fin-box" style="background: #f8fafc; border-top: 5px solid #2563eb;">
                    <p class="metric-label" style="color: #2563eb;">Parcelamento PS</p>
                    <p class="metric-value" style="font-size: 1.2rem; margin-bottom: 0;">R$ {v_parc:,.2f}</p>
                    <p style="margin:0; font-size:0.8rem; font-weight:600; color:#475569;">({p_renda:.2f}% da Renda)</p>
                </div>
            """, unsafe_allow_html=True)

        with ci3:
            st.markdown(f"""
                <div class="fin-box" style="background: #fff1f2; border-top: 5px solid #e11d48;">
                    <p class="metric-label" style="color: #e11d48;">Saldo Entrada</p>
                    <p class="metric-value" style="font-size: 1.2rem; margin-bottom: 0;">R$ {max(0, saldo_entrada):,.2f}</p>
                    <p style="margin:0; font-size:0.8rem; font-weight:600; color:#475569;">(Ato / 30 / 60 / 90)</p>
                </div>
            """, unsafe_allow_html=True)
        
        if saldo_entrada > 0:
            st.markdown("#### 🖋️ Parcelamento da Entrada")
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1: st.number_input("Ato (R$)", value=saldo_entrada/4, key="ato_v8")
            with sc2: st.number_input("30d (R$)", value=saldo_entrada/4, key="ato30_v8")
            with sc3: st.number_input("60d (R$)", value=saldo_entrada/4, key="ato60_v8")
            with sc4: st.number_input("90d (R$)", value=saldo_entrada/4, key="ato90_v8")
        
        st.markdown("---")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("⬅️ Voltar para Guia"):
                st.session_state.passo_simulacao = 'guide'
                st.rerun()
        with col_b2:
            if st.button("👤 Mudar Cliente"):
                st.session_state.passo_simulacao = 'input'
                st.rerun()

# =============================================================================
# 5. MAIN
# =============================================================================

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()

    st.markdown("""
        <div class="header-container">
            <div class="header-title">SIMULADOR DIRECIONAL V2</div>
            <div class="header-subtitle">Fluxo de Vendas e Recomendação de Estoque</div>
        </div>
    """, unsafe_allow_html=True)

    aba_simulador_automacao(df_finan, df_estoque, df_politicas)

if __name__ == "__main__":
    main()
