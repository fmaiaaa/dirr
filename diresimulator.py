# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V55.0
=============================================================================
Novas Funcionalidades:
- Gráficos: Gauge, Donut e Barras Comparativas.
- Simulação Reversa: "Quanto posso pagar por mês?"
- Comparador de Unidades: Lado a lado.
- Amortização: Tabela SAC vs PRICE.
- Mobile First: Design responsivo e botões otimizados.
- Integração WhatsApp e PDF.
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from streamlit_gsheets import GSheetsConnection
import io
import streamlit.components.v1 as components
import base64
try:
    from PIL import Image
except ImportError:
    Image = None
import os
import plotly.graph_objects as go
import plotly.express as px
import urllib.parse
import math

# Tenta importar fpdf de forma segura
try:
    from fpdf import FPDF
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

# =============================================================================
# 0. CONSTANTES E UTILITÁRIOS
# =============================================================================
ID_FINAN = "1wJD3tXe1e8FxL4mVEfNKGdtaS__Dl4V6-sm1G6qfL0s"
ID_RANKING = "1N00McOjO1O_MuKyQhp-CVhpAet_9Lfq-VqVm1FmPV00"
ID_ESTOQUE = "1VG-hgBkddyssN1OXgIA33CVsKGAdqT-5kwbgizxWDZQ"

URL_FINAN = f"https://docs.google.com/spreadsheets/d/{ID_FINAN}/edit#gid=0"
URL_RANKING = f"https://docs.google.com/spreadsheets/d/{ID_RANKING}/edit#gid=0"
URL_ESTOQUE = f"https://docs.google.com/spreadsheets/d/{ID_ESTOQUE}/edit#gid=0"

URL_FAVICON_RESERVA = "https://direcional.com.br/wp-content/uploads/2021/04/cropped-favicon-direcional-32x32.png"

COR_AZUL_ESC = "#002c5d"
COR_VERMELHO = "#e30613"
COR_FUNDO = "#fcfdfe"
COR_BORDA = "#eef2f6"
COR_TEXTO_MUTED = "#64748b"

def fmt_br(valor):
    """Formata números para o padrão brasileiro XXX.XXX,XX"""
    try:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

def gerar_texto_whatsapp(d):
    """Gera texto formatado para envio via WhatsApp"""
    texto = (
        f"*SIMULAÇÃO IMOBILIÁRIA - DIRECIONAL*\n"
        f"Olá, {d.get('nome', 'Cliente')}! Segue o resumo da sua simulação:\n\n"
        f"🏠 *IMÓVEL*: {d.get('empreendimento_nome')}\n"
        f"📍 *UNIDADE*: Bloco {d.get('bloco_u', '-')} - {d.get('unidade_id')}\n"
        f"💰 *VALOR*: R$ {fmt_br(d.get('imovel_valor', 0))}\n\n"
        f"💳 *FINANCEIRO*:\n"
        f"• Financiamento: R$ {fmt_br(d.get('finan_usado', 0))}\n"
        f"• FGTS/Subsídio: R$ {fmt_br(d.get('fgts_sub_usado', 0))}\n"
        f"• Pro Soluto: {d.get('ps_parcelas')}x de R$ {fmt_br(d.get('ps_mensal', 0))}\n\n"
        f"🚀 *ENTRADA (ATO)*:\n"
        f"• Total: R$ {fmt_br(d.get('entrada_total', 0))}\n"
        f"• Ato Imediato: R$ {fmt_br(d.get('ato_final', 0))}\n\n"
        f"_Simulação sujeita a aprovação de crédito._"
    )
    return urllib.parse.quote(texto)

# =============================================================================
# 1. CARREGAMENTO E TRATAMENTO DE DADOS
# =============================================================================

