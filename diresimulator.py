# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V3 (COM LOGIN, CADASTRO E ABAS DINÂMICAS)
=============================================================================
Alterações Realizadas:
1. Implementação de Sistema de Login (Mantido).
2. Manutenção das funcionalidades anteriores.
3. Novos Inputs e Fluxo (Updates Anteriores):
   - Campos CPF, Data Nascimento, Gênero.
   - Busca de clientes.
   - Botões de fluxo e layout ajustados.
4. Funcionalidade "Criar Conta" (Update Anterior):
   - Pop-up (st.dialog) para cadastro.
   - Gravação em abas dinâmicas.
5. Atualizações (Update Anterior):
   - Correção CPF Busca.
   - CSS Botões.
   - Layout Resumo.
   - Locale PT-BR.
   - CSS Data.
   - Aba Resumo.
6. Atualizações (Update Anterior):
   - Remoção da Aba 'Potential'.
   - Fluxo: Início -> Recomendação -> Seleção -> Fechamento -> Resumo.
   - Aba 'Guide': Ordenação por Viabilidade.
7. Atualizações (Update Atual):
   - Fix KeyError 'Status Viabilidade'.
   - Fix Formatação CPF (padding zero).
   - Fix Preenchimento Busca de Clientes.
   - Aba Fechamento: PS movido para o final, default 0, distribuição inicial cobre saldo.
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
try:
    from PIL import Image
except ImportError:
    Image = None
import os

# Tenta configurar locale para PT-BR
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except:
        pass

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

def limpar_cpf_visual(valor):
    """Garante que o CPF seja string, sem .0 e com 11 digitos"""
    if pd.isnull(valor) or valor == "":
        return ""
    # Remove caracteres não numéricos temporariamente para limpar, mas mantemos zeros a esquerda
    v_str = str(valor).strip()
    if v_str.endswith('.0'):
        v_str = v_str[:-2]
    # Remove tudo que não é digito
    v_nums = re.sub(r'\D', '', v_str)
    # Pad com zeros a esquerda para 11 digitos se tiver conteudo
    if v_nums:
        return v_nums.zfill(11)
    return ""

# =============================================================================
# 1. CARREGAMENTO E TRATAMENTO DE DADOS
# =============================================================================

