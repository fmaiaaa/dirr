# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V2
=============================================================================
Fluxo Automatizado de Recomendação (Sequencial):
1. Etapa 1: Entrada de dados do cliente.
2. Etapa 2: Valor Potencial de Compra.
3. Etapa 3: Guia de Viabilidade (Seleção do Produto).
4. Etapa 4: Fechamento Financeiro.
5. Etapa 5: Resumo da Compra e Exportação PDF.

Versão: 38.0 (Inputs Clean, Tabelas Executivas e PDF de Alta Fidelidade)
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from streamlit_gsheets import GSheetsConnection
import io
import streamlit.components.v1 as components
from PIL import Image
import os

# Tenta importar fpdf de forma segura
try:
    from fpdf import FPDF
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

# =============================================================================
# 0. CONSTANTES DE ACESSO (IDs DAS PLANILHAS REAIS)
# =============================================================================
ID_FINAN = "1wJD3tXe1e8FxL4mVEfNKGdtaS__Dl4V6-sm1G6qfL0s"
ID_RANKING = "1N00McOjO1O_MuKyQhp-CVhpAet_9Lfq-VqVm1FmPV00"
ID_ESTOQUE = "1VG-hgBkddyssN1OXgIA33CVsKGAdqT-5kwbgizxWDZQ"

# URLs oficiais para o conector privado
URL_FINAN = f"https://docs.google.com/spreadsheets/d/{ID_FINAN}/edit#gid=0"
URL_RANKING = f"https://docs.google.com/spreadsheets/d/{ID_RANKING}/edit#gid=0"
URL_ESTOQUE = f"https://docs.google.com/spreadsheets/d/{ID_ESTOQUE}/edit#gid=0"

# Link de reserva (caso o ícone descarregado não esteja na pasta)
URL_FAVICON_RESERVA = "https://direcional.com.br/wp-content/uploads/2021/04/cropped-favicon-direcional-32x32.png"

# Cores Oficiais Direcional
COR_AZUL_ESC = "#002c5d"
COR_VERMELHO = "#e30613" # Vermelho Direcional padrão

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

        # --- 1.1 Funções Auxiliares ---
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

        # --- 1.2 Carregar Ranking ---
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

        # --- 1.3 Carregar Financiamento ---
        try:
            df_finan = conn.read(spreadsheet=URL_FINAN)
        except Exception:
            df_finan = pd.DataFrame()

        # --- 1.4 Carregar Estoque ---
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
# 3. INTERFACE E DESIGN
# =============================================================================

