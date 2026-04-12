# -*- coding: utf-8 -*-
from __future__ import annotations
# =============================================================================
# SIMULADOR STREAMLIT — FICHEIRO ÚNICO (gerado automaticamente)
# =============================================================================
# Gerado por: python scripts/build_streamlit_monolith.py
# NÃO editar este ficheiro à mão. Altere simulador_dv/*.py e regenere.
#
# Execução:
#   cd <raiz do repositório>
#   pip install -r requirements.txt
#   streamlit run streamlit_monolith.py
#
# Nota: static/, credentials e .streamlit/secrets continuam ficheiros à parte.
# =============================================================================


# ========================================================================
# config/constants.py
# ========================================================================

# URLs, IDs e paleta (espelho do Excel / branding)
ID_GERAL = "https://docs.google.com/spreadsheets/d/1N00McOjO1O_MuKyQhp-CVhpAet_9Lfq-VqVm1FmPV00/edit#gid=0"

URL_FINAN = f"https://docs.google.com/spreadsheets/d/{ID_GERAL}/edit#gid=0"
URL_RANKING = f"https://docs.google.com/spreadsheets/d/{ID_GERAL}/edit#gid=0"
URL_ESTOQUE = f"https://docs.google.com/spreadsheets/d/{ID_GERAL}/edit#gid=0"

URL_FAVICON_RESERVA = "https://direcional.com.br/wp-content/uploads/2021/04/cropped-favicon-direcional-32x32.png"
URL_LOGO_DIRECIONAL_BIG = "https://logodownload.org/wp-content/uploads/2021/04/direcional-engenharia-logo.png"

# Mesmos ficheiros da ficha Credenciamento Vendas RJ (pasta deste .py, raiz do repo ou assets/)
LOGO_TOPO_ARQUIVO = "502.57_LOGO DIRECIONAL_V2F-01.png"
FAVICON_ARQUIVO = "502.57_LOGO D_COR_V3F.png"
FUNDO_CADASTRO_ARQUIVO = "fundo_cadastrorh.jpg"

# Paleta alinhada à ficha Credenciamento Vendas RJ (Streamlit)
COR_AZUL_ESC = "#04428f"
COR_VERMELHO = "#cb0935"
COR_FUNDO = "#04428f"
COR_BORDA = "#eef2f6"
COR_TEXTO_MUTED = "#64748b"
COR_INPUT_BG = "#f0f2f6"
COR_TEXTO_LABEL = "#1e293b"
COR_VERMELHO_ESCURO = "#9e0828"


def _hex_rgb_triplet(hex_color: str) -> str:
    """Converte #RRGGBB em 'r, g, b' para rgba(...) no CSS."""
    x = (hex_color or "").strip().lstrip("#")
    if len(x) != 6:
        return "0, 0, 0"
    return f"{int(x[0:2], 16)}, {int(x[2:4], 16)}, {int(x[4:6], 16)}"


RGB_AZUL_CSS = _hex_rgb_triplet(COR_AZUL_ESC)
RGB_VERMELHO_CSS = _hex_rgb_triplet(COR_VERMELHO)

# ========================================================================
# config/taxas_comparador.py
# ========================================================================

# -*- coding: utf-8 -*-

# Mesmo literal do Excel: subtrai 30% do parâmetro de política para obter % líquido de renda.
OFFSET_LAMBDA: float = 0.30


def excel_e4_mensal(ipca_aa: float) -> float:
    """E4 = (1+E3)^(1/12)-1 com E3 = IPCA anual em decimal."""
    return (1.0 + float(ipca_aa)) ** (1.0 / 12.0) - 1.0


def excel_e1(tx_emcash_b5: float, e4: float) -> float:
    """E1 = B5 + E4 (espelho literal do Excel)."""
    return float(tx_emcash_b5) + float(e4)

# ========================================================================
# data/politicas_ps.py
# ========================================================================

# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

# Valores extraídos de excel_extracao_celulas.txt (aba POLITICAS, linhas 2–7).
# Manter alinhado ao Excel: cada classificação = um bloco do comparador (K3, X3, AJ3…).
DEFAULT_POLITICAS_ROWS: List[Dict[str, Any]] = [
    {"classificacao": "EMCASH", "prosoluto_pct": 0.25, "faixa_renda": 0.0, "fx_renda_1": 0.55, "fx_renda_2": 0.55, "parcelas_max": 66.0},
    {"classificacao": "DIAMANTE", "prosoluto_pct": 0.25, "faixa_renda": 4000.0, "fx_renda_1": 0.5, "fx_renda_2": 0.5, "parcelas_max": 84.0},
    {"classificacao": "OURO", "prosoluto_pct": 0.20, "faixa_renda": 4000.0, "fx_renda_1": 0.5, "fx_renda_2": 0.5, "parcelas_max": 84.0},
    {"classificacao": "PRATA", "prosoluto_pct": 0.18, "faixa_renda": 4000.0, "fx_renda_1": 0.48, "fx_renda_2": 0.48, "parcelas_max": 84.0},
    {"classificacao": "BRONZE", "prosoluto_pct": 0.15, "faixa_renda": 4000.0, "fx_renda_1": 0.45, "fx_renda_2": 0.45, "parcelas_max": 84.0},
    {"classificacao": "AÇO", "prosoluto_pct": 0.12, "faixa_renda": 4000.0, "fx_renda_1": 0.4, "fx_renda_2": 0.4, "parcelas_max": 84.0},
]


@dataclass(frozen=True)
class PoliticaPSRow:
    classificacao: str
    prosoluto_pct: float
    faixa_renda: float
    fx_renda_1: float
    fx_renda_2: float
    parcelas_max: float


def _norm_key(s: str) -> str:
    t = str(s or "").strip().upper()
    if t in ("ACO", "AÇO"):
        return "AÇO"
    return t


def politica_row_from_defaults(classificacao: str) -> Optional[PoliticaPSRow]:
    k = _norm_key(classificacao)
    for row in DEFAULT_POLITICAS_ROWS:
        if _norm_key(str(row["classificacao"])) == k:
            return PoliticaPSRow(
                classificacao=str(row["classificacao"]),
                prosoluto_pct=float(row["prosoluto_pct"]),
                faixa_renda=float(row["faixa_renda"]),
                fx_renda_1=float(row["fx_renda_1"]),
                fx_renda_2=float(row["fx_renda_2"]),
                parcelas_max=float(row["parcelas_max"]),
            )
    return None


def _default_rows_list() -> List[PoliticaPSRow]:
    out = []
    for r in DEFAULT_POLITICAS_ROWS:
        pr = politica_row_from_defaults(r["classificacao"])
        if pr:
            out.append(pr)
    return out


def politicas_from_dataframe(df: Optional[pd.DataFrame]) -> List[PoliticaPSRow]:
    """Interpreta aba POLITICAS com colunas A–F (primeiras 6 colunas se sem nome)."""
    if df is None or df.empty:
        return _default_rows_list()
    out: List[PoliticaPSRow] = []
    df = df.copy()
    cols = list(df.columns)
    for _, row in df.iterrows():
        try:
            vals = [row.get(c) for c in cols[:6]]
            if len(vals) < 6:
                continue
            a, b, c, d, e, f = vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]
            if a is None or str(a).strip() == "" or str(a).lower() == "nan":
                continue
            if "CLASSIF" in str(a).upper():
                continue
            pr = PoliticaPSRow(
                classificacao=str(a).strip(),
                prosoluto_pct=float(b) if b is not None and str(b) != "nan" else 0.0,
                faixa_renda=float(c) if c is not None and str(c) != "nan" else 0.0,
                fx_renda_1=float(d) if d is not None and str(d) != "nan" else 0.0,
                fx_renda_2=float(e) if e is not None and str(e) != "nan" else 0.0,
                parcelas_max=float(f) if f is not None and str(f) != "nan" else 0.0,
            )
            if pr.prosoluto_pct > 0 and pr.parcelas_max > 0:
                out.append(pr)
        except (TypeError, ValueError, IndexError):
            continue
    return out if out else _default_rows_list()


def resolve_politica_row(
    politica_ui: str,
    ranking: str,
    df_politicas: Optional[pd.DataFrame] = None,
) -> PoliticaPSRow:
    """
    - Política Emcash (produto) → linha EMCASH na POLITICAS.
    - Política Direcional → linha do ranking (DIAMANTE, OURO, ...).
    """
    rows = politicas_from_dataframe(df_politicas)

    if str(politica_ui or "").strip().lower() == "emcash":
        key = "EMCASH"
    else:
        key = _norm_key(ranking or "DIAMANTE")

    for r in rows:
        if _norm_key(r.classificacao) == key:
            return r
    fb = politica_row_from_defaults(key)
    if fb:
        return fb
    return rows[0]


def classificacao_efetiva(politica_ui: str, ranking: str) -> str:
    if str(politica_ui or "").strip().lower() == "emcash":
        return "EMCASH"
    return _norm_key(ranking or "DIAMANTE")

# ========================================================================
# data/premissas.py
# ========================================================================

# -*- coding: utf-8 -*-
from typing import Any, Dict, Optional

import pandas as pd

# Valores extraídos de excel_extracao_celulas.txt (aba PREMISSAS)
DEFAULT_PREMISSAS: Dict[str, float] = {
    "dire_pre_m": 0.005,      # B2 a.m.
    "dire_pos_m": 0.015,      # B3 a.m.
    "emcash_fin_m": 0.0089,   # B4 a.m. → E2 no Comparador
    "tx_emcash_b5": 0.035,    # B5 (somado a E4 no Excel em E1)
    "ipca_aa": 0.05307,       # B6 a.a. (decimal)
    "renda_f2": 4700.0,
    "renda_f3": 8600.0,
    "renda_f4": 12000.0,
    "vv_f2": 275000.0,
    "vv_f3": 350000.0,
    "vv_f4": 500000.0,
    # Mantém paridade com o app antes da correção Emcash (financiamento Direcional)
    "direcional_fin_aa_pct": 8.16,
}

# Rótulos da coluna A do Excel → chaves internas
_LABEL_MAP = {
    "DIRE PRE": "dire_pre_m",
    "DIRE POS": "dire_pos_m",
    "EMCASH": "emcash_fin_m",
    "TX EMCASH": "tx_emcash_b5",
    "IPCA EMCASH": "ipca_aa",
    "RENDA F2": "renda_f2",
    "RENDA F3": "renda_f3",
    "RENDA F4": "renda_f4",
    "VV F2": "vv_f2",
    "VV F3": "vv_f3",
    "VV F4": "vv_f4",
}


def _to_float(x: Any) -> Optional[float]:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace("%", "").replace("R$", "")
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def premissas_from_dataframe(df: pd.DataFrame | None) -> Dict[str, float]:
    """Interpreta planilha estilo PREMISSAS (col A rótulo, col B valor) ou chave/valor."""
    out = dict(DEFAULT_PREMISSAS)
    if df is None or df.empty:
        return out
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    cols = list(df.columns)
    if len(cols) >= 2:
        c0, c1 = cols[0], cols[1]
        for _, row in df.iterrows():
            label = str(row.get(c0, "")).strip().upper()
            val = _to_float(row.get(c1))
            if val is None:
                continue
            for k_excel, key in _LABEL_MAP.items():
                if k_excel.upper() in label or label == k_excel.upper():
                    out[key] = val
                    break
    return out

# ========================================================================
# core/pro_soluto_comparador.py
# ========================================================================

# -*- coding: utf-8 -*-
from typing import Any, Dict, Mapping, Optional

import pandas as pd



def k3_lambda(renda: float, row: PoliticaPSRow) -> float:
    """K3 = IF(B4 < I1, I2, I3) com faixa e FX da linha POLITICAS."""
    r = float(renda or 0.0)
    if r < float(row.faixa_renda):
        return float(row.fx_renda_1)
    return float(row.fx_renda_2)


def fator_renda_liquido(k3: float) -> float:
    """(K3 - 30%) como no Excel (G14, núcleo da parcela sobre renda)."""
    return max(0.0, float(k3) - OFFSET_LAMBDA)


def parcela_max_g14(renda: float, k3: float) -> float:
    """SIMULADOR PS G14 / C43 linha simples: (K3-30%) * B4."""
    return float(renda or 0.0) * fator_renda_liquido(k3)


def parcela_max_j8(renda: float, k3: float, e1: float) -> float:
    """COMPARADOR J8: B4 * (K3-30%) * (1-E1)."""
    return float(renda or 0.0) * fator_renda_liquido(k3) * (1.0 - float(e1))


def pv_l8_positivo(e2_mensal: float, prazo_k2: int, parcela_j8: float) -> float:
    """
    L8 = -PV(E2, K2, J8) no Excel → valor positivo máximo de PS (PV de anuidade).
    """
    r = float(e2_mensal)
    n = int(prazo_k2 or 0)
    pmt = float(parcela_j8)
    if n <= 0 or pmt <= 0:
        return 0.0
    if abs(r) < 1e-15:
        return float(pmt * n)
    return float(pmt * (1.0 - (1.0 + r) ** (-n)) / r)


def cap_valor_unidade(valor_unidade: float, row: PoliticaPSRow) -> float:
    """POLITICAS col B × valor da unidade."""
    return float(valor_unidade or 0.0) * float(row.prosoluto_pct)


def valor_max_ps_g15(l_comparador: float, cap_politica_vu: float) -> float:
    """MIN(L, cap) — Excel usa int(L) no comparador; usamos floor para valores positivos."""
    lc = float(l_comparador)
    if lc > 0:
        lc = float(int(lc))
    cap = float(cap_politica_vu)
    return min(lc, cap) if lc > 0 else min(0.0, cap)


def parcela_ps_pmt(
    valor_ps: float,
    prazo_meses: int,
    premissas: Optional[Mapping[str, float]],
    politica_ui: str,
) -> float:
    """
    Parcela mensal do PS alinhada à célula **I5** do COMPARADOR TX EMCASH:
    `(PMT(E2, n, PV) × -1) × (1+E1)`.

    **E2** é **sempre** `emcash_fin_m` (**PREMISSAS B4**), igual ao **E2** global do comparador.
    A política de venda (Emcash/Direcional na UI) **não** altera esta taxa; ela só afeta
    tier/POLITICAS em `metricas_pro_soluto`. O financiamento do imóvel continua usando
    `taxa_mensal_financiamento_imobiliario` em outros módulos.

    `politica_ui` mantém compatibilidade de assinatura com a UI; é ignorado para E2.
    """
    _ = politica_ui  # API / Streamlit; I5 não troca E2 com Emcash vs Direcional
    p = dict(DEFAULT_PREMISSAS)
    if premissas:
        p.update({k: float(v) for k, v in premissas.items() if v is not None})
    e4 = excel_e4_mensal(p["ipca_aa"])
    e1 = excel_e1(p["tx_emcash_b5"], e4)
    pv = float(valor_ps or 0.0)
    n = int(prazo_meses or 0)
    if n <= 0 or pv <= 0:
        return 0.0
    e2 = float(p["emcash_fin_m"])
    if e2 <= -1:
        return 0.0
    try:
        # PMT Excel com PV>0 devolve valor negativo; I5 usa (PMT*-1)*(1+E1) → prestação positiva.
        pmt_excel = -pv * (e2 * (1 + e2) ** n) / ((1 + e2) ** n - 1)
        pmt_pos = abs(float(pmt_excel))
    except (ZeroDivisionError, ValueError, OverflowError):
        return 0.0
    return float(pmt_pos * (1.0 + e1))


