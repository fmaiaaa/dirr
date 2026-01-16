# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V2
=============================================================================
Fluxo Automatizado de Recomendação (Sequencial):
1. Etapa 1: Entrada de dados do cliente.
2. Etapa 2: Valor Potencial de Compra (Visão Financeira).
3. Etapa 3: Escolha do Produto, Unidades Recomendadas e Seleção de Unidade.
4. Etapa 4: Detalhamento do Fluxo de Pagamento e Saldo de Ato.

Versão: 6.0 (Fluxo Completo de Fechamento Financeiro)
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
        'Valor de Venda': np.random.randint(190000, 340000, 80),
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
        
        .block-container {
            max-width: 1200px !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 2rem !important;
            margin: auto !important;
        }

        .header-container { text-align: center; padding: 30px 0; background: #ffffff; border-bottom: 1px solid #e2e8f0; margin-bottom: 30px; border-radius: 0 0 15px 15px; }
        .header-title { color: #0f172a; font-size: 2.2rem; font-weight: 700; margin: 0; }
        
        .card { background: white; padding: 25px; border-radius: 18px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; width: 100%; }
        .recommendation-card { border-left: 5px solid #2563eb; background: #f8fafc; padding: 15px; border-radius: 12px; margin-bottom: 10px; text-align: center; }
        .price-tag { color: #2563eb; font-weight: 700; font-size: 1.1rem; }
        
        .stButton button { border-radius: 10px !important; padding: 10px !important; font-weight: 600 !important; }
        
        .metric-label { color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; text-align: center; width: 100%; }
        .metric-value { color: #1e293b; font-size: 1.2rem; font-weight: 700; text-align: center; width: 100%; }
        
        h1, h2, h3, h4 { text-align: center !important; width: 100%; }
        
        .ref-box {
            background: #f1f5f9;
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            color: #475569;
            font-size: 0.85rem;
            margin-bottom: 10px;
        }
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
    if 'unidade_escolhida' not in st.session_state:
        st.session_state.unidade_escolhida = None

    # --- PASSO 1: ENTRADA DE DADOS ---
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
        
        ps_medio = df_estoque[df_estoque['Status'] == 'Disponível']['Valor de Venda'].mean() * d['perc_ps']
        dobro_renda = 2 * d['renda']
        valor_potencial = d['finan_estimado'] + d['fgts_sub'] + ps_medio + dobro_renda
        
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="card"><p class="metric-label">Financiamento Aprovado</p><p class="metric-value">R$ {d["finan_estimado"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="card"><p class="metric-label">FGTS + Subsídio</p><p class="metric-value">R$ {d["fgts_sub"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="card"><p class="metric-label">Pro Soluto Médio</p><p class="metric-value">R$ {ps_medio:,.2f}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><p class="metric-label">Dobro da Renda</p><p class="metric-value">R$ {dobro_renda:,.2f}</p></div>', unsafe_allow_html=True)

        _, col_pot, _ = st.columns([1, 2, 1])
        with col_pot:
            st.markdown(f"""
                <div class="card" style="border-top: 5px solid #2563eb; text-align: center; background: #f0f7ff;">
                    <p class="metric-label" style="color: #2563eb; font-size: 1.1rem;">Valor Potencial de Compra</p>
                    <p class="metric-value" style="font-size: 2.2rem; color: #0f172a;">R$ {valor_potencial:,.2f}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🏢 Escolher Produto e Ver Unidades", type="primary", use_container_width=True):
                st.session_state.passo_simulacao = 'results'
                st.rerun()
            st.write("")
            if st.button("⬅️ Editar Dados do Cliente", use_container_width=True):
                st.session_state.passo_simulacao = 'input'
                st.rerun()

    # --- PASSO 3: PRODUTOS E UNIDADES ---
    elif st.session_state.passo_simulacao == 'results':
        d = st.session_state.dados_cliente
        st.markdown(f"### 🎯 Etapa 3: Escolha do Produto")
        
        df_viaveis = motor.filtrar_unidades_viaveis(d['renda'], d['finan_estimado'], d['fgts_sub'], d['perc_ps'])
        
        if df_viaveis.empty:
            st.error("❌ Não foram encontradas unidades compatíveis.")
            if st.button("⬅️ Voltar"): st.session_state.passo_simulacao = 'potential'; st.rerun()
        else:
            _, col_sel_emp, _ = st.columns([1, 2, 1])
            with col_sel_emp:
                emp_opcoes = ["Todos"] + sorted(df_viaveis['Empreendimento'].unique().tolist())
                emp_escolhido_rec = st.selectbox("Selecione o Empreendimento:", options=emp_opcoes)
            
            df_filtrado = df_viaveis if emp_escolhido_rec == "Todos" else df_viaveis[df_viaveis['Empreendimento'] == emp_escolhido_rec]
            df_filtrado = df_filtrado.sort_values('Valor de Venda', ascending=False)
            
            st.markdown("#### ⭐ Unidades Recomendadas")
            if not df_filtrado.empty:
                max_p = df_filtrado['Poder_Compra'].max()
                def rec(pct):
                    lim = max_p * pct
                    cands = df_filtrado[df_filtrado['Valor de Venda'] <= lim]
                    return cands.iloc[0] if not cands.empty else df_filtrado.iloc[-1]
                r100, r90, r75 = rec(1.0), rec(0.9), rec(0.75)
                
                c_r1, c_r2, c_r3 = st.columns(3)
                with c_r1: st.markdown(f'<div class="recommendation-card" style="border-color:#2563eb;"><small>IDEAL (100%)</small><br><b>{r100["Identificador"]}</b><br><small>{r100["Empreendimento"]}</small><br><span class="price-tag">R$ {r100["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                with c_r2: st.markdown(f'<div class="recommendation-card" style="border-color:#f59e0b;"><small>SEGURA (90%)</small><br><b>{r90["Identificador"]}</b><br><small>{r90["Empreendimento"]}</small><br><span class="price-tag">R$ {r90["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                with c_r3: st.markdown(f'<div class="recommendation-card" style="border-color:#10b981;"><small>FACILITADA (75%)</small><br><b>{r75["Identificador"]}</b><br><small>{r75["Empreendimento"]}</small><br><span class="price-tag">R$ {r75["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📋 Lista Completa de Unidades Disponíveis")
            f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([1.2, 1, 0.8, 1, 0.8])
            with f_col1: filtro_emp = st.multiselect("Empreendimento:", options=sorted(df_viaveis['Empreendimento'].unique()), key="f_emp_3")
            with f_col2: filtro_bairro = st.multiselect("Bairro:", options=sorted(df_viaveis['Bairro'].unique()), key="f_bairro_3")
            with f_col3: filtro_andar = st.multiselect("Andar:", options=sorted(df_viaveis['Andar'].unique()), key="f_andar_3")
            with f_col4: ordenacao = st.selectbox("Ordenar por Valor:", ["Maior Preço", "Menor Preço"], key="f_ordem_3")
            with f_col5: p_max = st.number_input("Preço Máximo:", value=float(df_viaveis['Valor de Venda'].max()), key="f_preco_3")
            
            df_tabela = df_viaveis.copy()
            if filtro_emp: df_tabela = df_tabela[df_tabela['Empreendimento'].isin(filtro_emp)]
            if filtro_bairro: df_tabela = df_tabela[df_tabela['Bairro'].isin(filtro_bairro)]
            if filtro_andar: df_tabela = df_tabela[df_tabela['Andar'].isin(filtro_andar)]
            df_tabela = df_tabela[df_tabela['Valor de Venda'] <= p_max]
            df_tabela = df_tabela.sort_values('Valor de Venda', ascending=(ordenacao == "Menor Preço"))
            st.dataframe(df_tabela[['Identificador', 'Empreendimento', 'Bairro', 'Andar', 'Valor de Venda', 'PS_Unidade', 'Poder_Compra']], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("✅ Seleção para Fechamento")
            col_final_1, col_final_2 = st.columns([2, 1])
            with col_final_1:
                unidade_final = st.selectbox("Escolha a unidade definitiva para o fluxo:", options=df_filtrado['Identificador'].unique())
            with col_final_2:
                st.write("")
                if st.button("💰 Avançar para Detalhes de Pagamento", type="primary", use_container_width=True):
                    st.session_state.unidade_escolhida = df_filtrado[df_filtrado['Identificador'] == unidade_final].iloc[0].to_dict()
                    st.session_state.passo_simulacao = 'payment_flow'
                    st.rerun()

            if st.button("⬅️ Voltar ao Potencial"): st.session_state.passo_simulacao = 'potential'; st.rerun()

    # --- PASSO 4: DETALHAMENTO DO FLUXO DE PAGAMENTO ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        u = st.session_state.unidade_escolhida
        st.markdown(f"### 📑 Etapa 4: Detalhamento do Fluxo - {u['Identificador']}")
        
        st.markdown(f"""
            <div class="card" style="border-left: 5px solid #2563eb;">
                <b>Unidade Selecionada:</b> {u['Identificador']} | <b>Empreendimento:</b> {u['Empreendimento']}<br>
                <b>Valor da Unidade:</b> R$ {u['Valor de Venda']:,.2f}
            </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            col_inp, col_ref = st.columns([2, 1])
            
            with col_inp:
                f_usado = st.number_input("Financiamento a utilizar (R$)", value=float(d['finan_estimado']))
                fgts_usado = st.number_input("FGTS + Subsídio a utilizar (R$)", value=float(d['fgts_sub']))
                
                ps_max_real = u['Valor de Venda'] * d['perc_ps']
                ps_usado = st.number_input("Pro Soluto a utilizar (R$)", value=float(ps_max_real), max_value=float(u['Valor de Venda']))
                
                parc_ps = st.number_input("Quantidade de Parcelas Pro Soluto", min_value=1, max_value=84, value=84)
            
            with col_ref:
                st.markdown(f'<div class="ref-box"><b>Referência (Aprovado):</b><br>R$ {d["finan_estimado"]:,.2f}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ref-box"><b>Referência (Estimado):</b><br>R$ {d["fgts_sub"]:,.2f}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ref-box"><b>Máximo Permitido:</b><br>R$ {ps_max_real:,.2f}</div>', unsafe_allow_html=True)

            # Cálculos de Pro Soluto
            valor_parc_ps = ps_usado / parc_ps
            pct_renda = (valor_parc_ps / d['renda']) * 100
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1: st.metric("Valor da Parcela PS", f"R$ {valor_parc_ps:,.2f}")
            with c2: st.metric("% da Renda do Cliente", f"{pct_renda:.2f}%")
            
            saldo_restante = u['Valor de Venda'] - f_usado - fgts_usado - ps_usado
            
            st.markdown(f"""
                <div class="card" style="text-align: center; background: #fff1f2; border-top: 5px solid #e11d48;">
                    <p class="metric-label" style="color: #e11d48;">Saldo de Entrada (Ato / Séries)</p>
                    <p class="metric-value" style="font-size: 2rem;">R$ {max(0, saldo_restante):,.2f}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if saldo_restante > 0:
                st.markdown("#### Detalhamento do Saldo")
                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1: ato = st.number_input("Valor Ato (R$)", value=saldo_restante/4)
                with sc2: ato30 = st.number_input("Valor Ato 30 (R$)", value=saldo_restante/4)
                with sc3: ato60 = st.number_input("Valor Ato 60 (R$)", value=saldo_restante/4)
                with sc4: ato90 = st.number_input("Valor Ato 90 (R$)", value=saldo_restante/4)
                
                soma_atos = ato + ato30 + ato60 + ato90
                diferenca = saldo_restante - soma_atos
                if abs(diferenca) > 0.01:
                    st.warning(f"Atenção: A soma dos atos (R$ {soma_atos:,.2f}) difere do saldo total (Diferença: R$ {diferenca:,.2f})")
            
            st.markdown("---")
            if st.button("⬅️ Voltar para Unidades", use_container_width=True):
                st.session_state.passo_simulacao = 'results'
                st.rerun()
            if st.button("👤 Mudar Cliente", use_container_width=True):
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
