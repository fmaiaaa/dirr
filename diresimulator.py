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

Versão: 29.9 (Correção de Contraste: Texto Branco em Fundos Azul e Vermelho)
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        /* Cor de texto padrão para o corpo e elementos comuns */
        html, body, [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', sans-serif;
            color: {COR_AZUL_ESC};
        }}
        
        /* Fundo branco total */
        .main {{ background-color: #ffffff; }}
        .block-container {{ max-width: 1200px !important; padding: 1rem !important; margin: auto !important; }}
        
        /* Header */
        .header-container {{ text-align: center; padding: 35px 0; background: #ffffff; border-bottom: 5px solid {COR_VERMELHO}; margin-bottom: 25px; border-radius: 0 0 15px 15px; }}
        .header-title {{ color: {COR_AZUL_ESC}; font-size: 2.2rem; font-weight: 800; margin: 0; text-transform: uppercase; letter-spacing: 1px; }}
        .header-subtitle {{ color: #64748b; font-size: 1rem; font-weight: 400; margin-top: 8px; }}
        
        /* Cards */
        .card {{ background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; min-height: 130px; display: flex; flex-direction: column; justify-content: center; }}
        .recommendation-card {{ background: #ffffff; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; margin-bottom: 15px; text-align: center; min-height: 160px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
        
        .thin-card {{ background: white; padding: 15px 20px; border-radius: 8px; border: 1px solid #e2e8f0; border-left: 5px solid {COR_VERMELHO}; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }}
        
        /* Destaques */
        .price-tag {{ color: {COR_VERMELHO} !important; font-weight: 700; font-size: 1.2rem; }}
        .metric-label {{ color: #64748b !important; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; text-align: center; }}
        .metric-value {{ color: {COR_AZUL_ESC} !important; font-size: 1.4rem; font-weight: 700; text-align: center; }}
        
        /* Estilização de Botões (CORREÇÃO DE TEXTO BRANCO) */
        .stButton button {{ 
            border-radius: 8px !important; 
            padding: 12px !important; 
            font-weight: 600 !important; 
            color: #ffffff !important; 
            border: none !important; 
        }}

        /* Botão de VOLTAR: Azul Escuro */
        .stButton button {{ 
            background-color: {COR_AZUL_ESC} !important; 
            color: white !important;
        }}
        .stButton button:hover {{ 
            background-color: #001a3d !important; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
        }}
        
        /* Botão de AVANÇAR: Vermelho */
        .stButton button[kind="primary"] {{ 
            background-color: {COR_VERMELHO} !important; 
            color: white !important;
        }}
        .stButton button[kind="primary"]:hover {{ 
            background-color: #c40a10 !important; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
        }}
        
        /* Títulos */
        h1, h2, h3, h4 {{ text-align: center !important; width: 100%; color: {COR_AZUL_ESC} !important; font-weight: 700; }}
        
        /* Caixas Financeiras */
        .fin-box {{ text-align: center; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 15px; width: 100%; background: #ffffff; color: {COR_AZUL_ESC}; }}
        .inline-ref {{ font-size: 0.85rem; color: #475569 !important; margin-top: -12px; margin-bottom: 14px; font-weight: 500; text-align: left; background: #f8f9fa; padding: 6px 10px; border-radius: 4px; border-left: 3px solid {COR_VERMELHO}; }}
        
        /* Rodapé */
        .footer {{ text-align: center; padding: 30px 0; color: {COR_AZUL_ESC} !important; font-size: 0.85rem; border-top: 1px solid {COR_VERMELHO}; margin-top: 50px; font-weight: 400; background: #ffffff; }}
        
        /* Resumo (CORREÇÃO DE TEXTO BRANCO NO HEADER) */
        .summary-header {{ background: {COR_AZUL_ESC}; padding: 15px; border-radius: 10px 10px 0 0; font-weight: 600; text-align: center; margin-bottom: 0px; }}
        .summary-header b, .summary-header span, .summary-header div {{ color: white !important; }}
        .summary-body {{ background: white; padding: 20px; border: 1px solid #e2e8f0; border-radius: 0 0 10px 10px; margin-bottom: 20px; color: {COR_AZUL_ESC}; }}
        
        /* Custom Alert / Info Box (CORREÇÃO DE TEXTO BRANCO) */
        .custom-alert {{ background-color: {COR_AZUL_ESC}; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center; font-weight: 600; }}
        .custom-alert, .custom-alert b, .custom-alert span, .custom-alert p {{ color: white !important; }}
        
        /* Correção específica para a caixa de mensalidade azul */
        .blue-box-white-text {{ 
            background-color: {COR_AZUL_ESC} !important; 
            color: white !important; 
        }}
        .blue-box-white-text b, .blue-box-white-text span {{
            color: white !important;
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
        
        # Cabeçalho do Documento
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(0, 0, 210, 40, 'F')
        
        # Linha Vermelha Direcional no topo
        pdf.set_fill_color(227, 6, 19) 
        pdf.rect(0, 0, 210, 3, 'F')
        
        pdf.set_text_color(0, 44, 93) # Azul Escuro
        pdf.set_font("Helvetica", 'B', 18)
        pdf.ln(10)
        pdf.cell(0, 12, "SIMULADOR IMOBILIARIO DV", ln=True, align='C')
        pdf.set_text_color(100, 116, 139) # Cinza
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(0, 8, "Resumo de Compra e Viabilidade Financeira", ln=True, align='C')
        
        pdf.set_draw_color(0, 44, 93)
        pdf.line(60, 35, 150, 35)
        pdf.ln(15)

        # Informações do Cliente
        pdf.set_text_color(0, 44, 93)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, f"Cliente: {d.get('nome', 'Não informado')}", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 8, f"Renda Familiar: R$ {d.get('renda', 0):,.2f}", ln=True)
        pdf.ln(10)

        def criar_bloco_pdf(titulo, conteudo):
            pdf.set_fill_color(0, 44, 93)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 10, f"  {titulo}", ln=True, fill=True)
            
            pdf.set_text_color(0, 44, 93) # Letras internas em azul escuro
            pdf.set_font("Helvetica", '', 10.5)
            pdf.set_fill_color(255, 255, 255)
            pdf.set_draw_color(226, 232, 240)
            pdf.ln(2)
            for linha in conteudo:
                pdf.cell(0, 8, f"    {linha}", ln=True, border='LR')
            
            pdf.cell(0, 2, "", ln=True, border='LRB')
            pdf.ln(12)

        imovel_cont = [
            f"Empreendimento: {d.get('empreendimento_nome')}",
            f"Unidade: {d.get('unidade_id')}",
            f"Valor de Venda: R$ {d.get('imovel_valor', 0):,.2f}"
        ]
        criar_bloco_pdf("DADOS DO IMÓVEL", imovel_cont)

        finan_cont = [
            f"Financiamento Bancário: R$ {d.get('finan_usado', 0):,.2f}",
            f"FGTS + Subsídio: R$ {d.get('fgts_sub_usado', 0):,.2f}",
            f"Pro Soluto Total: R$ {d.get('ps_usado', 0):,.2f} ({d.get('ps_parcelas')}x de R$ {d.get('ps_mensal', 0):,.2f})"
        ]
        criar_bloco_pdf("PLANO DE FINANCIAMENTO", finan_cont)

        entrada_cont = [
            f"Total de Entrada: R$ {d.get('entrada_total', 0):,.2f}",
            "--------------------------------------------------------------------------------",
            f"Ato: R$ {d.get('ato_final', 0):,.2f}",
            f"Ato 30 Dias: R$ {d.get('ato_30', 0):,.2f}",
            f"Ato 60 Dias: R$ {d.get('ato_60', 0):,.2f}",
            f"Ato 90 Dias: R$ {d.get('ato_90', 0):,.2f}"
        ]
        criar_bloco_pdf("FLUXO DE ENTRADA (ATO)", entrada_cont)

        pdf.set_y(-25)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.set_text_color(227, 6, 19)
        pdf.cell(0, 10, "Este documento é uma simulação sujeita a análise de crédito.", ln=True, align='C')

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
        with m1: st.markdown(f'<div class="card"><p class="metric-label">Financiamento</p><p class="metric-value">R$ {d["finan_estimado"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="card"><p class="metric-label">FGTS + Subsídio</p><p class="metric-value">R$ {d["fgts_sub"]:,.2f}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="card"><p class="metric-label">Pro Soluto</p><p class="metric-value">R$ {ps_min_total:,.0f} a {ps_max_total:,.0f}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="card"><p class="metric-label">Capacidade de Entrada</p><p class="metric-value">R$ {dobro_renda:,.2f}</p></div>', unsafe_allow_html=True)

        st.markdown(f"""
            <div class="card" style="border-top: 5px solid {COR_AZUL_ESC}; text-align: center; background: #ffffff; min-height: auto; padding: 30px;">
                <p class="metric-label" style="color: {COR_AZUL_ESC}; font-size: 1.1rem;">Valor Potencial de Compra Estimado</p>
                <p class="metric-value" style="font-size: 2.2rem; color: {COR_AZUL_ESC}; margin-bottom:5px;">R$ {pot_min:,.2f} a R$ {pot_max:,.2f}</p>
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
        
        df_disp_total = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
        res = df_disp_total['Valor de Venda'].apply(lambda vv: motor.calcular_poder_compra(d['renda'], d['finan_estimado'], d['fgts_sub'], d['perc_ps'], vv))
        df_disp_total['Poder_Compra'] = [x[0] for x in res]
        df_disp_total['PS_Unidade'] = [x[1] for x in res]
        df_disp_total['Viavel'] = df_disp_total['Valor de Venda'] <= df_disp_total['Poder_Compra']
        df_disp_total['Status Viabilidade'] = df_disp_total['Viavel'].apply(lambda x: "Viável" if x else "Inviável")
        
        df_viaveis = df_disp_total[df_disp_total['Viavel']].copy()
        
        with st.expander("Empreendimentos viáveis", expanded=False):
            if df_viaveis.empty:
                st.write("Sem produtos viáveis no momento.")
            else:
                emp_counts = df_viaveis.groupby('Empreendimento').size().to_dict()
                for emp, qtd in emp_counts.items():
                    st.markdown(f'<div class="thin-card"><div><b>{emp}</b></div><div>{qtd} unid. viáveis</div></div>', unsafe_allow_html=True)

        tab_rec, tab_list = st.tabs(["Recomendações de Unidades", "Estoque Completo"])
        
        with tab_rec:
            if df_viaveis.empty:
                st.info("Atualmente, o cliente não possui unidades viáveis.")
            else:
                emp_rec = st.selectbox("Filtrar Recomendações por Empreendimento:", options=["Todos"] + sorted(df_viaveis['Empreendimento'].unique().tolist()), key="sel_emp_v23")
                df_filt_rec = df_viaveis if emp_rec == "Todos" else df_viaveis[df_viaveis['Empreendimento'] == emp_rec]
                df_filt_rec = df_filt_rec.sort_values('Valor de Venda', ascending=False)
                
                if not df_filt_rec.empty:
                    r100, r90, r75 = df_filt_rec.iloc[0], df_filt_rec.iloc[len(df_filt_rec)//2], df_filt_rec.iloc[-1]
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(f'<div class="recommendation-card" style="border-top-color:{COR_AZUL_ESC};"><b>IDEAL</b><br><small>{r100["Empreendimento"]}</small><br>{r100["Identificador"]}<br><span class="price-tag">R$ {r100["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="recommendation-card" style="border-top-color:{COR_VERMELHO};"><b>SEGURA</b><br><small>{r90["Empreendimento"]}</small><br>{r90["Identificador"]}<br><span class="price-tag">R$ {r90["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="recommendation-card" style="border-top-color:{COR_AZUL_ESC};"><b>FACILITADA</b><br><small>{r75["Empreendimento"]}</small><br>{r75["Identificador"]}<br><span class="price-tag">R$ {r75["Valor de Venda"]:,.2f}</span></div>', unsafe_allow_html=True)

        with tab_list:
            f1, f2, f3, f4, f5, f6 = st.columns([1.2, 1, 0.7, 1.1, 0.9, 0.8])
            with f1: f_emp = st.multiselect("Empreendimento:", options=sorted(df_disp_total['Empreendimento'].unique()), key="f_emp_tab_v25")
            with f2: f_bairro = st.multiselect("Bairro:", options=sorted(df_disp_total['Bairro'].unique()), key="f_bairro_tab_v25")
            with f3: f_andar = st.multiselect("Andar:", options=sorted(df_disp_total['Andar'].unique()), key="f_andar_tab_v25")
            with f4: f_status_v = st.multiselect("Viabilidade:", options=["Viável", "Inviável"], key="f_status_tab_v25")
            with f5: f_ordem = st.selectbox("Ordenar Preço:", ["Maior Preço", "Menor Preço"], key="f_ordem_tab_v25")
            with f6: f_pmax = st.number_input("Preço Máx:", value=float(df_disp_total['Valor de Venda'].max()), key="f_pmax_tab_v25")
            
            df_tab = df_disp_total.copy()
            if f_emp: df_tab = df_tab[df_tab['Empreendimento'].isin(f_emp)]
            if f_bairro: df_tab = df_tab[df_tab['Bairro'].isin(f_bairro)]
            if f_andar: df_tab = df_tab[df_tab['Andar'].isin(f_andar)]
            if f_status_v: df_tab = df_tab[df_tab['Status Viabilidade'].isin(f_status_v)]
            df_tab = df_tab[df_tab['Valor de Venda'] <= f_pmax]
            df_tab = df_tab.sort_values('Valor de Venda', ascending=(f_ordem == "Menor Preço"))
            
            st.dataframe(df_tab[['Identificador', 'Empreendimento', 'Bairro', 'Andar', 'Valor de Venda', 'Poder_Compra', 'Status Viabilidade']], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### Seleção do Imóvel")
        
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
                st.warning("Nenhuma unidade disponível.")
                uni_escolhida_id = None
            else:
                uni_escolhida_id = st.selectbox("Escolha a Unidade:", options=unidades_disp['Identificador'].unique(), 
                                               format_func=lambda x: label_uni_guide(x, unidades_disp), key="sel_uni_guide_v26")

        st.write("")
        if st.button("Avançar para Fechamento Financeiro", type="primary", use_container_width=True, key="btn_fech_v26"):
            if uni_escolhida_id:
                st.session_state.dados_cliente['unidade_id'] = uni_escolhida_id
                st.session_state.dados_cliente['empreendimento_nome'] = emp_escolhido
                st.session_state.passo_simulacao = 'payment_flow'
                st.rerun()
            else:
                st.error("Por favor, selecione uma unidade válida.")
        
        if st.button("Voltar para Valor Potencial de Compra", use_container_width=True, key="btn_pot_v23"): 
            st.session_state.passo_simulacao = 'potential'; st.rerun()

    # --- ETAPA 4 ---
    elif st.session_state.passo_simulacao == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### Fechamento Financeiro")
        
        u_id = d.get('unidade_id')
        emp_name = d.get('empreendimento_nome')
        unidades_filtradas = df_estoque[(df_estoque['Empreendimento'] == emp_name) & (df_estoque['Identificador'] == u_id)]
        
        if unidades_filtradas.empty:
            st.error("Erro ao recuperar unidade selecionada.")
            if st.button("Voltar para Seleção de Imóvel"): st.session_state.passo_simulacao = 'guide'; st.rerun()
        else:
            u = unidades_filtradas.iloc[0]
            st.markdown(f'<div class="custom-alert">Unidade Selecionada: {u["Identificador"]} - {u["Empreendimento"]} (R$ {u["Valor de Venda"]:,.2f})</div>', unsafe_allow_html=True)
            
            f_u = st.number_input("Financiamento", value=float(d['finan_estimado']), key="fin_u_v23")
            st.markdown(f'<p class="inline-ref">Referência Aprovada: R$ {d["finan_estimado"]:,.2f}</p>', unsafe_allow_html=True)
            
            fgts_u = st.number_input("FGTS + Subsídio", value=float(d['fgts_sub']), key="fgt_u_v23")
            st.markdown(f'<p class="inline-ref">Referência Estimada: R$ {d["fgts_sub"]:,.2f}</p>', unsafe_allow_html=True)
            
            ps_max_real = u['Valor de Venda'] * d['perc_ps']
            ps_u = st.number_input("Pro Soluto", value=float(ps_max_real), key="ps_u_v23")
            st.markdown(f'<p class="inline-ref">Máximo Permitido ({int(d["perc_ps"]*100)}%): R$ {ps_max_real:,.2f}</p>', unsafe_allow_html=True)
            
            parc = st.number_input("Quantidade de Parcelas do Pro Soluto", min_value=1, max_value=d['prazo_ps_max'], value=d['prazo_ps_max'], key="parc_u_v23")
            st.markdown(f'<p class="inline-ref">Limite de Parcelamento: {d["prazo_ps_max"]}x</p>', unsafe_allow_html=True)
            
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
            
            st.markdown(f"""
                <div class="fin-box" style="border-top: 5px solid {COR_AZUL_ESC};"><b>Valor do Imóvel:</b> R$ {u['Valor de Venda']:,.2f}</div>
                <div class="fin-box blue-box-white-text" style="border-top: 5px solid {COR_AZUL_ESC};">
                    <b>Mensalidade Pro Soluto:</b> R$ {v_parc:,.2f} em {parc}x
                </div>
            """, unsafe_allow_html=True)
            
            if comp_r > d['limit_ps_renda']:
                st.warning(f"Atenção: Parcela ultrapassa o limite de {d['limit_ps_renda']*100:.0f}% da renda.")

            st.markdown(f'<div class="fin-box" style="background:#ffffff; border-top: 5px solid {COR_VERMELHO};"><b>Saldo Entrada Restante:</b> R$ {max(0, saldo_e):,.2f}</div>', unsafe_allow_html=True)
            
            if saldo_e > 0:
                st.markdown("#### Parcelamento da Entrada")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.session_state.ato_1 = st.number_input("Ato", value=st.session_state.ato_1, key="ato_1_v24")
                    st.session_state.ato_3 = st.number_input("Ato 60", value=st.session_state.ato_3, key="ato_3_v24")
                with col_b:
                    st.session_state.ato_2 = st.number_input("Ato 30", value=st.session_state.ato_2, key="ato_2_v24")
                    st.session_state.ato_4 = st.number_input("Ato 90", value=st.session_state.ato_4, key="ato_4_v24")
                
                soma_entrada = st.session_state.ato_1 + st.session_state.ato_2 + st.session_state.ato_3 + st.session_state.ato_4
                if abs(soma_entrada - saldo_e) > 0.01:
                    st.error(f"A some das parcelas não confere com o Saldo de Entrada.")
            
            st.session_state.dados_cliente.update({
                'imovel_valor': u['Valor de Venda'], 'finan_usado': f_u, 'fgts_sub_usado': fgts_u,
                'ps_usado': ps_u, 'ps_parcelas': parc, 'ps_mensal': v_parc, 'entrada_total': saldo_e,
                'ato_final': st.session_state.ato_1, 'ato_30': st.session_state.ato_2,
                'ato_60': st.session_state.ato_3, 'ato_90': st.session_state.ato_4
            })
        
        st.markdown("---")
        if st.button("Obter Resumo de Compra", type="primary", use_container_width=True, key="btn_to_summary"):
            st.session_state.passo_simulacao = 'summary'
            st.rerun()
        if st.button("Voltar para Seleção de Imóvel", use_container_width=True, key="btn_back_to_guide"): 
            st.session_state.passo_simulacao = 'guide'; st.rerun()

    # --- ETAPA 5 ---
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
                        file_name=f"Resumo de Compra - {d.get('nome', 'Cliente')}.pdf", 
                        mime="application/pdf",
                        use_container_width=True,
                        key="btn_download_pdf_final"
                    )
        else:
            st.warning("Função de PDF indisponível. Verifique o arquivo requirements.txt.")

        st.markdown(f'<div class="summary-header">DADOS DO IMÓVEL</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Empreendimento:</b> {d.get('empreendimento_nome')}<br>
            <b>Unidade:</b> {d.get('unidade_id')}<br><b>Valor de Venda:</b> <span class="price-tag">R$ {d.get('imovel_valor', 0):,.2f}</span></div>""", unsafe_allow_html=True)

        st.markdown(f'<div class="summary-header">PLANO DE FINANCIAMENTO</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Financiamento Bancário:</b> R$ {d.get('finan_usado', 0):,.2f}<br>
            <b>FGTS + Subsídio:</b> R$ {d.get('fgts_sub_usado', 0):,.2f}<br>
            <b>Pro Soluto Total:</b> R$ {d.get('ps_usado', 0):,.2f} ({d.get('ps_parcelas')}x de R$ {d.get('ps_mensal', 0):,.2f})</div>""", unsafe_allow_html=True)

        st.markdown(f'<div class="summary-header">FLUXO DE ENTRADA (ATO)</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Total de Entrada:</b> R$ {d.get('entrada_total', 0):,.2f}<br><hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 10px 0;">
            <b>Ato:</b> R$ {d.get('ato_final', 0):,.2f}<br><b>Ato 30 Dias:</b> R$ {d.get('ato_30', 0):,.2f}<br>
            <b>Ato 60 Dias:</b> R$ {d.get('ato_60', 0):,.2f}<br><b>Ato 90 Dias:</b> R$ {d.get('ato_90', 0):,.2f}</div>""", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("Iniciar Novo Cliente", type="primary", use_container_width=True, key="btn_new_client_summary"): 
            st.session_state.dados_cliente = {}; st.session_state.passo_simulacao = 'input'; st.rerun()
        if st.button("Editar Fechamento Financeiro", use_container_width=True, key="btn_edit_fin_summary"):
            st.session_state.passo_simulacao = 'payment_flow'; st.rerun()

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas = carregar_dados_sistema()
    if df_finan.empty or df_estoque.empty:
        st.warning("Carregando dados privados...")
        st.stop()
    st.markdown(f'<div class="header-container"><div class="header-title">SIMULADOR IMOBILIÁRIO DV</div><div class="header-subtitle">Sistema de Gestão de Vendas e Viabilidade Imobiliária</div></div>', unsafe_allow_html=True)
    aba_simulador_automacao(df_finan, df_estoque, df_politicas)
    st.markdown(f'<div class="footer">Desenvolvido por Lucas Maia</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
