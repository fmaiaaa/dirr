# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V2 (MODIFICADO)
=============================================================================
Alterações Realizadas:
1. Lógica de Viabilidade: Agora calculada unidade a unidade (granular).
2. Poder de Compra: O valor na Etapa 2 é apenas um guia (baseado na média do estoque).
3. Recomendação: As sugestões (Ideal, Seguro, Facilitado) utilizam o poder de compra 
   específico de cada unidade em relação ao seu preço.
4. Estilização: Cor Azul Escuro (#002c5d) e design original preservados.
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
            color: {COR_AZUL_ESC}; 
            font-size: 1rem; 
            font-weight: 600; 
            margin-top: 15px; 
            letter-spacing: 0.1em;
            text-transform: uppercase;
            opacity: 0.8;
        }}
        
        .card, .fin-box, .recommendation-card {{ 
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
            font-weight: 700; 
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
            pdf.image("favicon.png", 10, 8, 10)
        
        pdf.ln(15)
        pdf.set_text_color(*AZUL_RGB)
        pdf.set_font("Helvetica", 'B', 22)
        pdf.cell(0, 12, "RELATÓRIO DE VIABILIDADE", ln=True, align='C')
        pdf.set_text_color(*AZUL_RGB)
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
        pdf.set_text_color(*AZUL_RGB)
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
        nome = st.text_input("Nome do Cliente", value=st.session_state.dados_cliente.get('nome', ""), placeholder="Nome Completo", key="in_nome_v28")
        renda = st.number_input("Renda Familiar", min_value=1.0, value=st.session_state.dados_cliente.get('renda', 3500.0), step=100.0, key="in_renda_v28")
        
        ranking_options = [r for r in df_politicas['CLASSIFICAÇÃO'].unique().tolist() if r != "EMCASH"] if not df_politicas.empty else ["DIAMANTE"]
        ranking = st.selectbox("Ranking do Cliente", options=ranking_options, index=0, key="in_rank_v28")
        politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"], key="in_pol_v28")
        social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False), key="in_soc_v28")
        cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True), key="in_cot_v28")
        
        if st.button("Avançar para Valor Potencial de Compra", type="primary", use_container_width=True, key="btn_s1_v28"):
            if not nome.strip():
                st.markdown(f'<div class="custom-alert">Por favor, informe o Nome do Cliente para continuar.</div>', unsafe_allow_html=True)
            elif any(char.isdigit() for char in nome):
                st.markdown(f'<div class="custom-alert">Nome Invalido. Por favor, insira um nome valido sem numeros.</div>', unsafe_allow_html=True)
            else:
                class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
                politica_row = df_politicas[df_politicas['CLASSIFICAÇÃO'] == class_b].iloc[0]
                limit_ps_r = politica_row['FX_RENDA_1'] if renda < politica_row['FAIXA_RENDA'] else politica_row['FX_RENDA_2']
                
                # Para o enquadramento do GUIA, usamos um valor de avaliação padrão
                f_faixa_ref, s_faixa_ref, fx_nome_ref = motor.obter_enquadramento(renda, social, cotista, valor_avaliacao=240000)

                st.session_state.dados_cliente = {
                    'nome': nome, 'renda': renda, 'social': social, 'cotista': cotista,
                    'ranking': ranking, 'politica': politica_ps, 
                    'perc_ps': politica_row['PROSOLUTO'], 
                    'prazo_ps_max': int(politica_row['PARCELAS']),
                    'limit_ps_renda': limit_ps_r,
                    'finan_f_ref': f_faixa_ref, 'sub_f_ref': s_faixa_ref
                }
                st.session_state.passo_simulacao = 'potential'
                st.rerun()

    # --- ETAPA 2: POTENCIAL (GUIA) ---
    elif st.session_state.passo_simulacao == 'potential':
        d = st.session_state.dados_cliente
        st.markdown(f"### Valor Potencial de Compra - {d['nome'] or 'Cliente'}")
        
        df_pot = df_estoque[df_estoque['Status'] == 'Disponível']
        
        if df_pot.empty:
            st.warning("Não há empreendimentos disponíveis.")
            ps_medio = 0
            pot_final = 0
        else:
            # Cálculo referencial baseado na média de mercado para servir como guia
            v_medio = df_pot['Valor de Venda'].mean()
            ps_medio = v_medio * d['perc_ps']
            dobro_renda = 2 * d['renda']
            pot_final = d['finan_f_ref'] + d['sub_f_ref'] + ps_medio + dobro_renda
        
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="card"><p class="metric-label">Finan. Ref.</p><p class="metric-value">R$ {fmt_br(d["finan_f_ref"])}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="card"><p class="metric-label">Subsídio Ref.</p><p class="metric-value">R$ {fmt_br(d["sub_f_ref"])}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="card"><p class="metric-label">Pro Soluto Ref.</p><p class="metric-value">R$ {fmt_br(ps_medio)}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><p class="metric-label">Capacidade Entrada</p><p class="metric-value">R$ {fmt_br(2 * d["renda"])}</p></div>', unsafe_allow_html=True)

        st.markdown(f"""
            <div class="card" style="border-top: 4px solid {COR_AZUL_ESC}; background: #ffffff; min-height: 120px;">
                <p class="metric-label" style="color: {COR_AZUL_ESC}; font-size: 0.8rem;">Poder de Aquisição Estimado (Guia)</p>
                <p class="metric-value" style="font-size: 2.8rem; color: {COR_AZUL_ESC};">R$ {fmt_br(pot_final)}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.info("Este valor é apenas uma estimativa guia. A viabilidade real será calculada para cada unidade individualmente na próxima etapa.")
        
        if st.button("Avançar para Recomendação Granular", type="primary", use_container_width=True, key="btn_s2_v28"):
            st.session_state.passo_simulacao = 'guide'; st.rerun()
        st.write("")
        if st.button("Voltar para Dados do Cliente", use_container_width=True, key="btn_edit_v28"):
            st.session_state.passo_simulacao = 'input'; st.rerun()

    # --- ETAPA 3: SELEÇÃO E RECOMENDAÇÃO GRANULAR ---
    elif st.session_state.passo_simulacao == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### Recomendação de Imóveis (Análise por Unidade)")
        
        df_disp_total = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
        
        if df_disp_total.empty:
            st.warning("Não há estoque disponível.")
            df_viaveis = pd.DataFrame()
        else:
            # Lógica de cálculo UNIDADE A UNIDADE
            def calcular_viabilidade_unidade(row):
                v_venda = row['Valor de Venda']
                v_aval = row['Valor de Avaliação Bancária']
                # Financiamento e subsídio mudam conforme a faixa da unidade (baseada na avaliação)
                fin, sub, fx_n = motor.obter_enquadramento(d['renda'], d['social'], d['cotista'], v_aval)
                # O poder de compra é calculado especificamente para esta unidade (Pro Soluto escala com o valor da unidade)
                poder, ps_u = motor.calcular_poder_compra(d['renda'], fin, sub, d['perc_ps'], v_venda)
                gap = poder - v_venda
                return pd.Series([poder, gap, gap >= 0, fin, sub])

            # Aplicando a lógica individual
            df_disp_total[['Poder_Compra', 'Gap', 'Viavel', 'Finan_Unid', 'Sub_Unid']] = df_disp_total.apply(calcular_viabilidade_unidade, axis=1)
            df_disp_total['Status Viabilidade'] = df_disp_total['Viavel'].apply(lambda x: "Viavel" if x else "Inviavel")
            
            df_viaveis = df_disp_total[df_disp_total['Viavel']].sort_values('Gap', ascending=False).copy()
        
        st.markdown("#### Panorama de Produtos Viáveis")
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
                            <div class="card" style="min-height: 80px; padding: 15px; border-top: 3px solid {COR_VERMELHO};">
                                <p style="margin:0; font-weight:700; color:{COR_AZUL_ESC};">{emp}</p>
                                <p style="margin:5px 0 0 0; font-size:0.85rem; color:{COR_TEXTO_MUTED};">{qtd} unidades viaveis</p>
                            </div>
                        """, unsafe_allow_html=True)

        st.write("")
        tab_rec, tab_list = st.tabs(["Sugestões de Unidades", "Estoque Geral"])
        
        with tab_rec:
            emp_names_rec = sorted(df_disp_total['Empreendimento'].unique().tolist())
            emp_rec = st.selectbox("Escolha um empreendimento para recomendações:", options=["Todos"] + emp_names_rec, key="sel_emp_rec_v28")
            
            df_pool = df_disp_total if emp_rec == "Todos" else df_disp_total[df_disp_total['Empreendimento'] == emp_rec]
            
            if df_pool.empty:
                st.info("Nenhuma unidade encontrada para este filtro.")
            else:
                # Novas Sugestões baseadas na viabilidade individual
                # Ideal: Maior valor de venda que seja viável (100% do poder)
                df_ideal_pool = df_pool[df_pool['Viavel']]
                df_ideal = df_ideal_pool.sort_values('Valor de Venda', ascending=False).head(1) if not df_ideal_pool.empty else pd.DataFrame()

                # Seguro: Unidades onde o valor de venda é <= 90% do poder de compra calculado PARA ELAS
                df_seguro_pool = df_pool[df_pool['Valor de Venda'] <= (df_pool['Poder_Compra'] * 0.90)]
                df_seguro = df_seguro_pool.sort_values('Valor de Venda', ascending=False).head(1) if not df_seguro_pool.empty else pd.DataFrame()

                # Facilitado: Unidades onde o valor de venda é <= 75% do poder de compra calculado PARA ELAS
                df_facilitado_pool = df_pool[df_pool['Valor de Venda'] <= (df_pool['Poder_Compra'] * 0.75)]
                df_facilitado = df_facilitado_pool.sort_values('Valor de Venda', ascending=False).head(1) if not df_facilitado_pool.empty else pd.DataFrame()

                def render_card_granular(df_unids, perfil_label, subtitulo, border_color):
                    if df_unids.empty:
                        st.markdown(f'''<div class="recommendation-card" style="border-top: 4px solid #cbd5e1; padding: 15px; min-height: 180px; opacity: 0.5;">
                            <b style="color:#64748b;">{perfil_label}</b><br><small>Nenhuma unidade encontrada</small>
                        </div>''', unsafe_allow_html=True)
                        return
                    
                    unid_ref = df_unids.iloc[0]
                    st.markdown(f'''<div class="recommendation-card" style="border-top: 4px solid {border_color}; padding: 15px; min-height: 180px;">
                        <span style="font-size:0.65rem; color:{COR_AZUL_ESC}; opacity:0.8;">PERFIL</span><br><b style="color:{COR_AZUL_ESC}; font-size:1.1rem;">{perfil_label}</b><br>
                        <small style="color:{COR_AZUL_ESC}; font-size:0.95rem;">{unid_ref["Empreendimento"]}</small><br>
                        <span style="color:{COR_AZUL_ESC}; font-size:1.0rem;">Unidade: {unid_ref["Identificador"]}</span><br>
                        <div class="price-tag" style="font-size:1.3rem; margin:2px 0;">R$ {fmt_br(unid_ref["Valor de Venda"])}</div>
                        <small style="color:{COR_AZUL_ESC}; opacity:0.9; font-size:0.8rem;">{subtitulo}</small>
                    </div>''', unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                with c1: render_card_granular(df_ideal, "IDEAL", "Até 100% da Capacidade Real", COR_AZUL_ESC)
                with c2: render_card_granular(df_seguro, "SEGURO", "Folga de 10% no Orçamento", COR_VERMELHO)
                with c3: render_card_granular(df_facilitado, "FACILITADO", "Folga de 25% no Orçamento", COR_AZUL_ESC)

        with tab_list:
            if df_disp_total.empty:
                st.info("Sem dados para exibir.")
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
                df_tab_view['Gap'] = df_tab_view['Gap'].apply(fmt_br)

                st.dataframe(
                    df_tab_view[['Identificador', 'Bairro', 'Empreendimento', 'Valor de Venda', 'Poder_Compra', 'Gap', 'Status Viabilidade']], 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Identificador": st.column_config.TextColumn("Unidade"),
                        "Valor de Venda": st.column_config.TextColumn("Preço (R$)"),
                        "Poder_Compra": st.column_config.TextColumn("Poder Real (R$)"),
                        "Gap": st.column_config.TextColumn("Saldo (R$)"),
                    }
                )

        st.markdown("---")
        st.markdown("### Seleção de Unidade para Fechamento")
        emp_names = sorted(df_estoque[df_estoque['Status'] == 'Disponível']['Empreendimento'].unique())
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            emp_escolhido = st.selectbox("Escolha o Empreendimento:", options=emp_names, key="sel_emp_guide_v28")
        
        unidades_disp = df_disp_total[(df_disp_total['Empreendimento'] == emp_escolhido)].copy()
        unidades_disp = unidades_disp.sort_values(['Bloco_Sort', 'Andar', 'Apto_Sort'])
        
        with col_sel2:
            if unidades_disp.empty:
                st.warning("Sem estoque disponivel.")
                uni_escolhida_id = None
            else:
                def label_uni(uid):
                    u_row = unidades_disp[unidades_disp['Identificador'] == uid].iloc[0]
                    cor_status = "✅" if u_row['Viavel'] else "❌"
                    return f"{uid} - {cor_status} (R$ {fmt_br(u_row['Valor de Venda'])})"
                uni_escolhida_id = st.selectbox("Escolha a Unidade:", options=unidades_disp['Identificador'].unique(), 
                                                format_func=label_uni, key="sel_uni_guide_v28")

        if st.button("Avançar para Fechamento Financeiro", type="primary", use_container_width=True, key="btn_fech_v28"):
            if uni_escolhida_id:
                u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                
                st.session_state.dados_cliente.update({
                    'unidade_id': uni_escolhida_id,
                    'empreendimento_nome': emp_escolhido,
                    'imovel_valor': u_row['Valor de Venda'],
                    'imovel_avaliacao': u_row['Valor de Avaliação Bancária'],
                    'finan_estimado': u_row['Finan_Unid'],
                    'fgts_sub': u_row['Sub_Unid'],
                    'faixa_unidade': "Calculada via Avaliação" # Informativo
                })
                st.session_state.passo_simulacao = 'payment_flow'
                st.rerun()
            else:
                st.error("Por favor, selecione uma unidade.")
        
        if st.button("Voltar para Valor Potencial", use_container_width=True, key="btn_pot_v28"): 
            st.session_state.passo_simulacao = 'potential'; st.rerun()

    # --- ETAPA 4: FECHAMENTO ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### Fechamento Financeiro")
        
        u_valor = d.get('imovel_valor', 0)
        u_aval = d.get('imovel_avaliacao', u_valor)
        st.markdown(f'<div class="custom-alert">Unidade Selecionada: {d["unidade_id"]} - {d["empreendimento_nome"]} (R$ {fmt_br(u_valor)})<br><small style="font-weight:400;">Valor de Avaliação: R$ {fmt_br(u_aval)}</small></div>', unsafe_allow_html=True)
        
        f_u = st.number_input("Financiamento Bancário", value=float(d['finan_estimado']), step=1000.0, key="fin_u_v28")
        st.markdown(f'<span class="inline-ref">Financiamento Específico Unidade: R$ {fmt_br(d.get("finan_estimado", 0))}</span>', unsafe_allow_html=True)
            
        fgts_u = st.number_input("FGTS + Subsídio", value=float(d['fgts_sub']), step=1000.0, key="fgt_u_v28")
        st.markdown(f'<span class="inline-ref">Subsídio Específico Unidade: R$ {fmt_br(d.get("fgts_sub", 0))}</span>', unsafe_allow_html=True)
        
        ps_max_real = u_valor * d['perc_ps']
        ps_u = st.number_input("Pro Soluto Direcional", value=float(ps_max_real), step=1000.0, key="ps_u_v28")
        st.markdown(f'<span class="inline-ref">Limite Permitido ({d.get("perc_ps", 0)*100:.0f}%): R$ {fmt_br(ps_max_real)}</span>', unsafe_allow_html=True)
        
        parc = st.number_input("Número de Parcelas Pro Soluto", min_value=1, max_value=144, value=d['prazo_ps_max'], key="parc_u_v28")
        st.markdown(f'<span class="inline-ref">Prazo Máximo: {d.get("prazo_ps_max", 0)} meses</span>', unsafe_allow_html=True)
        
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
        with fin1: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b style="color:{COR_AZUL_ESC};">VALOR DO IMÓVEL</b><br><span style="color:{COR_AZUL_ESC};">R$ {fmt_br(u_valor)}</span></div>""", unsafe_allow_html=True)
        with fin2: 
            st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_VERMELHO};"><b style="color:{COR_AZUL_ESC};">MENSALIDADE PS</b><br><span style="color:{COR_AZUL_ESC};">R$ {fmt_br(v_parc)} ({parc}x)</span></div>""", unsafe_allow_html=True)
            st.markdown(f'<center><span style="font-size:0.65rem; color:{COR_AZUL_ESC}; font-weight:700; opacity:0.8;">LIMITE RENDA: {d.get("limit_ps_renda", 0)*100:.0f}%</span></center>', unsafe_allow_html=True)
        with fin3: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b style="color:{COR_AZUL_ESC};">SALDO DE ENTRADA</b><br><span style="color:{COR_AZUL_ESC};">R$ {fmt_br(max(0, saldo_e))}</span></div>""", unsafe_allow_html=True)
        
        if comp_r > d['limit_ps_renda']:
            st.warning(f"Atenção: Parcela Pro Soluto excede o limite de {d['limit_ps_renda']*100:.0f}% da renda.")

        if saldo_e > 0:
            st.markdown("#### Distribuição da Entrada")
            col_a, col_b = st.columns(2)
            with col_a:
                st.session_state.ato_1 = st.number_input("Ato", value=st.session_state.ato_1, key="ato_1_v28")
                st.session_state.ato_3 = st.number_input("Ato 60", value=st.session_state.ato_3, key="ato_3_v28")
            with col_b:
                st.session_state.ato_2 = st.number_input("Ato 30", value=st.session_state.ato_2, key="ato_2_v28")
                st.session_state.ato_4 = st.number_input("Ato 90", value=st.session_state.ato_4, key="ato_4_v28")
            
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
        if st.button("Avançar para Resumo de Compra", type="primary", use_container_width=True, key="btn_to_summary_v28"):
            st.session_state.passo_simulacao = 'summary'; st.rerun()
        if st.button("Voltar para Seleção de Imóvel", use_container_width=True, key="btn_back_to_guide_v28"): 
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
                        key="btn_download_pdf_final_v28"
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
        if st.button("Fazer Nova Simulação", type="primary", use_container_width=True, key="btn_new_client_summary_v28"): 
            st.session_state.dados_cliente = {}; st.session_state.passo_simulacao = 'input'; st.rerun()
        if st.button("Voltar para Fechamento Financeiro", use_container_width=True, key="btn_edit_fin_summary_v28"):
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
