# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V2 (MODIFICADO)
=============================================================================
Alterações Realizadas:
1. Lógica de Recomendação: Agora sempre recomenda uma unidade (fallback para a mais barata).
2. Referências Financeiras: Adicionada seção informativa na etapa de fechamento.
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
    try:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

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
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                val = val.replace('R$', '').replace('.', '').replace(',', '.').strip()
                try:
                    return float(val)
                except: return 0.0
            return 0.0

        try:
            df_politicas = conn.read(spreadsheet=URL_RANKING)
            df_politicas.columns = [str(c).strip() for c in df_politicas.columns]
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
            df_finan.columns = [str(c).strip() for c in df_finan.columns]
            for col in df_finan.columns:
                df_finan[col] = df_finan[col].apply(limpar_moeda)
        except Exception:
            df_finan = pd.DataFrame()

        try:
            df_raw = conn.read(spreadsheet=URL_ESTOQUE)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            
            try:
                df_filtro = conn.read(spreadsheet=URL_ESTOQUE, worksheet="Página2")
                if 'Nome do empreendimento' in df_filtro.columns:
                    lista_permitidos = df_filtro['Nome do empreendimento'].dropna().astype(str).str.strip().unique()
                else:
                    lista_permitidos = None
            except Exception:
                lista_permitidos = None

            df_estoque = df_raw.rename(columns={
                'Nome do Empreendimento': 'Empreendimento',
                'VALOR DE VENDA': 'Valor de Venda',
                'Status da unidade': 'Status'
            })
            
            df_estoque['Valor de Venda'] = df_estoque['Valor de Venda'].apply(limpar_moeda)
            
            if lista_permitidos is not None:
                df_estoque = df_estoque[df_estoque['Empreendimento'].astype(str).str.strip().isin(lista_permitidos)]

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

            def extrair_bloco_seguro(id_unid):
                try:
                    val_str = str(id_unid)
                    if '-' in val_str:
                        prefixo = val_str.split('-')[0]
                        nums = re.sub(r'\D', '', prefixo)
                        return int(nums) if nums else 1
                    return 1
                except: return 1

            def extrair_apto_seguro(id_unid):
                try:
                    val_str = str(id_unid)
                    sufixo = val_str.split('-')[-1]
                    nums = re.sub(r'\D', '', sufixo)
                    return int(nums) if nums else 0
                except: return 0

            df_estoque['Andar'] = df_estoque['Identificador'].apply(extrair_andar_seguro)
            df_estoque['Bloco_Sort'] = df_estoque['Identificador'].apply(extrair_bloco_seguro)
            df_estoque['Apto_Sort'] = df_estoque['Identificador'].apply(extrair_apto_seguro)

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

    def obter_enquadramento(self, renda, social, cotista, valor_imovel=250000):
        if self.df_finan.empty: return 0.0, 0.0, "N/A"
        
        # Determinação da Faixa
        if valor_imovel <= 190000: # Faixa 1 (Limite genérico Direcional)
            faixa = "F1"
        elif valor_imovel <= 275000:
            faixa = "F2"
        elif valor_imovel <= 350000:
            faixa = "F3"
        else:
            faixa = "F4"
            
        renda_col = pd.to_numeric(self.df_finan['Renda'], errors='coerce').fillna(0)
        idx = (renda_col - renda).abs().idxmin()
        row = self.df_finan.iloc[idx]
        
        s_suf, c_suf = ('Sim' if social else 'Nao'), ('Sim' if cotista else 'Nao')
        
        c_finan = f"Finan_Social_{s_suf}_Cotista_{c_suf}_{faixa}"
        c_sub = f"Subsidio_Social_{s_suf}_Cotista_{c_suf}_{faixa}"
        
        val_finan = row.get(c_finan, 0.0)
        val_sub = row.get(c_sub, 0.0)
        
        # Fallback se F1 não existir na planilha (tenta F2)
        if val_finan == 0 and faixa == "F1":
            c_finan = f"Finan_Social_{s_suf}_Cotista_{c_suf}_F2"
            c_sub = f"Subsidio_Social_{s_suf}_Cotista_{c_suf}_F2"
            val_finan = row.get(c_finan, 0.0)
            val_sub = row.get(c_sub, 0.0)

        return float(val_finan), float(val_sub), faixa

    def calcular_poder_compra(self, renda, finan, fgts_sub, perc_ps, valor_unidade):
        pro_soluto_unidade = valor_unidade * perc_ps
        poder = (2 * renda) + finan + fgts_sub + pro_soluto_unidade
        return poder, pro_soluto_unidade

