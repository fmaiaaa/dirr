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

# Regra comercial (planilha / curva): subsídios abaixo deste valor não entram na simulação.
SUBSIDIO_MINIMO_CURVA: float = 1999.99


def subsidio_curva_efetivo(valor) -> float:
    try:
        v = float(valor or 0.0)
    except (TypeError, ValueError):
        return 0.0
    if v < SUBSIDIO_MINIMO_CURVA:
        return 0.0
    return v


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


def _norm_col_name(s: str) -> str:
    return (
        str(s or "")
        .strip()
        .upper()
        .replace("Ç", "C")
        .replace("Ã", "A")
        .replace("Õ", "O")
    )


def _find_pol_col(df: pd.DataFrame, *candidates: str) -> Optional[str]:
    cmap = {_norm_col_name(c): c for c in df.columns}
    for want in candidates:
        k = _norm_col_name(want)
        if k in cmap:
            return cmap[k]
    return None


def _parse_prosoluto_pct(v: Any) -> float:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 0.0
    s = str(v).strip().replace("%", "").replace(" ", "")
    if s == "" or s.lower() == "nan":
        return 0.0
    s = s.replace(",", ".")
    try:
        x = float(s)
    except ValueError:
        return 0.0
    if x > 1.0:
        return x / 100.0
    return float(x)


def _parse_float_cell_pol(v: Any, default: float = 0.0) -> float:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    s = str(v).strip().replace("%", "").replace(" ", "").replace(",", ".")
    if s == "" or s.lower() == "nan":
        return default
    try:
        return float(s)
    except ValueError:
        return default


def politicas_from_dataframe(df: Optional[pd.DataFrame]) -> List[PoliticaPSRow]:
    """
    Interpreta aba POLITICAS: prioriza colunas nomeadas; senão A–F posicionais.
    Ignora classificações repetidas (mantém a primeira — evita bloco histórico duplicado).
    """
    if df is None or df.empty:
        return _default_rows_list()
    out: List[PoliticaPSRow] = []
    seen: set[str] = set()
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    c_cls = _find_pol_col(df, "CLASSIFICAÇÃO", "CLASSIFICACAO", "CLASSIFICACAO")
    c_ps = _find_pol_col(df, "PROSOLUTO", "PRO SOLUTO", "% PS", "%PS")
    c_fx = _find_pol_col(df, "FAIXA RENDA", "FAIXA_RENDA")
    c_f1 = _find_pol_col(df, "FX RENDA 1", "FX_RENDA_1", "FX RENDA1")
    c_f2 = _find_pol_col(df, "FX RENDA 2", "FX_RENDA_2", "FX RENDA2")
    c_pc = _find_pol_col(df, "PARCELAS", "PRAZO PS", "PARCELAS MAX")

    use_named = bool(c_cls and c_ps and c_fx and c_f1 and c_f2 and c_pc)

    for _, row in df.iterrows():
        try:
            if use_named:
                a = row.get(c_cls)
                b = row.get(c_ps)
                c = row.get(c_fx)
                d = row.get(c_f1)
                e = row.get(c_f2)
                f = row.get(c_pc)
            else:
                cols = list(df.columns)
                vals = [row.get(x) for x in cols[:6]]
                if len(vals) < 6:
                    continue
                a, b, c, d, e, f = vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]
            if a is None or str(a).strip() == "" or str(a).lower() == "nan":
                continue
            if "CLASSIF" in str(a).upper():
                continue
            cls_raw = str(a).strip()
            key = _norm_key(cls_raw)
            if key in seen:
                continue
            pct = _parse_prosoluto_pct(b)
            fr = _parse_float_cell_pol(c)
            f1 = _parse_float_cell_pol(d)
            f2 = _parse_float_cell_pol(e)
            pm = _parse_float_cell_pol(f)
            pr = PoliticaPSRow(
                classificacao=cls_raw,
                prosoluto_pct=pct,
                faixa_renda=fr,
                fx_renda_1=f1,
                fx_renda_2=f2,
                parcelas_max=pm,
            )
            if pr.prosoluto_pct > 0 and pr.parcelas_max > 0:
                seen.add(key)
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
    "renda_f1": 2850.0,
    "renda_f2": 4700.0,
    "renda_f3": 8600.0,
    "renda_f4": 12000.0,
    "vv_f2": 275000.0,
    "vv_f3": 350000.0,
    "vv_f4": 500000.0,
    "dire_fin_aa_f1_min": 4.0,
    "dire_fin_aa_f1_max": 5.0,
    "dire_fin_aa_f2_min": 4.75,
    "dire_fin_aa_f2_max": 7.0,
    "dire_fin_aa_f3_min": 7.66,
    "dire_fin_aa_f3_max": 8.16,
    "dire_fin_aa_f4": 10.0,
    "direcional_fin_aa_pct": 8.16,
    "dire_ps_amort_m": 0.013351896270462446,
    "ps_pv_meses_desconto_direcional": 11.0,
}

# Rótulos da coluna A do Excel → chaves internas
_LABEL_MAP = {
    "DIRE PRE": "dire_pre_m",
    "DIRE POS": "dire_pos_m",
    "EMCASH": "emcash_fin_m",
    "TX EMCASH": "tx_emcash_b5",
    "IPCA EMCASH": "ipca_aa",
    "RENDA F1": "renda_f1",
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

# Comparador TX EMCASH, coluna L (ex. L15): =PV($E$2,$K$2,J15,)*-1*0,96
PS_PV_FATOR_COLUNA_L: float = 0.96


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
    """Simulador Pro Soluto, células G14 e C43 (linha simples): (K3 − 30%) × B4."""
    return float(renda or 0.0) * fator_renda_liquido(k3)


def parcela_max_j8(renda: float, k3: float, e1: float) -> float:
    """COMPARADOR J8: B4 * (K3-30%) * (1-E1)."""
    return float(renda or 0.0) * fator_renda_liquido(k3) * (1.0 - float(e1))


def pv_l8_positivo(e2_mensal: float, prazo_k2: int, parcela_j8: float) -> float:
    """
    L8 = -PV(E2, K2, J8) no Excel: valor positivo máximo de Pro Soluto (valor presente de anuidade).
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


def _politica_emcash_ui(politica_ui: str) -> bool:
    return str(politica_ui or "").strip().lower() == "emcash"


def principal_ps_b3_ajustado(valor_ps: float) -> float:
    """SIMULADOR PS / Comparador B3: B41 + B41*((1+0,5%)^4-1)."""
    v = float(valor_ps or 0.0)
    if v <= 0.0:
        return 0.0
    return float(v * (1.0 + ((1.0 + 0.005) ** 4 - 1.0)))


def _pmt_price_positivo(pv: float, taxa_mensal: float, n: int) -> float:
    """Prestação constante (sistema PRICE), valor positivo; pv > 0."""
    r = float(taxa_mensal)
    nper = int(n or 0)
    pvv = float(pv or 0.0)
    if nper <= 0 or pvv <= 0.0 or r <= -1.0:
        return 0.0
    try:
        return float(pvv * r * (1.0 + r) ** nper / ((1.0 + r) ** nper - 1.0))
    except (ZeroDivisionError, OverflowError, ValueError):
        return 0.0


def valor_ps_maximo_parcela_j8(
    parcela_j8: float,
    prazo_meses: int,
    premissas: Optional[Mapping[str, float]],
    politica_ui: str,
) -> float:
    """Maior PS (B41) com PMT(n) ≤ parcela_j8 (inverso de parcela_ps_pmt)."""
    cap = float(parcela_j8 or 0.0)
    n = int(prazo_meses or 0)
    if cap <= 0.0 or n <= 0:
        return 0.0
    p = dict(DEFAULT_PREMISSAS)
    if premissas:
        p.update({k: float(v) for k, v in premissas.items() if v is not None})

    if _politica_emcash_ui(politica_ui):
        e4 = excel_e4_mensal(p["ipca_aa"])
        e1 = excel_e1(p["tx_emcash_b5"], e4)
        e2 = float(p["emcash_fin_m"])
        if e2 <= -1.0:
            return 0.0
        try:
            coef_core = e2 * (1.0 + e2) ** n / ((1.0 + e2) ** n - 1.0)
            coef = float(coef_core) * (1.0 + e1)
            if coef <= 0.0:
                return 0.0
            return float(cap / coef)
        except (ZeroDivisionError, ValueError, OverflowError):
            return 0.0

    r = float(p.get("dire_ps_amort_m", DEFAULT_PREMISSAS["dire_ps_amort_m"]))
    if r <= -1.0:
        return 0.0
    try:
        pv_adj = cap * ((1.0 + r) ** n - 1.0) / (r * (1.0 + r) ** n)
    except (ZeroDivisionError, ValueError, OverflowError):
        return 0.0
    mult = principal_ps_b3_ajustado(1.0)
    if mult <= 0.0:
        return 0.0
    return float(pv_adj / mult)


def parcela_ps_pmt(
    valor_ps: float,
    prazo_meses: int,
    premissas: Optional[Mapping[str, float]],
    politica_ui: str,
) -> float:
    """
    Emcash (UI): I5 — (PMT(E2, n, B41) × -1) × (1+E1).
    Direcional: B43/CE — PMT com principal B3 ajustado e taxa `dire_ps_amort_m` (sem (1+E1)).
    """
    p = dict(DEFAULT_PREMISSAS)
    if premissas:
        p.update({k: float(v) for k, v in premissas.items() if v is not None})
    pv_raw = float(valor_ps or 0.0)
    n = int(prazo_meses or 0)
    if n <= 0 or pv_raw <= 0.0:
        return 0.0

    if _politica_emcash_ui(politica_ui):
        e4 = excel_e4_mensal(p["ipca_aa"])
        e1 = excel_e1(p["tx_emcash_b5"], e4)
        e2 = float(p["emcash_fin_m"])
        if e2 <= -1:
            return 0.0
        try:
            pmt_excel = -pv_raw * (e2 * (1 + e2) ** n) / ((1 + e2) ** n - 1)
            pmt_pos = abs(float(pmt_excel))
        except (ZeroDivisionError, ValueError, OverflowError):
            return 0.0
        return float(pmt_pos * (1.0 + e1))

    taxa_ps = float(p.get("dire_ps_amort_m", DEFAULT_PREMISSAS["dire_ps_amort_m"]))
    pv_adj = principal_ps_b3_ajustado(pv_raw)
    return _pmt_price_positivo(pv_adj, taxa_ps, n)


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
    prazo_ps_ui = int(min(row.parcelas_max, 120.0))
    e4 = excel_e4_mensal(p["ipca_aa"])
    e1 = excel_e1(p["tx_emcash_b5"], e4)
    k3 = k3_lambda(renda, row)
    j8 = parcela_max_j8(renda, k3, e1)
    g14 = parcela_max_g14(renda, k3)
    e2_comp = float(p["emcash_fin_m"])
    if _politica_emcash_ui(politica_ui):
        row_em = politica_row_from_defaults("EMCASH")
        prazo_pv_k2 = int(min(row_em.parcelas_max, 120.0)) if row_em else 66
    else:
        desc = int(float(p.get("ps_pv_meses_desconto_direcional", 11.0)))
        prazo_pv_k2 = max(1, prazo_ps_ui - desc)
    l8_bruto = pv_l8_positivo(e2_comp, prazo_pv_k2, j8)
    l8 = float(l8_bruto) * PS_PV_FATOR_COLUNA_L
    cap_vu = cap_valor_unidade(valor_unidade, row)
    ps_cap_parcela_j8 = valor_ps_maximo_parcela_j8(j8, prazo_ps_ui, p, politica_ui)
    ps_max_calc = valor_max_ps_g15(l8, cap_vu)
    if ps_cap_parcela_j8 > 0.0:
        ps_max_calc = min(ps_max_calc, ps_cap_parcela_j8)
    if ps_cap_estoque is not None and float(ps_cap_estoque) > 0:
        ps_max_efetivo = min(ps_max_calc, float(ps_cap_estoque), cap_vu)
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
        "prazo_ps_politica": prazo_ps_ui,
        "ps_cap_parcela_j8": ps_cap_parcela_j8,
    }


def parcela_ps_para_valor(
    valor_ps: float,
    prazo_meses: int,
    politica_ui: str,
    premissas: Optional[Mapping[str, float]] = None,
    parcela_max_j8: Optional[float] = None,
) -> float:
    """Parcela corrigida; limitada ao teto J8 quando informado."""
    raw = parcela_ps_pmt(valor_ps, prazo_meses, premissas, politica_ui)
    if parcela_max_j8 is None:
        return raw
    j8v = float(parcela_max_j8)
    if j8v <= 0.0:
        return raw
    return float(min(raw, j8v))

# ========================================================================
# core/comparador_emcash.py
# ========================================================================

# -*- coding: utf-8 -*-
from typing import Any, Mapping, Optional


def _politica_emcash(politica: Any) -> bool:
    s = str(politica or "").strip().upper()
    return "EMCASH" in s


def _renda_cliente_financiamento(dados_cliente: Mapping[str, Any]) -> Optional[float]:
    for key in ("renda", "renda_familiar", "renda_mensal"):
        if key not in dados_cliente:
            continue
        raw = dados_cliente.get(key)
        if raw is None:
            continue
        try:
            return float(raw)
        except (TypeError, ValueError):
            continue
    return None


def direcional_fin_aa_pct_por_renda(
    renda_mensal: float, premissas_resolvido: Mapping[str, float]
) -> float:
    p = premissas_resolvido
    r = max(0.0, float(renda_mensal or 0.0))
    rf1 = float(p.get("renda_f1", 2850.0))
    rf2 = float(p.get("renda_f2", 4700.0))
    rf3 = float(p.get("renda_f3", 8600.0))
    a1_lo = float(p.get("dire_fin_aa_f1_min", 4.0))
    a1_hi = float(p.get("dire_fin_aa_f1_max", 5.0))
    a2_lo = float(p.get("dire_fin_aa_f2_min", 4.75))
    a2_hi = float(p.get("dire_fin_aa_f2_max", 7.0))
    a3_lo = float(p.get("dire_fin_aa_f3_min", 7.66))
    a3_hi = float(p.get("dire_fin_aa_f3_max", 8.16))
    a4 = float(p.get("dire_fin_aa_f4", 10.0))
    if r <= rf1:
        return (a1_lo + a1_hi) / 2.0
    if r <= rf2:
        return (a2_lo + a2_hi) / 2.0
    if r <= rf3:
        return (a3_lo + a3_hi) / 2.0
    return a4


def taxa_mensal_financiamento_imobiliario(
    politica: Any,
    premissas: Optional[Mapping[str, float]] = None,
    renda_mensal: Optional[float] = None,
) -> float:
    """
    Taxa mensal usada no PMT / SAC / PRICE do **financiamento do imóvel**.
    - Emcash: mensal direta B4 (0.0089 no Excel de referência).
    - Direcional: por faixa de renda quando `renda_mensal` é informada; senão `direcional_fin_aa_pct`.
    """
    p = dict(DEFAULT_PREMISSAS)
    if premissas:
        p.update({k: float(v) for k, v in premissas.items() if v is not None})
    if _politica_emcash(politica):
        return float(p["emcash_fin_m"])
    if renda_mensal is not None:
        aa = direcional_fin_aa_pct_por_renda(float(renda_mensal), p)
    else:
        aa = float(p.get("direcional_fin_aa_pct", 8.16))
    return (1.0 + aa / 100.0) ** (1.0 / 12.0) - 1.0


def taxa_anual_pct_equivalente(taxa_mensal: float) -> float:
    """Converte taxa mensal efetiva em % a.a. equivalente (composta)."""
    return ((1.0 + float(taxa_mensal)) ** 12 - 1.0) * 100.0


def resolver_taxa_financiamento_anual_pct(
    dados_cliente: Mapping[str, Any],
    premissas: Optional[Mapping[str, float]] = None,
) -> float:
    """Taxa anual em % compatível com calcular_parcela_financiamento e calcular_comparativo_sac_price."""
    renda = _renda_cliente_financiamento(dados_cliente)
    i_m = taxa_mensal_financiamento_imobiliario(
        dados_cliente.get("politica", ""),
        premissas,
        renda_mensal=renda,
    )
    return taxa_anual_pct_equivalente(i_m)

# ========================================================================
# app.py
# ========================================================================

# -*- coding: utf-8 -*-

import logging
import streamlit as st
import pandas as pd
import re
from streamlit_gsheets import GSheetsConnection
import base64
from datetime import datetime, date
import time
import locale
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from pathlib import Path
import pytz
import altair as alt
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
# 0. UTILITÁRIOS
# =============================================================================


def fmt_br(valor):
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"


def _pdf_text_seguro(valor) -> str:
    """
    PyFPDF 1.x (pacote `fpdf`) grava páginas em Latin-1; caracteres como travessão Unicode (U+2014)
    quebram na geração. fpdf2 tolera melhor UTF-8, mas o ambiente pode ter só o `fpdf` antigo.
    """
    if valor is None:
        return ""
    t = str(valor)
    t = (
        t.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2212", "-")
        .replace("\u2026", "...")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )
    try:
        t.encode("latin-1")
        return t
    except UnicodeEncodeError:
        return t.encode("latin-1", errors="replace").decode("latin-1")


def reais_streamlit_md(valor_formatado: str) -> str:
    """Streamlit interpreta $ como delimitador LaTeX; sem escape, 'R$ 1.999,99' vira texto matemático (verde)."""
    return f"R\\$ {valor_formatado}"


def reais_streamlit_html(valor_formatado: str) -> str:
    """Valor monetário em HTML para st.markdown: sem '$' literal, evita modo matemático do Markdown."""
    return f"R&#36; {valor_formatado}"


_WHATSAPP_TEXTO_MAX = 3600


def _wa_escape_texto(valor) -> str:
    """Evita * _ ~ ` nos valores, para não quebrar negrito/itálico no WhatsApp."""
    if valor is None:
        return "-"
    t = str(valor).replace("*", "·").replace("_", " ").replace("~", " ").replace("`", "'")
    t = re.sub(r"\s+", " ", t).strip()
    return t if t else "-"


def montar_mensagem_whatsapp_resumo(
    d: dict,
    *,
    volta_caixa_val: float = 0.0,
    nome_consultor: str = "",
    canal_imobiliaria: str = "",
) -> str:
    """
    Texto para colar ou enviar via api.whatsapp.com/send.
    Formatação: *negrito* em títulos e rótulos; linhas com • e *rótulo:* valor.
    """
    def item(label: str, valor) -> str:
        return f"• *{_wa_escape_texto(label)}:* {_wa_escape_texto(valor)}"

    def brs(key, default=0):
        return f"R$ {fmt_br(d.get(key, default))}"

    soc = "Sim" if d.get("social") else "Não"
    cot = "Sim" if d.get("cotista") else "Não"
    pol = d.get("politica", "") or "-"
    rank = d.get("ranking", "") or "-"
    amort = nome_sistema_amortizacao_completo(str(d.get("sistema_amortizacao", "SAC")))
    prazo = d.get("prazo_financiamento", 360)
    rendas = list(d.get("rendas_lista") or [])

    linhas = [
        "*Resumo da simulação — Direcional*",
        "",
        "*Dados do cliente*",
        item("Nome", d.get("nome", "Cliente")),
        item("CPF", d.get("cpf", "-")),
        item("Data de nascimento", d.get("data_nascimento", "-")),
        item("Renda familiar total", brs("renda", 0)),
    ]
    for i, rv in enumerate(rendas[:4], start=1):
        try:
            rvf = float(rv or 0)
        except (TypeError, ValueError):
            rvf = 0.0
        if rvf > 0:
            linhas.append(item(f"Renda participante {i}", f"R$ {fmt_br(rvf)}"))

    linhas.extend(
        [
            "",
            "*Perfil e crédito*",
            item("Política de Pro Soluto", pol),
            item("Ranking", rank),
            item("Fator social", soc),
            item("Cotista FGTS", cot),
            item("Financiamento de referência (curva)", brs("finan_f_ref", 0)),
            item("Subsídio de referência (curva)", brs("sub_f_ref", 0)),
            "",
            "*Dados do imóvel*",
            item("Empreendimento", d.get("empreendimento_nome", "-")),
            item("Unidade", d.get("unidade_id", "-")),
            item("Valor comercial de venda", brs("imovel_valor", 0)),
            item("Avaliação bancária", brs("imovel_avaliacao", 0)),
        ]
    )
    if d.get("unid_entrega"):
        linhas.append(item("Previsão de entrega", d.get("unid_entrega")))
    if d.get("unid_area"):
        linhas.append(item("Área privativa", f"{d.get('unid_area')} m²"))
    if d.get("unid_tipo"):
        linhas.append(item("Tipologia", d.get("unid_tipo")))
    if d.get("unid_endereco") and d.get("unid_bairro"):
        linhas.append(
            item("Localização", f"{d.get('unid_endereco')} - {d.get('unid_bairro')}")
        )

    linhas.extend(
        [
            "",
            "*Financiamento*",
            item("Financiamento utilizado", brs("finan_usado", 0)),
            item("Sistema de amortização e prazo", f"{amort} — {prazo} meses"),
            item("Parcela estimada do financiamento", brs("parcela_financiamento", 0)),
            item("Fundo de Garantia do Tempo de Serviço e subsídio", brs("fgts_sub_usado", 0)),
            "",
            "*Entrada e Pro Soluto*",
            item("Pro Soluto (valor)", brs("ps_usado", 0)),
            item("Número de parcelas do Pro Soluto", d.get("ps_parcelas", "-")),
            item("Mensalidade do Pro Soluto", brs("ps_mensal", 0)),
            item("Total em atos (ato 0 e parcelados)", brs("entrada_total", 0)),
            item("Ato 0", brs("ato_final", 0)),
            item("Ato 30", brs("ato_30", 0)),
            item("Ato 60", brs("ato_60", 0)),
        ]
    )
    if not _politica_emcash(d.get("politica")):
        linhas.append(item("Ato 90", brs("ato_90", 0)))
    _ent_tot = float(d.get("entrada_total", 0) or 0) + float(d.get("ps_usado", 0) or 0)
    linhas.append(item("Entrada total (atos e Pro Soluto)", f"R$ {fmt_br(_ent_tot)}"))

    linhas.append(item("Volta ao caixa", f"R$ {fmt_br(volta_caixa_val)}"))
    try:
        vref = float(d.get("volta_caixa_ref", 0) or 0)
    except (TypeError, ValueError):
        vref = 0.0
    if vref > 0:
        linhas.append(item("Referência folga volta ao caixa", brs("volta_caixa_ref", 0)))

    nc = (nome_consultor or "").strip()
    ci = (canal_imobiliaria or "").strip()
    if nc or ci:
        linhas.extend(["", "*Consultor*"])
        if nc:
            linhas.append(item("Nome", nc))
        if ci:
            linhas.append(item("Canal ou imobiliária", ci))

    linhas.extend(
        [
            "",
            f"_Simulação em {d.get('data_simulacao', date.today().strftime('%d/%m/%Y'))}_",
        ]
    )

    msg = "\n".join(linhas)
    if len(msg) > _WHATSAPP_TEXTO_MAX:
        msg = (
            msg[: _WHATSAPP_TEXTO_MAX - 80].rstrip()
            + "\n\n_(Mensagem encurtada; use o PDF para o detalhe completo.)_"
        )
    return msg


def _url_whatsapp_enviar_texto(texto: str) -> str:
    return f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto)}"