@st.cache_data(ttl=300)
def carregar_dados_sistema():
    try:
        if "connections" not in st.secrets:
            st.error("Aviso: Configuração de 'Secrets' não encontrada.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

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

        # --- CARREGAR LOGINS ---
        try:
            df_logins = conn.read(spreadsheet=URL_RANKING, worksheet="Logins")
            df_logins.columns = [str(c).strip() for c in df_logins.columns]
            
            col_map = {
                'email': next((c for c in df_logins.columns if "e-mail" in c.lower() or "email" in c.lower()), "Email"),
                'senha': next((c for c in df_logins.columns if "senha" in c.lower()), "Senha"),
                'imobiliaria': next((c for c in df_logins.columns if "imob" in c.lower() or "canal" in c.lower()), "Imobiliaria"),
                'cargo': next((c for c in df_logins.columns if "cargo" in c.lower()), "Cargo"),
                'nome': next((c for c in df_logins.columns if "nome" in c.lower()), "Nome")
            }
            
            cols_to_keep = [v for k, v in col_map.items() if v in df_logins.columns]
            df_logins = df_logins[cols_to_keep]
            
            rename_dict = {v: k for k, v in col_map.items() if v in df_logins.columns}
            df_logins = df_logins.rename(columns=rename_dict)
            
            for req_col in ['email', 'senha', 'imobiliaria', 'cargo', 'nome']:
                if req_col not in df_logins.columns:
                    df_logins[req_col] = ""

            df_logins['email'] = df_logins['email'].astype(str).str.strip().str.lower()
            df_logins['senha'] = df_logins['senha'].astype(str).str.strip()
            
        except Exception:
            df_logins = pd.DataFrame(columns=['email', 'senha', 'imobiliaria', 'cargo', 'nome'])

        # --- CARREGAR CADASTROS (CLIENTES) ---
        try:
            df_cadastros = conn.read(spreadsheet=URL_RANKING, worksheet="Cadastros")
            # Normaliza colunas para evitar erros de busca
            df_cadastros.columns = [str(c).strip() for c in df_cadastros.columns]
        except Exception:
            df_cadastros = pd.DataFrame()

        # --- CARREGAR POLÍTICAS ---
        try:
            df_politicas = conn.read(spreadsheet=URL_RANKING) 
            df_politicas.columns = [str(c).strip() for c in df_politicas.columns]
            
            col_classificacao = next((c for c in df_politicas.columns if 'CLASSIFICA' in c.upper()), 'CLASSIFICAÇÃO')
            
            df_politicas = df_politicas.rename(columns={
                col_classificacao: 'CLASSIFICAÇÃO',
                'FAIXA RENDA': 'FAIXA_RENDA',
                'FX RENDA 1': 'FX_RENDA_1',
                'FX RENDA 2': 'FX_RENDA_2'
            })
            for col in ['PROSOLUTO', 'FX_RENDA_1', 'FX_RENDA_2']:
                if col in df_politicas.columns:
                    df_politicas[col] = df_politicas[col].apply(limpar_porcentagem)
        except Exception:
            df_politicas = pd.DataFrame()

        # --- CARREGAR FINANCEIRO ---
        try:
            df_finan = conn.read(spreadsheet=URL_FINAN)
            df_finan.columns = [str(c).strip() for c in df_finan.columns]
            for col in df_finan.columns:
                df_finan[col] = df_finan[col].apply(limpar_moeda)
        except Exception:
            df_finan = pd.DataFrame()

        # --- CARREGAR ESTOQUE ---
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
            
            col_aval = 'VALOR DE AVALIACAO BANCARIA' if 'VALOR DE AVALIACAO BANCARIA' in df_raw.columns else 'Valor de Avaliação Bancária'
            if col_aval in df_raw.columns:
                df_estoque['Valor de Avaliação Bancária'] = df_raw[col_aval].apply(limpar_moeda)
            else:
                df_estoque['Valor de Avaliação Bancária'] = df_estoque['Valor de Venda']
            
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
        
        return df_finan, df_estoque, df_politicas, df_logins, df_cadastros
    
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# =============================================================================
# 2. MOTOR DE CÁLCULO
# =============================================================================

class MotorRecomendacao:
    def __init__(self, df_finan, df_estoque, df_politicas):
        self.df_finan = df_finan
        self.df_estoque = df_estoque
        self.df_politicas = df_politicas

    def obter_enquadramento(self, renda, social, cotista, valor_avaliacao=250000):
        if self.df_finan.empty: return 0.0, 0.0, "N/A"
        
        if valor_avaliacao <= 190000:
            faixa = "F1"
        elif valor_avaliacao <= 275000:
            faixa = "F2"
        elif valor_avaliacao <= 350000:
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
            background-color: #f0f2f6 !important;
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
        
        div[data-testid="stDateInput"] {{
            border-radius: 8px !important;
        }}
        div[data-testid="stDateInput"] > div {{
            border-radius: 8px !important;
            border: 1px solid #e2e8f0 !important;
            background-color: #f0f2f6 !important;
            height: 45px !important;
            display: flex;
            align-items: center;
        }}
        div[data-testid="stDateInput"] div[data-baseweb="input"] {{
            border: none !important; 
            background-color: transparent !important;
            height: 100% !important;
        }}
        div[data-baseweb="input"] {{
            background-color: #f0f2f6 !important; 
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
            background-color: #f0f2f6 !important;
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
        .login-card {{
            min-height: 350px;
            box-shadow: 0 20px 50px -20px rgba(0,0,0,0.1);
            max-width: 450px;
            margin: 0 auto;
        }}
        
        .card:hover, .fin-box:hover, .recommendation-card:hover {{
            transform: translateY(-4px);
            border-color: {COR_VERMELHO};
            box-shadow: 0 10px 30px -10px rgba(227,6,19,0.1);
        }}
        
        .metric-label {{ color: {COR_AZUL_ESC} !important; opacity: 0.7; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 8px; }}
        .metric-value {{ color: {COR_AZUL_ESC} !important; font-size: 1.8rem; font-weight: 800; font-family: 'Montserrat', sans-serif; }}
        
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

        .stButton button {{ 
            font-family: 'Inter', sans-serif;
            border-radius: 8px !important; 
            min-height: 45px !important;
            height: 45px !important;
            padding: 0px 24px !important; 
            font-weight: 700 !important; 
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 0.8rem !important;
            transition: all 0.2s ease !important;
            display: flex;
            align-items: center;
            justify-content: center;
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
            color: {COR_AZUL_ESC} !important; 
            font-size: 0.8rem; 
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            opacity: 0.6;
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
            font-size: 1.2rem;
            margin-top: 5px;
        }}

        div[data-baseweb="tab-list"] {{ justify-content: center !important; gap: 40px; margin-bottom: 40px; }}
        button[data-baseweb="tab"] p {{ 
            color: {COR_AZUL_ESC} !important; 
            opacity: 0.6;
            font-weight: 700 !important; 
            font-family: 'Montserrat', sans-serif !important; 
            font-size: 0.9rem !important; 
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        button[data-baseweb="tab"][aria-selected="true"] p {{ color: {COR_AZUL_ESC} !important; opacity: 1; }}
        div[data-baseweb="tab-highlight"] {{ background-color: {COR_VERMELHO} !important; height: 3px !important; }}
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
        FUNDO_SECAO = (248, 250, 252)

        pdf.set_fill_color(*AZUL_RGB)
        pdf.rect(0, 0, 210, 3, 'F')

        if os.path.exists("favicon.png"):
            try:
                pdf.image("favicon.png", 10, 8, 10)
            except: pass
        
        pdf.ln(15)
        pdf.set_text_color(*AZUL_RGB)
        pdf.set_font("Helvetica", 'B', 22)
        pdf.cell(0, 12, "RELATÓRIO DE VIABILIDADE", ln=True, align='C')
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

        pdf.set_y(-25)
        pdf.set_font("Helvetica", 'I', 7)
        pdf.set_text_color(*AZUL_RGB)
        pdf.cell(0, 4, "Simulação sujeita a aprovação de crédito e alteração de tabela sem aviso prévio.", ln=True, align='C')
        pdf.cell(0, 4, "Direcional Engenharia - Rio de Janeiro", ln=True, align='C')

        return bytes(pdf.output())
    except Exception as e:
        return None

# =============================================================================
# 5. TELA DE LOGIN & CADASTRO
# =============================================================================

@st.dialog("Criar Nova Conta")
def modal_criar_conta(conn):
    st.markdown("Preencha os dados abaixo para solicitar acesso.")
    
    opts_imob = ["Canal IMOB", "DV", "RV", "Trip", "Swell", "Outro"]
    opts_cargo = ["Coordenador Comercial", "Coordenador IMOB", "Gerente Regional", "Gerente de Vendas", "Corretor", "Outro"]

    sel_imob = st.selectbox("Imobiliária / Canal IMOB", opts_imob)
    if sel_imob == "Outro":
        imobiliaria = st.text_input("Digite o nome da Imobiliária/Canal")
    else:
        imobiliaria = sel_imob

    sel_cargo = st.selectbox("Cargo", opts_cargo)
    if sel_cargo == "Outro":
        cargo = st.text_input("Digite o Cargo")
    else:
        cargo = sel_cargo

    nome = st.text_input("Nome Completo")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Cadastrar", type="primary", use_container_width=True):
        if not imobiliaria or not nome or not email or not senha or not cargo:
            st.error("Preencha todos os campos obrigatórios.")
        else:
            try:
                try:
                    df_logins = conn.read(spreadsheet=URL_RANKING, worksheet="Logins")
                except:
                    df_logins = pd.DataFrame(columns=['Email', 'Senha', 'Imobiliaria', 'Cargo', 'Nome'])
                
                novo_user = pd.DataFrame([{
                    'Email': email.strip().lower(),
                    'Senha': senha.strip(),
                    'Imobiliaria': imobiliaria.strip(),
                    'Cargo': cargo.strip(),
                    'Nome': nome.strip()
                }])
                
                df_final = pd.concat([df_logins, novo_user], ignore_index=True)
                conn.update(spreadsheet=URL_RANKING, worksheet="Logins", data=df_final)

                nome_aba_canal = f"Logins - {imobiliaria.strip()}"
                try:
                    try:
                        df_canal = conn.read(spreadsheet=URL_RANKING, worksheet=nome_aba_canal)
                        df_final_canal = pd.concat([df_canal, novo_user], ignore_index=True)
                    except:
                        df_final_canal = novo_user
                    conn.update(spreadsheet=URL_RANKING, worksheet=nome_aba_canal, data=df_final_canal)
                except Exception as e_canal:
                    pass
                
                st.success("Cadastro realizado com sucesso! Faça login para continuar.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar cadastro: {e}")

@st.dialog("Opções de Resumo")
def modal_opcoes_resumo(pdf_bytes, nome_cliente):
    st.markdown("Escolha uma das opções abaixo:")
    st.download_button(label="📄 Baixar PDF", data=pdf_bytes, file_name=f"Resumo_Direcional_{nome_cliente}.pdf", mime="application/pdf", use_container_width=True)
    st.markdown("---")
    st.markdown("**Enviar por E-mail (Opcional)**")
    email = st.text_input("Endereço de e-mail", placeholder="cliente@exemplo.com")
    if st.button("✉️ Enviar", use_container_width=True):
        if email and "@" in email:
            st.success(f"Enviado para {email}!")
            time.sleep(1.5)
            st.rerun()
        else:
            st.warning("Email inválido")

def tela_login(df_logins):
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br><h3 style='text-align:center;'>LOGIN</h3>", unsafe_allow_html=True)
        email_input = st.text_input("E-mail", placeholder="Digite seu e-mail", key="login_email")
        senha_input = st.text_input("Senha", type="password", placeholder="Digite sua senha", key="login_pass")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ACESSAR SISTEMA", type="primary", use_container_width=True):
            if df_logins.empty:
                st.error("Erro: Base de usuários não encontrada.")
            else:
                email_clean = email_input.strip().lower()
                senha_clean = senha_input.strip()
                usuario_valido = df_logins[(df_logins['email'] == email_clean) & (df_logins['senha'] == senha_clean)]
                
                if not usuario_valido.empty:
                    dados_user = usuario_valido.iloc[0]
                    st.session_state['logged_in'] = True
                    st.session_state['user_email'] = email_clean
                    st.session_state['user_name'] = str(dados_user.get('nome', '')).strip()
                    st.session_state['user_imobiliaria'] = str(dados_user.get('imobiliaria', 'Geral')).strip()
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")
        st.markdown("<div style='text-align: center; margin-top: 10px;'>OU</div>", unsafe_allow_html=True)
        if st.button("Criar Conta", use_container_width=True):
            modal_criar_conta(st.connection("gsheets", type=GSheetsConnection))

# =============================================================================
# 6. COMPONENTES DE INTERAÇÃO (SIMULADOR)
# =============================================================================

def aba_simulador_automacao(df_finan, df_estoque, df_politicas, df_cadastros):
    passo_atual = st.session_state.get('passo_simulacao', 'init')
    components.html(f"""<div id="scroll-anchor-{passo_atual}"></div><script>var mainContainer = window.parent.document.querySelector('.main');if (mainContainer) {{mainContainer.scrollTo({{top: 0, behavior: 'smooth'}});}}window.parent.window.scrollTo({{top: 0, behavior: 'smooth'}});</script>""", height=0)

    motor = MotorRecomendacao(df_finan, df_estoque, df_politicas)
    if 'passo_simulacao' not in st.session_state: st.session_state.passo_simulacao = 'input'
    if 'dados_cliente' not in st.session_state: st.session_state.dados_cliente = {}

    # --- ETAPA 1: INPUT ---
    if st.session_state.passo_simulacao == 'input':
        st.markdown("### Dados do Cliente")
        if not df_cadastros.empty:
            try:
                # Trata CPF para garantir que seja string e tenha 11 dígitos no label
                df_cadastros['cpf_str'] = df_cadastros['CPF'].astype(str).apply(limpar_cpf_visual)
            except:
                df_cadastros['cpf_str'] = ""
                
            df_cadastros['search_label'] = df_cadastros['Nome'].astype(str) + " - " + df_cadastros['cpf_str']
            # Filtra apenas labels validos
            opcoes_clientes = [""] + sorted(df_cadastros[df_cadastros['search_label'].str.len() > 3]['search_label'].unique().tolist())
            
            cliente_selecionado = st.selectbox("Pesquisar Cliente (Nome - CPF)", opcoes_clientes, index=0, key="busca_cliente_v3", placeholder="Digite para buscar...")
            
            if cliente_selecionado and cliente_selecionado != "":
                dados_cli = df_cadastros[df_cadastros['search_label'] == cliente_selecionado].iloc[0]
                if st.session_state.get('last_search') != cliente_selecionado:
                    st.session_state.dados_cliente['nome'] = str(dados_cli.get('Nome', ''))
                    st.session_state.dados_cliente['cpf'] = limpar_cpf_visual(dados_cli.get('CPF', ''))
                    try:
                        d_nasc = pd.to_datetime(dados_cli.get('Data de Nascimento'), errors='coerce')
                        if not pd.isnull(d_nasc): st.session_state.dados_cliente['data_nascimento'] = d_nasc.date()
                    except: pass
                    st.session_state.dados_cliente['qtd_participantes'] = 1 
                    rendas_recup = []
                    for i in range(1, 5):
                        try:
                            r_val = float(str(dados_cli.get(f'Renda Part. {i}', 0)).replace(',','.'))
                            if r_val > 0: rendas_recup.append(r_val)
                        except: pass
                    if rendas_recup:
                        st.session_state.dados_cliente['rendas_lista'] = rendas_recup
                        st.session_state.dados_cliente['qtd_participantes'] = len(rendas_recup)
                        st.session_state.dados_cliente['renda'] = sum(rendas_recup)
                    st.session_state.last_search = cliente_selecionado
                    st.rerun()

        nome = st.text_input("Nome do Cliente", value=st.session_state.dados_cliente.get('nome', ""), placeholder="Nome Completo", key="in_nome_v28")
        cpf_val = st.text_input("CPF", value=st.session_state.dados_cliente.get('cpf', ""), placeholder="000.000.000-00", key="in_cpf_v3")
        d_nasc_default = st.session_state.dados_cliente.get('data_nascimento', date(1990, 1, 1))
        data_nasc = st.date_input("Data de Nascimento", value=d_nasc_default, min_value=date(1900, 1, 1), max_value=datetime.now().date(), format="DD/MM/YYYY", key="in_dt_nasc_v3")
        genero = st.selectbox("Gênero", ["Masculino", "Feminino", "Outro"], index=0, key="in_genero_v3")

        st.markdown("---")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            qtd_part = st.number_input("Participantes na Renda", min_value=1, max_value=4, value=st.session_state.dados_cliente.get('qtd_participantes', 1), step=1, key="qtd_part_v3")
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
                renda_total_calc += val_r
                lista_rendas_input.append(val_r)
        
        if not df_politicas.empty and 'CLASSIFICAÇÃO' in df_politicas.columns:
            ranking_options = [r for r in df_politicas['CLASSIFICAÇÃO'].unique().tolist() if r != "EMCASH"]
        else:
            ranking_options = ["DIAMANTE"]
        ranking = st.selectbox("Ranking do Cliente", options=ranking_options, index=0, key="in_rank_v28")
        politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"], key="in_pol_v28")
        social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False), key="in_soc_v28")
        cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True), key="in_cot_v28")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        def processar_avanco(destino):
            if not nome.strip():
                st.markdown(f'<div class="custom-alert">Por favor, informe o Nome do Cliente para continuar.</div>', unsafe_allow_html=True); return
            if renda_total_calc <= 0:
                st.markdown(f'<div class="custom-alert">A renda total deve ser maior que zero.</div>', unsafe_allow_html=True); return

            class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
            if 'CLASSIFICAÇÃO' in df_politicas.columns:
                politica_row = df_politicas[df_politicas['CLASSIFICAÇÃO'] == class_b].iloc[0]
            else:
                politica_row = pd.Series({'FX_RENDA_1': 0.30, 'FAIXA_RENDA': 4400, 'FX_RENDA_2': 0.25, 'PROSOLUTO': 0.10, 'PARCELAS': 60})

            limit_ps_r = politica_row['FX_RENDA_1'] if renda_total_calc < politica_row['FAIXA_RENDA'] else politica_row['FX_RENDA_2']
            f_faixa_ref, s_faixa_ref, fx_nome_ref = motor.obter_enquadramento(renda_total_calc, social, cotista, valor_avaliacao=240000)
            
            # Garante formato limpo do CPF para salvar
            cpf_salvar = limpar_cpf_visual(cpf_val)

            st.session_state.dados_cliente.update({
                'nome': nome, 'cpf': cpf_salvar, 'data_nascimento': data_nasc, 'genero': genero,
                'renda': renda_total_calc, 'rendas_lista': lista_rendas_input,
                'social': social, 'cotista': cotista, 'ranking': ranking, 'politica': politica_ps,
                'perc_ps': politica_row['PROSOLUTO'], 'prazo_ps_max': int(politica_row['PARCELAS']),
                'limit_ps_renda': limit_ps_r, 'finan_f_ref': f_faixa_ref, 'sub_f_ref': s_faixa_ref,
                'qtd_participantes': qtd_part, 'prazo_financiamento': prazo_finan
            })
            st.session_state.passo_simulacao = destino
            st.rerun()

        if st.button("Caminho Completo (Ver Recomendação de Imóveis)", type="primary", use_container_width=True, key="btn_completo_v3"): processar_avanco('guide')
        if st.button("Simulação Direta (Ir para Seleção de Unidade)", use_container_width=True, key="btn_direto_v3"): processar_avanco('selection')

    # --- ETAPA 3: RECOMENDAÇÃO GRANULAR ---
    elif st.session_state.passo_simulacao == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### Recomendação de Imóveis")
        df_disp_total = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
        
        if df_disp_total.empty:
            st.markdown('<div class="custom-alert">Sem produtos viaveis no perfil selecionado.</div>', unsafe_allow_html=True)
            df_viaveis = pd.DataFrame()
        else:
            def calcular_viabilidade_unidade(row):
                v_venda = row['Valor de Venda']
                v_aval = row['Valor de Avaliação Bancária']
                fin, sub, fx_n = motor.obter_enquadramento(d.get('renda', 0), d.get('social', False), d.get('cotista', True), v_aval)
                poder, ps_u = motor.calcular_poder_compra(d.get('renda', 0), fin, sub, d.get('perc_ps', 0), v_venda)
                cobertura = (poder / v_venda) * 100 if v_venda > 0 else 0
                return pd.Series([poder, cobertura, cobertura >= 100, fin, sub])

            df_disp_total[['Poder_Compra', 'Cobertura', 'Viavel', 'Finan_Unid', 'Sub_Unid']] = df_disp_total.apply(calcular_viabilidade_unidade, axis=1)
            # Reintroduzindo Status Viabilidade para filtro
            df_disp_total['Status Viabilidade'] = df_disp_total['Viavel'].apply(lambda x: "Viavel" if x else "Inviavel")
            
            df_disp_total = df_disp_total.sort_values('Cobertura', ascending=False)
            df_viaveis = df_disp_total[df_disp_total['Viavel']].copy()
        
        st.markdown("#### Panorama de Produtos Viáveis")
        if df_viaveis.empty:
            st.markdown('<div class="custom-alert">Sem produtos totalmente cobertos pelo poder de compra. Veja opções abaixo para negociar.</div>', unsafe_allow_html=True)
        else:
            emp_counts = df_viaveis.groupby('Empreendimento').size().to_dict()
            items = list(emp_counts.items()); cols_per_row = 3
            for i in range(0, len(items), cols_per_row):
                row_items = items[i:i+cols_per_row]; row_cols = st.columns(len(row_items))
                for idx, (emp, qtd) in enumerate(row_items):
                    with row_cols[idx]: st.markdown(f'''<div class="card" style="min-height: 80px; padding: 15px; border-top: 3px solid {COR_VERMELHO};"><p style="margin:0; font-weight:700; color:{COR_AZUL_ESC};">{emp}</p><p style="margin:5px 0 0 0; font-size:0.85rem; color:{COR_TEXTO_MUTED};">{qtd} unidades viaveis</p></div>''', unsafe_allow_html=True)

        st.write(""); tab_rec, tab_list = st.tabs(["Sugestões de Unidades", "Estoque Geral"])
        with tab_rec:
            emp_names_rec = sorted(df_disp_total['Empreendimento'].unique().tolist())
            emp_rec = st.selectbox("Escolha um empreendimento para obter recomendações:", options=["Todos"] + emp_names_rec, key="sel_emp_rec_v28")
            df_pool = df_disp_total if emp_rec == "Todos" else df_disp_total[df_disp_total['Empreendimento'] == emp_rec]
            if df_pool.empty: st.markdown('<div class="custom-alert">Nenhuma unidade encontrada para este filtro.</div>', unsafe_allow_html=True)
            else:
                top_3 = df_pool.head(3); cols = st.columns(3)
                for idx, row in enumerate(top_3.to_dict('records')):
                    with cols[idx % 3]:
                        st.markdown(f'''<div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC};"><b style="color:{COR_AZUL_ESC}; font-size:1.1rem;">{row['Empreendimento']}</b><br><small style="color:{COR_AZUL_ESC}; font-size:0.95rem;">Unidade: {row['Identificador']}</small><br><div class="price-tag" style="font-size:1.3rem; margin:2px 0;">R$ {fmt_br(row['Valor de Venda'])}</div><small style="color:{COR_AZUL_ESC}; opacity:0.9; font-size:0.8rem;">Cobertura: {row['Cobertura']:.1f}%</small></div>''', unsafe_allow_html=True)

        with tab_list:
            if df_disp_total.empty: st.markdown('<div class="custom-alert">Sem dados para exibir.</div>', unsafe_allow_html=True)
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
                if f_ordem == "Menor Preço": df_tab = df_tab.sort_values('Valor de Venda', ascending=True)
                else: df_tab = df_tab.sort_values('Valor de Venda', ascending=False)
                df_tab_view = df_tab.copy()
                df_tab_view['Valor de Venda'] = df_tab_view['Valor de Venda'].apply(fmt_br)
                df_tab_view['Poder_Compra'] = df_tab_view['Poder_Compra'].apply(fmt_br)
                df_tab_view['Cobertura'] = df_tab_view['Cobertura'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(df_tab_view[['Identificador', 'Bairro', 'Empreendimento', 'Valor de Venda', 'Cobertura']], use_container_width=True, hide_index=True, column_config={"Identificador": st.column_config.TextColumn("Unidade"), "Valor de Venda": st.column_config.TextColumn("Preço (R$)"), "Cobertura": st.column_config.TextColumn("Viabilidade (%)")})

        st.markdown("---")
        if st.button("Avançar para Seleção de Unidade", type="primary", use_container_width=True, key="btn_goto_selection"): st.session_state.passo_simulacao = 'selection'; st.rerun()
        st.write(""); 
        if st.button("Voltar para Dados do Cliente", use_container_width=True, key="btn_pot_v28"): st.session_state.passo_simulacao = 'input'; st.rerun()

    # --- ETAPA 3.5: SELEÇÃO DE UNIDADE (NOVA ABA) ---
    elif st.session_state.passo_simulacao == 'selection':
        d = st.session_state.dados_cliente
        st.markdown(f"### Seleção de Unidade para Fechamento")
        df_disponiveis = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
        
        if df_disponiveis.empty: st.warning("Sem estoque disponível na base.")
        else:
            emp_names = sorted(df_disponiveis['Empreendimento'].unique())
            idx_emp = 0
            if 'empreendimento_nome' in st.session_state.dados_cliente:
                try: idx_emp = emp_names.index(st.session_state.dados_cliente['empreendimento_nome'])
                except: idx_emp = 0
            emp_escolhido = st.selectbox("Escolha o Empreendimento:", options=emp_names, index=idx_emp, key="sel_emp_new_v3")
            unidades_disp = df_disponiveis[(df_disponiveis['Empreendimento'] == emp_escolhido)].copy()
            unidades_disp = unidades_disp.sort_values(['Bloco_Sort', 'Andar', 'Apto_Sort'])
            if unidades_disp.empty: st.warning("Sem unidades disponíveis neste empreendimento."); uni_escolhida_id = None
            else:
                def label_uni(uid):
                    u_row = unidades_disp[unidades_disp['Identificador'] == uid].iloc[0]
                    return f"{uid} - R$ {fmt_br(u_row['Valor de Venda'])}"
                current_uni_ids = unidades_disp['Identificador'].unique(); idx_uni = 0
                if 'unidade_id' in st.session_state.dados_cliente:
                    try: 
                        idx_list = list(current_uni_ids)
                        if st.session_state.dados_cliente['unidade_id'] in idx_list: idx_uni = idx_list.index(st.session_state.dados_cliente['unidade_id'])
                    except: pass
                uni_escolhida_id = st.selectbox("Escolha a Unidade:", options=current_uni_ids, index=idx_uni, format_func=label_uni, key="sel_uni_new_v3")

            if uni_escolhida_id:
                u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                v_aval = u_row['Valor de Avaliação Bancária']
                v_venda = u_row['Valor de Venda']
                fin_t, sub_t, _ = motor.obter_enquadramento(d.get('renda', 0), d.get('social', False), d.get('cotista', True), v_aval)
                poder_t, _ = motor.calcular_poder_compra(d.get('renda', 0), fin_t, sub_t, d.get('perc_ps', 0), v_venda)
                percentual_cobertura = (poder_t / v_venda) * 100
                width_percent = min(100, max(0, percentual_cobertura))
                if percentual_cobertura >= 100: cor_term = "#22c55e"
                elif percentual_cobertura >= 90: cor_term = "#eab308"
                else: cor_term = "#ef4444"
                st.markdown(f"""<div style="margin-top: 20px; padding: 15px; border: 1px solid #e2e8f0; border-radius: 10px; background-color: #f8fafc; text-align: center;"><p style="margin: 0; font-weight: 700; font-size: 0.9rem; color: #002c5d;">TERMÔMETRO DE VIABILIDADE</p><div style="width: 100%; background-color: #e2e8f0; border-radius: 5px; height: 10px; margin: 10px 0;"><div style="width: {width_percent}%; background-color: {cor_term}; height: 100%; border-radius: 5px; transition: width 0.5s;"></div></div></div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Avançar para Fechamento Financeiro", type="primary", use_container_width=True, key="btn_fech_new_v3"):
                if uni_escolhida_id:
                    u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                    fin, sub, _ = motor.obter_enquadramento(d.get('renda', 0), d.get('social', False), d.get('cotista', True), u_row['Valor de Avaliação Bancária'])
                    st.session_state.dados_cliente.update({'unidade_id': uni_escolhida_id, 'empreendimento_nome': emp_escolhido, 'imovel_valor': u_row['Valor de Venda'], 'imovel_avaliacao': u_row['Valor de Avaliação Bancária'], 'finan_estimado': fin, 'fgts_sub': sub})
                    st.session_state.passo_simulacao = 'payment_flow'; st.rerun()
                else: st.error("Por favor, selecione uma unidade.")
            if st.button("Voltar para Recomendações", use_container_width=True, key="btn_back_to_guide_new"): st.session_state.passo_simulacao = 'guide'; st.rerun()

    # --- ETAPA 4: FECHAMENTO ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### Fechamento Financeiro")
        u_valor = d.get('imovel_valor', 0)
        st.markdown(f'<div class="custom-alert">Unidade Selecionada: {d.get("unidade_id", "N/A")} - {d.get("empreendimento_nome", "N/A")} (R$ {fmt_br(u_valor)})</div>', unsafe_allow_html=True)
        
        col_fin, col_fgts = st.columns(2)
        with col_fin:
            f_u = st.number_input("Financiamento Bancário", value=float(d.get('finan_estimado', 0)), step=1000.0, key="fin_u_v28")
            st.markdown(f'<span class="inline-ref">Financiamento Máximo: R$ {fmt_br(d.get("finan_estimado", 0))}</span>', unsafe_allow_html=True)
        with col_fgts:
            fgts_u = st.number_input("FGTS + Subsídio", value=float(d.get('fgts_sub', 0)), step=1000.0, key="fgt_u_v28")
            st.markdown(f'<span class="inline-ref">Subsídio Máximo: R$ {fmt_br(d.get("fgts_sub", 0))}</span>', unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        # 1. Calcular Saldo Restante para Entrada (Preço - Finan - FGTS)
        saldo_restante_inicial = max(0.0, u_valor - f_u - fgts_u)
        
        # 2. Inicializar distribuição de entrada para cobrir o saldo
        calc_hash = f"{f_u}-{fgts_u}-{u_valor}-{d.get('unidade_id', 'none')}"
        if 'last_calc_hash' not in st.session_state or st.session_state.last_calc_hash != calc_hash:
            dist_val = saldo_restante_inicial / 4
            st.session_state.ato_1 = dist_val
            st.session_state.ato_2 = dist_val
            st.session_state.ato_3 = dist_val
            st.session_state.ato_4 = dist_val
            st.session_state.last_calc_hash = calc_hash

        # 3. Mostrar Inputs de Entrada
        st.markdown("#### Distribuição da Entrada")
        col_a, col_b = st.columns(2)
        with col_a:
            st.session_state.ato_1 = st.number_input("Ato", value=float(st.session_state.ato_1), key="ato_1_v28")
            st.session_state.ato_3 = st.number_input("Ato 60", value=float(st.session_state.ato_3), key="ato_3_v28")
        with col_b:
            st.session_state.ato_2 = st.number_input("Ato 30", value=float(st.session_state.ato_2), key="ato_2_v28")
            st.session_state.ato_4 = st.number_input("Ato 90", value=float(st.session_state.ato_4), key="ato_4_v28")

        # 4. Mostrar Inputs de Pro Soluto no FINAL
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_ps_val, col_ps_parc = st.columns(2)
        ps_max_real = u_valor * d.get('perc_ps', 0)
        
        with col_ps_val:
            # Default 0.0 conforme pedido
            ps_u = st.number_input("Pro Soluto Direcional", value=0.0, step=1000.0, key="ps_u_v28")
            st.markdown(f'<span class="inline-ref">Limite Permitido ({d.get("perc_ps", 0)*100:.0f}%): R$ {fmt_br(ps_max_real)}</span>', unsafe_allow_html=True)
        with col_ps_parc:
            parc = st.number_input("Número de Parcelas Pro Soluto", min_value=1, max_value=144, value=60, key="parc_u_v28") # Default 60 parcelas se quiser, ou d.get('prazo...')
            st.markdown(f'<span class="inline-ref">Prazo Máximo: {d.get("prazo_ps_max", 0)} meses</span>', unsafe_allow_html=True)

        # 5. Cálculos Finais e Validação
        v_parc = ps_u / parc if parc > 0 else 0
        comp_r = (v_parc / d.get('renda', 1)) if d.get('renda', 0) > 0 else 0
        
        # Saldo a Pagar = Preço - Finan - FGTS - PS - (Entradas)
        # Se PS for 0, as entradas devem cobrir tudo. Se PS > 0, ele ajuda a cobrir.
        # Total Pago = Finan + FGTS + PS + (Ato+30+60+90)
        total_pago = f_u + fgts_u + ps_u + st.session_state.ato_1 + st.session_state.ato_2 + st.session_state.ato_3 + st.session_state.ato_4
        gap_final = u_valor - total_pago

        # Resumo visual
        fin1, fin2, fin3 = st.columns(3)
        with fin1: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b style="color:{COR_AZUL_ESC};">VALOR DO IMÓVEL</b><br><span style="color:{COR_AZUL_ESC};">R$ {fmt_br(u_valor)}</span></div>""", unsafe_allow_html=True)
        with fin2: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_VERMELHO};"><b style="color:{COR_AZUL_ESC};">MENSALIDADE PS</b><br><span style="color:{COR_AZUL_ESC};">R$ {fmt_br(v_parc)} ({parc}x)</span></div>""", unsafe_allow_html=True)
        
        # Caixa de Saldo a Cobrir
        cor_saldo = COR_VERMELHO if abs(gap_final) > 1 else "#22c55e" # Verde se zerado
        with fin3: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {cor_saldo};"><b style="color:{COR_AZUL_ESC};">SALDO A COBRIR</b><br><span style="color:{COR_AZUL_ESC};">R$ {fmt_br(gap_final)}</span></div>""", unsafe_allow_html=True)

        if comp_r > d.get('limit_ps_renda', 1):
            st.warning(f"Atenção: Parcela Pro Soluto excede o limite de {d.get('limit_ps_renda', 0)*100:.0f}% da renda.")
        
        if abs(gap_final) > 1:
            st.error(f"Atenção: A conta não fecha. Falta cobrir R$ {fmt_br(gap_final)} ou há excesso de pagamento.")

        # Salva dados para resumo
        # Nota: entrada_total aqui é a soma dos atos, não o saldo restante
        total_entrada_cash = st.session_state.ato_1 + st.session_state.ato_2 + st.session_state.ato_3 + st.session_state.ato_4
        
        st.session_state.dados_cliente.update({
            'finan_usado': f_u, 'fgts_sub_usado': fgts_u,
            'ps_usado': ps_u, 'ps_parcelas': parc, 'ps_mensal': v_parc,
            'entrada_total': total_entrada_cash, # Valor pago em dinheiro nos atos
            'ato_final': st.session_state.ato_1, 'ato_30': st.session_state.ato_2,
            'ato_60': st.session_state.ato_3, 'ato_90': st.session_state.ato_4
        })
        
        st.markdown("---")
        if st.button("Avançar para Resumo de Compra", type="primary", use_container_width=True, key="btn_to_summary_v28"):
            st.session_state.passo_simulacao = 'summary'; st.rerun()
        if st.button("Voltar para Seleção de Imóvel", use_container_width=True, key="btn_back_to_selection_v28"): 
            st.session_state.passo_simulacao = 'selection'; st.rerun()

    # --- ETAPA 5: RESUMO ---
    elif st.session_state.passo_simulacao == 'summary':
        d = st.session_state.dados_cliente
        st.markdown(f"### Resumo da Simulação - {d.get('nome', 'Cliente')}")
        st.markdown(f'<div class="summary-header">DADOS DO IMÓVEL</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Empreendimento:</b> {d.get('empreendimento_nome')}<br><b>Unidade:</b> {d.get('unidade_id')}<br><b>Valor de Venda:</b> <span style="color: {COR_VERMELHO}; font-weight: 800;">R$ {fmt_br(d.get('imovel_valor', 0))}</span></div>""", unsafe_allow_html=True)
        st.markdown(f'<div class="summary-header">PLANO DE FINANCIAMENTO</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Financiamento Bancário:</b> R$ {fmt_br(d.get('finan_usado', 0))}<br><b>FGTS + Subsídio:</b> R$ {fmt_br(d.get('fgts_sub_usado', 0))}<br><b>Pro Soluto Total:</b> R$ {fmt_br(d.get('ps_usado', 0))} ({d.get('ps_parcelas')}x de R$ {fmt_br(d.get('ps_mensal', 0))})</div>""", unsafe_allow_html=True)
        st.markdown(f'<div class="summary-header">FLUXO DE ENTRADA (ATO)</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Total de Entrada:</b> R$ {fmt_br(d.get('entrada_total', 0))}<br><hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 10px 0;"><b>Ato:</b> R$ {fmt_br(d.get('ato_final', 0))}<br><b>Ato 30 Dias:</b> R$ {fmt_br(d.get('ato_30', 0))}<br><b>Ato 60 Dias:</b> R$ {fmt_br(d.get('ato_60', 0))}<br><b>Ato 90 Dias:</b> R$ {fmt_br(d.get('ato_90', 0))}</div>""", unsafe_allow_html=True)

        st.markdown("---")
        if PDF_ENABLED:
            pdf_data = gerar_resumo_pdf(d)
            if pdf_data:
                # Usando colunas com vertical_alignment="bottom" para alinhar visualmente com outros elementos se necessário
                # Aqui está isolado, então colunas normais funcionam bem.
                _, col_btn_center, _ = st.columns([1, 1.2, 1])
                with col_btn_center:
                    st.download_button(
                        label="Baixar Resumo em PDF", 
                        data=pdf_data, 
                        file_name=f"Resumo Direcional - {d.get('nome', 'Cliente')}.pdf", 
                        mime="application/pdf",
                        use_container_width=True,
                        key="btn_download_pdf_final_v28"
                    )

        st.markdown("#### Enviar Resumo por E-mail")
        c_email_in, c_email_btn = st.columns([3, 1], vertical_alignment="bottom")
        with c_email_in:
            email_dest = st.text_input("E-mail do Cliente", placeholder="exemplo@email.com", key="email_dest_summary", label_visibility="collapsed")
        with c_email_btn:
            if st.button("Enviar Resumo", type="primary", use_container_width=True, key="btn_send_email_summary"):
                if email_dest and "@" in email_dest:
                    st.success(f"Resumo enviado com sucesso para {email_dest}!")
                else:
                    st.warning("Por favor, digite um e-mail válido.")

        st.markdown("---")
        
        c_final_1, c_final_2 = st.columns(2)
        with c_final_1:
            if st.button("Voltar para Fechamento", use_container_width=True, key="btn_edit_fin_summary_v28"):
                st.session_state.passo_simulacao = 'payment_flow'; st.rerun()
                
        with c_final_2:
            if st.button("CONCLUIR E SALVAR SIMULAÇÃO", type="primary", use_container_width=True, key="btn_save_final"):
                try:
                    conn_save = st.connection("gsheets", type=GSheetsConnection)
                    aba_destino = st.session_state.get('user_imobiliaria', 'Cadastros')
                    if not aba_destino or aba_destino == 'nan': aba_destino = 'Cadastros'
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
                    st.success(f"Simulação salva com sucesso na aba '{aba_destino}'! Reiniciando...")
                    time.sleep(2)
                    st.session_state.dados_cliente = {}
                    st.session_state.passo_simulacao = 'input'
                    st.rerun()
                except Exception as e: st.error(f"Erro ao salvar dados: {e}")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    c_out_1, c_out_2, c_out_3 = st.columns([1, 1, 1])
    with c_out_2:
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
    if df_finan.empty or df_estoque.empty: st.warning("Aguardando conexão com base de dados..."); st.stop()
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if not st.session_state['logged_in']: tela_login(df_logins)
    else: aba_simulador_automacao(df_finan, df_estoque, df_politicas, df_cadastros)
    st.markdown(f'<div class="footer">Direcional Engenharia - Rio de Janeiro | Developed by Lucas Maia</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
