# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V2
=============================================================================
Fluxo Automatizado de Recomendação (Sequencial):
1. Etapa 1: Entrada de dados do cliente (com validação de nome).
2. Etapa 2: Valor Potencial de Compra.
3. Etapa 4: Fechamento Financeiro.
5. Etapa 5: Resumo da Compra e Exportação PDF Profissional.

Versão: 50.0 (Ícone Direcional Fixo na Web e PDF - Elite Tecnológica)
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

# Tenta importar fpdf de forma segura
try:
    from fpdf import FPDF
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

# =============================================================================
# 0. CONSTANTES DE ACESSO
# =============================================================================
ID_FINAN = "1wJD3tXe1e8FxL4mVEfNKGdtaS__Dl4V6-sm1G6qfL0s"
ID_RANKING = "1N00McOjO1O_MuKyQhp-CVhpAet_9Lfq-VqVm1FmPV00"
ID_ESTOQUE = "1VG-hgBkddyssN1OXgIA33CVsKGAdqT-5kwbgizxWDZQ"

URL_FINAN = f"https://docs.google.com/spreadsheets/d/{ID_FINAN}/edit#gid=0"
URL_RANKING = f"https://docs.google.com/spreadsheets/d/{ID_RANKING}/edit#gid=0"
URL_ESTOQUE = f"https://docs.google.com/spreadsheets/d/{ID_ESTOQUE}/edit#gid=0"

URL_FAVICON_RESERVA = "https://direcional.com.br/wp-content/uploads/2021/04/cropped-favicon-direcional-32x32.png"

# Cores Oficiais Direcional - Elite Tecnológica
COR_AZUL_ESC = "#002c5d"
COR_VERMELHO = "#e30613"  # Vermelho Direcional Oficial
COR_FUNDO = "#fcfdfe"
COR_BORDA = "#eef2f6"
COR_TEXTO_MUTED = "#64748b"

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

        def limpar_porcentagem(val):
            if isinstance(val, str):
                v = val.replace('%', '').replace(',', '.').strip()
                try:
                    num = float(v)
                    return num / 100 if num > 1 else num
                except: return 0.0
            return val

        def limpar_moeda(val):
            if isinstance(val, str):
                val = val.replace('R$', '').replace('.', '').replace(',', '.').strip()
            try:
                num = float(val)
                return num if num > 0 else 0.0
            except: return 0.0

        try:
            df_politicas = conn.read(spreadsheet=URL_RANKING)
            df_politicas = df_politicas.rename(columns={
                'FAIXA RENDA': 'FAIXA_RENDA',
                'FX RENDA 1': 'FX_RENDA_1',
                'FX RENDA 2': 'FX_RENDA_2'
            })
            for col in ['PROSOLUTO', 'FX_RENDA_1', 'FX_RENDA_2']:
                if col in df_politicas.columns:
                    df_politicas[col] = df_politicas[col].apply(limpar_porcentagem)
        except Exception:
            df_politicas = pd.DataFrame()

        try:
            df_finan = conn.read(spreadsheet=URL_FINAN)
        except Exception:
            df_finan = pd.DataFrame()

        try:
            df_raw = conn.read(spreadsheet=URL_ESTOQUE)
            df_estoque = df_raw.rename(columns={
                'Nome do Empreendimento': 'Empreendimento',
                'VALOR DE VENDA': 'Valor de Venda',
                'Status da unidade': 'Status'
            })
            df_estoque['Valor de Venda'] = df_estoque['Valor de Venda'].apply(limpar_moeda)
            df_estoque = df_estoque[
                (df_estoque['Valor de Venda'] > 0) & 
                (df_estoque['Empreendimento'].notnull())
            ].copy()

            if 'Bairro' not in df_estoque.columns: df_estoque['Bairro'] = "Rio de Janeiro"
            if 'Identificador' not in df_estoque.columns: df_estoque['Identificador'] = df_estoque.index.astype(str)
                
            def extrair_andar_seguro(id_unid):
                try:
                    val_str = str(id_unid)
                    if '-' in val_str: val_str = val_str.split('-')[-1]
                    nums = re.sub(r'\D', '', val_str)
                    return int(nums) // 100 if nums else 0
                except: return 0

            df_estoque['Andar'] = df_estoque['Identificador'].apply(extrair_andar_seguro)
        except Exception:
            df_estoque = pd.DataFrame()
        
        return df_finan, df_estoque, df_politicas
    
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
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
        self.df_finan['Renda'] = pd.to_numeric(self.df_finan['Renda'], errors='coerce').fillna(0)
        idx = (self.df_finan['Renda'] - renda).abs().idxmin()
        row = self.df_finan.iloc[idx]
        s_suf, c_suf = ('Sim' if social else 'Nao'), ('Sim' if cotista else 'Nao')
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
        res = estoque_disp['Valor de Venda'].apply(lambda vv: self.calcular_poder_compra(renda, finan, fgts_sub, perc_ps, vv))
        estoque_disp['Poder_Compra'] = [x[0] for x in res]
        estoque_disp['PS_Unidade'] = [x[1] for x in res]
        estoque_disp['Viavel'] = estoque_disp['Valor de Venda'] <= estoque_disp['Poder_Compra']
        return estoque_disp[estoque_disp['Viavel']]