def _normalizar_separador_decimal_duas_casas(s: str) -> str:
    """`,` ou `.` como decimal na antepenúltima posição com 2 dígitos finais (por exemplo, 1.234,56 no padrão brasileiro ou 1,234.56 no padrão internacional). Evita 2.000 ser lido como mil."""
    s = str(s).strip()
    if len(s) < 3 or s[-3] not in ",." or not s[-2:].isdigit():
        return s
    dec_sep = s[-3]
    frac = s[-2:]
    head = s[:-3]
    if dec_sep == ",":
        head = head.replace(".", "").replace(",", "")
    else:
        head = head.replace(",", "").replace(".", "")
    return f"{head}.{frac}"


def safe_float_convert(val):
    if pd.isnull(val) or val == "":
        return 0.0
    if isinstance(val, bool):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace("R$", "").replace("\u00a0", " ").strip()
    s_compact = re.sub(r"\s+", "", s)
    s_try = _normalizar_separador_decimal_duas_casas(s_compact)
    try:
        return float(s_try)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    if "," in s_compact:
        s2 = s_compact.replace(".", "").replace(",", ".")
    else:
        if s_compact.count(".") >= 1:
            s2 = s_compact.replace(".", "")
        else:
            s2 = s_compact
    try:
        return float(s2)
    except ValueError:
        return 0.0


def texto_moeda_para_float(s, default=0.0):
    """Converte texto livre (BR/US) em float; vazio → default. Vírgula ou ponto antes de 2 casas finais = decimal."""
    if s is None:
        return default
    if isinstance(s, bool):
        return default
    if isinstance(s, (int, float)):
        return float(s)
    t = str(s).strip()
    if t == "":
        return default
    t = t.replace("R$", "").replace("r$", "").replace("\u00a0", " ")
    t = re.sub(r"\s+", "", t)
    if t == "":
        return default
    t = _normalizar_separador_decimal_duas_casas(t)
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


def clamp_moeda_positiva(v, maximo=None):
    """Garante valor >= 0; se maximo > 0, aplica teto (por exemplo, curva de financiamento e subsídio ou teto do Pro Soluto)."""
    try:
        x = float(v or 0.0)
    except (TypeError, ValueError):
        x = 0.0
    x = max(0.0, x)
    if maximo is not None and float(maximo) > 0:
        x = min(x, float(maximo))
    return x


_AMORTIZACAO_NOME_COMPLETO = {
    "SAC": "SAC",
    "PRICE": "PRICE",
}


def nome_sistema_amortizacao_completo(codigo: str) -> str:
    c = str(codigo or "").strip().upper()
    return _AMORTIZACAO_NOME_COMPLETO.get(c, str(codigo or ""))


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

def scroll_to_top():
    js = """<script>var body = window.parent.document.querySelector(".main"); if (body) { body.scrollTop = 0; } window.scrollTo(0, 0);</script>"""
    st.components.v1.html(js, height=0)

def inject_enter_confirma_campo():
    """Enter em campo de texto não submete o fluxo: apenas confirma o campo (blur)."""
    js = r"""
<script>
(function () {
  function isTextLike(el) {
    if (!el || !el.closest) return false;
    return el.closest('[data-testid="stTextInput"]') != null
      || el.closest('[data-testid="stNumberInput"]') != null
      || el.closest('[data-baseweb="input"]') != null;
  }
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" || e.isComposing) return;
    var t = e.target;
    if (!t || (t.tagName !== "INPUT" && t.tagName !== "TEXTAREA")) return;
    if (t.type === "submit" || t.type === "button" || t.type === "file") return;
    if (t.closest("form[data-testid=\"stForm\"]")) {
      e.preventDefault();
      e.stopPropagation();
      t.blur();
      return;
    }
    if (isTextLike(t)) {
      e.preventDefault();
      t.blur();
    }
  }, true);
})();
</script>
"""
    st.components.v1.html(js, height=0, width=0)


def inject_login_password_manager_fields():
    """Garante atributos que gestores de palavras-passe e o navegador usam para o par e-mail + senha."""
    js = r"""
<script>
(function () {
  var doc = window.parent.document;
  function patchLoginInputs() {
    var forms = doc.querySelectorAll('[data-testid="stForm"]');
    for (var fi = 0; fi < forms.length; fi++) {
      var form = forms[fi];
      var inputs = form.querySelectorAll("input");
      var passEl = null;
      var i;
      for (i = 0; i < inputs.length; i++) {
        if (inputs[i].type === "password") { passEl = inputs[i]; break; }
      }
      if (!passEl) continue;
      var userEl = null;
      for (i = 0; i < inputs.length; i++) {
        var el = inputs[i];
        if (el === passEl) continue;
        var t = (el.type || "").toLowerCase();
        if (t === "text" || t === "email" || t === "") { userEl = el; break; }
      }
      if (!userEl) continue;
      userEl.setAttribute("autocomplete", "username");
      userEl.setAttribute("name", "username");
      passEl.setAttribute("autocomplete", "current-password");
      passEl.setAttribute("name", "password");
    }
  }
  patchLoginInputs();
  setTimeout(patchLoginInputs, 150);
  setTimeout(patchLoginInputs, 600);
})();
</script>
"""
    st.components.v1.html(js, height=0, width=0)

# =============================================================================
# 1. CARREGAMENTO DE DADOS
# =============================================================================

_COLS_HOME_BANNERS = ("Ordem", "URL_Imagem", "Titulo", "Ativo", "Tela_Cheia", "Descricao")


def normalizar_df_home_banners(df: pd.DataFrame | None) -> pd.DataFrame:
    """Planilha BD Home Banners: Ordem, URL_Imagem, Titulo, Ativo, Tela_Cheia, Descricao."""
    if df is None or df.empty:
        return pd.DataFrame(columns=list(_COLS_HOME_BANNERS))
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    ren = {
        "ordem": "Ordem",
        "URL Imagem": "URL_Imagem",
        "url_imagem": "URL_Imagem",
        "Título": "Titulo",
        "titulo": "Titulo",
        "ativo": "Ativo",
        "tela cheia": "Tela_Cheia",
        "Tela cheia": "Tela_Cheia",
        "tela_cheia": "Tela_Cheia",
        "Descrição": "Descricao",
        "descricao": "Descricao",
        "desc": "Descricao",
    }
    for a, b in list(ren.items()):
        if a in out.columns and a != b:
            out = out.rename(columns={a: b})
    for c in _COLS_HOME_BANNERS:
        if c not in out.columns:
            out[c] = None if c == "Ordem" else ""
    return out[list(_COLS_HOME_BANNERS)].copy()


def banner_ativo_sim(val) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    s = str(val).strip().upper()
    return s in ("SIM", "S", "TRUE", "1", "YES", "Y", "ATIVO", "VERDADEIRO")


