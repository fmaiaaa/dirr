# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V3 (FINAL ADJUSTED)
=============================================================================
Instruções para Google Colab:
1. Crie um arquivo chamado 'app.py' com este conteúdo.
2. Instale as dependências:
   !pip install streamlit pandas numpy fpdf streamlit-gsheets
3. Rode o app:
   !streamlit run app.py & npx localtunnel --port 8501
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
from datetime import datetime, date
import time
import locale
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Tenta importar fpdf
try:
    from fpdf import FPDF
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

try:
    from PIL import Image
except ImportError:
    Image = None
import os

# Configuração de Locale
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except:
        pass

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

# Paleta de Cores
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

def limpar_cpf_visual(valor):
    if pd.isnull(valor) or valor == "": return ""
    v_str = str(valor).strip()
    if v_str.endswith('.0'): v_str = v_str[:-2]
    v_nums = re.sub(r'\D', '', v_str)
    if v_nums: return v_nums.zfill(11)
    return ""

def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', str(cpf))
    if len(cpf) != 11 or len(set(cpf)) == 1: return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto == 10: resto = 0
    if resto != int(cpf[9]): return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto == 10: resto = 0
    if resto != int(cpf[10]): return False
    return True

def calcular_cor_gradiente(valor):
    valor = max(0, min(100, valor))
    if valor < 50:
        fator = valor / 50
        r, g, b = 255, int(255 * fator), 0
    else:
        fator = (valor - 50) / 50
        r, g, b = int(255 * (1 - fator)), 255, 0
    return f"rgb({r},{g},{b})"

# =============================================================================
# 1. CARREGAMENTO DE DADOS
# =============================================================================

