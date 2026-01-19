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

Versão: 52.5 (Ajuste Faixas F1/F2/F3 e Filtro Restrito Página2)
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

# Cores Oficiais Direcional - Elite Tecnológica
COR_AZUL_ESC = "#002c5d"
COR_VERMELHO = "#e30613"  # Vermelho Direcional Oficial
COR_FUNDO = "#fcfdfe"
COR_BORDA = "#eef2f6"
COR_TEXTO_MUTED = "#64748b"

def fmt_br(valor):
    """Formata números para o padrão brasileiro XXX.XXX,XX"""
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
            # Normaliza cabeçalhos da planilha de financiamento
            df_finan.columns = [str(c).strip() for c in df_finan.columns]
        except Exception:
            df_finan = pd.DataFrame()

        try:
            # 1. Carrega os dados brutos de estoque
            df_raw = conn.read(spreadsheet=URL_ESTOQUE)
            
            # 2. Carrega a lista de empreendimentos permitidos (Aba 'Página2')
            try:
                df_filtro = conn.read(spreadsheet=URL_ESTOQUE, worksheet="Página2")
                if 'Nome do empreendimento' in df_filtro.columns:
                    lista_permitidos = df_filtro['Nome do empreendimento'].dropna().astype(str).str.strip().str.upper().unique()
                else:
                    lista_permitidos = []
            except Exception:
                lista_permitidos = []

            df_estoque = df_raw.rename(columns={
                'Nome do Empreendimento': 'Empreendimento',
                'VALOR DE VENDA': 'Valor de Venda',
                'Status da unidade': 'Status'
            })
            df_estoque['Valor de Venda'] = df_estoque['Valor de Venda'].apply(limpar_moeda)
            
            # Filtro Restrito Página2
            if len(lista_permitidos) > 0:
                df_estoque = df_estoque[df_estoque['Empreendimento'].astype(str).str.strip().str.upper().isin(lista_permitidos)]
            else:
                st.warning("Lista de empreendimentos permitidos (Página2) não encontrada ou vazia.")

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

    def extrair_perfil_financiamento(self, renda, social, cotista):
        """
        Extrai todas as faixas (F1, F2, F3) para a renda informada.
        """
        if self.df_finan.empty: return {}
        
        # Identifica a coluna de Renda (pode ser 'Renda' ou 'Renda Familiar')
        col_renda_nome = 'Renda' if 'Renda' in self.df_finan.columns else 'Renda Familiar'
        
        if col_renda_nome in self.df_finan.columns:
            # Limpeza robusta para garantir que a renda da planilha vire número
            renda_col = self.df_finan[col_renda_nome].astype(str).str.replace('R$', '', regex=False)
            renda_col = renda_col.str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            renda_num_series = pd.to_numeric(renda_col, errors='coerce').fillna(0)
        else:
             return {}

        # Busca a linha da renda mais próxima
        idx = (renda_num_series - renda).abs().idxmin()
        row = self.df_finan.iloc[idx]
        
        s_suf = 'Sim' if social else 'Nao'
        c_suf = 'Sim' if cotista else 'Nao'
        
        perfil = {}
        for faixa in ['F1', 'F2', 'F3']:
            col_finan = f"Finan_Social_{s_suf}_Cotista_{c_suf}_{faixa}"
            col_sub = f"Subsidio_Social_{s_suf}_Cotista_{c_suf}_{faixa}"
            
            def safe_float(v):
                if pd.isna(v) or v is None: return 0.0
                if isinstance(v, (int, float)): return float(v)
                if isinstance(v, str):
                     v = v.replace('R$', '').replace('.', '').replace(',', '.').replace('\xa0', '').strip()
                     try: return float(v)
                     except: return 0.0
                return 0.0

            perfil[faixa] = {
                'finan': safe_float(row.get(col_finan, 0)),
                'sub': safe_float(row.get(col_sub, 0))
            }
        return perfil

    def determinar_faixa_imovel(self, valor_imovel):
        """Define qual sufixo (F1, F2, F3) usar baseado no valor do imóvel."""
        if valor_imovel <= 275000:
            return 'F1'
        elif valor_imovel <= 350000:
            return 'F2'
        elif valor_imovel <= 500000:
            return 'F3'
        else:
            return 'F3' # Assume F3 como teto máximo de cálculo

    def calcular_poder_compra(self, renda, perfil_finan, perc_ps, valor_unidade):
        """
        Calcula se a unidade é viável usando a faixa correta de financiamento.
        """
        faixa = self.determinar_faixa_imovel(valor_unidade)
        dados_faixa = perfil_finan.get(faixa, {'finan': 0.0, 'sub': 0.0})
        
        finan = dados_faixa['finan']
        sub = dados_faixa['sub']
        
        pro_soluto_unidade = valor_unidade * perc_ps
        poder = (2 * renda) + finan + sub + pro_soluto_unidade
        
        return poder, pro_soluto_unidade, finan, sub

    def filtrar_unidades_viaveis(self, renda, perfil_finan, perc_ps):
        if self.df_estoque.empty or not perfil_finan: return pd.DataFrame()
        
        estoque_disp = self.df_estoque[self.df_estoque['Status'] == 'Disponível'].copy()
        
        def processar_linha(row):
            vv = row['Valor de Venda']
            poder, ps_u, fin_u, sub_u = self.calcular_poder_compra(renda, perfil_finan, perc_ps, vv)
            return pd.Series([poder, ps_u, fin_u, sub_u])

        resultados = estoque_disp.apply(processar_linha, axis=1)
        resultados.columns = ['Poder_Compra', 'PS_Unidade', 'Finan_Ref', 'Sub_Ref']
        
        estoque_final = pd.concat([estoque_disp, resultados], axis=1)
        estoque_final['Viavel'] = estoque_final['Valor de Venda'] <= estoque_final['Poder_Compra']
        
        return estoque_final[estoque_final['Viavel']]