def banner_tela_cheia_sim(val) -> bool:
    """SIM na coluna Tela_Cheia habilita clique para ver o banner em tela cheia (com descrição opcional)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    s = str(val).strip().upper()
    return s in ("SIM", "S", "TRUE", "1", "YES", "Y")


def login_row_is_adm(row: pd.Series) -> bool:
    v = row.get("Adm")
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return False
    return str(v).strip().upper() == "SIM"


def _img_url_seguro_https(url: str) -> str | None:
    u = (url or "").strip()
    if not u.startswith("https://"):
        return None
    try:
        p = urllib.parse.urlparse(u)
        if p.scheme != "https" or not p.netloc:
            return None
    except Exception:
        return None
    return html_std.escape(u, quote=True)


def _banner_descricao_html_segura(texto: str) -> str:
    t = str(texto or "").strip()
    if not t:
        return ""
    return html_std.escape(t)


def render_faixa_home_banners(df_banners: pd.DataFrame) -> None:
    df = normalizar_df_home_banners(df_banners)
    if df.empty:
        return
    df = df[df["Ativo"].apply(banner_ativo_sim)]
    if df.empty:
        return
    df = df.copy()
    df["_sort"] = pd.to_numeric(df["Ordem"], errors="coerce")
    df = df.sort_values("_sort", na_position="last")
    cards: list[str] = []
    lb_idx = 0
    for _, row in df.iterrows():
        src = _img_url_seguro_https(str(row.get("URL_Imagem", "") or ""))
        if not src:
            continue
        tit = str(row.get("Titulo", "") or "").strip()
        tit_esc = html_std.escape(tit)
        desc_raw = str(row.get("Descricao", "") or "").strip()
        desc_esc = _banner_descricao_html_segura(desc_raw)
        desc_block = ""
        if desc_esc:
            desc_block = (
                f'<div class="home-banner-lb-desc" style="white-space:pre-wrap;">{desc_esc}</div>'
            )
        cid = f"home-banner-lb-{lb_idx}"
        lb_idx += 1
        cards.append(
            f'<div class="home-banner-lb-root">'
            f'<input type="checkbox" id="{cid}" class="home-banner-lb-input" autocomplete="off" '
            f'aria-hidden="true" tabindex="-1" />'
            f'<label for="{cid}" class="home-banner-card home-banner-card--fs" title="Ampliar imagem">'
            f'<img src="{src}" alt="{tit_esc}" loading="lazy" decoding="async" />'
            f'<div class="home-banner-title">{tit_esc}</div>'
            f'<span class="home-banner-fs-hint">Clique para ampliar</span></label>'
            f'<div class="home-banner-lb-panel" role="presentation">'
            f'<label for="{cid}" class="home-banner-lb-backdrop" aria-label="Fechar"></label>'
            f'<div class="home-banner-lb-inner" role="dialog" aria-label="{tit_esc}">'
            f'<img class="home-banner-lb-img" src="{src}" alt="{tit_esc}" loading="lazy" decoding="async" />'
            f"{desc_block}"
            f'<label for="{cid}" class="home-banner-lb-close" aria-label="Fechar" title="Fechar">×</label>'
            f"</div></div></div>"
        )
    if not cards:
        return
    st.markdown(
        '<div class="home-banners-wrap" role="region" aria-label="Campanhas comerciais">'
        '<h2 class="home-banners-section-title">Campanhas comerciais</h2>'
        '<div class="home-banners-strip-outer">'
        '<div class="home-banners-strip" role="group" aria-label="Miniaturas de campanhas">'
        + "".join(cards)
        + "</div></div></div>",
        unsafe_allow_html=True,
    )


def gravar_nova_linha_home_banner(
    ordem: int,
    url_imagem: str,
    titulo: str,
    ativo_sim: bool,
    tela_cheia_sim: bool = False,
    descricao: str = "",
) -> tuple[bool, str]:
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_raw = conn.read(spreadsheet=ID_GERAL, worksheet="BD Home Banners")
        df_ex = normalizar_df_home_banners(df_raw)
        ativo_txt = "SIM" if ativo_sim else "NÃO"
        tc_txt = "SIM" if tela_cheia_sim else "NÃO"
        nova = pd.DataFrame(
            [
                {
                    "Ordem": int(ordem),
                    "URL_Imagem": url_imagem.strip(),
                    "Titulo": titulo.strip(),
                    "Ativo": ativo_txt,
                    "Tela_Cheia": tc_txt,
                    "Descricao": (descricao or "").strip(),
                }
            ]
        )
        df_final = pd.concat([df_ex, nova], ignore_index=True)
        conn.update(spreadsheet=ID_GERAL, worksheet="BD Home Banners", data=df_final)
        return True, ""
    except Exception as e:
        return False, str(e)


def excluir_linha_home_banner(indice_linha: int) -> tuple[bool, str]:
    """Remove uma linha da aba BD Home Banners pelo índice (0 = primeira linha de dados na leitura normalizada)."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_raw = conn.read(spreadsheet=ID_GERAL, worksheet="BD Home Banners")
        df_ex = normalizar_df_home_banners(df_raw)
        df_ex = df_ex.reset_index(drop=True)
        n = len(df_ex)
        if n == 0:
            return False, "A planilha de banners está vazia."
        if indice_linha < 0 or indice_linha >= n:
            return False, "Linha inválida."
        df_new = df_ex.drop(index=indice_linha).reset_index(drop=True)
        conn.update(spreadsheet=ID_GERAL, worksheet="BD Home Banners", data=df_new)
        return True, ""
    except Exception as e:
        return False, str(e)


def _rotulo_opcao_excluir_banner(df_bn: pd.DataFrame, i: int) -> str:
    r = df_bn.iloc[i]
    ordem = r.get("Ordem", "")
    tit = str(r.get("Titulo", "") or "").strip()
    tit = (tit[:42] + "…") if len(tit) > 43 else tit
    url = str(r.get("URL_Imagem", "") or "").strip()
    host = ""
    try:
        host = urllib.parse.urlparse(url).netloc[:28] if url else ""
    except Exception:
        host = ""
    sufixo = f" — {host}" if host else ""
    return f"Linha {i + 1} · Ordem {ordem} · {tit or '(sem título)'}{sufixo}"


_COLS_LOGINS = ["Email", "Senha", "Nome", "Cargo", "Imobiliaria", "Telefone", "Adm"]

_MAPA_LOGINS = {
    "Imobiliária/Canal IMOB": "Imobiliaria",
    "Cargo": "Cargo",
    "Nome": "Nome",
    "Email": "Email",
    "E-mail": "Email",
    "Escolha uma senha para o simulador": "Senha",
    "Senha": "Senha",
    "Número de telefone": "Telefone",
    "Telefone": "Telefone",
    "ADM?": "Adm",
}


def _normalizar_df_logins_raw(df_logins: pd.DataFrame) -> pd.DataFrame:
    df_logins = df_logins.copy()
    df_logins.columns = [str(c).strip() for c in df_logins.columns]
    df_logins = df_logins.rename(columns=_MAPA_LOGINS)
    if "Email" in df_logins.columns:
        df_logins["Email"] = df_logins["Email"].astype(str).str.strip().str.lower()
    if "Senha" in df_logins.columns:
        df_logins["Senha"] = df_logins["Senha"].astype(str).str.strip()
    return df_logins


@st.cache_data(ttl=300, show_spinner=False)
def carregar_apenas_logins() -> pd.DataFrame:
    """Só BD Logins — tela de login sem carregar estoque/financiamentos (mais rápido)."""
    try:
        if "connections" not in st.secrets:
            return pd.DataFrame(columns=_COLS_LOGINS)
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_logins = conn.read(spreadsheet=ID_GERAL, worksheet="BD Logins")
        return _normalizar_df_logins_raw(df_logins)
    except Exception:
        return pd.DataFrame(columns=_COLS_LOGINS)


@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados_sistema():
    try:
        if "connections" not in st.secrets:
            return (
                pd.DataFrame(),
                pd.DataFrame(),
                pd.DataFrame(),
                pd.DataFrame(),
                pd.DataFrame(),
                dict(DEFAULT_PREMISSAS),
            )
        conn = st.connection("gsheets", type=GSheetsConnection)
        def limpar_moeda(val): return safe_float_convert(val)

        # Histórico em BD Simulações não é mais carregado na UI (gravação no resumo mantida)
        df_cadastros = pd.DataFrame()

        # 1. POLITICAS (Pro Soluto — comparador)
        df_politicas = pd.DataFrame()
        for ws_pol in ("POLITICAS", "BD Politicas", "BD Políticas"):
            try:
                df_politicas = conn.read(spreadsheet=ID_GERAL, worksheet=ws_pol)
                df_politicas.columns = [str(c).strip() for c in df_politicas.columns]
                if not df_politicas.empty:
                    break
            except Exception:
                continue

        # 2. FINANCIAMENTOS
        try:
            df_finan = conn.read(spreadsheet=ID_GERAL, worksheet="BD Financiamentos")
            df_finan.columns = [str(c).strip() for c in df_finan.columns]
            for col in df_finan.columns: df_finan[col] = df_finan[col].apply(limpar_moeda)
        except: 
            df_finan = pd.DataFrame()

        # 3. ESTOQUE
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

        try:
            df_hb_raw = conn.read(spreadsheet=ID_GERAL, worksheet="BD Home Banners")
            df_home_banners = normalizar_df_home_banners(df_hb_raw)
        except Exception:
            df_home_banners = pd.DataFrame(columns=list(_COLS_HOME_BANNERS))

        return df_finan, df_estoque, df_politicas, df_cadastros, df_home_banners, premissas_dict
    except Exception as e:
        st.error(f"Erro dados: {e}")
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            dict(DEFAULT_PREMISSAS),
        )

# =============================================================================
# 2. MOTOR E FUNÇÕES
# =============================================================================

class MotorRecomendacao:
    def __init__(self, df_finan, df_estoque, df_politicas):
        self.df_finan = df_finan
        self.df_estoque = df_estoque
        self.df_politicas = df_politicas # Mantido apenas para compatibilidade, não usado logicamente

    def obter_enquadramento(self, renda, social, cotista, valor_avaliacao=250000):
        """Lê a planilha BD Financiamentos: linha pela renda mais próxima; colunas Finan_* e Subsidio_*."""
        if self.df_finan.empty:
            return 0.0, 0.0, "N/A"
        if valor_avaliacao <= 275000:
            faixa = "F2"
        elif valor_avaliacao <= 350000:
            faixa = "F3"
        else:
            faixa = "F4"
        renda_col = pd.to_numeric(self.df_finan["Renda"], errors="coerce").fillna(0)
        idx = (renda_col - float(renda)).abs().idxmin()
        row = self.df_finan.iloc[idx]
        s, c = ("Sim" if social else "Nao"), ("Sim" if cotista else "Nao")
        col_fin = f"Finan_Social_{s}_Cotista_{c}_{faixa}"
        col_sub = f"Subsidio_Social_{s}_Cotista_{c}_{faixa}"
        vf = row.get(col_fin, 0.0)
        vs = row.get(col_sub, 0.0)
        return float(vf), subsidio_curva_efetivo(vs), faixa

    def obter_quatro_combinacoes_f2_f3_f4(self, renda):
        """
        As 4 combinações Social×Cotista nas faixas F2, F3 e F4 (BD Financiamentos), linha = renda mais próxima.
        Colunas: Finan_Social_{Sim|Nao}_Cotista_{Sim|Nao}_{F2|F3|F4} e Subsidio_*.
        """
        linhas = []
        meta = [
            (False, False, "Social não · Não cotista"),
            (True, False, "Social sim · Não cotista"),
            (False, True, "Social não · Cotista"),
            (True, True, "Social sim · Cotista"),
        ]
        faixas = ("F2", "F3", "F4")

        def _cell(row, col_name):
            v = row.get(col_name, 0.0)
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        if self.df_finan.empty or "Renda" not in self.df_finan.columns:
            for social, cotista, rotulo in meta:
                z = {"social": social, "cotista": cotista, "rotulo": rotulo}
                for fz in faixas:
                    z[f"fin_{fz}"] = 0.0
                    z[f"sub_{fz}"] = 0.0
                linhas.append(z)
            return linhas

        renda_col = pd.to_numeric(self.df_finan["Renda"], errors="coerce").fillna(0)
        idx = (renda_col - float(renda)).abs().idxmin()
        row = self.df_finan.iloc[idx]
        for social, cotista, rotulo in meta:
            s = "Sim" if social else "Nao"
            c = "Sim" if cotista else "Nao"
            entry = {"social": social, "cotista": cotista, "rotulo": rotulo}
            for fz in faixas:
                entry[f"fin_{fz}"] = _cell(row, f"Finan_Social_{s}_Cotista_{c}_{fz}")
                entry[f"sub_{fz}"] = subsidio_curva_efetivo(
                    _cell(row, f"Subsidio_Social_{s}_Cotista_{c}_{fz}")
                )
            linhas.append(entry)
        return linhas

    def calcular_poder_compra(self, renda, finan, fgts_sub, val_ps_limite):
        return (2 * renda) + finan + fgts_sub + val_ps_limite, val_ps_limite

_DIR_SIM_APP = Path(__file__).resolve().parent


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
    """Imagem local (ficha Vendas RJ); senão fallback neutro."""
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


