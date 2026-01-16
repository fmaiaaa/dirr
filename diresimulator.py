# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V2
=============================================================================
Fluxo Automatizado de Recomendação:
1. Entrada de dados do cliente (Nome, Renda, Fator Social, Cotista, Ranking).
2. Cálculo automático de Financiamento e FGTS+Subsídio.
3. Filtragem de empreendimentos viáveis (Poder de Compra).
4. Recomendação de unidades por faixas de negociação (100%, 90%, 75%).

Versão: 3.0 (Automação de Recomendação & Poder de Compra)
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# =============================================================================
# 1. CONFIGURAÇÕES E DADOS (MOCK - BASEADO NOS ARQUIVOS DE TESTE)
# =============================================================================

def carregar_dados_sistema():
    # MOCK: TABELA FINANCIAMENTOS (Baseada na lógica da planilha original)
    rendas = np.arange(1500, 12100, 100)
    data_finan = []
    for r in rendas:
        # Lógica aproximada da tabela: Faixa 2 vs Faixa 3
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

    # MOCK: BASE ESTOQUE (Baseada no snippet BASE ESTOQUE.csv)
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
    
    # MOCK: POLÍTICAS PS (Baseada no snippet POLITICAS.csv)
    df_politicas = pd.DataFrame({
        'CLASSIFICAÇÃO': ['EMCASH', 'DIAMANTE', 'OURO', 'PRATA', 'BRONZE', 'AÇO'],
        'PERC_PS': [0.25, 0.25, 0.20, 0.18, 0.15, 0.10],
        'PARCELAS': [66, 84, 84, 84, 80, 60]
    })
    
    return df_finan, df_estoque, df_politicas

# =============================================================================
# 2. MOTOR DE CÁLCULO E RECOMENDAÇÃO
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
        # Fórmula: 2x Renda + Financiamento + FGTS/Subsídio + Pro Soluto (específico da unidade)
        pro_soluto_unidade = valor_unidade * perc_ps
        poder = (2 * renda) + finan + fgts_sub + pro_soluto_unidade
        return poder, pro_soluto_unidade

    def filtrar_unidades_viaveis(self, renda, finan, fgts_sub, perc_ps):
        estoque_disp = self.df_estoque[self.df_estoque['Status'] == 'Disponível'].copy()
        
        # Calcula poder de compra para cada unidade (já que o PS depende do valor da unidade)
        estoque_disp['Poder_Compra'], estoque_disp['PS_Unidade'] = zip(*estoque_disp['Valor de Venda'].apply(
            lambda vv: self.calcular_poder_compra(renda, finan, fgts_sub, perc_ps, vv)
        ))
        
        # Unidade disponível se Valor Venda <= Poder de Compra
        estoque_disp['Viavel'] = estoque_disp['Valor de Venda'] <= estoque_disp['Poder_Compra']
        return estoque_disp[estoque_disp['Viavel']]

# =============================================================================
# 3. INTERFACE E DESIGN (CSS PREMIUM)
# =============================================================================