@st.cache_data(ttl=300)
def carregar_dados_sistema():
    try:
        if "connections" not in st.secrets:
            st.error("Aviso: Configuração de 'Secrets' não encontrada.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        def limpar_moeda(val):
            if isinstance(val, str):
                val = val.replace('R$', '').replace('.', '').replace(',', '.').strip()
            try: return float(val) if float(val) > 0 else 0.0
            except: return 0.0

        def limpar_porcentagem(val):
            if isinstance(val, str):
                v = val.replace('%', '').replace(',', '.').strip()
                try: 
                    n = float(v)
                    return n / 100 if n > 1 else n
                except: return 0.0
            return val

        try:
            df_politicas = conn.read(spreadsheet=URL_RANKING).rename(columns={'FAIXA RENDA': 'FAIXA_RENDA', 'FX RENDA 1': 'FX_RENDA_1', 'FX RENDA 2': 'FX_RENDA_2'})
            for col in ['PROSOLUTO', 'FX_RENDA_1', 'FX_RENDA_2']:
                if col in df_politicas.columns: df_politicas[col] = df_politicas[col].apply(limpar_porcentagem)
        except: df_politicas = pd.DataFrame()

        try: df_finan = conn.read(spreadsheet=URL_FINAN)
        except: df_finan = pd.DataFrame()

        try:
            df_raw = conn.read(spreadsheet=URL_ESTOQUE)
            df_estoque = df_raw.rename(columns={'Nome do Empreendimento': 'Empreendimento', 'VALOR DE VENDA': 'Valor de Venda', 'Status da unidade': 'Status', 'BLOCO': 'Bloco'})
            df_estoque['Valor de Venda'] = df_estoque['Valor de Venda'].apply(limpar_moeda)
            df_estoque = df_estoque[(df_estoque['Valor de Venda'] > 0) & (df_estoque['Empreendimento'].notnull())].copy()
            if 'Bairro' not in df_estoque.columns: df_estoque['Bairro'] = "Rio de Janeiro"
            if 'Identificador' not in df_estoque.columns: df_estoque['Identificador'] = df_estoque.index.astype(str)
            if 'Bloco' not in df_estoque.columns: df_estoque['Bloco'] = "1"
        except: df_estoque = pd.DataFrame()

        return df_finan, df_estoque, df_politicas
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# =============================================================================
# 2. MOTOR DE CÁLCULO E AMORTIZAÇÃO
# =============================================================================

class MotorElite:
    @staticmethod
    def calcular_sac_price(valor_financiado, prazo_meses, taxa_anual):
        taxa_mensal = (1 + taxa_anual/100)**(1/12) - 1
        # PRICE
        pmt_price = valor_financiado * (taxa_mensal * (1 + taxa_mensal)**prazo_meses) / ((1 + taxa_mensal)**prazo_meses - 1)
        # SAC (Primeira Parcela)
        amort_sac = valor_financiado / prazo_meses
        juros_sac_1 = valor_financiado * taxa_mensal
        pmt_sac_1 = amort_sac + juros_sac_1
        return pmt_price, pmt_sac_1

    @staticmethod
    def obter_enquadramento(df_finan, renda, social, cotista):
        if df_finan.empty: return 0.0, 0.0
        df_finan['Renda'] = pd.to_numeric(df_finan['Renda'], errors='coerce').fillna(0)
        idx = (df_finan['Renda'] - renda).abs().idxmin()
        row = df_finan.iloc[idx]
        s_suf, c_suf = ('Sim' if social else 'Nao'), ('Sim' if cotista else 'Nao')
        return float(row.get(f"Finan_Social_{s_suf}_Cotista_{c_suf}", 0)), float(row.get(f"Subsidio_Social_{s_suf}_Cotista_{c_suf}", 0))

# =============================================================================
# 3. DESIGN E CSS (ELITE MOBILE OPTIMIZED)
# =============================================================================

def aplicar_estilo():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&family=Inter:wght@400;600;700&display=swap');
        html, body, [data-testid="stAppViewContainer"] {{ font-family: 'Inter', sans-serif; background-color: {COR_FUNDO}; }}
        h1, h2, h3 {{ font-family: 'Montserrat', sans-serif; text-align: center; color: {COR_AZUL_ESC}; font-weight: 800; }}
        
        /* Mobile Native Optimization */
        @media (max-width: 768px) {{
            .block-container {{ padding: 1rem !important; }}
            .stButton button {{ width: 100% !important; }}
            .header-title {{ font-size: 1.8rem !important; }}
        }}

        .progress-container {{ width: 100%; height: 6px; background: {COR_BORDA}; border-radius: 10px; margin-bottom: 30px; }}
        .progress-bar {{ height: 100%; background: {COR_VERMELHO}; transition: width 0.5s; }}
        
        .card, .fin-box {{ 
            background: white; padding: 25px; border-radius: 12px; border: 1px solid {COR_BORDA}; 
            text-align: center; margin-bottom: 20px; transition: 0.3s;
        }}
        .card:hover {{ border-color: {COR_VERMELHO}; transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.05); }}
        
        .metric-label {{ font-size: 0.7rem; font-weight: 700; color: {COR_TEXTO_MUTED}; text-transform: uppercase; letter-spacing: 1px; }}
        .metric-value {{ font-size: 1.4rem; font-weight: 800; color: {COR_AZUL_ESC}; font-family: 'Montserrat'; }}
        
        .whatsapp-btn {{
            background: #25d366; color: white !important; border-radius: 8px; padding: 12px;
            font-weight: 700; text-align: center; display: block; text-decoration: none; margin-top: 10px;
        }}
        
        /* Badges */
        .badge-ideal {{ background: {COR_AZUL_ESC}; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.6rem; font-weight: 700; }}
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 4. INTERFACE PRINCIPAL
# =============================================================================

