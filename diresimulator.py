# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V2
=============================================================================
Aplicação profissional para corretores:
- Enquadramento automático de financiamento (Tabelas Direcional).
- Gestão de estoque e filtros avançados.
- Simulação de Pro Soluto (PS) com validação de políticas.
- Geração de fluxo de pagamento detalhado.

Versão: 2.6 (Fluxo de Entrada de Dados Otimizado)
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# =============================================================================
# 1. CONFIGURAÇÕES E DADOS (MOCK - PREPARADO PARA TABELAS REAIS)
# =============================================================================

def carregar_dados_sistema():
    # MOCK: TABELA FINANCIAMENTOS (Será substituída por pd.read_csv futuramente)
    rendas = np.arange(1700, 12100, 100)
    data_finan = []
    for r in rendas:
        data_finan.append({
            'Renda': r,
            'F2_N_N': r * 55, # Faixa 2, Social Não, Cotista Não
            'F2_S_N': r * 58, # Faixa 2, Social Sim, Cotista Não
            'F2_N_S': r * 62, # Faixa 2, Social Não, Cotista Sim
            'F2_S_S': r * 65, # Faixa 2, Social Sim, Cotista Sim
            'F3_Geral': r * 45,
            'Subsidio_Base': 55000 if r < 2000 else (20000 if r < 4000 else 0)
        })
    df_finan = pd.DataFrame(data_finan)

    # MOCK: BASE ESTOQUE
    data_estoque = {
        'Identificador': [f'BL{i:02d}-0{j:02d}' for i in range(1, 6) for j in range(1, 6)],
        'Empreendimento': ['Viva Vida Recanto Clube', 'Conquista Oceânica', 'Residencial Jerivá', 'Nova Caxias Up', 'BeON Porto'] * 5,
        'Valor de Venda': np.random.randint(210000, 360000, 25),
        'Status': ['Disponível'] * 20 + ['Reservado'] * 5
    }
    df_estoque = pd.DataFrame(data_estoque)
    
    # MOCK: POLITICAS
    df_politicas = pd.DataFrame({
        'CLASSIFICAÇÃO': ['EMCASH', 'DIAMANTE', 'OURO', 'PRATA', 'BRONZE', 'AÇO'],
        'MAX_PS': [0.25, 0.25, 0.20, 0.18, 0.15, 0.10],
        'PARCELAS': [66, 84, 84, 84, 80, 60]
    })
    
    return df_finan, df_estoque, df_politicas

# =============================================================================
# 2. MOTOR DE CÁLCULO (LÓGICA FUNCIONAL)
# =============================================================================

class MotorVendas:
    def __init__(self, df_finan, df_politicas):
        self.df_finan = df_finan
        self.df_politicas = df_politicas

    def obter_financiamento(self, renda, social, cotista):
        """Retorna financiamento e subsídio sugeridos com base na renda e flags."""
        idx = (self.df_finan['Renda'] - renda).abs().idxmin()
        row = self.df_finan.iloc[idx]
        
        s_key = 'S' if social else 'N'
        c_key = 'S' if cotista else 'N'
        col = f"F2_{s_key}_{c_key}"
        
        valor = row[col] if renda <= 4700 else row['F3_Geral']
        subsidio = row['Subsidio_Base'] if renda <= 4700 else 0
        
        return float(valor), float(subsidio)

    def calcular_simulacao(self, valor_unidade, finan, fgts_sub, classif):
        """Calcula o GAP, Pro Soluto e necessidade de Ato."""
        gap = valor_unidade - finan - fgts_sub
        pol = self.df_politicas[self.df_politicas['CLASSIFICAÇÃO'] == classif].iloc[0]
        
        ps_max = valor_unidade * pol['MAX_PS']
        excedente_ato = max(0, gap - ps_max)
        valor_ps = min(gap, ps_max)
        
        return {
            'gap': max(0, gap),
            'ps_financiado': max(0, valor_ps),
            'ato_complementar': excedente_ato,
            'parcelas': pol['PARCELAS'],
            'mensal': max(0, valor_ps) / pol['PARCELAS'] if valor_ps > 0 else 0
        }

# =============================================================================
# 3. INTERFACE E DESIGN (CSS PREMIUM)
# =============================================================================

