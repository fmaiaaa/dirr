# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V30 (UPDATED LAYOUT & AUTO EMAIL)
=============================================================================
Instruções para Google Colab:
1. Crie um arquivo chamado 'app.py' com este conteúdo.
2. Instale as dependências:
   !pip install streamlit pandas numpy fpdf streamlit-gsheets pytz
3. Configure os segredos (.streamlit/secrets.toml) para o envio de email.
4. Rode o app:
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
import os
import pytz

# Tenta importar fpdf e PIL
try:
    from fpdf import FPDF
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

try:
    from PIL import Image
except ImportError:
    Image = None

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
COR_INPUT_BG = "#f0f2f6"

def fmt_br(valor):
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
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

def safe_float_convert(val):
    if pd.isnull(val) or val == "": return 0.0
    if isinstance(val, (int, float, np.number)): return float(val)
    s = str(val).replace('R$', '').strip()
    try: return float(s)
    except:
        if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
        elif ',' in s: s = s.replace(',', '.')
        try: return float(s)
        except: return 0.0

def calcular_cor_gradiente(valor):
    """
    Interpola linearmente entre Vermelho (#e30613) e Azul (#002c5d)
    0% -> Vermelho
    100% -> Azul
    """
    valor = max(0, min(100, valor))
    f = valor / 100.0
    
    # Vermelho: 227, 6, 19
    # Azul: 0, 44, 93
    r = int(227 + (0 - 227) * f)
    g = int(6 + (44 - 6) * f)
    b = int(19 + (93 - 19) * f)
    
    return f"rgb({r},{g},{b})"

def calcular_comparativo_sac_price(valor, meses, taxa_anual):
    if valor <= 0 or meses <= 0:
        return {"SAC": {"primeira": 0, "ultima": 0, "juros": 0}, "PRICE": {"parcela": 0, "juros": 0}}
    i = (1 + taxa_anual/100)**(1/12) - 1
    
    # PRICE
    try:
        pmt_price = valor * (i * (1 + i)**meses) / ((1 + i)**meses - 1)
        total_pago_price = pmt_price * meses
        juros_price = total_pago_price - valor
    except: pmt_price = 0; juros_price = 0

    # SAC
    try:
        amort = valor / meses
        pmt_sac_ini = amort + (valor * i)
        pmt_sac_fim = amort + (amort * i)
        total_pago_sac = (pmt_sac_ini + pmt_sac_fim) * meses / 2
        juros_sac = total_pago_sac - valor
    except: pmt_sac_ini = 0; pmt_sac_fim = 0; juros_sac = 0
    
    return {
        "SAC": {"primeira": pmt_sac_ini, "ultima": pmt_sac_fim, "juros": juros_sac},
        "PRICE": {"parcela": pmt_price, "juros": juros_price}
    }

def calcular_parcela_financiamento(valor_financiado, meses, taxa_anual_pct, sistema):
    if valor_financiado <= 0 or meses <= 0: return 0.0
    i_mensal = (1 + taxa_anual_pct/100)**(1/12) - 1
    if sistema == "PRICE":
        try: return valor_financiado * (i_mensal * (1 + i_mensal)**meses) / ((1 + i_mensal)**meses - 1)
        except: return 0.0
    else:
        amortizacao = valor_financiado / meses
        juros = valor_financiado * i_mensal
        return amortizacao + juros

def scroll_to_top():
    js = """<script>var body = window.parent.document.querySelector(".main"); if (body) { body.scrollTop = 0; } window.scrollTo(0, 0);</script>"""
    st.components.v1.html(js, height=0)

# =============================================================================
# 1. CARREGAMENTO DE DADOS
# =============================================================================

@st.cache_data(ttl=300)
def carregar_dados_sistema():
    try:
        if "connections" not in st.secrets:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        conn = st.connection("gsheets", type=GSheetsConnection)
        def limpar_moeda(val): return safe_float_convert(val)

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
            df_logins['Email'] = df_logins['Email'].astype(str).str.strip().str.lower()
            df_logins['Senha'] = df_logins['Senha'].astype(str).str.strip()
        except: df_logins = pd.DataFrame(columns=['Email', 'Senha'])

        # Cadastros
        try: df_cadastros = conn.read(spreadsheet=URL_RANKING, worksheet="Simulações")
        except:
            try: df_cadastros = conn.read(spreadsheet=URL_RANKING, worksheet="Cadastros")
            except: df_cadastros = pd.DataFrame()
        
        # Politicas
        try:
            df_politicas = conn.read(spreadsheet=URL_RANKING)
            df_politicas.columns = [str(c).strip() for c in df_politicas.columns]
            col_class = next((c for c in df_politicas.columns if 'CLASSIFICA' in c.upper() or 'RANKING' in c.upper()), 'CLASSIFICAÇÃO')
            df_politicas = df_politicas.rename(columns={col_class: 'CLASSIFICAÇÃO', 'FAIXA RENDA': 'FAIXA_RENDA', 'FX RENDA 1': 'FX_RENDA_1', 'FX RENDA 2': 'FX_RENDA_2'})
        except: df_politicas = pd.DataFrame()

        # Finan
        try:
            df_finan = conn.read(spreadsheet=URL_FINAN)
            df_finan.columns = [str(c).strip() for c in df_finan.columns]
            for col in df_finan.columns: df_finan[col] = df_finan[col].apply(limpar_moeda)
        except: df_finan = pd.DataFrame()

        # Estoque
        try:
            df_raw = conn.read(spreadsheet=URL_ESTOQUE)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            mapa_estoque = {'Nome do Empreendimento': 'Empreendimento', 'VALOR DE VENDA': 'Valor de Venda', 'Status da unidade': 'Status', 'Identificador': 'Identificador', 'Bairro': 'Bairro'}
            col_aval = 'VALOR DE AVALIACAO BANCARIA' if 'VALOR DE AVALIACAO BANCARIA' in df_raw.columns else 'Valor de Avaliação Bancária'
            if col_aval in df_raw.columns: mapa_estoque[col_aval] = 'Valor de Avaliação Bancária'
            df_estoque = df_raw.rename(columns=mapa_estoque)
            df_estoque['Valor de Venda'] = df_estoque['Valor de Venda'].apply(limpar_moeda) if 'Valor de Venda' in df_estoque.columns else 0.0
            df_estoque['Valor de Avaliação Bancária'] = df_estoque['Valor de Avaliação Bancária'].apply(limpar_moeda) if 'Valor de Avaliação Bancária' in df_estoque.columns else df_estoque['Valor de Venda']
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
        if valor_avaliacao <= 275000: faixa = "F2"
        elif valor_avaliacao <= 350000: faixa = "F3"
        else: faixa = "F4"
        renda_col = pd.to_numeric(self.df_finan['Renda'], errors='coerce').fillna(0)
        idx = (renda_col - float(renda)).abs().idxmin()
        row = self.df_finan.iloc[idx]
        s, c = ('Sim' if social else 'Nao'), ('Sim' if cotista else 'Nao')
        col_fin = f"Finan_Social_{s}_Cotista_{c}_{faixa}"
        col_sub = f"Subsidio_Social_{s}_Cotista_{c}_{faixa}"
        vf = row.get(col_fin, 0.0)
        vs = row.get(col_sub, 0.0)
        return float(vf), float(vs), faixa

    def calcular_poder_compra(self, renda, finan, fgts_sub, perc_ps, valor_unidade):
        ps = valor_unidade * perc_ps
        return (2 * renda) + finan + fgts_sub + ps, ps