def configurar_layout():
    st.set_page_config(page_title="Recomendador Direcional", page_icon="🏠", layout="wide")
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .main { background-color: #f8fafc; }
        .header-container { text-align: center; padding: 25px 0; background: #ffffff; border-bottom: 1px solid #e2e8f0; margin-bottom: 30px; border-radius: 0 0 20px 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .header-title { color: #0f172a; font-size: 2rem; font-weight: 700; }
        .card { background: white; padding: 25px; border-radius: 18px; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .recommendation-card { border-left: 6px solid #2563eb; background: #eff6ff; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
        .price-tag { color: #2563eb; font-weight: 700; font-size: 1.2rem; }
        .stButton button { width: 100%; background: #0f172a !important; color: white !important; border-radius: 10px !important; padding: 12px !important; font-weight: 600 !important; border: none !important; }
        div[data-baseweb="tab-list"] { justify-content: center; border-bottom: none; }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 4. ABAS E LÓGICA DE UI
# =============================================================================

def aba_simulador_automacao(df_finan, df_estoque, df_politicas):
    motor = MotorRecomendacao(df_finan, df_estoque, df_politicas)
    
    col_input, col_result = st.columns([1, 1.5], gap="large")
    
    with col_input:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("👤 Perfil do Cliente")
        nome = st.text_input("Nome do Cliente", placeholder="João da Silva")
        renda = st.number_input("Renda Bruta Familiar (R$)", min_value=1500.0, value=3500.0, step=100.0)
        
        c1, c2 = st.columns(2)
        with c1: social = st.toggle("Fator Social", value=False)
        with c2: cotista = st.toggle("Cotista FGTS", value=True)
        
        st.markdown("---")
        st.subheader("🏆 Crédito & Política")
        ranking = st.selectbox("Ranking do Cliente", options=df_politicas['CLASSIFICAÇÃO'].unique(), index=2)
        politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"])
        
        # Se política for Emcash, forçamos o percentual do ranking EMCASH (geralmente maior)
        if politica_ps == "Emcash":
            perc_ps = df_politicas[df_politicas['CLASSIFICAÇÃO'] == 'EMCASH']['PERC_PS'].values[0]
            ranking_atual = 'EMCASH'
        else:
            perc_ps = df_politicas[df_politicas['CLASSIFICAÇÃO'] == ranking]['PERC_PS'].values[0]
            ranking_atual = ranking

        # Cálculo de Enquadramento Automático
        finan_aprox, fgts_sub = motor.obter_enquadramento(renda, social, cotista)
        
        st.markdown(f"""
        <div style="background: #f1f5f9; padding: 15px; border-radius: 12px; margin-top: 10px;">
            <p style="margin:0; font-size:0.75rem; color:#64748b; font-weight:700;">ENQUADRAMENTO ESTIMADO</p>
            <div style="display:flex; justify-content:space-between; margin-top:5px;">
                <span>Financiamento: <b>R$ {finan_aprox:,.2f}</b></span>
                <span>Sub./FGTS: <b>R$ {fgts_sub:,.2f}</b></span>
            </div>
            <p style="margin:5px 0 0 0; font-size:0.8rem;">Teto Pro Soluto ({ranking_atual}): <b>{perc_ps*100:.0f}%</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        btn_recomendar = st.button("🚀 Encontrar Melhores Oportunidades")

    with col_result:
        if btn_recomendar:
            # 1. Filtra unidades onde o valor cabe no poder de compra
            df_viáveis = motor.filtrar_unidades_viaveis(renda, finan_aprox, fgts_sub, perc_ps)
            
            if df_viáveis.empty:
                st.error("❌ Nenhuma unidade disponível para este perfil de renda com as políticas atuais.")
            else:
                st.markdown(f"### 🎯 Recomendações para {nome or 'o Cliente'}")
                
                empreendimentos_viaveis = df_viáveis['Empreendimento'].unique()
                emp_escolhido = st.selectbox("Selecione o Empreendimento para ver as Unidades:", options=empreendimentos_viaveis)
                
                unidades_emp = df_viáveis[df_viáveis['Empreendimento'] == emp_escolhido].sort_values('Valor de Venda', ascending=False)
                
                # --- LÓGICA DE RECOMENDAÇÃO (100%, 90%, 75%) ---
                total_power = unidades_emp['Poder_Compra'].max()
                
                def get_best_unit(threshold):
                    limit = total_power * threshold
                    candidates = unidades_emp[unidades_emp['Valor de Venda'] <= limit]
                    if candidates.empty:
                        return unidades_emp.iloc[-1] # Se nada cabe, recomenda a mais barata
                    return candidates.iloc[0] # Retorna a mais cara dentro do limite

                rec_100 = get_best_unit(1.0)
                rec_90 = get_best_unit(0.9)
                rec_75 = get_best_unit(0.75)

                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.markdown(f"""<div class="recommendation-card" style="border-color: #2563eb;">
                        <small>OPÇÃO IDEAL (100%)</small><br>
                        <strong>{rec_100['Identificador']}</strong><br>
                        <span class="price-tag">R$ {rec_100['Valor de Venda']:,.2f}</span>
                    </div>""", unsafe_allow_html=True)

                with col_b:
                    st.markdown(f"""<div class="recommendation-card" style="border-color: #f59e0b;">
                        <small>OPÇÃO SEGURA (90%)</small><br>
                        <strong>{rec_90['Identificador']}</strong><br>
                        <span class="price-tag">R$ {rec_90['Valor de Venda']:,.2f}</span>
                    </div>""", unsafe_allow_html=True)

                with col_c:
                    st.markdown(f"""<div class="recommendation-card" style="border-color: #10b981;">
                        <small>OPÇÃO FACILITADA (75%)</small><br>
                        <strong>{rec_75['Identificador']}</strong><br>
                        <span class="price-tag">R$ {rec_75['Valor de Venda']:,.2f}</span>
                    </div>""", unsafe_allow_html=True)

                st.markdown("---")
                st.subheader("Todas as Unidades Viáveis neste Produto")
                st.dataframe(unidades_emp[['Identificador', 'Valor de Venda', 'PS_Unidade', 'Poder_Compra']], 
                             use_container_width=True, hide_index=True)
                
                st.info(f"💡 **Dica do Sistema:** Para o cliente {nome}, a unidade {rec_100['Identificador']} é a que melhor aproveita o poder de compra máximo de R$ {total_power:,.2f}.")
        else:
            st.info("Aguardando definição do perfil para calcular a viabilidade de estoque...")

# =============================================================================
# 5. EXECUÇÃO
# =============================================================================

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()

    st.markdown("""
        <div class="header-container">
            <div class="header-title">SIMULADOR DIRECIONAL V2</div>
            <div class="header-subtitle">Recomendação Automática de Unidades e Empreendimentos</div>
        </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["🎯 Simulador & Recomendação", "🏢 Estoque Completo", "📜 Políticas de PS"])

    with tabs[0]:
        aba_simulador_automacao(df_finan, df_estoque, df_politicas)

    with tabs[1]:
        st.markdown("### 📋 Base de Estoque Total")
        st.dataframe(df_estoque, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.markdown("### 📖 Regras de Classificação e Pro Soluto")
        st.table(df_politicas.style.format({'PERC_PS': '{:.0%}'}))
        st.warning("A política 'Emcash' ignora o ranking do cliente para usar o teto de 25%.")

if __name__ == "__main__":
    main()