def configurar_layout():
    st.set_page_config(page_title="Simulador Direcional", page_icon="🏢", layout="wide")
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        * { font-family: 'Inter', sans-serif; }
        .main { background-color: #f4f7f9; }
        
        /* Cabeçalho */
        .header-container { text-align: center; padding: 30px 0; background: #ffffff; border-bottom: 1px solid #e0e6ed; margin-bottom: 30px; border-radius: 0 0 20px 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
        .header-title { color: #1e293b; font-size: 2.2rem; font-weight: 700; margin-bottom: 5px; }
        .header-subtitle { color: #64748b; font-size: 1rem; }

        /* Cards Informativos */
        .metric-card { background: white; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03); text-align: center; }
        .metric-label { color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 10px; }
        .metric-value { color: #0f172a; font-size: 1.5rem; font-weight: 700; }
        
        /* Status Badges */
        .status-ok { color: #10b981; background: #ecfdf5; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
        .status-warning { color: #f59e0b; background: #fffbeb; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }

        /* Formulários e Botões */
        .stButton button { width: 100%; background: #2563eb !important; color: white !important; border-radius: 10px !important; padding: 12px !important; font-weight: 600 !important; border: none !important; transition: 0.3s; }
        .stButton button:hover { background: #1d4ed8 !important; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); }
        
        div[data-baseweb="tab-list"] { justify-content: center; gap: 20px; border-bottom: none; }
        div[data-baseweb="tab"] { background: transparent; color: #94a3b8; font-weight: 600; padding: 10px 25px; }
        div[aria-selected="true"] { color: #2563eb !important; border-bottom: 3px solid #2563eb !important; }
        
        /* Enquadramento Box */
        .enquadramento-box {
            background: #f8fafc;
            padding: 15px;
            border-radius: 12px;
            border: 1px dashed #cbd5e1;
            margin-top: 15px;
        }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 4. COMPONENTES DE ABA
# =============================================================================

def aba_painel_vendas(df_finan, df_estoque, df_politicas):
    motor = MotorVendas(df_finan, df_politicas)
    
    col_input, col_result = st.columns([1, 1.2], gap="large")
    
    with col_input:
        st.markdown("### 📝 Dados do Cliente")
        with st.container():
            st.markdown('<div style="background: white; padding: 25px; border-radius: 20px; border: 1px solid #e2e8f0;">', unsafe_allow_html=True)
            
            nome_cliente = st.text_input("Nome Completo", placeholder="Nome do Cliente")
            renda_familiar = st.number_input("Renda Familiar Bruta (R$)", min_value=1700.0, value=3500.0, step=100.0)
            
            c1, c2 = st.columns(2)
            with c1: tem_fator_social = st.toggle("Fator Social", value=False, help="Marque se o cliente possuir dependente ou for casado.")
            with c2: eh_cotista = st.toggle("Cotista FGTS", value=True, help="Marque se o cliente tiver 3 anos ou mais de registro.")
            
            # --- CÁLCULO EM TEMPO REAL ---
            f_sugerido, s_sugerido = motor.obter_financiamento(renda_familiar, tem_fator_social, eh_cotista)
            
            st.markdown(f"""
            <div class="enquadramento-box">
                <p style="margin:0; font-size:0.8rem; color:#64748b; font-weight:600; text-transform:uppercase;">Valores Estimados de Enquadramento</p>
                <div style="display:flex; justify-content:space-between; margin-top:10px;">
                    <div>
                        <small style="color:#94a3b8;">Financiamento</small><br>
                        <strong style="color:#2563eb; font-size:1.1rem;">R$ {f_sugerido:,.2f}</strong>
                    </div>
                    <div style="text-align:right;">
                        <small style="color:#94a3b8;">FGTS + Subsídio</small><br>
                        <strong style="color:#1e293b; font-size:1.1rem;">R$ {s_sugerido:,.2f}</strong>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("Configuração da Venda")
            
            classificacao = st.selectbox("Classificação de Crédito", options=df_politicas['CLASSIFICAÇÃO'].unique(), index=2)
            
            unidade_escolhida = st.selectbox("Unidade Disponível", 
                                            options=df_estoque[df_estoque['Status'] == 'Disponível']['Identificador'],
                                            help="Selecione uma unidade para simular o Pro Soluto.")
            
            # Permitir ajuste manual dos valores de enquadramento se necessário
            with st.expander("Ajustar Valores de Enquadramento"):
                finan_final = st.number_input("Financiamento Aprovado (R$)", value=f_sugerido)
                fgts_final = st.number_input("FGTS + Subsídio (R$)", value=s_sugerido)
            
            btn_calcular = st.button("🚀 Gerar Simulação Completa")
            st.markdown('</div>', unsafe_allow_html=True)

    with col_result:
        if btn_calcular:
            dados_unidade = df_estoque[df_estoque['Identificador'] == unidade_escolhida].iloc[0]
            vv = dados_unidade['Valor de Venda']
            # Usa os valores ajustados do expander (que iniciam com os sugeridos)
            res = motor.calcular_simulacao(vv, finan_final, fgts_final, classificacao)
            
            st.markdown(f"### 📊 Relatório: {unidade_escolhida}")
            
            # Grid de Métricas
            m1, m2 = st.columns(2)
            with m1:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Valor da Unidade</div><div class="metric-value">R$ {vv:,.2f}</div></div>""", unsafe_allow_html=True)
                st.write("")
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Financiamento</div><div class="metric-value" style="color: #2563eb;">R$ {finan_final:,.2f}</div></div>""", unsafe_allow_html=True)
            with m2:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Pro Soluto Total</div><div class="metric-value" style="color: #f59e0b;">R$ {res['gap']:,.2f}</div></div>""", unsafe_allow_html=True)
                st.write("")
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Parcela Mensal</div><div class="metric-value">R$ {res['mensal']:,.2f}</div></div>""", unsafe_allow_html=True)

            st.markdown("---")
            
            # Gráfico de Composição do Pagamento
            fig = go.Figure(data=[go.Pie(
                labels=['Financiamento', 'FGTS/Subsídio', 'Pro Soluto', 'Ato'],
                values=[finan_final, fgts_final, res['ps_financiado'], res['ato_complementar']],
                hole=.5,
                marker=dict(colors=['#2563eb', '#64748b', '#f59e0b', '#ef4444'])
            )])
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

            # Validação de Política
            status_txt = "✅ DENTRO DA POLÍTICA" if res['ato_complementar'] == 0 else "⚠️ REQUER ATO COMPLEMENTAR"
            status_class = "status-ok" if res['ato_complementar'] == 0 else "status-warning"
            
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 15px; border-left: 5px solid {'#10b981' if res['ato_complementar'] == 0 else '#f59e0b'};">
                <strong>Análise para {nome_cliente or 'Cliente'}:</strong> <span class="{status_class}">{status_txt}</span><br><br>
                O GAP total é de <b>R$ {res['gap']:,.2f}</b>. <br>
                Classificação <b>{classificacao}</b> permite até <b>{res['parcelas']} parcelas</b>.<br>
                Entrada mínima necessária (Ato): <b>R$ {res['ato_complementar']:,.2f}</b>.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Insira os dados do cliente e selecione uma unidade para visualizar o fluxo de pagamento detalhado.")

def aba_estoque_geral(df):
    st.markdown("### 🏢 Gestão de Inventário")
    col1, col2, col3 = st.columns(3)
    
    with col1: emp = st.multiselect("Filtrar Produto", options=df['Empreendimento'].unique())
    with col2: preco_max = st.slider("Preço Máximo", int(df['Valor de Venda'].min()), int(df['Valor de Venda'].max()), int(df['Valor de Venda'].max()))
    with col3: status = st.selectbox("Status", ["Todos", "Disponível", "Reservado"])

    df_f = df.copy()
    if emp: df_f = df_f[df_f['Empreendimento'].isin(emp)]
    if status != "Todos": df_f = df_f[df_f['Status'] == status]
    df_f = df_f[df_f['Valor de Venda'] <= preco_max]

    st.dataframe(df_f, use_container_width=True, hide_index=True)

# =============================================================================
# 5. EXECUÇÃO PRINCIPAL
# =============================================================================

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()

    st.markdown("""
        <div class="header-container">
            <div class="header-title">SIMULADOR DIRECIONAL V2</div>
            <div class="header-subtitle">Sistema Inteligente de Vendas e Enquadramento - Regional Rio de Janeiro</div>
        </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["🎯 Simulador de Venda", "📋 Base de Estoque", "📖 Políticas & Regras"])

    with tabs[0]:
        aba_painel_vendas(df_finan, df_estoque, df_politicas)

    with tabs[1]:
        aba_estoque_geral(df_estoque)

    with tabs[2]:
        st.markdown("### 📜 Políticas de Crédito Vigentes")
        st.table(df_politicas.style.format({'MAX_PS': '{:.0%}'}))
        st.info("As regras acima definem o limite de parcelamento de Pro Soluto por perfil de risco do cliente.")

if __name__ == "__main__":
    main()