# =============================================================================
# 3. INTERFACE E DESIGN
# =============================================================================

def configurar_layout():
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
        
        .inline-ref {{
            font-size: 0.78rem;
            color: #64748b;
            margin-top: -15px;
            margin-bottom: 15px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

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
        .stButton button:not([kind="primary"]):hover {{
            border-color: {COR_VERMELHO} !important;
            color: {COR_VERMELHO} !important;
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

        .price-tag {{
            color: {COR_VERMELHO};
            font-weight: 900;
            font-size: 1.2rem;
            margin-top: 10px;
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

        /* Tabela de Referencia de Politica */
        .policy-ref-table {{
            width: 100%;
            background: #f8fafc;
            border-radius: 12px;
            padding: 20px;
            border: 1px dashed #cbd5e1;
            margin-bottom: 25px;
        }}
        .policy-ref-title {{
            font-size: 0.7rem;
            font-weight: 800;
            text-transform: uppercase;
            color: #64748b;
            letter-spacing: 0.1em;
            margin-bottom: 15px;
            text-align: left;
        }}
        .policy-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }}
        .policy-item {{
            text-align: left;
        }}
        .policy-item-label {{
            font-size: 0.65rem;
            color: #94a3b8;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .policy-item-value {{
            font-size: 0.85rem;
            color: {COR_AZUL_ESC};
            font-weight: 700;
        }}
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 4. FUNÇÃO PARA GERAR PDF
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

        if os.path.exists("favicon.png"):
            pdf.image("favicon.png", 10, 8, 10)
        
        pdf.ln(15)
        pdf.set_text_color(*AZUL_RGB)
        pdf.set_font("Helvetica", 'B', 22)
        pdf.cell(0, 12, "RELATÓRIO DE VIABILIDADE", ln=True, align='C')
        pdf.set_text_color(*CINZA_RGB)
        pdf.set_font("Helvetica", '', 9)
        pdf.cell(0, 6, "SIMULADOR IMOBILIÁRIO DV - DOCUMENTO EXECUTIVO", ln=True, align='C')
        pdf.ln(15)

        pdf.set_fill_color(*FUNDO_SECAO)
        pdf.rect(10, pdf.get_y(), 190, 24, 'F')
        pdf.set_xy(15, pdf.get_y() + 6)
        pdf.set_text_color(*AZUL_RGB)
        pdf.set_font("Helvetica", 'B', 13)
        pdf.cell(0, 6, f"CLIENTE: {d.get('nome', 'Nao informado').upper()}", ln=True)
        pdf.set_x(15)
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(0, 6, f"Renda Familiar: R$ {fmt_br(d.get('renda', 0))}", ln=True)
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

        adicionar_secao_pdf("DADOS DO IMÓVEL")
        adicionar_linha_detalhe("Empreendimento", d.get('empreendimento_nome'))
        adicionar_linha_detalhe("Unidade Selecionada", d.get('unidade_id'))
        adicionar_linha_detalhe("Valor de Venda do Imovel", f"R$ {fmt_br(d.get('imovel_valor', 0))}", destaque=True)
        pdf.ln(8)

        adicionar_secao_pdf("ENGENHARIA FINANCEIRA")
        adicionar_linha_detalhe("Financiamento Bancário Estimado", f"R$ {fmt_br(d.get('finan_usado', 0))}")
        adicionar_linha_detalhe("Subsídio + FGTS Utilizado", f"R$ {fmt_br(d.get('fgts_sub_usado', 0))}")
        adicionar_linha_detalhe("Pro Soluto Direcional", f"R$ {fmt_br(d.get('ps_usado', 0))}")
        adicionar_linha_detalhe("Mensalidade Pro Soluto", f"{d.get('ps_parcelas')}x de R$ {fmt_br(d.get('ps_mensal', 0))}")
        pdf.ln(8)

        adicionar_secao_pdf("PLANO DE ENTRADA (FLUXO DE CAIXA)")
        adicionar_linha_detalhe("VALOR TOTAL DE ENTRADA", f"R$ {fmt_br(d.get('entrada_total', 0))}", destaque=True)
        adicionar_linha_detalhe("Parcela de Ato (Imediato)", f"R$ {fmt_br(d.get('ato_final', 0))}")
        adicionar_linha_detalhe("Parcela 30 Dias", f"R$ {fmt_br(d.get('ato_30', 0))}")
        adicionar_linha_detalhe("Parcela 60 Dias", f"R$ {fmt_br(d.get('ato_60', 0))}")
        adicionar_linha_detalhe("Parcela 90 Dias", f"R$ {fmt_br(d.get('ato_90', 0))}")

        pdf.set_y(-25)
        pdf.set_font("Helvetica", 'I', 7)
        pdf.set_text_color(*CINZA_RGB)
        pdf.cell(0, 4, "Simulação sujeita a aprovação de crédito e alteração de tabela sem aviso prévio.", ln=True, align='C')
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

    # --- ETAPA 1: INPUT ---
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
                class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
                politica_row = df_politicas[df_politicas['CLASSIFICAÇÃO'] == class_b].iloc[0]
                limit_ps_r = politica_row['FX_RENDA_1'] if renda < politica_row['FAIXA_RENDA'] else politica_row['FX_RENDA_2']
                
                # Coleta valores específicos da Faixa 1 para a próxima tela
                f_faixa1, s_faixa1, fx_nome = motor.obter_enquadramento(renda, social, cotista, valor_imovel=180000)

                st.session_state.dados_cliente = {
                    'nome': nome, 'renda': renda, 'social': social, 'cotista': cotista,
                    'ranking': ranking, 'politica': politica_ps, 
                    'perc_ps': politica_row['PROSOLUTO'], 
                    'prazo_ps_max': int(politica_row['PARCELAS']),
                    'limit_ps_renda': limit_ps_r,
                    'finan_f1': f_faixa1, 'sub_f1': s_faixa1
                }
                st.session_state.passo_simulacao = 'potential'
                st.rerun()

    # --- ETAPA 2: POTENCIAL ---
    elif st.session_state.passo_simulacao == 'potential':
        d = st.session_state.dados_cliente
        st.markdown(f"### Valor Potencial de Compra - {d['nome'] or 'Cliente'}")
        
        df_pot = df_estoque[df_estoque['Status'] == 'Disponível']
        
        if df_pot.empty:
            st.warning("Não há empreendimentos disponíveis.")
            ps_medio = 0
            pot_final = 0
        else:
            v_medio = df_pot['Valor de Venda'].mean()
            ps_medio = v_medio * d['perc_ps']
            dobro_renda = 2 * d['renda']
            
            # Cálculo Base: Finan F1 + Sub F1 + Pro Soluto Médio + 2x Renda
            pot_final = d['finan_f1'] + d['sub_f1'] + ps_medio + dobro_renda
        
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="card"><p class="metric-label">Financiamento</p><p class="metric-value">R$ {fmt_br(d["finan_f1"])}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="card"><p class="metric-label">Subsídio</p><p class="metric-value">R$ {fmt_br(d["sub_f1"])}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="card"><p class="metric-label">Pro Soluto</p><p class="metric-value">R$ {fmt_br(ps_medio)}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><p class="metric-label">Capacidade de Entrada</p><p class="metric-value">R$ {fmt_br(2 * d["renda"])}</p></div>', unsafe_allow_html=True)

        st.markdown(f"""
            <div class="card" style="border-top: 4px solid {COR_AZUL_ESC}; background: #ffffff; min-height: 120px;">
                <p class="metric-label" style="color: {COR_AZUL_ESC}; font-size: 0.8rem;">Poder de Aquisição Estimado</p>
                <p class="metric-value" style="font-size: 2.8rem; color: {COR_AZUL_ESC};">R$ {fmt_br(pot_final)}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Avançar para Seleção de Imóvel", type="primary", use_container_width=True, key="btn_s2_v23"):
            st.session_state.passo_simulacao = 'guide'; st.rerun()
        st.write("")
        if st.button("Voltar para Dados do Cliente", use_container_width=True, key="btn_edit_v23"):
            st.session_state.passo_simulacao = 'input'; st.rerun()

    # --- ETAPA 3: SELEÇÃO E RECOMENDAÇÃO ---
    elif st.session_state.passo_simulacao == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### Seleção de Imóvel")
        
        df_disp_total = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
        
        if df_disp_total.empty:
            st.warning("Não há estoque disponível.")
            df_viaveis = pd.DataFrame()
        else:
            def calcular_viabilidade_unidade(row):
                v_venda = row['Valor de Venda']
                fin, sub, fx_n = motor.obter_enquadramento(d['renda'], d['social'], d['cotista'], v_venda)
                # Lógica: Finan Faixa Unidade + (Sub+FGTS) + Pro Soluto + 2x Renda
                poder, ps_u = motor.calcular_poder_compra(d['renda'], fin, sub, d['perc_ps'], v_venda)
                gap = poder - v_venda
                return pd.Series([poder, gap, gap >= 0])

            df_disp_total[['Poder_Compra', 'Gap', 'Viavel']] = df_disp_total.apply(calcular_viabilidade_unidade, axis=1)
            df_disp_total['Status Viabilidade'] = df_disp_total['Viavel'].apply(lambda x: "Viavel" if x else "Inviavel")
            
            # Panorama: Ordenar por Gap Decrescente (Só os viáveis)
            df_viaveis = df_disp_total[df_disp_total['Viavel']].sort_values('Gap', ascending=False).copy()
        
        st.markdown("#### Panorama de Produtos (Viáveis)")
        if df_viaveis.empty:
            st.info("Sem produtos viaveis no perfil selecionado para exibição automática.")
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
                                <p style="margin:5px 0 0 0; font-size:0.85rem; color:{COR_TEXTO_MUTED};">{qtd} unidades viaveis</p>
                            </div>
                        """, unsafe_allow_html=True)

        st.write("")
        tab_rec, tab_list = st.tabs(["Sugestões Inteligentes", "Estoque Geral"])
        
        with tab_rec:
            # Selecionar empreendimento para recomendação
            emp_names_rec = sorted(df_disp_total['Empreendimento'].unique().tolist())
            emp_rec = st.selectbox("Escolha um empreendimento para recomendações:", options=["Todos"] + emp_names_rec, key="sel_emp_rec_v27")
            
            df_pool = df_disp_total if emp_rec == "Todos" else df_disp_total[df_disp_total['Empreendimento'] == emp_rec]
            
            if df_pool.empty:
                st.info("Nenhuma unidade encontrada para este filtro.")
            else:
                # Função auxiliar de seleção (sempre recomenda algo)
                def obter_melhor_ajuste(df_base, limite_poder):
                    # Tenta unidades dentro do preço (melhor custo-benefício, ou seja, a mais cara que cabe)
                    dentro_orcamento = df_base[df_base['Valor de Venda'] <= limite_poder]
                    if not dentro_orcamento.empty:
                        return dentro_orcamento.sort_values('Valor de Venda', ascending=False).iloc[0]
                    else:
                        # Se nenhuma cabe, recomenda a MAIS BARATA disponível
                        return df_base.sort_values('Valor de Venda', ascending=True).iloc[0]

                # 1. Ideal (100% do Poder)
                # Poder de compra varia por unidade (faixa), então usamos a média do pool para estimar o limite
                ideal = obter_melhor_ajuste(df_pool, df_pool['Poder_Compra'].mean())
                
                # 2. Seguro (90% do Poder)
                seguro = obter_melhor_ajuste(df_pool, df_pool['Poder_Compra'].mean() * 0.90)
                
                # 3. Facilitado (75% do Poder)
                facilitado = obter_melhor_ajuste(df_pool, df_pool['Poder_Compra'].mean() * 0.75)

                c1, c2, c3 = st.columns(3)
                with c1: 
                    st.markdown(f'''<div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC};">
                        <span style="font-size:0.7rem; color:{COR_TEXTO_MUTED}">PERFIL</span><br><b>IDEAL</b><br>
                        <small>{ideal["Empreendimento"]}</small><br>Unid. {ideal["Identificador"]}<br>
                        <div class="price-tag">R$ {fmt_br(ideal["Valor de Venda"])}</div>
                        <small style="color:{COR_TEXTO_MUTED}">100% do Poder de Compra</small>
                    </div>''', unsafe_allow_html=True)
                with c2: 
                    st.markdown(f'''<div class="recommendation-card" style="border-top: 4px solid {COR_VERMELHO};">
                        <span style="font-size:0.7rem; color:{COR_TEXTO_MUTED}">PERFIL</span><br><b>SEGURO</b><br>
                        <small>{seguro["Empreendimento"]}</small><br>Unid. {seguro["Identificador"]}<br>
                        <div class="price-tag">R$ {fmt_br(seguro["Valor de Venda"])}</div>
                        <small style="color:{COR_TEXTO_MUTED}">90% do Poder de Compra</small>
                    </div>''', unsafe_allow_html=True)
                with c3: 
                    st.markdown(f'''<div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC};">
                        <span style="font-size:0.7rem; color:{COR_TEXTO_MUTED}">PERFIL</span><br><b>FACILITADO</b><br>
                        <small>{facilitado["Empreendimento"]}</small><br>Unid. {facilitado["Identificador"]}<br>
                        <div class="price-tag">R$ {fmt_br(facilitado["Valor de Venda"])}</div>
                        <small style="color:{COR_TEXTO_MUTED}">75% do Poder de Compra</small>
                    </div>''', unsafe_allow_html=True)

        with tab_list:
            if df_disp_total.empty:
                st.info("Sem dados para exibir.")
            else:
                f1, f2, f3, f4 = st.columns([1.2, 1, 0.7, 1.1])
                with f1: f_emp = st.multiselect("Empreendimento:", options=sorted(df_disp_total['Empreendimento'].unique()), key="f_emp_tab_v25")
                with f2: f_status_v = st.multiselect("Viabilidade:", options=["Viavel", "Inviavel"], key="f_status_tab_v25")
                with f3: f_ordem = st.selectbox("Ordem:", ["Maior Gap", "Menor Gap", "Maior Preço"], key="f_ordem_tab_v25")
                with f4: f_pmax = st.number_input("Preço Máx:", value=float(df_disp_total['Valor de Venda'].max()), key="f_pmax_tab_v25")
                
                df_tab = df_disp_total.copy()
                if f_emp: df_tab = df_tab[df_tab['Empreendimento'].isin(f_emp)]
                if f_status_v: df_tab = df_tab[df_tab['Status Viabilidade'].isin(f_status_v)]
                df_tab = df_tab[df_tab['Valor de Venda'] <= f_pmax]
                
                if f_ordem == "Maior Gap": df_tab = df_tab.sort_values('Gap', ascending=False)
                elif f_ordem == "Menor Gap": df_tab = df_tab.sort_values('Gap', ascending=True)
                else: df_tab = df_tab.sort_values('Valor de Venda', ascending=False)
                
                df_tab_view = df_tab.copy()
                df_tab_view['Valor de Venda'] = df_tab_view['Valor de Venda'].apply(fmt_br)
                df_tab_view['Poder_Compra'] = df_tab_view['Poder_Compra'].apply(fmt_br)
                df_tab_view['Gap'] = df_tab_view['Gap'].apply(fmt_br)

                st.dataframe(
                    df_tab_view[['Identificador', 'Empreendimento', 'Valor de Venda', 'Poder_Compra', 'Gap', 'Status Viabilidade']], 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Identificador": st.column_config.TextColumn("Unidade"),
                        "Valor de Venda": st.column_config.TextColumn("Preço (R$)"),
                        "Poder_Compra": st.column_config.TextColumn("Poder (R$)"),
                        "Gap": st.column_config.TextColumn("Saldo (R$)"),
                    }
                )

        st.markdown("---")
        st.markdown("### Seleção de Unidade para Fechamento")
        emp_names = sorted(df_estoque[df_estoque['Status'] == 'Disponível']['Empreendimento'].unique())
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            emp_escolhido = st.selectbox("Escolha o Empreendimento:", options=emp_names, key="sel_emp_guide_v26")
        
        # Filtra e ordena as unidades por Bloco, Andar e Apartamento
        unidades_disp = df_estoque[(df_estoque['Empreendimento'] == emp_escolhido) & (df_estoque['Status'] == 'Disponível')].copy()
        unidades_disp = unidades_disp.sort_values(['Bloco_Sort', 'Andar', 'Apto_Sort'])
        
        with col_sel2:
            if unidades_disp.empty:
                st.warning("Sem estoque disponivel.")
                uni_escolhida_id = None
            else:
                def label_uni(uid):
                    u_row = unidades_disp[unidades_disp['Identificador'] == uid].iloc[0]
                    return f"{uid} (R$ {fmt_br(u_row['Valor de Venda'])})"
                uni_escolhida_id = st.selectbox("Escolha a Unidade:", options=unidades_disp['Identificador'].unique(), 
                                                format_func=label_uni, key="sel_uni_guide_v26")

        if st.button("Avançar para Fechamento Financeiro", type="primary", use_container_width=True, key="btn_fech_v26"):
            if uni_escolhida_id:
                u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                fin_real, sub_real, faixa_real = motor.obter_enquadramento(d['renda'], d['social'], d['cotista'], u_row['Valor de Venda'])
                
                st.session_state.dados_cliente.update({
                    'unidade_id': uni_escolhida_id,
                    'empreendimento_nome': emp_escolhido,
                    'imovel_valor': u_row['Valor de Venda'],
                    'finan_estimado': fin_real,
                    'fgts_sub': sub_real,
                    'faixa_unidade': faixa_real
                })
                st.session_state.passo_simulacao = 'payment_flow'
                st.rerun()
            else:
                st.error("Por favor, selecione uma unidade.")
        
        if st.button("Voltar para Valor Potencial", use_container_width=True, key="btn_pot_v23"): 
            st.session_state.passo_simulacao = 'potential'; st.rerun()

    # --- ETAPA 4: FECHAMENTO ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### Fechamento Financeiro")
        
        u_valor = d.get('imovel_valor', 0)
        st.markdown(f'<div class="custom-alert">Unidade Selecionada: {d["unidade_id"]} - {d["empreendimento_nome"]} (R$ {fmt_br(u_valor)})</div>', unsafe_allow_html=True)
        
        # --- NOVO: REFERÊNCIAS DE POLÍTICA ---
        st.markdown(f"""
            <div class="policy-ref-table">
                <div class="policy-ref-title">Referências de Política para este Perfil</div>
                <div class="policy-grid">
                    <div class="policy-item">
                        <div class="policy-item-label">Faixa do Imóvel</div>
                        <div class="policy-item-value">{d.get('faixa_unidade', 'N/A')}</div>
                    </div>
                    <div class="policy-item">
                        <div class="policy-item-label">Ref. Finan/Sub</div>
                        <div class="policy-item-value">R$ {fmt_br(d.get('finan_estimado',0) + d.get('fgts_sub',0))}</div>
                    </div>
                    <div class="policy-item">
                        <div class="policy-item-label">PS Permitido</div>
                        <div class="policy-item-value">{d.get('perc_ps', 0)*100:.0f}% (R$ {fmt_br(u_valor * d.get('perc_ps',0))})</div>
                    </div>
                    <div class="policy-item">
                        <div class="policy-item-label">Parcelas Máx.</div>
                        <div class="policy-item-value">{d.get('prazo_ps_max', 0)}x permitidas</div>
                    </div>
                </div>
                <div style="margin-top:10px; font-size:0.65rem; color:#94a3b8; font-weight:600;">
                    Limite de Comprometimento: {d.get('limit_ps_renda', 0)*100:.0f}% da renda de R$ {fmt_br(d.get('renda',0))}
                </div>
            </div>
        """, unsafe_allow_html=True)

        f_u = st.number_input("Financiamento Bancário", value=float(d['finan_estimado']), step=1000.0, key="fin_u_v23")
        fgts_u = st.number_input("FGTS + Subsídio", value=float(d['fgts_sub']), step=1000.0, key="fgt_u_v23")
        
        ps_max_real = u_valor * d['perc_ps']
        ps_u = st.number_input("Pro Soluto Direcional", value=float(ps_max_real), step=1000.0, key="ps_u_v23")
        
        parc = st.number_input("Número de Parcelas Pro Soluto", min_value=1, max_value=144, value=d['prazo_ps_max'], key="parc_u_v23")
        
        v_parc = ps_u / parc
        comp_r = (v_parc / d['renda'])
        saldo_e = u_valor - f_u - fgts_u - ps_u

        calc_hash = f"{f_u}-{fgts_u}-{ps_u}-{d['unidade_id']}"
        if 'last_calc_hash' not in st.session_state or st.session_state.last_calc_hash != calc_hash:
            dist_val = max(0.0, saldo_e / 4)
            st.session_state.ato_1, st.session_state.ato_2 = dist_val, dist_val
            st.session_state.ato_3, st.session_state.ato_4 = dist_val, dist_val
            st.session_state.last_calc_hash = calc_hash
        
        fin1, fin2, fin3 = st.columns(3)
        with fin1: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b>VALOR DO IMÓVEL</b><br>R$ {fmt_br(u_valor)}</div>""", unsafe_allow_html=True)
        with fin2: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_VERMELHO};"><b>MENSALIDADE PS</b><br>R$ {fmt_br(v_parc)} ({parc}x)</div>""", unsafe_allow_html=True)
        with fin3: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b>SALDO DE ENTRADA</b><br>R$ {fmt_br(max(0, saldo_e))}</div>""", unsafe_allow_html=True)
        
        if comp_r > d['limit_ps_renda']:
            st.warning(f"Atenção: Parcela Pro Soluto excede o limite de {d['limit_ps_renda']*100:.0f}% da renda.")

        if saldo_e > 0:
            st.markdown("#### Distribuição da Entrada")
            col_a, col_b = st.columns(2)
            with col_a:
                st.session_state.ato_1 = st.number_input("Ato", value=st.session_state.ato_1, key="ato_1_v24")
                st.session_state.ato_3 = st.number_input("Ato 60", value=st.session_state.ato_3, key="ato_3_v24")
            with col_b:
                st.session_state.ato_2 = st.number_input("Ato 30", value=st.session_state.ato_2, key="ato_2_v24")
                st.session_state.ato_4 = st.number_input("Ato 90", value=st.session_state.ato_4, key="ato_4_v24")
            
            soma_entrada = st.session_state.ato_1 + st.session_state.ato_2 + st.session_state.ato_3 + st.session_state.ato_4
            if abs(soma_entrada - saldo_e) > 0.1:
                st.error(f"Erro na Distribuição: A soma (R$ {fmt_br(soma_entrada)}) difere do saldo (R$ {fmt_br(saldo_e)}).")
        
        st.session_state.dados_cliente.update({
            'finan_usado': f_u, 'fgts_sub_usado': fgts_u,
            'ps_usado': ps_u, 'ps_parcelas': parc, 'ps_mensal': v_parc, 'entrada_total': saldo_e,
            'ato_final': st.session_state.ato_1, 'ato_30': st.session_state.ato_2,
            'ato_60': st.session_state.ato_3, 'ato_90': st.session_state.ato_4
        })
        
        st.markdown("---")
        if st.button("Avançar para Resumo de Compra", type="primary", use_container_width=True, key="btn_to_summary"):
            st.session_state.passo_simulacao = 'summary'; st.rerun()
        if st.button("Voltar para Seleção de Imóvel", use_container_width=True, key="btn_back_to_guide"): 
            st.session_state.passo_simulacao = 'guide'; st.rerun()

    # --- ETAPA 5: RESUMO ---
    elif st.session_state.passo_simulacao == 'summary':
        d = st.session_state.dados_cliente
        st.markdown(f"### Resumo da Simulação - {d.get('nome', 'Cliente')}")
        
        if PDF_ENABLED:
            pdf_data = gerar_resumo_pdf(d)
            if pdf_data:
                _, col_btn_center, _ = st.columns([1, 1.2, 1])
                with col_btn_center:
                    st.download_button(
                        label="Baixar Resumo em PDF", 
                        data=pdf_data, 
                        file_name=f"Resumo Direcional - {d.get('nome', 'Cliente')}.pdf", 
                        mime="application/pdf",
                        use_container_width=True,
                        key="btn_download_pdf_final"
                    )

        st.markdown(f'<div class="summary-header">DADOS DO IMÓVEL</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Empreendimento:</b> {d.get('empreendimento_nome')}<br>
            <b>Unidade:</b> {d.get('unidade_id')}<br><b>Valor de Venda:</b> <span style="color: {COR_VERMELHO}; font-weight: 800;">R$ {fmt_br(d.get('imovel_valor', 0))}</span></div>""", unsafe_allow_html=True)

        st.markdown(f'<div class="summary-header">PLANO DE FINANCIAMENTO</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Financiamento Bancário:</b> R$ {fmt_br(d.get('finan_usado', 0))}<br>
            <b>FGTS + Subsídio:</b> R$ {fmt_br(d.get('fgts_sub_usado', 0))}<br>
            <b>Pro Soluto Total:</b> R$ {fmt_br(d.get('ps_usado', 0))} ({d.get('ps_parcelas')}x de R$ {fmt_br(d.get('ps_mensal', 0))})</div>""", unsafe_allow_html=True)

        st.markdown(f'<div class="summary-header">FLUXO DE ENTRADA (ATO)</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Total de Entrada:</b> R$ {fmt_br(d.get('entrada_total', 0))}<br><hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 10px 0;">
            <b>Ato:</b> R$ {fmt_br(d.get('ato_final', 0))}<br><b>Ato 30 Dias:</b> R$ {fmt_br(d.get('ato_30', 0))}<br>
            <b>Ato 60 Dias:</b> R$ {fmt_br(d.get('ato_60', 0))}<br><b>Ato 90 Dias:</b> R$ {fmt_br(d.get('ato_90', 0))}</div>""", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("Fazer Nova Simulação", type="primary", use_container_width=True, key="btn_new_client_summary"): 
            st.session_state.dados_cliente = {}; st.session_state.passo_simulacao = 'input'; st.rerun()
        if st.button("Voltar para Fechamento Financeiro", use_container_width=True, key="btn_edit_fin_summary"):
            st.session_state.passo_simulacao = 'payment_flow'; st.rerun()

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()
    if df_finan.empty or df_estoque.empty:
        st.warning("Aguardando conexão com base de dados...")
        st.stop()
    
    logo_src = URL_FAVICON_RESERVA
    if os.path.exists("favicon.png"):
        try:
            with open("favicon.png", "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                logo_src = f"data:image/png;base64,{encoded}"
        except: pass

    st.markdown(f'''
        <div class="header-container">
            <img src="{logo_src}" style="position: absolute; top: 30px; left: 40px; height: 50px;">
            <div class="header-title">SIMULADOR IMOBILIÁRIO DV</div>
            <div class="header-subtitle">Sistema de Gestão de Vendas e Viabilidade Imobiliária</div>
        </div>
    ''', unsafe_allow_html=True)
    
    aba_simulador_automacao(df_finan, df_estoque, df_politicas)
    st.markdown(f'<div class="footer">Direcional Engenharia - Rio de Janeiro | Developed by Lucas Maia</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