def configurar_layout():
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
            background-color: {COR_INPUT_BG} !important;
            transition: all 0.2s ease-in-out !important;
        }}

        div[data-baseweb="input"]:focus-within {{
            border-color: {COR_VERMELHO} !important;
            box-shadow: 0 0 0 1px {COR_VERMELHO} !important;
            background-color: #ffffff !important;
        }}

        /* --- ALTURA E ALINHAMENTO UNIFICADOS PARA INPUTS --- */
        .stTextInput input, .stNumberInput input, .stDateInput input, div[data-baseweb="select"] > div {{
            height: 48px !important;
            min-height: 48px !important;
            padding: 0 15px !important;
            color: {COR_AZUL_ESC} !important;
            font-size: 1rem !important;
            line-height: 48px !important;
            text-align: left !important;
            display: flex !important;
            align-items: center !important;
        }}
        
        /* CORREÇÃO PARA ALINHAMENTO DE ALTURA NO ESTOQUE GERAL */
        div[data-testid="stNumberInput"] div[data-baseweb="input"] {{
            height: 48px !important;
            min-height: 48px !important;
            display: flex;
            align-items: center;
        }}

        div[data-baseweb="select"] span {{
            text-align: left !important;
            display: flex !important;
            align-items: center !important;
            height: 100% !important;
        }}

        div[data-testid="stDateInput"] > div, div[data-baseweb="select"] > div {{
            background-color: {COR_INPUT_BG} !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            display: flex;
            align-items: center;
        }}

        div[data-testid="stDateInput"] div[data-baseweb="input"] {{
            border: none !important;
            background-color: transparent !important;
        }}

        div[data-testid="stNumberInput"] button {{
             height: 48px !important;
             border-color: #e2e8f0 !important;
             background-color: {COR_INPUT_BG} !important;
             color: {COR_AZUL_ESC} !important;
        }}

        div[data-testid="stNumberInput"] button:hover {{ background-color: #e2e8f0 !important; }}

        .stButton button {{
            font-family: 'Inter', sans-serif;
            border-radius: 8px !important;
            padding: 0 20px !important;
            width: 100% !important;
            height: 60px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 1rem !important;
            transition: all 0.2s ease !important;
        }}

        div[data-testid="column"] .stButton button, [data-testid="stSidebar"] .stButton button {{
             min-height: 48px !important;
             height: 48px !important;
             font-size: 0.9rem !important;
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
            background: {COR_INPUT_BG} !important;
            color: {COR_AZUL_ESC} !important;
            border: 1px solid #e2e8f0 !important;
        }}
        .stButton button:not([kind="primary"]:hover) {{
            border-color: #e2e8f0 !important;
        }}
        .stButton button:not([kind="primary"]):hover {{
            border-color: {COR_VERMELHO} !important;
            color: {COR_VERMELHO} !important;
            background: #ffffff !important;
        }}
        
        .stDownloadButton button {{
            background: {COR_INPUT_BG} !important;
            color: {COR_AZUL_ESC} !important;
            border: 1px solid #e2e8f0 !important;
            height: 48px !important;
        }}
        .stDownloadButton button:hover {{
            border-color: {COR_VERMELHO} !important;
            color: {COR_VERMELHO} !important;
            background: #ffffff !important;
        }}

        [data-testid="stSidebar"] .stButton button {{
            padding: 8px 12px !important;
            font-size: 0.75rem !important;
            margin-bottom: 2px !important;
            height: auto !important;
            min-height: 30px !important;
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
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
            font-weight: 600;
            color: #ffffff !important;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 60px; 
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

        .badge-ideal, .badge-seguro, .badge-facilitado, .badge-multi {{
            background-color: {COR_VERMELHO} !important;
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85rem;
            margin-top: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        [data-testid="stSidebar"] {{ background-color: #fff; border-right: 1px solid {COR_BORDA}; }}
        
        .sidebar-profile {{
            background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
            border: 1px solid {COR_BORDA};
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);
        }}
        .profile-avatar {{
            width: 56px;
            height: 56px;
            background: {COR_AZUL_ESC};
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.5rem;
            margin: 0 auto 1rem auto;
            box-shadow: 0 4px 10px rgba(0, 44, 93, 0.3);
        }}

        .hist-item {{ display: block; width: 100%; text-align: left; padding: 8px; margin-bottom: 4px; border-radius: 8px; background: #fff; border: 1px solid {COR_BORDA}; color: {COR_AZUL_ESC}; font-size: 0.75rem; transition: all 0.2s; }}
        .hist-item:hover {{ border-color: {COR_VERMELHO}; background: #fff5f5; }}

        div[data-baseweb="tab-list"] {{ justify-content: center !important; gap: 40px; margin-bottom: 40px; }}
        button[data-baseweb="tab"] p {{ color: {COR_AZUL_ESC} !important; opacity: 0.6; font-weight: 700 !important; font-family: 'Montserrat', sans-serif !important; font-size: 0.9rem !important; text-transform: uppercase; letter-spacing: 0.1em; }}
        button[data-baseweb="tab"][aria-selected="true"] p {{ color: {COR_AZUL_ESC} !important; opacity: 1; }}
        div[data-baseweb="tab-highlight"] {{ background-color: {COR_VERMELHO} !important; height: 3px !important; }}

        /* --- STEPPER (Visual CSS - Non-interactive) --- */
        .stepper-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3.5rem;
            position: relative;
            padding: 0 1rem;
        }}
        
        .stepper-line-bg {{
            position: absolute;
            top: 24px;
            left: 20px;
            right: 20px;
            height: 3px;
            background-color: #e2e8f0;
            z-index: 0;
            border-radius: 99px;
        }}
        
        .stepper-step {{
            position: relative;
            z-index: 2;
            display: flex;
            flex-direction: column;
            align-items: center;
            cursor: default;
            flex: 1;
        }}
        
        .step-bubble {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background-color: white;
            border: 2px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1rem;
            color: #64748b;
            margin-bottom: 0.75rem;
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        }}
        
        .step-label {{
            font-size: 0.75rem;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: color 0.3s;
        }}
        
        /* Active State */
        .stepper-step.active .step-bubble {{
            background: {COR_AZUL_ESC};
            border-color: {COR_AZUL_ESC};
            color: white;
            transform: scale(1.15);
            box-shadow: 0 0 0 6px rgba(0, 44, 93, 0.15);
        }}
        .stepper-step.active .step-label {{
            color: {COR_AZUL_ESC};
        }}
        
        /* Completed State */
        .stepper-step.completed .step-bubble {{
            background: #10b981; /* Emerald 500 */
            border-color: #10b981;
            color: white;
        }}
        .stepper-step.completed .step-label {{
            color: #10b981;
        }}

        .footer {{ text-align: center; padding: 80px 0; color: {COR_AZUL_ESC} !important; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; opacity: 0.6; }}
        </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step_name):
    steps = [
        {"id": "input", "label": "Dados"},
        {"id": "guide", "label": "Análise"},
        {"id": "selection", "label": "Imóvel"},
        {"id": "payment_flow", "label": "Pagamento"},
        {"id": "summary", "label": "Resumo"}
    ]
    current_idx = 0
    for i, s in enumerate(steps):
        if s["id"] == current_step_name:
            current_idx = i
            break
    
    html = '<div class="stepper-container"><div class="stepper-line-bg"></div>'
    for i, step in enumerate(steps):
        status_class = ""
        icon_content = str(i + 1)
        if i < current_idx:
            status_class = "completed"
            icon_content = "✓"
        elif i == current_idx:
            status_class = "active"
        html += f"""<div class="stepper-step {status_class}">
    <div class="step-bubble">{icon_content}</div>
    <div class="step-label">{step['label']}</div>
</div>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def gerar_resumo_pdf(d):
    if not PDF_ENABLED:
        return None

    try:
        pdf = FPDF()
        pdf.add_page()

        # Margens
        pdf.set_margins(12, 12, 12)
        pdf.set_auto_page_break(auto=True, margin=12)

        largura_util = pdf.w - pdf.l_margin - pdf.r_margin

        AZUL = (0, 44, 93)
        VERMELHO = (227, 6, 19)
        BRANCO = (255, 255, 255)
        FUNDO_SECAO = (248, 250, 252)

        # Barra superior
        pdf.set_fill_color(*AZUL)
        pdf.rect(0, 0, pdf.w, 3, 'F')

        # Logo
        if os.path.exists("favicon.png"):
            try:
                pdf.image("favicon.png", pdf.l_margin, 8, 10)
            except:
                pass

        # Título
        pdf.ln(8)
        pdf.set_text_color(*AZUL)
        pdf.set_font("Helvetica", 'B', 20)
        pdf.cell(0, 10, "RELATORIO DE VIABILIDADE", ln=True, align='C')

        pdf.set_font("Helvetica", '', 9)
        pdf.cell(0, 5, "SIMULADOR IMOBILIARIO DV - DOCUMENTO EXECUTIVO", ln=True, align='C')
        pdf.ln(6)

        # Bloco cliente
        y = pdf.get_y()
        pdf.set_fill_color(*FUNDO_SECAO)
        pdf.rect(pdf.l_margin, y, largura_util, 16, 'F')

        pdf.set_xy(pdf.l_margin + 4, y + 4)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 5, f"CLIENTE: {d.get('nome', 'Nao informado').upper()}", ln=True)

        pdf.set_x(pdf.l_margin + 4)
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(0, 5, f"Renda Familiar: R$ {fmt_br(d.get('renda', 0))}", ln=True)

        pdf.ln(6)

        # Helpers
        def secao(titulo):
            pdf.set_fill_color(*AZUL)
            pdf.set_text_color(*BRANCO)
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(largura_util, 7, f"  {titulo}", ln=True, fill=True)
            pdf.ln(2)

        def linha(label, valor, destaque=False):
            pdf.set_text_color(*AZUL)
            pdf.set_font("Helvetica", '', 10)
            pdf.cell(largura_util * 0.6, 6, label)

            if destaque:
                pdf.set_text_color(*VERMELHO)
                pdf.set_font("Helvetica", 'B', 10)
            else:
                pdf.set_font("Helvetica", 'B', 10)

            pdf.cell(largura_util * 0.4, 6, valor, ln=True, align='R')
            pdf.set_draw_color(235, 238, 242)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + largura_util, pdf.get_y())

        # ===============================
        # CONTEÚDO
        # ===============================
        secao("DADOS DO IMOVEL")
        linha("Empreendimento", str(d.get('empreendimento_nome')))
        linha("Unidade Selecionada", str(d.get('unidade_id')))
        linha("Valor de Venda do Imovel", f"R$ {fmt_br(d.get('imovel_valor', 0))}", True)

        pdf.ln(4)

        secao("ENGENHARIA FINANCEIRA")
        linha("Financiamento Bancario Estimado", f"R$ {fmt_br(d.get('finan_usado', 0))}")
        prazo = d.get('prazo_financiamento', 360)
        linha("Sistema de Amortizacao", f"{d.get('sistema_amortizacao', 'SAC')} - {prazo}x")
        linha("Parcela Estimada Financiamento", f"R$ {fmt_br(d.get('parcela_financiamento', 0))}")
        linha("Subsidio + FGTS Utilizado", f"R$ {fmt_br(d.get('fgts_sub_usado', 0))}")
        linha("Pro Soluto Direcional", f"R$ {fmt_br(d.get('ps_usado', 0))}")
        linha("Mensalidade Pro Soluto", f"{d.get('ps_parcelas')}x de R$ {fmt_br(d.get('ps_mensal', 0))}")

        pdf.ln(4)

        secao("PLANO DE ENTRADA (FLUXO DE CAIXA)")
        linha("VALOR TOTAL DE ENTRADA", f"R$ {fmt_br(d.get('entrada_total', 0))}", True)
        linha("Parcela de Ato (Imediato)", f"R$ {fmt_br(d.get('ato_final', 0))}")
        linha("Parcela 30 Dias", f"R$ {fmt_br(d.get('ato_30', 0))}")
        linha("Parcela 60 Dias", f"R$ {fmt_br(d.get('ato_60', 0))}")
        linha("Parcela 90 Dias", f"R$ {fmt_br(d.get('ato_90', 0))}")

        # ===============================
        # SEÇÃO ANOTAÇÕES (preenche espaço)
        # ===============================
        pdf.ln(4)
        secao("ANOTAÇÕES")

        y_inicio = pdf.get_y()
        altura_rodape = 14
        altura_disponivel = pdf.h - pdf.b_margin - y_inicio - altura_rodape

        if altura_disponivel > 10:
            pdf.set_fill_color(250, 252, 255)
            pdf.rect(pdf.l_margin, y_inicio, largura_util, altura_disponivel, 'F')

            pdf.set_draw_color(220, 225, 230)
            linha_y = y_inicio + 6
            while linha_y < y_inicio + altura_disponivel - 4:
                pdf.line(
                    pdf.l_margin + 4,
                    linha_y,
                    pdf.l_margin + largura_util - 4,
                    linha_y
                )
                linha_y += 7

            pdf.set_y(y_inicio + altura_disponivel)

        # ===============================
        # RODAPÉ
        # ===============================
        pdf.set_font("Helvetica", 'I', 7)
        pdf.set_text_color(*AZUL)
        pdf.cell(
            0,
            4,
            f"Simulacao realizada em {d.get('data_simulacao', date.today().strftime('%d/%m/%Y'))}. "
            "Sujeito a analise de credito e alteracao de tabela sem aviso previo.",
            ln=True,
            align='C'
        )
        pdf.cell(0, 4, "Direcional Engenharia - Rio de Janeiro", ln=True, align='C')

        return bytes(pdf.output())

    except:
        return None

def enviar_email_smtp(destinatario, nome_cliente, pdf_bytes):
    if "email" not in st.secrets: return False, "Configuracoes de e-mail nao encontradas."
    try:
        smtp_server = st.secrets["email"]["smtp_server"].strip()
        smtp_port = int(st.secrets["email"]["smtp_port"])
        sender_email = st.secrets["email"]["sender_email"].strip()
        sender_password = st.secrets["email"]["sender_password"].strip().replace(" ", "")
    except Exception as e: return False, f"Erro config: {e}"

    msg = MIMEMultipart()
    msg['From'] = sender_email; msg['To'] = destinatario; msg['Subject'] = f"Resumo da Simulacao - {nome_cliente}"
    msg.attach(MIMEText(f"Ola,\n\nSegue em anexo o resumo da simulacao imobiliaria para {nome_cliente}.\n\nAtenciosamente,\nDirecional Engenharia", 'plain'))
    if pdf_bytes:
        part = MIMEApplication(pdf_bytes, Name=f"Resumo_{nome_cliente}.pdf")
        part['Content-Disposition'] = f'attachment; filename="Resumo_{nome_cliente}.pdf"'
        msg.attach(part)
    try:
        server = smtplib.SMTP(smtp_server, smtp_port); server.ehlo(); server.starttls(); server.ehlo()
        server.login(sender_email, sender_password); server.sendmail(sender_email, destinatario, msg.as_string()); server.quit()
        return True, "E-mail enviado com sucesso!"
    except smtplib.SMTPAuthenticationError:
        return False, "Erro de Autenticacao (535). Verifique Senha de App."
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
    # Alterado para text-align: center para alinhar com o tema
    st.markdown(f"<h3 style='text-align: center; color: {COR_AZUL_ESC}; margin: 0;'>Resumo da Simulação</h3>", unsafe_allow_html=True)
    st.markdown("Escolha como deseja exportar o documento.")
    pdf_data = gerar_resumo_pdf(d)

    if pdf_data:
        st.download_button(label="Baixar PDF", data=pdf_data, file_name=f"Resumo_Direcional_{d.get('nome', 'Cliente')}.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.warning("Geração de PDF indisponível.")

    st.markdown("---")
    st.markdown("**Enviar por E-mail**")
    email = st.text_input("Endereço de e-mail", placeholder="cliente@exemplo.com")
    if st.button("Enviar Email", use_container_width=True):
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

    # --- SIDEBAR PERFIL (ATUALIZADA) ---
    with st.sidebar:
        user_name = st.session_state.get('user_name', 'Corretor').upper()
        user_cargo = st.session_state.get('user_cargo', 'Consultor').upper()
        user_imob = st.session_state.get('user_imobiliaria', 'Direcional').upper()

        st.markdown(f"""
        <div class="sidebar-profile">
            <div class="profile-avatar">{user_name[0] if user_name else 'C'}</div>
            <div class="profile-name">{user_name}</div>
            <div class="profile-role">{user_cargo}</div>
            <div class="profile-sub">{user_imob}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Histórico de Simulações")

        search_term = st.text_input("Buscar cliente...", placeholder="Digite o nome", label_visibility="collapsed")

        try:
            df_h = df_cadastros.copy()
            if not df_h.empty:
                col_corretor = next((c for c in df_h.columns if 'Nome do Corretor' in c), None)
                col_nome_cliente = next((c for c in df_h.columns if c == 'Nome'), None)
                col_data_sim = next((c for c in df_h.columns if 'Data' in c and '/' in str(df_h[c].iloc[0])), None)

                if col_corretor:
                    my_hist = df_h[df_h[col_corretor].astype(str).str.strip().str.upper() == user_name.strip()]
                    if search_term and col_nome_cliente:
                        my_hist = my_hist[my_hist[col_nome_cliente].astype(str).str.contains(search_term, case=False, na=False)]
                    my_hist = my_hist.tail(15).iloc[::-1]

                    if not my_hist.empty:
                        for idx, row in my_hist.iterrows():
                            c_nome = row.get('Nome', 'Cli')
                            c_emp = row.get('Empreendimento Final', 'Emp')
                            c_data = ""
                            if col_data_sim and pd.notnull(row.get(col_data_sim)):
                                try: c_data = str(row.get(col_data_sim)).split('.')[0]
                                except: pass

                            label = f"{c_nome} | {c_emp}"
                            if c_data: label += f" | {c_data}"

                            if st.button(label, key=f"hist_{idx}", use_container_width=True):
                                st.session_state.dados_cliente = {
                                    'nome': row.get('Nome'), 'empreendimento_nome': row.get('Empreendimento Final'),
                                    'unidade_id': row.get('Unidade Final'),
                                    'imovel_valor': safe_float_convert(row.get('Preço Unidade Final', 0)),
                                    'finan_estimado': safe_float_convert(row.get('Financiamento Aprovado', 0)),
                                    'fgts_sub': safe_float_convert(row.get('Subsídio Máximo', 0)),
                                    'finan_usado': safe_float_convert(row.get('Financiamento Final', 0)),
                                    'fgts_sub_usado': safe_float_convert(row.get('FGTS + Subsídio Final', 0)),
                                    'ps_usado': safe_float_convert(row.get('Pro Soluto Final', 0)),
                                    'ps_parcelas': int(float(str(row.get('Número de Parcelas do Pro Soluto', 0)).replace(',','.'))),
                                    'ps_mensal': safe_float_convert(row.get('Mensalidade PS', 0)),
                                    'ato_final': safe_float_convert(row.get('Ato', 0)),
                                    'ato_30': safe_float_convert(row.get('Ato 30', 0)),
                                    'ato_60': safe_float_convert(row.get('Ato 60', 0)),
                                    'ato_90': safe_float_convert(row.get('Ato 90', 0)),
                                }
                                st.session_state.dados_cliente['entrada_total'] = st.session_state.dados_cliente['ato_final'] + st.session_state.dados_cliente['ato_30'] + st.session_state.dados_cliente['ato_60'] + st.session_state.dados_cliente['ato_90']
                                st.session_state.passo_simulacao = 'summary'
                                scroll_to_top()
                                st.rerun()
                    else: st.caption("Nenhum histórico recente.")
                else: st.caption("Coluna de corretor não encontrada.")
            else: st.caption("Sem dados cadastrados.")
        except Exception as e: st.caption(f"Erro histórico: {str(e)}")

    # RENDER PROGRESS BAR
    render_stepper(passo)

    # --- ETAPA 1: INPUT ---
    if passo == 'input':
        st.markdown("### Dados do Cliente")
        nome = st.text_input("Nome Completo", value=st.session_state.dados_cliente.get('nome', ""), placeholder="Nome Completo", key="in_nome_v28")

        cpf_val = st.text_input("CPF", value=st.session_state.dados_cliente.get('cpf', ""), placeholder="000.000.000-00", key="in_cpf_v3", max_chars=14)
        if cpf_val and not validar_cpf(cpf_val):
            st.markdown(f"<small style='color: {COR_VERMELHO};'>CPF inválido</small>", unsafe_allow_html=True)

        d_nasc_default = st.session_state.dados_cliente.get('data_nascimento', date(1990, 1, 1))
        if isinstance(d_nasc_default, str):
            try: d_nasc_default = datetime.strptime(d_nasc_default, '%Y-%m-%d').date()
            except: d_nasc_default = date(1990, 1, 1)

        data_nasc = st.date_input("Data de Nascimento", value=d_nasc_default, min_value=date(1900, 1, 1), max_value=datetime.now().date(), format="DD/MM/YYYY", key="in_dt_nasc_v3")
        genero = st.selectbox("Gênero", ["Masculino", "Feminino", "Outro"], index=0, key="in_genero_v3")

        st.markdown("---")
        qtd_part = st.number_input("Participantes na Renda", min_value=1, max_value=4, value=st.session_state.dados_cliente.get('qtd_participantes', 1), step=1, key="qtd_part_v3")

        cols_renda = st.columns(qtd_part)
        renda_total_calc = 0.0
        lista_rendas_input = []
        rendas_anteriores = st.session_state.dados_cliente.get('rendas_lista', [])
        
        # Helper to clear input on empty
        def get_val(idx, default):
            v = float(rendas_anteriores[idx]) if idx < len(rendas_anteriores) else default
            return None if v == 0.0 else v

        for i in range(qtd_part):
            with cols_renda[i]:
                def_val = 3500.0 if i == 0 and not rendas_anteriores else 0.0
                current_val = get_val(i, def_val)
                val_r = st.number_input(f"Renda Part. {i+1}", min_value=0.0, value=current_val, step=100.0, key=f"renda_part_{i}_v3", placeholder="0,00")
                if val_r is None: val_r = 0.0
                renda_total_calc += val_r; lista_rendas_input.append(val_r)

        rank_opts = ["DIAMANTE", "OURO", "PRATA", "BRONZE", "AÇO"]
        ranking = st.selectbox("Ranking do Cliente", options=rank_opts, index=0, key="in_rank_v28")
        politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"], key="in_pol_v28")
        social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False), key="in_soc_v28")
        cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True), key="in_cot_v28")

        st.markdown("<br>", unsafe_allow_html=True)

        def processar_avanco(destino):
            if not nome.strip(): st.markdown(f'<div class="custom-alert">Por favor, informe o Nome do Cliente para continuar.</div>', unsafe_allow_html=True); return
            if not cpf_val.strip(): st.markdown(f'<div class="custom-alert">Por favor, informe o CPF do Cliente.</div>', unsafe_allow_html=True); return
            if not validar_cpf(cpf_val): st.markdown(f'<div class="custom-alert">CPF Inválido. Corrija para continuar.</div>', unsafe_allow_html=True); return
            if renda_total_calc <= 0: st.markdown(f'<div class="custom-alert">A renda total deve ser maior que zero.</div>', unsafe_allow_html=True); return

            class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
            map_ps_percent = {'EMCASH': 0.25, 'DIAMANTE': 0.25, 'OURO': 0.20, 'PRATA': 0.18, 'BRONZE': 0.15, 'AÇO': 0.12}
            perc_ps_max = map_ps_percent.get(class_b, 0.12)
            prazo_ps_max = 66 if politica_ps == "Emcash" else 84
            limit_ps_r = 0.30
            f_faixa_ref, s_faixa_ref, fx_nome_ref = motor.obter_enquadramento(renda_total_calc, social, cotista, valor_avaliacao=240000)

            st.session_state.dados_cliente.update({
                'nome': nome, 'cpf': limpar_cpf_visual(cpf_val), 'data_nascimento': data_nasc, 'genero': genero,
                'renda': renda_total_calc, 'rendas_lista': lista_rendas_input,
                'social': social, 'cotista': cotista, 'ranking': ranking, 'politica': politica_ps,
                'perc_ps': perc_ps_max, 'prazo_ps_max': prazo_ps_max,
                'limit_ps_renda': limit_ps_r, 'finan_f_ref': f_faixa_ref, 'sub_f_ref': s_faixa_ref,
                'qtd_participantes': qtd_part
            })
            st.session_state.passo_simulacao = destino
            scroll_to_top()
            st.rerun()

        if st.button("Obter recomendações", type="primary", use_container_width=True, key="btn_avancar_guide"):
            processar_avanco('guide')

        st.write("") 

        if st.button("Ir direto para escolha de unidades", use_container_width=True, key="btn_avancar_direto"):
            processar_avanco('selection')

    # --- ETAPA 2: RECOMENDAÇÃO ---
    elif passo == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### Recomendação de Imóveis")

        df_disp_total = df_estoque[df_estoque['Status'] == 'Disponível'].copy()

        if df_disp_total.empty: st.markdown('<div class="custom-alert">Sem produtos viaveis no perfil selecionado.</div>', unsafe_allow_html=True); df_viaveis = pd.DataFrame()
        else:
            def calcular_viabilidade_unidade(row):
                v_venda = row['Valor de Venda']
                v_aval = row['Valor de Avaliação Bancária']
                try: v_venda = float(v_venda)
                except: v_venda = 0.0
                try: v_aval = float(v_aval)
                except: v_aval = v_venda

                fin, sub, fx_n = motor.obter_enquadramento(d.get('renda', 0), d.get('social', False), d.get('cotista', True), v_aval)
                ps_max_val = v_venda * d.get('perc_ps', 0.10)
                capacity = ps_max_val + fin + sub + (2 * d.get('renda', 0))
                cobertura = (capacity / v_venda) * 100 if v_venda > 0 else 0
                is_viavel = capacity >= v_venda
                return pd.Series([capacity, cobertura, is_viavel, fin, sub])

            df_disp_total[['Poder_Compra', 'Cobertura', 'Viavel', 'Finan_Unid', 'Sub_Unid']] = df_disp_total.apply(calcular_viabilidade_unidade, axis=1)
            df_viaveis = df_disp_total[df_disp_total['Viavel']].copy()

        tab_viaveis, tab_sugestoes, tab_estoque = st.tabs(["EMPREENDIMENTOS VIÁVEIS", "RECOMENDAÇÃO DE UNIDADES", "ESTOQUE GERAL"])

        with tab_viaveis:
             st.markdown("<br>", unsafe_allow_html=True)
             if df_viaveis.empty:
                 if not df_disp_total.empty:
                    cheapest = df_disp_total.sort_values('Valor de Venda', ascending=True).iloc[0]
                    emp_fallback = cheapest['Empreendimento']
                    st.markdown(f"""
                            <div class="card" style="min-height: 80px; padding: 15px; border-top: 3px solid {COR_AZUL_ESC};">
                                <p style="margin:0; font-weight:700; color:{COR_AZUL_ESC};">{emp_fallback}</p>
                                <p style="margin:5px 0 0 0; font-size:0.85rem; color:{COR_TEXTO_MUTED};">Melhor preço disponível: R$ {fmt_br(cheapest['Valor de Venda'])}</p>
                            </div>
                        """, unsafe_allow_html=True)
                 else:
                    st.error("Sem estoque disponível.")
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
                                <div class="card" style="min-height: 80px; padding: 15px; border-top: 3px solid {COR_AZUL_ESC};">
                                    <p style="margin:0; font-weight:700; color:{COR_AZUL_ESC};">{emp}</p>
                                    <p style="margin:5px 0 0 0; font-size:0.85rem; color:{COR_TEXTO_MUTED};">{qtd} unidades viáveis</p>
                                </div>
                            """, unsafe_allow_html=True)

        with tab_sugestoes:
            st.markdown("<br>", unsafe_allow_html=True)
            emp_names_rec = sorted(df_disp_total['Empreendimento'].unique().tolist())
            emp_rec = st.selectbox("Escolha um empreendimento para obter recomendações:", options=["Todos"] + emp_names_rec, key="sel_emp_rec_v28")
            df_pool = df_disp_total if emp_rec == "Todos" else df_disp_total[df_disp_total['Empreendimento'] == emp_rec]

            if df_pool.empty: st.markdown('<div class="custom-alert">Nenhuma unidade encontrada.</div>', unsafe_allow_html=True)
            else:
                pool_viavel = df_pool[df_pool['Viavel']]
                cand_facil = pd.DataFrame(); cand_ideal = pd.DataFrame(); cand_seguro = pd.DataFrame()
                
                # Logic: We need 3 cards: Ideal, Seguro, Facilitado.
                # If we don't have perfect matches, we fallback to cheapest available options.
                
                # 1. Try to find logic matches first
                if not pool_viavel.empty:
                    # Ideal: 100% coverage, most expensive one that fits
                    ideal_pool = pool_viavel[pool_viavel['Cobertura'] >= 100]
                    if not ideal_pool.empty:
                        cand_ideal = ideal_pool.sort_values('Valor de Venda', ascending=False).head(1)
                    
                    # Seguro: Highest Coverage (safest bet), regardless of price
                    cand_seguro = pool_viavel.sort_values('Cobertura', ascending=False).head(1)
                    
                    # Facilitado: Lowest Price (easiest to buy)
                    cand_facil = pool_viavel.sort_values('Valor de Venda', ascending=True).head(1)
                
                # 2. Collect what we found
                found_units = []
                if not cand_ideal.empty: found_units.append({'type': 'IDEAL', 'row': cand_ideal.iloc[0]})
                if not cand_seguro.empty: found_units.append({'type': 'SEGURO', 'row': cand_seguro.iloc[0]})
                if not cand_facil.empty: found_units.append({'type': 'FACILITADO', 'row': cand_facil.iloc[0]})
                
                # Deduplicate based on price/id to avoid showing same unit 3 times if possible, 
                # but user asked for 3 units always. If logic returns same unit for all 3 (e.g. only 1 unit exists),
                # we must show it 3 times or find others?
                # User said: "Se o 90% nao der, recomende a de 100%, a mais barata e a segunda mais barata."
                # This implies finding *distinct* units if possible.
                
                # Let's get top 3 cheapest units from pool as base fallback
                fallback_pool = df_pool.sort_values('Valor de Venda', ascending=True)
                
                final_cards = []
                
                # Strategy: Fill slots 1(Ideal), 2(Seguro), 3(Facilitado)
                # Slot 1: Logic Ideal -> Fallback Cheapest
                # Slot 2: Logic Seguro -> Fallback 2nd Cheapest
                # Slot 3: Logic Facilitado -> Fallback 3rd Cheapest
                
                # Helper to get unique unit not already in final_cards
                def get_fallback_unit(exclude_ids):
                    for idx, row in fallback_pool.iterrows():
                        if row['Identificador'] not in exclude_ids:
                            return row
                    return None

                # Card 1: IDEAL
                if not cand_ideal.empty:
                    final_cards.append({'label': 'IDEAL', 'row': cand_ideal.iloc[0], 'css': 'badge-ideal'})
                else:
                    # Fallback 1: Cheapest (100% coverage unit not found, maybe expensive)
                    # Logic says: "Se 100% nao der, recomende a mais barata"
                    u = get_fallback_unit([])
                    if u is not None: final_cards.append({'label': 'IDEAL', 'row': u, 'css': 'badge-ideal'})

                # Card 2: SEGURO
                exclude = [c['row']['Identificador'] for c in final_cards]
                if not cand_seguro.empty and cand_seguro.iloc[0]['Identificador'] not in exclude:
                      final_cards.append({'label': 'SEGURO', 'row': cand_seguro.iloc[0], 'css': 'badge-seguro'})
                else:
                    # Fallback 2: 2nd Cheapest
                    u = get_fallback_unit(exclude)
                    if u is not None: final_cards.append({'label': 'SEGURO', 'row': u, 'css': 'badge-seguro'})
                
                # Card 3: FACILITADO
                exclude = [c['row']['Identificador'] for c in final_cards]
                if not cand_facil.empty and cand_facil.iloc[0]['Identificador'] not in exclude:
                      final_cards.append({'label': 'FACILITADO', 'row': cand_facil.iloc[0], 'css': 'badge-facilitado'})
                else:
                      # Fallback 3: 3rd Cheapest
                      u = get_fallback_unit(exclude)
                      if u is not None: final_cards.append({'label': 'FACILITADO', 'row': u, 'css': 'badge-facilitado'})

                # Render
                if not final_cards: st.warning("Nenhuma unidade encontrada.")
                else:
                    cols = st.columns(len(final_cards))
                    for idx, card in enumerate(final_cards):
                        row = card['row']
                        with cols[idx]:
                            st.markdown(f'''
                            <div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC}; height: 100%; justify-content: flex-start;">
                                <span style="font-size:0.65rem; color:{COR_AZUL_ESC}; opacity:0.8;">PERFIL</span><br>
                                <div style="margin-top:5px; margin-bottom:15px;"><span class="{card['css']}">{card['label']}</span></div>
                                <b style="color:{COR_AZUL_ESC}; font-size:1.1rem;">{row['Empreendimento']}</b><br>
                                <div style="font-size:0.85rem; color:{COR_TEXTO_MUTED}; text-align:center; border-top:1px solid #eee; padding-top:10px; width:100%;">
                                    <b>Unidade: {row['Identificador']}</b>
                                </div>
                                <div class="price-tag" style="font-size:1.4rem; margin:10px 0;">R$ {fmt_br(row['Valor de Venda'])}</div>
                            </div>''', unsafe_allow_html=True)

        with tab_estoque:
            if df_disp_total.empty:
                st.markdown('<div class="custom-alert">Sem dados para exibir.</div>', unsafe_allow_html=True)
            else:
                f_cols = st.columns([1.2, 1.5, 1, 1, 1])
                with f_cols[0]: f_bairro = st.multiselect("Bairro:", options=sorted(df_disp_total['Bairro'].unique()), key="f_bairro_tab_v28")
                with f_cols[1]: f_emp = st.multiselect("Empreendimento:", options=sorted(df_disp_total['Empreendimento'].unique()), key="f_emp_tab_v28")
                with f_cols[2]:
                    cob_opts = ["Todas", "Acima de 10%", "Acima de 20%", "Acima de 30%", "Acima de 40%", "Acima de 50%", "Acima de 60%", "Acima de 70%", "Acima de 80%", "Acima de 90%", "100%"]
                    f_cob_sel = st.selectbox("Cobertura Mínima:", options=cob_opts, key="f_cob_sel_v28")
                    cob_min_val = 0
                    if "10%" in f_cob_sel: cob_min_val = 10
                    elif "20%" in f_cob_sel: cob_min_val = 20
                    elif "30%" in f_cob_sel: cob_min_val = 30
                    elif "40%" in f_cob_sel: cob_min_val = 40
                    elif "50%" in f_cob_sel: cob_min_val = 50
                    elif "60%" in f_cob_sel: cob_min_val = 60
                    elif "70%" in f_cob_sel: cob_min_val = 70
                    elif "80%" in f_cob_sel: cob_min_val = 80
                    elif "90%" in f_cob_sel: cob_min_val = 90
                    elif "100%" in f_cob_sel: cob_min_val = 100

                with f_cols[3]: f_ordem = st.selectbox("Ordem:", ["Menor Preço", "Maior Preço"], key="f_ordem_tab_v28")
                # CSS Hack for height matching - applied via class injection on main style usually, but here specific inline if needed or via container
                with f_cols[4]: f_pmax = st.number_input("Preço Máx:", value=None, key="f_pmax_tab_v28", placeholder="0,00")

                df_tab = df_disp_total.copy()
                if f_bairro: df_tab = df_tab[df_tab['Bairro'].isin(f_bairro)]
                if f_emp: df_tab = df_tab[df_tab['Empreendimento'].isin(f_emp)]
                df_tab = df_tab[df_tab['Cobertura'] >= cob_min_val]
                if f_pmax: df_tab = df_tab[df_tab['Valor de Venda'] <= f_pmax]

                if f_ordem == "Menor Preço": df_tab = df_tab.sort_values('Valor de Venda', ascending=True)
                else: df_tab = df_tab.sort_values('Valor de Venda', ascending=False)

                df_tab_view = df_tab.copy()
                df_tab_view['Valor de Venda'] = df_tab_view['Valor de Venda'].apply(fmt_br)
                df_tab_view['Poder_Compra'] = df_tab_view['Poder_Compra'].apply(fmt_br)
                df_tab_view['Cobertura'] = df_tab_view['Cobertura'].apply(lambda x: f"{x:.1f}%")

                st.dataframe(
                    df_tab_view[['Identificador', 'Bairro', 'Empreendimento', 'Valor de Venda', 'Poder_Compra', 'Cobertura']],
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Identificador": st.column_config.TextColumn("Unidade"),
                        "Valor de Venda": st.column_config.TextColumn("Preço (R$)"),
                        "Poder_Compra": st.column_config.TextColumn("Poder Real (R$)"),
                        "Cobertura": st.column_config.TextColumn("% Cobertura"),
                    }
                )

        st.markdown("---")
        if st.button("Avançar para Escolha de Unidade", type="primary", use_container_width=True, key="btn_goto_selection"): st.session_state.passo_simulacao = 'selection'; scroll_to_top(); st.rerun()
        st.write("");
        if st.button("Voltar para Dados do Cliente", use_container_width=True, key="btn_pot_v28"): st.session_state.passo_simulacao = 'input'; scroll_to_top(); st.rerun()

    # --- ETAPA 3: SELEÇÃO + TERMOMETRO ---
    elif passo == 'selection':
        d = st.session_state.dados_cliente
        st.markdown(f"### Escolha de Unidade")

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
                            <div style="width: {percentual_cobertura}%; background: linear-gradient(90deg, #e30613 0%, #002c5d 100%); height: 100%; border-radius: 5px; transition: width 0.5s;"></div>
                        </div>
                        <small>{percentual_cobertura:.1f}% Coberto</small>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Avançar para Fechamento Financeiro", type="primary", use_container_width=True):
                if uni_escolhida_id:
                    u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                    fin, sub, _ = motor.obter_enquadramento(d.get('renda', 0), d.get('social', False), d.get('cotista', True), u_row['Valor de Avaliação Bancária'])
                    st.session_state.dados_cliente.update({
                        'unidade_id': uni_escolhida_id, 'empreendimento_nome': emp_escolhido,
                        'imovel_valor': u_row['Valor de Venda'], 'imovel_avaliacao': u_row['Valor de Avaliação Bancária'],
                        'finan_estimado': fin, 'fgts_sub': sub
                    })
                    st.session_state.passo_simulacao = 'payment_flow'; scroll_to_top(); st.rerun()
            if st.button("Voltar para Recomendação de Imóveis", use_container_width=True): st.session_state.passo_simulacao = 'guide'; scroll_to_top(); st.rerun()

    # --- ETAPA 4: FECHAMENTO FINANCEIRO ---
    elif passo == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### Fechamento Financeiro")
        u_valor = d.get('imovel_valor', 0)
        u_nome = d.get('empreendimento_nome', 'N/A')
        u_unid = d.get('unidade_id', 'N/A')

        st.markdown(f'<div class="custom-alert">{u_nome} - {u_unid} (R$ {fmt_br(u_valor)})</div>', unsafe_allow_html=True)

        def get_float_or_none(val):
            return None if val == 0.0 else val

        # 1. Valor Financiamento (Full width)
        current_finan = get_float_or_none(float(d.get('finan_estimado', 0)))
        f_u_input = st.number_input("Financiamento", value=current_finan, step=1000.0, key="fin_u_v28", placeholder="0,00")
        f_u = f_u_input if f_u_input is not None else 0.0
        st.markdown(f'<span class="inline-ref">Financiamento Máximo: R$ {fmt_br(d.get("finan_estimado", 0))}</span>', unsafe_allow_html=True)

        # 2. Prazo (Full width)
        prazo_finan = st.selectbox("Prazo Financiamento (Meses)", [360, 420], key="prazo_v3_closed")

        # 3. Tabela (Full width)
        tab_fin = st.selectbox("Sistema de Amortização", ["SAC", "PRICE"], key="tab_fin_v28")
        
        # Display estimated installments (Dynamic Calculation)
        # Using the selected 'prazo_finan' to update values immediately
        taxa_padrao = 8.16 # Taxa fixa padrão para estimativa
        sac_details = calcular_comparativo_sac_price(f_u, prazo_finan, taxa_padrao)["SAC"]
        price_details = calcular_comparativo_sac_price(f_u, prazo_finan, taxa_padrao)["PRICE"]
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-around; margin-bottom: 20px; font-size: 0.85rem; color: #64748b;">
            <span><b>SAC:</b> R$ {fmt_br(sac_details['primeira'])} a R$ {fmt_br(sac_details['ultima'])} (Juros: R$ {fmt_br(sac_details['juros'])})</span>
            <span><b>PRICE:</b> R$ {fmt_br(price_details['parcela'])} fixas (Juros: R$ {fmt_br(price_details['juros'])})</span>
        </div>
        """, unsafe_allow_html=True)

        # FGTS (Full width)
        current_fgts = get_float_or_none(float(d.get('fgts_sub', 0)))
        fgts_u_input = st.number_input("FGTS + Subsídio", value=current_fgts, step=1000.0, key="fgt_u_v28", placeholder="0,00")
        fgts_u = fgts_u_input if fgts_u_input is not None else 0.0
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

        ps_atual = st.session_state.get('ps_u_view', 0)
        # Handle None from input
        if ps_atual is None: ps_atual = 0.0
        
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

        # Botões de Distribuição Automática Alinhados
        st.markdown('<label style="font-size: 0.8rem; font-weight: 600;">Distribuir Atos Automaticamente:</label>', unsafe_allow_html=True)
        col_dist1, col_dist2, col_dist3, col_dist4 = st.columns(4)

        with col_dist1:
             if st.button("1x", use_container_width=True, key="btn_d1"): distribuir(1)
        with col_dist2:
             if st.button("2x", use_container_width=True, key="btn_d2"): distribuir(2)
        with col_dist3:
             if st.button("3x", use_container_width=True, key="btn_d3"): distribuir(3)
        with col_dist4:
             if st.button("4x", use_container_width=True, disabled=is_emcash, key="btn_d4"): distribuir(4)

        if 'ato_1_v28' not in st.session_state: st.session_state['ato_1_v28'] = st.session_state.ato_1
        if 'ato_2_v28' not in st.session_state: st.session_state['ato_2_v28'] = st.session_state.ato_2
        if 'ato_3_v28' not in st.session_state: st.session_state['ato_3_v28'] = st.session_state.ato_3
        if 'ato_4_v28' not in st.session_state: st.session_state['ato_4_v28'] = st.session_state.ato_4

        st.write("") # Espaçamento
        col_a, col_b = st.columns(2)
        with col_a:
            v1 = get_float_or_none(st.session_state.ato_1)
            r1 = st.number_input("Ato (Imediato)", key="ato_1_v28", step=100.0, value=v1, placeholder="0,00")
            st.session_state.ato_1 = r1 if r1 is not None else 0.0

            v3 = get_float_or_none(st.session_state.ato_3)
            r3 = st.number_input("Ato 60 Dias", key="ato_3_v28", step=100.0, value=v3, placeholder="0,00")
            st.session_state.ato_3 = r3 if r3 is not None else 0.0

        with col_b:
            v2 = get_float_or_none(st.session_state.ato_2)
            r2 = st.number_input("Ato 30 Dias", key="ato_2_v28", step=100.0, value=v2, placeholder="0,00")
            st.session_state.ato_2 = r2 if r2 is not None else 0.0

            v4 = get_float_or_none(st.session_state.ato_4)
            r4 = st.number_input("Ato 90 Dias", key="ato_4_v28", step=100.0, disabled=is_emcash, value=v4, placeholder="0,00")
            st.session_state.ato_4 = r4 if r4 is not None else 0.0

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_ps_val, col_ps_parc = st.columns(2)

        ps_max_real = u_valor * d.get('perc_ps', 0)
        with col_ps_val:
            ps_u_input = st.number_input("Pro Soluto Direcional", value=None, step=1000.0, key="ps_u_view", placeholder="0,00")
            ps_u = ps_u_input if ps_u_input is not None else 0.0
            st.markdown(f'<span class="inline-ref">Limite Permitido ({d.get("perc_ps", 0)*100:.0f}%): R$ {fmt_br(ps_max_real)}</span>', unsafe_allow_html=True)

        with col_ps_parc:
            parc = st.number_input("Parcelas Pro Soluto", min_value=1, max_value=d.get("prazo_ps_max", 60), value=min(60, d.get("prazo_ps_max", 60)), key="parc_u_v28")
            st.markdown(f'<span class="inline-ref">Prazo Máximo: {d.get("prazo_ps_max", 0)} meses</span>', unsafe_allow_html=True)

        v_parc = ps_u / parc if parc > 0 else 0
        total_pago = f_u + fgts_u + ps_u + st.session_state.ato_1 + st.session_state.ato_2 + st.session_state.ato_3 + st.session_state.ato_4
        gap_final = u_valor - total_pago

        fin1, fin2, fin3 = st.columns(3)
        with fin1: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b>VALOR DO IMÓVEL</b><br>R$ {fmt_br(u_valor)}</div>""", unsafe_allow_html=True)
        with fin2: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_VERMELHO};"><b>MENSALIDADE PS</b><br>R$ {fmt_br(v_parc)} ({parc}x)</div>""", unsafe_allow_html=True)

        # Validação visual do saldo
        cor_saldo = COR_AZUL_ESC

        with fin3: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {cor_saldo};"><b>SALDO A COBRIR</b><br>R$ {fmt_br(gap_final)}</div>""", unsafe_allow_html=True)

        if abs(gap_final) > 1:
            msg_saldo = f"Atenção: {'Falta cobrir' if gap_final > 0 else 'Valor excedente de'} R$ {fmt_br(abs(gap_final))}."
            st.error(msg_saldo)

        total_entrada_cash = st.session_state.ato_1 + st.session_state.ato_2 + st.session_state.ato_3 + st.session_state.ato_4

        # Calcular parcela financiamento para salvar
        taxa_juros_padrao = 8.16 # Taxa média mercado/MCMV para estimativa
        parcela_fin = calcular_parcela_financiamento(f_u, prazo_finan, taxa_juros_padrao, tab_fin)

        st.session_state.dados_cliente.update({
            'finan_usado': f_u,
            'fgts_sub_usado': fgts_u,
            'ps_usado': ps_u,
            'ps_parcelas': parc,
            'ps_mensal': v_parc,
            'entrada_total': total_entrada_cash,
            'ato_final': st.session_state.ato_1,
            'ato_30': st.session_state.ato_2,
            'ato_60': st.session_state.ato_3,
            'ato_90': st.session_state.ato_4,
            'sistema_amortizacao': tab_fin,
            'prazo_financiamento': prazo_finan, # Atualiza prazo
            'parcela_financiamento': parcela_fin
        })

        st.markdown("---")
        if st.button("Avançar para Resumo da Simulação", type="primary", use_container_width=True):
            if abs(gap_final) <= 1:
                st.session_state.passo_simulacao = 'summary'
                scroll_to_top()
                st.rerun()
            else:
                st.error(f"Não é possível avançar. O valor total pago deve ser igual ao valor do imóvel (Saldo R$ 0,00).")

        if st.button("Voltar para Escolha de Unidade", use_container_width=True): st.session_state.passo_simulacao = 'selection'; scroll_to_top(); st.rerun()

    # --- ETAPA 5: RESUMO ---
    elif passo == 'summary':
        d = st.session_state.dados_cliente
        st.markdown(f"### Resumo da Simulação - {d.get('nome', 'Cliente')}")
        st.markdown(f'<div class="summary-header">DADOS DO IMÓVEL</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Empreendimento:</b> {d.get('empreendimento_nome')}<br><b>Unidade:</b> {d.get('unidade_id')}<br><b>Valor de Venda:</b> <span style="color: {COR_VERMELHO}; font-weight: 800;">R$ {fmt_br(d.get('imovel_valor', 0))}</span></div>""", unsafe_allow_html=True)
        st.markdown(f'<div class="summary-header">PLANO DE FINANCIAMENTO</div>', unsafe_allow_html=True)

        # Exibe parcelas formatadas com prazo
        prazo_txt = d.get('prazo_financiamento', 360)
        parcela_texto = f"Parcela Estimada ({d.get('sistema_amortizacao', 'SAC')} - {prazo_txt}x): R$ {fmt_br(d.get('parcela_financiamento', 0))}"

        st.markdown(f"""<div class="summary-body"><b>Financiamento Bancário:</b> R$ {fmt_br(d.get('finan_usado', 0))}<br><b>{parcela_texto}</b><br><b>FGTS + Subsídio:</b> R$ {fmt_br(d.get('fgts_sub_usado', 0))}<br><b>Pro Soluto Total:</b> R$ {fmt_br(d.get('ps_usado', 0))} ({d.get('ps_parcelas')}x de R$ {fmt_br(d.get('ps_mensal', 0))})</div>""", unsafe_allow_html=True)
        st.markdown(f'<div class="summary-header">FLUXO DE ENTRADA (ATO)</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Total de Entrada:</b> R$ {fmt_br(d.get('entrada_total', 0))}<br><hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 10px 0;"><b>Ato:</b> R$ {fmt_br(d.get('ato_final', 0))}<br><b>Ato 30 Dias:</b> R$ {fmt_br(d.get('ato_30', 0))}<br><b>Ato 60 Dias:</b> R$ {fmt_br(d.get('ato_60', 0))}<br><b>Ato 90 Dias:</b> R$ {fmt_br(d.get('ato_90', 0))}</div>""", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("Opções de Resumo (PDF / E-mail)", use_container_width=True):
            show_export_dialog(d)

        st.markdown("---")
        if st.button("CONCLUIR E SALVAR SIMULAÇÃO", type="primary", use_container_width=True):
            
            # --- ENVIO AUTOMÁTICO DE EMAIL ---
            broker_email = st.session_state.get('user_email')
            if broker_email:
                with st.spinner("Gerando PDF e enviando para seu e-mail..."):
                    pdf_bytes_auto = gerar_resumo_pdf(d)
                    if pdf_bytes_auto:
                        sucesso_email, msg_email = enviar_email_smtp(broker_email, d.get('nome', 'Cliente'), pdf_bytes_auto)
                        if sucesso_email:
                            st.toast("PDF enviado para seu e-mail com sucesso!", icon="📧")
                        else:
                            st.toast(f"Falha no envio automático: {msg_email}", icon="⚠️")
            # ---------------------------------
            
            try:
                conn_save = st.connection("gsheets", type=GSheetsConnection)
                aba_destino = 'Simulações'
                rendas_ind = d.get('rendas_lista', [])
                while len(rendas_ind) < 4: rendas_ind.append(0.0)

                # Capacidade de entrada pode ser o Total pago - Financiamento - Subsídio
                capacidade_entrada = d.get('entrada_total', 0) + d.get('ps_usado', 0)

                nova_linha = {
                    "Nome": d.get('nome'),
                    "CPF": d.get('cpf'),
                    "Data de Nascimento": str(d.get('data_nascimento')),
                    "Prazo Financiamento": d.get('prazo_financiamento'),
                    "Renda Part. 1": rendas_ind[0],
                    "Renda Part. 4": rendas_ind[3],
                    "Renda Part. 3": rendas_ind[2],
                    "Renda Part. 4.1": 0.0,
                    "Ranking": d.get('ranking'),
                    "Política de Pro Soluto": d.get('politica'),
                    "Fator Social": "Sim" if d.get('social') else "Não",
                    "Cotista FGTS": "Sim" if d.get('cotista') else "Não",
                    "Financiamento Aprovado": d.get('finan_f_ref', 0),
                    "Subsídio Máximo": d.get('sub_f_ref', 0),
                    "Pro Soluto Médio": d.get('ps_usado', 0), # Usando o valor efetivo como referência
                    "Capacidade de Entrada": capacidade_entrada,
                    "Poder de Aquisição Médio": (2 * d.get('renda', 0)) + d.get('finan_f_ref', 0) + d.get('sub_f_ref', 0) + (d.get('imovel_valor', 0) * 0.10), # Estimativa
                    "Empreendimento Final": d.get('empreendimento_nome'),
                    "Unidade Final": d.get('unidade_id'),
                    "Preço Unidade Final": d.get('imovel_valor', 0),
                    "Financiamento Final": d.get('finan_usado', 0),
                    "FGTS + Subsídio Final": d.get('fgts_sub_usado', 0),
                    "Pro Soluto Final": d.get('ps_usado', 0),
                    "Número de Parcelas do Pro Soluto": d.get('ps_parcelas', 0),
                    "Mensalidade PS": d.get('ps_mensal', 0),
                    "Ato": d.get('ato_final', 0),
                    "Ato 30": d.get('ato_30', 0),
                    "Ato 60": d.get('ato_60', 0),
                    "Ato 90": d.get('ato_90', 0),
                    "Renda Part. 2": rendas_ind[1],
                    "Nome do Corretor": st.session_state.get('user_name', ''),
                    "Canal/Imobiliária": st.session_state.get('user_imobiliaria', ''),
                    "Data/Horário": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M:%S")
                }
                df_novo = pd.DataFrame([nova_linha])
                try:
                    df_existente = conn_save.read(spreadsheet=URL_RANKING, worksheet=aba_destino)
                    df_final_save = pd.concat([df_existente, df_novo], ignore_index=True)
                except: df_final_save = df_novo
                conn_save.update(spreadsheet=URL_RANKING, worksheet=aba_destino, data=df_final_save)
                st.cache_data.clear()
                st.markdown(f'<div class="custom-alert">Salvo em \'{aba_destino}\'!</div>', unsafe_allow_html=True); time.sleep(2); st.session_state.dados_cliente = {}; st.session_state.passo_simulacao = 'input'; scroll_to_top(); st.rerun()
            except Exception as e: st.error(f"Erro ao salvar: {e}")

        if st.button("Voltar para Fechamento Financeiro", use_container_width=True): st.session_state.passo_simulacao = 'payment_flow'; scroll_to_top(); st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Botão Sair fora da coluna para herdar estilo grande
    if st.button("Sair do Sistema", key="btn_logout_bottom", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

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