def main():
    aplicar_estilo()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()
    
    if 'passo_simulacao' not in st.session_state: st.session_state.passo_simulacao = 'input'
    if 'dados_cliente' not in st.session_state: st.session_state.dados_cliente = {}
    if 'comparador' not in st.session_state: st.session_state.comparador = []

    # Header
    st.markdown(f'<div style="text-align:center; padding: 40px 0;"><h1 class="header-title">SIMULADOR DIRECIONAL ELITE</h1><p style="color:{COR_TEXTO_MUTED}; font-weight:700;">V55.0 - GESTÃO DE INTELIGÊNCIA IMOBILIÁRIA</p></div>', unsafe_allow_html=True)

    # Barra de Progresso
    passos = {'input': 20, 'potential': 40, 'guide': 60, 'payment_flow': 80, 'summary': 100}
    st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width: {passos[st.session_state.passo_simulacao]}%"></div></div>', unsafe_allow_html=True)

    # --- ETAPA 1: ENTRADA ---
    if st.session_state.passo_simulacao == 'input':
        with st.container():
            st.markdown("### 👤 Perfil do Investidor")
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Completo", value=st.session_state.dados_cliente.get('nome', ""))
            renda = c2.number_input("Renda Familiar Mensal (R$)", value=st.session_state.dados_cliente.get('renda', 4500.0), step=500.0)
            
            rank_opts = [r for r in df_politicas['CLASSIFICAÇÃO'].unique() if r != "EMCASH"]
            ranking = c1.selectbox("Classificação Interna", rank_opts)
            pol_ps = c2.selectbox("Política Financeira", ["Emcash", "Direcional"], index=0)
            
            s1, s2 = st.columns(2)
            social = s1.toggle("Beneficiário Social", value=True)
            cotista = s2.toggle("Conta FGTS (+3 anos)", value=True)
            
            if st.button("CALCULAR POTENCIAL DE COMPRA", type="primary", use_container_width=True):
                if not nome: st.warning("Por favor, insira o nome."); st.stop()
                finan, sub = MotorElite.obter_enquadramento(df_finan, renda, social, cotista)
                pol_ativa = "EMCASH" if pol_ps == "Emcash" else ranking
                p_row = df_politicas[df_politicas['CLASSIFICAÇÃO'] == pol_ativa].iloc[0]
                lim_renda = p_row['FX_RENDA_1'] if renda < p_row['FAIXA_RENDA'] else p_row['FX_RENDA_2']
                
                st.session_state.dados_cliente.update({
                    'nome': nome, 'renda': renda, 'social': social, 'cotista': cotista, 'ranking': ranking,
                    'politica': pol_ps, 'perc_ps': p_row['PROSOLUTO'], 'prazo_ps': int(p_row['PARCELAS']),
                    'finan_est': finan, 'sub_est': sub, 'lim_renda': lim_renda
                })
                st.session_state.passo_simulacao = 'potential'; st.rerun()

    # --- ETAPA 2: POTENCIAL ---
    elif st.session_state.passo_simulacao == 'potential':
        d = st.session_state.dados_cliente
        st.markdown(f"### 📈 Análise de Crédito: {d['nome']}")
        
        # Simulação Reversa
        with st.expander("🔄 SIMULAÇÃO REVERSA: QUANTO POSSO PAGAR POR MÊS?"):
            pmt_desejada = st.slider("Parcela Mensal Pro Soluto Ideal:", 100, 3000, 800)
            valor_ps_possivel = pmt_desejada * d['prazo_ps']
            v_imovel_est = (valor_ps_possivel + d['finan_est'] + d['sub_est'] + (2*d['renda']))
            st.info(f"Com uma parcela de R$ {fmt_br(pmt_desejada)}, seu potencial de compra sobe para aprox. R$ {fmt_br(v_imovel_est)}")

        # Gráfico Gauge de Poder de Compra
        fig_g = go.Figure(go.Indicator(
            mode = "gauge+number", value = d['finan_est'] + d['sub_est'] + (2*d['renda']),
            domain = {'x': [0, 1], 'y': [0, 1]}, title = {'text': "Poder de Aquisição Imediato (R$)"},
            gauge = {'axis': {'range': [None, 400000]}, 'bar': {'color': COR_VERMELHO}, 'steps': [{'range': [0, 200000], 'color': "lightgray"}]}
        ))
        fig_g.update_layout(height=250, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_g, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="card"><p class="metric-label">Financiamento</p><p class="metric-value">R$ {fmt_br(d["finan_est"])}</p></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="card"><p class="metric-label">Subsídio + FGTS</p><p class="metric-value">R$ {fmt_br(d["sub_est"])}</p></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="card"><p class="metric-label">Prazo Pro Soluto</p><p class="metric-value">{d["prazo_ps"]} Meses</p></div>', unsafe_allow_html=True)

        if st.button("VER UNIDADES DISPONÍVEIS", type="primary", use_container_width=True):
            st.session_state.passo_simulacao = 'guide'; st.rerun()
        if st.button("VOLTAR E EDITAR"): st.session_state.passo_simulacao = 'input'; st.rerun()

    # --- ETAPA 3: GUIA (ESTOQUE & COMPARADOR) ---
    elif st.session_state.passo_simulacao == 'guide':
        d = st.session_state.dados_cliente
        st.markdown("### 🏢 Seleção de Unidades e Comparador")
        
        df_v = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
        df_v['Poder'] = d['finan_est'] + d['sub_est'] + (2*d['renda']) + (df_v['Valor de Venda']*d['perc_ps'])
        df_v['Viavel'] = df_v['Valor de Venda'] <= df_v['Poder']
        df_v = df_v.sort_values(['Bloco', 'Identificador'])

        # Filtros Mobile-Friendly
        f_emp = st.selectbox("Filtrar Empreendimento", ["Todos"] + list(df_v['Empreendimento'].unique()))
        df_f = df_v if f_emp == "Todos" else df_v[df_v['Empreendimento'] == f_emp]

        # Comparador
        st.markdown("#### Comparar Unidades (Selecione até 3)")
        cols_comp = st.multiselect("Selecione as unidades para comparar:", df_f['Identificador'].tolist(), max_selections=3)
        if cols_comp:
            df_comp = df_f[df_f['Identificador'].isin(cols_comp)]
            st.table(df_comp[['Identificador', 'Bloco', 'Andar', 'Valor de Venda']].assign(
                Mensal_Est = lambda x: (x['Valor de Venda']*d['perc_ps'])/d['prazo_ps']
            ).rename(columns={'Mensal_Est': 'Mensal PS (Est.)'}))

        st.markdown("---")
        # Lista com Botão de Seleção
        for _, row in df_f.head(10).iterrows():
            with st.container():
                col_i, col_b = st.columns([4, 1])
                badge = "✅ VIÁVEL" if row['Viavel'] else "❌ INV."
                col_i.markdown(f"**Bloco {row['Bloco']} - Unid {row['Identificador']}** | R$ {fmt_br(row['Valor de Venda'])} | {badge}")
                if col_b.button("SELECIONAR", key=f"sel_{row['Identificador']}"):
                    st.session_state.dados_cliente.update({'unidade_id': row['Identificador'], 'imovel_valor': row['Valor de Venda'], 'empreendimento_nome': row['Empreendimento'], 'bloco_u': row['Bloco']})
                    st.session_state.passo_simulacao = 'payment_flow'; st.rerun()

        if st.button("VOLTAR"): st.session_state.passo_simulacao = 'potential'; st.rerun()

    # --- ETAPA 4: FECHAMENTO (SAC vs PRICE) ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### 💵 Fechamento Financeiro: {d['unidade_id']}")
        
        f_u = st.number_input("Financiamento Bancário (R$)", value=float(d['finan_est']))
        sub_u = st.number_input("FGTS + Subsídio (R$)", value=float(d['sub_est']))
        ps_u = st.number_input("Pro Soluto (R$)", value=float(d['imovel_valor']*d['perc_ps']))
        parc_u = st.number_input("Parcelas Pro Soluto", value=d['prazo_ps'], min_value=1)
        
        saldo_ato = d['imovel_valor'] - f_u - sub_u - ps_u
        v_mensal_ps = ps_u / parc_u

        # Tabela SAC vs PRICE
        with st.expander("📊 COMPARATIVO DE AMORTIZAÇÃO BANCÁRIA (ESTIMADO)"):
            taxa_banco = st.number_input("Taxa de Juros Anual (%)", value=9.5)
            p_price, p_sac = MotorElite.calcular_sac_price(f_u, 420, taxa_banco)
            st.markdown(f"""
            | Modalidade | Parcela Inicial (Est.) | Característica |
            | :--- | :--- | :--- |
            | **S.A.C** | R$ {fmt_br(p_sac)} | Parcelas decrescentes ao longo do tempo. |
            | **PRICE** | R$ {fmt_br(p_price)} | Parcelas fixas durante todo o contrato. |
            """)

        st.session_state.dados_cliente.update({
            'finan_usado': f_u, 'fgts_sub_usado': sub_u, 'ps_usado': ps_u, 'ps_parcelas': parc_u,
            'ps_mensal': v_mensal_ps, 'entrada_total': saldo_ato, 'ato_final': saldo_ato
        })

        if st.button("GERAR PROPOSTA FINAL", type="primary", use_container_width=True):
            st.session_state.passo_simulacao = 'summary'; st.rerun()
        if st.button("TROCAR UNIDADE"): st.session_state.passo_simulacao = 'guide'; st.rerun()

    # --- ETAPA 5: RESUMO ---
    elif st.session_state.passo_simulacao == 'summary':
        d = st.session_state.dados_cliente
        st.markdown(f"### 🏆 Resumo da Simulação: {d['nome']}")
        
        # Gráfico Donut de Composição
        fig_d = go.Figure(data=[go.Pie(
            labels=['Financiamento', 'FGTS/Sub', 'Pro Soluto', 'Entrada'],
            values=[d['finan_usado'], d['fgts_sub_usado'], d['ps_usado'], d['entrada_total']],
            hole=.6, marker=dict(colors=[COR_AZUL_ESC, '#64748b', COR_VERMELHO, '#eef2f6'])
        )])
        fig_d.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0), showlegend=True, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_d, use_container_width=True)

        st.markdown('<div class="summary-header">DETALHES DO PLANO</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body">
            <b>Empreendimento:</b> {d['empreendimento_nome']}<br>
            <b>Unidade:</b> Bloco {d['bloco_u']} - {d['unidade_id']}<br>
            <b>Valor de Venda:</b> R$ {fmt_br(d['imovel_valor'])}<hr>
            <b>Mensais Pro Soluto:</b> {d['ps_parcelas']}x R$ {fmt_br(d['ps_mensal'])}<br>
            <b>Entrada (Ato):</b> R$ {fmt_br(d['entrada_total'])}
        </div>""", unsafe_allow_html=True)

        if PDF_ENABLED:
            pdf_b = gerar_resumo_pdf(d)
            if pdf_b: st.download_button("📩 BAIXAR PROPOSTA PDF", data=pdf_b, file_name=f"Proposta_{d['nome']}.pdf", use_container_width=True)
        
        st.markdown(f'<a href="https://wa.me/?text={gerar_texto_whatsapp(d)}" target="_blank" class="whatsapp-btn">📱 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
        
        if st.button("NOVA SIMULAÇÃO", type="primary", use_container_width=True):
            st.session_state.dados_cliente = {}; st.session_state.passo_simulacao = 'input'; st.rerun()

    st.markdown(f'<div style="text-align:center; padding: 40px; color:{COR_TEXTO_MUTED}; font-size:0.7rem;">Direcional Engenharia - Rio de Janeiro | Developed by Lucas Maia</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