# =============================================================================
# 3. INTERFACE E DESIGN (ELITE TECNOLÓGICA)
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

        # Logótipo no PDF
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

    # --- ETAPA 1 ---
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
                # Extrai perfil completo para a renda
                perfil_finan = motor.extrair_perfil_financiamento(renda, social, cotista)
                
                class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
                politica_row = df_politicas[df_politicas['CLASSIFICAÇÃO'] == class_b].iloc[0]
                limit_ps_r = politica_row['FX_RENDA_1'] if renda < politica_row['FAIXA_RENDA'] else politica_row['FX_RENDA_2']
                
                st.session_state.dados_cliente = {
                    'nome': nome, 'renda': renda, 'social': social, 'cotista': cotista,
                    'ranking': ranking, 'politica': politica_ps, 
                    'perc_ps': politica_row['PROSOLUTO'], 
                    'prazo_ps_max': int(politica_row['PARCELAS']),
                    'limit_ps_renda': limit_ps_r, 
                    'perfil_finan': perfil_finan
                }
                st.session_state.passo_simulacao = 'potential'
                st.rerun()

    # --- ETAPA 2 ---
    elif st.session_state.passo_simulacao == 'potential':
        d = st.session_state.dados_cliente
        st.markdown(f"### Valor Potencial de Compra - {d['nome'] or 'Cliente'}")
        
        df_pot = df_estoque[df_estoque['Status'] == 'Disponível']
        pf = d.get('perfil_finan', {})
        
        # Lógica de Range para Financiamento (Min: F1, Max: F3)
        finan_min = pf.get('F1', {}).get('finan', 0)
        finan_max = pf.get('F3', {}).get('finan', 0)
        if finan_max == 0: finan_max = finan_min

        # Subsídio (Fixo para a renda)
        sub_val = pf.get('F1', {}).get('sub', 0)
        
        if df_pot.empty:
            st.warning("Não há empreendimentos disponíveis.")
            ps_min_total, ps_max_total = 0, 0
        else:
            ps_min_total = df_pot['Valor de Venda'].min() * d['perc_ps']
            ps_max_total = df_pot['Valor de Venda'].max() * d['perc_ps']
            
        dobro_renda = 2 * d['renda']
        pot_min = finan_min + sub_val + ps_min_total + dobro_renda
        pot_max = finan_max + sub_val + ps_max_total + dobro_renda
        
        m1, m2, m3, m4 = st.columns(4)
        
        finan_str = f"R$ {fmt_br(finan_min)} a {fmt_br(finan_max)}" if abs(finan_max - finan_min) > 100 else f"R$ {fmt_br(finan_max)}"
            
        with m1: st.markdown(f'<div class="card"><p class="metric-label">Financiamento</p><p class="metric-value" style="font-size: 1.4rem;">{finan_str}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="card"><p class="metric-label">FGTS + Subsídio</p><p class="metric-value">R$ {fmt_br(sub_val)}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="card"><p class="metric-label">Pro Soluto</p><p class="metric-value" style="font-size: 1.4rem;">R$ {fmt_br(ps_min_total)} a {fmt_br(ps_max_total)}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><p class="metric-label">Capacidade de Entrada</p><p class="metric-value">R$ {fmt_br(dobro_renda)}</p></div>', unsafe_allow_html=True)

        st.markdown(f"""
            <div class="card" style="border-top: 4px solid {COR_AZUL_ESC}; background: #ffffff; min-height: 120px;">
                <p class="metric-label" style="color: {COR_AZUL_ESC}; font-size: 0.8rem;">Poder de Aquisição Estimado</p>
                <p class="metric-value" style="font-size: 2.8rem; color: {COR_AZUL_ESC};">R$ {fmt_br(pot_min)} a R$ {fmt_br(pot_max)}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Avançar para Seleção de Imóvel", type="primary", use_container_width=True, key="btn_s2_v23"):
            st.session_state.passo_simulacao = 'guide'; st.rerun()
        st.write("")
        if st.button("Voltar para Dados do Cliente", use_container_width=True, key="btn_edit_v23"):
            st.session_state.passo_simulacao = 'input'; st.rerun()

    # --- ETAPA 3 ---
    elif st.session_state.passo_simulacao == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### Seleção de Imóvel")
        df_disp_total = motor.filtrar_unidades_viaveis(d['renda'], d['perfil_finan'], d['perc_ps'])
        
        if df_disp_total.empty:
            st.warning("Nenhum imóvel viável encontrado com as condições atuais.")
            df_viaveis = pd.DataFrame()
        else:
            df_disp_total['Status Viabilidade'] = "Viavel"
            df_viaveis = df_disp_total.copy()

        st.markdown("#### Empreendimentos Viáveis")
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
        tab_rec, tab_list = st.tabs(["Sugestões de Unidades", "Estoque Geral"])
        
        with tab_rec:
            if df_viaveis.empty:
                st.info("Nenhuma unidade atende ao poder de compra atual.")
            else:
                emp_rec = st.selectbox("Refinar Sugestões:", options=["Todos"] + sorted(df_viaveis['Empreendimento'].unique().tolist()), key="sel_emp_v23")
                df_filt_rec = df_viaveis if emp_rec == "Todos" else df_viaveis[df_viaveis['Empreendimento'] == emp_rec]
                df_filt_rec = df_filt_rec.sort_values('Valor de Venda', ascending=False)
                
                if not df_filt_rec.empty:
                    r100 = df_filt_rec.iloc[0]
                    r90 = df_filt_rec.iloc[len(df_filt_rec)//2]
                    r75 = df_filt_rec.iloc[-1]
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(f'<div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC};"><b>IDEAL</b><br><small>{r100["Empreendimento"]}</small><br>{r100["Identificador"]}<br><span class="price-tag">R$ {fmt_br(r100["Valor de Venda"])}</span></div>', unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="recommendation-card" style="border-top: 4px solid {COR_VERMELHO};"><b>SEGURO</b><br><small>{r90["Empreendimento"]}</small><br>{r90["Identificador"]}<br><span class="price-tag">R$ {fmt_br(r90["Valor de Venda"])}</span></div>', unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC};"><b>FACILITADO</b><br><small>{r75["Empreendimento"]}</small><br>{r75["Identificador"]}<br><span class="price-tag">R$ {fmt_br(r75["Valor de Venda"])}</span></div>', unsafe_allow_html=True)

        with tab_list:
            if df_viaveis.empty:
                st.info("Sem dados para exibir.")
            else:
                f1, f2, f3 = st.columns([2, 1, 1])
                with f1: f_emp = st.multiselect("Filtrar Projeto:", options=sorted(df_viaveis['Empreendimento'].unique()), key="f_emp_tab_v25")
                with f2: f_ordem = st.selectbox("Ordem:", ["Maior Preço", "Menor Preço"], key="f_ordem_tab_v25")
                with f3: f_pmax = st.number_input("Preço Máx:", value=float(df_viaveis['Valor de Venda'].max()), key="f_pmax_tab_v25")
                
                df_tab = df_viaveis.copy()
                if f_emp: df_tab = df_tab[df_tab['Empreendimento'].isin(f_emp)]
                df_tab = df_tab[df_tab['Valor de Venda'] <= f_pmax]
                df_tab = df_tab.sort_values('Valor de Venda', ascending=(f_ordem == "Menor Preço"))
                
                df_tab_view = df_tab.copy()
                df_tab_view['Valor de Venda'] = df_tab_view['Valor de Venda'].apply(fmt_br)
                df_tab_view['Poder_Compra'] = df_tab_view['Poder_Compra'].apply(fmt_br)

                st.dataframe(
                    df_tab_view[['Identificador', 'Empreendimento', 'Bairro', 'Andar', 'Valor de Venda', 'Poder_Compra', 'Status Viabilidade']], 
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Identificador": st.column_config.TextColumn("Unidade"),
                        "Valor de Venda": st.column_config.TextColumn("Valor Tabela"),
                        "Poder_Compra": st.column_config.TextColumn("Teto Aquisicao")
                    }
                )

        st.markdown("---")
        st.markdown("### Unidade Selecionada")
        emp_names = sorted(df_estoque['Empreendimento'].unique())
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            emp_escolhido = st.selectbox("Escolha o Empreendimento:", options=emp_names, key="sel_emp_guide_v26")
        unidades_disp = df_estoque[(df_estoque['Empreendimento'] == emp_escolhido) & (df_estoque['Status'] == 'Disponível')]
        with col_sel2:
            if unidades_disp.empty:
                st.warning("Sem estoque disponível.")
                uni_escolhida_id = None
            else:
                uni_escolhida_id = st.selectbox("Escolha a Unidade:", options=unidades_disp['Identificador'].unique(), 
                                                format_func=lambda x: f"{x} (R$ {fmt_br(unidades_disp[unidades_disp['Identificador']==x]['Valor de Venda'].values[0])})", key="sel_uni_guide_v26")

        if st.button("Avançar para Fechamento Financeiro", type="primary", use_container_width=True, key="btn_fech_v26"):
            if uni_escolhida_id:
                st.session_state.dados_cliente.update({'unidade_id': uni_escolhida_id, 'empreendimento_nome': emp_escolhido})
                st.session_state.passo_simulacao = 'payment_flow'; st.rerun()
            else: st.error("Selecione uma unidade.")
        
        if st.button("Voltar", use_container_width=True, key="btn_pot_v23"): 
            st.session_state.passo_simulacao = 'potential'; st.rerun()

    # --- ETAPA 4 ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        u = df_estoque[(df_estoque['Empreendimento'] == d['empreendimento_nome']) & (df_estoque['Identificador'] == d['unidade_id'])].iloc[0]
        st.markdown(f"### Fechamento Financeiro - {u['Identificador']}")
        st.markdown(f'<div class="custom-alert">Valor de Venda: R$ {fmt_br(u["Valor de Venda"])}</div>', unsafe_allow_html=True)
        
        faixa = motor.determinar_faixa_imovel(u["Valor de Venda"])
        fin_ref = d['perfil_finan'].get(faixa, {}).get('finan', 0)
        sub_ref = d['perfil_finan'].get(faixa, {}).get('sub', 0)

        f_u = st.number_input("Financiamento Bancário", value=float(fin_ref), step=1000.0, key="fin_u_v23")
        st.markdown(f'<p class="inline-ref">Financiamento Referência ({faixa}): R$ {fmt_br(fin_ref)}</p>', unsafe_allow_html=True)
        
        fgts_u = st.number_input("FGTS + Subsídio", value=float(sub_ref), step=1000.0, key="fgt_u_v23")
        st.markdown(f'<p class="inline-ref">Subsídio Referência: R$ {fmt_br(sub_ref)}</p>', unsafe_allow_html=True)
        
        ps_max = u['Valor de Venda'] * d['perc_ps']
        ps_u = st.number_input("Pro Soluto Direcional", value=float(ps_max), step=1000.0, key="ps_u_v23")
        parc = st.number_input("Parcelas Pro Soluto", min_value=1, max_value=d['prazo_ps_max'], value=d['prazo_ps_max'], key="parc_u_v23")
        
        saldo_e = u['Valor de Venda'] - f_u - fgts_u - ps_u
        v_parc = ps_u / parc

        fin1, fin2, fin3 = st.columns(3)
        with fin1: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b>VALOR IMÓVEL</b><br>R$ {fmt_br(u['Valor de Venda'])}</div>""", unsafe_allow_html=True)
        with fin2: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_VERMELHO};"><b>MENSALIDADE PS</b><br>R$ {fmt_br(v_parc)} ({parc}x)</div>""", unsafe_allow_html=True)
        with fin3: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b>SALDO ENTRADA</b><br>R$ {fmt_br(max(0, saldo_e))}</div>""", unsafe_allow_html=True)
        
        if saldo_e > 0:
            st.markdown("#### Distribuição da Entrada")
            c_a, c_b = st.columns(2)
            ato1 = c_a.number_input("Ato", value=saldo_e/4, key="ato_1_v24")
            ato2 = c_b.number_input("Ato 30", value=saldo_e/4, key="ato_2_v24")
            ato3 = c_a.number_input("Ato 60", value=saldo_e/4, key="ato_3_v24")
            ato4 = c_b.number_input("Ato 90", value=saldo_e/4, key="ato_4_v24")
            if abs((ato1+ato2+ato3+ato4) - saldo_e) > 1: st.error("A soma do fluxo diverge da entrada.")

        st.session_state.dados_cliente.update({
            'imovel_valor': u['Valor de Venda'], 'finan_usado': f_u, 'fgts_sub_usado': fgts_u,
            'ps_usado': ps_u, 'ps_parcelas': parc, 'ps_mensal': v_parc, 'entrada_total': saldo_e,
            'ato_final': ato1 if saldo_e > 0 else 0, 'ato_30': ato2 if saldo_e > 0 else 0,
            'ato_60': ato3 if saldo_e > 0 else 0, 'ato_90': ato4 if saldo_e > 0 else 0
        })
        
        if st.button("Gerar Resumo", type="primary", use_container_width=True): st.session_state.passo_simulacao = 'summary'; st.rerun()
        if st.button("Voltar", use_container_width=True): st.session_state.passo_simulacao = 'guide'; st.rerun()

    # --- ETAPA 5 ---
    elif st.session_state.passo_simulacao == 'summary':
        d = st.session_state.dados_cliente
        st.markdown(f"### Resumo Final - {d.get('nome')}")
        
        if PDF_ENABLED:
            pdf_data = gerar_resumo_pdf(d)
            if pdf_data: st.download_button("Baixar PDF Profissional", data=pdf_data, file_name=f"Relatorio_{d.get('nome')}.pdf", mime="application/pdf", use_container_width=True)

        st.markdown(f'<div class="summary-header">PLANO DE COMPRA</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body">
            <b>Imóvel:</b> {d.get('empreendimento_nome')} - {d.get('unidade_id')}<br>
            <b>Valor:</b> R$ {fmt_br(d.get('imovel_valor', 0))}<br><hr>
            <b>Financiamento:</b> R$ {fmt_br(d.get('finan_usado', 0))}<br>
            <b>Subsídio/FGTS:</b> R$ {fmt_br(d.get('fgts_sub_usado', 0))}<br>
            <b>Pro Soluto:</b> R$ {fmt_br(d.get('ps_usado', 0))} ({d.get('ps_parcelas')}x de R$ {fmt_br(d.get('ps_mensal', 0))})<br><hr>
            <b>Entrada (Fluxo):</b> R$ {fmt_br(d.get('entrada_total', 0))}
        </div>""", unsafe_allow_html=True)

        if st.button("Nova Simulação", type="primary", use_container_width=True): 
            st.session_state.dados_cliente = {}; st.session_state.passo_simulacao = 'input'; st.rerun()

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()
    if df_finan.empty or df_estoque.empty:
        st.warning("Conectando à base de dados...")
        st.stop()
    
    st.markdown(f'''<div class="header-container"><div class="header-title">SIMULADOR IMOBILIÁRIO DV</div><div class="header-subtitle">Gestão de Vendas - Direcional Rio</div></div>''', unsafe_allow_html=True)
    aba_simulador_automacao(df_finan, df_estoque, df_politicas)
    st.markdown(f'<div class="footer">Desenvolvido por Lucas Maia | Direcional Engenharia</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