@st.cache_data(ttl=300)
def carregar_dados_sistema():
    try:
        if "connections" not in st.secrets:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        conn = st.connection("gsheets", type=GSheetsConnection)

        def limpar_porcentagem(val):
            if isinstance(val, str):
                v = val.replace('%', '').replace(',', '.').strip()
                try: return float(v) / 100 if float(v) > 1 else float(v)
                except: return 0.0
            return val

        def limpar_moeda(val):
            if isinstance(val, (int, float)): return float(val)
            if isinstance(val, str):
                val = val.replace('R$', '').replace('.', '').replace(',', '.').strip()
                try: return float(val)
                except: return 0.0
            return 0.0

        # Logins
        try:
            df_logins = conn.read(spreadsheet=URL_RANKING, worksheet="Logins")
            df_logins.columns = [str(c).strip() for c in df_logins.columns]
            mapa = {}
            for col in df_logins.columns:
                c_low = col.lower()
                if "senha" in c_low: mapa[col] = 'Senha'
                elif "imob" in c_low or "canal" in c_low: mapa[col] = 'Imobiliaria'
                elif "email" in c_low: mapa[col] = 'Email'
                elif "nome" in c_low: mapa[col] = 'Nome'
                elif "cargo" in c_low: mapa[col] = 'Cargo'
            df_logins = df_logins.rename(columns=mapa)
            for c in ['Email', 'Senha', 'Imobiliaria', 'Cargo', 'Nome']:
                if c not in df_logins.columns: df_logins[c] = ""
            df_logins['Email'] = df_logins['Email'].astype(str).str.strip().str.lower()
            df_logins['Senha'] = df_logins['Senha'].astype(str).str.strip()
            df_logins = df_logins.drop_duplicates(subset=['Email'], keep='last')
        except: df_logins = pd.DataFrame(columns=['Email', 'Senha', 'Imobiliaria', 'Cargo', 'Nome'])

        # Cadastros
        try:
            df_cadastros = conn.read(spreadsheet=URL_RANKING, worksheet="Cadastros")
            df_cadastros.columns = [str(c).strip() for c in df_cadastros.columns]
        except: df_cadastros = pd.DataFrame()

        # Politicas
        try:
            df_politicas = conn.read(spreadsheet=URL_RANKING)
            df_politicas.columns = [str(c).strip() for c in df_politicas.columns]
            col_class = next((c for c in df_politicas.columns if 'CLASSIFICA' in c.upper() or 'RANKING' in c.upper()), 'CLASSIFICAÇÃO')
            df_politicas = df_politicas.rename(columns={col_class: 'CLASSIFICAÇÃO', 'FAIXA RENDA': 'FAIXA_RENDA', 'FX RENDA 1': 'FX_RENDA_1', 'FX RENDA 2': 'FX_RENDA_2'})
            for col in ['PROSOLUTO', 'FX_RENDA_1', 'FX_RENDA_2']:
                if col in df_politicas.columns: df_politicas[col] = df_politicas[col].apply(limpar_porcentagem)
        except: df_politicas = pd.DataFrame()

        # Financeiro
        try:
            df_finan = conn.read(spreadsheet=URL_FINAN)
            df_finan.columns = [str(c).strip() for c in df_finan.columns]
            for col in df_finan.columns: df_finan[col] = df_finan[col].apply(limpar_moeda)
        except: df_finan = pd.DataFrame()

        # Estoque
        try:
            df_raw = conn.read(spreadsheet=URL_ESTOQUE)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            try:
                df_filtro = conn.read(spreadsheet=URL_ESTOQUE, worksheet="Página2")
                lista_permitidos = df_filtro['Nome do empreendimento'].dropna().astype(str).str.strip().unique() if 'Nome do empreendimento' in df_filtro.columns else None
            except: lista_permitidos = None

            df_estoque = df_raw.rename(columns={'Nome do Empreendimento': 'Empreendimento', 'VALOR DE VENDA': 'Valor de Venda', 'Status da unidade': 'Status'})
            df_estoque['Valor de Venda'] = df_estoque['Valor de Venda'].apply(limpar_moeda)
            col_aval = 'VALOR DE AVALIACAO BANCARIA' if 'VALOR DE AVALIACAO BANCARIA' in df_raw.columns else 'Valor de Avaliação Bancária'
            df_estoque['Valor de Avaliação Bancária'] = df_raw[col_aval].apply(limpar_moeda) if col_aval in df_raw.columns else df_estoque['Valor de Venda']
            
            if lista_permitidos is not None:
                df_estoque = df_estoque[df_estoque['Empreendimento'].astype(str).str.strip().isin(lista_permitidos)]
            
            df_estoque = df_estoque[(df_estoque['Valor de Venda'] > 0) & (df_estoque['Empreendimento'].notnull())].copy()
            if 'Identificador' not in df_estoque.columns: df_estoque['Identificador'] = df_estoque.index.astype(str)
            if 'Bairro' not in df_estoque.columns: df_estoque['Bairro'] = 'Rio de Janeiro'

            def extrair_dados_unid(id_unid, tipo):
                try:
                    s = str(id_unid)
                    p, sx = (s.split('-')[0], s.split('-')[-1]) if '-' in s else (s, s)
                    np_val = re.sub(r'\D', '', p)
                    ns_val = re.sub(r'\D', '', sx)
                    if tipo == 'andar': return int(ns_val)//100 if ns_val else 0
                    if tipo == 'bloco': return int(np_val) if np_val else 1
                    if tipo == 'apto': return int(ns_val) if ns_val else 0
                except: return 0 if tipo != 'bloco' else 1

            df_estoque['Andar'] = df_estoque['Identificador'].apply(lambda x: extrair_dados_unid(x, 'andar'))
            df_estoque['Bloco_Sort'] = df_estoque['Identificador'].apply(lambda x: extrair_dados_unid(x, 'bloco'))
            df_estoque['Apto_Sort'] = df_estoque['Identificador'].apply(lambda x: extrair_dados_unid(x, 'apto'))
        except: df_estoque = pd.DataFrame()

        return df_finan, df_estoque, df_politicas, df_logins, df_cadastros
    except Exception as e:
        st.error(f"Erro dados: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# =============================================================================
# 2. MOTOR E FUNÇÕES
# =============================================================================

class MotorRecomendacao:
    def __init__(self, df_finan, df_estoque, df_politicas):
        self.df_finan = df_finan
        self.df_estoque = df_estoque
        self.df_politicas = df_politicas

    def obter_enquadramento(self, renda, social, cotista, valor_avaliacao=250000):
        if self.df_finan.empty: return 0.0, 0.0, "N/A"
        if valor_avaliacao <= 190000: faixa = "F1"
        elif valor_avaliacao <= 275000: faixa = "F2"
        elif valor_avaliacao <= 350000: faixa = "F3"
        else: faixa = "F4"
        
        renda_col = pd.to_numeric(self.df_finan['Renda'], errors='coerce').fillna(0)
        idx = (renda_col - renda).abs().idxmin()
        row = self.df_finan.iloc[idx]
        
        s, c = ('Sim' if social else 'Nao'), ('Sim' if cotista else 'Nao')
        vf = row.get(f"Finan_Social_{s}_Cotista_{c}_{faixa}", 0.0)
        vs = row.get(f"Subsidio_Social_{s}_Cotista_{c}_{faixa}", 0.0)
        
        if vf == 0 and faixa == "F1":
            vf = row.get(f"Finan_Social_{s}_Cotista_{c}_F2", 0.0)
            vs = row.get(f"Subsidio_Social_{s}_Cotista_{c}_F2", 0.0)
        return float(vf), float(vs), faixa

    def calcular_poder_compra(self, renda, finan, fgts_sub, perc_ps, valor_unidade):
        ps = valor_unidade * perc_ps
        return (2 * renda) + finan + fgts_sub + ps, ps

def configuring_layout():
    favicon = URL_FAVICON_RESERVA
    if os.path.exists("favicon.png") and Image:
        try: favicon = Image.open("favicon.png")
        except: pass
    st.set_page_config(page_title="Simulador Direcional Elite", page_icon=favicon, layout="wide")
    
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', sans-serif;
            color: {COR_AZUL_ESC}; 
            background-color: {COR_FUNDO};
        }}
        
        h1, h2, h3, h4 {{
            font-family: 'Montserrat', sans-serif !important;
            text-align: center !important; 
            color: {COR_AZUL_ESC} !important; 
            font-weight: 800;
            letter-spacing: -0.04em;
        }}

        .stMarkdown p, .stText, label, .stSelectbox label, .stTextInput label, .stNumberInput label {{
            color: {COR_AZUL_ESC} !important;
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

        .stTextInput input, .stNumberInput input, .stDateInput input {{
            padding: 14px 18px !important;
            color: {COR_AZUL_ESC} !important;
        }}
        
        div[data-testid="stDateInput"] {{ border-radius: 8px !important; }}
        div[data-testid="stDateInput"] > div {{ border-radius: 8px !important; border: 1px solid #e2e8f0 !important; background-color: #f0f2f6 !important; }}
        div[data-testid="stDateInput"] div[data-baseweb="input"] {{ border: none !important; background-color: transparent !important; }}
        
        div[data-testid="stNumberInput"] button:hover {{
            background-color: {COR_VERMELHO} !important;
            color: #ffffff !important;
            border-color: {COR_VERMELHO} !important;
        }}

        div[data-testid="stToggle"] div[aria-checked="true"] {{ background-color: {COR_VERMELHO} !important; }}
        
        .stButton button {{ 
            font-family: 'Inter', sans-serif;
            border-radius: 8px !important; 
            padding: 20px 40px !important; 
            width: 100% !important;
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
            color: {COR_AZUL_ESC}; 
            font-size: 1rem; 
            font-weight: 600; 
            margin-top: 15px; 
            letter-spacing: 0.1em;
            text-transform: uppercase;
            opacity: 0.8;
        }}
        
        .card, .fin-box, .recommendation-card, .login-card {{ 
            background: #ffffff; 
            padding: 25px; 
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
            font-weight: 400; 
            color: #ffffff !important; 
        }}
        .price-tag {{ 
            color: {COR_VERMELHO}; 
            font-weight: 900; 
            font-size: 1.5rem; 
            margin-top: 5px; 
        }}
        .inline-ref {{
            font-size: 0.72rem;
            color: {COR_AZUL_ESC};
            margin-top: -12px;
            margin-bottom: 15px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: block;
            opacity: 0.9;
        }}
        
        .metric-label {{ color: {COR_AZUL_ESC} !important; opacity: 0.7; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 8px; }}
        .metric-value {{ color: {COR_AZUL_ESC} !important; font-size: 1.8rem; font-weight: 800; font-family: 'Montserrat', sans-serif; }}

        /* BADGES */
        .badge-ideal {{ background-color: #22c55e; color: white; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; margin-top: 10px; text-transform: uppercase; letter-spacing: 0.05em; }}
        .badge-seguro {{ background-color: #eab308; color: white; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; margin-top: 10px; text-transform: uppercase; letter-spacing: 0.05em; }}
        .badge-facilitado {{ background-color: #f97316; color: white; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; margin-top: 10px; text-transform: uppercase; letter-spacing: 0.05em; }}
        .badge-multi {{ background: linear-gradient(90deg, #eab308 0%, #f97316 100%); color: white; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; margin-top: 10px; text-transform: uppercase; letter-spacing: 0.05em; }}

        /* Sidebar Styling */
        [data-testid="stSidebar"] {{ background-color: #fff; border-right: 1px solid {COR_BORDA}; }}
        .profile-container {{ text-align: center; margin-bottom: 10px; padding: 15px; background: #f8fafc; border-radius: 12px; }}
        .profile-name {{ font-weight: 800; font-size: 1.1rem; color: {COR_AZUL_ESC}; }}
        .profile-role {{ font-size: 0.85rem; color: #64748b; font-weight: 600; margin-bottom: 5px; }}
        .profile-sub {{ font-size: 0.8rem; color: #94a3b8; }}
        
        .hist-item {{ display: block; width: 100%; text-align: left; padding: 12px; margin-bottom: 8px; border-radius: 8px; background: #fff; border: 1px solid {COR_BORDA}; color: {COR_AZUL_ESC}; font-size: 0.85rem; transition: all 0.2s; }}
        .hist-item:hover {{ border-color: {COR_VERMELHO}; background: #fff5f5; }}

        /* Tabs Centered */
        div[data-baseweb="tab-list"] {{ justify-content: center !important; gap: 40px; margin-bottom: 40px; }}
        button[data-baseweb="tab"] p {{ color: {COR_AZUL_ESC} !important; opacity: 0.6; font-weight: 700 !important; font-family: 'Montserrat', sans-serif !important; font-size: 0.9rem !important; text-transform: uppercase; letter-spacing: 0.1em; }}
        button[data-baseweb="tab"][aria-selected="true"] p {{ color: {COR_AZUL_ESC} !important; opacity: 1; }}
        div[data-baseweb="tab-highlight"] {{ background-color: {COR_VERMELHO} !important; height: 3px !important; }}
        
        .footer {{ text-align: center; padding: 80px 0; color: {COR_AZUL_ESC} !important; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; opacity: 0.6; }}
        </style>
    """, unsafe_allow_html=True)

# ... (Funções PDF e Email) ...
def gerar_resumo_pdf(d):
    if not PDF_ENABLED: return None
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        AZUL_RGB, VERMELHO_RGB, BRANCO_RGB, FUNDO_SECAO = (0, 44, 93), (227, 6, 19), (255, 255, 255), (248, 250, 252)
        pdf.set_fill_color(*AZUL_RGB); pdf.rect(0, 0, 210, 3, 'F')
        if os.path.exists("favicon.png"):
            try: pdf.image("favicon.png", 10, 8, 10)
            except: pass
        pdf.ln(15); pdf.set_text_color(*AZUL_RGB); pdf.set_font("Helvetica", 'B', 22); pdf.cell(0, 12, "RELATÓRIO DE VIABILIDADE", ln=True, align='C')
        pdf.set_font("Helvetica", '', 9); pdf.cell(0, 6, "SIMULADOR IMOBILIÁRIO DV - DOCUMENTO EXECUTIVO", ln=True, align='C'); pdf.ln(15)
        pdf.set_fill_color(*FUNDO_SECAO); pdf.rect(10, pdf.get_y(), 190, 24, 'F'); pdf.set_xy(15, pdf.get_y() + 6)
        pdf.set_text_color(*AZUL_RGB); pdf.set_font("Helvetica", 'B', 13); pdf.cell(0, 6, f"CLIENTE: {d.get('nome', 'Nao informado').upper()}", ln=True)
        pdf.set_x(15); pdf.set_font("Helvetica", '', 10); pdf.cell(0, 6, f"Renda Familiar: R$ {fmt_br(d.get('renda', 0))}", ln=True); pdf.ln(15)

        def adicionar_secao_pdf(titulo):
            pdf.set_fill_color(*AZUL_RGB); pdf.set_text_color(*BRANCO_RGB); pdf.set_font("Helvetica", 'B', 10); pdf.cell(0, 10, f"   {titulo}", ln=True, fill=True); pdf.ln(4)

        def adicionar_linha_detalhe(label, valor, destaque=False):
            pdf.set_x(15); pdf.set_text_color(*AZUL_RGB); pdf.set_font("Helvetica", '', 10); pdf.cell(110, 9, label, border=0)
            if destaque: pdf.set_text_color(*VERMELHO_RGB); pdf.set_font("Helvetica", 'B', 10)
            else: pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(0, 9, valor, border=0, ln=True, align='R'); pdf.set_draw_color(241, 245, 249); pdf.line(15, pdf.get_y(), 195, pdf.get_y())

        adicionar_secao_pdf("DADOS DO IMÓVEL")
        adicionar_linha_detalhe("Empreendimento", str(d.get('empreendimento_nome')))
        adicionar_linha_detalhe("Unidade Selecionada", str(d.get('unidade_id')))
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
        pdf.set_y(-25); pdf.set_font("Helvetica", 'I', 7); pdf.set_text_color(*AZUL_RGB)
        pdf.cell(0, 4, "Simulação sujeita a aprovação de crédito e alteração de tabela sem aviso prévio.", ln=True, align='C')
        pdf.cell(0, 4, "Direcional Engenharia - Rio de Janeiro", ln=True, align='C')
        return bytes(pdf.output())
    except: return None

def enviar_email_smtp(destinatario, nome_cliente, pdf_bytes):
    if "email" not in st.secrets: return False, "Configurações de e-mail não encontradas."
    try:
        smtp_server = st.secrets["email"]["smtp_server"].strip()
        smtp_port = int(st.secrets["email"]["smtp_port"])
        sender_email = st.secrets["email"]["sender_email"].strip()
        sender_password = st.secrets["email"]["sender_password"].strip().replace(" ", "")
    except Exception as e: return False, f"Erro config: {e}"

    msg = MIMEMultipart()
    msg['From'] = sender_email; msg['To'] = destinatario; msg['Subject'] = f"Resumo da Simulação - {nome_cliente}"
    msg.attach(MIMEText(f"Olá,\n\nSegue em anexo o resumo da simulação imobiliária para {nome_cliente}.\n\nAtenciosamente,\nDirecional Engenharia", 'plain'))
    if pdf_bytes:
        part = MIMEApplication(pdf_bytes, Name=f"Resumo_{nome_cliente}.pdf")
        part['Content-Disposition'] = f'attachment; filename="Resumo_{nome_cliente}.pdf"'
        msg.attach(part)
    try:
        server = smtplib.SMTP(smtp_server, smtp_port); server.ehlo(); server.starttls(); server.ehlo()
        server.login(sender_email, sender_password); server.sendmail(sender_email, destinatario, msg.as_string()); server.quit()
        return True, "E-mail enviado com sucesso!"
    except smtplib.SMTPAuthenticationError:
        return False, "Erro de Autenticação (535). Verifique Senha de App."
    except Exception as e: return False, f"Erro envio: {e}"

def tela_login(df_logins):
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br><h3 style='text-align:center;'>LOGIN</h3>", unsafe_allow_html=True)
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_pass")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ACESSAR SISTEMA", type="primary", use_container_width=True):
            if df_logins.empty: st.error("Base de usuários vazia.")
            else:
                user = df_logins[(df_logins['Email'] == email.strip().lower()) & (df_logins['Senha'] == senha.strip())]
                if not user.empty:
                    data = user.iloc[0]
                    st.session_state.update({
                        'logged_in': True, 'user_email': email,
                        'user_name': str(data.get('Nome', '')).strip(),
                        'user_imobiliaria': str(data.get('Imobiliaria', 'Geral')).strip(),
                        'user_cargo': str(data.get('Cargo', '')).strip()
                    })
                    st.success("Login realizado!"); st.rerun()
                else: st.error("Credenciais inválidas.")

@st.dialog("Opções de Exportação")
def show_export_dialog(d):
    st.markdown("Escolha como deseja exportar o resumo da simulação.")
    pdf_data = gerar_resumo_pdf(d)
    
    if pdf_data:
        st.download_button(label="📄 Baixar PDF", data=pdf_data, file_name=f"Resumo_Direcional_{d.get('nome', 'Cliente')}.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.warning("Geração de PDF indisponível.")
    
    st.markdown("---")
    st.markdown("**Enviar por E-mail**")
    email = st.text_input("Endereço de e-mail", placeholder="cliente@exemplo.com")
    if st.button("✉️ Enviar Email", use_container_width=True):
        if email and "@" in email:
            sucesso, msg = enviar_email_smtp(email, d.get('nome', 'Cliente'), pdf_data)
            if sucesso: st.success(msg)
            else: st.error(msg)
        else:
            st.error("E-mail inválido")

# =============================================================================
# APLICAÇÃO PRINCIPAL
# =============================================================================

def aba_simulador_automacao(df_finan, df_estoque, df_politicas, df_cadastros):
    passo = st.session_state.get('passo_simulacao', 'input')
    motor = MotorRecomendacao(df_finan, df_estoque, df_politicas)
    if 'dados_cliente' not in st.session_state: st.session_state.dados_cliente = {}

    # --- SIDEBAR PERFIL (ATUALIZADA: SEM FOTO, DADOS DIRETOS) ---
    with st.sidebar:
        user_name = st.session_state.get('user_name', 'Corretor').upper()
        user_cargo = st.session_state.get('user_cargo', 'Consultor').upper()
        user_imob = st.session_state.get('user_imobiliaria', 'Direcional').upper()
        
        st.markdown(f"""
        <div class="profile-container">
            <div class="profile-name">{user_name}</div>
            <div class="profile-role">{user_cargo}</div>
            <div class="profile-sub">{user_imob}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### Histórico de Simulações")
        
        search_term = st.text_input("Buscar cliente...", placeholder="Digite o nome", label_visibility="collapsed")
        
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df_h = conn.read(spreadsheet=URL_RANKING, worksheet="Cadastros")
            if not df_h.empty and 'Nome do Corretor' in df_h.columns:
                # Filtra pelo corretor
                my_hist = df_h[df_h['Nome do Corretor'] == st.session_state.get('user_name')]
                
                # Filtra pela busca se houver
                if search_term:
                    my_hist = my_hist[my_hist['Nome'].astype(str).str.contains(search_term, case=False, na=False)]
                
                # Ordena e pega os últimos
                my_hist = my_hist.tail(15).iloc[::-1] # Inverte para mostrar mais recente primeiro
                
                if not my_hist.empty:
                    for idx, row in my_hist.iterrows():
                        label = f"{row.get('Nome', 'Cli')} | {row.get('Empreendimento Final', 'Emp')}"
                        # Botões diretos, um embaixo do outro
                        if st.button(label, key=f"hist_{idx}", use_container_width=True):
                            # Carrega dados
                            st.session_state.dados_cliente = {
                                'nome': row.get('Nome'), 'empreendimento_nome': row.get('Empreendimento Final'),
                                'unidade_id': row.get('Unidade Final'),
                                'imovel_valor': float(str(row.get('Preço Unidade Final', 0)).replace('R$','').replace('.','').replace(',','.')),
                                'finan_estimado': float(str(row.get('Financiamento Aprovado', 0)).replace('R$','').replace('.','').replace(',','.')),
                                'fgts_sub': float(str(row.get('Subsídio Máximo', 0)).replace('R$','').replace('.','').replace(',','.')),
                                'finan_usado': float(str(row.get('Financiamento Final', 0)).replace('R$','').replace('.','').replace(',','.')),
                                'fgts_sub_usado': float(str(row.get('FGTS + Subsídio Final', 0)).replace('R$','').replace('.','').replace(',','.')),
                                'ps_usado': float(str(row.get('Pro Soluto Final', 0)).replace('R$','').replace('.','').replace(',','.')),
                                'ps_parcelas': int(float(str(row.get('Número de Parcelas do Pro Soluto', 0)).replace(',','.'))),
                                'ps_mensal': float(str(row.get('Mensalidade PS', 0)).replace('R$','').replace('.','').replace(',','.')),
                                'ato_final': float(str(row.get('Ato', 0)).replace('R$','').replace('.','').replace(',','.')),
                                'ato_30': float(str(row.get('Ato 30', 0)).replace('R$','').replace('.','').replace(',','.')),
                                'ato_60': float(str(row.get('Ato 60', 0)).replace('R$','').replace('.','').replace(',','.')),
                                'ato_90': float(str(row.get('Ato 90', 0)).replace('R$','').replace('.','').replace(',','.')),
                            }
                            st.session_state.dados_cliente['entrada_total'] = st.session_state.dados_cliente['ato_final'] + st.session_state.dados_cliente['ato_30'] + st.session_state.dados_cliente['ato_60'] + st.session_state.dados_cliente['ato_90']
                            st.session_state.passo_simulacao = 'summary'
                            st.rerun()
                else:
                    st.caption("Nenhum histórico encontrado.")
            else:
                st.caption("Sem dados.")
        except:
            st.caption("Erro ao carregar histórico.")

    # --- ETAPA 1: INPUT ---
    if passo == 'input':
        st.markdown("### Dados do Cliente")
        nome = st.text_input("Nome Completo", value=st.session_state.dados_cliente.get('nome', ""), placeholder="Nome Completo", key="in_nome_v28")
        
        cpf_val = st.text_input("CPF", value=st.session_state.dados_cliente.get('cpf', ""), placeholder="000.000.000-00", key="in_cpf_v3", max_chars=14)
        if cpf_val and not validar_cpf(cpf_val):
            st.markdown(f"<small style='color: {COR_VERMELHO};'>CPF inválido</small>", unsafe_allow_html=True)
        
        d_nasc_default = st.session_state.dados_cliente.get('data_nascimento', date(1990, 1, 1))
        data_nasc = st.date_input("Data de Nascimento", value=d_nasc_default, min_value=date(1900, 1, 1), max_value=datetime.now().date(), format="DD/MM/YYYY", key="in_dt_nasc_v3")
        genero = st.selectbox("Gênero", ["Masculino", "Feminino", "Outro"], index=0, key="in_genero_v3")

        st.markdown("---")
        col_p1, col_p2 = st.columns(2)
        with col_p1: qtd_part = st.number_input("Participantes na Renda", min_value=1, max_value=4, value=st.session_state.dados_cliente.get('qtd_participantes', 1), step=1, key="qtd_part_v3")
        with col_p2:
            idx_prazo = 0 if st.session_state.dados_cliente.get('prazo_financiamento', 360) == 360 else 1
            prazo_finan = st.selectbox("Prazo Financiamento (Meses)", [360, 420], index=idx_prazo, key="prazo_v3")
        
        cols_renda = st.columns(qtd_part)
        renda_total_calc = 0.0
        lista_rendas_input = []
        rendas_anteriores = st.session_state.dados_cliente.get('rendas_lista', [])
        for i in range(qtd_part):
            with cols_renda[i]:
                def_val = float(rendas_anteriores[i]) if i < len(rendas_anteriores) else (3500.0 if i == 0 else 0.0)
                val_r = st.number_input(f"Renda Part. {i+1}", min_value=0.0, value=def_val, step=100.0, key=f"renda_part_{i}_v3")
                renda_total_calc += val_r; lista_rendas_input.append(val_r)
        
        rank_opts = ["DIAMANTE"]
        if not df_politicas.empty and 'CLASSIFICAÇÃO' in df_politicas.columns:
            rank_opts = [x for x in df_politicas['CLASSIFICAÇÃO'].dropna().unique().tolist() if x.upper() != "EMCASH"] or ["DIAMANTE"]
            
        ranking = st.selectbox("Ranking do Cliente", options=rank_opts, index=0, key="in_rank_v28")
        politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"], key="in_pol_v28")
        social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False), key="in_soc_v28")
        cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True), key="in_cot_v28")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        def processar_avanco(destino):
            if not nome.strip(): st.markdown(f'<div class="custom-alert">Por favor, informe o Nome do Cliente para continuar.</div>', unsafe_allow_html=True); return
            if cpf_val and not validar_cpf(cpf_val): st.markdown(f'<div class="custom-alert">CPF Inválido. Corrija para continuar.</div>', unsafe_allow_html=True); return
            if renda_total_calc <= 0: st.markdown(f'<div class="custom-alert">A renda total deve ser maior que zero.</div>', unsafe_allow_html=True); return

            class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
            politica_row = pd.Series({'FX_RENDA_1': 0.30, 'FAIXA_RENDA': 4400, 'FX_RENDA_2': 0.25, 'PROSOLUTO': 0.10, 'PARCELAS': 60})
            if 'CLASSIFICAÇÃO' in df_politicas.columns:
                filtro = df_politicas[df_politicas['CLASSIFICAÇÃO'] == class_b]
                if not filtro.empty: politica_row = filtro.iloc[0]

            limit_ps_r = politica_row['FX_RENDA_1'] if renda_total_calc < politica_row['FAIXA_RENDA'] else politica_row['FX_RENDA_2']
            f_faixa_ref, s_faixa_ref, fx_nome_ref = motor.obter_enquadramento(renda_total_calc, social, cotista, valor_avaliacao=240000)
            
            st.session_state.dados_cliente.update({
                'nome': nome, 'cpf': limpar_cpf_visual(cpf_val), 'data_nascimento': data_nasc, 'genero': genero,
                'renda': renda_total_calc, 'rendas_lista': lista_rendas_input,
                'social': social, 'cotista': cotista, 'ranking': ranking, 'politica': politica_ps,
                'perc_ps': politica_row['PROSOLUTO'], 'prazo_ps_max': int(politica_row['PARCELAS']),
                'limit_ps_renda': limit_ps_r, 'finan_f_ref': f_faixa_ref, 'sub_f_ref': s_faixa_ref,
                'qtd_participantes': qtd_part, 'prazo_financiamento': prazo_finan
            })
            st.session_state.passo_simulacao = destino
            st.rerun()

        # Botão único para avançar para a recomendação
        if st.button("AVANÇAR PARA RECOMENDAÇÃO", type="primary", use_container_width=True, key="btn_avancar_guide"):
            processar_avanco('guide')

    # --- ETAPA 2: RECOMENDAÇÃO (Direto do Input) ---
    elif passo == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### Recomendação de Imóveis")
        
        df_disp_total = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
        
        if df_disp_total.empty: st.markdown('<div class="custom-alert">Sem produtos viaveis no perfil selecionado.</div>', unsafe_allow_html=True); df_viaveis = pd.DataFrame()
        else:
            def calcular_viabilidade_unidade(row):
                v_venda = row['Valor de Venda']
                v_aval = row['Valor de Avaliação Bancária']
                fin, sub, fx_n = motor.obter_enquadramento(d.get('renda', 0), d.get('social', False), d.get('cotista', True), v_aval)
                poder, ps_u = motor.calcular_poder_compra(d.get('renda', 0), fin, sub, d.get('perc_ps', 0), v_venda)
                cobertura = (poder / v_venda) * 100 if v_venda > 0 else 0
                return pd.Series([poder, cobertura, cobertura >= 100, fin, sub])

            df_disp_total[['Poder_Compra', 'Cobertura', 'Viavel', 'Finan_Unid', 'Sub_Unid']] = df_disp_total.apply(calcular_viabilidade_unidade, axis=1)
            df_disp_total['Status Viabilidade'] = df_disp_total['Viavel'].apply(lambda x: "Viavel" if x else "Inviavel")
            df_viaveis = df_disp_total[df_disp_total['Viavel']].copy()
            df_panorama = df_viaveis[df_viaveis['Viavel']]
        
        # PANORAMA DE PRODUTOS
        st.markdown("#### Panorama de Produtos Viáveis")
        if df_panorama.empty:
            st.markdown('<div class="custom-alert">Nenhum empreendimento 100% viável encontrado. Veja abaixo opções que podem se encaixar.</div>', unsafe_allow_html=True)
        else:
            emp_counts = df_panorama.groupby('Empreendimento').size().to_dict()
            items = list(emp_counts.items())
            cols_per_row = 3
            for i in range(0, len(items), cols_per_row):
                row_items = items[i:i+cols_per_row]
                row_cols = st.columns(len(row_items))
                for idx, (emp, qtd) in enumerate(row_items):
                    with row_cols[idx]:
                        st.markdown(f"""
                            <div class="card" style="min-height: 80px; padding: 15px; border-top: 3px solid {COR_VERMELHO};">
                                <p style="margin:0; font-weight:700; color:{COR_AZUL_ESC};">{emp}</p>
                                <p style="margin:5px 0 0 0; font-size:0.85rem; color:{COR_TEXTO_MUTED};">{qtd} unidades viaveis</p>
                            </div>
                        """, unsafe_allow_html=True)

        st.write("")
        # ABAS DE SELEÇÃO CENTRALIZADAS
        tab_sugestoes, tab_estoque = st.tabs(["SUGESTÕES DE UNIDADES", "ESTOQUE GERAL"])

        with tab_sugestoes:
            st.markdown("<br>", unsafe_allow_html=True)
            emp_names_rec = sorted(df_disp_total['Empreendimento'].unique().tolist())
            emp_rec = st.selectbox("Escolha um empreendimento para obter recomendações:", options=["Todos"] + emp_names_rec, key="sel_emp_rec_v28")
            df_pool = df_disp_total if emp_rec == "Todos" else df_disp_total[df_disp_total['Empreendimento'] == emp_rec]
            
            if df_pool.empty: st.markdown('<div class="custom-alert">Nenhuma unidade encontrada.</div>', unsafe_allow_html=True)
            else:
                pool_sorted = df_pool.sort_values('Valor de Venda', ascending=False)
                cand_ideal = pool_sorted[pool_sorted['Cobertura'] >= 100].head(1)
                cand_seguro = pool_sorted[pool_sorted['Cobertura'] >= 90].head(1)
                cand_facil = pool_sorted[pool_sorted['Cobertura'] >= 75].head(1)
                
                def extract_info(df_cand, label, css_class):
                    if df_cand.empty: return None
                    row = df_cand.iloc[0]
                    unidades_irmas = df_pool[df_pool['Valor de Venda'] == row['Valor de Venda']]['Identificador'].tolist()
                    unidades_str = ", ".join(unidades_irmas[:5]) + ("..." if len(unidades_irmas)>5 else "")
                    return {'preco': row['Valor de Venda'], 'emp': row['Empreendimento'], 'unidades': unidades_str, 'labels': [label], 'css': css_class}

                info_ideal = extract_info(cand_ideal, "IDEAL", "badge-ideal")
                info_seguro = extract_info(cand_seguro, "SEGURO", "badge-seguro")
                info_facil = extract_info(cand_facil, "FACILITADO", "badge-facilitado")
                
                cards_finais = []
                if info_ideal: cards_finais.append(info_ideal)
                if info_seguro:
                    if info_ideal and info_seguro['preco'] == info_ideal['preco']: pass 
                    else: cards_finais.append(info_seguro)
                if info_facil:
                    last_card = cards_finais[-1] if cards_finais else None
                    if last_card and info_facil['preco'] == last_card['preco']:
                        if "FACILITADO" not in last_card['labels']:
                            last_card['labels'].append("FACILITADO")
                            if "SEGURO" in last_card['labels']: last_card['css'] = "badge-multi"
                    else: cards_finais.append(info_facil)
                
                if not cards_finais: st.warning("Nenhuma unidade atende aos critérios mínimos (75% cobertura).")
                else:
                    cols = st.columns(len(cards_finais))
                    for idx, card in enumerate(cards_finais):
                        with cols[idx]:
                            labels_html = "".join([f'<span class="{("badge-ideal" if l=="IDEAL" else ("badge-seguro" if l=="SEGURO" else "badge-facilitado"))}" style="margin-right:5px;">{l}</span>' for l in card['labels']])
                            if len(card['labels']) > 1 and "SEGURO" in card['labels'] and "FACILITADO" in card['labels']: labels_html = f'<span class="badge-multi">SEGURO & FACILITADO</span>'
                            st.markdown(f'''
                            <div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC}; height: 100%; justify-content: flex-start;">
                                <span style="font-size:0.65rem; color:{COR_AZUL_ESC}; opacity:0.8;">PERFIL</span><br>
                                <div style="margin-top:5px; margin-bottom:15px;">{labels_html}</div>
                                <b style="color:{COR_AZUL_ESC}; font-size:1.1rem;">{card['emp']}</b><br>
                                <div style="font-size:0.85rem; color:{COR_TEXTO_MUTED}; text-align:center; border-top:1px solid #eee; padding-top:10px; width:100%;">
                                    <b>Unidade(s):</b><br>{card['unidades']}
                                </div>
                                <div class="price-tag" style="font-size:1.4rem; margin:10px 0;">R$ {fmt_br(card['preco'])}</div>
                            </div>''', unsafe_allow_html=True)

        with tab_estoque:
            if df_disp_total.empty:
                st.markdown('<div class="custom-alert">Sem dados para exibir.</div>', unsafe_allow_html=True)
            else:
                f_cols = st.columns([1.2, 1.5, 1, 1, 1])
                with f_cols[0]: f_bairro = st.multiselect("Bairro:", options=sorted(df_disp_total['Bairro'].unique()), key="f_bairro_tab_v28")
                with f_cols[1]: f_emp = st.multiselect("Empreendimento:", options=sorted(df_disp_total['Empreendimento'].unique()), key="f_emp_tab_v28")
                with f_cols[2]: f_status_v = st.multiselect("Viabilidade:", options=["Viavel", "Inviavel"], key="f_status_tab_v28")
                with f_cols[3]: f_ordem = st.selectbox("Ordem:", ["Menor Preço", "Maior Preço"], key="f_ordem_tab_v28")
                with f_cols[4]: f_pmax = st.number_input("Preço Máx:", value=float(df_disp_total['Valor de Venda'].max()), key="f_pmax_tab_v28")
                
                df_tab = df_disp_total.copy()
                if f_bairro: df_tab = df_tab[df_tab['Bairro'].isin(f_bairro)]
                if f_emp: df_tab = df_tab[df_tab['Empreendimento'].isin(f_emp)]
                if f_status_v: df_tab = df_tab[df_tab['Status Viabilidade'].isin(f_status_v)]
                df_tab = df_tab[df_tab['Valor de Venda'] <= f_pmax]
                
                if f_ordem == "Menor Preço": 
                    df_tab = df_tab.sort_values('Valor de Venda', ascending=True)
                else: 
                    df_tab = df_tab.sort_values('Valor de Venda', ascending=False)
                
                df_tab_view = df_tab.copy()
                df_tab_view['Valor de Venda'] = df_tab_view['Valor de Venda'].apply(fmt_br)
                df_tab_view['Poder_Compra'] = df_tab_view['Poder_Compra'].apply(fmt_br)
                df_tab_view['Cobertura'] = df_tab_view['Cobertura'].apply(lambda x: f"{x:.1f}%")

                st.dataframe(
                    df_tab_view[['Identificador', 'Bairro', 'Empreendimento', 'Valor de Venda', 'Poder_Compra', 'Cobertura', 'Status Viabilidade']], 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Identificador": st.column_config.TextColumn("Unidade"),
                        "Valor de Venda": st.column_config.TextColumn("Preço (R$)"),
                        "Poder_Compra": st.column_config.TextColumn("Poder Real (R$)"),
                        "Cobertura": st.column_config.TextColumn("Cob. (%)"),
                    }
                )

        st.markdown("---")
        if st.button("AVANÇAR PARA SELEÇÃO DE UNIDADE", type="primary", use_container_width=True, key="btn_goto_selection"): st.session_state.passo_simulacao = 'selection'; st.rerun()
        st.write(""); 
        if st.button("VOLTAR PARA DADOS DO CLIENTE", use_container_width=True, key="btn_pot_v28"): st.session_state.passo_simulacao = 'input'; st.rerun()

    # --- ETAPA 3: SELEÇÃO + TERMOMETRO ---
    elif passo == 'selection':
        d = st.session_state.dados_cliente
        st.markdown(f"### Seleção de Unidade")
        
        df_disponiveis = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
        
        if df_disponiveis.empty: st.warning("Sem estoque disponível.")
        else:
            emp_names = sorted(df_disponiveis['Empreendimento'].unique())
            idx_emp = 0
            if 'empreendimento_nome' in st.session_state.dados_cliente:
                try: idx_emp = emp_names.index(st.session_state.dados_cliente['empreendimento_nome'])
                except: idx_emp = 0
            emp_escolhido = st.selectbox("Escolha o Empreendimento:", options=emp_names, index=idx_emp, key="sel_emp_new_v3")
            unidades_disp = df_disponiveis[(df_disponiveis['Empreendimento'] == emp_escolhido)].copy()
            unidades_disp = unidades_disp.sort_values(['Bloco_Sort', 'Andar', 'Apto_Sort'])
            
            if unidades_disp.empty: st.warning("Sem unidades disponíveis.")
            else:
                current_uni_ids = unidades_disp['Identificador'].unique(); idx_uni = 0
                if 'unidade_id' in st.session_state.dados_cliente:
                    try: 
                        idx_list = list(current_uni_ids)
                        if st.session_state.dados_cliente['unidade_id'] in idx_list: idx_uni = idx_list.index(st.session_state.dados_cliente['unidade_id'])
                    except: pass
                
                def label_uni(uid):
                    u = unidades_disp[unidades_disp['Identificador'] == uid].iloc[0]
                    return f"{uid} - R$ {fmt_br(u['Valor de Venda'])}"
                
                uni_escolhida_id = st.selectbox("Escolha a Unidade:", options=current_uni_ids, index=idx_uni, format_func=label_uni, key="sel_uni_new_v3")

                if uni_escolhida_id:
                    u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                    v_aval = u_row['Valor de Avaliação Bancária']
                    v_venda = u_row['Valor de Venda']
                    fin_t, sub_t, _ = motor.obter_enquadramento(d.get('renda', 0), d.get('social', False), d.get('cotista', True), v_aval)
                    poder_t, _ = motor.calcular_poder_compra(d.get('renda', 0), fin_t, sub_t, d.get('perc_ps', 0), v_venda)
                    
                    percentual_cobertura = min(100, max(0, (poder_t / v_venda) * 100))
                    cor_term = calcular_cor_gradiente(percentual_cobertura)
                    
                    st.markdown(f"""
                    <div style="margin-top: 20px; padding: 15px; border: 1px solid #e2e8f0; border-radius: 10px; background-color: #f8fafc; text-align: center;">
                        <p style="margin: 0; font-weight: 700; font-size: 0.9rem; color: #002c5d;">TERMÔMETRO DE VIABILIDADE</p>
                        <div style="width: 100%; background-color: #e2e8f0; border-radius: 5px; height: 10px; margin: 10px 0;">
                            <div style="width: {percentual_cobertura}%; background-color: {cor_term}; height: 100%; border-radius: 5px; transition: width 0.5s;"></div>
                        </div>
                        <small>{percentual_cobertura:.1f}% Coberto</small>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Avançar para Fechamento", type="primary", use_container_width=True):
                if uni_escolhida_id:
                    u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                    fin, sub, _ = motor.obter_enquadramento(d.get('renda', 0), d.get('social', False), d.get('cotista', True), u_row['Valor de Avaliação Bancária'])
                    st.session_state.dados_cliente.update({
                        'unidade_id': uni_escolhida_id, 'empreendimento_nome': emp_escolhido, 
                        'imovel_valor': u_row['Valor de Venda'], 'imovel_avaliacao': u_row['Valor de Avaliação Bancária'], 
                        'finan_estimado': fin, 'fgts_sub': sub
                    })
                    st.session_state.passo_simulacao = 'payment_flow'; st.rerun()
            if st.button("Voltar", use_container_width=True): st.session_state.passo_simulacao = 'guide'; st.rerun()

    # --- ETAPA 4: FECHAMENTO FINANCEIRO ---
    elif passo == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### Fechamento Financeiro")
        u_valor = d.get('imovel_valor', 0)
        st.markdown(f'<div class="custom-alert">Unidade: {d.get("unidade_id", "N/A")} (R$ {fmt_br(u_valor)})</div>', unsafe_allow_html=True)
        
        col_fin, col_fgts = st.columns(2)
        with col_fin: 
            f_u = st.number_input("Financiamento", value=float(d.get('finan_estimado', 0)), step=1000.0, key="fin_u_v28")
            st.markdown(f'<span class="inline-ref">Financiamento Máximo: R$ {fmt_br(d.get("finan_estimado", 0))}</span>', unsafe_allow_html=True)
        
        with col_fgts: 
            fgts_u = st.number_input("FGTS + Subsídio", value=float(d.get('fgts_sub', 0)), step=1000.0, key="fgt_u_v28")
            st.markdown(f'<span class="inline-ref">Subsídio Máximo: R$ {fmt_br(d.get("fgts_sub", 0))}</span>', unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        # Inicialização do saldo restante para a primeira vez
        saldo_restante_inicial = max(0.0, u_valor - f_u - fgts_u)
        calc_hash = f"{f_u}-{fgts_u}-{u_valor}-{d.get('unidade_id', 'none')}"
        if 'last_calc_hash' not in st.session_state or st.session_state.last_calc_hash != calc_hash:
            dist_val = saldo_restante_inicial / 4
            st.session_state.ato_1 = dist_val; st.session_state.ato_2 = dist_val; st.session_state.ato_3 = dist_val; st.session_state.ato_4 = dist_val
            st.session_state.last_calc_hash = calc_hash

        # Verifica se é EMCASH
        is_emcash = (d.get('politica') == 'Emcash')
        if is_emcash: st.session_state.ato_4 = 0.0 

        st.markdown("#### Distribuição da Entrada (Saldo a Pagar)")
        
        # Botões de Distribuição Automática
        col_dist1, col_dist2, col_dist3, col_dist4 = st.columns(4)
        ps_atual = st.session_state.get('ps_u_view', 0)
        saldo_para_atos = max(0.0, u_valor - f_u - fgts_u - ps_atual)
        
        def distribuir(n_parcelas):
            val = saldo_para_atos / n_parcelas
            st.session_state['ato_1_v28'] = val
            st.session_state['ato_2_v28'] = val if n_parcelas >= 2 else 0.0
            st.session_state['ato_3_v28'] = val if n_parcelas >= 3 else 0.0
            st.session_state['ato_4_v28'] = val if n_parcelas >= 4 and not is_emcash else 0.0
            st.session_state.ato_1 = st.session_state['ato_1_v28']
            st.session_state.ato_2 = st.session_state['ato_2_v28']
            st.session_state.ato_3 = st.session_state['ato_3_v28']
            st.session_state.ato_4 = st.session_state['ato_4_v28']
            st.rerun()

        if col_dist1.button("1x", use_container_width=True): distribuir(1)
        if col_dist2.button("2x", use_container_width=True): distribuir(2)
        if col_dist3.button("3x", use_container_width=True): distribuir(3)
        if col_dist4.button("4x", use_container_width=True, disabled=is_emcash): distribuir(4)

        if 'ato_1_v28' not in st.session_state: st.session_state['ato_1_v28'] = st.session_state.ato_1
        if 'ato_2_v28' not in st.session_state: st.session_state['ato_2_v28'] = st.session_state.ato_2
        if 'ato_3_v28' not in st.session_state: st.session_state['ato_3_v28'] = st.session_state.ato_3
        if 'ato_4_v28' not in st.session_state: st.session_state['ato_4_v28'] = st.session_state.ato_4

        col_a, col_b = st.columns(2)
        with col_a:
            st.number_input("Ato (Imediato)", key="ato_1_v28", step=100.0)
            st.number_input("Ato 60 Dias", key="ato_3_v28", step=100.0)
        with col_b:
            st.number_input("Ato 30 Dias", key="ato_2_v28", step=100.0)
            st.number_input("Ato 90 Dias", key="ato_4_v28", step=100.0, disabled=is_emcash)

        st.session_state.ato_1 = st.session_state['ato_1_v28']
        st.session_state.ato_2 = st.session_state['ato_2_v28']
        st.session_state.ato_3 = st.session_state['ato_3_v28']
        st.session_state.ato_4 = st.session_state['ato_4_v28']

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_ps_val, col_ps_parc = st.columns(2)
        
        ps_max_real = u_valor * d.get('perc_ps', 0)
        with col_ps_val:
            ps_u = st.number_input("Pro Soluto Direcional", value=0.0, step=1000.0, key="ps_u_view") 
            st.markdown(f'<span class="inline-ref">Limite Permitido ({d.get("perc_ps", 0)*100:.0f}%): R$ {fmt_br(ps_max_real)}</span>', unsafe_allow_html=True)
            
        with col_ps_parc:
            parc = st.number_input("Parcelas Pro Soluto", min_value=1, max_value=144, value=60, key="parc_u_v28")
            st.markdown(f'<span class="inline-ref">Prazo Máximo: {d.get("prazo_ps_max", 0)} meses</span>', unsafe_allow_html=True)

        v_parc = ps_u / parc if parc > 0 else 0
        total_pago = f_u + fgts_u + ps_u + st.session_state.ato_1 + st.session_state.ato_2 + st.session_state.ato_3 + st.session_state.ato_4
        gap_final = u_valor - total_pago

        fin1, fin2, fin3 = st.columns(3)
        with fin1: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b>VALOR DO IMÓVEL</b><br>R$ {fmt_br(u_valor)}</div>""", unsafe_allow_html=True)
        with fin2: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_VERMELHO};"><b>MENSALIDADE PS</b><br>R$ {fmt_br(v_parc)} ({parc}x)</div>""", unsafe_allow_html=True)
        cor_saldo = COR_VERMELHO if abs(gap_final) > 1 else "#22c55e"
        with fin3: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {cor_saldo};"><b>SALDO A COBRIR</b><br>R$ {fmt_br(gap_final)}</div>""", unsafe_allow_html=True)

        if abs(gap_final) > 1: st.error(f"Atenção: Falta cobrir R$ {fmt_br(gap_final)}.")

        total_entrada_cash = st.session_state.ato_1 + st.session_state.ato_2 + st.session_state.ato_3 + st.session_state.ato_4
        st.session_state.dados_cliente.update({'finan_usado': f_u, 'fgts_sub_usado': fgts_u, 'ps_usado': ps_u, 'ps_parcelas': parc, 'ps_mensal': v_parc, 'entrada_total': total_entrada_cash, 'ato_final': st.session_state.ato_1, 'ato_30': st.session_state.ato_2, 'ato_60': st.session_state.ato_3, 'ato_90': st.session_state.ato_4})
        
        st.markdown("---")
        if st.button("Avançar para Resumo", type="primary", use_container_width=True):
            if abs(gap_final) <= 1: st.session_state.passo_simulacao = 'summary'; st.rerun()
            else: st.error(f"O saldo a cobrir deve ser zerado.")
        if st.button("Voltar", use_container_width=True): st.session_state.passo_simulacao = 'selection'; st.rerun()

    # --- ETAPA 5: RESUMO ---
    elif passo == 'summary':
        d = st.session_state.dados_cliente
        st.markdown(f"### Resumo da Simulação - {d.get('nome', 'Cliente')}")
        st.markdown(f'<div class="summary-header">DADOS DO IMÓVEL</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Empreendimento:</b> {d.get('empreendimento_nome')}<br><b>Unidade:</b> {d.get('unidade_id')}<br><b>Valor de Venda:</b> <span style="color: {COR_VERMELHO}; font-weight: 800;">R$ {fmt_br(d.get('imovel_valor', 0))}</span></div>""", unsafe_allow_html=True)
        st.markdown(f'<div class="summary-header">PLANO DE FINANCIAMENTO</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Financiamento Bancário:</b> R$ {fmt_br(d.get('finan_usado', 0))}<br><b>FGTS + Subsídio:</b> R$ {fmt_br(d.get('fgts_sub_usado', 0))}<br><b>Pro Soluto Total:</b> R$ {fmt_br(d.get('ps_usado', 0))} ({d.get('ps_parcelas')}x de R$ {fmt_br(d.get('ps_mensal', 0))})</div>""", unsafe_allow_html=True)
        st.markdown(f'<div class="summary-header">FLUXO DE ENTRADA (ATO)</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Total de Entrada:</b> R$ {fmt_br(d.get('entrada_total', 0))}<br><hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 10px 0;"><b>Ato:</b> R$ {fmt_br(d.get('ato_final', 0))}<br><b>Ato 30 Dias:</b> R$ {fmt_br(d.get('ato_30', 0))}<br><b>Ato 60 Dias:</b> R$ {fmt_br(d.get('ato_60', 0))}<br><b>Ato 90 Dias:</b> R$ {fmt_br(d.get('ato_90', 0))}</div>""", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("Opções de Resumo (PDF / E-mail)", use_container_width=True):
            show_export_dialog(d)

        st.markdown("---")
        if st.button("CONCLUIR E SALVAR SIMULAÇÃO", type="primary", use_container_width=True):
            try:
                conn_save = st.connection("gsheets", type=GSheetsConnection)
                aba_destino = 'Cadastros'
                rendas_ind = d.get('rendas_lista', [])
                while len(rendas_ind) < 4: rendas_ind.append(0.0)
                nova_linha = {
                    "Nome": d.get('nome'), "CPF": d.get('cpf'), "Data de Nascimento": str(d.get('data_nascimento')),
                    "Prazo Financiamento": d.get('prazo_financiamento'), "Renda Part. 1": rendas_ind[0], "Renda Part. 2": rendas_ind[1],
                    "Renda Part. 3": rendas_ind[2], "Renda Part. 4": rendas_ind[3], "Ranking": d.get('ranking'), "Política de Pro Soluto": d.get('politica'),
                    "Fator Social": "Sim" if d.get('social') else "Não", "Cotista FGTS": "Sim" if d.get('cotista') else "Não",
                    "Financiamento Aprovado": d.get('finan_f_ref', 0), "Subsídio Máximo": d.get('sub_f_ref', 0), "Pro Soluto Médio": d.get('ps_medio_ref', 0),
                    "Capacidade de Entrada": d.get('cap_entrada_ref', 0), "Poder de Aquisição Médio": d.get('poder_aquisicao_ref', 0),
                    "Empreendimento Final": d.get('empreendimento_nome'), "Unidade Final": d.get('unidade_id'), "Preço Unidade Final": d.get('imovel_valor', 0),
                    "Financiamento Final": d.get('finan_usado', 0), "FGTS + Subsídio Final": d.get('fgts_sub_usado', 0),
                    "Pro Soluto Final": d.get('ps_usado', 0), "Número de Parcelas do Pro Soluto": d.get('ps_parcelas', 0), "Mensalidade PS": d.get('ps_mensal', 0),
                    "Ato": d.get('ato_final', 0), "Ato 30": d.get('ato_30', 0), "Ato 60": d.get('ato_60', 0), "Ato 90": d.get('ato_90', 0),
                    "Nome do Corretor": st.session_state.get('user_name', ''), "Canal/Imobiliária": st.session_state.get('user_imobiliaria', '')
                }
                df_novo = pd.DataFrame([nova_linha])
                try:
                    df_existente = conn_save.read(spreadsheet=URL_RANKING, worksheet=aba_destino)
                    df_final_save = pd.concat([df_existente, df_novo], ignore_index=True)
                except: df_final_save = df_novo
                conn_save.update(spreadsheet=URL_RANKING, worksheet=aba_destino, data=df_final_save)
                st.success(f"Salvo em '{aba_destino}'!"); time.sleep(2); st.session_state.dados_cliente = {}; st.session_state.passo_simulacao = 'input'; st.rerun()
            except Exception as e: st.error(f"Erro ao salvar: {e}")

        if st.button("Voltar", use_container_width=True): st.session_state.passo_simulacao = 'payment_flow'; st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    c_out_1, c_out_2, c_out_3 = st.columns([1, 1, 1])
    with c_out_2:
        if st.button("Sair do Sistema", key="btn_logout_bottom", use_container_width=True): st.session_state['logged_in'] = False; st.rerun()

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas, df_logins, df_cadastros = carregar_dados_sistema()
    logo_src = URL_FAVICON_RESERVA
    if os.path.exists("favicon.png"):
        try:
            with open("favicon.png", "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                logo_src = f"data:image/png;base64,{encoded}"
        except: pass
    st.markdown(f'''<div class="header-container"><img src="{logo_src}" style="position: absolute; top: 30px; left: 40px; height: 50px;"><div class="header-title">SIMULADOR IMOBILIÁRIO DV</div><div class="header-subtitle">Sistema de Gestão de Vendas e Viabilidade Imobiliária</div></div>''', unsafe_allow_html=True)
    
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']: tela_login(df_logins)
    else: aba_simulador_automacao(df_finan, df_estoque, df_politicas, df_cadastros)
    
    st.markdown(f'<div class="footer">Direcional Engenharia - Rio de Janeiro | Developed by Lucas Maia</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