def configurar_layout():
    icone_final = URL_FAVICON_RESERVA
    if os.path.exists("favicon.png"):
        try:
            icone_final = Image.open("favicon.png")
        except:
            pass

    st.set_page_config(page_title="Simulador Direcional", page_icon=icone_final, layout="wide")
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');
        
        html, body, [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', sans-serif;
            color: {COR_AZUL_ESC};
            line-height: 1.6;
        }}
        
        h1, h2, h3, h4 {{
            font-family: 'Montserrat', sans-serif !important;
            text-align: center !important; 
            width: 100%; 
            color: {COR_AZUL_ESC} !important; 
            font-weight: 800;
            letter-spacing: -0.5px;
            margin-bottom: 1.8rem !important;
        }}

        .main {{ background-color: #f8fafc; }}
        .block-container {{ max-width: 1200px !important; padding: 2.5rem 1rem !important; margin: auto !important; }}
        
        /* ESTILIZAÇÃO "CLEAN" DE INPUTS - Remove o visual de botões de incremento */
        div[data-baseweb="input"], .stTextInput input, .stNumberInput input {{
            border-radius: 25px !important; /* Visual puramente oval/circular externo */
            border: 1.5px solid #e2e8f0 !important;
            padding: 10px 20px !important;
            background-color: #ffffff !important;
            transition: all 0.3s ease !important;
            color: {COR_AZUL_ESC} !important;
            font-weight: 600 !important;
        }}
        
        /* Remove botões de Step (setinhas) para um visual limpo */
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {{
            -webkit-appearance: none;
            margin: 0;
        }}
        input[type=number] {{
            -moz-appearance: textfield;
        }}

        .stTextInput input:focus, .stNumberInput input:focus {{
            border-color: {COR_AZUL_ESC} !important;
            box-shadow: 0 0 0 4px rgba(0, 44, 93, 0.08) !important;
        }}
        
        /* Selectbox Profissional */
        div[data-baseweb="select"] > div {{
            border-radius: 20px !important;
            border: 1.5px solid #e2e8f0 !important;
            background-color: #ffffff !important;
        }}

        /* Header */
        .header-container {{ 
            text-align: center; 
            padding: 45px 0; 
            background: #ffffff; 
            border-bottom: 6px solid {COR_VERMELHO}; 
            margin-bottom: 45px; 
            border-radius: 0 0 24px 24px; 
            box-shadow: 0 10px 40px rgba(0, 44, 93, 0.05);
        }}
        .header-title {{ 
            font-family: 'Montserrat', sans-serif;
            color: {COR_AZUL_ESC}; 
            font-size: 2.6rem; 
            font-weight: 800; 
            margin: 0; 
            text-transform: uppercase; 
            letter-spacing: 3px; 
        }}
        
        /* Cartões */
        .card, .fin-box, .recommendation-card {{ 
            background: #ffffff; 
            padding: 30px; 
            border-radius: 20px; 
            border: 1px solid #edf2f7; 
            box-shadow: 0 8px 30px rgba(0,0,0,0.02); 
            margin-bottom: 30px; 
            min-height: 180px;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            width: 100%;
        }}
        
        .price-tag {{ color: {COR_VERMELHO} !important; font-weight: 800; font-size: 1.3rem; font-family: 'Montserrat', sans-serif; }}
        .metric-label {{ color: #94a3b8 !important; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; text-align: center; letter-spacing: 1.2px; margin-bottom: 8px; }}
        .metric-value {{ color: {COR_AZUL_ESC} !important; font-size: 1.35rem; font-weight: 800; text-align: center; font-family: 'Montserrat', sans-serif; }}
        
        /* Botões */
        .stButton button {{ 
            font-family: 'Inter', sans-serif;
            border-radius: 12px !important; 
            padding: 16px 32px !important; 
            font-weight: 600 !important; 
            color: #ffffff !important; 
            text-transform: uppercase;
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
        }}

        .stButton button[kind="primary"] {{ background-color: {COR_VERMELHO} !important; }}
        .stButton button {{ background-color: {COR_AZUL_ESC} !important; }}
        
        /* Tabelas Refinadas */
        [data-testid="stDataFrame"] {{
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 10px 25px rgba(0,0,0,0.03);
            overflow: hidden;
            background: white;
            padding: 5px;
        }}

        /* Rodapé */
        .footer {{ 
            text-align: center; 
            padding: 50px 0; 
            color: #94a3b8 !important; 
            font-size: 0.95rem; 
            border-top: 1px solid #e2e8f0; 
            margin-top: 80px; 
            font-weight: 500; 
        }}
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

        # Cabeçalho
        pdf.set_fill_color(*BRANCO_RGB)
        pdf.rect(0, 0, 210, 45, 'F')
        pdf.set_fill_color(*VERMELHO_RGB)
        pdf.rect(0, 0, 210, 4, 'F')
        
        pdf.set_text_color(*AZUL_RGB)
        pdf.set_font("Helvetica", 'B', 22)
        pdf.ln(15)
        pdf.cell(0, 10, "SIMULADOR IMOBILIARIO DV", ln=True, align='C')
        pdf.set_text_color(*CINZA_RGB)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 6, "Relatorio Executivo de Viabilidade Financeira", ln=True, align='C')
        pdf.ln(15)

        pdf.set_text_color(*AZUL_RGB)
        pdf.set_font("Helvetica", 'B', 13)
        pdf.cell(0, 10, f"CLIENTE: {d.get('nome', 'Nao informado').upper()}", ln=True)
        pdf.set_text_color(*AZUL_RGB)
        pdf.set_font("Helvetica", '', 12)
        pdf.cell(0, 8, f"Renda Familiar: R$ {d.get('renda', 0):,.2f}", ln=True)
        pdf.ln(10)

        def criar_card_pdf(titulo, linhas, destaque_vermelho=False):
            pdf.set_fill_color(*AZUL_RGB)
            pdf.set_text_color(*BRANCO_RGB)
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(0, 12, f"   {titulo}", ln=True, fill=True)
            
            pdf.set_fill_color(*BRANCO_RGB)
            pdf.set_draw_color(226, 232, 240)
            
            pdf.ln(2)
            for i, texto in enumerate(linhas):
                if texto == "SEPARATOR":
                    # LINHA GRÁFICA REAL EM VEZ DE TRAÇOS DE TEXTO
                    pdf.set_draw_color(226, 232, 240)
                    y_pos = pdf.get_y() + 4
                    pdf.line(20, y_pos, 190, y_pos)
                    pdf.ln(8)
                    continue

                if destaque_vermelho and i == len(linhas) - 1:
                    pdf.set_text_color(*VERMELHO_RGB)
                    pdf.set_font("Helvetica", 'B', 12)
                else:
                    pdf.set_text_color(*AZUL_RGB)
                    pdf.set_font("Helvetica", '', 11)
                
                pdf.cell(0, 9, f"      {texto}", ln=True, border='LR')
            
            pdf.cell(0, 3, "", ln=True, border='LRB')
            pdf.ln(12)

        criar_card_pdf("DADOS DO IMOVEL", [
            f"Empreendimento: {d.get('empreendimento_nome')}",
            f"Unidade: {d.get('unidade_id')}",
            f"Valor de Venda do Ativo: R$ {d.get('imovel_valor', 0):,.2f}"
        ], destaque_vermelho=True)

        criar_card_pdf("PLANO DE FINANCIAMENTO", [
            f"Financiamento Bancario Estimado: R$ {d.get('finan_usado', 0):,.2f}",
            f"Composicao FGTS + Subsidio: R$ {d.get('fgts_sub_usado', 0):,.2f}",
            f"Pro Soluto Total: R$ {d.get('ps_usado', 0):,.2f} ({d.get('ps_parcelas')} parcelas de R$ {d.get('ps_mensal', 0):,.2f})"
        ])

        criar_card_pdf("FLUXO DE ENTRADA (ATO)", [
            f"Valor Total de Entrada: R$ {d.get('entrada_total', 0):,.2f}",
            "SEPARATOR",
            f"Parcela de Ato: R$ {d.get('ato_final', 0):,.2f}",
            f"Ato 30 Dias: R$ {d.get('ato_30', 0):,.2f}",
            f"Ato 60 Dias: R$ {d.get('ato_60', 0):,.2f}",
            f"Ato 90 Dias: R$ {d.get('ato_90', 0):,.2f}"
        ])

        pdf.set_y(-25)
        pdf.set_font("Helvetica", 'I', 9)
        pdf.set_text_color(*CINZA_RGB)
        pdf.cell(0, 10, "Este documento e uma simulacao informativa sujeita a analise de credito oficial.", ln=True, align='C')

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
        nome = st.text_input("Nome do Cliente", value=st.session_state.dados_cliente.get('nome', ""), key="in_nome_v23")
        renda = st.number_input("Renda Familiar", min_value=1.0, value=st.session_state.dados_cliente.get('renda', 3500.0), step=100.0, key="in_renda_v23")
        
        ranking_options = [r for r in df_politicas['CLASSIFICAÇÃO'].unique().tolist() if r != "EMCASH"] if not df_politicas.empty else ["DIAMANTE"]
        ranking = st.selectbox("Ranking do Cliente", options=ranking_options, index=0, key="in_rank_v23")
        politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"], key="in_pol_v23")
        social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False), key="in_soc_v23")
        cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True), key="in_cot_v23")
        
        if st.button("Avançar para Valor Potencial de Compra", type="primary", use_container_width=True, key="btn_s1_v23"):
            if not nome.strip():
                st.markdown(f'<div class="custom-alert">Por favor, informe o Nome do Cliente para iniciar a simulação.</div>', unsafe_allow_html=True)
            else:
                finan, sub = motor.obter_enquadramento(renda, social, cotista)
                st.session_state.dados_cliente.update({
                    'nome': nome, 'renda': renda, 'social': social, 'cotista': cotista,
                    'ranking': ranking, 'politica': politica_ps, 'finan_estimado': finan, 'fgts_sub': sub
                })
                class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
                politica_row = df_politicas[df_politicas['CLASSIFICAÇÃO'] == class_b].iloc[0]
                st.session_state.dados_cliente.update({
                    'perc_ps': politica_row['PROSOLUTO'], 'prazo_ps_max': int(politica_row['PARCELAS']),
                    'limit_ps_renda': politica_row['FX_RENDA_1'] if renda < politica_row['FAIXA_RENDA'] else politica_row['FX_RENDA_2']
                })
                st.session_state.passo_simulacao = 'potential'; st.rerun()

    # --- ETAPA 2 ---
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
        with m1: st.markdown(f'<div class="card"><div class="metric-label">Financiamento</div><div class="metric-value">R$ {d["finan_estimado"]:,.2f}</div></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="card"><div class="metric-label">FGTS + Subsídio</div><div class="metric-value">R$ {d["fgts_sub"]:,.2f}</div></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="card"><div class="metric-label">Pro Soluto</div><div class="metric-value">R$ {ps_min_total:,.0f} a {ps_max_total:,.0f}</div></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><div class="metric-label">Entrada Limite</div><div class="metric-value">R$ {dobro_renda:,.2f}</div></div>', unsafe_allow_html=True)

        st.markdown(f"""<div class="card" style="border-top: 8px solid {COR_AZUL_ESC}; background: #ffffff;"><div class="metric-label">Valor Potencial de Compra Estimado</div><div class="metric-value" style="font-size: 2rem;">R$ {pot_min:,.2f} a R$ {pot_max:,.2f}</div></div>""", unsafe_allow_html=True)
        
        if st.button("Avançar para Seleção de Imóvel", type="primary", use_container_width=True, key="btn_s2_v23"):
            st.session_state.passo_simulacao = 'guide'; st.rerun()
        if st.button("Voltar para Dados do Cliente", use_container_width=True, key="btn_edit_v23"):
            st.session_state.passo_simulacao = 'input'; st.rerun()

    # --- ETAPA 3 ---
    elif st.session_state.passo_simulacao == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### Seleção de Imóvel")
        df_disp_total = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
        res = df_disp_total['Valor de Venda'].apply(lambda vv: motor.calcular_poder_compra(d['renda'], d['finan_estimado'], d['fgts_sub'], d['perc_ps'], vv))
        df_disp_total['Poder_Compra'] = [x[0] for x in res]
        df_disp_total['Status Viabilidade'] = df_disp_total['Valor de Venda'].apply(lambda vv: "Viável" if vv <= motor.calcular_poder_compra(d['renda'], d['finan_estimado'], d['fgts_sub'], d['perc_ps'], vv)[0] else "Inviável")
        
        tab_rec, tab_list = st.tabs(["Recomendações de Unidades", "Estoque Completo"])
        
        with tab_rec:
            df_viaveis = df_disp_total[df_disp_total['Status Viabilidade'] == "Viável"]
            if df_viaveis.empty:
                st.info("Nenhuma unidade viável com esta renda.")
            else:
                emp_rec = st.selectbox("Filtrar Recomendações por Empreendimento:", options=["Todos"] + sorted(df_viaveis['Empreendimento'].unique().tolist()), key="sel_emp_v23")
                df_filt_rec = df_viaveis if emp_rec == "Todos" else df_viaveis[df_viaveis['Empreendimento'] == emp_rec]
                df_filt_rec = df_filt_rec.sort_values('Valor de Venda', ascending=False)
                if not df_filt_rec.empty:
                    r100, r90, r75 = df_filt_rec.iloc[0], df_filt_rec.iloc[len(df_filt_rec)//2], df_filt_rec.iloc[-1]
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(f'<div class="recommendation-card" style="border-top: 8px solid {COR_AZUL_ESC};"><div class="metric-label">IDEAL</div><div class="metric-value">{r100["Identificador"]}</div><div class="price-tag">R$ {r100["Valor de Venda"]:,.2f}</div></div>', unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="recommendation-card" style="border-top: 8px solid {COR_VERMELHO};"><div class="metric-label">SEGURA</div><div class="metric-value">{r90["Identificador"]}</div><div class="price-tag">R$ {r90["Valor de Venda"]:,.2f}</div></div>', unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="recommendation-card" style="border-top: 8px solid {COR_AZUL_ESC};"><div class="metric-label">FACILITADA</div><div class="metric-value">{r75["Identificador"]}</div><div class="price-tag">R$ {r75["Valor de Venda"]:,.2f}</div></div>', unsafe_allow_html=True)

        with tab_list:
            # TABELA PROFISSIONAL COM COLUMN_CONFIG
            st.dataframe(
                df_disp_total[['Identificador', 'Empreendimento', 'Bairro', 'Andar', 'Valor de Venda', 'Poder_Compra', 'Status Viabilidade']],
                use_container_width=True, hide_index=True,
                column_config={
                    "Valor de Venda": st.column_config.NumberColumn("Preço de Venda", format="R$ %.2f"),
                    "Poder_Compra": st.column_config.NumberColumn("Potencial de Compra", format="R$ %.2f"),
                    "Status Viabilidade": st.column_config.StatusColumn("Viabilidade")
                }
            )

        st.markdown("---")
        st.markdown("### Seleção do Imóvel para Fechamento")
        emp_names = sorted(df_estoque[df_estoque['Status'] == 'Disponível']['Empreendimento'].unique())
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1: emp_escolhido = st.selectbox("Empreendimento:", options=emp_names, key="sel_emp_g")
        unidades_disp = df_estoque[(df_estoque['Empreendimento'] == emp_escolhido) & (df_estoque['Status'] == 'Disponível')]
        with col_sel2: uni_escolhida_id = st.selectbox("Unidade:", options=unidades_disp['Identificador'].unique(), key="sel_uni_g")

        if st.button("Avançar para Fechamento Financeiro", type="primary", use_container_width=True):
            st.session_state.dados_cliente.update({'unidade_id': uni_escolhida_id, 'empreendimento_nome': emp_escolhido})
            st.session_state.passo_simulacao = 'payment_flow'; st.rerun()
        if st.button("Voltar para Valor Potencial", use_container_width=True): 
            st.session_state.passo_simulacao = 'potential'; st.rerun()

    # --- ETAPA 4 ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### Fechamento Financeiro")
        u = df_estoque[(df_estoque['Empreendimento'] == d['empreendimento_nome']) & (df_estoque['Identificador'] == d['unidade_id'])].iloc[0]
        st.markdown(f'<div class="custom-alert">Unidade: {u["Identificador"]} - {u["Empreendimento"]} (R$ {u["Valor de Venda"]:,.2f})</div>', unsafe_allow_html=True)
        
        f_u = st.number_input("Financiamento", value=float(d['finan_estimado']), key="fin_u")
        fgts_u = st.number_input("FGTS + Subsídio", value=float(d['fgts_sub']), key="fgt_u")
        ps_u = st.number_input("Pro Soluto", value=float(u['Valor de Venda'] * d['perc_ps']), key="ps_u")
        parc = st.number_input("Parcelas PS", min_value=1, max_value=d['prazo_ps_max'], value=d['prazo_ps_max'], key="parc_u")
        
        v_parc = ps_u / parc
        saldo_e = u['Valor de Venda'] - f_u - fgts_u - ps_u

        fin1, fin2, fin3 = st.columns(3)
        with fin1: st.markdown(f'<div class="fin-box" style="border-top: 10px solid {COR_AZUL_ESC};"><div class="metric-label">Valor do Imóvel</div><div class="metric-value">R$ {u["Valor de Venda"]:,.2f}</div></div>', unsafe_allow_html=True)
        with fin2: st.markdown(f'<div class="fin-box" style="border-top: 10px solid {COR_VERMELHO};"><div class="metric-label">Mensalidade PS</div><div class="metric-value">R$ {v_parc:,.2f} ({parc}x)</div></div>', unsafe_allow_html=True)
        with fin3: st.markdown(f'<div class="fin-box" style="border-top: 10px solid {COR_AZUL_ESC};"><div class="metric-label">Saldo Entrada</div><div class="metric-value">R$ {max(0, saldo_e):,.2f}</div></div>', unsafe_allow_html=True)

        if saldo_e > 0:
            st.markdown("#### Fluxo de Entrada")
            dist = max(0.0, saldo_e / 4)
            c1, c2 = st.columns(2)
            with c1:
                ato1 = st.number_input("Ato", value=dist, key="ato1")
                ato3 = st.number_input("Ato 60", value=dist, key="ato3")
            with c2:
                ato2 = st.number_input("Ato 30", value=dist, key="ato2")
                ato4 = st.number_input("Ato 90", value=dist, key="ato4")
            st.session_state.dados_cliente.update({'ato_final': ato1, 'ato_30': ato2, 'ato_60': ato3, 'ato_90': ato4})

        st.session_state.dados_cliente.update({'imovel_valor': u['Valor de Venda'], 'finan_usado': f_u, 'fgts_sub_usado': fgts_u, 'ps_usado': ps_u, 'ps_parcelas': parc, 'ps_mensal': v_parc, 'entrada_total': saldo_e})
        
        if st.button("Obter Resumo", type="primary", use_container_width=True): st.session_state.passo_simulacao = 'summary'; st.rerun()
        if st.button("Voltar", use_container_width=True): st.session_state.passo_simulacao = 'guide'; st.rerun()

    # --- ETAPA 5 ---
    elif st.session_state.passo_simulacao == 'summary':
        d = st.session_state.dados_cliente
        st.markdown(f"### Resumo da Simulação - {d.get('nome', 'Cliente')}")
        if PDF_ENABLED:
            pdf_data = gerar_resumo_pdf(d)
            if pdf_data:
                st.download_button("Baixar PDF Oficial", data=pdf_data, file_name=f"Resumo Direcional - {d['nome']}.pdf", mime="application/pdf", use_container_width=True)

        st.markdown(f'<div class="summary-header">DADOS DO IMÓVEL</div><div class="summary-body"><b>Empreendimento:</b> {d["empreendimento_nome"]}<br><b>Unidade:</b> {d["unidade_id"]}<br><b>Valor:</b> <span class="price-tag">R$ {d["imovel_valor"]:,.2f}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-header">PLANO FINANCEIRO</div><div class="summary-body"><b>Financiamento:</b> R$ {d["finan_usado"]:,.2f}<br><b>Pro Soluto:</b> R$ {d["ps_usado"]:,.2f} ({d["ps_parcelas"]}x R$ {d["ps_mensal"]:,.2f})</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-header">FLUXO DE ATO</div><div class="summary-body"><b>Entrada:</b> R$ {d["entrada_total"]:,.2f}<hr style="border-top: 1px solid #e2e8f0;"><b>Ato:</b> R$ {d.get("ato_final",0):,.2f} | <b>30d:</b> R$ {d.get("ato_30",0):,.2f} | <b>60d:</b> R$ {d.get("ato_60",0):,.2f} | <b>90d:</b> R$ {d.get("ato_90",0):,.2f}</div>', unsafe_allow_html=True)
        if st.button("Novo Cliente", type="primary", use_container_width=True): st.session_state.dados_cliente = {}; st.session_state.passo_simulacao = 'input'; st.rerun()

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()
    if df_finan.empty or df_estoque.empty: st.warning("Aguarde o carregamento..."); st.stop()
    st.markdown(f'<div class="header-container"><div class="header-title">SIMULADOR IMOBILIÁRIO DV</div><div class="header-subtitle">Gestão de Viabilidade e Fechamento Direcional</div></div>', unsafe_allow_html=True)
    aba_simulador_automacao(df_finan, df_estoque, df_politicas)
    st.markdown(f'<div class="footer">Desenvolvido para Direcional Rio | Por Lucas Maia</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