def metricas_pro_soluto(
    renda: float,
    valor_unidade: float,
    politica_ui: str,
    ranking: str,
    premissas: Optional[Mapping[str, float]] = None,
    df_politicas: Optional[pd.DataFrame] = None,
    ps_cap_estoque: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calcula tetos e valores de referência para exibição/validação na UI.

    E2 no PV (L8) usa sempre emcash_fin_m como no COMPARADOR (célula E2 global).
    """
    p = dict(DEFAULT_PREMISSAS)
    if premissas:
        p.update({k: float(v) for k, v in premissas.items() if v is not None})
    row = resolve_politica_row(politica_ui, ranking, df_politicas)
    e4 = excel_e4_mensal(p["ipca_aa"])
    e1 = excel_e1(p["tx_emcash_b5"], e4)
    k3 = k3_lambda(renda, row)
    j8 = parcela_max_j8(renda, k3, e1)
    g14 = parcela_max_g14(renda, k3)
    e2_comp = float(p["emcash_fin_m"])
    prazo_k2 = int(min(row.parcelas_max, 120.0))
    l8 = pv_l8_positivo(e2_comp, prazo_k2, j8)
    cap_vu = cap_valor_unidade(valor_unidade, row)
    ps_max_calc = valor_max_ps_g15(l8, cap_vu)
    if ps_cap_estoque is not None and float(ps_cap_estoque) > 0:
        ps_max_efetivo = min(ps_max_calc, float(ps_cap_estoque))
    else:
        ps_max_efetivo = ps_max_calc

    return {
        "politica_row": row,
        "k3": k3,
        "e1": e1,
        "parcela_max_j8": j8,
        "parcela_max_g14": g14,
        "pv_l8": l8,
        "cap_valor_unidade": cap_vu,
        "ps_max_comparador_politica": ps_max_calc,
        "ps_max_efetivo": ps_max_efetivo,
        "prazo_ps_politica": prazo_k2,
    }


def parcela_ps_para_valor(
    valor_ps: float,
    prazo_meses: int,
    politica_ui: str,
    premissas: Optional[Mapping[str, float]] = None,
) -> float:
    """Atalho para UI: parcela corrigida dado valor e prazo."""
    return parcela_ps_pmt(valor_ps, prazo_meses, premissas, politica_ui)

# ========================================================================
# core/comparador_emcash.py
# ========================================================================

# -*- coding: utf-8 -*-
from typing import Any, Dict, Mapping, Optional



def valor_ps_ajustado_comparador(ps_total: float) -> float:
    """
    COMPARADOR TX EMCASH!B3:
    IF(B41=0,0.99, B41 + B41*((1+0.5%)^4-1))
    """
    if ps_total is None or float(ps_total) == 0.0:
        return 0.99
    b41 = float(ps_total)
    return b41 + b41 * ((1.005) ** 4 - 1.0)


def _politica_emcash(politica: Any) -> bool:
    s = str(politica or "").strip().upper()
    return "EMCASH" in s


def taxa_mensal_financiamento_imobiliario(
    politica: Any,
    premissas: Optional[Mapping[str, float]] = None,
) -> float:
    """
    Taxa mensal usada no PMT / SAC / PRICE do **financiamento do imóvel**.
    - Emcash: mensal direta B4 (0.0089 no Excel de referência).
    - Direcional: derivada de direcional_fin_aa_pct (padrão 8.16% a.a.).
    """
    p = dict(DEFAULT_PREMISSAS)
    if premissas:
        p.update({k: float(v) for k, v in premissas.items() if v is not None})
    if _politica_emcash(politica):
        return float(p["emcash_fin_m"])
    aa = float(p.get("direcional_fin_aa_pct", 8.16))
    return (1.0 + aa / 100.0) ** (1.0 / 12.0) - 1.0


def taxa_anual_pct_equivalente(taxa_mensal: float) -> float:
    """Converte taxa mensal efetiva em % a.a. equivalente (composta)."""
    return ((1.0 + float(taxa_mensal)) ** 12 - 1.0) * 100.0


def resolver_taxa_financiamento_anual_pct(
    dados_cliente: Mapping[str, Any],
    premissas: Optional[Mapping[str, float]] = None,
) -> float:
    """
    Taxa anual em % compatível com calcular_parcela_financiamento /
    calcular_fluxo_pagamento_detalhado / calcular_comparativo_sac_price.
    """
    i_m = taxa_mensal_financiamento_imobiliario(
        dados_cliente.get("politica", ""),
        premissas,
    )
    return taxa_anual_pct_equivalente(i_m)


def parcela_ps_emcash_pmt(
    valor_ps: float,
    prazo_meses: int,
    premissas: Optional[Mapping[str, float]] = None,
) -> float:
    """
    Espelha COMPARADOR!I5: (PMT(E2, CF2, B41)*-1)*(1+E1)
    Delega a pro_soluto_comparador.parcela_ps_pmt (Emcash).
    """

    return parcela_ps_pmt(valor_ps, prazo_meses, premissas, "Emcash")


def metricas_comparador_tx(
    dados_cliente: Mapping[str, Any],
    premissas: Optional[Mapping[str, float]] = None,
) -> Dict[str, float]:
    """Resumo para debug / UI: taxas e ajustes usados no ramo Emcash."""
    p = dict(DEFAULT_PREMISSAS)
    if premissas:
        p.update({k: float(v) for k, v in premissas.items() if v is not None})
    e4 = excel_e4_mensal(p["ipca_aa"])
    e1 = excel_e1(p["tx_emcash_b5"], e4)
    i_m = taxa_mensal_financiamento_imobiliario(
        dados_cliente.get("politica", ""), p
    )
    return {
        "taxa_mensal_fin_imv": i_m,
        "taxa_anual_fin_imv_pct": taxa_anual_pct_equivalente(i_m),
        "e1_comparador": e1,
        "e4_ipca_mensal": e4,
        "emcash_fin_mensal": float(p["emcash_fin_m"]),
    }

# ========================================================================
# app.py
# ========================================================================

# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
import re
from streamlit_gsheets import GSheetsConnection
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
import json
from pathlib import Path
import pytz
import altair as alt
import folium
from streamlit_folium import st_folium
import math
import json
import urllib.parse
import html as html_std


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
# 0. CATÁLOGO E UTILITÁRIOS (constantes em simulador_dv.config.constants)
# =============================================================================
# --- CATALOGO DE PRODUTOS COMPLETO ---
CATALOGO_PRODUTOS = {
    "CONQUISTA FLORIANÓPOLIS": {
        "video": "https://www.youtube.com/watch?v=oU5SeVbmCsk",
        "lat": -22.8878, "lon": -43.3567,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1FtNq9m06iZ3ZAce1Eu8GXYeaUDhBSiV8/view?usp=drivesdk"},
            {"nome": "Piscina Adulto", "link": "https://drive.google.com/file/d/1ud4Vk3oD2Gmcc9eOEMW-rn-2mIr1zGON/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/187TeBEzv2qbJQfbU8m30g7BDbs5kPYx8/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/1dTFFbyexiIJCk1k4-catyJ_dynvPj7Vj/view?usp=drivesdk"},
            {"nome": "Fitness Externo", "link": "https://drive.google.com/file/d/1pY9CikHmAqYwxBYj5ohLmqNC0S_fzXKu/view?usp=drivesdk"},
            {"nome": "Guarita", "link": "https://drive.google.com/file/d/1lMWl5-1OpjYKDLmX38Du9OQeYmUT-CwC/view?usp=drivesdk"},
            {"nome": "Apartamento Garden", "link": "https://drive.google.com/file/d/1u2pc7a6P4DOPYp69RN0icmOZoTFriuKt/view?usp=drivesdk"},
            {"nome": "Planta Tipo Meio", "link": "https://drive.google.com/file/d/1b4QxziB56rrcxMpgVMMNHN0XnPoKelFP/view?usp=drivesdk"},
            {"nome": "Planta Garden", "link": "https://drive.google.com/file/d/13fzvOhPY8uVlBhmbhCQrAnEbse4wv7MY/view?usp=drivesdk"},
            {"nome": "Masterplan", "link": "https://drive.google.com/file/d/1fR7GFbh9a-J3o3hv21bBbxudiW5-I6pe/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/1u5KoeItcTYVgAfkk5UjqrI83lSjt0i2u/view?usp=drivesdk"}
        ]
    },
    "ITANHANGÁ GREEN": {
        "video": "https://www.youtube.com/watch?v=Lt74juwBMXM",
        "lat": -22.9733, "lon": -43.3364,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1PvfgCc1O6NfPsNpGxjzChduroYoCQGsF/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1tB0lFoYSDuL8pVj8_eArd8edYJ7a-Zd-/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1_WWAQE_286TpbaNizsQVwCjMamahuOft/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/124HX2LthZRYI_FeMvZ9T-6WBVK-M94TT/view?usp=drivesdk"},
            {"nome": "Guarita", "link": "https://drive.google.com/file/d/1C6mF2DS_X1QCYkhfYzCSmd0Ror_S4m3x/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/1_v9Vy03-j5U9lppXubsWtAib4DEAiUCz/view?usp=drivesdk"},
            {"nome": "Planta Garden", "link": "https://drive.google.com/file/d/1etHATpKkP0ctj7H3uhFXHrAfB7xqpai3/view?usp=drivesdk"},
            {"nome": "Masterplan", "link": "https://drive.google.com/file/d/1NXXcLhPiiZiquei9QH8_QM1M19tpXVp8/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/18OdrnhrmHmvv2mu_MskLflGCMBgJQC2r/view?usp=drivesdk"}
        ]
    },
    "MAX NORTE": {
        "video": "https://www.youtube.com/watch?v=cnzn1cpJ4tA",
        "lat": -22.8086, "lon": -43.3633,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1AVdsT4MXMcH81K_EFUS2kgSU9luS6oCg/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1SECUIdrQC62v1Q4J7Rgwlh257PGcfyIB/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1d_33bONdid1qZgwTMieCUQsQ_QX0e5H6/view?usp=drivesdk"},
            {"nome": "Salão Gourmet", "link": "https://drive.google.com/file/d/1U_J6KqdChx3dTFwdPSm-EQHyrKUk4nbe/view?usp=drivesdk"},
            {"nome": "Guarita", "link": "https://drive.google.com/file/d/1KFpxyD0eTgXAJ_Te6b0Jl41s8d0S0Dmk/view?usp=drivesdk"},
            {"nome": "Apartamento", "link": "https://drive.google.com/file/d/1BQXjmuE_EU1WtPpoqhRsQzrHdBKkuY9a/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/1a9f7v6YFbpOhczb7nG_JeGtcgsXi0Fv7/view?usp=drivesdk"},
            {"nome": "Masterplan", "link": "https://drive.google.com/file/d/1s4WwrmqiPxBTq3McM6dae4mauGw3PpI5/view?usp=drivesdk"}
        ]
    },
    "NORTE CLUBE": {
        "video": "https://www.youtube.com/watch?v=ElO6Q95Hsak",
        "lat": -22.8752, "lon": -43.2905,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1CdMMB44Em88E4dmaNyq-YJe4eEX53NEE/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1khrmZKSMV5uhh68tvdE10iM28yxvGBMK/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1EKaLDk6GTJcIbY7VNVXnnurGqxTmhdxi/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/1IpwQYtIKde8EoOoDPGVGwoRmQ73b0ht8/view?usp=drivesdk"},
            {"nome": "Quadra", "link": "https://drive.google.com/file/d/1j-n1kjGXcOzc2cUDl8yYA7drkXNZBrZK/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/1AQc25GcW2-YCBNUIlcRMBVnjFAL1oSuQ/view?usp=drivesdk"},
            {"nome": "Planta Garden", "link": "https://drive.google.com/file/d/1ZL0l-x6ZnLLTFx_DZw7IIi3YeLkumlw3/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/1DMmjq6Mu785xMfuUq0DFcAnLV1LpnW4Z/view?usp=drivesdk"}
        ]
    },
    "CONQUISTA OCEÂNICA": {
        "video": "https://www.youtube.com/watch?v=4g5oy3SCh-A",
        "lat": -22.8711, "lon": -43.0133,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1hIsxtMe-5NyiIIy7nXxFNcndCamuX1pu/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1Q488b06oCll4iwU5l_BgVJEEn4uVneho/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1zQyrd4ZYb45bw76z7cajjZkiHjJnubbY/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/147z9BlYfjqEMc1yvHuosVHLEKATBSvjd/view?usp=drivesdk"},
            {"nome": "Guarita", "link": "https://drive.google.com/file/d/1O6COShsXlNGtzeewOBRnUE45NVNIiOoh/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/14RsOJBM6jYDF4KumRCz1sCzj3Aix-UjT/view?usp=drivesdk"},
            {"nome": "Planta Garden", "link": "https://drive.google.com/file/d/1BdldmlPt_97aAfcl_7YMp5uy7WJgs10U/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/1vD4q4gkD31Nm4qL4pHs3zLytUq3MFfii/view?usp=drivesdk"}
        ]
    },
    "PARQUE IGUAÇU": {
        "video": "https://www.youtube.com/watch?v=PQOA5AS0Sdo",
        "lat": -22.7758, "lon": -43.4861,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1mdp1DBxGd7WpG-1BB67BDLHlJ_EAtj0V/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1TTTiFl605kS0LiztlzXfvn1hRj_X4_Fc/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1jqjS025JccXTkMOP2QXBKAAc-4vKF5SN/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/1UJlpQm5rJqaZrF5DGgTmW8ygNLWpsp2y/view?usp=drivesdk"},
            {"nome": "Churrasqueira", "link": "https://drive.google.com/file/d/1d1vxr_-Nb5A7iyLc_Mn7FqCwBUxwO3oZ/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/1FiSP0QP2EBRRWlYGsgd4ZkyLiqEWn5CG/view?usp=drivesdk"},
            {"nome": "Planta Garden", "link": "https://drive.google.com/file/d/1uVoJkhPvylOMFRcJlR1bsfvBUAVwVVlv/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/1m529O3c6pEz3sD3-Vba1BAUJKzj9XOxg/view?usp=drivesdk"}
        ]
    },
    "SOUL SAMBA": {
        "video": "https://www.youtube.com/watch?v=qTPaarVhHgs",
        "lat": -22.8778, "lon": -43.2778,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1Iv-887JKrY-h6wSktD_SXjeLZM28n4-Y/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/14JNb9eQJLCbBkaIEExDmf9dH6yP3vKKA/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/16FjIZzAVVXouhm8eEwjDbArC8XsX2552/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/1wJszyTa-w1N6pczz2UJx6xi5zlDMhSeU/view?usp=drivesdk"},
            {"nome": "Guarita", "link": "https://drive.google.com/file/d/1MqZBsikoiaDY-TD2Wm759WJV8Ozy-Li7/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/14RtGmEXYyFNkI33WMRD_NFD2M3OdOwj7/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/1-hI2guSTSTHiynWe3QpC-CcXeuf2IhTs/view?usp=drivesdk"}
        ]
    },
    "VERT ALCÂNTARA": {
        "video": "https://www.youtube.com/watch?v=Lag2kS7wFnU",
        "lat": -22.8222, "lon": -43.0031,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1Hk_xywnFmA68J0lcuM6h9qK3GKgFT7Yt/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1pDm2u3z3pKqqqzMkYb93LIceScYzDFs_/view?usp=drivesdk"},
            {"nome": "Coworking", "link": "https://drive.google.com/file/d/1XiffjmMTws-9ciqEhh6FiRI3MYSSROnh/view?usp=drivesdk"},
            {"nome": "Sala de Jogos", "link": "https://drive.google.com/file/d/1hdENx08aVZBQP-df_l2fZOQ4FQF984DL/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/1D_zDCDaQVvK4DBc9UtURZSptGKZsvgb8/view?usp=drivesdk"},
            {"nome": "Planta Garden", "link": "https://drive.google.com/file/d/1C2x7nZoKAJ7DNqsqxIai4wFOW032sTqi/view?usp=drivesdk"}
        ]
    },
    "INN BARRA OLÍMPICA": {
        "video": "https://www.youtube.com/watch?v=SGEJFc3jh5A",
        "lat": -22.9567, "lon": -43.3761,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1ScG09d2xcPblZKQJYlssw-AMSOLmx6qO/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1cYMq0jujtHC_DPUXrNpRf4jYN_83ntiK/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1gaORQ2t3vur097TWHrGL_fF3oqSt6REu/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/1jYIt95E4_k0HhCpTCn7lBEM91G_VJLTF/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/1t-ZAfSHeyYWUgJx-2q00LpU15QSjSinh/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/1CEykILUVyBfz0o73QFdjyIbvpof5P28w/view?usp=drivesdk"}
        ]
    },
    "NOVA CAXIAS FUN": {
        "video": "https://www.youtube.com/watch?v=3P_o4jVWsOI",
        "lat": -22.7303, "lon": -43.3075,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/17YwXWQPvTXWX0bx0sNq9lX8ZN6r3Q7_F/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1jB16KnKTOdxFpj68OqOnnzlPl1ev1gyW/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1-OM3XVNlYgfo2az26feqDfoYCjUxn7-d/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/1DBoZI2zVeycc3KnmKAhwFIK1GkMefb_X/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/1Te0683dB6MeOr_5JbXpEkhkb-Qcu_iBJ/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/14l-h7mPypMoAFq7inaT-azt1CaP_evqF/view?usp=drivesdk"}
        ]
    },
    "NOVA CAXIAS UP": {
        "video": "https://www.youtube.com/watch?v=EbEcZvIdTvY",
        "lat": -22.7303, "lon": -43.3075,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/12I_GnSQVtCp-rdnUu3mUh43fc4qG54Ke/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1cGDJJN79thO85xEyz74TvqIh6h4vsuCl/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/13qIgtrn55FD46nNMOYrr04r9JRvbTpZ0/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/1_lJXmBx02NVA9pjWkR9DGDM6JQbQOkU8/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/1FimZCNjC9Jy4ByW5n2-FOukEqoFGER87/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/1gvehESpzNk4rqhA-bUOW_9YOT8XpEsi1/view?usp=drivesdk"}
        ]
    },
    "RESERVA DO SOL": {
        "video": "https://www.youtube.com/watch?v=Wij9XjG4slM",
        "lat": -22.9536, "lon": -43.3858,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1-RFBc4sQ7Tbo6qwhP3GXZQy3m7_DtFcB/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1HUqoUz1--CdmuZYd0DIvPhlyk9MnDt_O/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1BnEkT8v6OCRdhx624sJRMPfcMjJsU2Tb/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/13xuG8_MJF_yM0Mt9Nnzft10mdGE4KbFn/view?usp=drivesdk"},
            {"nome": "Planta Meio", "link": "https://drive.google.com/file/d/11wX-XPBMHOAqpKZUuwwJpJ_GcsiRxU1c/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/1Cj-EuPHMF86pe7s0nw6XML2esCTd4Nqn/view?usp=drivesdk"}
        ]
    },
    "RESIDENCIAL JERIVÁ": {
        "video": "https://www.youtube.com/watch?v=GdEvqLVXeFw",
        "lat": -22.8944, "lon": -43.5575,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1nzOHc7-n7gZDAFSbdNwDXgnQAJNouRPU/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1R-TYH7oauG_qSFGTZbFzHjSaPkRcCEHC/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1m4AHz4E5id5O5r5bI1-5zckXK5pPZ43s/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/12HxPpDvQeYhamousSPF976-7hb2WDbFc/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/1RnmcwKnMxy7jL5AbPUPFJToWV_O1PJV-/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/1i8X-05E1NWAOxAgSQ6K1aX70NDXUlIUN/view?usp=drivesdk"}
        ]
    },
    "RESIDENCIAL LARANJEIRAS": {
        "video": "https://www.youtube.com/watch?v=jmV1RHkRlZ4",
        "lat": -22.8944, "lon": -43.5575,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/19Eq2qFk5fx8AnG-ooWq6SsGGmQKsIvvb/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1v9zn2HdtjNWBKlrxAKFljUkCD7SHSupB/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1xVLehaJSdy1xvz6eELz3I8VtSPoQ8C-c/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/1WItdv2DY59gu-yzW1RXPykdCU5i2mdb2/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/1noEQfz_FQ7w3s7oopg8FQwhvfUfccjuT/view?usp=drivesdk"}
        ]
    },
    "VIVA VIDA REALENGO": {
        "video": "https://www.youtube.com/watch?v=cfRvstasGaw",
        "lat": -22.8797, "lon": -43.4286,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1plxTT4MmRUP4xUl_300Rz7eFSH36uLFw/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/1PT-z4PFD_VUTtxrPKoXJJ-lOL9ud17FQ/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1j51NJUlnu7M4T1Bwax7UfmorEhv5dYu4/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/17xl-SYLLtpyIxb82qkQAKHX1c4peLLcq/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/1-UfmBvETRRuvuq5R6rKA3Y_9s4xBzTc6/view?usp=drivesdk"}
        ]
    },
    "RECANTO CLUBE": {
        "video": "https://www.youtube.com/watch?v=7K3UUEIOT-8",
        "lat": -22.9694, "lon": -43.5936,
        "imagens": [
            {"nome": "Fachada", "link": "https://drive.google.com/file/d/1pfvsC4S15n4HbtWeNp2crJcs0PcH5MRV/view?usp=drivesdk"},
            {"nome": "Piscina", "link": "https://drive.google.com/file/d/19SDMm-pzyxBfK_jTK4Z5gp2-aLlW_Lxj/view?usp=drivesdk"},
            {"nome": "Playground", "link": "https://drive.google.com/file/d/1aOW9ErNYvbdmVPeyCKYdWH1Z32joTliw/view?usp=drivesdk"},
            {"nome": "Salão de Festas", "link": "https://drive.google.com/file/d/1bI4pk6j63uWBMmQnz07cDTNrB3YFCrpS/view?usp=drivesdk"},
            {"nome": "Planta Tipo", "link": "https://drive.google.com/file/d/1fOM-Ul_JZwjELDMkmwkHE_JN669V9-ob/view?usp=drivesdk"},
            {"nome": "Ficha Técnica", "link": "https://drive.google.com/file/d/1FT0IYF1VBWUX2iSxGqK7VuK-Z7sszSUK/view?usp=drivesdk"}
        ]
    }
}

def _load_catalogo_galeria():
    """Carrega catálogo de produtos (vídeos, mapa, imagens Drive) de JSON se existir (fonte única com app Flask)."""
    _here = os.path.dirname(os.path.abspath(__file__))
    _base = _here  # monólito: ficheiro na raiz do repositório (equiv. ex. pai de simulador_dv/)
    for path in [
        os.path.join(_base, "static", "img", "galeria", "catalogo_produtos.json"),
        os.path.join(_base, "catalogo_produtos.json"),
        os.path.join(_here, "static", "img", "galeria", "catalogo_produtos.json"),
    ]:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}

# Se existir JSON do catálogo, usa como fonte (sobrescreve); senão mantém CATALOGO_PRODUTOS in-code
_catalogo_json = _load_catalogo_galeria()
if _catalogo_json:
    CATALOGO_PRODUTOS.update(_catalogo_json)

def fmt_br(valor):
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

def limpar_cpf_visual(valor):
    if pd.isnull(valor) or valor == "": return ""
    v_str = str(valor).strip()
    # Remove decimal se existir
    if v_str.endswith('.0'): v_str = v_str[:-2]
    v_nums = re.sub(r'\D', '', v_str)
    # Garante 11 digitos preenchendo zeros a esquerda
    if v_nums: return v_nums.zfill(11)
    return ""

def formatar_cpf_saida(valor):
    v = limpar_cpf_visual(valor)
    if len(v) == 11:
        return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
    return v

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

# Função para máscara automática de CPF
def aplicar_mascara_cpf(valor):
    # Remove tudo que não é dígito
    v = re.sub(r'\D', '', str(valor))
    # Limita a 11 dígitos
    v = v[:11]
    # Aplica máscara progressiva
    if len(v) > 9:
        return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
    elif len(v) > 6:
        return f"{v[:3]}.{v[3:6]}.{v[6:]}"
    elif len(v) > 3:
        return f"{v[:3]}.{v[3:]}"
    return v

def safe_float_convert(val):
    if pd.isnull(val) or val == "": return 0.0
    if isinstance(val, (int, float, np.number)): return float(val)
    s = str(val).replace('R$', '').strip()
    try:
        return float(s)
    except:
        if ',' in s:
            s = s.replace('.', '').replace(',', '.')
        else:
            if s.count('.') >= 1:
                s = s.replace('.', '')
        try: return float(s)
        except: return 0.0

def texto_moeda_para_float(s, default=0.0):
    """Converte texto livre (BR ou simples) em float; vazio → default."""
    if s is None:
        return default
    if isinstance(s, (int, float, np.number)):
        return float(s)
    t = str(s).strip()
    if t == "":
        return default
    return safe_float_convert(t)

def texto_inteiro(s, default=None, min_v=None, max_v=None):
    """Converte texto em int opcionalmente limitado a [min_v, max_v]. Inválido/vazio → default."""
    if s is None:
        return default
    if isinstance(s, int) and not isinstance(s, bool):
        n = s
    elif isinstance(s, float):
        n = int(s)
    else:
        t0 = str(s).strip()
        if t0 == "":
            return default
        xf = safe_float_convert(t0)
        n = int(xf)
    if min_v is not None:
        n = max(min_v, n)
    if max_v is not None:
        n = min(max_v, n)
    return n

def float_para_campo_texto(v, vazio_se_zero=True):
    """Valor numérico para exibir em campo de texto; zero pode virar string vazia."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return ""
    if vazio_se_zero and abs(x) < 1e-9:
        return ""
    return fmt_br(x)

def calcular_cor_gradiente(valor):
    valor = max(0, min(100, valor))
    f = valor / 100.0
    r = int(227 + (0 - 227) * f)
    g = int(6 + (44 - 6) * f)
    b = int(19 + (93 - 19) * f)
    return f"rgb({r},{g},{b})"

def calcular_comparativo_sac_price(valor, meses, taxa_anual):
    if valor is None or valor <= 0 or meses <= 0:
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
    if valor_financiado is None or valor_financiado <= 0 or meses <= 0: return 0.0
    i_mensal = (1 + taxa_anual_pct/100)**(1/12) - 1
    if sistema == "PRICE":
        try: return valor_financiado * (i_mensal * (1 + i_mensal)**meses) / ((1 + i_mensal)**meses - 1)
        except: return 0.0
    else:
        amortizacao = valor_financiado / meses
        juros = valor_financiado * i_mensal
        return amortizacao + juros

# Função Auxiliar para Projeção de Fluxo COMPLETA e CORRIGIDA
def calcular_fluxo_pagamento_detalhado(valor_fin, meses_fin, taxa_anual, sistema, ps_mensal, meses_ps, atos_dict):
    i_mensal = (1 + taxa_anual/100)**(1/12) - 1
    fluxo = []
    saldo_devedor = valor_fin
    amortizacao_sac = valor_fin / meses_fin if meses_fin > 0 else 0
    
    pmt_price = 0
    if sistema == 'PRICE' and meses_fin > 0:
        pmt_price = valor_fin * (i_mensal * (1 + i_mensal)**meses_fin) / ((1 + i_mensal)**meses_fin - 1)

    # Gera fluxo até o final do financiamento
    # LÓGICA SOLICITADA:
    # Mês 1: Parcela Fin + Parcela PS + Ato 0 (Imediato)
    # Mês 2: Parcela Fin + Parcela PS + Ato 30
    # Mês 3: Parcela Fin + Parcela PS + Ato 60
    # Mês 4: Parcela Fin + Parcela PS + Ato 90
    # Mês 5+: Parcela Fin + Parcela PS (até fim do PS)
    # Pós PS: Apenas Parcela Fin

    # Mapa de ordem de empilhamento: Financiamento (base) -> Pro Soluto -> Ato (topo)
    order_map = {'Financiamento': 1, 'Pro Soluto': 2, 'Entrada/Ato': 3}

    for m in range(1, meses_fin + 1):
        if sistema == 'SAC':
            juros = saldo_devedor * i_mensal
            parc_fin = amortizacao_sac + juros
            saldo_devedor -= amortizacao_sac
        else: # PRICE
            parc_fin = pmt_price
            juros = saldo_devedor * i_mensal
            amort = pmt_price - juros
            saldo_devedor -= amort
        
        # Parcela Pro Soluto
        parc_ps = ps_mensal if m <= meses_ps else 0
        
        # Atos - Mapeamento direto por mês
        val_ato = 0.0
        label_ato = ""

        if m == 1:
            val_ato = atos_dict.get('ato_final', 0.0) # Ato Imediato
            if val_ato > 0: label_ato = "Ato"
        elif m == 2:
            val_ato = atos_dict.get('ato_30', 0.0)
            if val_ato > 0: label_ato = "Ato 30"
        elif m == 3:
            val_ato = atos_dict.get('ato_60', 0.0)
            if val_ato > 0: label_ato = "Ato 60"
        elif m == 4:
            val_ato = atos_dict.get('ato_90', 0.0)
            if val_ato > 0: label_ato = "Ato 90"
        
        # Adicionar componentes separados para o gráfico empilhado
        # Financiamento
        fluxo.append({
            'Mês': int(m),
            'Valor': float(parc_fin),
            'Tipo': 'Financiamento',
            'Ordem_Tipo': order_map['Financiamento'],
            'Total': float(parc_fin + parc_ps + val_ato)
        })
        
        # Pro Soluto (se houver)
        if parc_ps > 0:
            fluxo.append({
                'Mês': int(m),
                'Valor': float(parc_ps),
                'Tipo': 'Pro Soluto',
                'Ordem_Tipo': order_map['Pro Soluto'],
                'Total': float(parc_fin + parc_ps + val_ato)
            })
            
        # Atos (se houver)
        if val_ato > 0:
            fluxo.append({
                'Mês': int(m),
                'Valor': float(val_ato),
                'Tipo': 'Entrada/Ato',
                'Ordem_Tipo': order_map['Entrada/Ato'],
                'Total': float(parc_fin + parc_ps + val_ato)
            })
    
    return pd.DataFrame(fluxo)

def formatar_link_drive(url):
    """
    Retorna apenas a URL direta se for Google Drive para usar no modal customizado.
    """
    if "drive.google.com" in url and "/d/" in url:
        try:
            file_id = url.split("/d/")[1].split("/")[0]
            # Link direto para visualização raw (export=view)
            full_link = f"https://drive.google.com/uc?export=view&id={file_id}"
            return full_link
        except:
            return url
    return url

def scroll_to_top():
    js = """<script>var body = window.parent.document.querySelector(".main"); if (body) { body.scrollTop = 0; } window.scrollTo(0, 0);</script>"""
    st.components.v1.html(js, height=0)

# =============================================================================
# 1. CARREGAMENTO DE DADOS
# =============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados_sistema():
    try:
        if "connections" not in st.secrets:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), dict(DEFAULT_PREMISSAS)
        conn = st.connection("gsheets", type=GSheetsConnection)
        def limpar_moeda(val): return safe_float_convert(val)

        # Login removido — não lê mais BD Logins (compat.: 4.º retorno permanece DataFrame vazio)
        df_logins = pd.DataFrame(columns=['Email', 'Senha', 'Nome', 'Cargo', 'Imobiliaria', 'Telefone'])

        # 1. SIMULAÇÕES (CADASTROS)
        try: 
            df_cadastros = conn.read(spreadsheet=ID_GERAL, worksheet="BD Simulações")
            # Garantir formato correto do CPF se existir
            if 'CPF' in df_cadastros.columns:
                df_cadastros['CPF'] = df_cadastros['CPF'].apply(limpar_cpf_visual)
        except: 
            df_cadastros = pd.DataFrame()
        
        # 2. POLITICAS (Pro Soluto — comparador)
        df_politicas = pd.DataFrame()
        for ws_pol in ("POLITICAS", "BD Politicas", "BD Políticas"):
            try:
                df_politicas = conn.read(spreadsheet=ID_GERAL, worksheet=ws_pol)
                df_politicas.columns = [str(c).strip() for c in df_politicas.columns]
                if not df_politicas.empty:
                    break
            except Exception:
                continue

        # 3. FINANCIAMENTOS
        try:
            df_finan = conn.read(spreadsheet=ID_GERAL, worksheet="BD Financiamentos")
            df_finan.columns = [str(c).strip() for c in df_finan.columns]
            for col in df_finan.columns: df_finan[col] = df_finan[col].apply(limpar_moeda)
        except: 
            df_finan = pd.DataFrame()

        # 4. ESTOQUE
        try:
            # Tenta carregar os dados
            df_raw = conn.read(spreadsheet=ID_GERAL, worksheet="BD Estoque Filtrada")
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            
            # --- CORREÇÃO: VERIFICAR COLUNA DE VALOR DE VENDA ---
            # Se a coluna 'Valor de Venda' não existir (pois pode não ter propagado ou estar em outra aba),
            # usamos 'Valor Comercial Mínimo' como fallback para garantir que o estoque seja encontrado.
            col_valor_venda = 'Valor de Venda'
            if 'Valor de Venda' not in df_raw.columns:
                if 'Valor Comercial Mínimo' in df_raw.columns:
                    col_valor_venda = 'Valor Comercial Mínimo'
            
            mapa_estoque = {
                'Nome do Empreendimento': 'Empreendimento',
                col_valor_venda: 'Valor de Venda', # Usa a coluna detectada
                'Status da unidade': 'Status',
                'Identificador': 'Identificador',
                'Bairro': 'Bairro',
                'Valor de Avaliação Bancária': 'Valor de Avaliação Bancária', 
                'PS EmCash': 'PS_EmCash',
                'PS Diamante': 'PS_Diamante',
                'PS Ouro': 'PS_Ouro',
                'PS Prata': 'PS_Prata',
                'PS Bronze': 'PS_Bronze',
                'PS Aço': 'PS_Aco',
                'Previsão de expedição do habite-se': 'Data Entrega', # Alterado para Previsão de expedição do habite-se
                'Área privativa total': 'Area',
                'Tipo Planta/Área': 'Tipologia',
                'Endereço': 'Endereco',
                'Folga Volta ao Caixa': 'Volta_Caixa_Ref' # Mapeamento corrigido
            }
            
            # Garantir correspondência mesmo com espaços
            # Normalizar colunas do raw para sem espaços nas pontas
            df_raw.columns = [c.strip() for c in df_raw.columns]
            
            # Ajustar chaves do mapa para bater com colunas limpas
            mapa_ajustado = {}
            for k, v in mapa_estoque.items():
                if k.strip() in df_raw.columns:
                    mapa_ajustado[k.strip()] = v
            
            df_estoque = df_raw.rename(columns=mapa_ajustado)
            
            # Garantir colunas essenciais
            if 'Valor de Venda' not in df_estoque.columns: df_estoque['Valor de Venda'] = 0.0
            if 'Valor de Avaliação Bancária' not in df_estoque.columns: df_estoque['Valor de Avaliação Bancária'] = df_estoque['Valor de Venda']
            if 'Status' not in df_estoque.columns: df_estoque['Status'] = 'Disponível'
            if 'Empreendimento' not in df_estoque.columns: df_estoque['Empreendimento'] = 'N/A'
            if 'Data Entrega' not in df_estoque.columns: df_estoque['Data Entrega'] = ''
            if 'Area' not in df_estoque.columns: df_estoque['Area'] = ''
            if 'Tipologia' not in df_estoque.columns: df_estoque['Tipologia'] = ''
            if 'Endereco' not in df_estoque.columns: df_estoque['Endereco'] = ''
            if 'Volta_Caixa_Ref' not in df_estoque.columns: df_estoque['Volta_Caixa_Ref'] = 0.0 # Garantir coluna nova
            
            # Conversões numéricas
            df_estoque['Valor de Venda'] = df_estoque['Valor de Venda'].apply(limpar_moeda)
            df_estoque['Valor de Avaliação Bancária'] = df_estoque['Valor de Avaliação Bancária'].apply(limpar_moeda)
            df_estoque['Volta_Caixa_Ref'] = df_estoque['Volta_Caixa_Ref'].apply(limpar_moeda) # Converter nova coluna
            
            # Limpar colunas de PS
            cols_ps = ['PS_EmCash', 'PS_Diamante', 'PS_Ouro', 'PS_Prata', 'PS_Bronze', 'PS_Aco']
            for c in cols_ps:
                if c in df_estoque.columns:
                    df_estoque[c] = df_estoque[c].apply(limpar_moeda)
                else:
                    df_estoque[c] = 0.0
            
            # Tratamento de Status (NÃO FILTRA MAIS)
            if 'Status' in df_estoque.columns:
                 df_estoque['Status'] = df_estoque['Status'].astype(str).str.strip()

            # Filtros básicos (Mantendo apenas valor > 1000)
            df_estoque = df_estoque[(df_estoque['Valor de Venda'] > 1000)].copy()
            if 'Empreendimento' in df_estoque.columns:
                 df_estoque = df_estoque[df_estoque['Empreendimento'].notnull()]
            
            if 'Identificador' not in df_estoque.columns: 
                df_estoque['Identificador'] = df_estoque.index.astype(str)
            if 'Bairro' not in df_estoque.columns: 
                df_estoque['Bairro'] = 'Rio de Janeiro'

            # Extração de Bloco/Andar/Apto para ordenação
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
            
            if 'Empreendimento' in df_estoque.columns:
                df_estoque['Empreendimento'] = df_estoque['Empreendimento'].astype(str).str.strip()
            if 'Bairro' in df_estoque.columns:
                df_estoque['Bairro'] = df_estoque['Bairro'].astype(str).str.strip()
                                                                  
        except: 
            df_estoque = pd.DataFrame(columns=['Empreendimento', 'Valor de Venda', 'Status', 'Identificador', 'Bairro', 'Valor de Avaliação Bancária'])

        premissas_dict = dict(DEFAULT_PREMISSAS)
        for ws_prem in ("BD Premissas", "PREMISSAS"):
            try:
                df_pr = conn.read(spreadsheet=ID_GERAL, worksheet=ws_prem)
                premissas_dict = premissas_from_dataframe(df_pr)
                break
            except Exception:
                continue

        return df_finan, df_estoque, df_politicas, df_logins, df_cadastros, premissas_dict
    except Exception as e:
        st.error(f"Erro dados: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), dict(DEFAULT_PREMISSAS)

# =============================================================================
# 2. MOTOR E FUNÇÕES
# =============================================================================

class MotorRecomendacao:
    def __init__(self, df_finan, df_estoque, df_politicas):
        self.df_finan = df_finan
        self.df_estoque = df_estoque
        self.df_politicas = df_politicas # Mantido apenas para compatibilidade, não usado logicamente

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

    def calcular_poder_compra(self, renda, finan, fgts_sub, val_ps_limite):
        return (2 * renda) + finan + fgts_sub + val_ps_limite, val_ps_limite

_DIR_SIM_APP = Path(__file__).resolve().parent


def _resolver_png_raiz(nome: str) -> Path | None:
    """Procura PNG/JPG pelo nome exato na pasta do app, assets/ ou raiz do repo."""
    for base in (_DIR_SIM_APP, _DIR_SIM_APP.parent):
        for sub in ("", "assets"):
            rel = Path(sub) / nome if sub else Path(nome)
            p = base / rel
            if p.is_file():
                return p
    return None


def _resolver_imagem_fundo_local(nome: str) -> Path | None:
    """JPG/PNG: nome exato, stem+ext ou pasta assets/ (app e pai do repo)."""
    for base in (_DIR_SIM_APP, _DIR_SIM_APP.parent):
        for sub in ("", "assets"):
            root = base / sub if sub else base
            p = root / nome
            if p.is_file():
                return p
            stem = Path(nome).stem
            for ext in (".jpg", ".jpeg", ".JPG", ".JPEG", ".png", ".PNG"):
                p2 = root / f"{stem}{ext}"
                if p2.is_file():
                    return p2
    return None


def _css_url_fundo_simulador() -> str:
    """Data-URL com fundo_cadastrorh (ficha Vendas RJ); senão fallback neutro."""
    p = _resolver_imagem_fundo_local(FUNDO_CADASTRO_ARQUIVO)
    if p and p.is_file():
        try:
            raw = p.read_bytes()
            suf = p.suffix.lower()
            mime = "image/jpeg" if suf in (".jpg", ".jpeg") else "image/png"
            b64 = base64.b64encode(raw).decode("ascii")
            return f"data:{mime};base64,{b64}"
        except OSError:
            pass
    return (
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab"
        "?auto=format&fit=crop&w=1920&q=80"
    )


def _page_icon_streamlit():
    """Ícone da aba: 502.57_LOGO D_COR_V3F.png (ficha), senão favicon.png legado, senão URL."""
    p = _resolver_png_raiz(FAVICON_ARQUIVO)
    if p is not None and Image:
        try:
            return Image.open(p)
        except Exception:
            return str(p)
    if p is not None:
        return str(p)
    if os.path.exists("favicon.png") and Image:
        try:
            return Image.open("favicon.png")
        except Exception:
            pass
    return URL_FAVICON_RESERVA


def _src_logo_topo_header() -> str:
    """Logo do cabeçalho: 502.57_LOGO DIRECIONAL_V2F-01.png em data-URL; senão legado; senão URL."""
    p = _resolver_png_raiz(LOGO_TOPO_ARQUIVO)
    if p and p.is_file():
        try:
            suf = p.suffix.lower()
            mime = (
                "image/png"
                if suf == ".png"
                else "image/jpeg"
                if suf in (".jpg", ".jpeg")
                else "image/png"
            )
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{b64}"
        except OSError:
            pass
    if os.path.exists("favicon.png"):
        try:
            with open("favicon.png", "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
        except OSError:
            pass
    return URL_LOGO_DIRECIONAL_BIG


def configurar_layout():
    favicon = _page_icon_streamlit()
    st.set_page_config(
        page_title="Simulador Direcional Elite",
        page_icon=favicon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    bg_url = _css_url_fundo_simulador()
    st.markdown(f"""
        <style>
        /* Duas famílias: Montserrat (títulos / marca) + Inter (corpo e UI) */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@600;700;800&display=swap');
        @keyframes simFadeIn {{
            from {{ opacity: 0; transform: translateY(14px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        html, body, :root, [data-testid="stApp"] {{
            color-scheme: light !important;
        }}
        /* Indicador "Running…" + nome da função no topo (Streamlit stStatusWidget) */
        [data-testid="stStatusWidget"] {{
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            max-height: 0 !important;
            overflow: hidden !important;
            pointer-events: none !important;
        }}
        /* Spinner de cache (redundante com show_spinner=False, mas reforça se a UI mudar) */
        [data-testid="stSpinner"].stCacheSpinner {{
            display: none !important;
        }}
        /* Sidebar oculta (navegação/galeria/histórico removidos da UI) */
        section[data-testid="stSidebar"] {{ display: none !important; }}
        [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
        div[data-testid="collapsedControl"] {{ display: none !important; }}

        html, body {{
            font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
            font-feature-settings: 'kern' 1, 'liga' 1;
            -webkit-font-smoothing: antialiased;
            color: {COR_TEXTO_LABEL};
            background: transparent !important;
            background-color: transparent !important;
        }}
        .stApp,
        [data-testid="stApp"] {{
            background:
                linear-gradient(135deg, rgba({RGB_AZUL_CSS}, 0.82) 0%, rgba(30, 58, 95, 0.55) 38%, rgba({RGB_VERMELHO_CSS}, 0.22) 72%, rgba(15, 23, 42, 0.45) 100%),
                url("{bg_url}") center / cover no-repeat !important;
            background-attachment: scroll !important;
            background-color: transparent !important;
        }}
        [data-testid="stAppViewContainer"] {{
            background: transparent !important;
            background-color: transparent !important;
            font-family: 'Inter', system-ui, sans-serif;
            color: {COR_TEXTO_LABEL};
        }}
        header[data-testid="stHeader"],
        [data-testid="stHeader"] {{
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
        }}
        [data-testid="stHeader"] > div,
        [data-testid="stHeader"] header {{
            background: transparent !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }}
        [data-testid="stDecoration"] {{
            background: transparent !important;
            background-color: transparent !important;
        }}
        [data-testid="stToolbar"] {{
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            color: rgba(255, 255, 255, 0.92) !important;
        }}
        [data-testid="stToolbar"] button,
        [data-testid="stToolbar"] a {{
            color: rgba(255, 255, 255, 0.92) !important;
            background: transparent !important;
        }}
        [data-testid="stToolbar"] svg {{
            fill: currentColor !important;
        }}
        [data-testid="stHeader"] button {{
            background: transparent !important;
        }}
        [data-testid="stToolbar"] button:hover,
        [data-testid="stToolbar"] a:hover,
        [data-testid="stHeader"] button:hover {{
            background: rgba(255, 255, 255, 0.12) !important;
        }}
        [data-testid="stMain"] {{
            padding-left: clamp(14px, 4vw, 48px) !important;
            padding-right: clamp(14px, 4vw, 48px) !important;
            padding-top: clamp(12px, 3vh, 32px) !important;
            padding-bottom: clamp(14px, 4vh, 40px) !important;
            box-sizing: border-box !important;
        }}
        section.main > div {{
            padding-top: 0.25rem !important;
            padding-bottom: 0.35rem !important;
        }}

        /* SCROLL HORIZONTAL */
        .scrolling-wrapper {{
            display: flex;
            flex-wrap: nowrap;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            gap: 20px;
            padding-bottom: 20px;
            margin-bottom: 20px;
            width: 100%;
        }}
        
        .scrolling-wrapper .card-item {{
            flex: 0 0 auto;
            width: 320px; /* Largura ajustada para caber mais info */
        }}
        
        /* SCROLL IMAGENS */
        .scrolling-images {{
            display: flex;
            flex-wrap: nowrap;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            gap: 15px;
            padding-bottom: 15px;
            width: 100%;
        }}
        .scrolling-images img {{
            height: 250px;
            width: auto;
            border-radius: 12px;
            cursor: pointer;
            transition: transform 0.2s;
            border: 1px solid #eee;
        }}
        .scrolling-images img:hover {{
            transform: scale(1.02);
            border-color: {COR_AZUL_ESC};
        }}
        
        /* MASTERPLAN PLACEHOLDER */
        .masterplan-placeholder {{
            height: 250px;
            width: 350px;
            background-color: #f1f5f9;
            border: 2px dashed #cbd5e1;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #64748b;
            font-weight: 700;
            font-size: 0.9rem;
            flex: 0 0 auto;
            transition: all 0.2s;
        }}
        .masterplan-placeholder:hover {{
            border-color: {COR_AZUL_ESC};
            color: {COR_AZUL_ESC};
            background-color: #e2e8f0;
        }}
        
        /* LIGHTBOX MODAL CSS */
        .modal {{
            display: none; 
            position: fixed; 
            z-index: 99999; 
            padding-top: 20px; 
            left: 0;
            top: 0;
            width: 100%; 
            height: 100%; 
            overflow: hidden; 
            background-color: rgba(0,0,0,0.95);
        }}
        .modal-content {{
            margin: auto;
            display: block;
            width: auto;
            max-width: 90%;
            max-height: 90vh;
            object-fit: contain;
        }}
        .close {{
            position: absolute;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            transition: 0.3s;
            cursor: pointer;
            z-index: 100000;
        }}
        .close:hover,
        .close:focus {{
            color: #bbb;
            text-decoration: none;
            cursor: pointer;
        }}
        .prev, .next {{
            cursor: pointer;
            position: absolute;
            top: 50%;
            width: auto;
            padding: 16px;
            margin-top: -50px;
            color: white;
            font-weight: bold;
            font-size: 30px;
            transition: 0.6s ease;
            border-radius: 0 3px 3px 0;
            user-select: none;
            -webkit-user-select: none;
        }}
        .next {{ right: 0; border-radius: 3px 0 0 3px; }}
        .prev {{ left: 0; border-radius: 3px 0 0 3px; }}
        .prev:hover, .next:hover {{ background-color: rgba(0,0,0,0.8); }}

        h1, h2, h3, h4 {{
            font-family: 'Montserrat', 'Inter', sans-serif !important;
            text-align: center !important;
            color: {COR_AZUL_ESC} !important;
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1.25;
        }}

        .stMarkdown p, .stText, label, .stSelectbox label, .stTextInput label, .stNumberInput label {{
            color: {COR_TEXTO_LABEL} !important;
        }}
        [data-testid="stWidgetLabel"] label,
        [data-testid="stWidgetLabel"] p {{
            color: {COR_TEXTO_LABEL} !important;
        }}
        div[data-testid="stMarkdown"] p {{ color: #334155; line-height: 1.55; }}

        .block-container {{
            max-width: 1400px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            margin-top: clamp(4px, 1vh, 14px) !important;
            margin-bottom: clamp(4px, 1vh, 14px) !important;
            padding: 1.45rem 2rem 1.55rem 2rem !important;
            background: rgba(255, 255, 255, 0.78) !important;
            backdrop-filter: blur(18px) saturate(1.12);
            -webkit-backdrop-filter: blur(18px) saturate(1.12);
            border-radius: 24px !important;
            border: 1px solid rgba(255, 255, 255, 0.45) !important;
            box-shadow:
                0 4px 6px -1px rgba({RGB_AZUL_CSS}, 0.06),
                0 24px 48px -12px rgba({RGB_AZUL_CSS}, 0.18),
                inset 0 1px 0 rgba(255, 255, 255, 0.55) !important;
            animation: simFadeIn 0.65s cubic-bezier(0.22, 1, 0.36, 1) both;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 16px !important;
            background: transparent !important;
        }}

        /* Títulos de conteúdo — hierarquia clara, só Montserrat + Inter herdada */
        .stMarkdown h1 {{ font-size: clamp(1.5rem, 2.5vw, 1.85rem) !important; text-align: center; margin-bottom: 0.45rem !important; font-weight: 800 !important; }}
        .stMarkdown h2 {{ font-size: clamp(1.28rem, 2vw, 1.5rem) !important; text-align: center; margin-bottom: 0.45rem !important; font-weight: 700 !important; color: {COR_AZUL_ESC} !important; }}
        .stMarkdown h3 {{ font-size: clamp(1.12rem, 1.8vw, 1.28rem) !important; text-align: center; margin-bottom: 0.4rem !important; font-weight: 700 !important; }}
        .stMarkdown h4 {{ font-size: 1.05rem !important; margin-bottom: 0.35rem !important; font-weight: 700 !important; }}
        .stMarkdown h5 {{ font-size: 0.95rem !important; margin-bottom: 0.3rem !important; font-weight: 600 !important; color: {COR_TEXTO_MUTED} !important; }}
        [data-testid="stCaption"] {{
            font-family: 'Inter', sans-serif !important;
            color: #475569 !important;
            font-size: 0.9rem !important;
            line-height: 1.5 !important;
        }}

        div[data-baseweb="input"] {{
            border-radius: 10px !important;
            border: 1px solid #e2e8f0 !important;
            background-color: {COR_INPUT_BG} !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }}

        div[data-baseweb="input"]:focus-within {{
            border-color: rgba({RGB_AZUL_CSS}, 0.35) !important;
            box-shadow: 0 0 0 3px rgba({RGB_AZUL_CSS}, 0.08) !important;
            background-color: {COR_INPUT_BG} !important;
        }}

        /* Esconder botões + e - dos number inputs (apenas digitação) */
        div[data-testid="stNumberInput"] button {{
            display: none !important;
        }}
        div[data-testid="stNumberInput"] div[data-baseweb="input"],
        div[data-testid="stTextInput"] div[data-baseweb="input"],
        div[data-testid="stDateInput"] div[data-baseweb="input"],
        div[data-baseweb="select"] {{
            background-color: #f0f2f6 !important;
        }}

        /* --- ALTURA UNIFICADA 48px --- */
        .stTextInput input, .stNumberInput input, .stDateInput input, div[data-baseweb="select"] > div {{
            height: 48px !important;
            min-height: 48px !important;
            padding: 0 15px !important;
            color: {COR_TEXTO_LABEL} !important;
            font-size: 1rem !important;
            line-height: 48px !important;
            text-align: left !important;
            display: flex !important;
            align-items: center !important;
        }}
        div[data-testid="stNumberInput"] div[data-baseweb="input"] {{
            height: 48px !important;
            min-height: 48px !important;
            display: flex !important;
            align-items: center !important;
        }}

        div[data-baseweb="select"] span {{
            text-align: left !important;
            display: flex !important;
            align-items: center !important;
            height: 100% !important;
        }}

        div[data-testid="stDateInput"] > div, div[data-baseweb="select"] > div {{
            background-color: #f0f2f6 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            display: flex;
            align-items: center;
        }}

        div[data-testid="stDateInput"] div[data-baseweb="input"] {{
            border: none !important;
            background-color: transparent !important;
        }}

        .stButton button {{
            font-family: 'Inter', system-ui, sans-serif;
            border-radius: 12px !important;
            padding: 0 20px !important;
            width: 100% !important;
            height: 60px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 1rem !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }}
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px -6px rgba({RGB_AZUL_CSS}, 0.25) !important;
        }}
        .stButton button:active {{
            transform: scale(0.98);
        }}

        div[data-testid="column"] .stButton button, [data-testid="stSidebar"] .stButton button {{
             min-height: 48px !important;
             height: 48px !important;
             font-size: 0.9rem !important;
        }}

        /* Botões primários = gradiente vermelho (ficha Vendas RJ) */
        .stButton button[kind="primary"] {{
            background: linear-gradient(180deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%) !important;
            color: #ffffff !important;
            border: none !important;
        }}
        .stButton button[kind="primary"]:hover {{
            background: linear-gradient(180deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%) !important;
            box-shadow: 0 8px 22px -5px rgba({RGB_VERMELHO_CSS}, 0.45) !important;
        }}

        /* Botões secundários (limpar ×, outros) = cinza; Voltar = azul via .btn-azul-anchor */
        .stButton button:not([kind="primary"]) {{
            background: #f0f2f6 !important;
            color: {COR_AZUL_ESC} !important;
            border: 1px solid #e2e8f0 !important;
        }}
        .stButton button:not([kind="primary"]):hover {{
            border-color: #cbd5e1 !important;
            color: {COR_AZUL_ESC} !important;
            background: #e2e8f0 !important;
        }}

        /* Voltar = azul direcional (marcador data-btn-azul antes do botão) */
        div[data-testid="stMarkdown"]:has([data-btn-azul]) + div[data-testid="stButton"] button {{
            background: {COR_AZUL_ESC} !important;
            color: #ffffff !important;
            border: none !important;
        }}
        div[data-testid="stMarkdown"]:has([data-btn-azul]) + div[data-testid="stButton"] button:hover {{
            background: #03346e !important;
            box-shadow: 0 4px 14px rgba({RGB_AZUL_CSS}, 0.35) !important;
        }}
        a[href*="whatsapp.com"],
        a[href*="wa.me"] {{
            background-color: #25D366 !important;
            color: #ffffff !important;
            border: 1px solid #1ebe57 !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            text-decoration: none !important;
            box-shadow: 0 2px 8px rgba(37, 211, 102, 0.35) !important;
        }}
        a[href*="whatsapp.com"]:hover,
        a[href*="wa.me"]:hover {{
            background-color: #20bd5a !important;
            border-color: #1aa34a !important;
            color: #ffffff !important;
        }}
        div[data-testid="stAlert"] {{
            border-radius: 14px !important;
            border: 2px solid {COR_AZUL_ESC} !important;
            background: #ffffff !important;
            box-shadow: 0 2px 12px rgba({RGB_AZUL_CSS}, 0.1) !important;
        }}
        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span,
        div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"],
        div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] * {{
            color: {COR_AZUL_ESC} !important;
        }}
        div[data-testid="stAlert"] svg {{
            fill: {COR_AZUL_ESC} !important;
            color: {COR_AZUL_ESC} !important;
        }}

        .stDownloadButton button {{
            background: #f0f2f6 !important;
            color: {COR_AZUL_ESC} !important;
            border: 1px solid #e2e8f0 !important;
            height: 48px !important;
        }}
        .stDownloadButton button:hover {{
            border-color: #cbd5e1 !important;
            color: {COR_AZUL_ESC} !important;
            background: #e2e8f0 !important;
        }}

        [data-testid="stSidebar"] .stButton button {{
            padding: 8px 12px !important;
            font-size: 0.75rem !important;
            margin-bottom: 2px !important;
            height: auto !important;
            min-height: 30px !important;
        }}

        /* Cabeçalho global: sem caixa — logo e título sobre o degradê da página */
        .header-container {{
            text-align: center;
            padding: clamp(1rem, 3vw, 1.75rem) 1rem 1.25rem;
            margin: 0 auto 1.5rem;
            max-width: 920px;
            background: none !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            position: relative;
        }}
        .header-logo-wrap {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0 auto 1.1rem;
        }}
        .header-logo-wrap img {{
            display: block;
            margin: 0 auto;
            max-height: 78px;
            width: auto;
            max-width: min(320px, 88vw);
            height: auto;
            object-fit: contain;
            filter: drop-shadow(0 2px 12px rgba(0, 0, 0, 0.18));
        }}
        .header-title {{
            font-family: 'Montserrat', 'Inter', sans-serif;
            font-size: clamp(1.2rem, 2.8vw, 1.85rem);
            font-weight: 800;
            line-height: 1.2;
            margin: 0 0 0.5rem 0;
            letter-spacing: 0.04em;
            color: #ffffff;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2), 0 2px 24px rgba(0, 0, 0, 0.12);
        }}
        .header-title .header-title-muted {{
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-size: 0.92em;
            opacity: 0.95;
        }}
        .header-title .header-title-accent {{
            color: #ffffff;
            font-weight: 800;
            margin-left: 0.15em;
            padding: 0.08em 0.28em;
            border-radius: 6px;
            background: linear-gradient(135deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%);
            box-shadow: 0 2px 12px rgba({RGB_VERMELHO_CSS}, 0.45);
            text-shadow: none;
        }}
        .header-title-rule {{
            width: min(200px, 55vw);
            height: 3px;
            margin: 0.85rem auto 0;
            border-radius: 999px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.85), {COR_VERMELHO}, rgba(255,255,255,0.85), transparent);
            opacity: 0.95;
        }}
        .header-subtitle {{
            font-family: 'Inter', system-ui, sans-serif;
            color: rgba(255, 255, 255, 0.92);
            font-size: clamp(0.875rem, 1.6vw, 1rem);
            font-weight: 500;
            margin: 0.65rem 0 0 0;
            letter-spacing: 0.02em;
            line-height: 1.5;
            max-width: 36rem;
            margin-left: auto;
            margin-right: auto;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
        }}
        .header-subtitle strong {{
            color: #ffffff;
            font-weight: 600;
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
            box-shadow: 0 10px 30px -10px rgba({RGB_VERMELHO_CSS}, 0.14);
        }}

        .summary-header {{
            font-family: 'Montserrat', 'Inter', sans-serif;
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
            color: {COR_TEXTO_LABEL};
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
        .metric-value {{ color: {COR_AZUL_ESC} !important; font-size: 1.8rem; font-weight: 800; font-family: 'Montserrat', 'Inter', sans-serif; }}

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
        
        /* HOVER CARD EFFECT FOR ANALYTICS */
        .hover-card {{
            background-color: #ffffff;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #eef2f6;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            height: 100%;
        }}
        .hover-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba({RGB_AZUL_CSS}, 0.15);
            border-color: {COR_AZUL_ESC};
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
            box-shadow: 0 4px 10px rgba({RGB_AZUL_CSS}, 0.3);
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
            box-shadow: 0 0 0 6px rgba({RGB_AZUL_CSS}, 0.15);
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

        .footer {{
            text-align: center;
            padding: 2.25rem 1rem 1.25rem;
            font-family: 'Inter', system-ui, sans-serif;
            color: rgba(255, 255, 255, 0.78) !important;
            font-size: 0.8rem;
            line-height: 1.55;
            font-weight: 500;
            letter-spacing: 0.02em;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
        }}
        
        /* Estilização específica dos botões da Home */
        div[data-testid="stButton"] button.home-card-btn {{
             height: 250px !important;
             border-radius: 16px !important;
             border: 2px solid #eef2f6 !important;
             background-color: white !important;
             color: {COR_AZUL_ESC} !important;
             box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
             font-size: 1.2rem !important;
             font-weight: 700 !important;
        }}
        div[data-testid="stButton"] button.home-card-btn:hover {{
             border-color: {COR_VERMELHO} !important;
             color: {COR_VERMELHO} !important;
             transform: translateY(-5px);
             box-shadow: 0 10px 20px rgba({RGB_VERMELHO_CSS}, 0.15) !important;
        }}
        </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step_name):
    steps = [
        {"id": "input", "label": "Perfil"},
        {"id": "fechamento_aprovado", "label": "Fechamento"},
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
        pdf.cell(0, 10, "RELATÓRIO DE VIABILIDADE", ln=True, align='C')

        pdf.set_font("Helvetica", '', 9)
        pdf.cell(0, 5, "SIMULADOR IMOBILIARIO DV - DOCUMENTO EXECUTIVO", ln=True, align='C')
        pdf.ln(6)

        # Bloco cliente
        y = pdf.get_y()
        pdf.set_fill_color(*FUNDO_SECAO)
        pdf.rect(pdf.l_margin, y, largura_util, 16, 'F')

        pdf.set_xy(pdf.l_margin + 4, y + 4)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 5, f"CLIENTE: {d.get('nome', 'Não informado').upper()}", ln=True)

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
        secao("DADOS DO IMÓVEL")
        linha("Empreendimento", str(d.get('empreendimento_nome')))
        linha("Unidade Selecionada", str(d.get('unidade_id')))
        
        # Valor de Venda no Sistema = Valor Comercial Mínimo
        v_comercial = d.get('imovel_valor', 0)
        v_avaliacao = d.get('imovel_avaliacao', 0)
        
        # No PDF para o cliente, mostramos Avaliação e o "Desconto" para chegar no valor de venda
        linha("Valor de Tabela/Avaliação", f"R$ {fmt_br(v_avaliacao)}", True)
        
        if d.get('unid_entrega'): linha("Previsão de Entrega", str(d.get('unid_entrega')))
        if d.get('unid_area'): linha("Área Privativa", f"{d.get('unid_area')} m²")
        if d.get('unid_tipo'): linha("Tipologia", str(d.get('unid_tipo')))
        if d.get('unid_endereco') and d.get('unid_bairro'): 
            linha("Endereço", f"{d.get('unid_endereco')} - {d.get('unid_bairro')}")

        pdf.ln(4)
        
        # SEÇÃO DE NEGOCIAÇÃO (NOVO)
        secao("CONDIÇÃO COMERCIAL")
        # Calculamos a diferença como "Desconto"
        desconto = max(0, v_avaliacao - v_comercial)
        linha("Desconto/Condição Especial", f"R$ {fmt_br(desconto)}")
        linha("Valor Final de Venda", f"R$ {fmt_br(v_comercial)}", True)
        
        pdf.ln(4)

        secao("ENGENHARIA FINANCEIRA")
        linha("Financiamento Bancário Estimado", f"R$ {fmt_br(d.get('finan_usado', 0))}")
        prazo = d.get('prazo_financiamento', 360)
        linha("Sistema de Amortização", f"{d.get('sistema_amortizacao', 'SAC')} - {prazo}x")
        linha("Parcela Estimada do Financiamento", f"R$ {fmt_br(d.get('parcela_financiamento', 0))}")
        linha("Subsídio + FGTS Utilizado", f"R$ {fmt_br(d.get('fgts_sub_usado', 0))}")
        linha("Pro Soluto Direcional", f"R$ {fmt_br(d.get('ps_usado', 0))}")
        linha("Mensalidade do Pro Soluto", f"{d.get('ps_parcelas')}x de R$ {fmt_br(d.get('ps_mensal', 0))}")

        pdf.ln(4)

        secao("FLUXO DE ENTRADA (ATO)")
        linha("Valor Total de Entrada", f"R$ {fmt_br(d.get('entrada_total', 0))}", True)
        linha("Ato (Imediato)", f"R$ {fmt_br(d.get('ato_final', 0))}")
        linha("Ato 30 Dias", f"R$ {fmt_br(d.get('ato_30', 0))}")
        linha("Ato 60 Dias", f"R$ {fmt_br(d.get('ato_60', 0))}")
        linha("Ato 90 Dias", f"R$ {fmt_br(d.get('ato_90', 0))}")

        # ===============================
        # RODAPÉ (DADOS CORRETOR)
        # ===============================
        pdf.ln(4)
        
        # Dados do Corretor
        pdf.set_font("Helvetica", 'B', 9)
        pdf.set_text_color(*AZUL)
        pdf.cell(0, 5, "CONSULTOR RESPONSÁVEL", ln=True, align='L')
        pdf.set_font("Helvetica", '', 9)
        pdf.cell(0, 5, f"{d.get('corretor_nome', 'Não informado').upper()}", ln=True)
        pdf.cell(0, 5, f"Contato: {d.get('corretor_telefone', '')} | E-mail: {d.get('corretor_email', '')}", ln=True)

        pdf.ln(4)

        # Aviso Legal e Data
        pdf.set_font("Helvetica", 'I', 7)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            0,
            4,
            f"Simulação realizada em {d.get('data_simulacao', date.today().strftime('%d/%m/%Y'))}. "
            "Sujeito a análise de crédito e alteração de tabela sem aviso prévio.",
            ln=True,
            align='C'
        )
        pdf.cell(0, 4, "Direcional Engenharia - Rio de Janeiro", ln=True, align='C')

        return bytes(pdf.output())

    except:
        return None

def enviar_email_smtp(destinatario, nome_cliente, pdf_bytes, dados_cliente, tipo='cliente'):
    if "email" not in st.secrets: return False, "Configuracoes de e-mail nao encontradas."
    import urllib.parse
    
    try:
        smtp_server = st.secrets["email"]["smtp_server"].strip()
        smtp_port = int(st.secrets["email"]["smtp_port"])
        sender_email = st.secrets["email"]["sender_email"].strip()
        sender_password = st.secrets["email"]["sender_password"].strip().replace(" ", "")
    except Exception as e: return False, f"Erro config: {e}"

    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email; msg['To'] = destinatario
    
    # Extrair dados para o email
    emp = dados_cliente.get('empreendimento_nome', 'Seu Imóvel')
    unid = dados_cliente.get('unidade_id', '')
    val_venda = fmt_br(dados_cliente.get('imovel_valor', 0))
    val_aval = fmt_br(dados_cliente.get('imovel_avaliacao', 0))
    entrada = fmt_br(dados_cliente.get('entrada_total', 0))
    finan = fmt_br(dados_cliente.get('finan_usado', 0))
    ps = fmt_br(dados_cliente.get('ps_mensal', 0))
    renda_cli = fmt_br(dados_cliente.get('renda', 0))
    
    # Dados de atos para tabela do corretor
    a0 = fmt_br(dados_cliente.get('ato_final', 0))
    a30 = fmt_br(dados_cliente.get('ato_30', 0))
    a60 = fmt_br(dados_cliente.get('ato_60', 0))
    a90 = fmt_br(dados_cliente.get('ato_90', 0))
    
    corretor_nome = dados_cliente.get('corretor_nome', 'Direcional')
    corretor_tel = dados_cliente.get('corretor_telefone', '')
    corretor_email = dados_cliente.get('corretor_email', '')
    
    corretor_tel_clean = re.sub(r'\D', '', corretor_tel)
    if not corretor_tel_clean.startswith('55'):
        corretor_tel_clean = '55' + corretor_tel_clean # Assuming Brazil

    wa_msg = f"Olá {corretor_nome}, sou {nome_cliente}. Realizei uma simulação para o {emp} (Unidade {unid}) e gostaria de saber mais detalhes."
    wa_link = f"https://wa.me/{corretor_tel_clean}?text={urllib.parse.quote(wa_msg)}"
    
    URL_LOGO_BRANCA = "https://drive.google.com/uc?export=view&id=1m0iX6FCikIBIx4gtSX3Y_YMYxxND2wAh"

    # TEMPLATE CLIENTE (Foco no sonho, design limpo, usando Tabelas para evitar sobreposição)
    if tipo == 'cliente':
        msg['Subject'] = f"Seu sonho está próximo! Simulação - {emp}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        </head>
        <body style="font-family: 'Helvetica', Arial, sans-serif; color: #333; background-color: #f9f9f9; margin: 0; padding: 20px;">
            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                    <td align="center">
                        <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                            <!-- Cabeçalho -->
                            <tr>
                                <td align="center" style="background-color: #002c5d; padding: 30px; border-bottom: 4px solid #e30613;">
                                    <img src="{URL_LOGO_BRANCA}" width="150" style="display: block;">
                                </td>
                            </tr>
                            <!-- Corpo -->
                            <tr>
                                <td style="padding: 40px;">
                                    <h2 style="color: #002c5d; margin: 0 0 20px 0; font-weight: 300; text-align: center;">Olá, {nome_cliente}!</h2>
                                    <p style="font-size: 16px; line-height: 1.6; text-align: center; color: #555;">
                                        Foi ótimo apresentar as oportunidades da Direcional para você. O imóvel <strong>{emp}</strong> é incrível e desenhamos uma condição especial para o seu perfil.
                                    </p>
                                    
                                    <!-- Card Destaque -->
                                    <table width="100%" border="0" cellspacing="0" cellpadding="20" style="background-color: #f0f4f8; border-left: 5px solid #e30613; margin: 30px 0; border-radius: 4px;">
                                        <tr>
                                            <td>
                                                <p style="margin: 0; font-weight: bold; color: #002c5d; font-size: 18px;">{emp}</p>
                                                <p style="margin: 5px 0 0 0; color: #777;">Unidade: {unid}</p>
                                                <p style="margin: 15px 0 0 0; font-size: 24px; font-weight: bold; color: #e30613;">Valor Promocional: R$ {val_venda}</p>
                                            </td>
                                        </tr>
                                    </table>

                                    <div style="text-align: center; margin: 35px 0;">
                                        <a href="{wa_link}" style="background-color: #25D366; color: #ffffff; padding: 15px 30px; text-decoration: none; font-weight: bold; border-radius: 5px; font-size: 16px; display: inline-block;">FALAR COM O CORRETOR NO WHATSAPP</a>
                                        <p style="font-size: 12px; color: #999; margin-top: 10px;">(Abra o arquivo PDF em anexo para ver todos os detalhes)</p>
                                    </div>
                                    
                                    <!-- Rodapé Interno -->
                                    <table width="100%" border="0" cellspacing="0" cellpadding="20" style="margin-top: 40px; background-color: #002c5d; color: #ffffff;">
                                        <tr>
                                            <td align="center">
                                                <p style="margin: 0; font-size: 16px; font-weight: bold; color: #ffffff;">{corretor_nome.upper()}</p>
                                                <p style="margin: 5px 0 15px 0; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; color: #e30613;">Consultor Direcional</p>
                                                
                                                <p style="margin: 0; font-size: 14px;">
                                                    <span style="color: #ffffff;">WhatsApp:</span> <a href="{wa_link}" style="color: #e30613; text-decoration: none; font-weight: bold;">{corretor_tel}</a>
                                                    <span style="margin: 0 10px; color: #666;">|</span>
                                                    <span style="color: #ffffff;">Email:</span> <a href="mailto:{corretor_email}" style="color: #e30613; text-decoration: none; font-weight: bold;">{corretor_email}</a>
                                                </p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    # TEMPLATE CORRETOR (Foco técnico, dados completos, usando Tabelas)
    else:
        msg['Subject'] = f"LEAD: {nome_cliente} - {emp} - {unid}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        </head>
        <body style="font-family: 'Arial', sans-serif; color: #333; background-color: #eee; margin: 0; padding: 20px;">
            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                    <td align="center">
                        <table width="650" border="0" cellspacing="0" cellpadding="0" style="background-color: #fff; border: 1px solid #ccc;">
                            <!-- Header Azul com Logo Branca -->
                            <tr>
                                <td align="center" style="background-color: #002c5d; padding: 20px; border-bottom: 4px solid #e30613;">
                                    <img src="{URL_LOGO_BRANCA}" width="150" style="display: block;">
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 30px;">
                                    <h3 style="color: #002c5d; border-bottom: 2px solid #e30613; padding-bottom: 10px; margin-top: 0;">RESUMO DE ATENDIMENTO</h3>
                                    
                                    <!-- Info Header -->
                                    <table width="100%" border="0" cellspacing="0" cellpadding="15" style="margin-bottom: 20px; background: #f9f9f9;">
                                        <tr>
                                            <td width="50%" valign="top">
                                                <p style="margin: 0 0 5px 0; font-size: 12px; color: #666;">CLIENTE</p>
                                                <p style="margin: 0; font-weight: bold; font-size: 16px;">{nome_cliente}</p>
                                                <p style="margin: 5px 0 0 0; font-size: 14px;">Renda: R$ {renda_cli}</p>
                                            </td>
                                            <td width="50%" valign="top">
                                                <p style="margin: 0 0 5px 0; font-size: 12px; color: #666;">PRODUTO</p>
                                                <p style="margin: 0; font-weight: bold; font-size: 16px;">{emp}</p>
                                                <p style="margin: 5px 0 0 0;">Unid: {unid}</p>
                                            </td>
                                        </tr>
                                    </table>

                                    <h4 style="color: #002c5d; margin-top: 0;">Valores do Imóvel</h4>
                                    <table width="100%" border="1" cellspacing="0" cellpadding="8" style="border-collapse: collapse; border-color: #ddd; margin-bottom: 20px; font-size: 14px;">
                                        <tr style="background-color: #f2f2f2;">
                                            <td>Valor Venda (VCM)</td>
                                            <td align="right" style="color: #e30613;"><b>R$ {val_venda}</b></td>
                                        </tr>
                                        <tr>
                                            <td>Avaliação Bancária</td>
                                            <td align="right">R$ {val_aval}</td>
                                        </tr>
                                    </table>

                                    <h4 style="color: #002c5d;">Plano de Pagamento</h4>
                                    <table width="100%" border="1" cellspacing="0" cellpadding="8" style="border-collapse: collapse; border-color: #ddd; margin-bottom: 20px; font-size: 14px;">
                                        <tr style="background-color: #f2f2f2;">
                                            <td>Entrada Total</td>
                                            <td align="right" style="color: #002c5d;"><b>R$ {entrada}</b></td>
                                        </tr>
                                        <tr>
                                             <td>&nbsp;&nbsp;↳ Ato Imediato</td>
                                             <td align="right">R$ {a0}</td>
                                        </tr>
                                        <tr>
                                             <td>&nbsp;&nbsp;↳ 30 Dias</td>
                                             <td align="right">R$ {a30}</td>
                                        </tr>
                                        <tr>
                                             <td>&nbsp;&nbsp;↳ 60 Dias</td>
                                             <td align="right">R$ {a60}</td>
                                        </tr>
                                         <tr>
                                             <td>&nbsp;&nbsp;↳ 90 Dias</td>
                                             <td align="right">R$ {a90}</td>
                                        </tr>
                                        <tr style="background-color: #f2f2f2;">
                                            <td>Financiamento</td>
                                            <td align="right">R$ {finan}</td>
                                        </tr>
                                        <tr>
                                            <td>Mensal Pro Soluto</td>
                                            <td align="right">R$ {ps}</td>
                                        </tr>
                                    </table>
                                    
                                    <p style="font-size: 12px; color: #999; text-align: center; margin-top: 30px;">Simulação gerada via Direcional Rio Simulador.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    msg.attach(MIMEText(html_content, 'html'))
    
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

@st.dialog("Opções de Exportação")
def show_export_dialog(d):
    # Alterado para text-align: center para alinhar com o tema
    st.markdown(f"<h3 style='text-align: center; color: {COR_AZUL_ESC}; margin: 0;'>Resumo da Simulação</h3>", unsafe_allow_html=True)
    st.markdown("Escolha como deseja exportar o documento.")
    
    # Injetar dados do corretor no dicionário para o PDF
    d['corretor_nome'] = st.session_state.get('user_name', '')
    d['corretor_email'] = st.session_state.get('user_email', '')
    d['corretor_telefone'] = st.session_state.get('user_phone', '')
    
    pdf_data = gerar_resumo_pdf(d)

    if pdf_data:
        st.download_button(label="Baixar PDF", data=pdf_data, file_name=f"Resumo_Direcional_{d.get('nome', 'Cliente')}.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.warning("Geração de PDF indisponível.")

    st.markdown("---")
    st.markdown("**Enviar por E-mail (Cliente)**")
    email = st.text_input("Endereço de e-mail do cliente", placeholder="cliente@exemplo.com")
    if st.button("Enviar Email para Cliente", use_container_width=True):
        if email and "@" in email:
            # Passando DADOS COMPLETOS para o email HTML e tipo CLIENTE
            sucesso, msg = enviar_email_smtp(email, d.get('nome', 'Cliente'), pdf_data, d, tipo='cliente')
            if sucesso: st.success(msg)
            else: st.error(msg)
        else:
            st.error("E-mail inválido")

# =============================================================================
# APLICAÇÃO PRINCIPAL
# =============================================================================

def aba_simulador_automacao(df_finan, df_estoque, df_politicas, _df_cadastros, premissas_dict=None):
    passo = st.session_state.get('passo_simulacao', 'input')
    if passo == 'gallery':
        st.session_state.passo_simulacao = 'input'
        st.rerun()
    motor = MotorRecomendacao(df_finan, df_estoque, df_politicas)
    _prem = dict(DEFAULT_PREMISSAS)
    if premissas_dict:
        _prem.update(premissas_dict)

    def taxa_fin_vigente(d_cli):
        return resolver_taxa_financiamento_anual_pct(d_cli or {}, _prem)
    if 'dados_cliente' not in st.session_state: st.session_state.dados_cliente = {}

    # RENDER PROGRESS BAR
    if passo != 'client_analytics':
        render_stepper(passo)
        
    # --- ABA ANALYTICS (SECURE TAB - ALTAIR) ---
    if passo == 'client_analytics':
        d = st.session_state.dados_cliente
        
        st.markdown(f"### Painel da simulação: {d.get('nome', 'Simulação')}")

        # --- SEÇÃO 1: PERFIL USADO NA SIMULAÇÃO ---
        with st.container():
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="hover-card" style="border-left: 5px solid {COR_AZUL_ESC};">
                    <p style="font-weight: bold; margin-bottom: 10px; color: {COR_AZUL_ESC};">Perfil de crédito</p>
                    <p style="font-size: 0.9rem; margin: 0;">Ranking: {d.get('ranking')}</p>
                    <p style="font-size: 0.9rem; margin: 0;">Política PS: {d.get('politica', '—')}</p>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="hover-card" style="border-left: 5px solid {COR_AZUL_ESC};">
                    <p style="font-weight: bold; margin-bottom: 10px; color: {COR_AZUL_ESC};">Renda & Perfil</p>
                    <p style="font-size: 0.9rem; margin: 0;">Renda Familiar: R$ {fmt_br(d.get('renda', 0))}</p>
                    <p style="font-size: 0.9rem; margin: 0;">Participantes: {d.get('qtd_participantes')}</p>
                    <p style="font-size: 0.9rem; margin: 0;">FGTS: {'Sim' if d.get('cotista') else 'Não'} | Social: {'Sim' if d.get('social') else 'Não'}</p>
                </div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="hover-card" style="border-left: 5px solid {COR_AZUL_ESC};">
                    <p style="font-weight: bold; margin-bottom: 10px; color: {COR_AZUL_ESC};">Imóvel Salvo</p>
                    <p style="font-size: 0.9rem; margin: 0;">{d.get('empreendimento_nome')}</p>
                    <p style="font-size: 0.9rem; margin: 0;">Unidade: {d.get('unidade_id')}</p>
                    <p style="font-size: 0.9rem; margin: 0;">Valor: <span style='color:{COR_VERMELHO}; font-weight:bold;'>R$ {fmt_br(d.get('imovel_valor', 0))}</span></p>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # --- SEÇÃO 2: GRÁFICOS DE PIZZA (COMPOSIÇÃO) ---
        g_col1, g_col2 = st.columns(2)
        
        # Gráfico 1: Composição da Compra
        with g_col1:
            st.markdown("##### Composição da Compra")
            labels = ['Ato', '30 Dias', '60 Dias', '90 Dias', 'Pro Soluto', 'Financiamento', 'FGTS/Subsídio']
            values = [
                d.get('ato_final', 0), d.get('ato_30', 0), d.get('ato_60', 0), d.get('ato_90', 0),
                d.get('ps_usado', 0), d.get('finan_usado', 0), d.get('fgts_sub_usado', 0)
            ]
            
            # Filter zeros for cleaner chart
            clean_data = [(l, v) for l, v in zip(labels, values) if v > 0]
            if clean_data:
                df_pie = pd.DataFrame(clean_data, columns=['Tipo', 'Valor'])
                
                # Define cores personalizadas para cada tipo de pagamento
                color_scale = alt.Scale(domain=['Ato', '30 Dias', '60 Dias', '90 Dias', 'Pro Soluto', 'Financiamento', 'FGTS/Subsídio'],
                                                                  range=['#e30613', '#c0392b', '#94a3b8', '#64748b', '#f59e0b', '#002c5d', '#10b981'])

                # Selection for interactivity
                hover = alt.selection_point(on='mouseover', empty=False, fields=['Tipo'])

                base = alt.Chart(df_pie).encode(theta=alt.Theta("Valor", stack=True))
                pie = base.mark_arc(innerRadius=60, outerRadius=120).encode(
                    color=alt.Color("Tipo", scale=color_scale, legend=None),
                    order=alt.Order("Valor", sort="descending"),
                    tooltip=[alt.Tooltip("Tipo"), alt.Tooltip("Valor", format=",.2f")],
                    opacity=alt.condition(hover, alt.value(1), alt.value(0.7)),
                    stroke=alt.condition(hover, alt.value('white'), alt.value(None)),
                    strokeWidth=alt.condition(hover, alt.value(2), alt.value(0))
                ).add_params(hover)
                
                text = base.mark_text(radius=140).encode(
                    text=alt.Text("Valor", format=",.2f"),
                    order=alt.Order("Valor", sort="descending"),
                    color=alt.value(COR_AZUL_ESC)  
                )
                
                final_pie = pie.encode(color=alt.Color("Tipo", scale=color_scale, legend=alt.Legend(orient="bottom", columns=2, title=None))).configure_view(strokeWidth=0).configure_axis(grid=False, domain=False)
                st.altair_chart(final_pie, use_container_width=True)
            else:
                st.info("Sem dados financeiros suficientes.")

        # Gráfico 2: Composição de Renda
        with g_col2:
            st.markdown("##### Composição de Renda")
            rendas = d.get('rendas_lista', [])
            pie_renda = [(f"Part. {i+1}", r) for i, r in enumerate(rendas) if r > 0]
            if pie_renda:
                df_renda = pd.DataFrame(pie_renda, columns=['Participante', 'Renda'])
                
                color_scale_renda = alt.Scale(domain=[f"Part. {i+1}" for i in range(len(pie_renda))],
                                                                  range=['#002c5d', '#e30613', '#f59e0b', '#10b981'])

                hover_renda = alt.selection_point(on='mouseover', empty=False, fields=['Participante'])

                base = alt.Chart(df_renda).encode(theta=alt.Theta("Renda", stack=True))
                pie = base.mark_arc(innerRadius=60, outerRadius=120).encode(
                    color=alt.Color("Participante", scale=color_scale_renda, legend=alt.Legend(orient="bottom", title=None)),
                    order=alt.Order("Renda", sort="descending"),
                    tooltip=[alt.Tooltip("Participante"), alt.Tooltip("Renda", format=",.2f")],
                    opacity=alt.condition(hover_renda, alt.value(1), alt.value(0.7)),
                    stroke=alt.condition(hover_renda, alt.value('white'), alt.value(None)),
                    strokeWidth=alt.condition(hover_renda, alt.value(2), alt.value(0))
                ).add_params(hover_renda)

                st.altair_chart(pie.configure_view(strokeWidth=0), use_container_width=True)
            else:
                st.caption("Renda única ou não informada.")

        # --- SEÇÃO 3: PROJEÇÃO DE FLUXO DE PAGAMENTOS (BAR CHART + ZOOM) ---
        st.markdown("---")
        st.markdown("##### Projeção da Parcela Mensal (Financiamento + Pro Soluto + Atos)")
        
        # Recuperar dados para projeção
        v_fin = d.get('finan_usado', 0)
        p_fin = d.get('prazo_financiamento', 360)
        p_ps = d.get('ps_parcelas', 0)
        v_ps_mensal = d.get('ps_mensal', 0)
        sist = d.get('sistema_amortizacao', 'SAC')
        
        # Recuperar dados de ATOS para o cálculo correto do fluxo inicial
        atos_dict_calc = {
            'ato_final': d.get('ato_final', 0),
            'ato_30': d.get('ato_30', 0),
            'ato_60': d.get('ato_60', 0),
            'ato_90': d.get('ato_90', 0)
        }
        
        if v_fin > 0 and p_fin > 0:
            df_fluxo = calcular_fluxo_pagamento_detalhado(v_fin, p_fin, taxa_fin_vigente(d), sist, v_ps_mensal, p_ps, atos_dict_calc)
            
            # Projeção completa solicitada
            df_view = df_fluxo.copy() 
            
            # CORREÇÃO ALTAIR: Conversão explícita de tipos para evitar SchemaValidationError
            df_view['Mês'] = df_view['Mês'].astype(int)
            df_view['Valor'] = df_view['Valor'].astype(float)
            df_view['Total'] = df_view['Total'].astype(float)
            
            # Definir pontos para as linhas tracejadas
            # 1. Fim dos Atos: Onde termina o último ato (mês 1, 2, 3 ou 4)
            mes_fim_atos = 1
            if d.get('ato_90', 0) > 0: mes_fim_atos = 4
            elif d.get('ato_60', 0) > 0: mes_fim_atos = 3
            elif d.get('ato_30', 0) > 0: mes_fim_atos = 2
            
            # 2. Fim do Pro Soluto: Mês da última parcela
            mes_fim_ps = d.get('ps_parcelas', 0)

            # Cores para cada tipo
            domain_tipo = ['Financiamento', 'Pro Soluto', 'Entrada/Ato']
            range_tipo = [COR_AZUL_ESC, '#f59e0b', COR_VERMELHO] 

            zoom = alt.selection_interval(bind='scales')

            # Base chart with Ordinal x-axis for spacing
            base = alt.Chart(df_view).encode(
                x=alt.X('Mês:O', title='Mês do Financiamento', axis=alt.Axis(labelAngle=0)) # Ordinal para separar
            )

            # Barras Empilhadas
            bars = base.mark_bar().encode(
                y=alt.Y('Valor', title='Valor (R$)', stack='zero'),
                color=alt.Color('Tipo', scale=alt.Scale(domain=domain_tipo, range=range_tipo), legend=alt.Legend(title="Composição")),
                order=alt.Order('Ordem_Tipo', sort='ascending'), # Define a ordem de empilhamento usando a coluna auxiliar
                tooltip=['Mês', 'Tipo', alt.Tooltip('Valor', format=",.2f"), alt.Tooltip('Total', format=",.2f")]
            )

            # Linha Fim Atos
            charts = [bars]
            if mes_fim_atos > 0:
                # Conversão explícita para int e usar mesma coluna 'Mês'
                rule_atos = alt.Chart(pd.DataFrame({'Mês': [int(mes_fim_atos)]})).mark_rule(color='red', strokeDash=[5, 5]).encode(x='Mês:O')
                charts.append(rule_atos)
                
            if mes_fim_ps > 0:
                # Conversão explícita para int e usar mesma coluna 'Mês'
                rule_ps = alt.Chart(pd.DataFrame({'Mês': [int(mes_fim_ps)]})).mark_rule(color='orange', strokeDash=[5, 5]).encode(x='Mês:O')
                charts.append(rule_ps)

            final_chart = alt.layer(*charts).add_params(zoom).properties(height=400)

            st.altair_chart(final_chart, use_container_width=True)
            st.caption("Linha Vermelha Tracejada: Fim dos Atos | Linha Laranja Tracejada: Fim do Pro Soluto")

        # --- SEÇÃO 4: OPORTUNIDADES SEMELHANTES ---
        st.markdown("---")
        st.markdown("##### Oportunidades Semelhantes (Faixa de Preço)")
        
        target_price = d.get('imovel_valor', 0)
        
        try:
            if 'Valor de Venda' in df_estoque.columns and target_price > 0:
                min_p = target_price - 2500
                max_p = target_price + 2500
                
                similares = df_estoque[
                    (df_estoque['Valor de Venda'] >= min_p) & 
                    (df_estoque['Valor de Venda'] <= max_p) &
                    (df_estoque['Empreendimento'] != d.get('empreendimento_nome')) 
                ].sort_values('Valor de Venda').head(10)
                
                if not similares.empty:
                    cards_html = f"""<div class="scrolling-wrapper">"""
                    
                    for idx, row in similares.iterrows():
                         emp_name = row['Empreendimento']
                         unid_name = row['Identificador']
                         val_fmt = fmt_br(row['Valor de Venda'])
                         
                         # Avaliação também
                         aval_fmt = fmt_br(row['Valor de Avaliação Bancária'])
                         
                         cards_html += f"""<div class="card-item">
                            <div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC}; height: 100%; justify-content: flex-start;">
                                <b style="color:{COR_AZUL_ESC}; font-size:1.1rem;">{emp_name}</b><br>
                                <div style="font-size:0.85rem; color:{COR_TEXTO_MUTED}; text-align:center; border-top:1px solid #eee; padding-top:10px; width:100%;"><b>Unidade: {unid_name}</b></div>
                                <div style="margin-top:10px; width:100%;">
                                    <div style="font-size:0.8rem; color:#64748b;">Avaliação</div>
                                    <div style="font-weight:bold; color:{COR_AZUL_ESC};">R$ {aval_fmt}</div>
                                    <div style="font-size:0.8rem; color:#64748b; margin-top:5px;">Venda</div>
                                    <div class="price-tag" style="font-size:1.3rem; margin-top:0;">R$ {val_fmt}</div>
                                </div>
                            </div>
                         </div>"""
                    cards_html += "</div>"
                    st.markdown(cards_html, unsafe_allow_html=True)
                else:
                    st.info("Nenhuma outra unidade encontrada nessa faixa de preço (+/- 2500).")
            else:
                st.info("Dados de estoque indisponíveis para comparação.")
        except Exception:
             st.info("Não foi possível carregar oportunidades semelhantes.")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- BOTÃO VOLTAR (FULL WIDTH) - azul direcional ---
        st.markdown(f"""
            <style>
            div[data-testid="stMarkdown"]:has([data-btn-azul]) + div[data-testid="stButton"] button {{
                width: 100%;
                border-radius: 16px;
                height: 60px;
                font-size: 1.1rem;
                font-weight: bold;
                text-transform: uppercase;
            }}
            </style>
        """, unsafe_allow_html=True)

        st.markdown('<div data-btn-azul style="display:none" aria-hidden="true"></div>', unsafe_allow_html=True)
        if st.button("VOLTAR AO SIMULADOR", use_container_width=True):
             st.session_state.passo_simulacao = 'input'
             scroll_to_top()
             st.rerun()

    # --- ETAPA 1: INPUT (perfil da simulação — sem cadastro de pessoa) ---
    elif passo == 'input':
        st.markdown("### Perfil da simulação")
        st.caption("Informe renda e perfil de crédito. **Confirmar e avançar** leva direto aos valores aprovados.")

        rendas_anteriores = st.session_state.dados_cliente.get('rendas_lista', [])
        _dc_in = st.session_state.dados_cliente
        if "qtd_part_v3" not in st.session_state:
            st.session_state["qtd_part_v3"] = str(int(_dc_in.get("qtd_participantes", 1) or 1))
        for _i in range(4):
            _rk = f"renda_part_{_i}_v3"
            if _rk not in st.session_state:
                _def_r = 3500.0 if _i == 0 and not rendas_anteriores else 0.0
                _v_r = float(rendas_anteriores[_i]) if _i < len(rendas_anteriores) else _def_r
                st.session_state[_rk] = float_para_campo_texto(_v_r, vazio_se_zero=True)

        st.markdown(f"""<div style="border: 1px solid {COR_BORDA}; border-radius: 12px 12px 0 0; padding: 15px 20px; text-align: center; background: #f8fafc;">
<p style="font-weight: 700; font-size: 1.1rem; margin: 0; color: {COR_AZUL_ESC};">Renda e política</p></div>""", unsafe_allow_html=True)
        with st.form("form_cadastro"):
            st.text_input("Participantes na Renda (1 a 4)", key="qtd_part_v3", placeholder="Ex.: 2")
            _qp = texto_inteiro(st.session_state.get("qtd_part_v3"), default=1, min_v=1, max_v=4)
            qtd_part = _qp if _qp is not None else 1
            cols_renda = st.columns(qtd_part)
            for i in range(qtd_part):
                with cols_renda[i]:
                    st.text_input(f"Renda Part. {i+1}", key=f"renda_part_{i}_v3", placeholder="R$ 0,00")
            rank_opts = ["DIAMANTE", "OURO", "PRATA", "BRONZE", "AÇO"]
            curr_ranking = st.session_state.dados_cliente.get('ranking', "DIAMANTE")
            idx_ranking = rank_opts.index(curr_ranking) if curr_ranking in rank_opts else 0
            ranking = st.selectbox("Ranking do Cliente", options=rank_opts, index=idx_ranking, key="in_rank_v28")
            politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"], index=0 if st.session_state.dados_cliente.get('politica') != "Emcash" else 1, key="in_pol_v28")
            social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False), key="in_soc_v28")
            cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True), key="in_cot_v28")
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Confirmar e avançar", type="primary", use_container_width=True)
        st.markdown(f"""<div style="border: 1px solid {COR_BORDA}; border-top: none; border-radius: 0 0 12px 12px; height: 8px; background: #f8fafc;"></div>""", unsafe_allow_html=True)

        if submitted:
            _qp_sub = texto_inteiro(st.session_state.get("qtd_part_v3"), default=1, min_v=1, max_v=4)
            qtd_part = _qp_sub if _qp_sub is not None else 1
            lista_rendas_input = [texto_moeda_para_float(st.session_state.get(f"renda_part_{j}_v3")) for j in range(qtd_part)]
            renda_total_calc = sum(lista_rendas_input)
            if renda_total_calc <= 0:
                st.error("A renda total deve ser maior que zero.")
            else:
                st.session_state.dados_cliente.update({
                    'nome': 'Simulação',
                    'cpf': '',
                    'data_nascimento': None,
                    'renda': renda_total_calc,
                    'rendas_lista': lista_rendas_input,
                    'social': social,
                    'cotista': cotista,
                    'ranking': ranking,
                    'politica': politica_ps,
                    'qtd_participantes': qtd_part,
                    'finan_usado_historico': 0.0,
                    'ps_usado_historico': 0.0,
                    'fgts_usado_historico': 0.0,
                })
                prazo_ps_max = 66 if politica_ps == "Emcash" else 84
                f_faixa_ref, s_faixa_ref, _ = motor.obter_enquadramento(renda_total_calc, social, cotista, valor_avaliacao=240000)
                st.session_state.dados_cliente.update({
                    'prazo_ps_max': prazo_ps_max,
                    'limit_ps_renda': 0.30,
                    'finan_f_ref': f_faixa_ref,
                    'sub_f_ref': s_faixa_ref,
                })
                st.session_state.passo_simulacao = 'fechamento_aprovado'
                scroll_to_top()
                st.rerun()

    # --- ETAPA 2: VALORES APROVADOS (FECHAMENTO FINANCEIRO) - 2ª ABA ---
    elif passo == 'fechamento_aprovado':
        d = st.session_state.dados_cliente
        st.markdown("### Valores Aprovados (Fechamento Financeiro)")
        st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.9rem;'>Preencha os valores aprovados de financiamento e subsídio. As recomendações usarão esses valores reais.</p>", unsafe_allow_html=True)
        # Recalcular referência da curva (finan_f_ref, sub_f_ref) a partir do perfil do cliente para exibir valores corretos
        renda_cli = float(d.get('renda', 0) or 0)
        social_cli = bool(d.get('social', False))
        cotista_cli = bool(d.get('cotista', True))
        f_curva, s_curva, _ = motor.obter_enquadramento(renda_cli, social_cli, cotista_cli, valor_avaliacao=240000)
        st.session_state.dados_cliente['finan_f_ref'] = f_curva
        st.session_state.dados_cliente['sub_f_ref'] = s_curva
        d = st.session_state.dados_cliente
        if d.get('finan_usado') is None or (isinstance(d.get('finan_usado'), (int, float)) and d.get('finan_usado') == 0):
            st.session_state.dados_cliente['finan_usado'] = d.get('finan_f_ref', 0.0) or 0.0
        if d.get('fgts_sub_usado') is None or (isinstance(d.get('fgts_sub_usado'), (int, float)) and d.get('fgts_sub_usado') == 0):
            st.session_state.dados_cliente['fgts_sub_usado'] = d.get('sub_f_ref', 0.0) or 0.0
        d = st.session_state.dados_cliente
        def _num_f(k, default=0.0):
            v = st.session_state.dados_cliente.get(k, st.session_state.get(k, default))
            if v is None: return default
            try: return float(v)
            except (TypeError, ValueError): return default
        fin_default = _num_f('finan_usado', 0.0)
        if "fin_aprovado_key" not in st.session_state:
            st.session_state["fin_aprovado_key"] = float_para_campo_texto(fin_default, vazio_se_zero=True)
        st.text_input("Financiamento Aprovado (R$)", key="fin_aprovado_key", placeholder="Ex.: 250000 ou 250.000,00")
        f_u = texto_moeda_para_float(st.session_state.get("fin_aprovado_key"))
        st.session_state.dados_cliente['finan_usado'] = f_u
        fin_max = d.get("finan_f_ref", 0)
        st.markdown(f'<div class="inline-ref" style="background-color: transparent; padding: 0; font-family: inherit; font-size: 0.72rem; color: {COR_AZUL_ESC}; margin-top: -12px; margin-bottom: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; display: block; opacity: 0.9;">Financiamento Máximo (curva): R$ {fmt_br(fin_max)}</div>', unsafe_allow_html=True)

        sub_default = _num_f('fgts_sub_usado', 0.0)
        if "sub_aprovado_key" not in st.session_state:
            st.session_state["sub_aprovado_key"] = float_para_campo_texto(sub_default, vazio_se_zero=True)
        st.text_input("Subsídio Aprovado / FGTS + Subsídio (R$)", key="sub_aprovado_key", placeholder="Ex.: 50000 ou 50.000,00")
        s_u = texto_moeda_para_float(st.session_state.get("sub_aprovado_key"))
        st.session_state.dados_cliente['fgts_sub_usado'] = s_u
        fgts_max = d.get("sub_f_ref", 0)
        st.markdown(f'<div class="inline-ref" style="background-color: transparent; padding: 0; font-family: inherit; font-size: 0.72rem; color: {COR_AZUL_ESC}; margin-top: -12px; margin-bottom: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; display: block; opacity: 0.9;">Subsídio Máximo (curva): R$ {fmt_br(fgts_max)}</div>', unsafe_allow_html=True)

        prazo_atual = d.get('prazo_financiamento', 360)
        try: prazo_atual = int(prazo_atual) if prazo_atual is not None else 360
        except: prazo_atual = 360
        if "prazo_aprovado_key" not in st.session_state:
            st.session_state["prazo_aprovado_key"] = str(int(prazo_atual))
        st.text_input("Prazo do Financiamento (meses)", key="prazo_aprovado_key", placeholder="360")
        _pz = texto_inteiro(st.session_state.get("prazo_aprovado_key"), default=360, min_v=12, max_v=600)
        prazo_sel = _pz if _pz is not None else 360
        st.session_state.dados_cliente['prazo_financiamento'] = int(prazo_sel)

        idx_tab = 0 if d.get('sistema_amortizacao', "SAC") == "SAC" else 1
        sist_sel = st.selectbox("Sistema de Amortização", ["SAC", "PRICE"], index=idx_tab, key="sist_aprovado_key")
        st.session_state.dados_cliente['sistema_amortizacao'] = sist_sel
        taxa_padrao = taxa_fin_vigente(d)
        sac_details = calcular_comparativo_sac_price(f_u, int(prazo_sel), taxa_padrao)["SAC"]
        price_details = calcular_comparativo_sac_price(f_u, int(prazo_sel), taxa_padrao)["PRICE"]
        st.markdown(f"""<div style="margin-top: -8px; margin-bottom: 15px; font-size: 0.85rem; color: #64748b;"><b>SAC:</b> R$ {fmt_br(sac_details['primeira'])} a R$ {fmt_br(sac_details['ultima'])} (Juros totais: R$ {fmt_br(sac_details['juros'])}) &nbsp;|&nbsp; <b>PRICE:</b> R$ {fmt_br(price_details['parcela'])} fixas (Juros totais: R$ {fmt_br(price_details['juros'])})</div>""", unsafe_allow_html=True)

        st.markdown("---")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.button("Avançar para Recomendação de Imóveis", type="primary", use_container_width=True, key="btn_fech_to_guide"):
                st.session_state.passo_simulacao = 'guide'; scroll_to_top(); st.rerun()
        with col_f2:
            if st.button("Escolha direta de unidade (estoque)", use_container_width=True, key="btn_fech_to_selection"):
                st.session_state.passo_simulacao = 'selection'; scroll_to_top(); st.rerun()
        st.markdown('<div data-btn-azul style="display:none" aria-hidden="true"></div>', unsafe_allow_html=True)
        if st.button("Voltar ao perfil da simulação", use_container_width=True, key="btn_fech_voltar"): st.session_state.passo_simulacao = 'input'; scroll_to_top(); st.rerun()

    # --- ETAPA 3: RECOMENDAÇÃO (usa valores reais do fechamento) ---
    elif passo == 'guide':
        d = st.session_state.dados_cliente
        st.markdown("### Recomendação de Imóveis")

        df_disp_total = df_estoque.copy()

        if df_disp_total.empty: st.markdown('<div class="custom-alert">Sem produtos viaveis no perfil selecionado.</div>', unsafe_allow_html=True); df_viaveis = pd.DataFrame()
        else:
            def calcular_viabilidade_unidade(row):
                v_venda = row['Valor de Venda']
                v_aval = row['Valor de Avaliação Bancária']
                try: v_venda = float(v_venda)
                except: v_venda = 0.0
                try: v_aval = float(v_aval)
                except: v_aval = v_venda
                # Usar valores reais do fechamento (2ª aba), não da curva
                fin = float(d.get('finan_usado', 0) or 0)
                sub = float(d.get('fgts_sub_usado', 0) or 0)
                # SELEÇÃO DO PRO SOLUTO POR COLUNA
                pol = d.get('politica', 'Direcional')
                rank = d.get('ranking', 'DIAMANTE')
                ps_max_val = 0.0
                if pol == 'Emcash':
                    ps_max_val = row.get('PS_EmCash', 0.0)
                else:
                    col_rank = f"PS_{rank.title()}" if rank else 'PS_Diamante'
                    if rank == 'AÇO': col_rank = 'PS_Aco'
                    ps_max_val = row.get(col_rank, 0.0)
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
                
                final_cards = []

                if not pool_viavel.empty:
                    min_price_vi = pool_viavel['Valor de Venda'].min()
                    cand_facil = pool_viavel[pool_viavel['Valor de Venda'] == min_price_vi]
                    
                    max_cob = pool_viavel['Cobertura'].max()
                    cand_seguro = pool_viavel[pool_viavel['Cobertura'] == max_cob]
                    
                    ideal_pool = pool_viavel[pool_viavel['Cobertura'] >= 100]
                    if not ideal_pool.empty:
                        max_price_ideal = ideal_pool['Valor de Venda'].max()
                        cand_ideal = ideal_pool[ideal_pool['Valor de Venda'] == max_price_ideal]
                    else:
                        max_price_ideal = pool_viavel['Valor de Venda'].max()
                        cand_ideal = pool_viavel[pool_viavel['Valor de Venda'] == max_price_ideal]
                else:
                      fallback_pool = df_pool.sort_values('Valor de Venda', ascending=True)
                      if not fallback_pool.empty:
                          min_p = fallback_pool['Valor de Venda'].min()
                          cand_facil = fallback_pool[fallback_pool['Valor de Venda'] == min_p].head(5)
                          max_p = fallback_pool['Valor de Venda'].max()
                          cand_ideal = fallback_pool[fallback_pool['Valor de Venda'] == max_p].head(5)
                          cand_seguro = fallback_pool.iloc[[len(fallback_pool)//2]]

                def add_cards_group(label, df_group, css_class):
                    df_u = df_group.drop_duplicates(subset=['Identificador'])
                    for _, row in df_u.head(6).iterrows():
                        final_cards.append({'label': label, 'row': row, 'css': css_class})

                add_cards_group('IDEAL', cand_ideal, 'badge-ideal')
                add_cards_group('SEGURO', cand_seguro, 'badge-seguro')
                add_cards_group('FACILITADO', cand_facil, 'badge-facilitado')

                if not final_cards: st.warning("Nenhuma unidade encontrada.")
                else:
                    cards_html = f"""<div class="scrolling-wrapper">"""
                    
                    for card in final_cards:
                         row = card['row']
                         emp_name = row['Empreendimento']
                         unid_name = row['Identificador']
                         val_fmt = fmt_br(row['Valor de Venda'])
                         aval_fmt = fmt_br(row['Valor de Avaliação Bancária'])
                         label = card['label']
                         css_badge = card['css']
                         
                         cards_html += f"""
                         <div class="card-item">
                            <div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC}; height: 100%; justify-content: flex-start;">
                                <span style="font-size:0.65rem; color:{COR_AZUL_ESC}; opacity:0.8;">PERFIL</span><br>
                                <div style="margin-top:5px; margin-bottom:15px;"><span class="{css_badge}">{label}</span></div>
                                <b style="color:{COR_AZUL_ESC}; font-size:1.1rem;">{emp_name}</b><br>
                                <div style="font-size:0.85rem; color:{COR_TEXTO_MUTED}; text-align:center; border-top:1px solid #eee; padding-top:10px; width:100%;">
                                    <b>Unidade: {unid_name}</b>
                                </div>
                                <div style="margin: 10px 0; width: 100%;">
                                    <div style="font-size:0.8rem; color:#64748b;">Avaliação</div>
                                    <div style="font-weight:bold; color:{COR_AZUL_ESC};">R$ {aval_fmt}</div>
                                    <div style="font-size:0.8rem; color:#64748b; margin-top:5px;">Venda</div>
                                    <div class="price-tag" style="font-size:1.3rem; margin-top:0;">R$ {val_fmt}</div>
                                </div>
                            </div>
                         </div>"""
                    cards_html += "</div>"
                    st.markdown(cards_html, unsafe_allow_html=True)

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
                with f_cols[4]:
                    if "f_pmax_tab_v28" not in st.session_state:
                        st.session_state["f_pmax_tab_v28"] = ""
                    st.text_input("Preço Máx:", key="f_pmax_tab_v28", placeholder="Filtrar teto (R$)")

                df_tab = df_disp_total.copy()
                if f_bairro: df_tab = df_tab[df_tab['Bairro'].isin(f_bairro)]
                if f_emp: df_tab = df_tab[df_tab['Empreendimento'].isin(f_emp)]
                df_tab = df_tab[df_tab['Cobertura'] >= cob_min_val]
                f_pmax = texto_moeda_para_float(st.session_state.get("f_pmax_tab_v28"))
                if f_pmax > 0:
                    df_tab = df_tab[df_tab['Valor de Venda'] <= f_pmax]

                if f_ordem == "Menor Preço": df_tab = df_tab.sort_values('Valor de Venda', ascending=True)
                else: df_tab = df_tab.sort_values('Valor de Venda', ascending=False)

                df_tab_view = df_tab.copy()
                df_tab_view['Valor de Venda'] = df_tab_view['Valor de Venda'].apply(fmt_br)
                df_tab_view['Valor de Avaliação Bancária'] = df_tab_view['Valor de Avaliação Bancária'].apply(fmt_br)
                df_tab_view['Poder_Compra'] = df_tab_view['Poder_Compra'].apply(fmt_br)
                df_tab_view['Cobertura'] = df_tab_view['Cobertura'].apply(lambda x: f"{x:.1f}%")

                st.dataframe(
                    df_tab_view[['Identificador', 'Bairro', 'Empreendimento', 'Valor de Avaliação Bancária', 'Valor de Venda', 'Poder_Compra', 'Cobertura']],
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Identificador": st.column_config.TextColumn("Unidade"),
                        "Valor de Avaliação Bancária": st.column_config.TextColumn("Avaliação (R$)"),
                        "Valor de Venda": st.column_config.TextColumn("Venda (R$)"),
                        "Poder_Compra": st.column_config.TextColumn("Poder Real (R$)"),
                        "Cobertura": st.column_config.TextColumn("Cobertura"),
                    }
                )

        st.markdown("---")
        if st.button("Avançar para Escolha de Unidade", type="primary", use_container_width=True, key="btn_goto_selection"): st.session_state.passo_simulacao = 'selection'; scroll_to_top(); st.rerun()
        st.write("");
        st.markdown('<div data-btn-azul style="display:none" aria-hidden="true"></div>', unsafe_allow_html=True)
        if st.button("Voltar para Valores Aprovados", use_container_width=True, key="btn_pot_v28"): st.session_state.passo_simulacao = 'fechamento_aprovado'; scroll_to_top(); st.rerun()

    elif passo == 'selection':
         d = st.session_state.dados_cliente
         st.markdown("### Escolha de Unidade")
         
         df_disponiveis = df_estoque.copy()
         if df_disponiveis.empty: st.warning("Sem estoque disponível.")
         else:
            emp_names = sorted(df_disponiveis['Empreendimento'].unique())
            idx_emp = 0
            if 'empreendimento_nome' in st.session_state.dados_cliente:
                try: idx_emp = emp_names.index(st.session_state.dados_cliente['empreendimento_nome'])
                except: idx_emp = 0
            emp_escolhido = st.selectbox("Escolha o Empreendimento:", options=emp_names, index=idx_emp, key="sel_emp_new_v3")
            st.session_state.dados_cliente['empreendimento_nome'] = emp_escolhido
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
                    v_aval = fmt_br(u['Valor de Avaliação Bancária'])
                    v_venda = fmt_br(u['Valor de Venda'])
                    return f"{uid} | Aval: R$ {v_aval} | Venda: R$ {v_venda}"
                
                uni_escolhida_id = st.selectbox("Escolha a Unidade:", options=current_uni_ids, index=idx_uni, format_func=label_uni, key="sel_uni_new_v3")
                st.session_state.dados_cliente['unidade_id'] = uni_escolhida_id
                if uni_escolhida_id:
                    u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                    v_aval = u_row['Valor de Avaliação Bancária']; v_venda = u_row['Valor de Venda']
                    # Usar valores reais do fechamento (2ª aba)
                    fin_t = float(d.get('finan_usado', 0) or 0)
                    sub_t = float(d.get('fgts_sub_usado', 0) or 0)
                    # SELEÇÃO DO PRO SOLUTO POR COLUNA
                    pol = d.get('politica', 'Direcional')
                    rank = d.get('ranking', 'DIAMANTE')
                    
                    ps_max_val = 0.0
                    if pol == 'Emcash':
                        ps_max_val = u_row.get('PS_EmCash', 0.0)
                    else:
                        col_rank = f"PS_{rank.title()}" if rank else 'PS_Diamante'
                        if rank == 'AÇO': col_rank = 'PS_Aco'
                        ps_max_val = u_row.get(col_rank, 0.0)

                    # Definir limite de parcelas
                    prazo_max_ps = 66 if pol == 'Emcash' else 84
                    st.session_state.dados_cliente['prazo_ps_max'] = prazo_max_ps

                    poder_t, _ = motor.calcular_poder_compra(d.get('renda', 0), fin_t, sub_t, ps_max_val)
                    # Termômetro usa valor final de venda (se preenchido), senão valor da unidade
                    _vf_raw = st.session_state.get("valor_final_unidade_key")
                    _vf_num = texto_moeda_para_float(_vf_raw)
                    if _vf_num <= 0:
                        valor_para_termo = float(v_venda)
                    else:
                        valor_para_termo = _vf_num
                    percentual_cobertura = min(100, max(0, (poder_t / valor_para_termo) * 100)) if valor_para_termo > 0 else 0
                    cor_term = calcular_cor_gradiente(percentual_cobertura)
                    st.markdown(f"""
                        <div style="margin-top: 20px; padding: 15px; border: 1px solid #e2e8f0; border-radius: 10px; background-color: #f8fafc; text-align: center;">
                            <div style="display: flex; justify-content: space-around; margin-bottom: 10px; font-size: 0.9rem;">
                                <div><b>Valor de Avaliação:</b><br>R$ {fmt_br(v_aval)}</div>
                                <div><b>Valor considerado (Venda):</b><br>R$ {fmt_br(valor_para_termo)}</div>
                            </div>
                            <hr style="margin: 10px 0; border: 0; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0; font-weight: 700; font-size: 0.9rem; color: #002c5d;">TERMÔMETRO DE VIABILIDADE</p>
                            <div style="width: 100%; background-color: #e2e8f0; border-radius: 5px; height: 10px; margin: 10px 0;">
                                <div style="width: {percentual_cobertura}%; background: linear-gradient(90deg, #e30613 0%, #002c5d 100%); height: 100%; border-radius: 5px; transition: width 0.5s;"></div>
                            </div>
                            <small>{percentual_cobertura:.1f}% Coberto</small>
                        </div>
                    """, unsafe_allow_html=True)
                    # Campo Valor Final da Unidade (desconto/alteração) na aba de escolha
                    st.markdown("#### Valor Final da Unidade")
                    v_final_default = float(u_row['Valor de Venda'])
                    if d.get('imovel_valor') and d.get('unidade_id') == uni_escolhida_id:
                        v_final_default = float(d.get('imovel_valor'))
                    if "valor_final_unidade_key" not in st.session_state:
                        st.session_state["valor_final_unidade_key"] = float_para_campo_texto(v_final_default, vazio_se_zero=False)
                    st.text_input("Valor Final de Venda (R$)", key="valor_final_unidade_key", placeholder="Igual ao valor da unidade se não alterar")
                    st.caption("Opcional: preencha se houver desconto ou valor diferente do cadastro. O fechamento será calculado com base neste valor.")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Avançar para Fechamento Financeiro", type="primary", use_container_width=True):
                if uni_escolhida_id:
                    u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                    v_venda_unid = float(u_row['Valor de Venda'])
                    valor_final = texto_moeda_para_float(st.session_state.get("valor_final_unidade_key"))
                    if valor_final > 0:
                        imovel_valor_usar = float(valor_final)
                    else:
                        imovel_valor_usar = v_venda_unid
                    st.session_state.dados_cliente.update({
                        'unidade_id': uni_escolhida_id, 'empreendimento_nome': emp_escolhido,
                        'imovel_valor': imovel_valor_usar, 'imovel_avaliacao': u_row['Valor de Avaliação Bancária'],
                        'finan_estimado': d.get('finan_usado', 0), 'fgts_sub': d.get('fgts_sub_usado', 0),
                        'unid_entrega': u_row.get('Data Entrega', ''),
                        'unid_area': u_row.get('Area', ''),
                        'unid_tipo': u_row.get('Tipologia', ''),
                        'unid_endereco': u_row.get('Endereco', ''),
                        'unid_bairro': u_row.get('Bairro', ''),
                        'volta_caixa_ref': u_row.get('Volta_Caixa_Ref', 0.0)
                    })
                    st.session_state.passo_simulacao = 'payment_flow'; scroll_to_top(); st.rerun()
            st.markdown('<div data-btn-azul style="display:none" aria-hidden="true"></div>', unsafe_allow_html=True)
            if st.button("Voltar para Recomendação de Imóveis", use_container_width=True): st.session_state.passo_simulacao = 'guide'; scroll_to_top(); st.rerun()

    elif passo == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown("### Distribuição da Entrada (Fechamento)")
        # Valores já preenchidos na 2ª aba (Fechamento) e na escolha da unidade (garantir numérico)
        u_valor = float(d.get('imovel_valor', 0) or 0)
        u_nome = d.get('empreendimento_nome', 'N/A')
        u_unid = d.get('unidade_id', 'N/A')
        u_aval = d.get('imovel_avaliacao', u_valor)
        f_u_input = float(d.get('finan_usado', 0) or 0)
        fgts_u_input = float(d.get('fgts_sub_usado', 0) or 0)
        prazo_finan = int(d.get('prazo_financiamento', 360))
        tab_fin = d.get('sistema_amortizacao', 'SAC')
        st.session_state.dados_cliente['finan_usado'] = f_u_input
        st.session_state.dados_cliente['fgts_sub_usado'] = fgts_u_input
        st.session_state.dados_cliente['prazo_financiamento'] = prazo_finan
        st.session_state.dados_cliente['sistema_amortizacao'] = tab_fin

        st.markdown(f"""
        <div class="custom-alert" style="flex-direction: column; align-items: center; text-align: center; padding: 20px;">
            <div style="font-size: 1.1rem; margin-bottom: 5px;">{u_nome} - {u_unid}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Valor Final da Unidade: <b>R$ {fmt_br(u_valor)}</b></div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Financiamento: R$ {fmt_br(f_u_input)} | Subsídio: R$ {fmt_br(fgts_u_input)} | Prazo: {prazo_finan}x | {tab_fin}</div>
        </div>
        """, unsafe_allow_html=True)

        if 'ps_usado' not in st.session_state.dados_cliente: st.session_state.dados_cliente['ps_usado'] = 0.0
        if 'ato_final' not in st.session_state.dados_cliente: st.session_state.dados_cliente['ato_final'] = 0.0
        if 'ato_30' not in st.session_state.dados_cliente: st.session_state.dados_cliente['ato_30'] = 0.0
        if 'ato_60' not in st.session_state.dados_cliente: st.session_state.dados_cliente['ato_60'] = 0.0
        if 'ato_90' not in st.session_state.dados_cliente: st.session_state.dados_cliente['ato_90'] = 0.0
        def _num_val(k, default=0.0):
            v = st.session_state.get(k, default)
            if v is None:
                return default
            if isinstance(v, str):
                return texto_moeda_para_float(v, default)
            try:
                return float(v)
            except (TypeError, ValueError):
                return default

        st.markdown("#### Distribuição da Entrada (Saldo a Pagar)")
        
        if 'ps_u_key' not in st.session_state:
            st.session_state['ps_u_key'] = float_para_campo_texto(st.session_state.dados_cliente.get('ps_usado', 0.0), vazio_se_zero=True)
        ps_atual = _num_val('ps_u_key', 0.0)
        
        # Saldo para atos = Valor - Finan - FGTS - PS
        saldo_para_atos = max(0.0, u_valor - f_u_input - fgts_u_input - ps_atual)
        
        # Inicializa chaves de atos se necessário
        if 'ato_1_key' not in st.session_state:
            st.session_state['ato_1_key'] = float_para_campo_texto(st.session_state.dados_cliente.get('ato_final', 0.0), vazio_se_zero=True)
        if 'ato_2_key' not in st.session_state:
            st.session_state['ato_2_key'] = float_para_campo_texto(st.session_state.dados_cliente.get('ato_30', 0.0), vazio_se_zero=True)
        if 'ato_3_key' not in st.session_state:
            st.session_state['ato_3_key'] = float_para_campo_texto(st.session_state.dados_cliente.get('ato_60', 0.0), vazio_se_zero=True)
        if 'ato_4_key' not in st.session_state:
            st.session_state['ato_4_key'] = float_para_campo_texto(st.session_state.dados_cliente.get('ato_90', 0.0), vazio_se_zero=True)
        
        is_emcash = (d.get('politica') == 'Emcash')
        
        # --- Ato 1 (Imediato): só key + session_state (evita conflito value/key) ---
        st.text_input("Ato (Entrada Imediata)", key="ato_1_key", placeholder="0,00", help="Valor pago no ato da assinatura.")
        r1 = texto_moeda_para_float(st.session_state.get("ato_1_key"))
        st.session_state.dados_cliente['ato_final'] = r1
        
        # Função para distribuir o restante (usa PS atual da session)
        def distribuir_restante(n_parcelas):
            a1_atual = texto_moeda_para_float(st.session_state.get('ato_1_key'))
            ps_atual_cb = texto_moeda_para_float(st.session_state.get('ps_u_key'))
            gap_total = max(0.0, u_valor - f_u_input - fgts_u_input - ps_atual_cb)
            
            # Restante a distribuir nos outros atos
            restante = max(0.0, gap_total - a1_atual)
            
            if restante > 0 and n_parcelas > 0:
                val_per_target = restante / n_parcelas
                s_val = float_para_campo_texto(val_per_target, vazio_se_zero=False)
                if n_parcelas == 2:
                    st.session_state['ato_2_key'] = s_val
                    st.session_state['ato_3_key'] = s_val
                    st.session_state['ato_4_key'] = ""
                elif n_parcelas == 3:
                    st.session_state['ato_2_key'] = s_val
                    st.session_state['ato_3_key'] = s_val
                    st.session_state['ato_4_key'] = s_val
            else:
                st.session_state['ato_2_key'] = ""
                st.session_state['ato_3_key'] = ""
                st.session_state['ato_4_key'] = ""

            st.session_state.dados_cliente['ato_30'] = texto_moeda_para_float(st.session_state['ato_2_key'])
            st.session_state.dados_cliente['ato_60'] = texto_moeda_para_float(st.session_state['ato_3_key'])
            st.session_state.dados_cliente['ato_90'] = texto_moeda_para_float(st.session_state['ato_4_key'])

        st.markdown('<label style="font-size: 0.8rem; font-weight: 600;">Opções de Redistribuição do Saldo Restante:</label>', unsafe_allow_html=True)
        col_dist_a, col_dist_b = st.columns(2)
        
        # Botões de distribuição do restante
        with col_dist_a: 
            st.button("Distribuir Restante em 2x (30/60)", use_container_width=True, key="btn_rest_2x", on_click=distribuir_restante, args=(2,))
        with col_dist_b: 
            st.button("Distribuir Restante em 3x (30/60/90)", use_container_width=True, disabled=is_emcash, key="btn_rest_3x", on_click=distribuir_restante, args=(3,))
        
        st.write("") 
        col_atos_rest1, col_atos_rest2, col_atos_rest3 = st.columns(3)
        
        with col_atos_rest1:
            st.text_input("Ato 30 Dias", key="ato_2_key", placeholder="0,00")
            st.session_state.dados_cliente['ato_30'] = texto_moeda_para_float(st.session_state.get("ato_2_key"))
        with col_atos_rest2:
            st.text_input("Ato 60 Dias", key="ato_3_key", placeholder="0,00")
            st.session_state.dados_cliente['ato_60'] = texto_moeda_para_float(st.session_state.get("ato_3_key"))
        with col_atos_rest3:
            st.text_input("Ato 90 Dias", key="ato_4_key", placeholder="0,00", disabled=is_emcash)
            st.session_state.dados_cliente['ato_90'] = texto_moeda_para_float(st.session_state.get("ato_4_key")) if not is_emcash else 0.0
            
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_ps_val, col_ps_parc = st.columns(2)
        
        # Recuperação do limite de Pro Soluto via coluna da tabela estoque
        ps_max_real = 0.0
        if 'unidade_id' in d and 'empreendimento_nome' in d:
             # Filtra na tabela estoque
             # Note: df_estoque está disponível no escopo de aba_simulador_automacao
             row_u = df_estoque[(df_estoque['Identificador'] == d['unidade_id']) & (df_estoque['Empreendimento'] == d['empreendimento_nome'])]
             if not row_u.empty:
                 row_u = row_u.iloc[0]
                 pol = d.get('politica', 'Direcional')
                 rank = d.get('ranking', 'DIAMANTE')
                 if pol == 'Emcash':
                     ps_max_real = row_u.get('PS_EmCash', 0.0)
                 else:
                     col_rank = f"PS_{rank.title()}" if rank else 'PS_Diamante'
                     if rank == 'AÇO': col_rank = 'PS_Aco'
                     ps_max_real = row_u.get(col_rank, 0.0)

        # Motor Pro Soluto (COMPARADOR + POLITICAS) — limites e parcela corrigida (não é PS/N)
        try:
            mps = metricas_pro_soluto(
                renda=float(d.get("renda", 0) or 0),
                valor_unidade=u_valor,
                politica_ui=str(d.get("politica", "Direcional")),
                ranking=str(d.get("ranking", "DIAMANTE")),
                premissas=_prem,
                df_politicas=df_politicas,
                ps_cap_estoque=float(ps_max_real) if ps_max_real else None,
            )
        except Exception:
            mps = {
                "parcela_max_j8": 0.0,
                "parcela_max_g14": 0.0,
                "ps_max_efetivo": float(ps_max_real or 0),
                "ps_max_comparador_politica": 0.0,
                "cap_valor_unidade": 0.0,
                "prazo_ps_politica": int(d.get("prazo_ps_max", 60) or 60),
            }
        ps_limite_ui = float(mps.get("ps_max_efetivo", 0) or 0)
        prazo_cap_app = int(d.get("prazo_ps_max", 84) or 84)
        pol_prazo = int(mps.get("prazo_ps_politica", prazo_cap_app) or prazo_cap_app)
        parc_max_ui = max(1, min(pol_prazo, prazo_cap_app))

        with col_ps_val:
            st.text_input("Pro Soluto Direcional", key="ps_u_key", placeholder="0,00")
            ps_input_val = texto_moeda_para_float(st.session_state.get("ps_u_key"))
            st.session_state.dados_cliente['ps_usado'] = ps_input_val
            ref_text_ps = f"Limite máximo de Pro Soluto: R$ {fmt_br(ps_limite_ui)}"
            st.markdown(f'<div class="inline-ref" style="background-color: transparent; padding: 0; font-family: inherit; font-size: 0.72rem; color: {COR_AZUL_ESC}; margin-top: -12px; margin-bottom: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; display: block; opacity: 0.9;">{ref_text_ps}</div>', unsafe_allow_html=True)
            st.caption(
                f"Parcela máxima: "
                f"R$ {fmt_br(mps.get('parcela_max_g14', 0))}"
            )
            
        with col_ps_parc:
            if 'parc_ps_key' not in st.session_state:
                try:
                    _p0 = int(d.get('ps_parcelas', min(60, parc_max_ui)) or 1)
                except (TypeError, ValueError):
                    _p0 = 1
                _p0 = max(1, min(_p0, parc_max_ui))
                st.session_state['parc_ps_key'] = str(_p0)
            st.text_input("Parcelas Pro Soluto", key="parc_ps_key", placeholder=f"1 a {parc_max_ui}")
            _parc_i = texto_inteiro(st.session_state.get("parc_ps_key"), default=1, min_v=1, max_v=parc_max_ui)
            parc = _parc_i if _parc_i is not None else 1
            st.session_state.dados_cliente['ps_parcelas'] = parc
            st.markdown(f'<span class="inline-ref">Prazo máx. parcelas: {parc_max_ui} meses</span>', unsafe_allow_html=True)
        
        v_parc = parcela_ps_para_valor(
            float(ps_input_val or 0),
            parc,
            str(d.get("politica", "Direcional")),
            _prem,
        )
        st.session_state.dados_cliente['ps_mensal'] = v_parc
        st.session_state.dados_cliente['ps_mensal_simples'] = (float(ps_input_val or 0) / parc) if parc > 0 else 0.0
        st.markdown(f'<div style="margin-top: -8px; margin-bottom: 15px; font-size: 0.9rem; font-weight: 600; color: {COR_AZUL_ESC}; text-align: center;">Mensalidade PS: R$ {fmt_br(v_parc)} ({parc}x)</div>', unsafe_allow_html=True)
        
        # --- INPUT VOLTA AO CAIXA (NOVO) ---
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        if 'volta_caixa_key' not in st.session_state:
            st.session_state['volta_caixa_key'] = ""

        vc_ref = d.get('volta_caixa_ref', 0.0)
        st.text_input("Volta ao Caixa", key="volta_caixa_key", placeholder="0,00")
        vc_input_val = texto_moeda_para_float(st.session_state.get("volta_caixa_key"))
        
        ref_text_vc = f"Folga Volta ao Caixa: R$ {fmt_br(vc_ref)}"
        st.markdown(f'<div class="inline-ref" style="background-color: transparent; padding: 0; font-family: inherit; font-size: 0.72rem; color: {COR_AZUL_ESC}; margin-top: -12px; margin-bottom: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; display: block; opacity: 0.9;">{ref_text_vc}</div>', unsafe_allow_html=True)
        
        # Recalcular valores atuais para o resumo
        r1_val = st.session_state.dados_cliente['ato_final']
        r2_val = st.session_state.dados_cliente['ato_30']
        r3_val = st.session_state.dados_cliente['ato_60']
        r4_val = st.session_state.dados_cliente['ato_90']
        
        total_entrada_cash = r1_val + r2_val + r3_val + r4_val
        st.session_state.dados_cliente['entrada_total'] = total_entrada_cash
        
        # Inclui o Volta ao Caixa na dedução do GAP FINAL
        gap_final = u_valor - f_u_input - fgts_u_input - ps_input_val - total_entrada_cash - vc_input_val
        if abs(gap_final) > 1.0: st.error(f"Atenção: {'Falta cobrir' if gap_final > 0 else 'Valor excedente de'} R$ {fmt_br(abs(gap_final))}.")
        parcela_fin = calcular_parcela_financiamento(f_u_input, prazo_finan, taxa_fin_vigente(d), tab_fin)
        st.session_state.dados_cliente['parcela_financiamento'] = parcela_fin
        st.markdown("---")
        if st.button("Avançar para Resumo da Simulação", type="primary", use_container_width=True):
            if abs(gap_final) <= 1.0: st.session_state.passo_simulacao = 'summary'; scroll_to_top(); st.rerun()
            else: st.error(f"Não é possível avançar. Saldo pendente: R$ {fmt_br(gap_final)}")
        st.markdown('<div data-btn-azul style="display:none" aria-hidden="true"></div>', unsafe_allow_html=True)
        if st.button("Voltar para Escolha de Unidade", use_container_width=True): st.session_state.passo_simulacao = 'selection'; scroll_to_top(); st.rerun()

    elif passo == 'summary':
        d = st.session_state.dados_cliente
        st.markdown(f"### Resumo da Simulação - {d.get('nome', 'Cliente')}")
        st.markdown(f'<div class="summary-header">DADOS DO IMÓVEL</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="summary-body">
            <b>Empreendimento:</b> {d.get('empreendimento_nome')}<br>
            <b>Unidade:</b> {d.get('unidade_id')}<br>
            <b>Valor Comercial (Venda):</b> <span style="color: {COR_VERMELHO}; font-weight: 800;">R$ {fmt_br(d.get('imovel_valor', 0))}</span><br>
            <b>Avaliação Bancária:</b> R$ {fmt_br(d.get('imovel_avaliacao', 0))}
        </div>""", unsafe_allow_html=True)
        
        # --- NOVO: EXIBIR DETALHES ADICIONAIS ---
        st.markdown(f'<div class="summary-header">DETALHES DA UNIDADE</div>', unsafe_allow_html=True)
        detalhes_html = f"""<div class="summary-body">"""
        if d.get('unid_entrega'): detalhes_html += f"<b>Previsão de Entrega:</b> {d.get('unid_entrega')}<br>"
        if d.get('unid_area'): detalhes_html += f"<b>Área Privativa Total:</b> {d.get('unid_area')} m²<br>"
        if d.get('unid_tipo'): detalhes_html += f"<b>Tipo Planta/Área:</b> {d.get('unid_tipo')}<br>"
        if d.get('unid_endereco') and d.get('unid_bairro'): 
            detalhes_html += f"<b>Localização:</b> {d.get('unid_endereco')} - {d.get('unid_bairro')}"
        detalhes_html += "</div>"
        st.markdown(detalhes_html, unsafe_allow_html=True)
        
        st.markdown(f'<div class="summary-header">PLANO DE FINANCIAMENTO</div>', unsafe_allow_html=True)
        prazo_txt = d.get('prazo_financiamento', 360)
        parcela_texto = f"Parcela Estimada ({d.get('sistema_amortizacao', 'SAC')} - {prazo_txt}x): R$ {fmt_br(d.get('parcela_financiamento', 0))}"
        st.markdown(f"""<div class="summary-body"><b>Financiamento Bancário:</b> R$ {fmt_br(d.get('finan_usado', 0))}<br><b>{parcela_texto}</b><br><b>FGTS + Subsídio:</b> R$ {fmt_br(d.get('fgts_sub_usado', 0))}<br><b>Pro Soluto Total:</b> R$ {fmt_br(d.get('ps_usado', 0))} ({d.get('ps_parcelas')}x de R$ {fmt_br(d.get('ps_mensal', 0))})</div>""", unsafe_allow_html=True)
        st.markdown(f'<div class="summary-header">FLUXO DE ENTRADA (ATO)</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Total de Entrada:</b> R$ {fmt_br(d.get('entrada_total', 0))}<br><hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 10px 0;"><b>Ato:</b> R$ {fmt_br(d.get('ato_final', 0))}<br><b>Ato 30 Dias:</b> R$ {fmt_br(d.get('ato_30', 0))}<br><b>Ato 60 Dias:</b> R$ {fmt_br(d.get('ato_60', 0))}<br><b>Ato 90 Dias:</b> R$ {fmt_br(d.get('ato_90', 0))}</div>""", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("Opções de Resumo (PDF / E-mail)", use_container_width=True): show_export_dialog(d)
        st.markdown("---")
        if st.button("CONCLUIR E SALVAR SIMULAÇÃO", type="primary", use_container_width=True):
            broker_email = st.session_state.get('user_email')
            if broker_email:
                with st.spinner("Gerando PDF e enviando para seu e-mail..."):
                    pdf_bytes_auto = gerar_resumo_pdf(d)
                    if pdf_bytes_auto:
                        sucesso_email, msg_email = enviar_email_smtp(broker_email, d.get('nome', 'Cliente'), pdf_bytes_auto, d, tipo='corretor')
                        if sucesso_email: st.toast("PDF enviado para seu e-mail com sucesso!", icon="📧")
                        else: st.toast(f"Falha no envio automático: {msg_email}", icon="⚠️")
            try:
                conn_save = st.connection("gsheets", type=GSheetsConnection)
                aba_destino = 'BD Simulações' 
                rendas_ind = d.get('rendas_lista', [])
                while len(rendas_ind) < 4: rendas_ind.append(0.0)
                capacidade_entrada = d.get('entrada_total', 0) + d.get('ps_usado', 0)
                nova_linha = {
                    "Nome": d.get('nome'), "CPF": d.get('cpf'), "Data de Nascimento": str(d.get('data_nascimento')),
                    "Prazo Financiamento": d.get('prazo_financiamento'), "Renda Part. 1": rendas_ind[0], "Renda Part. 4": rendas_ind[3],
                    "Renda Part. 3": rendas_ind[2], "Renda Part. 4.1": 0.0, "Ranking": d.get('ranking'),
                    "Política de Pro Soluto": d.get('politica'), "Fator Social": "Sim" if d.get('social') else "Não",
                    "Cotista FGTS": "Sim" if d.get('cotista') else "Não", "Financiamento Aprovado": d.get('finan_f_ref', 0),
                    "Subsídio Máximo": d.get('sub_f_ref', 0), "Pro Soluto Médio": d.get('ps_usado', 0), "Capacidade de Entrada": capacidade_entrada,
                    "Poder de Aquisição Médio": (2 * d.get('renda', 0)) + d.get('finan_f_ref', 0) + d.get('sub_f_ref', 0) + (d.get('imovel_valor', 0) * 0.10),
                    "Empreendimento Final": d.get('empreendimento_nome'), "Unidade Final": d.get('unidade_id'),
                    "Preço Unidade Final": d.get('imovel_valor', 0), "Financiamento Final": d.get('finan_usado', 0),
                    "FGTS + Subsídio Final": d.get('fgts_sub_usado', 0), "Pro Soluto Final": d.get('ps_usado', 0),
                    "Número de Parcelas do Pro Soluto": d.get('ps_parcelas', 0), "Mensalidade PS": d.get('ps_mensal', 0),
                    "Ato": d.get('ato_final', 0), "Ato 30": d.get('ato_30', 0), "Ato 60": d.get('ato_60', 0), "Ato 90": d.get('ato_90', 0),
                    "Renda Part. 2": rendas_ind[1], "Nome do Corretor": st.session_state.get('user_name', ''),
                    "Canal/Imobiliária": st.session_state.get('user_imobiliaria', ''),
                    "Data/Horário": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M:%S"),
                    "Sistema de Amortização": d.get('sistema_amortizacao', 'SAC'),
                    "Quantidade Parcelas Financiamento": d.get('prazo_financiamento', 360),
                    "Quantidade Parcelas Pro Soluto": d.get('ps_parcelas', 0),
                    "Volta ao Caixa": st.session_state.get('volta_caixa_key', 0.0) # Adicionado ao salvamento
                }
                df_novo = pd.DataFrame([nova_linha])
                try:
                    df_existente = conn_save.read(spreadsheet=ID_GERAL, worksheet=aba_destino)
                    df_final_save = pd.concat([df_existente, df_novo], ignore_index=True)
                except: df_final_save = df_novo
                conn_save.update(spreadsheet=ID_GERAL, worksheet=aba_destino, data=df_final_save)
                st.cache_data.clear()
                st.markdown(f'<div class="custom-alert">Salvo em \'{aba_destino}\'!</div>', unsafe_allow_html=True); time.sleep(2); st.session_state.dados_cliente = {}; st.session_state.passo_simulacao = 'input'; scroll_to_top(); st.rerun()
            except Exception as e: st.error(f"Erro ao salvar: {e}")
        st.markdown('<div data-btn-azul style="display:none" aria-hidden="true"></div>', unsafe_allow_html=True)
        if st.button("Voltar para Fechamento Financeiro", use_container_width=True): st.session_state.passo_simulacao = 'payment_flow'; scroll_to_top(); st.rerun()

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas, _df_logins, df_cadastros, premissas_dict = carregar_dados_sistema()
    logo_src = html_std.escape(_src_logo_topo_header(), quote=True)
    st.markdown(
        f'''<header class="header-container" role="banner">
<div class="header-logo-wrap">
<img src="{logo_src}" alt="Direcional Engenharia" class="header-logo-img" decoding="async" loading="eager" />
</div>
<h1 class="header-title"><span class="header-title-muted">Simulador imobiliário</span>&#32;<span class="header-title-accent" aria-label="DV">DV</span></h1>
<div class="header-title-rule" aria-hidden="true"></div>
<p class="header-subtitle">Gestão de <strong>vendas</strong> e <strong>viabilidade</strong> imobiliária</p>
</header>''',
        unsafe_allow_html=True,
    )

    aba_simulador_automacao(df_finan, df_estoque, df_politicas, df_cadastros, premissas_dict)

    st.markdown(f'<div class="footer">Direcional Engenharia - Rio de Janeiro | Developed by Lucas Maia</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
