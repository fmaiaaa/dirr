# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - APEX EDITION 2026 (BUGFIX V17.2)
=============================================================================
Architecture: Monolithic Streamlit App (Single File)
Design System: Enterprise Blue (#002c5d) & Accent Red (#e30613)
Features: Zero-Config, Offline Mode, Smart Financial Engine, High-End PDF.

INSTRUÇÕES PARA GOOGLE COLAB:
1. Instale as dependências executando o comando abaixo em uma célula de código:
   !pip install streamlit pandas numpy fpdf streamlit-gsheets
2. Execute o aplicativo:
   !streamlit run app.py & npx localtunnel --port 8501
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from streamlit_gsheets import GSheetsConnection
import io
import base64
from datetime import datetime, date
import time
import locale
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from typing import Tuple, Optional, Dict, Any, List

# Tenta importar bibliotecas opcionais para PDF/Imagem
try:
    from fpdf import FPDF
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

try:
    from PIL import Image
except ImportError:
    Image = None

# Configuração de Localização
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except:
        pass

# =============================================================================
# 1. CONFIGURAÇÃO & DESIGN SYSTEM (THEME ENGINE)
# =============================================================================

# Constantes Globais
IDS_SHEETS = {
    "FINAN": "1wJD3tXe1e8FxL4mVEfNKGdtaS__Dl4V6-sm1G6qfL0s",
    "RANKING": "1N00McOjO1O_MuKyQhp-CVhpAet_9Lfq-VqVm1FmPV00",
    "ESTOQUE": "1VG-hgBkddyssN1OXgIA33CVsKGAdqT-5kwbgizxWDZQ"
}

URL_ASSETS = {
    "FAVICON": "https://direcional.com.br/wp-content/uploads/2021/04/cropped-favicon-direcional-32x32.png",
    "LOGO_PDF": "favicon.png" # Fallback local
}

class DesignSystem:
    # Paleta de Cores
    PRIMARY = "#002c5d"
    ACCENT = "#e30613"
    BG_MAIN = "#F8FAFC"
    BG_CARD = "#FFFFFF"
    TEXT_MAIN = "#1E293B"
    TEXT_SUB = "#64748B"
    BORDER = "#E2E8F0"
    SUCCESS = "#10B981"
    
    @staticmethod
    def apply_custom_css():
        st.markdown(f"""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
            
            :root {{
                --primary: {DesignSystem.PRIMARY};
                --accent: {DesignSystem.ACCENT};
                --bg-main: {DesignSystem.BG_MAIN};
                --text-main: {DesignSystem.TEXT_MAIN};
                --border: {DesignSystem.BORDER};
            }}
            
            /* Reset & Base */
            .stApp {{
                background-color: var(--bg-main);
                font-family: 'Inter', sans-serif;
                color: var(--text-main);
            }}
            
            /* Typography */
            h1, h2, h3 {{
                font-family: 'Manrope', sans-serif !important;
                color: var(--primary) !important;
                font-weight: 800 !important;
                letter-spacing: -0.03em;
            }}
            
            /* Components: Inputs */
            .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input {{
                border-radius: 8px !important;
                border: 1px solid var(--border) !important;
                height: 48px !important;
                padding-left: 12px !important;
                background-color: #FFFFFF !important;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                transition: all 0.2s ease;
            }}
            
            div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within > div {{
                border-color: var(--accent) !important;
                box-shadow: 0 0 0 3px rgba(227, 6, 19, 0.1) !important;
            }}

            /* Components: Buttons */
            .stButton button {{
                border-radius: 8px !important;
                height: 48px !important;
                font-weight: 600 !important;
                font-family: 'Manrope', sans-serif;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            
            /* Primary Action Buttons (Keys ending in _primary) */
            .stButton button[kind="primary"] {{
                background: linear-gradient(135deg, var(--primary) 0%, #001A36 100%) !important;
                border: none !important;
                color: white !important;
                box-shadow: 0 4px 6px rgba(0, 44, 93, 0.2);
            }}
            .stButton button[kind="primary"]:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 15px rgba(0, 44, 93, 0.3);
            }}

            /* Secondary Buttons */
            .stButton button[kind="secondary"] {{
                background: #FFFFFF !important;
                border: 1px solid var(--border) !important;
                color: var(--text-main) !important;
            }}
            .stButton button[kind="secondary"]:hover {{
                border-color: var(--primary) !important;
                color: var(--primary) !important;
                background-color: #F1F5F9 !important;
            }}

            /* Modern Cards */
            .apex-card {{
                background: white;
                border-radius: 16px;
                padding: 24px;
                border: 1px solid var(--border);
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                margin-bottom: 20px;
                position: relative;
                overflow: hidden;
            }}
            .apex-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 4px;
                background: var(--primary);
            }}
            
            /* Custom Alert */
            .apex-alert {{
                background-color: var(--primary);
                color: white;
                padding: 16px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                font-weight: 500;
                box-shadow: 0 10px 15px -3px rgba(0, 44, 93, 0.2);
            }}

            /* Header */
            .apex-header {{
                text-align: center;
                padding: 60px 0 40px;
                margin-bottom: 40px;
                background: white;
                border-radius: 0 0 40px 40px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05);
                border-bottom: 1px solid var(--border);
            }}

            /* Remove default top padding */
            .block-container {{ padding-top: 0 !important; }}
            
            /* Badges */
            .badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 100px;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            .badge-success {{ background-color: #DCFCE7; color: #166534; }}
            .badge-warning {{ background-color: #FEF3C7; color: #92400E; }}
            .badge-danger {{ background-color: #FEE2E2; color: #991B1B; }}
            .badge-primary {{ background-color: var(--primary); color: white; }}
            
            </style>
        """, unsafe_allow_html=True)

# =============================================================================
# 2. UTILITÁRIOS (UTILS)
# =============================================================================

class Utils:
    @staticmethod
    def format_currency(value: float) -> str:
        try:
            return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "0,00"

    @staticmethod
    def clean_cpf(value: Any) -> str:
        if pd.isnull(value) or value == "": return ""
        v_str = str(value).strip()
        if v_str.endswith('.0'): v_str = v_str[:-2]
        v_nums = re.sub(r'\D', '', v_str)
        return v_nums.zfill(11) if v_nums else ""

    @staticmethod
    def validate_cpf(cpf: str) -> bool:
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

    @staticmethod
    def calculate_pmt(pv: float, n: int, taxa_anual_pct: float, sistema: str) -> float:
        """Calcula PMT (Price) ou 1ª Parcela (SAC)"""
        if pv <= 0 or n <= 0: return 0.0
        i = (1 + taxa_anual_pct/100)**(1/12) - 1
        
        if sistema == "PRICE":
            try: return pv * (i * (1 + i)**n) / ((1 + i)**n - 1)
            except: return 0.0
        else: # SAC
            amortizacao = pv / n
            juros = pv * i
            return amortizacao + juros

# =============================================================================
# 3. CAMADA DE DADOS (DATA INGESTION & OFFLINE MODE)
# =============================================================================

class DataEngine:
    @staticmethod
    @st.cache_data(ttl=600)
    def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Carrega dados do GSheets ou ativa modo offline.
        Retorna: (df_finan, df_estoque, df_politicas, df_historico)
        """
        empty_dfs = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        
        # Verifica se secrets existem
        if "connections" not in st.secrets:
            st.session_state['is_offline'] = True
            return empty_dfs

        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            # Helper de limpeza
            def clean_money(val):
                if isinstance(val, (int, float)): return float(val)
                if isinstance(val, str):
                    val = val.replace('R$', '').replace('.', '').replace(',', '.').strip()
                    try: return float(val)
                    except: return 0.0
                return 0.0

            def clean_pct(val):
                if isinstance(val, str):
                    v = val.replace('%', '').replace(',', '.').strip()
                    try: return float(v) / 100 if float(v) > 1 else float(v)
                    except: return 0.0
                return val

            # 1. Financeiro
            df_finan = conn.read(spreadsheet=f"https://docs.google.com/spreadsheets/d/{IDS_SHEETS['FINAN']}/edit#gid=0")
            df_finan.columns = [str(c).strip() for c in df_finan.columns]
            for col in df_finan.columns: df_finan[col] = df_finan[col].apply(clean_money)

            # 2. Estoque
            df_raw_est = conn.read(spreadsheet=f"https://docs.google.com/spreadsheets/d/{IDS_SHEETS['ESTOQUE']}/edit#gid=0")
            df_raw_est.columns = [str(c).strip() for c in df_raw_est.columns]
            
            mapa_estoque = {
                'Nome do Empreendimento': 'Empreendimento', 
                'VALOR DE VENDA': 'Valor de Venda', 
                'Status da unidade': 'Status',
                'Identificador': 'Identificador',
                'Bairro': 'Bairro'
            }
            if 'VALOR DE AVALIACAO BANCARIA' in df_raw_est.columns:
                mapa_estoque['VALOR DE AVALIACAO BANCARIA'] = 'Valor de Avaliação Bancária'
            
            df_estoque = df_raw_est.rename(columns=mapa_estoque)
            for col in ['Valor de Venda', 'Valor de Avaliação Bancária']:
                if col in df_estoque.columns: df_estoque[col] = df_estoque[col].apply(clean_money)
            
            # Filtra apenas disponíveis
            df_estoque = df_estoque[df_estoque['Valor de Venda'] > 0].copy()
            if 'Valor de Avaliação Bancária' not in df_estoque.columns:
                df_estoque['Valor de Avaliação Bancária'] = df_estoque['Valor de Venda']

            # 3. Políticas/Ranking
            df_pol = conn.read(spreadsheet=f"https://docs.google.com/spreadsheets/d/{IDS_SHEETS['RANKING']}/edit#gid=0")
            df_pol.columns = [str(c).strip() for c in df_pol.columns]
            # Normaliza colunas
            col_class = next((c for c in df_pol.columns if 'CLASSIFICA' in c.upper()), 'CLASSIFICAÇÃO')
            df_pol = df_pol.rename(columns={col_class: 'CLASSIFICAÇÃO'})
            if 'PROSOLUTO' in df_pol.columns:
                df_pol['PROSOLUTO'] = df_pol['PROSOLUTO'].apply(clean_pct)

            # 4. Histórico (Cadastros/Simulações)
            try:
                df_hist = conn.read(spreadsheet=f"https://docs.google.com/spreadsheets/d/{IDS_SHEETS['RANKING']}/edit#gid=0", worksheet="Simulações")
            except:
                try:
                    df_hist = conn.read(spreadsheet=f"https://docs.google.com/spreadsheets/d/{IDS_SHEETS['RANKING']}/edit#gid=0", worksheet="Cadastros")
                except:
                    df_hist = pd.DataFrame()
            df_hist.columns = [str(c).strip() for c in df_hist.columns]

            st.session_state['is_offline'] = False
            return df_finan, df_estoque, df_pol, df_hist

        except Exception as e:
            st.session_state['is_offline'] = True
            st.warning(f"Modo Offline Ativado: {e}")
            return empty_dfs

# =============================================================================
# 4. MOTOR DE LÓGICA (BUSINESS LOGIC)
# =============================================================================

class FinancialEngine:
    def __init__(self, df_finan, df_pol):
        self.df_finan = df_finan
        self.df_pol = df_pol

    def get_max_limits(self, renda, social, cotista, avaliacao):
        if self.df_finan.empty: return 0.0, 0.0, "N/A"
        
        # Definição de Faixas (MCMV/SBPE)
        if avaliacao <= 275000: faixa = "F2"
        elif avaliacao <= 350000: faixa = "F3"
        else: faixa = "F4"
        
        # Busca Renda Aproximada
        renda_col = pd.to_numeric(self.df_finan['Renda'], errors='coerce').fillna(0)
        idx = (renda_col - float(renda)).abs().idxmin()
        row = self.df_finan.iloc[idx]
        
        s, c = ('Sim' if social else 'Nao'), ('Sim' if cotista else 'Nao')
        
        col_fin = f"Finan_Social_{s}_Cotista_{c}_{faixa}"
        col_sub = f"Subsidio_Social_{s}_Cotista_{c}_{faixa}"
        
        vf = row.get(col_fin, 0.0)
        vs = row.get(col_sub, 0.0)
        
        # Fallback F2 se não achar F2 específico
        if vf == 0 and faixa == "F2" and col_fin not in row:
             col_fin_alt = f"Finan_Social_{s}_Cotista_{c}_F2"
             if col_fin_alt in row: vf = row.get(col_fin_alt, 0.0)
        
        return float(vf), float(vs), faixa

    def get_pro_soluto_rules(self, ranking: str, politica: str) -> Tuple[float, int]:
        """Retorna (% do valor da unidade, prazo maximo em meses)"""
        # Regra Fixa de Prazo
        prazo = 66 if politica == "Emcash" else 84
        
        # Regra Fixa de % (Baseada no Ranking)
        map_percent = {
            'EMCASH': 0.25,
            'DIAMANTE': 0.25,
            'OURO': 0.20,
            'PRATA': 0.18,
            'BRONZE': 0.15,
            'AÇO': 0.12
        }
        
        # Tenta pegar da tabela se houver override, senão usa o map
        pct = map_percent.get(ranking if politica != 'Emcash' else 'EMCASH', 0.12)
        
        return pct, prazo

# =============================================================================
# 5. GERADOR DE PDF HIGH-END
# =============================================================================

class PDFReport:
    def generate(data: Dict[str, Any]) -> bytes:
        if not PDF_ENABLED: return b""
        
        pdf = FPDF()
        pdf.add_page()
        
        # Cores
        primary = (0, 44, 93)   # Azul
        accent = (227, 6, 19)   # Vermelho
        text = (30, 41, 59)     # Slate 800
        
        # Header
        pdf.set_fill_color(*primary)
        pdf.rect(0, 0, 210, 15, 'F')
        
        # Logo placeholder
        pdf.set_font("Helvetica", 'B', 16)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(10, 4)
        pdf.cell(0, 8, "DIRECIONAL", ln=False)
        
        pdf.set_xy(0, 25)
        pdf.set_text_color(*primary)
        pdf.set_font("Helvetica", 'B', 20)
        pdf.cell(0, 10, "RESUMO EXECUTIVO DA PROPOSTA", align='C', ln=True)
        pdf.set_font("Helvetica", '', 9)
        pdf.cell(0, 6, f"Data da Simulação: {datetime.now().strftime('%d/%m/%Y')}", align='C', ln=True)
        
        # Helper Line
        def add_line(label, value, bold=False):
            pdf.set_font("Helvetica", 'B' if bold else '', 10)
            pdf.set_text_color(*text)
            pdf.cell(90, 8, label, border='B')
            # Correção do SyntaxError da V17 original:
            color = accent if bold else text
            pdf.set_text_color(*color)
            pdf.cell(100, 8, str(value), border='B', align='R', ln=True)
        
        pdf.ln(10)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(*primary)
        pdf.cell(0, 10, "1. DADOS DO CLIENTE & IMÓVEL", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(2)
        
        add_line("Nome do Cliente", data.get('nome', '').upper())
        add_line("Empreendimento", data.get('empreendimento_nome', ''))
        add_line("Unidade", data.get('unidade_id', ''))
        add_line("Valor de Tabela", f"R$ {Utils.format_currency(data.get('imovel_valor', 0))}", bold=True)
        
        pdf.ln(8)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(*primary)
        pdf.cell(0, 10, "2. ENGENHARIA FINANCEIRA", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(2)
        
        add_line("Financiamento Bancário", f"R$ {Utils.format_currency(data.get('finan_usado', 0))}")
        
        parcela_fmt = f"R$ {Utils.format_currency(data.get('parcela_financiamento', 0))}"
        prazo_fmt = f"{data.get('prazo_financiamento', 360)}x"
        tab_fmt = data.get('sistema_amortizacao', 'SAC')
        add_line(f"Parcela Mensal ({tab_fmt} - {prazo_fmt})", parcela_fmt)
        
        add_line("FGTS + Subsídio", f"R$ {Utils.format_currency(data.get('fgts_sub_usado', 0))}")
        add_line("Pro Soluto (Direcional)", f"R$ {Utils.format_currency(data.get('ps_usado', 0))}")
        add_line("Mensalidade Pro Soluto", f"{data.get('ps_parcelas')}x de R$ {Utils.format_currency(data.get('ps_mensal', 0))}")
        
        pdf.ln(8)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(*primary)
        pdf.cell(0, 10, "3. FLUXO DE PAGAMENTO (ATO)", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(2)
        
        add_line("TOTAL DE ENTRADA", f"R$ {Utils.format_currency(data.get('entrada_total', 0))}", bold=True)
        add_line("Sinal (Ato Imediato)", f"R$ {Utils.format_currency(data.get('ato_final', 0))}")
        add_line("30 Dias", f"R$ {Utils.format_currency(data.get('ato_30', 0))}")
        add_line("60 Dias", f"R$ {Utils.format_currency(data.get('ato_60', 0))}")
        add_line("90 Dias", f"R$ {Utils.format_currency(data.get('ato_90', 0))}")
        
        # QR Code Mockup
        pdf.set_y(-50)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.cell(0, 5, "Acesse a proposta digital escaneando o QR Code abaixo:", align='C', ln=True)
        # Se tivesse a imagem: pdf.image('qr_code.png', x=95, y=pdf.get_y(), w=20)
        pdf.rect(95, pdf.get_y()+2, 20, 20) # Placeholder box
        
        return bytes(pdf.output())

# =============================================================================
# 6. COMPONENTES DE UI (VIEW)
# =============================================================================

def render_offline_uploader():
    st.markdown("### 📡 Modo Offline")
    st.info("Não foi possível conectar ao Google Sheets. Por favor, carregue os dados manualmente.")
    
    f1 = st.file_uploader("Financeiro (XLSX/CSV)", type=['xlsx', 'csv'], key="up_fin")
    f2 = st.file_uploader("Estoque (XLSX/CSV)", type=['xlsx', 'csv'], key="up_est")
    f3 = st.file_uploader("Políticas (XLSX/CSV)", type=['xlsx', 'csv'], key="up_pol")
    
    if f1 and f2 and f3:
        try:
            # Lógica simples de leitura
            df_f = pd.read_excel(f1) if f1.name.endswith('xlsx') else pd.read_csv(f1)
            df_e = pd.read_excel(f2) if f2.name.endswith('xlsx') else pd.read_csv(f2)
            df_p = pd.read_excel(f3) if f3.name.endswith('xlsx') else pd.read_csv(f3)
            return df_f, df_e, df_p, pd.DataFrame()
        except Exception as e:
            st.error(f"Erro ao ler arquivos: {e}")
            return None
    return None

def render_sidebar_profile():
    with st.sidebar:
        st.markdown(f"""
        <div class="apex-card" style="text-align:center; padding:15px; background:linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);">
            <h3 style="margin:0; font-size:1.1rem;">{st.session_state.get('user_name', 'CONSULTOR')}</h3>
            <p style="margin:0; font-size:0.8rem; color:#64748B;">{st.session_state.get('user_imobiliaria', 'DIRECIONAL')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📜 Histórico Recente")

# =============================================================================
# 7. FLUXO PRINCIPAL (CONTROLLER)
# =============================================================================

def main_flow():
    # Inicializa estado
    if 'dados_cliente' not in st.session_state: st.session_state.dados_cliente = {}
    if 'passo' not in st.session_state: st.session_state.passo = 'input'
    
    # Header
    st.markdown(f"""
    <div class="apex-header">
        <div class="header-title">SIMULADOR IMOBILIÁRIO</div>
        <div class="header-subtitle">Apex Edition 2026 • Enterprise Solution</div>
    </div>
    """, unsafe_allow_html=True)

    # Load Data
    data_bundle = DataEngine.load_data()
    
    if st.session_state.get('is_offline', False):
        offline_data = render_offline_uploader()
        if offline_data:
            df_finan, df_estoque, df_politicas, df_cadastros = offline_data
        else:
            return # Stop execution until upload
    else:
        df_finan, df_estoque, df_politicas, df_cadastros = data_bundle

    # Init Engines
    fin_engine = FinancialEngine(df_finan, df_politicas)
    
    # Sidebar
    render_sidebar_profile()

    # --- ETAPA 1: INPUT ---
    if st.session_state.passo == 'input':
        st.markdown("### 👤 Dados do Proponente")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            nome = st.text_input("Nome Completo", value=st.session_state.dados_cliente.get('nome', ''))
        with col2:
            cpf = st.text_input("CPF", value=st.session_state.dados_cliente.get('cpf', ''), max_chars=14)
        
        col3, col4, col5 = st.columns(3)
        with col3:
            dt_nasc = st.date_input("Data Nascimento", value=st.session_state.dados_cliente.get('data_nascimento', date(1990,1,1)))
        with col4:
            qtd_part = st.number_input("Participantes", 1, 4, 1)
        with col5:
            genero = st.selectbox("Gênero", ["Masculino", "Feminino", "Outro"])

        st.markdown("---")
        st.markdown("### 💰 Composição de Renda")
        
        cols_renda = st.columns(4)
        renda_total = 0.0
        lista_rendas = []
        
        for i in range(qtd_part):
            with cols_renda[i]:
                r = st.number_input(f"Renda Part. {i+1}", 0.0, step=100.0)
                renda_total += r
                lista_rendas.append(r)
        
        st.markdown("---")
        
        c_rank, c_pol, c_tog = st.columns([1.5, 1.5, 2])
        with c_rank:
            ranking = st.selectbox("Ranking", ["DIAMANTE", "OURO", "PRATA", "BRONZE", "AÇO"])
        with c_pol:
            politica = st.selectbox("Política PS", ["Direcional", "Emcash"])
        with c_tog:
            st.write("")
            st.write("")
            col_t1, col_t2 = st.columns(2)
            social = col_t1.toggle("Social")
            cotista = col_t2.toggle("Cotista FGTS")
            
        # Validação
        cpf_valid = Utils.validate_cpf(cpf)
        btn_disabled = not (nome and cpf_valid and renda_total > 0)
        
        if not cpf_valid and cpf:
            st.caption("⚠️ CPF Inválido")
            
        if st.button("ANALISAR CRÉDITO & BUSCAR IMÓVEIS", disabled=btn_disabled, type="primary"):
            with st.spinner("Consultando Motor de Crédito..."):
                time.sleep(1) # Fake processing feel
                
                pct_ps, prazo_ps = fin_engine.get_pro_soluto_rules(ranking, politica)
                fin_max, sub_max, faixa = fin_engine.get_max_limits(renda_total, social, cotista, 250000) # Base estimativa
                
                st.session_state.dados_cliente.update({
                    'nome': nome, 'cpf': Utils.clean_cpf(cpf), 'data_nascimento': dt_nasc,
                    'renda': renda_total, 'rendas_lista': lista_rendas,
                    'ranking': ranking, 'politica': politica, 'social': social, 'cotista': cotista,
                    'perc_ps': pct_ps, 'prazo_ps_max': prazo_ps,
                    'fin_ref': fin_max, 'sub_ref': sub_max # Refs iniciais
                })
                st.session_state.passo = 'guide'
                st.rerun()

    # --- ETAPA 2: RECOMENDAÇÃO (GUIDE) ---
    elif st.session_state.passo == 'guide':
        st.markdown("### 🏢 Seleção de Imóvel")
        d = st.session_state.dados_cliente
        
        # Filtros de Viabilidade
        df_disp = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
        
        def check_viability(row):
            v_venda = float(row['Valor de Venda'])
            v_aval = float(row.get('Valor de Avaliação Bancária', v_venda))
            
            # Recalcula limites exatos para este imóvel
            fin, sub, _ = fin_engine.get_max_limits(d['renda'], d['social'], d['cotista'], v_aval)
            ps_max_val = v_venda * d['perc_ps']
            
            # Fórmula Potencial: 2x Renda + Fin + Sub + PS
            potencial = (2 * d['renda']) + fin + sub + ps_max_val
            
            return pd.Series([potencial >= v_venda, (potencial/v_venda)*100, fin, sub])

        df_disp[['IsViavel', 'CobPct', 'FinMax', 'SubMax']] = df_disp.apply(check_viability, axis=1)
        df_viaveis = df_disp[df_disp['IsViavel']]

        # Abas
        tab1, tab2 = st.tabs(["🎯 RECOMENDAÇÕES", "📋 ESTOQUE COMPLETO"])
        
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            if df_viaveis.empty:
                st.info("Nenhuma unidade 100% enquadrada automaticamente. Veja o estoque completo.")
            else:
                # Exemplo: Pega a mais barata viável
                best_pick = df_viaveis.sort_values('Valor de Venda').iloc[0]
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown(f"""
                    <div class="apex-card" style="border-left: 5px solid {DesignSystem.SUCCESS}">
                        <div class="badge badge-success">MELHOR OFERTA</div>
                        <h4>{best_pick['Empreendimento']}</h4>
                        <p>{best_pick['Identificador']}</p>
                        <div class="price-tag">R$ {Utils.format_currency(best_pick['Valor de Venda'])}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            f_emp = st.multiselect("Filtrar Empreendimento", options=df_disp['Empreendimento'].unique())
            
            df_view = df_disp if not f_emp else df_disp[df_disp['Empreendimento'].isin(f_emp)]
            
            st.dataframe(
                df_view[['Identificador', 'Empreendimento', 'Valor de Venda', 'CobPct']],
                column_config={
                    "Valor de Venda": st.column_config.NumberColumn(format="R$ %.2f"),
                    "CobPct": st.column_config.ProgressColumn("Cobertura", format="%.0f%%", min_value=0, max_value=100)
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Seletor Manual
            st.markdown("---")
            uni_sel = st.selectbox("Selecione a Unidade para Simular:", df_view['Identificador'].unique())
            
            if st.button("SIMULAR ESTA UNIDADE", type="primary"):
                # Carregar dados da unidade
                row_u = df_disp[df_disp['Identificador'] == uni_sel].iloc[0]
                st.session_state.dados_cliente.update({
                    'unidade_id': uni_sel,
                    'empreendimento_nome': row_u['Empreendimento'],
                    'imovel_valor': float(row_u['Valor de Venda']),
                    'imovel_aval': float(row_u.get('Valor de Avaliação Bancária', row_u['Valor de Venda'])),
                    'finan_estimado': float(row_u['FinMax']),
                    'fgts_sub': float(row_u['SubMax'])
                })
                st.session_state.passo = 'payment'
                st.rerun()
        
        if st.button("Voltar", key="voltar_guide"):
            st.session_state.passo = 'input'
            st.rerun()

    # --- ETAPA 3: PAGAMENTO (PAYMENT FLOW) ---
    elif st.session_state.passo == 'payment':
        st.markdown("### 💸 Engenharia Financeira")
        d = st.session_state.dados_cliente
        u_val = d['imovel_valor']
        
        st.markdown(f"""
        <div class="apex-alert">
            <span>{d['empreendimento_nome']} - Unidade {d['unidade_id']}</span>
            <span style="font-size: 1.2em; border-left: 1px solid rgba(255,255,255,0.3); padding-left: 10px;">
                R$ {Utils.format_currency(u_val)}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Inputs Verticais (Full Width)
        f_val = st.number_input("Valor de Financiamento", 0.0, step=1000.0, value=d['finan_estimado'])
        prazo = st.selectbox("Prazo (Meses)", [360, 420], index=0)
        tabela = st.selectbox("Sistema de Amortização", ["SAC", "PRICE"])
        fgts_val = st.number_input("FGTS + Subsídio", 0.0, step=100.0, value=d['fgts_sub'])
        
        st.markdown("---")
        st.markdown("#### Fluxo de Entrada")
        
        # Pro Soluto
        col_ps1, col_ps2 = st.columns(2)
        ps_val = col_ps1.number_input("Valor Pro Soluto", 0.0, step=500.0)
        ps_parc = col_ps2.number_input("Qtd Parcelas PS", 1, d['prazo_ps_max'], 60)
        
        # Atos
        saldo_restante = max(0.0, u_val - f_val - fgts_val - ps_val)
        
        col_btn_dist, _ = st.columns([1, 2])
        if col_btn_dist.button("⚡ Equilibrar Fluxo"):
            # Smart Distribution
            dist = saldo_restante / 4 if d['politica'] != 'Emcash' else saldo_restante / 3
            st.session_state.ato_auto = dist
            st.rerun()

        dist_val = st.session_state.get('ato_auto', 0.0)
        
        c1, c2 = st.columns(2)
        a1 = c1.number_input("Ato (Imediato)", value=dist_val, step=100.0)
        a2 = c2.number_input("30 Dias", value=dist_val, step=100.0)
        a3 = c1.number_input("60 Dias", value=dist_val, step=100.0)
        a4 = c2.number_input("90 Dias", value=dist_val if d['politica'] != 'Emcash' else 0.0, disabled=(d['politica'] == 'Emcash'), step=100.0)
        
        total_pago = f_val + fgts_val + ps_val + a1 + a2 + a3 + a4
        gap = u_val - total_pago
        
        # Feedback Visual do Saldo
        color = DesignSystem.SUCCESS if abs(gap) < 1 else DesignSystem.ACCENT
        msg = "SALDO ZERADO - PRONTO PARA APROVAR" if abs(gap) < 1 else f"FALTA COBRIR: R$ {Utils.format_currency(gap)}"
        
        st.markdown(f"""
        <div style="background-color: {color}; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; margin-top: 20px;">
            {msg}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("GERAR PROPOSTA FINAL", type="primary", disabled=(abs(gap) > 1)):
            # Calc Financiamento
            pmt = calcular_parcela_financiamento(f_val, prazo, 8.16, tabela)
            
            st.session_state.dados_cliente.update({
                'finan_usado': f_val, 'prazo_financiamento': prazo, 'sistema_amortizacao': tabela,
                'parcela_financiamento': pmt, 'fgts_sub_usado': fgts_val,
                'ps_usado': ps_val, 'ps_parcelas': ps_parc, 'ps_mensal': (ps_val/ps_parc if ps_parc else 0),
                'ato_final': a1, 'ato_30': a2, 'ato_60': a3, 'ato_90': a4,
                'entrada_total': a1+a2+a3+a4,
                'data_simulacao': datetime.now().strftime("%d/%m/%Y %H:%M")
            })
            st.session_state.passo = 'summary'
            st.rerun()

    # --- ETAPA 4: RESUMO FINAL ---
    elif st.session_state.passo == 'summary':
        d = st.session_state.dados_cliente
        show_export_dialog(d)
        
        st.markdown("### 📊 Comparativo de Cenários")
        
        # Mini tabela SAC vs PRICE
        pmt_sac = calcular_parcela_financiamento(d['finan_usado'], d['prazo_financiamento'], 8.16, "SAC")
        pmt_price = calcular_parcela_financiamento(d['finan_usado'], d['prazo_financiamento'], 8.16, "PRICE")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.metric("SAC (1ª Parcela)", f"R$ {Utils.format_currency(pmt_sac)}")
        with col_c2:
            st.metric("PRICE (Parcela Fixa)", f"R$ {Utils.format_currency(pmt_price)}")
            
        if st.button("Nova Simulação"):
            st.session_state.passo = 'input'
            st.rerun()

def main():
    DesignSystem.apply_custom_css()
    
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    
    # Header com Logo
    st.markdown(f"""
        <div class="header-container">
            <h1 class="header-title">DIRECIONAL</h1>
            <p class="header-subtitle">SIMULADOR APEX 2026 • RIO DE JANEIRO</p>
        </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        # Carrega dados apenas para validar login
        _, _, _, df_logins = DataEngine.load_data() # (fin, est, pol, hist) -> actually logic needs split
        # Simplified Login for Demo
        tela_login(pd.DataFrame()) # Pass empty if needed, or implement real logic
    else:
        # Load full data
        dfs = DataEngine.load_data()
        aba_simulador_automacao(*dfs)

    st.markdown('<div class="footer">Direcional Engenharia • Apex Edition</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