def _resolver_png_raiz(nome: str) -> Path | None:
    """Procura PNG/JPG pelo nome exato na pasta do app, assets/ ou raiz do repo."""
    for base in (_DIR_SIM_APP, _DIR_SIM_APP.parent):
        for sub in ("", "assets"):
            rel = Path(sub) / nome if sub else Path(nome)
            p = base / rel
            if p.is_file():
                return p
    return None


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

    bg_url = _css_url_fundo_simulador().replace("&", "&amp;")
    st.markdown(f"""
        <style>
/* ==========================================================================
   Direcional Elite — UI refresh (Streamlit)
   - Cleaner typography and spacing
   - Modern cards, buttons, inputs
   - Better responsiveness
   ========================================================================== */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@600;700;800&display=swap');

:root {
  --de-font: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  --de-font-display: 'Montserrat', var(--de-font);

  --de-bg: #070B13;
  --de-surface: rgba(255,255,255,0.06);
  --de-surface-2: rgba(255,255,255,0.10);
  --de-border: rgba(255,255,255,0.12);
  --de-border-2: rgba(255,255,255,0.18);

  --de-text: rgba(255,255,255,0.92);
  --de-text-dim: rgba(255,255,255,0.72);
  --de-text-mute: rgba(255,255,255,0.55);

  --de-accent: #7C3AED;
  --de-accent-2: #22C55E;
  --de-warn: #F59E0B;
  --de-danger: #EF4444;

  --de-shadow: 0 18px 50px rgba(0,0,0,0.55);
  --de-shadow-soft: 0 10px 30px rgba(0,0,0,0.35);

  --de-radius: 16px;
  --de-radius-sm: 12px;
  --de-pad: 18px;
}

@keyframes deGradientFlow {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}

/* Base */
html, body, [class*='css'], [data-testid='stAppViewContainer'] * {
  font-family: var(--de-font) !important;
}

/* App background */
html body [data-testid='stAppViewContainer'] {
  background:
    radial-gradient(1200px 700px at 12% 15%, rgba(124,58,237,0.22) 0%, rgba(124,58,237,0.0) 60%),
    radial-gradient(900px 520px at 85% 18%, rgba(34,197,94,0.18) 0%, rgba(34,197,94,0.0) 62%),
    radial-gradient(1200px 700px at 50% 115%, rgba(59,130,246,0.12) 0%, rgba(59,130,246,0.0) 55%),
    linear-gradient(180deg, #060814 0%, #070B13 55%, #060814 100%);
  color: var(--de-text) !important;
}

/* Reduce Streamlit default top padding and keep content centered */
section[data-testid='stMain'] > div {
  padding-top: 1.15rem !important;
  padding-bottom: 2.0rem !important;
  max-width: 1320px;
}

/* Headings */
h1, h2, h3, h4 {
  font-family: var(--de-font-display) !important;
  letter-spacing: -0.02em;
}

h1 { font-weight: 800 !important; }
h2 { font-weight: 800 !important; }
h3 { font-weight: 700 !important; }

/* Subtle top brand bar */
header[data-testid='stHeader'] {
  background: transparent !important;
}

header[data-testid='stHeader']::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 10000;
  background: linear-gradient(90deg, rgba(124,58,237,0.0), rgba(124,58,237,1.0), rgba(34,197,94,1.0), rgba(59,130,246,1.0), rgba(124,58,237,0.0));
  background-size: 200% 100%;
  animation: deGradientFlow 10s linear infinite;
  box-shadow: 0 0 18px rgba(124,58,237,0.35);
}

/* Hide Streamlit "running" status and footer */
#MainMenu, footer, header [data-testid='stStatusWidget'] { visibility: hidden; }

/* Cards (containers) */
[data-testid='stVerticalBlockBorderWrapper'] {
  background: var(--de-surface);
  border: 1px solid var(--de-border);
  border-radius: var(--de-radius);
  box-shadow: var(--de-shadow-soft);
}

/* Make inner container padding nicer */
[data-testid='stVerticalBlock'] {
  gap: 0.65rem;
}

/* Tabs */
button[data-baseweb='tab'] {
  color: var(--de-text-dim) !important;
  border-radius: 999px !important;
  padding: 10px 14px !important;
  margin-right: 6px !important;
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
}

button[data-baseweb='tab'][aria-selected='true'] {
  color: var(--de-text) !important;
  background: rgba(124,58,237,0.22) !important;
  border-color: rgba(124,58,237,0.45) !important;
}

/* Buttons */
.stButton > button {
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  background: rgba(255,255,255,0.07) !important;
  color: var(--de-text) !important;
  padding: 0.60rem 0.90rem !important;
  font-weight: 700 !important;
  transition: transform 120ms ease, background 120ms ease, border-color 120ms ease;
}

.stButton > button:hover {
  transform: translateY(-1px);
  border-color: rgba(255,255,255,0.22) !important;
  background: rgba(255,255,255,0.10) !important;
}

.stButton > button:active {
  transform: translateY(0px);
}

/* Primary button style when Streamlit sets it */
.stButton > button[kind='primary'] {
  background: linear-gradient(135deg, rgba(124,58,237,0.95) 0%, rgba(99,102,241,0.95) 55%, rgba(34,197,94,0.90) 120%) !important;
  border-color: rgba(124,58,237,0.55) !important;
  box-shadow: 0 14px 30px rgba(124,58,237,0.22);
}

/* Inputs */
[data-baseweb='input'] input,
[data-baseweb='textarea'] textarea,
[data-baseweb='select'] > div {
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  border-radius: 12px !important;
  color: var(--de-text) !important;
}

[data-baseweb='input'] input:focus,
[data-baseweb='textarea'] textarea:focus {
  border-color: rgba(124,58,237,0.55) !important;
  box-shadow: 0 0 0 3px rgba(124,58,237,0.18) !important;
}

label, .stMarkdown, .stText, p { color: var(--de-text) !important; }
small, .stCaption, .stMarkdown small { color: var(--de-text-mute) !important; }

/* Metric cards */
[data-testid='stMetric'] {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.10);
  padding: 14px 14px;
  border-radius: 14px;
}

[data-testid='stMetricLabel'] p { color: var(--de-text-mute) !important; }
[data-testid='stMetricValue'] { color: var(--de-text) !important; }

/* Dataframes / tables */
[data-testid='stDataFrame'] {
  border-radius: var(--de-radius-sm);
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.10);
}

/* Sidebar (if used) */
section[data-testid='stSidebar'] {
  background: rgba(10, 12, 20, 0.55) !important;
  border-right: 1px solid rgba(255,255,255,0.08) !important;
  backdrop-filter: blur(14px);
}

/* Toasts */
[data-testid='stToast'] {
  background: rgba(15, 18, 30, 0.86) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: 14px !important;
}

/* Make expanders look cleaner */
details {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 14px;
  padding: 6px 10px;
}

/* Mobile tweaks */
@media (max-width: 768px) {
  section[data-testid='stMain'] > div { padding-left: 0.9rem !important; padding-right: 0.9rem !important; }
  button[data-baseweb='tab'] { padding: 8px 10px !important; }
}
</style>

    """, unsafe_allow_html=True)

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
        pdf.cell(0, 10, _pdf_text_seguro("Relatório de viabilidade"), ln=True, align='C')

        pdf.set_font("Helvetica", '', 9)
        pdf.cell(0, 5, _pdf_text_seguro("Simulador imobiliário Direcional - documento executivo"), ln=True, align='C')
        pdf.ln(6)

        # Bloco cliente
        y = pdf.get_y()
        pdf.set_fill_color(*FUNDO_SECAO)
        pdf.rect(pdf.l_margin, y, largura_util, 16, 'F')

        pdf.set_xy(pdf.l_margin + 4, y + 4)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 5, _pdf_text_seguro(f"Cliente: {d.get('nome', 'Não informado')}"), ln=True)

        pdf.set_x(pdf.l_margin + 4)
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(0, 5, _pdf_text_seguro(f"Renda familiar: R$ {fmt_br(d.get('renda', 0))}"), ln=True)

        pdf.ln(6)

        # Helpers
        def secao(titulo):
            pdf.set_fill_color(*AZUL)
            pdf.set_text_color(*BRANCO)
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(largura_util, 7, _pdf_text_seguro(f"  {titulo}"), ln=True, fill=True)
            pdf.ln(2)

        def linha(label, valor, destaque=False):
            label = _pdf_text_seguro(label)
            valor = _pdf_text_seguro(valor)
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
        secao("Dados do imóvel")
        linha("Empreendimento", _pdf_text_seguro(d.get("empreendimento_nome")))
        linha("Unidade selecionada", _pdf_text_seguro(d.get("unidade_id")))
        
        # Valor de Venda no Sistema = Valor Comercial Mínimo
        v_comercial = d.get('imovel_valor', 0)
        v_avaliacao = d.get('imovel_avaliacao', 0)
        
        # No PDF para o cliente, mostramos Avaliação e o "Desconto" para chegar no valor de venda
        linha("Valor de tabela ou avaliação", f"R$ {fmt_br(v_avaliacao)}", True)
        
        if d.get("unid_entrega"):
            linha("Previsão de Entrega", _pdf_text_seguro(d.get("unid_entrega")))
        if d.get("unid_area"):
            linha("Área privativa", _pdf_text_seguro(f"{d.get('unid_area')} metros quadrados"))
        if d.get("unid_tipo"):
            linha("Tipologia", _pdf_text_seguro(d.get("unid_tipo")))
        if d.get("unid_endereco") and d.get("unid_bairro"):
            linha(
                "Endereço",
                _pdf_text_seguro(f"{d.get('unid_endereco')} - {d.get('unid_bairro')}"),
            )

        pdf.ln(4)
        
        # SEÇÃO DE NEGOCIAÇÃO (NOVO)
        secao("Condição comercial")
        # Calculamos a diferença como "Desconto"
        desconto = max(0, v_avaliacao - v_comercial)
        linha("Desconto ou condição especial", f"R$ {fmt_br(desconto)}")
        linha("Valor final de venda", f"R$ {fmt_br(v_comercial)}", True)
        
        pdf.ln(4)

        secao("Engenharia financeira")
        linha("Financiamento bancário estimado", f"R$ {fmt_br(d.get('finan_usado', 0))}")
        prazo = d.get('prazo_financiamento', 360)
        linha(
            "Sistema de amortização do financiamento",
            f"{nome_sistema_amortizacao_completo(str(d.get('sistema_amortizacao', 'SAC')))} - {prazo} meses",
        )
        linha("Parcela estimada do financiamento", f"R$ {fmt_br(d.get('parcela_financiamento', 0))}")
        linha("Subsídio e Fundo de Garantia do Tempo de Serviço utilizados", f"R$ {fmt_br(d.get('fgts_sub_usado', 0))}")

        pdf.ln(4)

        secao("Fluxo de entrada (atos e Pro Soluto)")
        linha("Pro Soluto (parte da entrada)", f"R$ {fmt_br(d.get('ps_usado', 0))}")
        linha("Mensalidade do Pro Soluto", f"{d.get('ps_parcelas')} parcelas de R$ {fmt_br(d.get('ps_mensal', 0))}")
        _ent_ps = float(d.get('entrada_total', 0) or 0) + float(d.get('ps_usado', 0) or 0)
        linha("Valor total de entrada em atos", f"R$ {fmt_br(d.get('entrada_total', 0))}")
        linha("Entrada total (atos e Pro Soluto)", f"R$ {fmt_br(_ent_ps)}", True)
        linha("Ato 0", f"R$ {fmt_br(d.get('ato_final', 0))}")
        linha("Ato 30", f"R$ {fmt_br(d.get('ato_30', 0))}")
        linha("Ato 60", f"R$ {fmt_br(d.get('ato_60', 0))}")
        if not _politica_emcash(d.get("politica")):
            linha("Ato 90", f"R$ {fmt_br(d.get('ato_90', 0))}")

        # ===============================
        # RODAPÉ (DADOS CORRETOR)
        # ===============================
        pdf.ln(4)
        
        # Dados do Corretor
        pdf.set_font("Helvetica", 'B', 9)
        pdf.set_text_color(*AZUL)
        pdf.cell(0, 5, _pdf_text_seguro("Consultor responsável"), ln=True, align='L')
        pdf.set_font("Helvetica", '', 9)
        pdf.cell(0, 5, _pdf_text_seguro(f"{d.get('corretor_nome', 'Não informado')}"), ln=True)
        pdf.cell(
            0,
            5,
            _pdf_text_seguro(
                f"Contato: {d.get('corretor_telefone', '')} | E-mail: {d.get('corretor_email', '')}"
            ),
            ln=True,
        )

        pdf.ln(4)

        # Aviso Legal e Data
        pdf.set_font("Helvetica", 'I', 7)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            0,
            4,
            _pdf_text_seguro(
                f"Simulação realizada em {d.get('data_simulacao', date.today().strftime('%d/%m/%Y'))}. "
                "Sujeito a análise de crédito e alteração de tabela sem aviso prévio."
            ),
            ln=True,
            align='C'
        )
        pdf.cell(0, 4, _pdf_text_seguro("Direcional Engenharia - Rio de Janeiro"), ln=True, align='C')

        # PyFPDF: output(dest="S") devolve str; fpdf2 pode devolver bytes. Latin-1 é o esperado pelo PDF bruto.
        out = pdf.output(dest="S")
        if isinstance(out, (bytes, bytearray)):
            return bytes(out)
        return out.encode("latin-1", errors="replace")

    except Exception:
        logging.getLogger(__name__).exception("Falha em gerar_resumo_pdf")
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
    _emcash_corretor = _politica_emcash(dados_cliente.get("politica"))
    _html_linha_ato_90 = (
        ""
        if _emcash_corretor
        else (
            "<tr>\n"
            '                                             <td>&nbsp;&nbsp;↳ Ato 90</td>\n'
            f'                                             <td align="right">R$ {a90}</td>\n'
            "                                        </tr>\n"
        )
    )

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
                                                <p style="margin: 15px 0 0 0; font-size: 24px; font-weight: bold; color: #e30613;">Valor promocional: R$ {val_venda}</p>
                                            </td>
                                        </tr>
                                    </table>

                                    <div style="text-align: center; margin: 35px 0;">
                                        <a href="{wa_link}" style="background-color: #25D366; color: #ffffff; padding: 15px 30px; text-decoration: none; font-weight: bold; border-radius: 5px; font-size: 16px; display: inline-block;">Falar com o corretor pelo WhatsApp</a>
                                        <p style="font-size: 12px; color: #999; margin-top: 10px;">(Abra o documento em formato PDF em anexo para ver todos os detalhes.)</p>
                                    </div>
                                    
                                    <!-- Rodapé Interno -->
                                    <table width="100%" border="0" cellspacing="0" cellpadding="20" style="margin-top: 40px; background-color: #002c5d; color: #ffffff;">
                                        <tr>
                                            <td align="center">
                                                <p style="margin: 0; font-size: 16px; font-weight: bold; color: #ffffff;">{corretor_nome}</p>
                                                <p style="margin: 5px 0 15px 0; font-size: 12px; font-weight: bold; color: #e30613;">Consultor Direcional</p>
                                                
                                                <p style="margin: 0; font-size: 14px;">
                                                    <span style="color: #ffffff;">WhatsApp:</span> <a href="{wa_link}" style="color: #e30613; text-decoration: none; font-weight: bold;">{corretor_tel}</a>
                                                    <span style="margin: 0 10px; color: #666;">|</span>
                                                    <span style="color: #ffffff;">E-mail:</span> <a href="mailto:{corretor_email}" style="color: #e30613; text-decoration: none; font-weight: bold;">{corretor_email}</a>
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
                                             <td>&nbsp;&nbsp;↳ Ato 0</td>
                                             <td align="right">R$ {a0}</td>
                                        </tr>
                                        <tr>
                                             <td>&nbsp;&nbsp;↳ Ato 30</td>
                                             <td align="right">R$ {a30}</td>
                                        </tr>
                                        <tr>
                                             <td>&nbsp;&nbsp;↳ Ato 60</td>
                                             <td align="right">R$ {a60}</td>
                                        </tr>
                                        {_html_linha_ato_90}
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


def tela_login(df_logins: pd.DataFrame) -> None:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown(
            "<h3 style='text-align:center;margin:0 0 0.35rem 0;'>Acesso ao simulador</h3>",
            unsafe_allow_html=True,
        )
        st.caption("Utilize o e-mail e a senha cadastrados na planilha **Logins** da base de dados.")
        with st.form("login_form"):
            email = st.text_input(
                "Endereço de e-mail",
                key="login_email",
                autocomplete="username",
            )
            senha = st.text_input(
                "Senha",
                type="password",
                key="login_pass",
                autocomplete="current-password",
            )
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)

        if submitted:
            if df_logins.empty:
                st.error("Base de usuários vazia ou indisponível. Verifique a conexão com a planilha.")
            else:
                em = email.strip().lower()
                user = df_logins[
                    (df_logins["Email"] == em) & (df_logins["Senha"] == senha.strip())
                ]
                if not user.empty:
                    data = user.iloc[0]
                    st.session_state.update(
                        {
                            "logged_in": True,
                            "user_email": em,
                            "user_name": str(data.get("Nome", "")).strip(),
                            "user_imobiliaria": str(data.get("Imobiliaria", "Geral")).strip(),
                            "user_cargo": str(data.get("Cargo", "")).strip(),
                            "user_phone": str(data.get("Telefone", "")).strip(),
                            "user_is_adm": login_row_is_adm(data),
                        }
                    )
                    st.success("Login realizado.")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
        inject_login_password_manager_fields()