# =============================================================================
# 3. INTERFACE E DESIGN (ELITE TECNOLÓGICA)
# =============================================================================

def configurar_layout():
    # ALTERAÇÃO: Carrega o ícone localmente via PIL para o favicon do navegador
    favicon = URL_FAVICON_RESERVA
    if os.path.exists("favicon.png") and Image:
        try:
            favicon = Image.open("favicon.png")
        except:
            pass
        
    st.set_page_config(page_title="Simulador Direcional Elite", page_icon=favicon, layout="wide")
    
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Elite Interface Core */
        html, body, [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', sans-serif;
            color: #1a1e26;
            background-color: {COR_FUNDO};
        }}
        
        h1, h2, h3, h4 {{
            font-family: 'Montserrat', sans-serif !important;
            text-align: center !important; 
            color: {COR_AZUL_ESC} !important; 
            font-weight: 800;
            letter-spacing: -0.04em;
        }}

        .block-container {{ max-width: 1400px !important; padding: 4rem 2rem !important; }}
        
        div[data-baseweb="input"] {{
            border-radius: 8px !important;
            border: 1px solid #e2e8f0 !important;
            background-color: #ffffff !important;
            transition: all 0.2s ease-in-out !important;
        }}
        
        div[data-baseweb="input"]:focus-within {{
            border-color: {COR_VERMELHO} !important;
            box-shadow: 0 0 0 1px {COR_VERMELHO} !important;
        }}

        .stTextInput input, .stNumberInput input {{
            padding: 14px 18px !important;
            color: {COR_AZUL_ESC} !important;
        }}
        
        div[data-testid="stNumberInput"] button:hover {{
            background-color: {COR_VERMELHO} !important;
            color: #ffffff !important;
            border-color: {COR_VERMELHO} !important;
        }}

        div[data-testid="stToggle"] div[aria-checked="true"] {{
            background-color: {COR_VERMELHO} !important;
        }}
        
        div[data-baseweb="select"] > div {{
            border-radius: 8px !important;
            border: 1px solid #e2e8f0 !important;
        }}

        .header-container {{ 
            text-align: center; 
            padding: 70px 0; 
            background: #ffffff; 
            margin-bottom: 60px; 
            border-radius: 0 0 40px 40px; 
            border-bottom: 1px solid {COR_BORDA};
            box-shadow: 0 15px 35px -20px rgba(0,44,93,0.1);
            position: relative;
        }}
        .header-title {{ 
            font-family: 'Montserrat', sans-serif;
            color: {COR_AZUL_ESC}; 
            font-size: 3rem; 
            font-weight: 900; 
            margin: 0; 
            text-transform: uppercase; 
            letter-spacing: 0.2em; 
        }}
        .header-subtitle {{ 
            color: {COR_TEXTO_MUTED}; 
            font-size: 1rem; 
            font-weight: 600; 
            margin-top: 15px; 
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}
        
        .card, .fin-box, .recommendation-card {{ 
            background: #ffffff; 
            padding: 40px; 
            border-radius: 16px; 
            border: 1px solid {COR_BORDA}; 
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        
        .card:hover, .fin-box:hover, .recommendation-card:hover {{
            transform: translateY(-4px);
            border-color: {COR_VERMELHO};
            box-shadow: 0 10px 30px -10px rgba(227,6,19,0.1);
        }}
        
        .metric-label {{ color: {COR_TEXTO_MUTED} !important; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 12px; }}
        .metric-value {{ color: {COR_AZUL_ESC} !important; font-size: 1.8rem; font-weight: 800; font-family: 'Montserrat', sans-serif; }}
        
        .stButton button {{ 
            font-family: 'Inter', sans-serif;
            border-radius: 8px !important; 
            padding: 20px 40px !important; 
            font-weight: 700 !important; 
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 0.8rem !important;
            transition: all 0.2s ease !important;
        }}

        .stButton button[kind="primary"] {{ 
            background: {COR_VERMELHO} !important; 
            color: #ffffff !important;
            border: none !important;
        }}
        .stButton button[kind="primary"]:hover {{ 
            background: #c40510 !important;
            box-shadow: 0 8px 20px -5px rgba(227, 6, 19, 0.4) !important;
        }}
        
        .stButton button:not([kind="primary"]) {{ 
            background: #ffffff !important; 
            color: {COR_AZUL_ESC} !important;
            border: 1px solid {COR_AZUL_ESC} !important;
        }}
        
        [data-testid="stDataFrame"] {{
            border: 1px solid {COR_BORDA} !important;
            background: #ffffff;
            padding: 8px;
            border-radius: 12px;
            box-shadow: 0 10px 30px -15px rgba(0,0,0,0.05);
        }}

        .footer {{ 
            text-align: center; 
            padding: 80px 0; 
            color: {COR_TEXTO_MUTED} !important; 
            font-size: 0.8rem; 
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}
        
        .summary-header {{ 
            font-family: 'Montserrat', sans-serif;
            background: {COR_AZUL_ESC}; 
            color: #ffffff !important; 
            padding: 20px; 
            border-radius: 12px 12px 0 0; 
            font-weight: 800; 
            text-align: center; 
            text-transform: uppercase;
            letter-spacing: 0.15em;
            font-size: 0.9rem;
        }}
        .summary-body {{ 
            background: #ffffff; 
            padding: 40px; 
            border: 1px solid {COR_BORDA}; 
            border-radius: 0 0 12px 12px; 
            margin-bottom: 40px; 
            color: {COR_AZUL_ESC}; 
        }}
        
        .custom-alert {{ 
            background-color: {COR_AZUL_ESC}; 
            padding: 25px; 
            border-radius: 10px; 
            margin-bottom: 30px; 
            text-align: center; 
            font-weight: 700; 
            color: #ffffff !important; 
        }}

        div[data-baseweb="tab-list"] {{ justify-content: center !important; gap: 40px; margin-bottom: 40px; }}
        button[data-baseweb="tab"] p {{ 
            color: {COR_TEXTO_MUTED} !important; 
            font-weight: 700 !important; 
            font-family: 'Montserrat', sans-serif !important; 
            font-size: 0.9rem !important; 
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        button[data-baseweb="tab"][aria-selected="true"] p {{ color: {COR_AZUL_ESC} !important; }}
        div[data-baseweb="tab-highlight"] {{ background-color: {COR_VERMELHO} !important; height: 3px !important; }}
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 4. FUNÇÃO PARA GERAR PDF (ESTILO PREMIUM EXECUTIVO)
# =============================================================================

def gerar_resumo_pdf(d):
    if not PDF_ENABLED:
        return None
        
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        AZUL_RGB = (0, 44, 93)
        VERMELHO_RGB = (227, 6, 19)
        BRANCO_RGB = (255, 255, 255)
        CINZA_RGB = (100, 116, 139)
        FUNDO_SECAO = (248, 250, 252)

        pdf.set_fill_color(*AZUL_RGB)
        pdf.rect(0, 0, 210, 3, 'F')

        # Logótipo no PDF (Canto Superior Esquerdo)
        if os.path.exists("favicon.png"):
            pdf.image("favicon.png", 10, 8, 10)
        
        pdf.ln(15)
        pdf.set_text_color(*AZUL_RGB)
        pdf.set_font("Helvetica", 'B', 22)
        pdf.cell(0, 12, "RELATORIO DE VIABILIDADE", ln=True, align='C')
        pdf.set_text_color(*CINZA_RGB)
        pdf.set_font("Helvetica", '', 9)
        pdf.cell(0, 6, "SIMULADOR IMOBILIARIO DIRE RIO - DOCUMENTO EXECUTIVO", ln=True, align='C')
        pdf.ln(15)

        pdf.set_fill_color(*FUNDO_SECAO)
        pdf.rect(10, pdf.get_y(), 190, 24, 'F')
        pdf.set_xy(15, pdf.get_y() + 6)
        pdf.set_text_color(*AZUL_RGB)
        pdf.set_font("Helvetica", 'B', 13)
        pdf.cell(0, 6, f"CLIENTE: {d.get('nome', 'Nao informado').upper()}", ln=True)
        pdf.set_x(15)
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(0, 6, f"Renda Familiar Declarada: R$ {d.get('renda', 0):,.2f}", ln=True)
        pdf.ln(15)

        def adicionar_secao_pdf(titulo):
            pdf.set_fill_color(*AZUL_RGB)
            pdf.set_text_color(*BRANCO_RGB)
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(0, 10, f"   {titulo}", ln=True, fill=True)
            pdf.ln(4)

        def adicionar_linha_detalhe(label, valor, destaque=False):
            pdf.set_x(15)
            pdf.set_text_color(*AZUL_RGB)
            pdf.set_font("Helvetica", '', 10)
            pdf.cell(110, 9, label, border=0)
            
            if destaque:
                pdf.set_text_color(*VERMELHO_RGB)
                pdf.set_font("Helvetica", 'B', 10)
            else:
                pdf.set_font("Helvetica", 'B', 10)
                
            pdf.cell(0, 9, valor, border=0, ln=True, align='R')
            pdf.set_draw_color(241, 245, 249)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())

        adicionar_secao_pdf("ESPECIFICACOES DO ATIVO")
        adicionar_linha_detalhe("Empreendimento", d.get('empreendimento_nome'))
        adicionar_linha_detalhe("Unidade Selecionada", d.get('unidade_id'))
        adicionar_linha_detalhe("Valor de Venda do Imovel", f"R$ {d.get('imovel_valor', 0):,.2f}", destaque=True)
        pdf.ln(8)

        adicionar_secao_pdf("ENGENHARIA FINANCEIRA")
        adicionar_linha_detalhe("Financiamento Bancario Estimado", f"R$ {d.get('finan_usado', 0):,.2f}")
        adicionar_linha_detalhe("Subsidio + FGTS Utilizado", f"R$ {d.get('fgts_sub_usado', 0):,.2f}")
        adicionar_linha_detalhe("Pro Soluto Direcional", f"R$ {d.get('ps_usado', 0):,.2f}")
        adicionar_linha_detalhe("Mensalidade Pro Soluto", f"{d.get('ps_parcelas')}x de R$ {d.get('ps_mensal', 0):,.2f}")
        pdf.ln(8)

        adicionar_secao_pdf("PLANO DE ENTRADA (FLUXO DE CAIXA)")
        adicionar_linha_detalhe("VALOR TOTAL DE ENTRADA", f"R$ {d.get('entrada_total', 0):,.2f}", destaque=True)
        adicionar_linha_detalhe("Parcela de Ato (Imediato)", f"R$ {d.get('ato_final', 0):,.2f}")
        adicionar_linha_detalhe("Parcela 30 Dias", f"R$ {d.get('ato_30', 0):,.2f}")
        adicionar_linha_detalhe("Parcela 60 Dias", f"R$ {d.get('ato_60', 0):,.2f}")
        adicionar_linha_detalhe("Parcela 90 Dias", f"R$ {d.get('ato_90', 0):,.2f}")

        pdf.set_y(-25)
        pdf.set_font("Helvetica", 'I', 7)
        pdf.set_text_color(*CINZA_RGB)
        pdf.cell(0, 4, "Simulacao sujeita a aprovacao de credito e alteracao de tabela sem aviso previo.", ln=True, align='C')
        pdf.cell(0, 4, "Direcional Engenharia - Rio de Janeiro", ln=True, align='C')

        return bytes(pdf.output())
    except Exception:
        return None

# =============================================================================
# 5. COMPONENTES DE INTERAÇÃO
# =============================================================================

def aba_simulador_automacao(df_finan, df_estoque, df_politicas):
    passo_atual = st.session_state.get('passo_simulacao', 'init')
    components.html(
        f"""
        <div id="scroll-anchor-{passo_atual}"></div>
        <script>
            var mainContainer = window.parent.document.querySelector('.main');
            if (mainContainer) {{
                mainContainer.scrollTo({{top: 0, behavior: 'smooth'}});
            }}
            window.parent.window.scrollTo({{top: 0, behavior: 'smooth'}});
        </script>
        """,
        height=0
    )

    motor = MotorRecomendacao(df_finan, df_estoque, df_politicas)
    
    if 'passo_simulacao' not in st.session_state:
        st.session_state.passo_simulacao = 'input'
    if 'dados_cliente' not in st.session_state:
        st.session_state.dados_cliente = {}

    if st.session_state.passo_simulacao == 'input':
        st.markdown("### Dados do Cliente")
        nome = st.text_input("Nome do Cliente", value=st.session_state.dados_cliente.get('nome', ""), placeholder="Nome Completo", key="in_nome_v23")
        renda = st.number_input("Renda Familiar", min_value=1.0, value=st.session_state.dados_cliente.get('renda', 3500.0), step=100.0, key="in_renda_v23")
        
        ranking_options = [r for r in df_politicas['CLASSIFICAÇÃO'].unique().tolist() if r != "EMCASH"] if not df_politicas.empty else ["DIAMANTE"]
        ranking = st.selectbox("Ranking do Cliente", options=ranking_options, index=0, key="in_rank_v23")
        politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"], key="in_pol_v23")
        social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False), key="in_soc_v23")
        cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True), key="in_cot_v23")
        
        if st.button("Avançar para Valor Potencial de Compra", type="primary", use_container_width=True, key="btn_s1_v23"):
            if not nome.strip():
                st.markdown(f'<div class="custom-alert">Por favor, informe o Nome do Cliente para continuar.</div>', unsafe_allow_html=True)
            elif any(char.isdigit() for char in nome):
                st.markdown(f'<div class="custom-alert">Nome Invalido. Por favor, insira um nome valido sem numeros.</div>', unsafe_allow_html=True)
            else:
                finan, sub = motor.obter_enquadramento(renda, social, cotista)
                class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
                politica_row = df_politicas[df_politicas['CLASSIFICAÇÃO'] == class_b].iloc[0]
                limit_ps_r = politica_row['FX_RENDA_1'] if renda < politica_row['FAIXA_RENDA'] else politica_row['FX_RENDA_2']
                
                st.session_state.dados_cliente = {
                    'nome': nome, 'renda': renda, 'social': social, 'cotista': cotista,
                    'ranking': ranking, 'politica': politica_ps, 
                    'perc_ps': politica_row['PROSOLUTO'], 
                    'prazo_ps_max': int(politica_row['PARCELAS']),
                    'limit_ps_renda': limit_ps_r, 'finan_estimado': finan, 'fgts_sub': sub
                }
                st.session_state.passo_simulacao = 'potential'
                st.rerun()

    elif st.session_state.passo_simulacao == 'potential':
        d = st.session_state.dados_cliente
        st.markdown(f"### Valor Potencial de Compra - {d['nome'] or 'Cliente'}")
        
        df_pot = df_estoque[df_estoque['Status'] == 'Disponível']
        ps_min_total = df_pot['Valor de Venda'].min() * d['perc_ps']
        ps_max_total = df_pot['Valor de Venda'].max() * d['perc_ps']
        dobro_renda = 2 * d['renda']
        pot_min = d['finan_estimado'] + d['fgts_sub'] + ps_min_total + dobro_renda
        pot_max = d['finan_estimado'] + d['fgts_sub'] + ps_max_total + dobro_renda
        
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="card"><p class="metric-label">Financiamento</p><p class="metric-value">R$ {d["finan_estimado"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="card"><p class="metric-label">FGTS + Subsidio</p><p class="metric-value">R$ {d["fgts_sub"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="card"><p class="metric-label">Pro Soluto</p><p class="metric-value">R$ {ps_min_total:,.0f} a {ps_max_total:,.0f}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><p class="metric-label">Capacidade Entrada</p><p class="metric-value">R$ {dobro_renda:,.2f}</p></div>', unsafe_allow_html=True)

        st.markdown(f"""
            <div class="card" style="border-top: 4px solid {COR_AZUL_ESC}; background: #ffffff; min-height: 120px;">
                <p class="metric-label" style="color: {COR_AZUL_ESC}; font-size: 0.8rem;">Poder de Aquisicao Estimado</p>
                <p class="metric-value" style="font-size: 2.8rem; color: {COR_AZUL_ESC};">R$ {pot_min:,.2f} a R$ {pot_max:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Explorar Produtos Viaveis", type="primary", use_container_width=True, key="btn_s2_v23"):
            st.session_state.passo_simulacao = 'guide'; st.rerun()
        st.write("")
        if st.button("Ajustar Dados do Cliente", use_container_width=True, key="btn_edit_v23"):
            st.session_state.passo_simulacao = 'input'; st.rerun()

    elif st.session_state.passo_simulacao == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### Catalogo de Viabilidade")
        
        df_disp_total = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
        res = df_disp_total['Valor de Venda'].apply(lambda vv: motor.calcular_poder_compra(d['renda'], d['finan_estimado'], d['fgts_sub'], d['perc_ps'], vv))
        df_disp_total['Poder_Compra'] = [x[0] for x in res]
        df_disp_total['PS_Unidade'] = [x[1] for x in res]
        df_disp_total['Viavel'] = df_disp_total['Valor de Venda'] <= df_disp_total['Poder_Compra']
        df_disp_total['Status Viabilidade'] = df_disp_total['Viavel'].apply(lambda x: "Viavel" if x else "Inviavel")
        
        df_viaveis = df_disp_total[df_disp_total['Viavel']].copy()
        
        st.markdown("#### Resumo de Ofertas Ativas")
        if df_viaveis.empty:
            st.info("Sem produtos viaveis no perfil selecionado.")
        else:
            emp_counts = df_viaveis.groupby('Empreendimento').size().to_dict()
            items = list(emp_counts.items())
            cols_per_row = 3
            for i in range(0, len(items), cols_per_row):
                row_items = items[i:i+cols_per_row]
                row_cols = st.columns(len(row_items))
                for idx, (emp, qtd) in enumerate(row_items):
                    with row_cols[idx]:
                        st.markdown(f"""
                            <div class="card" style="min-height: 100px; padding: 20px; border-top: 3px solid {COR_VERMELHO};">
                                <p style="margin:0; font-weight:700; color:{COR_AZUL_ESC};">{emp}</p>
                                <p style="margin:5px 0 0 0; font-size:0.85rem; color:{COR_TEXTO_MUTED};">{qtd} unidades disponiveis</p>
                            </div>
                        """, unsafe_allow_html=True)

        st.write("")
        tab_rec, tab_list = st.tabs(["Sugestoes Estrategicas", "Estoque Geral"])
        
        with tab_rec:
            if df_viaveis.empty:
                st.info("Nenhuma unidade atende ao poder de compra atual.")
            else:
                emp_rec = st.selectbox("Refinar Sugestoes:", options=["Todos"] + sorted(df_viaveis['Empreendimento'].unique().tolist()), key="sel_emp_v23")
                df_filt_rec = df_viaveis if emp_rec == "Todos" else df_viaveis[df_viaveis['Empreendimento'] == emp_rec]
                df_filt_rec = df_filt_rec.sort_values('Valor de Venda', ascending=False)
                
                if not df_filt_rec.empty:
                    r100, r90, r75 = df_filt_rec.iloc[0], df_filt_rec.iloc[len(df_filt_rec)//2], df_filt_rec.iloc[-1]
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(f'<div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC};"><b>PERFIL IDEAL</b><br><small>{r100["Empreendimento"]}</small><br>{r100["Identificador"]}<br><span class="price-tag">R$ {r100["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="recommendation-card" style="border-top: 4px solid {COR_VERMELHO};"><b>OPCAO SEGURA</b><br><small>{r90["Empreendimento"]}</small><br>{r90["Identificador"]}<br><span class="price-tag">R$ {r90["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC};"><b>MAIOR FACILIDADE</b><br><small>{r75["Empreendimento"]}</small><br>{r75["Identificador"]}<br><span class="price-tag">R$ {r75["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)

        with tab_list:
            f1, f2, f3, f4, f5, f6 = st.columns([1.2, 1, 0.7, 1.1, 0.9, 0.8])
            with f1: f_emp = st.multiselect("Empreendimento:", options=sorted(df_disp_total['Empreendimento'].unique()), key="f_emp_tab_v25")
            with f2: f_bairro = st.multiselect("Bairro:", options=sorted(df_disp_total['Bairro'].unique()), key="f_bairro_tab_v25")
            with f3: f_andar = st.multiselect("Andar:", options=sorted(df_disp_total['Andar'].unique()), key="f_andar_tab_v25")
            with f4: f_status_v = st.multiselect("Viabilidade:", options=["Viavel", "Inviavel"], key="f_status_tab_v25")
            with f5: f_ordem = st.selectbox("Ordem:", ["Maior Preço", "Menor Preço"], key="f_ordem_tab_v25")
            with f6: f_pmax = st.number_input("Preço Máx:", value=float(df_disp_total['Valor de Venda'].max()), key="f_pmax_tab_v25")
            
            df_tab = df_disp_total.copy()
            if f_emp: df_tab = df_tab[df_tab['Empreendimento'].isin(f_emp)]
            if f_bairro: df_tab = df_tab[df_tab['Bairro'].isin(f_bairro)]
            if f_andar: df_tab = df_tab[df_tab['Andar'].isin(f_andar)]
            if f_status_v: df_tab = df_tab[df_tab['Status Viabilidade'].isin(f_status_v)]
            df_tab = df_tab[df_tab['Valor de Venda'] <= f_pmax]
            df_tab = df_tab.sort_values('Valor de Venda', ascending=(f_ordem == "Menor Preço"))
            
            st.dataframe(
                df_tab[['Identificador', 'Empreendimento', 'Bairro', 'Andar', 'Valor de Venda', 'Poder_Compra', 'Status Viabilidade']], 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Identificador": st.column_config.TextColumn("Unidade", width="small"),
                    "Empreendimento": st.column_config.TextColumn("Projeto", width="medium"),
                    "Bairro": st.column_config.TextColumn("Localizacao", width="medium"),
                    "Andar": st.column_config.NumberColumn("Pavimento", format="%dº", width="small"),
                    "Valor de Venda": st.column_config.NumberColumn("Valor de Tabela", format="R$ %.2f", width="medium"),
                    "Poder_Compra": st.column_config.NumberColumn("Teto de Aquisicao", format="R$ %.2f", width="medium"),
                    "Status Viabilidade": st.column_config.TextColumn("Viabilidade", width="small")
                }
            )

        st.markdown("---")
        st.markdown("### Selecao de Ativo")
        
        def label_emp_guide(name):
            sub = df_estoque[(df_estoque['Empreendimento'] == name) & (df_estoque['Status'] == 'Disponível')]
            if sub.empty: return name
            return f"{name} (R$ {sub['Valor de Venda'].min():,.0f} a R$ {sub['Valor de Venda'].max():,.0f})"

        def label_uni_guide(uid, unidades_context):
            u_row = unidades_context[unidades_context['Identificador'] == uid].iloc[0]
            return f"{uid} (R$ {u_row['Valor de Venda']:,.2f})"

        emp_names = sorted(df_estoque[df_estoque['Status'] == 'Disponível']['Empreendimento'].unique())
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            emp_escolhido = st.selectbox("Escolha o Empreendimento:", options=emp_names, format_func=label_emp_guide, key="sel_emp_guide_v26")
        unidades_disp = df_estoque[(df_estoque['Empreendimento'] == emp_escolhido) & (df_estoque['Status'] == 'Disponível')]
        with col_sel2:
            if unidades_disp.empty:
                st.warning("Sem estoque disponivel.")
                uni_escolhida_id = None
            else:
                uni_escolhida_id = st.selectbox("Escolha a Unidade:", options=unidades_disp['Identificador'].unique(), 
                                               format_func=lambda x: label_uni_guide(x, unidades_disp), key="sel_uni_guide_v26")

        st.write("")
        if st.button("Avancar para Montagem de Fluxo", type="primary", use_container_width=True, key="btn_fech_v26"):
            if uni_escolhida_id:
                st.session_state.dados_cliente['unidade_id'] = uni_escolhida_id
                st.session_state.dados_cliente['empreendimento_nome'] = emp_escolhido
                st.session_state.passo_simulacao = 'payment_flow'
                st.rerun()
            else:
                st.error("Por favor, selecione uma unidade.")
        
        if st.button("Voltar ao Poder de Compra", use_container_width=True, key="btn_pot_v23"): 
            st.session_state.passo_simulacao = 'potential'; st.rerun()

    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### Engenharia de Fechamento")
        
        u_id = d.get('unidade_id')
        emp_name = d.get('empreendimento_nome')
        unidades_filtradas = df_estoque[(df_estoque['Empreendimento'] == emp_name) & (df_estoque['Identificador'] == u_id)]
        
        if unidades_filtradas.empty:
            st.error("Falha ao recuperar unidade.")
            if st.button("Voltar ao Catalogo"): st.session_state.passo_simulacao = 'guide'; st.rerun()
        else:
            u = unidades_filtradas.iloc[0]
            st.markdown(f'<div class="custom-alert">Ativo Selecionado: {u["Identificador"]} - {u["Empreendimento"]} (R$ {u["Valor de Venda"]:,.2f})</div>', unsafe_allow_html=True)
            
            f_u = st.number_input("Financiamento Bancário", value=float(d['finan_estimado']), step=1000.0, key="fin_u_v23")
            fgts_u = st.number_input("FGTS + Subsidio", value=float(d['fgts_sub']), step=1000.0, key="fgt_u_v23")
            
            ps_max_real = u['Valor de Venda'] * d['perc_ps']
            ps_u = st.number_input("Pro Soluto Direcional", value=float(ps_max_real), step=1000.0, key="ps_u_v23")
            st.markdown(f'<p style="font-size:0.75rem; color:{COR_TEXTO_MUTED}; margin-top:-15px; margin-bottom:15px; font-weight:700; text-transform:uppercase;">LIMITE DIRECIONAL ({int(d["perc_ps"]*100)}%): R$ {ps_max_real:,.2f}</p>', unsafe_allow_html=True)
            
            parc = st.number_input("Numero de Parcelas Pro Soluto", min_value=1, max_value=d['prazo_ps_max'], value=d['prazo_ps_max'], key="parc_u_v23")
            
            v_parc = ps_u / parc
            comp_r = (v_parc / d['renda'])
            saldo_e = u['Valor de Venda'] - f_u - fgts_u - ps_u

            calc_hash = f"{f_u}-{fgts_u}-{ps_u}-{u_id}"
            if 'last_calc_hash' not in st.session_state or st.session_state.last_calc_hash != calc_hash:
                dist_val = max(0.0, saldo_e / 4)
                st.session_state.ato_1 = dist_val
                st.session_state.ato_2 = dist_val
                st.session_state.ato_3 = dist_val
                st.session_state.ato_4 = dist_val
                st.session_state.last_calc_hash = calc_hash
            
            fin1, fin2, fin3 = st.columns(3)
            with fin1: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b>VALOR DO ATIVO</b><br>R$ {u['Valor de Venda']:,.2f}</div>""", unsafe_allow_html=True)
            with fin2: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_VERMELHO};"><b>MENSALIDADE PS</b><br>R$ {v_parc:,.2f} ({parc}x)</div>""", unsafe_allow_html=True)
            with fin3: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b>SALDO ENTRADA</b><br>R$ {max(0, saldo_e):,.2f}</div>""", unsafe_allow_html=True)
            
            if comp_r > d['limit_ps_renda']:
                st.warning(f"Atencao: Parcela Pro Soluto excede o limite de {d['limit_ps_renda']*100:.0f}% da renda.")

            if saldo_e > 0:
                st.markdown("#### Distribuicao da Entrada")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.session_state.ato_1 = st.number_input("Ato", value=st.session_state.ato_1, key="ato_1_v24")
                    st.session_state.ato_3 = st.number_input("Ato 60", value=st.session_state.ato_3, key="ato_3_v24")
                with col_b:
                    st.session_state.ato_2 = st.number_input("Ato 30", value=st.session_state.ato_2, key="ato_2_v24")
                    st.session_state.ato_4 = st.number_input("Ato 90", value=st.session_state.ato_4, key="ato_4_v24")
                
                soma_entrada = st.session_state.ato_1 + st.session_state.ato_2 + st.session_state.ato_3 + st.session_state.ato_4
                if abs(soma_entrada - saldo_e) > 0.01:
                    st.error(f"Erro na Distribuicao: A soma das parcelas (R$ {soma_entrada:,.2f}) difere do saldo de entrada.")
            
            st.session_state.dados_cliente.update({
                'imovel_valor': u['Valor de Venda'], 'finan_usado': f_u, 'fgts_sub_usado': fgts_u,
                'ps_usado': ps_u, 'ps_parcelas': parc, 'ps_mensal': v_parc, 'entrada_total': saldo_e,
                'ato_final': st.session_state.ato_1, 'ato_30': st.session_state.ato_2,
                'ato_60': st.session_state.ato_3, 'ato_90': st.session_state.ato_4
            })
        
        st.markdown("---")
        if st.button("Finalizar e Ver Resumo", type="primary", use_container_width=True, key="btn_to_summary"):
            st.session_state.passo_simulacao = 'summary'
            st.rerun()
        if st.button("Voltar ao Catalogo", use_container_width=True, key="btn_back_to_guide"): 
            st.session_state.passo_simulacao = 'guide'; st.rerun()

    elif st.session_state.passo_simulacao == 'summary':
        d = st.session_state.dados_cliente
        st.markdown(f"### Resumo Final da Operacao - {d.get('nome', 'Cliente')}")
        
        if PDF_ENABLED:
            pdf_data = gerar_resumo_pdf(d)
            if pdf_data:
                _, col_btn_center, _ = st.columns([1, 1.2, 1])
                with col_btn_center:
                    st.download_button(
                        label="Exportar Relatorio Executivo (PDF)", 
                        data=pdf_data, 
                        file_name=f"Resumo Direcional - {d.get('nome', 'Cliente')}.pdf", 
                        mime="application/pdf",
                        use_container_width=True,
                        key="btn_download_pdf_final"
                    )

        st.markdown(f'<div class="summary-header">DADOS DO IMOVEL</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Empreendimento:</b> {d.get('empreendimento_nome')}<br>
            <b>Unidade:</b> {d.get('unidade_id')}<br><b>Valor de Venda:</b> <span style="color: {COR_VERMELHO}; font-weight: 800;">R$ {d.get('imovel_valor', 0):,.2f}</span></div>""", unsafe_allow_html=True)

        st.markdown(f'<div class="summary-header">PLANO DE FINANCIAMENTO</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Financiamento Bancario:</b> R$ {d.get('finan_usado', 0):,.2f}<br>
            <b>FGTS + Subsidio:</b> R$ {d.get('fgts_sub_usado', 0):,.2f}<br>
            <b>Pro Soluto Total:</b> R$ {d.get('ps_usado', 0):,.2f} ({d.get('ps_parcelas')}x de R$ {d.get('ps_mensal', 0):,.2f})</div>""", unsafe_allow_html=True)

        st.markdown(f'<div class="summary-header">FLUXO DE ENTRADA (ATO)</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Total de Entrada:</b> R$ {d.get('entrada_total', 0):,.2f}<br><hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 10px 0;">
            <b>Ato:</b> R$ {d.get('ato_final', 0):,.2f}<br><b>Ato 30 Dias:</b> R$ {d.get('ato_30', 0):,.2f}<br>
            <b>Ato 60 Dias:</b> R$ {d.get('ato_60', 0):,.2f}<br><b>Ato 90 Dias:</b> R$ {d.get('ato_90', 0):,.2f}</div>""", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("Novo Simulador", type="primary", use_container_width=True, key="btn_new_client_summary"): 
            st.session_state.dados_cliente = {}; st.session_state.passo_simulacao = 'input'; st.rerun()
        if st.button("Corrigir Engenharia Financeira", use_container_width=True, key="btn_edit_fin_summary"):
            st.session_state.passo_simulacao = 'payment_flow'; st.rerun()

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()
    if df_finan.empty or df_estoque.empty:
        st.warning("Aguardando conexao com base de dados...")
        st.stop()
    
    # ALTERAÇÃO: Codifica a imagem local para Base64 para garantir a exibição na web
    logo_src = URL_FAVICON_RESERVA
    if os.path.exists("favicon.png"):
        try:
            with open("favicon.png", "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                logo_src = f"data:image/png;base64,{encoded}"
        except:
            pass

    st.markdown(f'''
        <div class="header-container">
            <img src="{logo_src}" style="position: absolute; top: 30px; left: 40px; height: 50px;">
            <div class="header-title">SIMULADOR ELITE DIRE RIO</div>
            <div class="header-subtitle">Gestao de Vendas Direcional Engenharia v2.0</div>
        </div>
    ''', unsafe_allow_html=True)
    
    aba_simulador_automacao(df_finan, df_estoque, df_politicas)
    st.markdown(f'<div class="footer">Direcional Engenharia - Rio de Janeiro | Developed by Lucas Maia</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