@st.dialog("Resumo: PDF, e-mail e WhatsApp")
def show_export_dialog(d):
    st.markdown(f"<h3 style='text-align: center; color: {COR_AZUL_ESC}; margin: 0;'>Resumo da Simulação</h3>", unsafe_allow_html=True)
    st.caption("Baixe o PDF, envie o relatório por e-mail ao cliente ou abra o WhatsApp com o texto do resumo.")

    d["corretor_nome"] = st.session_state.get("user_name", "")
    d["corretor_email"] = st.session_state.get("user_email", "")
    d["corretor_telefone"] = st.session_state.get("user_phone", "")

    pdf_data = gerar_resumo_pdf(d)

    st.markdown("**1. Documento PDF**")
    if pdf_data:
        st.download_button(
            label="Baixar documento PDF",
            data=pdf_data,
            file_name=f"Resumo_Direcional_{d.get('nome', 'Cliente')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.warning("Geração do documento PDF indisponível.")

    st.markdown("---")
    st.markdown("**2. Enviar por e-mail (cliente)**")
    email = st.text_input("Endereço de e-mail do cliente", placeholder="cliente@exemplo.com", key="export_dialog_email_cliente")
    if st.button("Enviar e-mail para o cliente", use_container_width=True, key="export_dialog_btn_email"):
        if email and "@" in email:
            sucesso, msg = enviar_email_smtp(email, d.get("nome", "Cliente"), pdf_data, d, tipo="cliente")
            if sucesso:
                st.success(msg)
            else:
                st.error(msg)
        else:
            st.error("E-mail inválido")

    st.markdown("---")
    st.markdown("**3. Texto por WhatsApp**")
    st.caption("Abre o WhatsApp (Web ou app) com a mensagem pronta; escolha o contato e envie.")
    _vc_wa = texto_moeda_para_float(st.session_state.get("volta_caixa_key"))
    _wa_msg = montar_mensagem_whatsapp_resumo(
        d,
        volta_caixa_val=_vc_wa,
        nome_consultor=st.session_state.get("user_name", "") or "",
        canal_imobiliaria=st.session_state.get("user_imobiliaria", "") or "",
    )
    _wa_link = _url_whatsapp_enviar_texto(_wa_msg)
    _wa_link_max = 6000
    if len(_wa_link) <= _wa_link_max:
        st.link_button(
            "Abrir WhatsApp com o texto do resumo",
            _wa_link,
            use_container_width=True,
            type="secondary",
        )
    else:
        st.info(
            "O link automático ficou grande demais para o navegador. Copie o texto abaixo e cole no WhatsApp."
        )
    with st.expander("Ver ou copiar texto do WhatsApp"):
        st.caption("Negrito (*texto*) e tópicos funcionam ao colar no WhatsApp.")
        st.text_area("Texto da mensagem", value=_wa_msg, height=240, label_visibility="collapsed", key="export_dialog_wa_text")

# =============================================================================
# APLICAÇÃO PRINCIPAL
# =============================================================================

def aba_simulador_automacao(
    df_finan,
    df_estoque,
    df_politicas,
    premissas_dict=None,
    df_home_banners: pd.DataFrame | None = None,
):
    if st.session_state.get("passo_simulacao") in (
        "input",
        "fechamento_aprovado",
        "guide",
        "selection",
        "payment_flow",
    ):
        st.session_state.passo_simulacao = "sim"
    passo = st.session_state.get("passo_simulacao", "sim")
    if passo in ("gallery", "client_analytics"):
        st.session_state.passo_simulacao = "sim"
        st.rerun()
    motor = MotorRecomendacao(df_finan, df_estoque, df_politicas)
    _prem = dict(DEFAULT_PREMISSAS)
    if premissas_dict:
        _prem.update(premissas_dict)

    def taxa_fin_vigente(d_cli):
        return resolver_taxa_financiamento_anual_pct(d_cli or {}, _prem)
    if 'dados_cliente' not in st.session_state: st.session_state.dados_cliente = {}

    st.markdown(
        '<div class="header-brand-bar-wrap"><div class="header-brand-bar" aria-hidden="true"></div></div>',
        unsafe_allow_html=True,
    )
    render_faixa_home_banners(df_home_banners if df_home_banners is not None else pd.DataFrame())
    if st.session_state.get("user_is_adm"):
        with st.expander("Banners da página inicial (administrador — base de dados, aba Banners da home)", expanded=False):
            st.caption(
                "Inclua o endereço **https** da imagem (por exemplo, Postimages). Na página inicial as imagens aparecem em **miniatura**; o visitante **amplia ao clicar**. "
                "Colunas na planilha: Ordem, URL da imagem, Título, Ativo, **Tela cheia** (legado na planilha), **Descrição** "
                "(opcional; aparece no painel ampliado). "
                "Adicione as colunas necessárias na aba **Banners da home** da base de dados se ainda não existirem."
            )
            with st.form("form_novo_home_banner"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    bn_ordem = st.number_input("Ordem", min_value=1, max_value=999, value=1, step=1)
                with c2:
                    bn_ativo = st.selectbox("Ativo", ["SIM", "NÃO"], index=0)
                with c3:
                    bn_tela_cheia = st.selectbox(
                        "Tela cheia (planilha)",
                        ["NÃO", "SIM"],
                        index=0,
                        help="Valor gravado na planilha (legado). Todas as campanhas já abrem ampliadas ao clicar; a descrição, se houver, aparece no painel ampliado.",
                    )
                bn_url = st.text_input(
                    "Endereço da imagem (URL)",
                    placeholder="https://i.postimg.cc/...",
                )
                bn_titulo = st.text_input("Título", placeholder="Texto abaixo da imagem")
                bn_descricao = st.text_area(
                    "Descrição (painel ampliado)",
                    placeholder="Opcional. Só é mostrada quando o visitante amplia a imagem ao clicar.",
                    height=100,
                )
                enviar_bn = st.form_submit_button("Gravar nova linha na aba Banners da home", type="primary")
            if enviar_bn:
                url_t = (bn_url or "").strip()
                ativo_sim = str(bn_ativo or "").strip().upper() == "SIM"
                tc_sim = str(bn_tela_cheia or "").strip().upper() == "SIM"
                if not url_t.startswith("https://"):
                    st.error("A URL da imagem deve começar com https:// (use o link direto do Postimages).")
                elif not (bn_titulo or "").strip():
                    st.error("Informe o título (legenda).")
                else:
                    ok, err = gravar_nova_linha_home_banner(
                        int(bn_ordem),
                        url_t,
                        bn_titulo.strip(),
                        ativo_sim,
                        tela_cheia_sim=tc_sim,
                        descricao=(bn_descricao or "").strip(),
                    )
                    if ok:
                        st.cache_data.clear()
                        st.success("Banner gravado na planilha. Recarregando…")
                        st.rerun()
                    else:
                        st.error(f"Não foi possível gravar: {err}")

            st.markdown("---")
            st.markdown("**Remover banner**")
            _df_bn_adm = normalizar_df_home_banners(
                df_home_banners if df_home_banners is not None else pd.DataFrame()
            )
            _df_bn_adm = _df_bn_adm.reset_index(drop=True)
            if _df_bn_adm.empty:
                st.caption("Não há linhas para excluir na aba Banners da home da base de dados.")
            else:
                _opts_idx = list(range(len(_df_bn_adm)))
                _ix_del = st.selectbox(
                    "Banner a excluir (ordem igual à da planilha ao carregar)",
                    options=_opts_idx,
                    format_func=lambda j: _rotulo_opcao_excluir_banner(_df_bn_adm, int(j)),
                    key="home_banner_excluir_select",
                )
                _conf_del = st.checkbox(
                    "Confirmo que quero remover permanentemente esta linha da planilha",
                    key="home_banner_excluir_confirma",
                )
                if st.button("Excluir banner selecionado", type="secondary", key="home_banner_excluir_btn"):
                    if not _conf_del:
                        st.warning("Marque a confirmação para excluir.")
                    else:
                        ok_del, err_del = excluir_linha_home_banner(int(_ix_del))
                        if ok_del:
                            st.cache_data.clear()
                            st.success("Banner removido da planilha. Recarregando…")
                            st.rerun()
                        else:
                            st.error(f"Não foi possível excluir: {err_del}")

    # --- PÁGINA ÚNICA: perfil → valores → recomendações → unidade → distribuição (ordem fixa) ---
    if passo == 'sim':
        st.markdown("### Perfil da simulação")
        st.markdown(
            '<p style="font-size:0.8rem;color:#111111;margin:0 0 0.75rem 0;">Informe renda e perfil de crédito. '
            "Os blocos abaixo atualizam automaticamente ao alterar estes campos.</p>",
            unsafe_allow_html=True,
        )

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

        st.text_input("Participantes na renda (1 a 4)", key="qtd_part_v3", placeholder="Exemplo: 2")
        _qp = texto_inteiro(st.session_state.get("qtd_part_v3"), default=1, min_v=1, max_v=4)
        qtd_part = _qp if _qp is not None else 1
        cols_renda = st.columns(qtd_part)
        for i in range(qtd_part):
            with cols_renda[i]:
                st.text_input(f"Renda do participante {i + 1}", key=f"renda_part_{i}_v3", placeholder="R$ 0,00")
        rank_opts = ["DIAMANTE", "OURO", "PRATA", "BRONZE", "AÇO"]
        curr_ranking = st.session_state.dados_cliente.get('ranking', "DIAMANTE")
        idx_ranking = rank_opts.index(curr_ranking) if curr_ranking in rank_opts else 0
        ranking = st.selectbox("Ranking do Cliente", options=rank_opts, index=idx_ranking, key="in_rank_v28")
        _pol_saved = st.session_state.dados_cliente.get("politica")
        _pol_idx = 0 if _pol_saved == "Direcional" else 1
        politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"], index=_pol_idx, key="in_pol_v28")

        lista_rendas_input = [texto_moeda_para_float(st.session_state.get(f"renda_part_{j}_v3")) for j in range(qtd_part)]
        renda_total_calc = sum(lista_rendas_input)
        prazo_ps_max = 66 if politica_ps == "Emcash" else 84
        st.session_state.dados_cliente.update({
            'nome': 'Simulação',
            'cpf': '',
            'data_nascimento': None,
            'renda': renda_total_calc,
            'rendas_lista': lista_rendas_input,
            'ranking': ranking,
            'politica': politica_ps,
            'qtd_participantes': qtd_part,
            'finan_usado_historico': 0.0,
            'ps_usado_historico': 0.0,
            'fgts_usado_historico': 0.0,
            'prazo_ps_max': prazo_ps_max,
            'limit_ps_renda': 0.30,
        })

        st.markdown("---")
        # --- ETAPA 2: VALORES APROVADOS (FECHAMENTO FINANCEIRO) ---
        d = st.session_state.dados_cliente
        st.markdown("### Valores Aprovados (Fechamento Financeiro)")

        renda_cli = float(d.get("renda", 0) or 0)
        _matriz_bd = motor.obter_quatro_combinacoes_f2_f3_f4(renda_cli)
        _ix_sim_sim = next(
            (i for i, rowq in enumerate(_matriz_bd) if rowq["social"] and rowq["cotista"]),
            max(0, len(_matriz_bd) - 1),
        )
        _row_sim_cot = _matriz_bd[_ix_sim_sim]
        _val_aval_para_faixa = float(d.get("imovel_avaliacao") or 0) or 240000.0
        _, _, _faixa_curva = motor.obter_enquadramento(
            renda_cli, True, True, valor_avaliacao=_val_aval_para_faixa
        )
        if str(_faixa_curva) not in ("F2", "F3", "F4"):
            _faixa_curva = "F2"
        _fin_ref_sim_cot = float(_row_sim_cot.get(f"fin_{_faixa_curva}", 0) or 0)
        _sub_ref_sim_cot = float(_row_sim_cot.get(f"sub_{_faixa_curva}", 0) or 0)

        def _sim_nao(v):
            return "Sim" if v else "Não"

        _tbl_rows = "".join(
            f"<tr>"
            f"<td style='padding:8px 10px;text-align:center;border-bottom:1px solid #e2e8f0;color:#334155;font-weight:600;'>{_sim_nao(it['social'])}</td>"
            f"<td style='padding:8px 10px;text-align:center;border-bottom:1px solid #e2e8f0;color:#334155;font-weight:600;'>{_sim_nao(it['cotista'])}</td>"
            f"<td style='padding:8px 8px;text-align:right;border-bottom:1px solid #e2e8f0;color:#0f172a;'>{reais_streamlit_html(fmt_br(it['fin_F2']))}</td>"
            f"<td style='padding:8px 8px;text-align:right;border-bottom:1px solid #e2e8f0;color:#0f172a;'>{reais_streamlit_html(fmt_br(it['sub_F2']))}</td>"
            f"<td style='padding:8px 8px;text-align:right;border-bottom:1px solid #e2e8f0;color:#0f172a;'>{reais_streamlit_html(fmt_br(it['fin_F3']))}</td>"
            f"<td style='padding:8px 8px;text-align:right;border-bottom:1px solid #e2e8f0;color:#0f172a;'>{reais_streamlit_html(fmt_br(it['sub_F3']))}</td>"
            f"<td style='padding:8px 8px;text-align:right;border-bottom:1px solid #e2e8f0;color:#0f172a;'>{reais_streamlit_html(fmt_br(it['fin_F4']))}</td>"
            f"<td style='padding:8px 8px;text-align:right;border-bottom:1px solid #e2e8f0;color:#0f172a;'>{reais_streamlit_html(fmt_br(it['sub_F4']))}</td>"
            f"</tr>"
            for it in _matriz_bd
        )
        st.markdown(
            f"""<div class="finan-subsidios-table-bleed" style="width:100vw;max-width:100%;position:relative;left:50%;transform:translateX(-50%);margin:0.5rem 0 1rem;padding:0 clamp(10px,2.2vw,28px);box-sizing:border-box;overflow-x:auto;-webkit-overflow-scrolling:touch;">
<table style="width:100%;min-width:min(100%,720px);border-collapse:collapse;font-size:clamp(0.72rem,1.6vw,0.85rem);color:#111111;table-layout:fixed;">
<caption style="caption-side:top;padding-bottom:10px;font-weight:700;color:#111111;text-align:center;font-size:clamp(0.85rem,2vw,1rem);">Financiamentos e subsídios (base de dados — Financiamentos) — Faixas 2, 3 e 4</caption>
<thead>
<tr>
<th rowspan="2" style="text-align:center;vertical-align:middle;padding:8px 10px;border-bottom:2px solid #cbd5e1;width:12%;">Fator Social</th>
<th rowspan="2" style="text-align:center;vertical-align:middle;padding:8px 10px;border-bottom:2px solid #cbd5e1;width:14%;">Cotista do Fundo de Garantia do Tempo de Serviço</th>
<th colspan="2" style="text-align:center;padding:6px 8px;border-bottom:1px solid #cbd5e1;">Faixa 2</th>
<th colspan="2" style="text-align:center;padding:6px 8px;border-bottom:1px solid #cbd5e1;">Faixa 3</th>
<th colspan="2" style="text-align:center;padding:6px 8px;border-bottom:1px solid #cbd5e1;">Faixa 4</th>
</tr>
<tr>
<th style="text-align:right;padding:6px 8px;border-bottom:2px solid #cbd5e1;white-space:normal;line-height:1.25;">Financiamento</th>
<th style="text-align:right;padding:6px 8px;border-bottom:2px solid #cbd5e1;white-space:normal;line-height:1.25;">Subsídios</th>
<th style="text-align:right;padding:6px 8px;border-bottom:2px solid #cbd5e1;white-space:normal;line-height:1.25;">Financiamento</th>
<th style="text-align:right;padding:6px 8px;border-bottom:2px solid #cbd5e1;white-space:normal;line-height:1.25;">Subsídios</th>
<th style="text-align:right;padding:6px 8px;border-bottom:2px solid #cbd5e1;white-space:normal;line-height:1.25;">Financiamento</th>
<th style="text-align:right;padding:6px 8px;border-bottom:2px solid #cbd5e1;white-space:normal;line-height:1.25;">Subsídios</th>
</tr>
</thead>
<tbody>{_tbl_rows}</tbody>
</table></div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="font-size:0.8rem;color:#111111;margin:0.5rem 0 1rem 0;">Subsídios da curva inferiores a '
            f"{reais_streamlit_html(fmt_br(SUBSIDIO_MINIMO_CURVA))} são desconsiderados (tratados como "
            f"{reais_streamlit_html('0,00')}), alinhado à regra da planilha comercial. "
            f"A tabela acima é só referência; financiamento e subsídio aprovados podem ser outros valores.</p>",
            unsafe_allow_html=True,
        )
        st.session_state.dados_cliente["social"] = True
        st.session_state.dados_cliente["cotista"] = True

        st.session_state.dados_cliente["finan_f_ref"] = _fin_ref_sim_cot
        st.session_state.dados_cliente["sub_f_ref"] = _sub_ref_sim_cot
        d = st.session_state.dados_cliente
        if d.get("finan_usado") is None:
            st.session_state.dados_cliente["finan_usado"] = float(_fin_ref_sim_cot or 0)
        if d.get("fgts_sub_usado") is None:
            st.session_state.dados_cliente["fgts_sub_usado"] = float(_sub_ref_sim_cot or 0)
        d = st.session_state.dados_cliente
        def _num_f(k, default=0.0):
            v = st.session_state.dados_cliente.get(k, st.session_state.get(k, default))
            if v is None: return default
            try: return float(v)
            except (TypeError, ValueError): return default
        # Sem teto pela curva da BD: só valores não negativos (tabela = referência).
        fin_default = clamp_moeda_positiva(_num_f('finan_usado', 0.0), None)
        _pair_ref = (float(_fin_ref_sim_cot or 0), float(_sub_ref_sim_cot or 0))
        _prev_pair = st.session_state.get("_fin_sub_ref_curva_par")
        if _prev_pair is not None:
            pf, ps = float(_prev_pair[0]), float(_prev_pair[1])
            if abs(pf - _pair_ref[0]) > 0.02 or abs(ps - _pair_ref[1]) > 0.02:
                tf = texto_moeda_para_float(st.session_state.get("fin_aprovado_key"))
                ts = texto_moeda_para_float(st.session_state.get("sub_aprovado_key"))
                if abs(tf - pf) < 0.02:
                    st.session_state["fin_aprovado_key"] = float_para_campo_texto(_pair_ref[0], vazio_se_zero=True)
                    st.session_state.dados_cliente["finan_usado"] = _pair_ref[0]
                    fin_default = clamp_moeda_positiva(_pair_ref[0], None)
                if abs(ts - ps) < 0.02:
                    st.session_state["sub_aprovado_key"] = float_para_campo_texto(_pair_ref[1], vazio_se_zero=True)
                    st.session_state.dados_cliente["fgts_sub_usado"] = _pair_ref[1]
        st.session_state["_fin_sub_ref_curva_par"] = _pair_ref

        if "fin_aprovado_key" not in st.session_state:
            st.session_state["fin_aprovado_key"] = float_para_campo_texto(fin_default, vazio_se_zero=True)
        else:
            if texto_moeda_para_float(st.session_state.get("fin_aprovado_key")) == 0 and fin_default > 0:
                st.session_state["fin_aprovado_key"] = float_para_campo_texto(fin_default, vazio_se_zero=True)
            _f_raw = texto_moeda_para_float(st.session_state.get("fin_aprovado_key"))
            _f_ok = clamp_moeda_positiva(_f_raw, None)
            if abs(_f_raw - _f_ok) > 0.009:
                st.session_state["fin_aprovado_key"] = float_para_campo_texto(_f_ok, vazio_se_zero=True)
        st.text_input("Financiamento aprovado (reais)", key="fin_aprovado_key", placeholder="Exemplo: 250000 ou 250.000,00")
        f_u = clamp_moeda_positiva(texto_moeda_para_float(st.session_state.get("fin_aprovado_key")), None)
        st.session_state.dados_cliente['finan_usado'] = f_u

        sub_default = clamp_moeda_positiva(_num_f('fgts_sub_usado', 0.0), None)
        if "sub_aprovado_key" not in st.session_state:
            st.session_state["sub_aprovado_key"] = float_para_campo_texto(sub_default, vazio_se_zero=True)
        else:
            if texto_moeda_para_float(st.session_state.get("sub_aprovado_key")) == 0 and sub_default > 0:
                st.session_state["sub_aprovado_key"] = float_para_campo_texto(sub_default, vazio_se_zero=True)
            _s_raw = texto_moeda_para_float(st.session_state.get("sub_aprovado_key"))
            _s_ok = clamp_moeda_positiva(_s_raw, None)
            if abs(_s_raw - _s_ok) > 0.009:
                st.session_state["sub_aprovado_key"] = float_para_campo_texto(_s_ok, vazio_se_zero=True)
        st.text_input(
            "Subsídio aprovado e Fundo de Garantia do Tempo de Serviço (reais)",
            key="sub_aprovado_key",
            placeholder="Exemplo: 50000 ou 50.000,00",
        )
        s_u = clamp_moeda_positiva(texto_moeda_para_float(st.session_state.get("sub_aprovado_key")), None)
        st.session_state.dados_cliente['fgts_sub_usado'] = s_u

        prazo_atual = d.get('prazo_financiamento', 360)
        try: prazo_atual = int(prazo_atual) if prazo_atual is not None else 360
        except: prazo_atual = 360
        if "prazo_aprovado_key" not in st.session_state:
            st.session_state["prazo_aprovado_key"] = str(int(prazo_atual))
        st.text_input("Prazo do financiamento (meses)", key="prazo_aprovado_key", placeholder="360")
        _pz = texto_inteiro(st.session_state.get("prazo_aprovado_key"), default=360, min_v=12, max_v=600)
        prazo_sel = _pz if _pz is not None else 360
        st.session_state.dados_cliente['prazo_financiamento'] = int(prazo_sel)

        _opcoes_amort = list(_AMORTIZACAO_NOME_COMPLETO.values())
        _cod_amort_atual = str(d.get("sistema_amortizacao", "SAC")).strip().upper()
        _idx_amort = 1 if _cod_amort_atual == "PRICE" else 0
        sist_sel_label = st.selectbox(
            "Sistema de amortização do financiamento",
            options=_opcoes_amort,
            index=_idx_amort,
            key="sist_aprovado_ui_v1",
        )
        sist_sel = "PRICE" if sist_sel_label == _AMORTIZACAO_NOME_COMPLETO["PRICE"] else "SAC"
        st.session_state.dados_cliente['sistema_amortizacao'] = sist_sel
        taxa_padrao = taxa_fin_vigente(d)
        sac_details = calcular_comparativo_sac_price(f_u, int(prazo_sel), taxa_padrao)["SAC"]
        price_details = calcular_comparativo_sac_price(f_u, int(prazo_sel), taxa_padrao)["PRICE"]
        _n_sac = _AMORTIZACAO_NOME_COMPLETO["SAC"]
        _n_price = _AMORTIZACAO_NOME_COMPLETO["PRICE"]
        st.markdown(
            f"""<div style="margin-top: -8px; margin-bottom: 15px; font-size: 0.85rem; color: #111111; text-align: center;"><b>{_n_sac}:</b> {reais_streamlit_html(fmt_br(sac_details['primeira']))} a {reais_streamlit_html(fmt_br(sac_details['ultima']))} (juros totais: {reais_streamlit_html(fmt_br(sac_details['juros']))}) &nbsp;|&nbsp; <b>{_n_price}:</b> {reais_streamlit_html(fmt_br(price_details['parcela']))} parcelas fixas (juros totais: {reais_streamlit_html(fmt_br(price_details['juros']))})</div>""",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        # --- ETAPA 3: RECOMENDAÇÃO (filtro empreendimento + cards; sem abas) ---
        d = st.session_state.dados_cliente
        st.markdown("### Recomendação de Imóveis")

        df_disp_total = df_estoque.copy()

        if df_disp_total.empty:
            st.markdown('<div class="custom-alert">Sem estoque carregado para recomendações.</div>', unsafe_allow_html=True)
        else:
            def _ps_max_estoque_row(row):
                pol = d.get("politica", "Direcional")
                rank = d.get("ranking", "DIAMANTE")
                if pol == "Emcash":
                    try:
                        return float(row.get("PS_EmCash", 0) or 0)
                    except (TypeError, ValueError):
                        return 0.0
                col_rank = f"PS_{rank.title()}" if rank else "PS_Diamante"
                if rank == "AÇO":
                    col_rank = "PS_Aco"
                try:
                    return float(row.get(col_rank, 0) or 0)
                except (TypeError, ValueError):
                    return 0.0

            def calcular_poder_compra_linha(row):
                """Dobro da renda + financiamento + subsídio + Pro Soluto efetivo (comparador, políticas e teto do estoque)."""
                try:
                    v_venda = float(row.get("Valor de Venda", 0) or 0)
                except (TypeError, ValueError):
                    v_venda = 0.0
                fin = float(d.get("finan_usado", 0) or 0)
                sub = float(d.get("fgts_sub_usado", 0) or 0)
                ren = float(d.get("renda", 0) or 0)
                ps_stock = max(0.0, _ps_max_estoque_row(row))
                ps_eff = 0.0
                if ps_stock <= 1e-9:
                    ps_eff = 0.0
                else:
                    try:
                        mps = metricas_pro_soluto(
                            ren,
                            v_venda,
                            str(d.get("politica", "Direcional")),
                            str(d.get("ranking", "DIAMANTE")),
                            _prem,
                            df_politicas,
                            ps_cap_estoque=ps_stock,
                        )
                        ps_eff = float(mps.get("ps_max_efetivo", 0) or 0)
                    except Exception:
                        ps_eff = float(ps_stock)
                poder = (2.0 * ren) + fin + sub + max(0.0, ps_eff)
                cobertura = (poder / v_venda) * 100.0 if v_venda > 0 else 0.0
                return pd.Series([poder, cobertura, fin, sub])

            df_disp_total[["Poder_Compra", "Cobertura", "Finan_Unid", "Sub_Unid"]] = df_disp_total.apply(
                calcular_poder_compra_linha, axis=1
            )
            df_disp_total = df_disp_total.sort_values(["Valor de Venda", "Identificador"], ascending=[True, True])

            st.markdown("<br>", unsafe_allow_html=True)
            emp_names_rec = sorted(df_disp_total["Empreendimento"].unique().tolist())
            emp_rec = st.selectbox(
                "Filtrar por empreendimento:",
                options=["Todos"] + emp_names_rec,
                key="sel_emp_rec_v28",
            )
            df_pool = df_disp_total if emp_rec == "Todos" else df_disp_total[df_disp_total["Empreendimento"] == emp_rec]

            if df_pool.empty:
                st.markdown('<div class="custom-alert">Nenhuma unidade encontrada para o filtro.</div>', unsafe_allow_html=True)
            else:
                cand_ideal = pd.DataFrame()
                cand_seguro = pd.DataFrame()
                final_cards = []

                vv = pd.to_numeric(df_pool["Valor de Venda"], errors="coerce").fillna(0.0)
                pc = pd.to_numeric(df_pool["Poder_Compra"], errors="coerce").fillna(0.0)
                lim_seg = 0.9 * pc
                mask_ideal = (vv > 0) & (vv <= pc)
                ideal_sub = df_pool[mask_ideal]
                label_ideal = "IDEAL"
                if not ideal_sub.empty:
                    max_p_i = pd.to_numeric(ideal_sub["Valor de Venda"], errors="coerce").max()
                    cand_ideal = ideal_sub[pd.to_numeric(ideal_sub["Valor de Venda"], errors="coerce") == max_p_i]
                else:
                    pool_pos = df_pool[vv > 0]
                    if pool_pos.empty:
                        cand_ideal = pd.DataFrame()
                    else:
                        min_v_i = pd.to_numeric(pool_pos["Valor de Venda"], errors="coerce").min()
                        cand_ideal = pool_pos[
                            pd.to_numeric(pool_pos["Valor de Venda"], errors="coerce") == min_v_i
                        ]
                        label_ideal = "MENOR PREÇO"

                mask_seg = (vv > 0) & (vv <= lim_seg)
                seg_sub = df_pool[mask_seg]
                label_seguro = "SEGURO"
                if not seg_sub.empty:
                    max_p_s = pd.to_numeric(seg_sub["Valor de Venda"], errors="coerce").max()
                    cand_seguro = seg_sub[pd.to_numeric(seg_sub["Valor de Venda"], errors="coerce") == max_p_s]
                else:
                    stretch = df_pool[(vv > 0) & (vv > lim_seg)]
                    if stretch.empty:
                        cand_seguro = pd.DataFrame()
                    else:
                        min_v_s = pd.to_numeric(stretch["Valor de Venda"], errors="coerce").min()
                        cand_seguro = stretch[
                            pd.to_numeric(stretch["Valor de Venda"], errors="coerce") == min_v_s
                        ]
                        label_seguro = "MENOR PREÇO"

                if not cand_ideal.empty and not cand_seguro.empty:
                    _k_ideal = set(
                        zip(
                            cand_ideal["Empreendimento"].astype(str),
                            cand_ideal["Identificador"].astype(str),
                        )
                    )
                    cand_seguro = cand_seguro[
                        ~cand_seguro.apply(
                            lambda r: (str(r["Empreendimento"]), str(r["Identificador"])) in _k_ideal,
                            axis=1,
                        )
                    ]

                def add_cards_group(label, df_group, css_class):
                    df_u = df_group.drop_duplicates(subset=["Identificador"])
                    for _, row in df_u.head(8).iterrows():
                        final_cards.append({"label": label, "row": row, "css": css_class})

                add_cards_group(label_ideal, cand_ideal, "badge-ideal")
                add_cards_group(label_seguro, cand_seguro, "badge-seguro")

                if not final_cards:
                    st.info("Ajuste o filtro de empreendimento ou os valores aprovados para ver sugestões de unidades.")
                else:
                    cards_html = """<div class="recommendation-cards-outer"><div class="scrolling-wrapper">"""
                    
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
                                <span style="font-size:0.65rem; color:#111111; opacity:0.95;">Perfil</span><br>
                                <div style="margin-top:5px; margin-bottom:15px;"><span class="{css_badge}">{label}</span></div>
                                <b style="color:#111111; font-size:1.1rem;">{emp_name}</b><br>
                                <div style="font-size:0.85rem; color:#111111; text-align:center; border-top:1px solid #eee; padding-top:10px; width:100%;">
                                    <b>Unidade: {unid_name}</b>
                                </div>
                                <div style="margin: 10px 0; width: 100%;">
                                    <div style="font-size:0.8rem; color:#111111;">Avaliação</div>
                                    <div style="font-weight:bold; color:#111111;">{reais_streamlit_html(aval_fmt)}</div>
                                    <div style="font-size:0.8rem; color:#111111; margin-top:5px;">Valor de venda</div>
                                    <div class="price-tag" style="font-size:1.3rem; margin-top:0;">{reais_streamlit_html(val_fmt)}</div>
                                </div>
                            </div>
                         </div>"""
                    cards_html += "</div></div>"
                    st.markdown(cards_html, unsafe_allow_html=True)

        st.markdown("---")
        # --- ETAPA 4: ESCOLHA DE UNIDADE (lista por preço crescente) ---
        d = st.session_state.dados_cliente
        st.markdown("### Escolha de Unidade")
        uni_escolhida_id = None
        df_disponiveis = df_estoque.copy()
        if df_disponiveis.empty:
            st.warning("Sem estoque disponível.")
        else:
            emp_names = sorted(df_disponiveis['Empreendimento'].unique())
            idx_emp = 0
            if 'empreendimento_nome' in st.session_state.dados_cliente:
                try:
                    idx_emp = emp_names.index(st.session_state.dados_cliente['empreendimento_nome'])
                except Exception:
                    idx_emp = 0
            emp_escolhido = st.selectbox("Escolha o Empreendimento:", options=emp_names, index=idx_emp, key="sel_emp_new_v3")
            st.session_state.dados_cliente['empreendimento_nome'] = emp_escolhido
            unidades_disp = df_disponiveis[(df_disponiveis['Empreendimento'] == emp_escolhido)].copy()
            unidades_disp = unidades_disp.sort_values(['Valor de Venda', 'Identificador'], ascending=[True, True])
            if unidades_disp.empty:
                st.warning("Sem unidades disponíveis.")
            else:
                uni_ordered = unidades_disp.drop_duplicates(subset=['Identificador'], keep='first')
                current_uni_ids = uni_ordered['Identificador'].tolist()
                idx_uni = 0
                if 'unidade_id' in st.session_state.dados_cliente:
                    try:
                        if st.session_state.dados_cliente['unidade_id'] in current_uni_ids:
                            idx_uni = current_uni_ids.index(st.session_state.dados_cliente['unidade_id'])
                    except Exception:
                        pass

                def label_uni(uid):
                    u = unidades_disp[unidades_disp["Identificador"] == uid].iloc[0]
                    try:
                        v_aval = fmt_br(float(u.get("Valor de Avaliação Bancária", 0) or 0))
                    except (TypeError, ValueError):
                        v_aval = fmt_br(0)
                    v_venda = fmt_br(u["Valor de Venda"])
                    try:
                        v_vc = float(u.get("Volta_Caixa_Ref", 0) or 0)
                    except (TypeError, ValueError):
                        v_vc = 0.0
                    v_vc_fmt = fmt_br(v_vc)
                    return (
                        f"{uid} | Avaliação: R$ {v_aval} | Venda: R$ {v_venda} | Volta ao Caixa: R$ {v_vc_fmt}"
                    )

                uni_escolhida_id = st.selectbox(
                    "Escolha a Unidade (do menor ao maior preço):",
                    options=current_uni_ids,
                    index=idx_uni,
                    format_func=label_uni,
                    key="sel_uni_new_v3",
                )
                if uni_escolhida_id:
                    u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                    v_venda = u_row["Valor de Venda"]
                    v_venda_unid = float(v_venda)
                    st.session_state.dados_cliente.update({
                        'unidade_id': uni_escolhida_id,
                        'empreendimento_nome': emp_escolhido,
                        'imovel_valor': v_venda_unid,
                        'imovel_avaliacao': u_row['Valor de Avaliação Bancária'],
                        'finan_estimado': d.get('finan_usado', 0),
                        'fgts_sub': d.get('fgts_sub_usado', 0),
                        'unid_entrega': u_row.get('Data Entrega', ''),
                        'unid_area': u_row.get('Area', ''),
                        'unid_tipo': u_row.get('Tipologia', ''),
                        'unid_endereco': u_row.get('Endereco', ''),
                        'unid_bairro': u_row.get('Bairro', ''),
                        'volta_caixa_ref': u_row.get('Volta_Caixa_Ref', 0.0),
                    })
                    pol = d.get('politica', 'Direcional')
                    prazo_max_ps = 66 if pol == 'Emcash' else 84
                    st.session_state.dados_cliente['prazo_ps_max'] = prazo_max_ps

        st.markdown("---")
        # --- ETAPA 5: DISTRIBUIÇÃO DA ENTRADA (FECHAMENTO) ---
        d = st.session_state.dados_cliente
        st.markdown("### Distribuição da Entrada (Fechamento)")
        if float(d.get('imovel_valor', 0) or 0) <= 0 or not d.get('unidade_id'):
            st.markdown(
                '<p style="font-size:0.8rem;color:#111111;margin:0 0 0.5rem 0;">Selecione <strong>empreendimento</strong> e '
                "<strong>unidade</strong> na seção acima para calcular a distribuição da entrada.</p>",
                unsafe_allow_html=True,
            )
        # Valores da unidade vêm do cadastro (Valor de Venda); demais valores do fluxo anterior
        u_valor = float(d.get('imovel_valor', 0) or 0)
        f_u_input = clamp_moeda_positiva(float(d.get('finan_usado', 0) or 0), None)
        fgts_u_input = clamp_moeda_positiva(float(d.get('fgts_sub_usado', 0) or 0), None)
        if u_valor > 0:
            f_u_input = min(f_u_input, u_valor)
            fgts_u_input = min(fgts_u_input, max(0.0, u_valor - f_u_input))
        prazo_finan = int(d.get('prazo_financiamento', 360))
        tab_fin = d.get('sistema_amortizacao', 'SAC')
        st.session_state.dados_cliente['finan_usado'] = f_u_input
        st.session_state.dados_cliente['fgts_sub_usado'] = fgts_u_input
        st.session_state.dados_cliente['prazo_financiamento'] = prazo_finan
        st.session_state.dados_cliente['sistema_amortizacao'] = tab_fin

        if 'ps_usado' not in st.session_state.dados_cliente:
            st.session_state.dados_cliente['ps_usado'] = 0.0
        if 'ato_final' not in st.session_state.dados_cliente:
            st.session_state.dados_cliente['ato_final'] = 0.0
        if 'ato_30' not in st.session_state.dados_cliente:
            st.session_state.dados_cliente['ato_30'] = 0.0
        if 'ato_60' not in st.session_state.dados_cliente:
            st.session_state.dados_cliente['ato_60'] = 0.0
        if 'ato_90' not in st.session_state.dados_cliente:
            st.session_state.dados_cliente['ato_90'] = 0.0

        is_emcash = _politica_emcash(d.get("politica"))

        ps_max_real = 0.0
        if 'unidade_id' in d and 'empreendimento_nome' in d:
            row_u = df_estoque[(df_estoque['Identificador'] == d['unidade_id']) & (df_estoque['Empreendimento'] == d['empreendimento_nome'])]
            if not row_u.empty:
                row_u = row_u.iloc[0]
                pol = d.get('politica', 'Direcional')
                rank = d.get('ranking', 'DIAMANTE')
                if pol == 'Emcash':
                    ps_max_real = row_u.get('PS_EmCash', 0.0)
                else:
                    col_rank = f"PS_{rank.title()}" if rank else 'PS_Diamante'
                    if rank == 'AÇO':
                        col_rank = 'PS_Aco'
                    ps_max_real = row_u.get(col_rank, 0.0)

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
                "ps_cap_parcela_j8": 0.0,
            }
        prazo_cap_app = int(d.get("prazo_ps_max", 84) or 84)
        pol_prazo = int(mps.get("prazo_ps_politica", prazo_cap_app) or prazo_cap_app)
        parc_max_ui = max(1, min(pol_prazo, prazo_cap_app))

        vc_ref_num = float(d.get('volta_caixa_ref', 0) or 0)
        if 'volta_caixa_key' not in st.session_state:
            st.session_state['volta_caixa_key'] = ""
        _vc0 = texto_moeda_para_float(st.session_state.get('volta_caixa_key'))
        _vc1 = max(0.0, min(_vc0, vc_ref_num)) if vc_ref_num > 0 else max(0.0, _vc0)
        if abs(_vc0 - _vc1) > 0.009:
            st.session_state['volta_caixa_key'] = float_para_campo_texto(_vc1, vazio_se_zero=True)

        if 'parc_ps_key' not in st.session_state:
            try:
                _p0 = int(d.get('ps_parcelas', min(60, parc_max_ui)) or 1)
            except (TypeError, ValueError):
                _p0 = 1
            _p0 = max(1, min(_p0, parc_max_ui))
            st.session_state['parc_ps_key'] = str(_p0)
        else:
            _pi = texto_inteiro(st.session_state.get("parc_ps_key"), default=1, min_v=1, max_v=parc_max_ui)
            _pi = _pi if _pi is not None else 1
            st.session_state['parc_ps_key'] = str(int(max(1, min(_pi, parc_max_ui))))

        _parc_sync = int(st.session_state["parc_ps_key"] or "1")
        _parc_sync = max(1, min(_parc_sync, parc_max_ui))
        j8_fe = float(mps.get("parcela_max_j8") or 0)
        pol_fe = str(d.get("politica", "Direcional"))
        ps_cap_parc_fe = (
            valor_ps_maximo_parcela_j8(j8_fe, _parc_sync, _prem, pol_fe)
            if j8_fe > 0 and _parc_sync > 0
            else 0.0
        )
        ps_limite_base_fe = float(mps.get("ps_max_efetivo", 0) or 0)
        if ps_cap_parc_fe > 0.0:
            ps_limite_ui = min(ps_limite_base_fe, ps_cap_parc_fe) if ps_limite_base_fe > 0.0 else ps_cap_parc_fe
        else:
            ps_limite_ui = ps_limite_base_fe

        if 'ps_u_key' not in st.session_state:
            st.session_state['ps_u_key'] = float_para_campo_texto(st.session_state.dados_cliente.get('ps_usado', 0.0), vazio_se_zero=True)
        _ps0 = texto_moeda_para_float(st.session_state.get('ps_u_key'))
        _teto_ps_opts = []
        if ps_limite_ui > 0:
            _teto_ps_opts.append(ps_limite_ui)
        if u_valor > 0:
            _teto_ps_opts.append(max(0.0, u_valor - f_u_input - fgts_u_input))
        _teto_ps = min(_teto_ps_opts) if _teto_ps_opts else None
        _ps1 = clamp_moeda_positiva(_ps0, _teto_ps)
        if abs(_ps0 - _ps1) > 0.009:
            st.session_state['ps_u_key'] = float_para_campo_texto(_ps1, vazio_se_zero=True)

        if 'ato_1_key' not in st.session_state:
            st.session_state['ato_1_key'] = float_para_campo_texto(st.session_state.dados_cliente.get('ato_final', 0.0), vazio_se_zero=True)
        if 'ato_2_key' not in st.session_state:
            st.session_state['ato_2_key'] = float_para_campo_texto(st.session_state.dados_cliente.get('ato_30', 0.0), vazio_se_zero=True)
        if 'ato_3_key' not in st.session_state:
            st.session_state['ato_3_key'] = float_para_campo_texto(st.session_state.dados_cliente.get('ato_60', 0.0), vazio_se_zero=True)
        if is_emcash:
            st.session_state.pop("ato_4_key", None)
            st.session_state.dados_cliente["ato_90"] = 0.0
        elif "ato_4_key" not in st.session_state:
            st.session_state["ato_4_key"] = float_para_campo_texto(
                st.session_state.dados_cliente.get("ato_90", 0.0), vazio_se_zero=True
            )

        _vc_cap = texto_moeda_para_float(st.session_state.get('volta_caixa_key'))
        _vc_cap = max(0.0, min(_vc_cap, vc_ref_num)) if vc_ref_num > 0 else max(0.0, _vc_cap)
        _teto_cap = []
        if ps_limite_ui > 0:
            _teto_cap.append(ps_limite_ui)
        if u_valor > 0:
            _teto_cap.append(max(0.0, u_valor - f_u_input - fgts_u_input))
        _teto_ps_cap = min(_teto_cap) if _teto_cap else None
        _ps_cap = clamp_moeda_positiva(texto_moeda_para_float(st.session_state.get('ps_u_key')), _teto_ps_cap)
        cap_atos = max(0.0, u_valor - f_u_input - fgts_u_input - _ps_cap - _vc_cap)

        r1s = max(0.0, texto_moeda_para_float(st.session_state.get("ato_1_key")))
        r2s = max(0.0, texto_moeda_para_float(st.session_state.get("ato_2_key")))
        r3s = max(0.0, texto_moeda_para_float(st.session_state.get("ato_3_key")))
        r4s = max(0.0, texto_moeda_para_float(st.session_state.get("ato_4_key"))) if not is_emcash else 0.0
        soma_at = r1s + r2s + r3s + r4s
        if soma_at > cap_atos + 0.01:
            if soma_at > 0 and cap_atos >= 0:
                _kf = cap_atos / soma_at
                r1s, r2s, r3s, r4s = r1s * _kf, r2s * _kf, r3s * _kf, r4s * _kf
            else:
                r1s = r2s = r3s = r4s = 0.0
            st.session_state['ato_1_key'] = float_para_campo_texto(r1s, vazio_se_zero=True)
            st.session_state['ato_2_key'] = float_para_campo_texto(r2s, vazio_se_zero=True)
            st.session_state['ato_3_key'] = float_para_campo_texto(r3s, vazio_se_zero=True)
            if not is_emcash:
                st.session_state["ato_4_key"] = float_para_campo_texto(r4s, vazio_se_zero=True)

        _opts_ps_btn = []
        if ps_limite_ui > 0:
            _opts_ps_btn.append(ps_limite_ui)
        if u_valor > 0:
            _opts_ps_btn.append(max(0.0, u_valor - f_u_input - fgts_u_input))
        _teto_ps_btn = min(_opts_ps_btn) if _opts_ps_btn else 0.0
        st.session_state["_ps_teto_para_botao"] = float(_teto_ps_btn or 0)

        def _preencher_ps_restante() -> None:
            du = st.session_state.dados_cliente
            uv = float(du.get("imovel_valor", 0) or 0)
            fi = float(du.get("finan_usado", 0) or 0)
            su = float(du.get("fgts_sub_usado", 0) or 0)
            em = _politica_emcash(du.get("politica"))
            a1 = max(0.0, texto_moeda_para_float(st.session_state.get("ato_1_key")))
            a2 = max(0.0, texto_moeda_para_float(st.session_state.get("ato_2_key")))
            a3 = max(0.0, texto_moeda_para_float(st.session_state.get("ato_3_key")))
            a4 = 0.0 if em else max(0.0, texto_moeda_para_float(st.session_state.get("ato_4_key")))
            vc_ref_b = float(du.get("volta_caixa_ref", 0) or 0)
            vcr_b = texto_moeda_para_float(st.session_state.get("volta_caixa_key"))
            vc_use_b = max(0.0, min(vcr_b, vc_ref_b)) if vc_ref_b > 0 else max(0.0, vcr_b)
            gap = max(0.0, uv - fi - su - a1 - a2 - a3 - a4 - vc_use_b)
            teto_b = float(st.session_state.get("_ps_teto_para_botao", 0) or 0)
            novo = min(gap, teto_b) if teto_b > 0 else gap
            st.session_state["ps_u_key"] = float_para_campo_texto(novo, vazio_se_zero=True)

        # --- Ato 0: só key + session_state (evita conflito value/key) ---
        st.text_input("Ato 0", key="ato_1_key", placeholder="0,00", help="Valor pago no ato da assinatura.")
        r1 = max(0.0, texto_moeda_para_float(st.session_state.get("ato_1_key")))
        st.session_state.dados_cliente['ato_final'] = r1
        
        # Função para distribuir o restante (usa PS atual da session)
        def distribuir_restante(n_parcelas):
            a1_atual = max(0.0, texto_moeda_para_float(st.session_state.get('ato_1_key')))
            ps_atual_cb = texto_moeda_para_float(st.session_state.get('ps_u_key'))
            vc_cb = texto_moeda_para_float(st.session_state.get('volta_caixa_key'))
            vc_cb = max(0.0, min(vc_cb, vc_ref_num)) if vc_ref_num > 0 else max(0.0, vc_cb)
            _opts_cb = []
            if ps_limite_ui > 0:
                _opts_cb.append(ps_limite_ui)
            if u_valor > 0:
                _opts_cb.append(max(0.0, u_valor - f_u_input - fgts_u_input))
            _teto_cb = min(_opts_cb) if _opts_cb else None
            ps_atual_cb = clamp_moeda_positiva(ps_atual_cb, _teto_cb)
            gap_total = max(0.0, u_valor - f_u_input - fgts_u_input - ps_atual_cb - vc_cb)
            
            # Restante a distribuir nos outros atos
            restante = max(0.0, gap_total - a1_atual)
            
            if restante > 0 and n_parcelas > 0:
                val_per_target = restante / n_parcelas
                s_val = float_para_campo_texto(val_per_target, vazio_se_zero=False)
                if n_parcelas == 2:
                    st.session_state["ato_2_key"] = s_val
                    st.session_state["ato_3_key"] = s_val
                    if is_emcash:
                        st.session_state.pop("ato_4_key", None)
                    else:
                        st.session_state["ato_4_key"] = ""
                elif n_parcelas == 3:
                    st.session_state["ato_2_key"] = s_val
                    st.session_state["ato_3_key"] = s_val
                    st.session_state["ato_4_key"] = s_val
            else:
                st.session_state["ato_2_key"] = ""
                st.session_state["ato_3_key"] = ""
                if is_emcash:
                    st.session_state.pop("ato_4_key", None)
                else:
                    st.session_state["ato_4_key"] = ""

            st.session_state.dados_cliente["ato_30"] = max(0.0, texto_moeda_para_float(st.session_state["ato_2_key"]))
            st.session_state.dados_cliente["ato_60"] = max(0.0, texto_moeda_para_float(st.session_state["ato_3_key"]))
            if is_emcash:
                st.session_state.dados_cliente["ato_90"] = 0.0
            else:
                st.session_state.dados_cliente["ato_90"] = max(
                    0.0, texto_moeda_para_float(st.session_state.get("ato_4_key"))
                )

        if is_emcash:
            st.button(
                "Distribuir saldo restante em duas parcelas (30 e 60 dias)",
                use_container_width=True,
                key="btn_rest_2x",
                on_click=distribuir_restante,
                args=(2,),
            )
        else:
            col_dist_a, col_dist_b = st.columns(2)
            with col_dist_a:
                st.button(
                    "Distribuir saldo restante em duas parcelas (30 e 60 dias)",
                    use_container_width=True,
                    key="btn_rest_2x",
                    on_click=distribuir_restante,
                    args=(2,),
                )
            with col_dist_b:
                st.button(
                    "Distribuir saldo restante em três parcelas (30, 60 e 90 dias)",
                    use_container_width=True,
                    key="btn_rest_3x",
                    on_click=distribuir_restante,
                    args=(3,),
                )

        st.write("")
        if is_emcash:
            col_atos_rest1, col_atos_rest2 = st.columns(2)
            with col_atos_rest1:
                st.text_input("Ato 30", key="ato_2_key", placeholder="0,00")
                st.session_state.dados_cliente["ato_30"] = max(
                    0.0, texto_moeda_para_float(st.session_state.get("ato_2_key"))
                )
            with col_atos_rest2:
                st.text_input("Ato 60", key="ato_3_key", placeholder="0,00")
                st.session_state.dados_cliente["ato_60"] = max(
                    0.0, texto_moeda_para_float(st.session_state.get("ato_3_key"))
                )
        else:
            col_atos_rest1, col_atos_rest2, col_atos_rest3 = st.columns(3)
            with col_atos_rest1:
                st.text_input("Ato 30", key="ato_2_key", placeholder="0,00")
                st.session_state.dados_cliente["ato_30"] = max(
                    0.0, texto_moeda_para_float(st.session_state.get("ato_2_key"))
                )
            with col_atos_rest2:
                st.text_input("Ato 60", key="ato_3_key", placeholder="0,00")
                st.session_state.dados_cliente["ato_60"] = max(
                    0.0, texto_moeda_para_float(st.session_state.get("ato_3_key"))
                )
            with col_atos_rest3:
                st.text_input("Ato 90", key="ato_4_key", placeholder="0,00")
                st.session_state.dados_cliente["ato_90"] = max(
                    0.0, texto_moeda_para_float(st.session_state.get("ato_4_key"))
                )

        st.button(
            "Preencher valor restante no Pro Soluto",
            key="btn_ps_preencher_restante",
            use_container_width=True,
            on_click=_preencher_ps_restante,
            help="Usa o saldo ainda não coberto (valor da unidade menos financiamento, Fundo de Garantia do Tempo de Serviço e subsídio, atos e volta ao caixa), limitado ao teto de Pro Soluto.",
        )
        st.write("")
        col_ps_parc, col_ps_val = st.columns(2)

        with col_ps_parc:
            st.text_input("Número de parcelas do Pro Soluto", key="parc_ps_key", placeholder=f"1 a {parc_max_ui}")
            _parc_i = texto_inteiro(st.session_state.get("parc_ps_key"), default=1, min_v=1, max_v=parc_max_ui)
            parc = _parc_i if _parc_i is not None else 1
            st.session_state.dados_cliente['ps_parcelas'] = parc
            st.markdown(f'<span class="inline-ref">Prazo máximo de parcelas do Pro Soluto: {parc_max_ui} meses</span>', unsafe_allow_html=True)

        j8_ui = float(mps.get("parcela_max_j8") or 0)
        pol_ui = str(d.get("politica", "Direcional"))
        ps_cap_parc_ui = valor_ps_maximo_parcela_j8(j8_ui, parc, _prem, pol_ui) if j8_ui > 0 and parc > 0 else 0.0
        ps_limite_base_ui = float(mps.get("ps_max_efetivo", 0) or 0)
        if ps_cap_parc_ui > 0.0:
            ps_limite_ui2 = min(ps_limite_base_ui, ps_cap_parc_ui) if ps_limite_base_ui > 0.0 else ps_cap_parc_ui
        else:
            ps_limite_ui2 = ps_limite_base_ui

        with col_ps_val:
            st.text_input("Valor do Pro Soluto", key="ps_u_key", placeholder="0,00")
            _ps_opts_f = []
            if ps_limite_ui2 > 0:
                _ps_opts_f.append(ps_limite_ui2)
            if u_valor > 0:
                _ps_opts_f.append(max(0.0, u_valor - f_u_input - fgts_u_input))
            _teto_ps_final = min(_ps_opts_f) if _ps_opts_f else None
            ps_input_val = clamp_moeda_positiva(texto_moeda_para_float(st.session_state.get("ps_u_key")), _teto_ps_final)
            st.session_state.dados_cliente['ps_usado'] = ps_input_val
            ref_text_ps = f"Limite máximo de Pro Soluto: {reais_streamlit_html(fmt_br(ps_limite_ui2))}"
            st.markdown(
                f'<div class="inline-ref" style="color:#111111;opacity:1;">{ref_text_ps}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<span class="inline-ref">Parcela máx. (J8): {reais_streamlit_html(fmt_br(j8_ui))}</span>',
                unsafe_allow_html=True,
            )

        v_parc = parcela_ps_para_valor(
            float(ps_input_val or 0),
            parc,
            pol_ui,
            _prem,
            parcela_max_j8=j8_ui if j8_ui > 0 else None,
        )
        st.session_state.dados_cliente['ps_mensal'] = v_parc
        st.session_state.dados_cliente['ps_mensal_simples'] = (float(ps_input_val or 0) / parc) if parc > 0 else 0.0
        st.markdown(
            f'<div style="margin-top: -8px; margin-bottom: 15px; font-size: 0.9rem; font-weight: 600; color: #111111; text-align: center;">'
            f"Mensalidade do Pro Soluto: {reais_streamlit_html(fmt_br(v_parc))} ({parc} parcelas)</div>",
            unsafe_allow_html=True,
        )
        
        # --- INPUT VOLTA AO CAIXA (NOVO) ---
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        vc_ref = d.get('volta_caixa_ref', 0.0)
        st.text_input("Volta ao Caixa", key="volta_caixa_key", placeholder="0,00")
        _vc_in = texto_moeda_para_float(st.session_state.get("volta_caixa_key"))
        vc_input_val = max(0.0, min(_vc_in, float(vc_ref or 0))) if float(vc_ref or 0) > 0 else max(0.0, _vc_in)

        ref_text_vc = f"Folga Volta ao Caixa: {reais_streamlit_html(fmt_br(vc_ref))}"
        st.markdown(
            f'<div class="inline-ref" style="color:#111111;opacity:1;">{ref_text_vc}</div>',
            unsafe_allow_html=True,
        )
        
        # Recalcular entrada: não negativa; soma dos atos ≤ saldo (valor − fin − subsídio − PS − volta ao caixa)
        r1_val = max(0.0, texto_moeda_para_float(st.session_state.get("ato_1_key")))
        r2_val = max(0.0, texto_moeda_para_float(st.session_state.get("ato_2_key")))
        r3_val = max(0.0, texto_moeda_para_float(st.session_state.get("ato_3_key")))
        r4_val = max(0.0, texto_moeda_para_float(st.session_state.get("ato_4_key"))) if not is_emcash else 0.0
        cap_entrada_final = max(0.0, u_valor - f_u_input - fgts_u_input - ps_input_val - vc_input_val)
        sum_ent = r1_val + r2_val + r3_val + r4_val
        if sum_ent > cap_entrada_final + 0.01:
            if sum_ent > 0 and cap_entrada_final >= 0:
                _kf2 = cap_entrada_final / sum_ent
                r1_val *= _kf2
                r2_val *= _kf2
                r3_val *= _kf2
                r4_val *= _kf2
            else:
                r1_val = r2_val = r3_val = r4_val = 0.0

        st.session_state.dados_cliente['ato_final'] = r1_val
        st.session_state.dados_cliente['ato_30'] = r2_val
        st.session_state.dados_cliente['ato_60'] = r3_val
        st.session_state.dados_cliente['ato_90'] = r4_val
        total_entrada_cash = r1_val + r2_val + r3_val + r4_val
        st.session_state.dados_cliente['entrada_total'] = total_entrada_cash

        # Inclui o Volta ao Caixa na dedução do GAP FINAL
        gap_final = u_valor - f_u_input - fgts_u_input - ps_input_val - total_entrada_cash - vc_input_val
        if abs(gap_final) > 1.0:
            st.error(
                f"Atenção: {'Falta cobrir' if gap_final > 0 else 'Valor excedente de'} R$ {fmt_br(abs(gap_final))}."
            )
        parcela_fin = calcular_parcela_financiamento(f_u_input, prazo_finan, taxa_fin_vigente(d), tab_fin)
        st.session_state.dados_cliente['parcela_financiamento'] = parcela_fin
        st.markdown("---")
        if st.button("Avançar para Resumo da Simulação", type="primary", use_container_width=True):
            if abs(gap_final) <= 1.0: st.session_state.passo_simulacao = 'summary'; scroll_to_top(); st.rerun()
            else:
                st.error(f"Não é possível avançar. Saldo pendente: R$ {fmt_br(gap_final)}")
        st.markdown('<div data-btn-azul style="display:none" aria-hidden="true"></div>', unsafe_allow_html=True)
    elif passo == 'summary':
        d = st.session_state.dados_cliente
        st.markdown(f"### Resumo da Simulação - {d.get('nome', 'Cliente')}")
        st.markdown(f'<div class="summary-header">Dados do imóvel</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="summary-body">
            <b>Empreendimento:</b> {d.get('empreendimento_nome')}<br>
            <b>Unidade:</b> {d.get('unidade_id')}<br>
            <b>Valor comercial de venda:</b> <span style="color: #111111; font-weight: 700;">{reais_streamlit_html(fmt_br(d.get('imovel_valor', 0)))}</span><br>
            <b>Avaliação bancária:</b> <span style="color: #111111;">{reais_streamlit_html(fmt_br(d.get('imovel_avaliacao', 0)))}</span>
        </div>""", unsafe_allow_html=True)
        
        # --- NOVO: EXIBIR DETALHES ADICIONAIS ---
        st.markdown(f'<div class="summary-header">Detalhes da unidade</div>', unsafe_allow_html=True)
        detalhes_html = f"""<div class="summary-body">"""
        if d.get('unid_entrega'): detalhes_html += f"<b>Previsão de Entrega:</b> {d.get('unid_entrega')}<br>"
        if d.get('unid_area'): detalhes_html += f"<b>Área privativa total:</b> {d.get('unid_area')} metros quadrados<br>"
        if d.get('unid_tipo'): detalhes_html += f"<b>Tipo de planta ou área:</b> {d.get('unid_tipo')}<br>"
        if d.get('unid_endereco') and d.get('unid_bairro'): 
            detalhes_html += f"<b>Localização:</b> {d.get('unid_endereco')} - {d.get('unid_bairro')}"
        detalhes_html += "</div>"
        st.markdown(detalhes_html, unsafe_allow_html=True)
        
        st.markdown(f'<div class="summary-header">Plano de financiamento</div>', unsafe_allow_html=True)
        prazo_txt = d.get('prazo_financiamento', 360)
        _amort_res = nome_sistema_amortizacao_completo(str(d.get("sistema_amortizacao", "SAC")))
        parcela_texto = f"Parcela estimada ({_amort_res} — {prazo_txt} meses): {reais_streamlit_html(fmt_br(d.get('parcela_financiamento', 0)))}"
        st.markdown(f"""<div class="summary-body"><b>Financiamento bancário:</b> {reais_streamlit_html(fmt_br(d.get('finan_usado', 0)))}<br><b>{parcela_texto}</b><br><b>Fundo de Garantia do Tempo de Serviço e subsídio:</b> {reais_streamlit_html(fmt_br(d.get('fgts_sub_usado', 0)))}</div>""", unsafe_allow_html=True)
        _ent_resumo = float(d.get('entrada_total', 0) or 0) + float(d.get('ps_usado', 0) or 0)
        st.markdown(f'<div class="summary-header">Fluxo de entrada (atos e Pro Soluto)</div>', unsafe_allow_html=True)
        _linha_resumo_ato_90 = (
            ""
            if _politica_emcash(d.get("politica"))
            else f"<br><b>Ato 90:</b> {reais_streamlit_html(fmt_br(d.get('ato_90', 0)))}"
        )
        st.markdown(
            f"""<div class="summary-body"><b>Pro Soluto (parte da entrada):</b> {reais_streamlit_html(fmt_br(d.get('ps_usado', 0)))} — {d.get('ps_parcelas')} parcelas de {reais_streamlit_html(fmt_br(d.get('ps_mensal', 0)))}<br><hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 10px 0;"><b>Total em atos (ato 0 e parcelados):</b> {reais_streamlit_html(fmt_br(d.get('entrada_total', 0)))}<br><b>Ato 0:</b> {reais_streamlit_html(fmt_br(d.get('ato_final', 0)))}<br><b>Ato 30:</b> {reais_streamlit_html(fmt_br(d.get('ato_30', 0)))}<br><b>Ato 60:</b> {reais_streamlit_html(fmt_br(d.get('ato_60', 0)))}{_linha_resumo_ato_90}<br><hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 10px 0;"><b>Entrada total (atos e Pro Soluto):</b> {reais_streamlit_html(fmt_br(_ent_resumo))}</div>""",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        _vc_wa = texto_moeda_para_float(st.session_state.get("volta_caixa_key"))
        _wa_msg = montar_mensagem_whatsapp_resumo(
            d,
            volta_caixa_val=_vc_wa,
            nome_consultor=st.session_state.get("user_name", "") or "",
            canal_imobiliaria=st.session_state.get("user_imobiliaria", "") or "",
        )
        _wa_link = _url_whatsapp_enviar_texto(_wa_msg)
        _wa_link_max = 6000
        if len(_wa_link) <= _wa_link_max:
            st.link_button(
                "Enviar resumo por WhatsApp",
                _wa_link,
                use_container_width=True,
                type="secondary",
                help="Abre o WhatsApp (Web ou aplicativo) com o texto do resumo já preenchido; escolha o contato e envie.",
            )
        else:
            st.info(
                "O link automático ficou grande demais para o navegador. Copie o texto abaixo e cole no WhatsApp."
            )
        with st.expander("Ver ou copiar texto do WhatsApp"):
            st.caption("Negrito (*texto*) e tópicos funcionam ao colar no WhatsApp.")
            st.text_area("Texto da mensagem", value=_wa_msg, height=280, label_visibility="collapsed")
        st.markdown("---")
        if st.button("Opções de resumo (PDF, e-mail e WhatsApp)", use_container_width=True):
            show_export_dialog(d)
        st.markdown("---")
        if st.button("Concluir e salvar simulação", type="primary", use_container_width=True):
            broker_email = st.session_state.get('user_email')
            if broker_email:
                with st.spinner("Gerando documento PDF e enviando para o seu e-mail..."):
                    pdf_bytes_auto = gerar_resumo_pdf(d)
                    if pdf_bytes_auto:
                        sucesso_email, msg_email = enviar_email_smtp(broker_email, d.get('nome', 'Cliente'), pdf_bytes_auto, d, tipo='corretor')
                        if sucesso_email: st.toast("Documento PDF enviado para o seu e-mail com sucesso.", icon="📧")
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
                st.markdown(f'<div class="custom-alert">Registro salvo na aba Simulações da base de dados.</div>', unsafe_allow_html=True); time.sleep(2); st.session_state.dados_cliente = {}; st.session_state.passo_simulacao = 'sim'; scroll_to_top(); st.rerun()
            except Exception as e: st.error(f"Erro ao salvar: {e}")
        st.markdown('<div data-btn-azul style="display:none" aria-hidden="true"></div>', unsafe_allow_html=True)
        if st.button("Voltar à simulação", use_container_width=True):
            st.session_state.passo_simulacao = 'sim'
            scroll_to_top()
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div data-btn-azul style="display:none" aria-hidden="true"></div>', unsafe_allow_html=True)
    if st.button("Sair do sistema", key="btn_logout_bottom", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["user_is_adm"] = False
        st.rerun()

def _inject_login_vertical_center_css() -> None:
    """Centraliza o bloco principal na altura da viewport (login). Só quando não autenticado."""
    st.markdown(
        """
        <style id="diresim-login-vert-center">
        html body [data-testid="stAppViewContainer"] {
            min-height: 100dvh !important;
            display: flex !important;
            flex-direction: column !important;
        }
        html body [data-testid="stAppViewContainer"] > section[data-testid="stMain"],
        html body section[data-testid="stMain"] {
            flex: 1 1 auto !important;
            min-height: calc(100dvh - 5.5rem) !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            padding-top: clamp(6px, 1.5vh, 14px) !important;
            padding-bottom: clamp(10px, 2.5vh, 28px) !important;
            box-sizing: border-box !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    configurar_layout()
    inject_enter_confirma_campo()
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        _inject_login_vertical_center_css()

    logo_src = html_std.escape(_src_logo_topo_header(), quote=True)
    st.markdown(
        f'''<header class="header-container" role="banner">
<div class="header-logo-wrap">
<img src="{logo_src}" alt="Direcional Engenharia" class="header-logo-img" decoding="async" loading="eager" />
</div>
<h1 class="header-title">Simulador imobiliário DV</h1>
</header>''',
        unsafe_allow_html=True,
    )

    if not st.session_state["logged_in"]:
        tela_login(carregar_apenas_logins())
    else:
        df_finan, df_estoque, df_politicas, _df_cad_hist, df_home_banners, premissas_dict = (
            carregar_dados_sistema()
        )
        aba_simulador_automacao(
            df_finan, df_estoque, df_politicas, premissas_dict, df_home_banners=df_home_banners
        )

    st.markdown(f'<div class="footer">Direcional Engenharia — Rio de Janeiro | Desenvolvido por Lucas Maia</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
