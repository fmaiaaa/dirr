# -*- coding: utf-8 -*-
from __future__ import annotations
# =============================================================================
# SIMULADOR STREAMLIT - FICHEIRO ÚNICO (gerado automaticamente)
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
# Paleta Streamlit: azul credenciamento; vermelho marca Direcional (#e30613)
COR_AZUL_ESC = "#04428f"
COR_VERMELHO = "#e30613"
COR_FUNDO = "#04428f"
COR_BORDA = "#eef2f6"
COR_TEXTO_MUTED = "#64748b"
COR_INPUT_BG = "#ffffff"
COR_INPUT_TEXTO = "#000000"
COR_TEXTO_LABEL = "#000000"
COR_VERMELHO_ESCURO = "#c40510"


def _hex_rgb_triplet(hex_color: str) -> str:
    """Converte #RRGGBB em 'r, g, b' para rgba(...) no CSS."""
    x = (hex_color or "").strip().lstrip("#")
    if len(x) != 6:
        return "0, 0, 0"
    return f"{int(x[0:2], 16)}, {int(x[2:4], 16)}, {int(x[4:6], 16)}"


RGB_AZUL_CSS = _hex_rgb_triplet(COR_AZUL_ESC)
RGB_VERMELHO_CSS = _hex_rgb_triplet(COR_VERMELHO)


def _hex_para_rgb_uint8(hex_color: str) -> tuple[int, int, int]:
    """Converte #RRGGBB em (R, G, B) 0–255 para FPDF."""
    x = (hex_color or "").strip().lstrip("#")
    if len(x) != 6:
        return (4, 66, 143)
    return (int(x[0:2], 16), int(x[2:4], 16), int(x[4:6], 16))


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
    {"classificacao": "EMCASH", "prosoluto_pct": 0.25, "faixa_renda": 0.0, "fx_renda_1": 0.55, "fx_renda_2": 0.55, "parcelas_max": 84.0},
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
    Ignora classificações repetidas (mantém a primeira - evita bloco histórico duplicado).
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
    "vv_f3": 400000.0,
    "vv_f4": 600000.0,
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
    """MIN(L, cap) - Excel usa int(L) no comparador; usamos floor para valores positivos."""
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


def meses_ate_entrega(data_entrega: Any) -> int:
    """C37 (tempo para entrega): se já passou, retorna 0; senão, meses corridos até a entrega."""
    if data_entrega is None:
        return 0
    s = str(data_entrega).strip()
    if not s:
        return 0
    dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
    if pd.isna(dt):
        return 0
    hoje = date.today()
    entrega = dt.date()
    meses = (entrega.year - hoje.year) * 12 + (entrega.month - hoje.month)
    if entrega.day < hoje.day:
        meses -= 1
    return max(0, int(meses))


def taxa_ps_direcional_por_entrega(
    premissas: Mapping[str, float],
    prazo_meses: int,
    meses_entrega: int,
) -> float:
    """
    Taxa efetiva mensal do Pro Soluto Direcional combinando fases pré e pós-entrega.
    - Até entrega: DIRE PRE
    - Após entrega: DIRE POS
    """
    n = int(prazo_meses or 0)
    if n <= 0:
        return float(premissas.get("dire_ps_amort_m", DEFAULT_PREMISSAS["dire_ps_amort_m"]))
    r_pre = float(premissas.get("dire_pre_m", DEFAULT_PREMISSAS["dire_pre_m"]))
    r_pos = float(premissas.get("dire_pos_m", DEFAULT_PREMISSAS["dire_pos_m"]))
    if r_pre <= -1.0 or r_pos <= -1.0:
        return float(premissas.get("dire_ps_amort_m", DEFAULT_PREMISSAS["dire_ps_amort_m"]))
    m_pre = max(0, min(int(meses_entrega or 0), n))
    m_pos = max(0, n - m_pre)
    fator_total = ((1.0 + r_pre) ** m_pre) * ((1.0 + r_pos) ** m_pos
    )
    try:
        return float(fator_total ** (1.0 / n) - 1.0)
    except (ValueError, OverflowError, ZeroDivisionError):
        return float(premissas.get("dire_ps_amort_m", DEFAULT_PREMISSAS["dire_ps_amort_m"]))


CURVA_PS_DIRE_84_BASE_10K: dict[int, float] = {
    0: 214.0, 1: 212.0, 2: 210.0, 3: 208.0, 4: 206.0, 5: 204.0, 6: 203.0, 7: 201.0,
    8: 199.0, 9: 198.0, 10: 196.0, 11: 194.0, 12: 193.0, 13: 191.0, 14: 190.0, 15: 188.0,
    16: 187.0, 17: 186.0, 18: 184.0, 19: 183.0, 20: 182.0, 21: 181.0, 22: 180.0, 23: 179.0,
    24: 177.0, 25: 176.0, 26: 175.0, 27: 174.0, 28: 173.0, 29: 172.0, 30: 171.0, 31: 171.0,
    32: 170.0, 33: 169.0, 34: 168.0, 35: 167.0, 36: 166.0, 37: 166.0, 38: 165.0, 39: 164.0,
    40: 163.0, 41: 163.0, 42: 162.0, 43: 161.0, 44: 161.0, 45: 160.0, 46: 160.0, 47: 159.0,
    48: 159.0, 49: 158.0, 50: 157.0, 51: 157.0, 52: 157.0, 53: 156.0, 54: 156.0, 55: 155.0,
}


def parcela_ps_direcional_curva_84(valor_ps: float, meses_entrega: int) -> float:
    """
    Curva comercial informada pelo time:
    - Base: Pro Soluto de R$ 10.000,00 em 84x
    - Chave: mês até entrega
    - Escalonamento linear para outros valores de Pro Soluto.
    """
    v = float(valor_ps or 0.0)
    if v <= 0.0:
        return 0.0
    if not CURVA_PS_DIRE_84_BASE_10K:
        return 0.0
    m = int(meses_entrega or 0)
    m_min = min(CURVA_PS_DIRE_84_BASE_10K.keys())
    m_max = max(CURVA_PS_DIRE_84_BASE_10K.keys())
    m = max(m_min, min(m, m_max))
    base_10k = float(CURVA_PS_DIRE_84_BASE_10K.get(m, CURVA_PS_DIRE_84_BASE_10K[m_max]))
    return float(base_10k * (v / 10000.0))


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
    meses_entrega: Optional[int] = None,
) -> float:
    """
    Emcash (UI): I5 - (PMT(E2, n, B41) × -1) × (1+E1).
    Direcional: PMT com principal B3 ajustado e taxa efetiva pré/pós conforme tempo até entrega.
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

    if n == 84:
        return parcela_ps_direcional_curva_84(pv_raw, int(meses_entrega or 0))
    taxa_ps = taxa_ps_direcional_por_entrega(
        p,
        n,
        int(meses_entrega or 0),
    )
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
        prazo_pv_k2 = int(min(row_em.parcelas_max, 120.0)) if row_em else 84
    else:
        desc = int(float(p.get("ps_pv_meses_desconto_direcional", 11.0)))
        prazo_pv_k2 = max(1, prazo_ps_ui - desc)
    l8_bruto = pv_l8_positivo(e2_comp, prazo_pv_k2, j8)
    l8 = float(l8_bruto) * PS_PV_FATOR_COLUNA_L
    cap_vu = cap_valor_unidade(valor_unidade, row)
    ps_cap_parcela_j8 = valor_ps_maximo_parcela_j8(j8, prazo_ps_ui, p, politica_ui)
    ps_max_calc = valor_max_ps_g15(l8, cap_vu)
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
    meses_entrega: Optional[int] = None,
) -> float:
    """Parcela corrigida; limitada ao teto J8 quando informado."""
    raw = parcela_ps_pmt(
        valor_ps,
        prazo_meses,
        premissas,
        politica_ui,
        meses_entrega=meses_entrega,
    )
    if parcela_max_j8 is None:
        return raw
    j8v = float(parcela_max_j8)
    if j8v <= 0.0:
        return raw
    return float(min(raw, j8v))


def menor_prazo_parcelas_ps_respeitando_j8(
    valor_ps: float,
    parcela_max_j8: float,
    politica_ui: str,
    premissas: Optional[Mapping[str, float]] = None,
    prazo_max: int = 84,
    meses_entrega: Optional[int] = None,
) -> Optional[int]:
    """
    Menor n em [1, prazo_max] tal que parcela_ps_pmt(n) ≤ J8 (PMT bruto, antes do cap na UI).
    """
    pv = float(valor_ps or 0.0)
    cap = float(parcela_max_j8 or 0.0)
    pmax = max(0, int(prazo_max or 0))
    if pv <= 0.0 or cap <= 0.0 or pmax <= 0:
        return None
    eps = 1e-6
    candidatos: list[int] = []
    for n in range(1, pmax + 1):
        raw = parcela_ps_pmt(
            pv, n, premissas, politica_ui, meses_entrega=meses_entrega
        )
        if raw <= cap + eps:
            candidatos.append(n)
    return min(candidatos) if candidatos else None


# ========================================================================
# core/comparador_emcash.py
# ========================================================================

# -*- coding: utf-8 -*-
from typing import Any, Mapping, Optional


def _politica_emcash(politica: Any) -> bool:
    s = str(politica or "").strip().upper()
    return "EMCASH" in s


# Aviso Emcash (parcelas 30/60): UI, PDF, e-mail, WhatsApp (hífen ASCII)
_EMCASH_NOTA_PARCELAS = (
    "As parcelas EMCASH incluem correção monetária (+IPCA) além dos juros"
    "."
)


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


def _st_iframe_html_snippet(html: str, *, height: int = 0, width: int | None = None) -> None:
    """Substitui st.components.v1.html (deprecado). Scripts devem usar window.parent como antes."""
    # st.iframe rejeita height=0 e width=0 (StreamlitInvalidHeightError / StreamlitInvalidWidthError).
    kw: dict = {}
    hi = int(height or 0)
    kw["height"] = hi if hi > 0 else "content"
    if width is not None and int(width) > 0:
        kw["width"] = int(width)
    st.iframe(html, **kw)
import pandas as pd
import re
from streamlit_gsheets import GSheetsConnection
import base64
from datetime import datetime, date, timedelta, timezone
import time
import secrets
import string
import locale
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import hashlib
from pathlib import Path
import json
import pytz
import altair as alt
import urllib.parse
import html as html_std
import jwt as jwt_lib
from typing import Callable

# Bloco [salesforce] no secrets.toml: USER / PASSWORD / TOKEN → variáveis SALESFORCE_* (mesma pasta, sem import circular)
_SF_SECRETS_TOML_ALIAS: dict[str, str] = {
    "USER": "SALESFORCE_USER",
    "PASSWORD": "SALESFORCE_PASSWORD",
    "TOKEN": "SALESFORCE_TOKEN",
    "DOMAIN": "SALESFORCE_DOMAIN",
    "CPF_FIELD": "SALESFORCE_CPF_FIELD",
    "RANKING_FIELD": "SALESFORCE_RANKING_FIELD",
    "RECORD_TYPE_CLIENTE_PF": "SALESFORCE_RECORD_TYPE_CLIENTE_PF",
    "LIGHTNING_ACCOUNT_BASE": "SALESFORCE_LIGHTNING_ACCOUNT_BASE",
    "RISK3_POLL_SECONDS": "SALESFORCE_RISK3_POLL_SECONDS",
    "RISK3_POLL_INTERVAL": "SALESFORCE_RISK3_POLL_INTERVAL",
    "REST_TIMEOUT": "SALESFORCE_REST_TIMEOUT",
    "RISK3_DUMP_STEPS": "SALESFORCE_RISK3_DUMP_STEPS",
    "RANKING_PF_AUTOCRIAR": "SALESFORCE_RANKING_PF_AUTOCRIAR",
    "ACCOUNT_CPF_FIELD": "SALESFORCE_ACCOUNT_CPF_FIELD",
}


def _chave_env_salesforce_desde_toml(k: str) -> str:
    k0 = str(k).strip()
    if not k0:
        return k0
    return _SF_SECRETS_TOML_ALIAS.get(k0.upper(), k0)


def _injetar_secrets_salesforce_no_env() -> None:
    """
    Copia credenciais do st.secrets para os.environ.
    Usa atribuição (não setdefault): na Cloud os secrets são a fonte de verdade a cada rerun.
    """
    try:
        sec = getattr(st, "secrets", None)
        if sec is None:
            return

        def _set(key: str, val) -> None:
            if val is not None and str(val).strip():
                os.environ[key] = str(val).strip()

        for key in (
            "SALESFORCE_USER",
            "SALESFORCE_PASSWORD",
            "SALESFORCE_TOKEN",
            "SALESFORCE_DOMAIN",
            "SALESFORCE_CPF_FIELD",
            "SALESFORCE_RANKING_FIELD",
            "SALESFORCE_RECORD_TYPE_CLIENTE_PF",
            "SALESFORCE_LIGHTNING_ACCOUNT_BASE",
            "SALESFORCE_RISK3_POLL_SECONDS",
            "SALESFORCE_RISK3_POLL_INTERVAL",
            "SALESFORCE_REST_TIMEOUT",
            "SALESFORCE_RISK3_DUMP_STEPS",
            "SALESFORCE_RANKING_PF_AUTOCRIAR",
            "SALESFORCE_ACCOUNT_CPF_FIELD",
        ):
            if hasattr(sec, "get"):
                _set(key, sec.get(key))
        # [salesforce] na Cloud pode vir como dict, AttrDict ou outro mapeamento — não usar só isinstance(..., dict).
        blk = None
        if hasattr(sec, "get"):
            blk = sec.get("salesforce")
        if blk is None and hasattr(sec, "__getitem__"):
            try:
                blk = sec["salesforce"]
            except Exception:
                blk = None
        if blk is not None and hasattr(blk, "items"):
            try:
                for k, v in blk.items():
                    if str(k).strip():
                        _set(_chave_env_salesforce_desde_toml(str(k).strip()), v)
            except Exception:
                pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Salesforce (inlined — não depende do ficheiro ``salesforce_api.py`` no deploy)
# ---------------------------------------------------------------------------
try:
    from simple_salesforce import Salesforce, SalesforceAuthenticationFailed
except ImportError:  # pragma: no cover
    Salesforce = None  # type: ignore[misc, assignment]
    SalesforceAuthenticationFailed = Exception  # type: ignore[misc, assignment]

_sf_logger = logging.getLogger(__name__)

_DV_SF_RANK_MEMO_TTL_SEC = 300.0
_DV_SF_RANK_MEMO_KEY = "_dv_sf_rank_memo_v1"


def _dv_sf_rank_memo_get(cpf11: str) -> tuple[str | None, str | None] | None:
    memo = st.session_state.get(_DV_SF_RANK_MEMO_KEY)
    if not isinstance(memo, dict):
        return None
    ent = memo.get(cpf11)
    if not isinstance(ent, dict):
        return None
    if time.time() - float(ent.get("t", 0) or 0) > _DV_SF_RANK_MEMO_TTL_SEC:
        return None
    return ent.get("rs"), ent.get("code")


def _dv_sf_rank_memo_set(cpf11: str, rs: str | None, code: str | None) -> None:
    memo = st.session_state.get(_DV_SF_RANK_MEMO_KEY)
    if not isinstance(memo, dict):
        memo = {}
    memo[cpf11] = {"t": time.time(), "rs": rs, "code": code}
    st.session_state[_DV_SF_RANK_MEMO_KEY] = memo


def _sf_ranking_progress_markup(
    frac: float,
    status: str,
    *,
    elapsed_s: float | None = None,
    meter_n: int | None = None,
    meter_total: int = 100,
) -> str:
    _ = (elapsed_s, meter_n, meter_total)  # assinatura compatível com chamadas antigas
    f = max(0.0, min(1.0, float(frac)))
    pct_int = int(round(f * 100))
    esc_status = html_std.escape(status or "")
    c_r = COR_VERMELHO
    c_b = COR_AZUL_ESC
    return (
        '<div class="dv-sf-rank-progress" style="font-family:system-ui,sans-serif;margin:0.25rem 0 0.5rem 0;">'
        '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:6px;">'
        f'<span style="color:#334155;font-size:0.88rem;font-weight:500;">{esc_status}</span>'
        f'<span style="color:{c_b};font-size:0.82rem;font-weight:600;">{pct_int}%</span>'
        "</div>"
        '<div style="height:14px;border-radius:8px;background:#e8eef3;overflow:hidden;box-shadow:inset 0 1px 2px rgba(0,0,0,0.06);">'
        f'<div style="height:100%;width:{pct_int}%;min-width:2px;border-radius:8px;'
        f"background:linear-gradient(90deg,{c_r} 0%,{c_b} 100%);"
        'transition:width 0.18s ease-out;"></div></div>'
        "</div>"
    )


def _sf_normalizar_cpf(cpf: str | None) -> str:
    if cpf is None:
        return ""
    return re.sub(r"\D", "", str(cpf).strip())


def _sf_conectar_salesforce(verbose: bool = False) -> Any | None:
    _injetar_secrets_salesforce_no_env()
    if Salesforce is None:
        if verbose:
            _sf_logger.warning("Pacote simple_salesforce não instalado.")
        return None

    username = (os.environ.get("SALESFORCE_USER") or "").strip()
    password = (os.environ.get("SALESFORCE_PASSWORD") or "").strip()
    token = (os.environ.get("SALESFORCE_TOKEN") or "").strip()
    # Produção: login (login.salesforce.com). Sandbox: test (test.salesforce.com).
    domain = (os.environ.get("SALESFORCE_DOMAIN") or "login").strip().lower()
    if domain in ("prod", "production", "login"):
        domain = "login"
    elif domain in ("sandbox", "test", "dev"):
        domain = "test"

    if not username or not password:
        if verbose:
            _sf_logger.info("Salesforce: SALESFORCE_USER ou SALESFORCE_PASSWORD ausentes.")
        return None

    try:
        if token:
            sf = Salesforce(
                username=username,
                password=password,
                security_token=token,
                domain=domain,
            )
        else:
            sf = Salesforce(username=username, password=password, domain=domain)
        if verbose:
            _sf_logger.info("Salesforce: conectado como %s", username)
        return sf
    except SalesforceAuthenticationFailed as e:
        _sf_logger.warning("Salesforce: falha de autenticação: %s", e)
        return None
    except Exception as e:
        _sf_logger.warning("Salesforce: erro ao conectar: %s", e)
        return None


def _sf_mapear_ranking_para_ui(valor: Any) -> str | None:
    if valor is None:
        return None
    s = str(valor).strip()
    if not s:
        return None
    key = re.sub(r"\s+", " ", s.lower())
    key_norm = (
        key.replace("ç", "c")
        .replace("ã", "a")
        .replace("õ", "o")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    mapping = {
        "diamante": "DIAMANTE",
        "diamond": "DIAMANTE",
        "ouro": "OURO",
        "gold": "OURO",
        "prata": "PRATA",
        "silver": "PRATA",
        "bronze": "BRONZE",
        "aco": "AÇO",
        "aço": "AÇO",
    }
    for needle, rank in mapping.items():
        if needle in key_norm or needle in key:
            return rank
    up = s.upper().strip()
    opts = ("DIAMANTE", "OURO", "PRATA", "BRONZE", "AÇO", "ACO")
    for o in opts:
        if up == o or up.replace("Ç", "C") == "ACO" and o == "AÇO":
            return "AÇO" if o == "ACO" else o
    if up == "ACO":
        return "AÇO"
    return None


def _sf_cpf_mascarado_br(cpf_digitos: str) -> str:
    return f"{cpf_digitos[0:3]}.{cpf_digitos[3:6]}.{cpf_digitos[6:9]}-{cpf_digitos[9:11]}"


def _sf_soql_escape_literal(val: str) -> str:
    return str(val).replace("\\", "\\\\").replace("'", "\\'")


# Person Account + poll de Ranking__c na Account (espelha a lógica de
# conta_pf_poll_ranking_cmd.py — Documentos/Automações Lucas/salesforce).
_SF_RECORD_TYPE_CLIENTE_PF_PADRAO = "012j0000000L7CjAAK"


def _sf_float_env_ranking(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _sf_truthy_env_ranking(name: str) -> bool:
    return (os.environ.get(name) or "").strip().lower() in ("1", "true", "yes", "on")


def _sf_autocriar_pf_account() -> bool:
    v = (os.environ.get("SALESFORCE_RANKING_PF_AUTOCRIAR") or "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def _sf_account_cpf_field_name() -> str:
    return (
        (os.environ.get("SALESFORCE_ACCOUNT_CPF_FIELD") or "").strip()
        or (os.environ.get("SALESFORCE_CPF_FIELD") or "").strip()
        or "CPF__c"
    )


def _sf_rand_alnum_sf(n: int) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def _sf_rand_digits_sf(n: int) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(n))


def _sf_montar_payload_conta_pf_ranking(cpf_digitos: str) -> dict[str, Any]:
    last_name = _sf_rand_alnum_sf(10)
    email_tag = _sf_rand_alnum_sf(10)
    email_val = f"diresimulator+{email_tag}@gmail.com"
    telefone = "219" + _sf_rand_digits_sf(8)
    record_type = (
        os.environ.get("SALESFORCE_RECORD_TYPE_CLIENTE_PF") or _SF_RECORD_TYPE_CLIENTE_PF_PADRAO
    ).strip()
    return {
        "RecordTypeId": record_type,
        "Salutation": "Sr.",
        "FirstName": "Diresimulator",
        "LastName": last_name,
        "AccountSource": "Stand",
        "Regional__c": "RJ",
        "Regional_Comercial__c": "RJ",
        "TelefoneAdicional__c": telefone,
        "Email_Adicional__c": email_val,
        "PersonEmail": email_val,
        "Unidade_de_negocio__c": "Direcional",
        "CPF__c": cpf_digitos,
    }


def _sf_erro_conta_ja_existe_cpf(mensagem: str) -> bool:
    u = (mensagem or "").lower()
    return "cpf" in u and ("já existe" in u or "ja existe" in u or "duplic" in u)


def _sf_extrair_account_id_do_erro_validacao(mensagem: str) -> str | None:
    m = re.search(r"\b(001[0-9A-Za-z]{12,17})\b", mensagem or "")
    return m.group(1) if m else None


def _sf_buscar_account_id_por_cpf(sf: Any, cpf_digitos: str) -> str | None:
    campo = _sf_account_cpf_field_name()
    for val in (cpf_digitos, _sf_cpf_mascarado_br(cpf_digitos)):
        safe = _sf_soql_escape_literal(val)
        q = f"SELECT Id FROM Account WHERE {campo} = '{safe}' LIMIT 1"
        try:
            r = sf.query(q)
            recs = r.get("records") or []
            if recs:
                i = recs[0].get("Id")
                if i:
                    return str(i).strip()
        except Exception:
            pass
    return None


def _sf_resolver_account_apos_falha_cpf_duplicado(
    sf: Any, cpf_digitos: str, acc_err: str
) -> str | None:
    if not _sf_erro_conta_ja_existe_cpf(acc_err):
        return None
    aid = _sf_extrair_account_id_do_erro_validacao(acc_err)
    if aid:
        return aid
    return _sf_buscar_account_id_por_cpf(sf, cpf_digitos)


def _sf_criar_conta_pf_ranking(sf: Any, cpf_digitos: str) -> tuple[str | None, str | None]:
    payload = _sf_montar_payload_conta_pf_ranking(cpf_digitos)
    try:
        res = sf.Account.create(payload)
        aid = (res.get("id") or "").strip()
        return (aid if aid else None, None)
    except Exception as e:
        return (None, str(e))


def _sf_excluir_account_criada_simulacao(sf: Any, account_id: str, http_timeout: float) -> None:
    """Remove Account criada só para leitura do ranking neste fluxo (loga falhas)."""
    aid = (account_id or "").strip()
    if not aid or not aid.startswith("001"):
        return
    try:
        sf.restful(f"sobjects/Account/{aid}", method="DELETE", timeout=http_timeout)
    except Exception as ex:
        _sf_logger.warning("Salesforce: exclusão da Account %s após simulação falhou: %s", aid, ex)


def _sf_buscar_oportunidade_recente_da_conta(
    sf: Any, account_id: str, http_timeout: float
) -> str | None:
    aid = (account_id or "").strip()
    if not aid or not aid.startswith("001"):
        return None
    soql = (
        "SELECT Id FROM Opportunity "
        f"WHERE AccountId = '{_sf_soql_escape_literal(aid)}' "
        "ORDER BY CreatedDate DESC LIMIT 1"
    )
    try:
        res = sf.query(soql, timeout=http_timeout)
        recs = (res or {}).get("records") or []
        if recs:
            oid = str(recs[0].get("Id") or "").strip()
            if oid.startswith("006"):
                return oid
    except Exception as ex:
        _sf_logger.warning("Salesforce: busca de Opportunity recente da Account %s falhou: %s", aid, ex)
    return None


def _sf_excluir_oportunidade_criada_simulacao(
    sf: Any, account_id: str, http_timeout: float
) -> None:
    """Remove Opportunity criada no fluxo para permitir limpeza da conta temporária."""
    oid = _sf_buscar_oportunidade_recente_da_conta(sf, account_id, http_timeout)
    if not oid:
        return
    try:
        sf.restful(f"sobjects/Opportunity/{oid}", method="DELETE", timeout=http_timeout)
    except Exception as ex:
        _sf_logger.warning(
            "Salesforce: exclusão da Opportunity %s após simulação falhou: %s",
            oid,
            ex,
        )


def _sf_get_ranking_account_rest(
    sf: Any, account_id: str, rfield: str, http_timeout: float
) -> str | None:
    aid = account_id.strip()
    try:
        rec = sf.restful(f"sobjects/Account/{aid}", method="GET", timeout=http_timeout)
        if _sf_truthy_env_ranking("SALESFORCE_RISK3_DUMP_STEPS"):
            try:
                _sf_logger.debug(
                    "SF poll GET Account %s: %s",
                    aid,
                    json.dumps(rec, ensure_ascii=False, default=str),
                )
            except (TypeError, ValueError):
                _sf_logger.debug("SF poll GET Account %s: %r", aid, rec)
        if isinstance(rec, dict):
            val = rec.get(rfield)
            if val is not None and str(val).strip() != "":
                return str(val).strip()
    except Exception as ex:
        _sf_logger.debug("SF GET Account %s: %s", aid, ex)
    return None


def _sf_poll_ranking_na_account(
    sf: Any,
    account_id: str,
    *,
    rfield: str,
    poll_sec: float,
    poll_iv: float,
    http_timeout: float,
    progress_p: Callable[[float, str], None] | None = None,
    prog_lo: float = 0.42,
    prog_hi: float = 0.92,
) -> str | None:
    """GET sobjects/Account/<Id> em loop até rfield vir preenchido ou timeout."""
    aid = account_id.strip()
    t0 = time.monotonic()
    deadline = t0 + max(1.0, float(poll_sec))
    last_log = time.monotonic()
    ps = max(1.0, float(poll_sec))
    span = max(float(prog_hi) - float(prog_lo), 1e-6)
    while time.monotonic() < deadline:
        rank = _sf_get_ranking_account_rest(sf, aid, rfield, http_timeout)
        if rank:
            if progress_p:
                progress_p(1.0, _SF_RANK_PROGRESS_MSG_SUCESSO)
            return rank
        elapsed = time.monotonic() - t0
        if progress_p:
            frac = float(prog_lo) + min(span, (elapsed / ps) * span)
            progress_p(
                frac,
                f"Aguardando a classificação do cliente… ({int(elapsed)} s)",
            )
        now = time.monotonic()
        if now - last_log >= 15.0:
            _sf_logger.info("Salesforce: aguardando %s na Account %s…", rfield, aid)
            last_log = now
        time.sleep(max(0.5, float(poll_iv)))
    return None


def _sf_ranking_bruto_para_ui(valor: str | None) -> str | None:
    if not valor:
        return None
    m = _sf_mapear_ranking_para_ui(valor)
    return str(m).strip() if m else str(valor).strip()


def _sf_consultar_por_cpf(sf: Any, cpf_bruto: str) -> tuple[dict | None, str | None]:
    """
    Consulta no Salesforce pelo CPF da conta (Account.CPF__c)
    e retorna a Opportunity mais recente com ranking do cliente.

    O CPF em Account.CPF__c está armazenado com máscara (ex.: 076.086.171-44).
    """
    cpf_digitos = _sf_normalizar_cpf(cpf_bruto)
    if not cpf_digitos or len(cpf_digitos) != 11 or not cpf_digitos.isdigit():
        return None, "Informe um CPF válido com 11 dígitos."

    cpf_mascarado = _sf_cpf_mascarado_br(cpf_digitos)
    lit = _sf_soql_escape_literal(cpf_mascarado)
    soql = f"""
        SELECT
            Id,
            Name,
            IDOportunidade__c,
            AccountId,
            Account.Name,
            Account.CPF__c,
            Account.Ranking__c,
            Account.Ranking_Score__c,
            Ranking__c,
            Ranking_Score__c
        FROM Opportunity
        WHERE Account.CPF__c = '{lit}'
        ORDER BY CreatedDate DESC
        LIMIT 10
    """
    try:
        res = sf.query(soql)
        registros = res.get("records", [])
        if not registros:
            return None, "Nenhum registro encontrado para o CPF informado."
        return registros[0], None
    except Exception as e:
        return None, f"Erro ao consultar o Salesforce: {e}"


# Compatível com código que ainda referencia o nome antigo.
_sf_consultar_opportunity_ranking_por_cpf = _sf_consultar_por_cpf

_SF_RANK_PROGRESS_MSG_SUCESSO = "Processo finalizado: classificação encontrada!"


def _sf_classificar_ranking_cpf_11(
    cpf_11: str,
    *,
    progress: Callable[[float, str, float], None] | None = None,
) -> tuple[str | None, str | None]:
    """
    Ranking por CPF: (1) última Opportunity + Account aninhada; (2) Account existente
    com GET/poll em Ranking__c; (3) se não houver conta e SALESFORCE_RANKING_PF_AUTOCRIAR
    estiver ativo, cria Person Account (Cliente PF) como em conta_pf_poll_ranking_cmd.py
    e faz poll até preencher o ranking. Se a conta tiver sido criada neste pedido
    (não reutilizada por duplicidade de CPF) e a classificação for encontrada,
    a Opportunity recente e a Account criada são excluídas ao final deste ramo.

    ``progress(frac_0_1, mensagem, elapsed_total_s)`` — opcional; barra gradiente na UI.

    Retorna (ranking_ui_ou_None, código_informativo_ou_None).
    Códigos: cpf_incompleto, pacote_ausente, sem_registo.
    """
    cpf = _sf_normalizar_cpf(cpf_11)
    if len(cpf) != 11:
        return None, "cpf_incompleto"

    if Salesforce is None:
        return None, "pacote_ausente"

    t_all = time.monotonic()

    def _p(frac: float, msg: str) -> None:
        if progress:
            progress(max(0.0, min(1.0, float(frac))), msg, time.monotonic() - t_all)

    _p(0.02, "Conectando ao sistema…")
    sf = _sf_conectar_salesforce(verbose=False)
    if sf is None:
        _sf_logger.warning("Salesforce: ligação ou autenticação sem sucesso (detalhe só em log).")
        return None, "sem_registo"
    _p(0.12, "Buscando informações do cliente…")

    rfield = (os.environ.get("SALESFORCE_RANKING_FIELD") or "Ranking__c").strip()
    poll_sec = _sf_float_env_ranking("SALESFORCE_RISK3_POLL_SECONDS", 90.0)
    poll_iv = _sf_float_env_ranking("SALESFORCE_RISK3_POLL_INTERVAL", 2.0)
    http_timeout = max(5.0, _sf_float_env_ranking("SALESFORCE_REST_TIMEOUT", 45.0))

    def _ranking_conta(account_id: str) -> str | None:
        _p(0.28, "Consultando a classificação do cliente…")
        bruto = _sf_get_ranking_account_rest(sf, account_id, rfield, http_timeout)
        if bruto:
            _p(1.0, _SF_RANK_PROGRESS_MSG_SUCESSO)
            return bruto
        _p(0.35, "Aguardando a classificação ficar disponível…")

        def _pp_sub(frac: float, m: str) -> None:
            _p(frac, m)

        return _sf_poll_ranking_na_account(
            sf,
            account_id,
            rfield=rfield,
            poll_sec=poll_sec,
            poll_iv=poll_iv,
            http_timeout=http_timeout,
            progress_p=_pp_sub,
            prog_lo=0.35,
            prog_hi=0.94,
        )

    opp, err = _sf_consultar_por_cpf(sf, cpf)
    _p(0.22, "Busca nas vendas concluída.")
    if err and "Informe um CPF válido" in err:
        return None, "cpf_incompleto"
    if err and "Erro ao consultar" in (err or ""):
        _sf_logger.warning("Salesforce Opportunity: %s", err)

    if opp is not None:
        info = _sf_extrair_ranking_ui_de_opportunity(opp)
        texto_opp = info.get("ranking_exibir")
        if texto_opp:
            _p(1.0, _SF_RANK_PROGRESS_MSG_SUCESSO)
            return _sf_ranking_bruto_para_ui(str(texto_opp)), None

    _p(
        0.23,
        "Classificação ainda não encontrada nas vendas. "
        "Verificando o cadastro do cliente…",
    )

    aid: str | None = None
    if opp is not None:
        raw_aid = opp.get("AccountId")
        if raw_aid:
            aid = str(raw_aid).strip()
    if not aid:
        _p(0.24, "Procurando cadastro com este CPF…")
        aid = _sf_buscar_account_id_por_cpf(sf, cpf)

    if aid:
        bruto = _ranking_conta(aid)
        if bruto:
            return _sf_ranking_bruto_para_ui(bruto), None
        return None, "sem_registo"

    if not _sf_autocriar_pf_account():
        return None, "sem_registo"

    _p(0.26, "Cliente não cadastrado. Incluindo no sistema…")
    new_aid, create_err = _sf_criar_conta_pf_ranking(sf, cpf)
    conta_criada_neste_fluxo = bool(new_aid)
    if not new_aid and create_err:
        new_aid = _sf_resolver_account_apos_falha_cpf_duplicado(sf, cpf, create_err)
        conta_criada_neste_fluxo = False
    if not new_aid:
        _sf_logger.warning("Salesforce PF Account: %s", create_err or "sem Id")
        return None, "sem_registo"
    _p(0.30, "Cadastro concluído. Obtendo a classificação…")

    bruto = _ranking_conta(new_aid)
    if bruto:
        if conta_criada_neste_fluxo:
            _sf_excluir_oportunidade_criada_simulacao(sf, new_aid, http_timeout)
            _sf_excluir_account_criada_simulacao(sf, new_aid, http_timeout)
        return _sf_ranking_bruto_para_ui(bruto), None
    return None, "sem_registo"


def _sf_extrair_ranking_ui_de_opportunity(opp: Any) -> dict[str, Any]:
    """Extrai ranking a partir do registo Opportunity (Account aninhada)."""
    conta = opp.get("Account") or {}
    raw_acc = conta.get("Ranking__c")
    raw_opp = opp.get("Ranking__c")
    m_acc = _sf_mapear_ranking_para_ui(raw_acc)
    m_opp = _sf_mapear_ranking_para_ui(raw_opp)
    texto = m_acc or m_opp or (raw_acc if raw_acc else None) or (raw_opp if raw_opp else None)
    return {
        "ranking_exibir": texto,
        "ranking_score_conta": conta.get("Ranking_Score__c"),
        "ranking_score_opp": opp.get("Ranking_Score__c"),
        "nome_conta": conta.get("Name"),
        "nome_opp": opp.get("Name"),
    }


@st.cache_data(ttl=300, show_spinner=False)
def _lookup_ranking_salesforce_cached(cpf11: str) -> tuple[str | None, str | None]:
    _injetar_secrets_salesforce_no_env()
    return _sf_classificar_ranking_cpf_11(cpf11)


@st.cache_data(ttl=300, show_spinner=False)
def _lookup_ranking_oportunidade_sf_cached(cpf11: str) -> tuple[dict[str, Any] | None, str | None]:
    """Detalhe do ranking: Opportunity quando existir; senão valores obtidos na Account/poll."""
    d = re.sub(r"\D", "", str(cpf11 or ""))
    if len(d) != 11:
        return None, "cpf_incompleto"
    _injetar_secrets_salesforce_no_env()
    texto, code = _sf_classificar_ranking_cpf_11(d)
    if not texto:
        if code == "cpf_incompleto":
            return None, "cpf_incompleto"
        if code == "pacote_ausente":
            return None, "pacote_ausente"
        return None, code or "sem_registo"
    sf = _sf_conectar_salesforce()
    if sf is not None:
        opp, _err = _sf_consultar_por_cpf(sf, d)
        if opp is not None:
            info = _sf_extrair_ranking_ui_de_opportunity(opp)
            if info.get("ranking_exibir"):
                return info, None
    return {
        "ranking_exibir": texto,
        "ranking_score_conta": None,
        "ranking_score_opp": None,
        "nome_conta": None,
        "nome_opp": None,
    }, None


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


def _dv_alerta_vermelho(inner_html: str) -> None:
    """Aviso ou erro com fundo vermelho Direcional e texto branco centralizado na caixa."""
    st.markdown(
        f'<div class="dv-alert-direcional" role="alert">'
        f'<div class="dv-alert-direcional-inner">{inner_html}</div></div>',
        unsafe_allow_html=True,
    )


def _dv_alerta_vermelho_texto(texto: str) -> None:
    """Versão com escape HTML (mensagens vindas de exceções ou texto puro)."""
    _dv_alerta_vermelho(html_std.escape(str(texto or "")).replace("\n", "<br/>"))


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
    _ = canal_imobiliaria  # reservado para extensões futuras; não entra no texto padrão
    def item(label: str, valor) -> str:
        return f"• *{_wa_escape_texto(label)}:* {_wa_escape_texto(valor)}"

    def brs(key, default=0):
        return f"R$ {fmt_br(d.get(key, default))}"

    amort = nome_sistema_amortizacao_completo(str(d.get("sistema_amortizacao", "SAC")))
    prazo = d.get("prazo_financiamento", 360)

    try:
        vc_apl = max(0.0, float(volta_caixa_val or 0))
    except (TypeError, ValueError):
        vc_apl = 0.0
    v_total = max(0.0, float(d.get("imovel_valor", 0) or 0))

    try:
        outros_apl_wa = max(0.0, float(d.get("outros_descontos", 0) or 0))
    except (TypeError, ValueError):
        outros_apl_wa = 0.0
    v_final_wa = max(0.0, v_total - vc_apl - outros_apl_wa)
    _pol_ps = str(d.get("politica", "Direcional") or "Direcional").strip()
    _pol_ps_label = "Emcash" if _politica_emcash(_pol_ps) else "Direcional"

    _nome_cli_raw = str(d.get("nome", "") or "").strip()

    linhas = [
        "*Resumo da simulação - Direcional*",
    ]
    if _nome_cli_raw:
        linhas.append(f"*Cliente / Imobiliária:* {_wa_escape_texto(_nome_cli_raw)}")
    linhas.extend(["", "*Renda*"])
    _cpf_wa_d = re.sub(r"\D", "", str(d.get("cpf") or ""))
    if len(_cpf_wa_d) == 11:
        linhas.append(item("CPF", _sf_cpf_mascarado_br(_cpf_wa_d)))
    elif str(d.get("cpf") or "").strip():
        linhas.append(item("CPF", _wa_escape_texto(str(d.get("cpf") or "").strip())))
    _rank_wa_s = str(d.get("ranking") or "").strip()
    if _rank_wa_s:
        linhas.append(item("Ranking do cliente", _wa_escape_texto(_rank_wa_s)))
    linhas.append(item("Renda familiar total", brs("renda", 0)))

    linhas.extend(["", "*Dados do imóvel*"])
    linhas.append(item("Empreendimento", d.get("empreendimento_nome", "-")))
    linhas.append(item("Unidade", d.get("unidade_id", "-")))
    linhas.append(item("Valor de venda (lista)", f"R$ {fmt_br(v_total)}"))
    _desc_wa = vc_apl + outros_apl_wa
    if _desc_wa > 0.009:
        linhas.append(item("Descontos Concedidos", f"R$ {fmt_br(_desc_wa)}"))
    _mot_wa = str(d.get("outros_descontos_motivo") or "").strip()
    if outros_apl_wa > 0.009 and _mot_wa:
        linhas.append(item("Origem dos outros descontos", _mot_wa))
    linhas.append(item("Valor final da unidade", f"R$ {fmt_br(v_final_wa)}"))
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
            item("Sistema de amortização e prazo", f"{amort} - {prazo} meses"),
            item("Parcela estimada do financiamento", brs("parcela_financiamento", 0)),
            item("FGTS + subsídio", brs("fgts_sub_usado", 0)),
            "",
            "*Entrada e Pro Soluto*",
        ]
    )
    if _politica_emcash(d.get("politica")):
        linhas.append(
            item(
                "Política de Pro Soluto",
                f"{_pol_ps_label} ({_wa_escape_texto(_EMCASH_NOTA_PARCELAS)})",
            )
        )
    else:
        linhas.append(item("Política de Pro Soluto", _pol_ps_label))
    linhas.extend(
        [
            item("Pro Soluto (valor)", brs("ps_usado", 0)),
            item("Número de parcelas do Pro Soluto", d.get("ps_parcelas", "-")),
            item("Mensalidade do Pro Soluto", brs("ps_mensal", 0)),
            item("Ato 1 (Entrada Imediata)", brs("ato_final", 0)),
        ]
    )
    if _politica_emcash(d.get("politica")):
        linhas.append(item("Ato 30", brs("ato_30", 0)))
        linhas.append(item("Ato 60", brs("ato_60", 0)))
    else:
        linhas.append(item("Ato 30", brs("ato_30", 0)))
        linhas.append(item("Ato 60", brs("ato_60", 0)))
        linhas.append(item("Ato 90", brs("ato_90", 0)))
    _ent_tot = float(d.get("entrada_total", 0) or 0) + float(d.get("ps_usado", 0) or 0)
    linhas.append(item("Entrada total (atos e Pro Soluto)", f"R$ {fmt_br(_ent_tot)}"))

    nc = (nome_consultor or "").strip()
    if nc:
        linhas.extend(["", f"*Consultor:* {_wa_escape_texto(nc)}"])

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


def _normalizar_numero_texto(s: str) -> str:
    """
    Normaliza números com vírgula/ponto seguindo a regra de entrada:
    - 2 casas após o separador => decimal (12,50 -> 12.50 | 12.50 -> 12.50)
    - 3+ casas após o separador => milhar/inteiro (1,250 -> 1250 | 1.250 -> 1250)
    """
    t = str(s).strip()
    if t == "":
        return t
    sinal = ""
    if t[0] in "+-":
        sinal = t[0]
        t = t[1:]
    if t == "":
        return sinal

    if "," not in t and "." not in t:
        return f"{sinal}{t}"

    # Com vírgula e ponto, usa o último separador como candidato a decimal.
    if "," in t and "." in t:
        idx = max(t.rfind(","), t.rfind("."))
        frac = t[idx + 1:]
        if frac.isdigit() and len(frac) <= 2:
            inteiro = re.sub(r"[.,]", "", t[:idx])
            return f"{sinal}{inteiro}.{frac}"
        return f"{sinal}{re.sub(r'[.,]', '', t)}"

    sep = "," if "," in t else "."
    partes = t.split(sep)
    if len(partes) == 1:
        return f"{sinal}{t}"

    frac = partes[-1]
    if frac.isdigit() and len(frac) <= 2:
        inteiro = "".join(partes[:-1])
        return f"{sinal}{inteiro}.{frac}"

    return f"{sinal}{''.join(partes)}"


def safe_float_convert(val):
    if pd.isnull(val) or val == "":
        return 0.0
    if isinstance(val, bool):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace("R$", "").replace("\u00a0", " ").strip()
    s_compact = re.sub(r"\s+", "", s)
    s_try = _normalizar_numero_texto(s_compact)
    try:
        return float(s_try)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    if "," in s_compact or "." in s_compact:
        s2 = _normalizar_numero_texto(s_compact)
    else:
        s2 = s_compact
    try:
        return float(s2)
    except ValueError:
        return 0.0


def texto_moeda_para_float(s, default=0.0):
    """Converte texto livre (BR/US) em float; vazio -> default."""
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
    t = _normalizar_numero_texto(t)
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
    _st_iframe_html_snippet(js, height=0)

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
    _st_iframe_html_snippet(js, height=0, width=0)


def inject_home_banner_dialog_modal():
    """Popup de campanha: overlay criado em JS (o Streamlit sanitiza o markdown e costuma remover <dialog>).

    Dados vêm de data-dv-src (URL) e data-dv-t64 / data-dv-b64 (título e texto em UTF-8 base64).
    """
    js = r"""
<script>
(function () {
  function b64ToUtf8(b64) {
    if (!b64) return "";
    try {
      var bin = atob(b64);
      var bytes = new Uint8Array(bin.length);
      for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return new TextDecoder("utf-8").decode(bytes);
    } catch (e) {
      return "";
    }
  }
  function closeDvCampanha(doc) {
    var root = doc.getElementById("dv-campanha-overlay-root");
    if (root) {
      try {
        if (root.__dvCampanhaResize) {
          var rw = root.__dvCampanhaResizeWin || window;
          rw.removeEventListener("resize", root.__dvCampanhaResize);
        }
      } catch (e0) {}
      root.remove();
    }
    try {
      doc.removeEventListener("keydown", doc.__dvCampanhaEscHandler);
    } catch (e2) {}
    doc.__dvCampanhaEscHandler = null;
  }
  function openDvCampanha(doc, src, titleB64, bodyB64) {
    closeDvCampanha(doc);
    var title = b64ToUtf8(titleB64);
    var body = b64ToUtf8(bodyB64);
    var root = doc.createElement("div");
    root.id = "dv-campanha-overlay-root";
    root.className = "dv-campanha-overlay";
    root.setAttribute("role", "dialog");
    root.setAttribute("aria-modal", "true");
    root.setAttribute("aria-label", "Campanha comercial");
    var back = doc.createElement("div");
    back.className = "dv-campanha-overlay-backdrop";
    var panel = doc.createElement("div");
    panel.className = "dv-campanha-overlay-panel";
    var closeBtn = doc.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "dv-campanha-overlay-close";
    closeBtn.setAttribute("aria-label", "Fechar");
    closeBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><line x1="2" y1="2" x2="12" y2="12" stroke="#0f172a" stroke-width="2" stroke-linecap="round"/><line x1="12" y1="2" x2="2" y2="12" stroke="#0f172a" stroke-width="2" stroke-linecap="round"/></svg>';
    closeBtn.addEventListener("click", function (ev) {
      ev.stopPropagation();
      closeDvCampanha(doc);
    });
    var imgWrap = doc.createElement("div");
    imgWrap.className = "dv-campanha-overlay-img-wrap";
    var img = doc.createElement("img");
    img.className = "dv-campanha-overlay-img";
    img.alt = "";
    img.loading = "eager";
    img.decoding = "async";
    img.src = src;
    imgWrap.appendChild(img);
    var textWrap = doc.createElement("div");
    textWrap.className = "dv-campanha-overlay-text";
    if (title) {
      var h = doc.createElement("h3");
      h.className = "dv-campanha-overlay-title";
      h.textContent = title;
      textWrap.appendChild(h);
    }
    if (body) {
      var p = doc.createElement("div");
      p.className = "dv-campanha-overlay-body";
      p.textContent = body;
      textWrap.appendChild(p);
    }
    var inner = doc.createElement("div");
    inner.className = "dv-campanha-overlay-inner";
    inner.appendChild(imgWrap);
    if (title || body) inner.appendChild(textWrap);
    panel.appendChild(closeBtn);
    panel.appendChild(inner);
    root.appendChild(back);
    root.appendChild(panel);
    function layoutCampanhaPopup() {
      try {
        var w = img.clientWidth;
        if (w > 0 && textWrap && inner.contains(textWrap)) {
          textWrap.style.width = w + "px";
          textWrap.style.maxWidth = w + "px";
        }
      } catch (e3) {}
    }
    img.addEventListener("load", layoutCampanhaPopup);
    if (img.complete) {
      requestAnimationFrame(layoutCampanhaPopup);
    }
    var rz = function () {
      requestAnimationFrame(layoutCampanhaPopup);
    };
    var win = doc.defaultView || window;
    win.addEventListener("resize", rz);
    root.__dvCampanhaResize = rz;
    root.__dvCampanhaResizeWin = win;
    back.addEventListener("click", function () {
      closeDvCampanha(doc);
    });
    panel.addEventListener("click", function (ev) {
      ev.stopPropagation();
    });
    doc.body.appendChild(root);
    doc.__dvCampanhaEscHandler = function (kev) {
      if (kev.key === "Escape") closeDvCampanha(doc);
    };
    doc.addEventListener("keydown", doc.__dvCampanhaEscHandler);
  }
  function wire(doc) {
    if (!doc || !doc.body) return;
    if (doc.__dvCampanhaPopupWired) return;
    doc.__dvCampanhaPopupWired = true;
    doc.addEventListener(
      "click",
      function (ev) {
        var t = ev.target;
        if (!t || !t.closest) return;
        var openBtn = t.closest(".home-banner-lb-open");
        if (openBtn) {
          ev.preventDefault();
          var src = openBtn.getAttribute("data-dv-src");
          if (!src) return;
          var d = openBtn.ownerDocument || doc;
          openDvCampanha(
            d,
            src,
            openBtn.getAttribute("data-dv-t64") || "",
            openBtn.getAttribute("data-dv-b64") || ""
          );
        }
      },
      true
    );
  }
  var appDoc = document;
  try {
    if (window.parent && window.parent !== window && window.parent.document) {
      appDoc = window.parent.document;
    }
  } catch (eParent) {
    appDoc = document;
  }
  wire(appDoc);
})();
</script>
"""
    _st_iframe_html_snippet(js, height=0, width=0)


def inject_modern_ui_runtime():
    """Marca o documento com preferências de movimento para CSS; JS vanilla no parent (Streamlit usa React internamente - não há runtime React app embutível neste ficheiro)."""
    js = r"""
<script>
(function () {
  var doc = document;
  try {
    if (window.parent && window.parent !== window && window.parent.document) {
      doc = window.parent.document;
    }
  } catch (e) {
    doc = document;
  }
  var root = doc.documentElement;
  if (!root || root.getAttribute("data-dv-ui-runtime") === "1") return;
  root.setAttribute("data-dv-ui-runtime", "1");
  try {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      root.setAttribute("data-dv-reduced-motion", "1");
    }
  } catch (e2) {}
})();
</script>
"""
    _st_iframe_html_snippet(js, height=0, width=0)


# =============================================================================
# 1. CARREGAMENTO DE DADOS
# =============================================================================

_COLS_HOME_BANNERS = (
    "Ordem",
    "URL_Imagem",
    "Titulo",
    "Ativo",
    "Tela_Cheia",
    "Descricao",
    "Chave_Campanha",
)
_WS_CAMPANHAS_TEXTO = "BD Campanhas Texto"
_COLS_CAMPANHAS_TEXTO = ("Ordem", "Titulo", "Texto", "Ativo", "Chave_Campanha")


def normalizar_df_campanhas_texto(df: pd.DataFrame | None) -> pd.DataFrame:
    """Planilha BD Campanhas Texto: Ordem, Titulo, Texto, Ativo (SIM/NÃO)."""
    if df is None or df.empty:
        return pd.DataFrame(columns=list(_COLS_CAMPANHAS_TEXTO))
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    ren = {
        "ordem": "Ordem",
        "título": "Titulo",
        "Título": "Titulo",
        "titulo": "Titulo",
        "texto": "Texto",
        "ativo": "Ativo",
        "chave": "Chave_Campanha",
        "Chave": "Chave_Campanha",
        "chave campanha": "Chave_Campanha",
        "Chave campanha": "Chave_Campanha",
        "chave_campanha": "Chave_Campanha",
    }
    for a, b in list(ren.items()):
        if a in out.columns and a != b:
            out = out.rename(columns={a: b})
    for c in _COLS_CAMPANHAS_TEXTO:
        if c not in out.columns:
            out[c] = None if c == "Ordem" else ""
    return out[list(_COLS_CAMPANHAS_TEXTO)].copy()


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
        "chave": "Chave_Campanha",
        "Chave": "Chave_Campanha",
        "chave campanha": "Chave_Campanha",
        "Chave campanha": "Chave_Campanha",
        "chave_campanha": "Chave_Campanha",
    }
    for a, b in list(ren.items()):
        if a in out.columns and a != b:
            out = out.rename(columns={a: b})
    for c in _COLS_HOME_BANNERS:
        if c not in out.columns:
            out[c] = None if c == "Ordem" else ""
    return out[list(_COLS_HOME_BANNERS)].copy()


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


def _titulo_campanha_com_dois_pontos_final(tit: str) -> str:
    """Garante exatamente um ':' no fim do título; remove ':' extras no final antes de acrescentar."""
    s = (tit or "").strip()
    if not s:
        return ""
    core = s.rstrip(":").rstrip()
    return f"{core}:" if core else ":"


def _html_campanhas_texto_bloco(df_texto: pd.DataFrame) -> str:
    df = normalizar_df_campanhas_texto(df_texto)
    if df.empty:
        return ""
    df = df.reset_index(drop=True)
    items: list[str] = []
    for _, row in df.iterrows():
        tit = str(row.get("Titulo", "") or "").strip()
        body = str(row.get("Texto", "") or "").strip()
        if not tit and not body:
            continue
        tit_esc = html_std.escape(_titulo_campanha_com_dois_pontos_final(tit))
        body_esc = html_std.escape(body)
        if tit_esc and body_esc:
            inner = f'<span class="home-campanhas-copy-titulo">{tit_esc}</span> {body_esc}'
        elif tit_esc:
            inner = f'<span class="home-campanhas-copy-titulo">{tit_esc}</span>'
        else:
            inner = body_esc
        items.append(f"<li>{inner}</li>")
    if not items:
        return ""
    return (
        '<div class="home-campanhas-copy" role="region" aria-label="Detalhes das campanhas">'
        '<ul class="home-campanhas-copy-list">'
        + "".join(items)
        + "</ul></div>"
    )


def _utf8_base64_attr(s: str) -> str:
    """UTF-8 → base64 (ASCII) para data-* no HTML (evita aspas quebradas)."""
    return base64.b64encode((s or "").encode("utf-8")).decode("ascii")


@st.dialog("Campanhas comerciais")
def dialog_adm_miniaturas_home_banners(df_home_banners: pd.DataFrame | None) -> None:
    """Gestão da aba BD Home Banners (URL, título e descrição do popup por miniatura)."""
    st.caption(
        "Aba **BD Home Banners** na planilha geral. Use **URL https** direta da imagem; a ordem na galeria segue a ordem das linhas. "
        "O **Título** e a **Descrição** desta linha são os que aparecem no **popup** ao clicar na miniatura."
    )
    with st.form("form_novo_home_banner"):
        bn_url = st.text_input(
            "Endereço da imagem (URL) (texto — https)",
            placeholder="https://i.postimg.cc/...",
        )
        bn_titulo = st.text_input(
            "Título no popup (texto)",
            placeholder="Ex.: Campanha de verão",
        )
        bn_desc = st.text_area(
            "Descrição no popup (texto)",
            placeholder="Texto curto que aparece abaixo da imagem…",
            height=72,
        )
        enviar_bn = st.form_submit_button("Gravar nova imagem na aba Banners da home", type="primary")
    if enviar_bn:
        url_t = (bn_url or "").strip()
        if not url_t.startswith("https://"):
            _dv_alerta_vermelho(
                "A URL da imagem deve começar com <strong>https://</strong> "
                "(use o link direto do Postimages)."
            )
        else:
            ok, err = gravar_nova_linha_home_banner(
                url_t,
                titulo=(bn_titulo or "").strip(),
                descricao=(bn_desc or "").strip(),
            )
            if ok:
                st.cache_data.clear()
                st.success("Imagem gravada na planilha. Recarregando…")
                st.rerun()
            else:
                _dv_alerta_vermelho_texto(f"Não foi possível gravar: {err}")

    st.markdown("**Remover miniatura**")
    _df_bn_adm = normalizar_df_home_banners(df_home_banners if df_home_banners is not None else pd.DataFrame())
    _df_bn_adm = _df_bn_adm.reset_index(drop=True)
    if _df_bn_adm.empty:
        st.caption("Não há linhas na aba Banners da home.")
    else:
        _opts_idx = list(range(len(_df_bn_adm)))
        _ix_del = st.selectbox(
            "Linha a excluir (mesma ordem da planilha ao carregar) (lista)",
            options=_opts_idx,
            format_func=lambda j: _rotulo_opcao_excluir_banner(_df_bn_adm, int(j)),
            key="home_banner_excluir_select",
        )
        _conf_del = st.checkbox(
            "Confirmo que quero remover permanentemente esta linha da planilha",
            key="home_banner_excluir_confirma",
        )
        if st.button("Excluir linha selecionada", type="secondary", key="home_banner_excluir_btn"):
            if not _conf_del:
                _dv_alerta_vermelho_texto("Marque a confirmação para excluir.")
            else:
                ok_del, err_del = excluir_linha_home_banner(int(_ix_del))
                if ok_del:
                    st.cache_data.clear()
                    st.success("Linha removida. Recarregando…")
                    st.rerun()
                else:
                    _dv_alerta_vermelho_texto(f"Não foi possível excluir: {err_del}")


@st.dialog("Textos - campanhas comerciais (administrador)")
def dialog_adm_textos_campanhas(df_campanhas_texto: pd.DataFrame) -> None:
    """Formulários admin para a aba de textos (lista pública abaixo das miniaturas)."""
    st.caption(
        f"Aba **{_WS_CAMPANHAS_TEXTO}** (colunas **Titulo** e **Texto**; **Ordem** e **Ativo** seguem a planilha). "
        "Estes textos aparecem na **lista abaixo das miniaturas** para todos os utilizadores."
    )
    with st.form("form_novo_campanha_texto"):
        ct_titulo = st.text_input(
            "Título (texto)",
            placeholder='Ex.: "Campanha de Carnaval"',
        )
        ct_texto = st.text_area(
            "Texto (texto)",
            placeholder="Ex.: Campanha x e y válida entre xc e yc.",
            height=100,
        )
        enviar_ct = st.form_submit_button(
            f"Gravar nova linha em {_WS_CAMPANHAS_TEXTO}", type="primary"
        )
    if enviar_ct:
        if not (ct_titulo or "").strip() and not (ct_texto or "").strip():
            _dv_alerta_vermelho_texto("Preencha pelo menos o título ou o texto.")
        else:
            ok_ct, err_ct = gravar_nova_linha_campanha_texto(
                (ct_titulo or "").strip(),
                (ct_texto or "").strip(),
            )
            if ok_ct:
                st.cache_data.clear()
                st.success("Linha gravada. Recarregando…")
                st.rerun()
            else:
                _dv_alerta_vermelho_texto(f"Não foi possível gravar: {err_ct}")

    st.markdown("**Remover linha de texto**")
    _df_ct_adm = normalizar_df_campanhas_texto(df_campanhas_texto)
    _df_ct_adm = _df_ct_adm.reset_index(drop=True)
    if _df_ct_adm.empty:
        st.caption(f"Não há linhas em {_WS_CAMPANHAS_TEXTO} (ou a aba ainda não existe).")
    else:
        _opts_ct = list(range(len(_df_ct_adm)))
        _ix_ct = st.selectbox(
            "Linha a excluir (lista)",
            options=_opts_ct,
            format_func=lambda j: _rotulo_opcao_excluir_campanha_texto(_df_ct_adm, int(j)),
            key="campanha_texto_excluir_select",
        )
        _conf_ct = st.checkbox(
            "Confirmo exclusão permanente desta linha",
            key="campanha_texto_excluir_confirma",
        )
        if st.button("Excluir linha selecionada", type="secondary", key="campanha_texto_excluir_btn"):
            if not _conf_ct:
                _dv_alerta_vermelho_texto("Marque a confirmação para excluir.")
            else:
                ok_dct, err_dct = excluir_linha_campanha_texto(int(_ix_ct))
                if ok_dct:
                    st.cache_data.clear()
                    st.success("Linha removida. Recarregando…")
                    st.rerun()
                else:
                    _dv_alerta_vermelho_texto(f"Não foi possível excluir: {err_dct}")


@st.dialog("Campanha comercial")
def dialog_visualizar_campanha(campanha: dict[str, str]) -> None:
    """Popup nativo Streamlit para exibir campanha com imagem e descrição."""
    src = str(campanha.get("src", "") or "").strip()
    titulo = str(campanha.get("titulo", "") or "").strip()
    descricao = str(campanha.get("descricao", "") or "").strip()
    if src:
        st.image(src, use_container_width=True)
    if titulo:
        st.markdown(
            f'<h3 class="dv-titulo-secao">{html_std.escape(titulo)}</h3>',
            unsafe_allow_html=True,
        )
    if descricao:
        st.write(descricao)
    else:
        st.caption("Sem descrição para esta campanha.")
    if st.button("Fechar", key=f"dv_fechar_campanha_{abs(hash(src + titulo)) % 10_000_000}", use_container_width=True):
        st.rerun()


def render_secao_campanhas_comerciais(
    df_banners: pd.DataFrame,
    df_texto_campanhas: pd.DataFrame | None = None,
    *,
    user_is_adm: bool = False,
) -> None:
    """Faixa de miniaturas (clique = popup com imagem + título/descrição da linha na BD Home Banners) + textos públicos em lista."""
    df_bn = normalizar_df_home_banners(df_banners).reset_index(drop=True)
    df_txt = df_texto_campanhas if df_texto_campanhas is not None else pd.DataFrame()
    copy_html = _html_campanhas_texto_bloco(df_txt)

    def _render_miniaturas_popup_real(campanhas: list[dict[str, str]]) -> None:
        """Renderiza miniaturas que disparam o popup JS legado (home-banner-lb-open)."""
        if not campanhas:
            return
        cards: list[str] = []
        for c in campanhas:
            src = _img_url_seguro_https(str(c.get("src", "") or ""))
            if not src:
                continue
            t64 = _utf8_base64_attr(str(c.get("titulo", "") or ""))
            b64 = _utf8_base64_attr(str(c.get("descricao", "") or ""))
            cards.append(
                f'<div class="home-banner-lb-root">'
                f'<button type="button" class="home-banner-card home-banner-card--fs home-banner-card--thumb home-banner-lb-open" '
                f'data-dv-src="{src}" data-dv-t64="{html_std.escape(t64, quote=True)}" data-dv-b64="{html_std.escape(b64, quote=True)}" '
                f'title="Ver campanha" aria-label="Abrir campanha em destaque">'
                f'<span class="home-banner-thumb-frame"><img src="{src}" alt="" loading="lazy" decoding="async" /></span>'
                f"</button></div>"
            )
        if not cards:
            return
        strip_html = (
            '<div class="home-banners-strip-outer">'
            '<div class="home-banners-strip" role="group" aria-label="Miniaturas de campanhas">'
            + "".join(cards)
            + "</div></div>"
        )
        st.markdown('<div class="home-banners-wrap">' + strip_html + "</div>", unsafe_allow_html=True)
    campanhas_ativas: list[dict[str, str]] = []
    if not df_bn.empty:
        for _, row in df_bn.iterrows():
            atv = str(row.get("Ativo", "SIM") or "").strip().upper()
            if atv in ("NÃO", "NAO", "N", "NO", "FALSE", "0"):
                continue
            src = _img_url_seguro_https(str(row.get("URL_Imagem", "") or ""))
            if not src:
                continue
            campanhas_ativas.append(
                {
                    "src": src,
                    "titulo": str(row.get("Titulo", "") or "").strip(),
                    "descricao": str(row.get("Descricao", "") or "").strip(),
                }
            )
    if not campanhas_ativas and not copy_html and not user_is_adm:
        return
    if not user_is_adm:
        st.markdown(
            '<div class="home-banners-wrap" role="region" aria-label="Campanhas comerciais">'
            '<h2 class="home-banners-section-title">Campanhas comerciais</h2>'
            + "</div>",
            unsafe_allow_html=True,
        )
        _render_miniaturas_popup_real(campanhas_ativas)
    else:
        st.markdown(
            '<div class="home-banners-wrap" role="region" aria-label="Campanhas comerciais">'
            '<h2 class="home-banners-section-title">Campanhas comerciais</h2>'
            "</div>",
            unsafe_allow_html=True,
        )
        bc1, bc2 = st.columns([1, 1], gap="small")
        with bc1:
            if st.button(
                "Campanhas comerciais",
                key="dv_open_dialog_campanhas_miniaturas",
                type="secondary",
                use_container_width=True,
            ):
                dialog_adm_miniaturas_home_banners(df_banners)
        with bc2:
            if st.button(
                "Textos - campanhas comerciais (administrador)",
                key="dv_open_dialog_campanhas_textos",
                type="secondary",
                use_container_width=True,
            ):
                dialog_adm_textos_campanhas(df_txt)
        _render_miniaturas_popup_real(campanhas_ativas)

    if copy_html:
        st.markdown(copy_html, unsafe_allow_html=True)


def gravar_nova_linha_home_banner(
    url_imagem: str,
    *,
    chave_campanha: str = "",
    titulo: str = "",
    descricao: str = "",
) -> tuple[bool, str]:
    """Anexa linha na aba BD Home Banners (Título e Descrição alimentam o popup da miniatura)."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_raw = conn.read(spreadsheet=ID_GERAL, worksheet="BD Home Banners")
        df_ex = normalizar_df_home_banners(df_raw)
        ordens = pd.to_numeric(df_ex["Ordem"], errors="coerce")
        prox = int(ordens.max()) + 1 if len(df_ex) and ordens.notna().any() else len(df_ex) + 1
        nova = pd.DataFrame(
            [
                {
                    "Ordem": prox,
                    "URL_Imagem": url_imagem.strip(),
                    "Titulo": (titulo or "").strip(),
                    "Ativo": "SIM",
                    "Tela_Cheia": "SIM",
                    "Descricao": (descricao or "").strip(),
                    "Chave_Campanha": (chave_campanha or "").strip(),
                }
            ]
        )
        df_final = pd.concat([df_ex, nova], ignore_index=True)
        conn.update(spreadsheet=ID_GERAL, worksheet="BD Home Banners", data=df_final)
        return True, ""
    except Exception as e:
        return False, str(e)


def gravar_nova_linha_campanha_texto(
    titulo: str,
    texto: str,
    *,
    chave_campanha: str = "",
) -> tuple[bool, str]:
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_raw = conn.read(spreadsheet=ID_GERAL, worksheet=_WS_CAMPANHAS_TEXTO)
        df_ex = normalizar_df_campanhas_texto(df_raw)
        ordens = pd.to_numeric(df_ex["Ordem"], errors="coerce")
        prox = int(ordens.max()) + 1 if len(df_ex) and ordens.notna().any() else len(df_ex) + 1
        nova = pd.DataFrame(
            [
                {
                    "Ordem": prox,
                    "Titulo": (titulo or "").strip(),
                    "Texto": (texto or "").strip(),
                    "Ativo": "SIM",
                    "Chave_Campanha": (chave_campanha or "").strip(),
                }
            ]
        )
        df_final = pd.concat([df_ex, nova], ignore_index=True)
        conn.update(spreadsheet=ID_GERAL, worksheet=_WS_CAMPANHAS_TEXTO, data=df_final)
        return True, ""
    except Exception as e:
        return False, str(e)


def excluir_linha_campanha_texto(indice_linha: int) -> tuple[bool, str]:
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_raw = conn.read(spreadsheet=ID_GERAL, worksheet=_WS_CAMPANHAS_TEXTO)
        df_ex = normalizar_df_campanhas_texto(df_raw)
        df_ex = df_ex.reset_index(drop=True)
        n = len(df_ex)
        if n == 0:
            return False, "A planilha de texto das campanhas está vazia."
        if indice_linha < 0 or indice_linha >= n:
            return False, "Linha inválida."
        df_new = df_ex.drop(index=indice_linha).reset_index(drop=True)
        conn.update(spreadsheet=ID_GERAL, worksheet=_WS_CAMPANHAS_TEXTO, data=df_new)
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
    url = str(r.get("URL_Imagem", "") or "").strip()
    snip = (url[:56] + "…") if len(url) > 57 else url
    return f"Linha {i + 1} · {snip or '(sem URL)'}"


def _rotulo_opcao_excluir_campanha_texto(df_ct: pd.DataFrame, i: int) -> str:
    r = df_ct.iloc[i]
    tit = str(r.get("Titulo", "") or "").strip()
    tit = (tit[:48] + "…") if len(tit) > 49 else tit
    snip = str(r.get("Texto", "") or "").strip().replace("\n", " ")
    snip = (snip[:36] + "…") if len(snip) > 37 else snip
    return f"Linha {i + 1} · {tit or '(sem título)'}{' - ' + snip if snip else ''}"


def _normalizar_df_logins(df_raw: pd.DataFrame | None) -> pd.DataFrame:
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()
    df = df_raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    mapa_logins = {
        "Imobiliária/Canal IMOB": "Imobiliaria",
        "Cargo": "Cargo",
        "Nome": "Nome",
        "Email": "Email",
        "Escolha uma senha para o simulador": "Senha",
        "Número de telefone": "Telefone",
    }
    df = df.rename(columns=mapa_logins)
    if "Email" in df.columns:
        df["Email"] = df["Email"].astype(str).str.strip().str.lower()
    if "Senha" in df.columns:
        df["Senha"] = df["Senha"].astype(str).str.strip()
    return df


_DV_COOKIE_SESS = "dv_sess_jwt_v1"
_DV_COOKIE_EMAIL = "dv_last_email"
_DV_COOKIE_CM_KEY = "dv_cookie_manager_v1"


def _dv_try_init_auth_cookie_manager():
    """Uma instância por rerun: vários CookieManager com a mesma key quebram o set/get de cookies."""
    try:
        from extra_streamlit_components import CookieManager

        cm = CookieManager(key=_DV_COOKIE_CM_KEY)
        cm.get_all()
        return cm
    except Exception:
        return None


def _validar_login_planilha(df_logins: pd.DataFrame, email: str, senha: str) -> dict | None:
    if df_logins is None or df_logins.empty:
        return None
    em = (email or "").strip().lower()
    sp = (senha or "").strip()
    if not em or not sp:
        return None
    if "Email" not in df_logins.columns or "Senha" not in df_logins.columns:
        return None
    for _, row in df_logins.iterrows():
        if str(row.get("Email", "")).strip().lower() != em:
            continue
        if str(row.get("Senha", "")).strip() != sp:
            continue
        return {
            "Nome": str(row.get("Nome", "") or "").strip(),
            "Email": str(row.get("Email", "") or "").strip(),
            "Telefone": str(row.get("Telefone", "") or "").strip(),
            "Imobiliaria": str(row.get("Imobiliaria", "") or "").strip(),
            "Cargo": str(row.get("Cargo", "") or "").strip(),
        }
    return None


def _render_login_section(df_logins: pd.DataFrame, cookie_manager=None) -> None:
    if cookie_manager is not None:
        try:
            _saved_em = cookie_manager.get(_DV_COOKIE_EMAIL)
            if _saved_em:
                st.session_state.setdefault("dv_login_email_in", str(_saved_em).strip())
        except Exception:
            pass

    logo_src = html_std.escape(_src_logo_topo_header(), quote=True)
    _login_head = f"""<div class="dv-login-page" role="region" aria-label="Início de sessão">
<header class="header-container" role="banner">
<div class="header-logo-wrap">
<img src="{logo_src}" alt="Direcional Engenharia" class="header-logo-img" decoding="async" loading="eager" />
</div>
<h1 class="header-title">Simulador imobiliário DV</h1>
</header>
<div class="header-brand-bar-wrap" aria-hidden="true"></div>
<h2 class="dv-login-acesso-h2">Acesso</h2>
</div>"""

    st.markdown(_login_head, unsafe_allow_html=True)
    if df_logins is None or df_logins.empty:
        st.warning(
            "Não foi possível carregar a folha **BD Logins** (ou não há ligação ao Google Sheets). "
            "Configure a aba na base ou as credenciais em *Secrets*."
        )
        if st.button(
            "Continuar em modo demonstração",
            type="primary",
            use_container_width=True,
            key="login_demo_fallback",
        ):
            _sessao_sem_login_defaults()
            st.rerun()
        return
    with st.form("dv_login_form", clear_on_submit=False):
        st.text_input("E-mail", key="dv_login_email_in")
        st.text_input("Senha", type="password", key="dv_login_senha_in")
        submitted = st.form_submit_button(
            "Entrar",
            type="primary",
            use_container_width=True,
        )
        if submitted:
            _em = st.session_state.get("dv_login_email_in", "")
            _pw = st.session_state.get("dv_login_senha_in", "")
            row = _validar_login_planilha(df_logins, str(_em), str(_pw))
            if not row:
                st.error("E-mail ou senha inválidos.")
            else:
                _dv_apply_session_from_row(row)
                _dv_persist_after_login(
                    row,
                    remember_long=True,
                    remember_email=True,
                    cookie_manager=cookie_manager,
                )
                st.rerun()


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
                pd.DataFrame(),
                dict(DEFAULT_PREMISSAS),
                pd.DataFrame(columns=list(_COLS_CAMPANHAS_TEXTO)),
            )
        conn = st.connection("gsheets", type=GSheetsConnection)
        def limpar_moeda(val): return safe_float_convert(val)

        # Histórico em BD Simulações não é mais carregado na UI (gravação no resumo mantida)
        df_cadastros = pd.DataFrame()

        # 1. POLITICAS (Pro Soluto - comparador)
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

        try:
            df_ct_raw = conn.read(spreadsheet=ID_GERAL, worksheet=_WS_CAMPANHAS_TEXTO)
            df_campanhas_texto = normalizar_df_campanhas_texto(df_ct_raw)
        except Exception:
            df_campanhas_texto = pd.DataFrame(columns=list(_COLS_CAMPANHAS_TEXTO))

        try:
            df_logins_raw = conn.read(spreadsheet=ID_GERAL, worksheet="BD Logins")
            df_logins = _normalizar_df_logins(df_logins_raw)
        except Exception:
            df_logins = pd.DataFrame()

        return (
            df_finan,
            df_estoque,
            df_politicas,
            df_logins,
            df_cadastros,
            df_home_banners,
            premissas_dict,
            df_campanhas_texto,
        )
    except Exception as e:
        _dv_alerta_vermelho_texto(f"Erro dados: {e}")
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            dict(DEFAULT_PREMISSAS),
            pd.DataFrame(columns=list(_COLS_CAMPANHAS_TEXTO)),
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
        # Limites de avaliação para colunas F2/F3/F4 na BD Financiamentos (alinhado à curva comercial).
        if valor_avaliacao <= 275000:
            faixa = "F2"
        elif valor_avaliacao <= 400000:
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


def _ps_max_estoque_row_cliente(row: pd.Series, d: dict) -> float:
    """PS máximo da linha de estoque conforme política e ranking em `d` (mesma regra da recomendação)."""
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


def _calcular_poder_compra_linha_estoque(
    row: pd.Series, d: dict, df_politicas: pd.DataFrame, prem: dict
) -> pd.Series:
    """Poder de compra por linha (alinhado à ETAPA Recomendação)."""
    try:
        v_venda = float(row.get("Valor de Venda", 0) or 0)
    except (TypeError, ValueError):
        v_venda = 0.0
    fin = float(d.get("finan_usado", 0) or 0)
    sub = float(d.get("fgts_sub_usado", 0) or 0)
    ren = float(d.get("renda", 0) or 0)
    try:
        vc_folga = max(0.0, float(row.get("Volta_Caixa_Ref", 0) or 0))
    except (TypeError, ValueError):
        vc_folga = 0.0
    ps_stock = max(0.0, _ps_max_estoque_row_cliente(row, d))
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
                prem,
                df_politicas,
                ps_cap_estoque=ps_stock,
            )
            ps_eff = float(mps.get("ps_max_efetivo", 0) or 0)
        except Exception:
            ps_eff = float(ps_stock)
    poder = (2.0 * ren) + fin + sub + max(0.0, ps_eff) + vc_folga
    cobertura = (poder / v_venda) * 100.0 if v_venda > 0 else 0.0
    return pd.Series([poder, cobertura, fin, sub])


def _metricas_lucro_unidade(
    row: pd.Series, d: dict, df_politicas: pd.DataFrame, prem: dict
) -> pd.Series:
    """
    Métricas para recomendação por lucro:
    poder_compra_base = 2*Renda + Finan + FGTS/Sub + PS_unidade
    necessidade_vcx = max(0, Valor Venda - poder_compra_base)
    Compatível quando necessidade_vcx <= VCX_teto.
    Lucro recomendado = 1,9% do Valor Venda + 50% do VCX excedente (não utilizado).
    """
    try:
        v_venda = float(row.get("Valor de Venda", 0) or 0)
    except (TypeError, ValueError):
        v_venda = 0.0
    try:
        vcx_teto = max(0.0, float(row.get("Volta_Caixa_Ref", 0) or 0))
    except (TypeError, ValueError):
        vcx_teto = 0.0
    ren = float(d.get("renda", 0) or 0)
    fin = float(d.get("finan_usado", 0) or 0)
    sub = float(d.get("fgts_sub_usado", 0) or 0)
    ps_unid = max(0.0, _ps_max_estoque_row_cliente(row, d))

    poder_compra_base = (2.0 * ren) + fin + sub + ps_unid
    necessidade_vcx = max(0.0, v_venda - poder_compra_base)
    saldo_teto_vcx = vcx_teto - necessidade_vcx
    compativel = bool(necessidade_vcx <= vcx_teto + 1e-9)

    vcx_usado = min(vcx_teto, necessidade_vcx)
    vcx_preservado = max(0.0, vcx_teto - vcx_usado)
    comissao = 0.019 * v_venda
    lucro = (comissao + (0.5 * vcx_preservado)) if compativel else -1e18
    return pd.Series([compativel, vcx_usado, vcx_preservado, lucro, saldo_teto_vcx])


def df_estoque_com_poder_compra(
    df: pd.DataFrame, d: dict, df_politicas: pd.DataFrame, prem: dict
) -> pd.DataFrame:
    """Anexa Poder_Compra, Cobertura, Finan_Unid, Sub_Unid (cópia do dataframe)."""
    out = df.copy()
    if out.empty:
        return out
    out[["Poder_Compra", "Cobertura", "Finan_Unid", "Sub_Unid"]] = out.apply(
        lambda r: _calcular_poder_compra_linha_estoque(r, d, df_politicas, prem),
        axis=1,
    )
    out[["Unidade_Compativel", "VCX_Usado_Fechamento", "VCX_Preservado", "Lucro_Recomendacao", "Saldo_Teto_VCX"]] = out.apply(
        lambda r: _metricas_lucro_unidade(r, d, df_politicas, prem),
        axis=1,
    )
    return out


def candidatos_df_recomendados(df_pool: pd.DataFrame) -> pd.DataFrame:
    """
    Subconjunto recomendado por maior lucro previsto entre unidades compatíveis.
    Se nenhuma for compatível, devolve a(s) unidade(s) com menor Valor de Venda
    (na UI o badge fica MENOR PREÇO).
    Espera colunas calculadas:
    - Unidade_Compativel
    - Lucro_Recomendacao
    """
    if df_pool.empty:
        return pd.DataFrame()
    if "Unidade_Compativel" not in df_pool.columns or "Lucro_Recomendacao" not in df_pool.columns:
        return pd.DataFrame()
    fit_sub = df_pool[df_pool["Unidade_Compativel"] == True].copy()
    if fit_sub.empty:
        if "Valor de Venda" not in df_pool.columns:
            return pd.DataFrame()
        pool_pos = df_pool.copy()
        pool_pos["Valor de Venda"] = pd.to_numeric(pool_pos["Valor de Venda"], errors="coerce").fillna(0.0)
        pool_pos = pool_pos[pool_pos["Valor de Venda"] > 0].copy()
        if pool_pos.empty:
            return pd.DataFrame()
        min_v = pool_pos["Valor de Venda"].min()
        rec = pool_pos[pool_pos["Valor de Venda"] == min_v].copy()
        rec["Lucro_Recomendacao"] = rec["Valor de Venda"] * 0.019
        rec["Unidade_Compativel"] = False
        return rec
    fit_sub["Lucro_Recomendacao"] = pd.to_numeric(fit_sub["Lucro_Recomendacao"], errors="coerce").fillna(-1e18)
    max_l = fit_sub["Lucro_Recomendacao"].max()
    return fit_sub[fit_sub["Lucro_Recomendacao"] == max_l]


def ids_unidades_recomendadas_empreendimento(
    df_estoque: pd.DataFrame,
    nome_empreendimento: str,
    d: dict,
    df_politicas: pd.DataFrame,
    prem: dict,
) -> set[str]:
    """Identificadores recomendados (normalizados em str) - mesma regra dos cards por empreendimento."""
    sub = df_estoque[df_estoque["Empreendimento"] == nome_empreendimento].copy()
    if sub.empty or "Identificador" not in sub.columns:
        return set()
    sub = df_estoque_com_poder_compra(sub, d, df_politicas, prem)
    cand = candidatos_df_recomendados(sub)
    if cand.empty:
        return set()
    return {str(x).strip() for x in cand["Identificador"].unique() if x is not None and str(x).strip() != ""}


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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@400;600;700;800;900&display=swap');
        /* Barra superior: alterna azul ↔ vermelho marca, sempre opaca (sem “esvair”) */
        @keyframes fichaBarBrandOscillate {{
            0%, 100% {{ background-color: {COR_AZUL_ESC}; }}
            50% {{ background-color: {COR_VERMELHO}; }}
        }}
        /* Entrada do cartão principal (só opacity: transform no ancestor prende position:fixed do <dialog> das campanhas) */
        @keyframes fichaFadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        /* Entradas suaves (só sem prefers-reduced-motion) */
        @keyframes dvFadeRise {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes dvModalShell {{
            from {{ opacity: 0; transform: scale(0.97) translateY(12px); }}
            to {{ opacity: 1; transform: scale(1) translateY(0); }}
        }}
        /* Tokens de design (UI contemporânea; usados em sombras, raios e transições) */
        :root {{
            --dv-ease-out: cubic-bezier(0.22, 1, 0.36, 1);
            --dv-ease-spring: cubic-bezier(0.34, 1.2, 0.64, 1);
            --dv-duration: 0.22s;
            --dv-duration-slow: 0.45s;
            --dv-radius-sm: 10px;
            --dv-input-radius: 10px;
            --dv-input-height: 48px;
            /* Igual ao padding horizontal do .block-container (alertas em largura total) */
            --dv-block-pad-x: clamp(1.1rem, 2.8vw, 2.25rem);
            --dv-radius-md: 14px;
            --dv-radius-lg: 18px;
            --dv-radius-xl: 22px;
            --dv-shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.04);
            --dv-shadow-sm: 0 4px 20px -8px rgba(15, 23, 42, 0.07), 0 2px 10px -4px rgba(15, 23, 42, 0.04);
            --dv-shadow-md: 0 16px 48px -12px rgba(15, 23, 42, 0.12), 0 8px 20px -8px rgba(15, 23, 42, 0.06);
            --dv-shadow-glow: 0 0 0 1px rgba({RGB_AZUL_CSS}, 0.06), 0 8px 32px -8px rgba({RGB_AZUL_CSS}, 0.12);
            --dv-surface-glass: rgba(255, 255, 255, 0.82);
            --dv-surface-glass-strong: rgba(255, 255, 255, 0.94);
            /* Tipografia unificada: um tamanho para todos os títulos, outro para corpo / apoio */
            --dv-title-font-size: clamp(1.12rem, 2vw, 1.28rem);
            /* Título principal do cabeçalho (Simulador imobiliário DV) */
            --dv-hero-title-font-size: clamp(1.72rem, 4.75vw, 2.62rem);
            /* Espaçamento entre blocos/campos (responsivo: mais ar no telemóvel e no ecrã largo) */
            --dv-stack-gap: clamp(1.22rem, 0.92rem + 2.1vw, 1.9rem);
            --dv-body-font-size: 1rem;
        }}
        @media (prefers-reduced-motion: no-preference) {{
            html {{
                scroll-behavior: smooth;
            }}
        }}
        ::selection {{
            background: rgba({RGB_AZUL_CSS}, 0.22) !important;
            color: #0f172a !important;
        }}
        html {{
            color-scheme: light only !important;
        }}
        html, body, :root, [data-testid="stApp"], [data-testid="stAppViewContainer"] {{
            color-scheme: light only !important;
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
        /*
         * Rerun / cálculos longos: o Streamlit aplica STALE_STYLES (opacity ~0.33 + transição)
         * em cada wrapper [data-testid="stElementContainer"] - a UI parece “lavada”.
         * Mantemos opacidade total para leitura e percepção estável durante o rerun.
         */
        [data-testid="stElementContainer"] {{
            opacity: 1 !important;
            transition: none !important;
        }}
        /* Sidebar oculta (navegação/galeria/histórico removidos da UI) */
        section[data-testid="stSidebar"] {{ display: none !important; }}
        [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
        div[data-testid="collapsedControl"] {{ display: none !important; }}

        html, body {{
            font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
            font-feature-settings: 'kern' 1, 'liga' 1;
            font-optical-sizing: auto;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            color: {COR_TEXTO_LABEL};
            background: transparent !important;
            background-color: transparent !important;
        }}
        /* Fundo estilo Ficha Credenciamento Vendas RJ: degradê diagonal marca + foto */
        .stApp,
        [data-testid="stApp"] {{
            background-color: transparent !important;
            background-image: linear-gradient(
                    135deg,
                    rgba({RGB_AZUL_CSS}, 0.82) 0%,
                    rgba(30, 58, 95, 0.55) 38%,
                    rgba({RGB_VERMELHO_CSS}, 0.22) 72%,
                    rgba(15, 23, 42, 0.45) 100%
                ),
                url("{bg_url}") !important;
            background-size: auto, cover !important;
            background-position: center, center center !important;
            background-attachment: scroll, scroll !important;
            background-repeat: no-repeat, no-repeat !important;
            animation: none !important;
        }}
        /* SO em dark: mantém UI clara (inputs, texto, popovers Base Web) */
        @media (prefers-color-scheme: dark) {{
            html, body, :root, [data-testid="stApp"], [data-testid="stAppViewContainer"] {{
                color-scheme: light only !important;
            }}
            [data-testid="stAppViewContainer"],
            section.main,
            [data-testid="stMain"] {{
                color: {COR_TEXTO_LABEL} !important;
            }}
            p, span, label, li,
            [data-testid="stWidgetLabel"] label,
            [data-testid="stWidgetLabel"] p,
            div[data-testid="stMarkdownContainer"],
            div[data-testid="stMarkdownContainer"] * {{
                color: inherit;
            }}
            div[data-testid="stMarkdown"] p {{
                color: #334155 !important;
                -webkit-text-fill-color: #334155 !important;
            }}
            .stTextInput input, .stNumberInput input, .stDateInput input, textarea,
            div[data-baseweb="input"] input {{
                background-color: {COR_INPUT_BG} !important;
                color: {COR_INPUT_TEXTO} !important;
                -webkit-text-fill-color: {COR_INPUT_TEXTO} !important;
            }}
            div[data-baseweb="select"] > div,
            div[data-testid="stDateInput"] > div {{
                background-color: {COR_INPUT_BG} !important;
                color: {COR_INPUT_TEXTO} !important;
            }}
            ul[role="listbox"], div[data-baseweb="popover"] {{
                background: #ffffff !important;
                color: #1e293b !important;
            }}
            [data-testid="stExpander"] details {{
                background: rgba(255, 255, 255, 0.96) !important;
            }}
        }}
        /* Mobile: fundo fixo custa desempenho; colunas empilham */
        @media (max-width: 768px) {{
            .stApp,
            [data-testid="stApp"] {{
                background-attachment: scroll, scroll !important;
            }}
            [data-testid="stMain"] {{
                padding-left: max(clamp(10px, 4vw, 28px), env(safe-area-inset-left, 0px)) !important;
                padding-right: max(clamp(10px, 4vw, 28px), env(safe-area-inset-right, 0px)) !important;
                padding-top: max(clamp(8px, 2.5vh, 24px), env(safe-area-inset-top, 0px)) !important;
                padding-bottom: max(clamp(10px, 3vh, 28px), env(safe-area-inset-bottom, 0px)) !important;
            }}
            .block-container {{
                max-width: 100% !important;
                width: 100% !important;
                --dv-stack-gap: clamp(1.28rem, 0.88rem + 2.8vw, 1.72rem) !important;
                padding: max(6px, env(safe-area-inset-top, 0px)) clamp(0.75rem, 3.5vw, 1.15rem) clamp(1.2rem, 0.85rem + 2.2vw, 1.65rem) clamp(0.75rem, 3.5vw, 1.15rem) !important;
                margin-left: auto !important;
                margin-right: auto !important;
                margin-top: clamp(4px, 1.5vw, 10px) !important;
                margin-bottom: clamp(4px, 1.5vw, 10px) !important;
                border-radius: 20px !important;
                background: rgba(255, 255, 255, 0.82) !important;
                border: 1px solid rgba(255, 255, 255, 0.5) !important;
                box-shadow:
                    0 4px 6px -1px rgba({RGB_AZUL_CSS}, 0.05),
                    0 16px 36px -10px rgba({RGB_AZUL_CSS}, 0.14),
                    inset 0 1px 0 rgba(255, 255, 255, 0.5) !important;
                backdrop-filter: blur(14px) saturate(1.1) !important;
                -webkit-backdrop-filter: blur(14px) saturate(1.1) !important;
            }}
            .header-brand-bar-wrap {{
                width: 100%;
                max-width: 100%;
                margin-left: 0;
                margin-right: 0;
                margin-bottom: var(--dv-stack-gap);
            }}
            .scrolling-wrapper .card-item {{
                width: min(300px, 88vw);
            }}
            .summary-body {{
                padding: 1.25rem clamp(0.75rem, 4vw, 1.25rem) !important;
            }}
            .stButton button {{
                min-height: var(--dv-input-height) !important;
                height: var(--dv-input-height) !important;
                padding: 0 14px !important;
                touch-action: manipulation;
            }}
        }}
        @media (max-width: 420px) {{
            .block-container {{
                padding: 0.7rem 0.5rem !important;
            }}
            .header-logo-wrap img {{
                max-height: 58px;
            }}
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
            border-top: none !important;
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
            border-bottom: none !important;
            box-shadow: none !important;
            color: rgba(255, 255, 255, 0.92) !important;
        }}
        [data-testid="stToolbar"] button,
        [data-testid="stToolbar"] a,
        [data-testid="stToolbar"] [data-testid] {{
            color: rgba(255, 255, 255, 0.92) !important;
            background: transparent !important;
            background-color: transparent !important;
        }}
        [data-testid="stHeader"] button,
        [data-testid="stHeader"] a {{
            color: rgba(255, 255, 255, 0.92) !important;
            background: transparent !important;
            background-color: transparent !important;
        }}
        [data-testid="stToolbar"] svg,
        [data-testid="stHeader"] svg {{
            fill: currentColor !important;
            color: inherit !important;
        }}
        [data-testid="stToolbar"] svg path[stroke],
        [data-testid="stHeader"] svg path[stroke] {{
            stroke: currentColor !important;
        }}
        [data-testid="stToolbar"] button:hover,
        [data-testid="stToolbar"] a:hover,
        [data-testid="stHeader"] button:hover {{
            background: rgba(255, 255, 255, 0.12) !important;
        }}
        [data-testid="stMain"] {{
            padding-left: max(clamp(14px, 5vw, 56px), env(safe-area-inset-left, 0px)) !important;
            padding-right: max(clamp(14px, 5vw, 56px), env(safe-area-inset-right, 0px)) !important;
            padding-top: max(clamp(12px, 3.5vh, 40px), env(safe-area-inset-top, 0px)) !important;
            padding-bottom: max(clamp(14px, 4vh, 44px), env(safe-area-inset-bottom, 0px)) !important;
            box-sizing: border-box !important;
        }}
        section.main > div {{
            padding-top: 0 !important;
            padding-bottom: clamp(0.65rem, 0.5rem + 0.8vw, 1.1rem) !important;
        }}

        @media (prefers-reduced-motion: no-preference) {{
            .header-container {{
                animation: dvFadeRise var(--dv-duration-slow) var(--dv-ease-out) both;
            }}
            .home-banners-wrap {{
                animation: dvFadeRise calc(var(--dv-duration-slow) + 0.1s) var(--dv-ease-out) 0.12s both;
            }}
        }}

        /* Espaçamento fixo entre cada conteúdo (blocos / campos) */
        .block-container [data-testid="stVerticalBlock"] {{
            display: flex !important;
            flex-direction: column !important;
            gap: var(--dv-stack-gap) !important;
            row-gap: var(--dv-stack-gap) !important;
            column-gap: var(--dv-stack-gap) !important;
            align-items: stretch !important;
        }}
        .block-container [data-testid="column"] [data-testid="stVerticalBlock"] {{
            display: flex !important;
            flex-direction: column !important;
            gap: var(--dv-stack-gap) !important;
            row-gap: var(--dv-stack-gap) !important;
            align-items: stretch !important;
        }}
        .block-container [data-testid="stVerticalBlock"] [data-testid="stVerticalBlock"] {{
            gap: var(--dv-stack-gap) !important;
            row-gap: var(--dv-stack-gap) !important;
        }}
        /* Evita somar margem do Streamlit ao gap do bloco vertical */
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] {{
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }}
        /* Sem margem extra dentro do markdown (o gap entre stElementContainer já define o ritmo) */
        .block-container [data-testid="stMarkdownContainer"] p,
        .block-container [data-testid="stMarkdownContainer"] h1,
        .block-container [data-testid="stMarkdownContainer"] h2,
        .block-container [data-testid="stMarkdownContainer"] h3,
        .block-container [data-testid="stMarkdownContainer"] h4,
        .block-container [data-testid="stMarkdownContainer"] h5,
        .block-container [data-testid="stMarkdownContainer"] h6 {{
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }}
        .block-container .dv-titulo-secao {{
            margin-top: 0 !important;
            margin-bottom: var(--dv-stack-gap) !important;
        }}
        .block-container [data-testid="stWidgetLabel"] {{
            margin-top: 0 !important;
            margin-bottom: 0.32rem !important;
        }}
        .block-container [data-testid="stWidgetLabel"] label,
        .block-container [data-testid="stWidgetLabel"] p {{
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            line-height: 1.35 !important;
            text-align: left !important;
        }}
        .block-container [data-testid="stElementContainer"] [data-baseweb="form-control-container"] {{
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }}
        /*
         * Injeção no topo (st.html do tema + st.iframe de scripts): o gap do flex soma faixa vazia.
         * margin-bottom negativo nos dois primeiros anula o gap até ao 3.º; o 3.º mantém distância ao cabeçalho.
         */
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(1) {{
            margin-top: 0 !important;
        }}
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+2) {{
            margin-bottom: calc(-1 * var(--dv-stack-gap)) !important;
        }}
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+3) {{
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            min-height: 0 !important;
        }}
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+3) > div {{
            min-height: 0 !important;
        }}
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+3) [data-testid="stHtml"],
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+3) [data-testid="stIFrame"] {{
            display: block !important;
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
            overflow: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 0 !important;
            border: 0 !important;
            box-shadow: none !important;
        }}
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+3) [data-testid="stIFrame"] iframe,
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+3) iframe {{
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
            border: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            display: block !important;
        }}
        /*
         * Colunas (st.columns): o mesmo seletor acima atingiria o stVerticalBlock interno e
         * anulava o gap entre os 2–3 primeiros widgets (ex.: Ato 30/60 + refs Pro Soluto).
         * Manter --dv-stack-gap só no fluxo principal; dentro de colunas, sem margem negativa.
         */
        .block-container [data-testid="column"] [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+2) {{
            margin-bottom: 0 !important;
        }}
        .block-container [data-testid="column"] [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+3) {{
            padding-top: revert !important;
            padding-bottom: revert !important;
            min-height: revert !important;
        }}
        .block-container [data-testid="column"] [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+3) > div {{
            min-height: revert !important;
        }}
        .block-container [data-testid="stMarkdownContainer"]:has(.header-container) {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}
        /* Um campo por linha: st.columns vira coluna única (valor + referência logo abaixo no mesmo “bloco”). */
        .block-container [data-testid="stHorizontalBlock"] {{
            display: flex !important;
            flex-direction: column !important;
            align-items: stretch !important;
            gap: var(--dv-stack-gap) !important;
            width: 100% !important;
            max-width: 100% !important;
        }}
        .block-container [data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
            width: 100% !important;
            min-width: 0 !important;
            flex: 1 1 auto !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            box-sizing: border-box !important;
        }}
        /* Wrapper interno da coluna (Streamlit): mesma largura útil que os campos fora de st.columns */
        .block-container [data-testid="stHorizontalBlock"] > div[data-testid="column"] > div {{
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            box-sizing: border-box !important;
        }}
        .block-container [data-testid="stHorizontalBlock"] [data-testid="column"] [data-testid="stVerticalBlock"] {{
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            box-sizing: border-box !important;
        }}
        .block-container [data-testid="stHorizontalBlock"] [data-testid="column"] [data-testid="stElementContainer"] {{
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            max-width: 100% !important;
        }}
        /* "Avançar para Resumo": contentores do <hr> sem margem extra (ritmo vem do hr + margens no .st-key-dv_btn_avancar_resumo) */
        .block-container div[data-testid="stElementContainer"]:has(hr.dv-avancar-rule) {{
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }}
        .block-container hr.dv-avancar-rule {{
            border: none !important;
            height: 1px !important;
            margin: 0 !important;
            background: linear-gradient(
                90deg,
                transparent 0%,
                rgba(148, 163, 184, 0.45) 50%,
                transparent 100%
            ) !important;
        }}
        /* Referência imediatamente após o campo (compensa row-gap do bloco vertical) */
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(
                [data-testid="stTextInput"],
                [data-testid="stNumberInput"],
                [data-testid="stDateInput"],
                [data-testid="stSelectbox"],
                [data-testid="stMultiSelect"],
                [data-testid="stTextArea"]
            ) + div[data-testid="stElementContainer"]:has(
                [data-testid="stMarkdownContainer"] .inline-ref,
                [data-testid="stMarkdownContainer"] .dv-campo-resumo-movel,
                [data-testid="stMarkdownContainer"] .inline-ref-vcx-linhas,
                [data-testid="stMarkdownContainer"] .dv-ref-prox-campo,
                [data-testid="stMarkdownContainer"] .dv-sug-min-ato
            ),
        .block-container [data-testid="column"] [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(
                [data-testid="stTextInput"],
                [data-testid="stNumberInput"],
                [data-testid="stDateInput"],
                [data-testid="stSelectbox"],
                [data-testid="stMultiSelect"],
                [data-testid="stTextArea"]
            ) + div[data-testid="stElementContainer"]:has(
                [data-testid="stMarkdownContainer"] .inline-ref,
                [data-testid="stMarkdownContainer"] .dv-campo-resumo-movel,
                [data-testid="stMarkdownContainer"] .inline-ref-vcx-linhas,
                [data-testid="stMarkdownContainer"] .dv-ref-prox-campo,
                [data-testid="stMarkdownContainer"] .dv-sug-min-ato
            ) {{
            margin-top: calc(var(--dv-ref-after-gap) - var(--dv-stack-gap)) !important;
        }}
        .block-container [data-testid="stElementContainer"]:has([data-testid="stHorizontalBlock"])
            + div[data-testid="stElementContainer"]:has(
                [data-testid="stMarkdownContainer"] .inline-ref,
                [data-testid="stMarkdownContainer"] .dv-campo-resumo-movel,
                [data-testid="stMarkdownContainer"] .dv-ref-prox-campo,
                [data-testid="stMarkdownContainer"] .dv-sug-min-ato
            ) {{
            margin-top: calc(var(--dv-ref-after-gap) - var(--dv-stack-gap)) !important;
        }}
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(
                [data-testid="stMarkdownContainer"] .dv-campo-resumo-movel
            ) + div[data-testid="stElementContainer"]:has(
                [data-testid="stMarkdownContainer"] .inline-ref
            ) {{
            margin-top: calc(var(--dv-ref-chain-gap) - var(--dv-stack-gap)) !important;
        }}
        .dv-ref-prox-campo {{
            margin: 0 !important;
            padding: 0 !important;
            text-align: center !important;
            line-height: 1.45 !important;
            color: #111111 !important;
        }}
        .block-container div[data-testid="stMarkdownContainer"] hr,
        .block-container hr {{
            margin: var(--dv-stack-gap) 0 !important;
            border: none !important;
            height: 1px !important;
            background: linear-gradient(
                90deg,
                transparent 0%,
                rgba(148, 163, 184, 0.45) 50%,
                transparent 100%
            ) !important;
        }}
        /* dv-avancar: a regra genérica .block-container hr acima vinha depois e anulava margin:0 — faixa dupla / “terceira linha” */
        .block-container div[data-testid="stMarkdownContainer"] hr.dv-avancar-rule,
        .block-container hr.dv-avancar-rule {{
            margin: 0 !important;
            height: 1px !important;
            border: none !important;
            background: linear-gradient(
                90deg,
                transparent 0%,
                rgba(148, 163, 184, 0.45) 50%,
                transparent 100%
            ) !important;
        }}
        /* Espaço igual entre <hr> superior, botão e <hr> inferior (sem linha extra colada ao botão) */
        .block-container .st-key-dv_btn_avancar_resumo {{
            margin-top: clamp(0.85rem, 2.8vw, 1.4rem) !important;
            margin-bottom: clamp(0.85rem, 2.8vw, 1.4rem) !important;
        }}

        /*
         * Recomendação de unidades: scroll no wrapper externo.
         * Antes o overflow estava no .scrolling-wrapper com max-width:100% — em cadeia flex (Streamlit)
         * o min-width:auto do content impedia overflow real e o arrasto horizontal no telemóvel falhava.
         */
        .block-container [data-testid="stElementContainer"]:has(.recommendation-cards-outer),
        .block-container div[data-testid="stMarkdownContainer"]:has(.recommendation-cards-outer) {{
            min-width: 0 !important;
            max-width: 100% !important;
            overflow-x: visible !important;
        }}
        .recommendation-cards-outer {{
            display: block;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
            overflow-x: auto;
            overflow-y: hidden;
            -webkit-overflow-scrolling: touch;
            overscroll-behavior-x: contain;
            touch-action: pan-x pan-y;
            scroll-behavior: smooth;
            scrollbar-width: thin;
            scrollbar-color: rgba({RGB_AZUL_CSS}, 0.5) rgba(148, 163, 184, 0.22);
            scrollbar-gutter: stable;
            padding: 0 2px 4px 2px;
        }}
        .recommendation-cards-outer .scrolling-wrapper {{
            display: flex;
            flex-direction: row;
            flex-wrap: nowrap;
            gap: 20px;
            width: max-content;
            max-width: none;
            min-width: min-content;
            overflow: visible;
            margin: 0 auto 12px auto;
            padding-bottom: 14px;
            box-sizing: border-box;
        }}
        .recommendation-cards-outer::-webkit-scrollbar {{
            height: 10px !important;
            -webkit-appearance: none;
            appearance: none;
            background: rgba(148, 163, 184, 0.22);
            border-radius: 99px;
        }}
        .recommendation-cards-outer::-webkit-scrollbar-track {{
            background: rgba(148, 163, 184, 0.2);
            border-radius: 99px;
        }}
        .recommendation-cards-outer::-webkit-scrollbar-thumb {{
            background: linear-gradient(90deg, rgba({RGB_AZUL_CSS}, 0.35), rgba({RGB_VERMELHO_CSS}, 0.42));
            border-radius: 99px;
        }}

        .scrolling-wrapper .card-item {{
            flex: 0 0 auto;
            width: 300px;
            transition: transform var(--dv-duration) var(--dv-ease-out),
                filter var(--dv-duration) var(--dv-ease-out);
        }}
        @media (hover: hover) and (prefers-reduced-motion: no-preference) {{
            .scrolling-wrapper .card-item:hover {{
                transform: translateY(-6px);
                filter: drop-shadow(0 14px 28px rgba(15, 23, 42, 0.14));
            }}
            .scrolling-wrapper .recommendation-card:hover {{
                transform: none !important;
                box-shadow: var(--dv-shadow-md) !important;
            }}
        }}

        h1, h2, h3, h4, h5, h6,
        .dv-titulo-secao,
        .home-banners-section-title {{
            font-family: 'Montserrat', 'Inter', sans-serif !important;
            font-size: var(--dv-title-font-size) !important;
            text-align: center !important;
            color: {COR_AZUL_ESC} !important;
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1.28;
        }}
        .header-title {{
            font-family: 'Montserrat', 'Inter', sans-serif !important;
            font-size: var(--dv-hero-title-font-size) !important;
            font-weight: 800 !important;
            text-transform: none !important;
            letter-spacing: -0.03em !important;
            line-height: 1.15 !important;
            text-wrap: balance;
        }}

        .stMarkdown p, .stText, label, .stSelectbox label, .stTextInput label, .stNumberInput label {{
            color: {COR_TEXTO_LABEL} !important;
            font-size: var(--dv-body-font-size) !important;
        }}
        [data-testid="stWidgetLabel"] label,
        [data-testid="stWidgetLabel"] p {{
            color: {COR_TEXTO_LABEL} !important;
            font-size: var(--dv-body-font-size) !important;
        }}
        /* Corpo: mesmo tamanho em markdown, alertas e texto de apoio */
        div[data-testid="stMarkdown"] p,
        div[data-testid="stMarkdownContainer"] p,
        .block-container .custom-alert,
        .block-container .dv-alert-direcional-inner,
        .block-container .summary-body,
        .block-container .summary-body b {{
            font-size: var(--dv-body-font-size) !important;
        }}
        /* Textos de apoio no cartão: centralizados (rótulos de widgets mantêm-se à esquerda) */
        .block-container div[data-testid="stMarkdown"] p,
        .block-container div[data-testid="stMarkdownContainer"] p {{
            color: #000000;
            line-height: 1.58;
            text-align: center !important;
            text-wrap: pretty;
        }}
        .block-container div[data-testid="stMarkdownContainer"] p.inline-ref,
        .block-container div[data-testid="stMarkdownContainer"] .inline-ref {{
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            opacity: 1 !important;
        }}
        h1, h2, h3, .home-banners-section-title, .dv-titulo-secao {{
            text-wrap: balance;
        }}

        /* Cartão de vidro - mesma linguagem da Ficha Credenciamento (max-width largo para o simulador) */
        .block-container {{
            --dv-rhythm: clamp(1.32rem, 1.15rem + 0.65vw, 1.55rem);
            --dv-stack-gap: clamp(1.26rem, 0.95rem + 2vw, 1.95rem);
            --dv-block-pad-x: clamp(1.1rem, 2.8vw, 2.25rem);
            --dv-ref-after-gap: 0.28rem;
            --dv-ref-chain-gap: 0.16rem;
            text-rendering: optimizeLegibility;
            max-width: min(1680px, 100%) !important;
            margin-left: auto !important;
            margin-right: auto !important;
            margin-top: clamp(4px, 1vh, 14px) !important;
            margin-bottom: clamp(4px, 1vh, 14px) !important;
            padding: max(6px, env(safe-area-inset-top, 0px)) var(--dv-block-pad-x) clamp(1.45rem, 1.1rem + 1.8vw, 2rem) var(--dv-block-pad-x) !important;
            background: rgba(255, 255, 255, 0.78) !important;
            backdrop-filter: blur(18px) saturate(1.15) !important;
            -webkit-backdrop-filter: blur(18px) saturate(1.15) !important;
            border-radius: 24px !important;
            border: 1px solid rgba(255, 255, 255, 0.45) !important;
            box-shadow:
                0 4px 6px -1px rgba({RGB_AZUL_CSS}, 0.06),
                0 24px 48px -12px rgba({RGB_AZUL_CSS}, 0.18),
                inset 0 1px 0 rgba(255, 255, 255, 0.55) !important;
        }}
        @media (prefers-reduced-motion: no-preference) {{
            .block-container {{
                animation: fichaFadeIn 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
            }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            .block-container {{
                animation: none !important;
            }}
        }}
        html[data-dv-reduced-motion="1"] .block-container {{
            animation: none !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 16px !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}

        /* Títulos em markdown: margens (tamanho = regra global h1–h6 / .dv-titulo-secao) */
        .stMarkdown h1 {{ text-align: center !important; margin: 0 !important; font-weight: 800 !important; color: {COR_AZUL_ESC} !important; }}
        .stMarkdown h1.header-title {{
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            line-height: 1.15 !important;
            font-size: var(--dv-hero-title-font-size) !important;
            text-transform: none !important;
            letter-spacing: -0.03em !important;
        }}
        .stMarkdown h2 {{ text-align: center !important; margin: 0 !important; color: {COR_AZUL_ESC} !important; }}
        .stMarkdown h3 {{ text-align: center !important; margin: 0 !important; color: {COR_AZUL_ESC} !important; }}
        .stMarkdown h4 {{ text-align: center !important; margin: 0 !important; color: {COR_AZUL_ESC} !important; }}
        .stMarkdown h5, .stMarkdown h6,
        [data-testid="stMarkdownContainer"] h5,
        [data-testid="stMarkdownContainer"] h6 {{
            display: none !important;
        }}
        .dv-titulo-secao {{
            margin: 0 !important;
            color: {COR_AZUL_ESC} !important;
        }}
        /* Sem subtítulos Streamlit (st.caption) em toda a app */
        [data-testid="stCaption"] {{
            display: none !important;
            height: 0 !important;
            max-height: 0 !important;
            overflow: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }}

        /* Largura total da coluna para todos os widgets editáveis */
        [data-testid="stTextInput"],
        [data-testid="stNumberInput"],
        [data-testid="stDateInput"],
        [data-testid="stSelectbox"],
        [data-testid="stMultiSelect"],
        [data-testid="stTextArea"] {{
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }}

        div[data-baseweb="input"] {{
            border-radius: var(--dv-input-radius) !important;
            border: 1px solid #e2e8f0 !important;
            background-color: {COR_INPUT_BG} !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            transition: border-color var(--dv-duration) var(--dv-ease-out),
                box-shadow var(--dv-duration) var(--dv-ease-out),
                background-color var(--dv-duration) var(--dv-ease-out) !important;
        }}

        div[data-baseweb="input"]:focus-within {{
            border-color: rgba({RGB_AZUL_CSS}, 0.35) !important;
            box-shadow: 0 0 0 3px rgba({RGB_AZUL_CSS}, 0.08) !important;
            background-color: {COR_INPUT_BG} !important;
        }}

        div[data-baseweb="select"] {{
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            border-radius: var(--dv-input-radius) !important;
        }}

        /* Esconder botões + e - dos number inputs (apenas digitação) */
        div[data-testid="stNumberInput"] button {{
            display: none !important;
        }}
        div[data-testid="stNumberInput"] div[data-baseweb="input"],
        div[data-testid="stTextInput"] div[data-baseweb="input"],
        div[data-testid="stDateInput"] div[data-baseweb="input"],
        div[data-baseweb="select"] {{
            background-color: {COR_INPUT_BG} !important;
        }}

        /* --- Altura 48px: texto, número, data (select/picklist tem regras à parte — várias linhas) --- */
        .stTextInput input, .stNumberInput input, .stDateInput input {{
            height: var(--dv-input-height) !important;
            min-height: var(--dv-input-height) !important;
            padding: 0 15px !important;
            color: {COR_INPUT_TEXTO} !important;
            -webkit-text-fill-color: {COR_INPUT_TEXTO} !important;
            font-size: var(--dv-body-font-size) !important;
            line-height: var(--dv-input-height) !important;
            text-align: left !important;
            display: flex !important;
            align-items: center !important;
            background-color: {COR_INPUT_BG} !important;
        }}
        .stTextInput input::placeholder,
        .stNumberInput input::placeholder,
        .stDateInput input::placeholder,
        .stTextArea textarea::placeholder,
        div[data-baseweb="input"] input::placeholder {{
            color: #6b7280 !important;
            opacity: 0.52 !important;
            -webkit-text-fill-color: #6b7280 !important;
        }}
        .stTextInput input::-webkit-input-placeholder,
        .stNumberInput input::-webkit-input-placeholder,
        .stDateInput input::-webkit-input-placeholder,
        .stTextArea textarea::-webkit-input-placeholder,
        div[data-baseweb="input"] input::-webkit-input-placeholder {{
            color: #6b7280 !important;
            opacity: 0.52 !important;
        }}
        div[data-testid="stNumberInput"] div[data-baseweb="input"],
        div[data-testid="stTextInput"] div[data-baseweb="input"] {{
            height: var(--dv-input-height) !important;
            min-height: var(--dv-input-height) !important;
            display: flex !important;
            align-items: center !important;
        }}

        div[data-testid="stDateInput"] > div {{
            background-color: {COR_INPUT_BG} !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: var(--dv-input-radius) !important;
            display: flex;
            align-items: center;
            min-height: var(--dv-input-height) !important;
            height: var(--dv-input-height) !important;
            box-sizing: border-box !important;
        }}

        /*
         * Picklists (Base Web): desktop = uma linha + ellipsis; só em larguras finas (max 768px)
         * quebra no valor fechado e nas opções. Regras em divs descendentes sobrepõem nowrap interno.
         * Setinha: coluna fixa à direita (largura constante) com o SVG centrado nessa faixa (horizontal + vertical).
         */
        @media (min-width: 769px) {{
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{
                background-color: {COR_INPUT_BG} !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: var(--dv-input-radius) !important;
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                gap: 8px !important;
                min-height: var(--dv-input-height) !important;
                height: var(--dv-input-height) !important;
                max-height: var(--dv-input-height) !important;
                padding: 0 12px !important;
                box-sizing: border-box !important;
                overflow: hidden !important;
            }}
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div:first-of-type,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div:first-of-type {{
                display: flex !important;
                align-items: center !important;
                align-self: center !important;
                min-width: 0 !important;
            }}
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div,
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > p,
            [data-testid="stSelectbox"] div[data-baseweb="select"] span,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > p,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] span {{
                text-align: left !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
                word-break: normal !important;
                overflow-wrap: normal !important;
                line-height: 1.38 !important;
                color: {COR_INPUT_TEXTO} !important;
                -webkit-text-fill-color: {COR_INPUT_TEXTO} !important;
                display: block !important;
                flex: 1 1 auto !important;
                min-width: 0 !important;
            }}
            /* Não usar só :has(svg) — tags do multiselect têm ícones na primeira coluna. */
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div:not(:first-of-type):has(svg),
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div:not(:first-of-type):has(svg) {{
                display: flex !important;
                flex-direction: row !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 6px !important;
                flex: 0 0 auto !important;
                width: auto !important;
                min-width: 2.375rem !important;
                max-width: none !important;
                box-sizing: border-box !important;
                flex-shrink: 0 !important;
                align-self: stretch !important;
                padding: 0 !important;
                margin: 0 !important;
            }}
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div:not(:first-of-type):has(svg) svg,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div:not(:first-of-type):has(svg) svg {{
                flex-shrink: 0 !important;
                display: block !important;
                margin: 0 !important;
            }}
            /* Setinha sem wrapper (svg filho direto da linha do controlo): coluna fixa à direita */
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > svg:last-of-type,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > svg:last-of-type {{
                flex: 0 0 2.375rem !important;
                width: 2.375rem !important;
                min-width: 2.375rem !important;
                max-width: 2.375rem !important;
                box-sizing: border-box !important;
                margin-left: auto !important;
                margin-right: 0 !important;
                display: block !important;
                align-self: center !important;
                object-fit: contain !important;
            }}
            [data-testid="stSelectbox"] div[data-baseweb="select"] p,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] p {{
                text-align: left !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
                word-break: normal !important;
                overflow-wrap: normal !important;
                line-height: 1.38 !important;
                color: {COR_INPUT_TEXTO} !important;
                -webkit-text-fill-color: {COR_INPUT_TEXTO} !important;
                margin: 0 !important;
                min-width: 0 !important;
            }}
            div[data-baseweb="popover"] ul[role="listbox"] [role="option"],
            ul[role="listbox"] [role="option"] {{
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
                word-break: normal !important;
                overflow-wrap: normal !important;
                min-height: 2.5rem !important;
                line-height: 1.35 !important;
                align-items: center !important;
            }}
        }}
        @media (max-width: 768px) {{
            [data-testid="stSelectbox"] div[data-baseweb="select"],
            [data-testid="stMultiSelect"] div[data-baseweb="select"] {{
                overflow: visible !important;
                max-width: 100% !important;
            }}
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{
                background-color: {COR_INPUT_BG} !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: var(--dv-input-radius) !important;
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                gap: 8px !important;
                min-height: var(--dv-input-height) !important;
                height: auto !important;
                max-height: none !important;
                padding: 8px 12px !important;
                box-sizing: border-box !important;
                overflow: visible !important;
                max-width: 100% !important;
            }}
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div:first-of-type,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div:first-of-type {{
                display: flex !important;
                align-items: center !important;
                align-self: center !important;
                min-width: 0 !important;
            }}
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div,
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > p,
            [data-testid="stSelectbox"] div[data-baseweb="select"] span,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > p,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] span {{
                text-align: left !important;
                white-space: normal !important;
                word-break: break-word !important;
                overflow-wrap: anywhere !important;
                text-overflow: unset !important;
                overflow: visible !important;
                height: auto !important;
                max-height: none !important;
                line-height: 1.38 !important;
                color: {COR_INPUT_TEXTO} !important;
                -webkit-text-fill-color: {COR_INPUT_TEXTO} !important;
                display: block !important;
                flex: 1 1 auto !important;
                min-width: 0 !important;
                max-width: 100% !important;
                -webkit-line-clamp: unset !important;
            }}
            [data-testid="stSelectbox"] div[data-baseweb="select"] div,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] div {{
                white-space: normal !important;
                word-break: break-word !important;
                overflow-wrap: anywhere !important;
                overflow: visible !important;
                text-overflow: clip !important;
                max-width: 100% !important;
            }}
            [data-testid="stSelectbox"] div[data-baseweb="select"] p,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] p {{
                white-space: normal !important;
                word-break: break-word !important;
                overflow-wrap: anywhere !important;
                overflow: visible !important;
                text-overflow: unset !important;
                max-width: 100% !important;
                -webkit-line-clamp: unset !important;
                margin: 0 !important;
            }}
            /* Não usar só :has(svg) — tags do multiselect têm ícones na primeira coluna. */
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div:not(:first-of-type):has(svg),
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div:not(:first-of-type):has(svg) {{
                display: flex !important;
                flex-direction: row !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 6px !important;
                flex: 0 0 auto !important;
                width: auto !important;
                min-width: 2.375rem !important;
                max-width: none !important;
                box-sizing: border-box !important;
                flex-shrink: 0 !important;
                align-self: stretch !important;
                padding: 0 !important;
                margin: 0 !important;
            }}
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div:not(:first-of-type):has(svg) svg,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div:not(:first-of-type):has(svg) svg {{
                flex-shrink: 0 !important;
                display: block !important;
                margin: 0 !important;
            }}
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div > svg:last-of-type,
            [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > svg:last-of-type {{
                flex: 0 0 2.375rem !important;
                width: 2.375rem !important;
                min-width: 2.375rem !important;
                max-width: 2.375rem !important;
                box-sizing: border-box !important;
                margin-left: auto !important;
                margin-right: 0 !important;
                display: block !important;
                align-self: center !important;
                object-fit: contain !important;
            }}
            div[data-baseweb="popover"] ul[role="listbox"] [role="option"],
            ul[role="listbox"] [role="option"] {{
                white-space: normal !important;
                word-break: break-word !important;
                overflow-wrap: anywhere !important;
                text-overflow: unset !important;
                overflow: visible !important;
                height: auto !important;
                min-height: 2.5rem !important;
                line-height: 1.35 !important;
                align-items: center !important;
                -webkit-line-clamp: unset !important;
            }}
            div[data-baseweb="popover"] ul[role="listbox"] [role="option"] div,
            div[data-baseweb="popover"] ul[role="listbox"] [role="option"] span,
            div[data-baseweb="popover"] ul[role="listbox"] [role="option"] p,
            ul[role="listbox"] [role="option"] div,
            ul[role="listbox"] [role="option"] span,
            ul[role="listbox"] [role="option"] p {{
                white-space: normal !important;
                word-break: break-word !important;
                overflow-wrap: anywhere !important;
                overflow: visible !important;
                text-overflow: unset !important;
                -webkit-line-clamp: unset !important;
                max-width: 100% !important;
            }}
        }}

        div[data-testid="stDateInput"] div[data-baseweb="input"] {{
            border: none !important;
            background-color: transparent !important;
        }}

        /* Áreas de texto: mesma largura / raio; altura mínima alinhada à linha única */
        [data-testid="stTextArea"] textarea,
        .stTextArea textarea {{
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            min-height: var(--dv-input-height) !important;
            padding: 12px 15px !important;
            border-radius: var(--dv-input-radius) !important;
            border: 1px solid #e2e8f0 !important;
            background-color: {COR_INPUT_BG} !important;
            color: {COR_INPUT_TEXTO} !important;
            -webkit-text-fill-color: {COR_INPUT_TEXTO} !important;
            font-size: var(--dv-body-font-size) !important;
            line-height: 1.45 !important;
        }}
        [data-testid="stTextArea"] div[data-baseweb="textarea"],
        [data-testid="stTextArea"] div[data-baseweb="input"] {{
            border-radius: var(--dv-input-radius) !important;
            border: 1px solid #e2e8f0 !important;
            background-color: {COR_INPUT_BG} !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }}
        [data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within,
        [data-testid="stTextArea"] div[data-baseweb="input"]:focus-within {{
            border-color: rgba({RGB_AZUL_CSS}, 0.35) !important;
            box-shadow: 0 0 0 3px rgba({RGB_AZUL_CSS}, 0.08) !important;
        }}

        .stButton button {{
            font-family: 'Inter', system-ui, sans-serif;
            border-radius: var(--dv-radius-sm) !important;
            padding: 0 16px !important;
            width: 100% !important;
            min-height: var(--dv-input-height) !important;
            height: var(--dv-input-height) !important;
            font-weight: 600 !important;
            font-size: var(--dv-body-font-size) !important;
            transition: background-color var(--dv-duration) var(--dv-ease-out),
                border-color var(--dv-duration) var(--dv-ease-out),
                box-shadow var(--dv-duration) var(--dv-ease-out),
                transform 0.12s var(--dv-ease-out),
                color var(--dv-duration) var(--dv-ease-out) !important;
        }}
        @media (prefers-reduced-motion: no-preference) {{
            .stButton button:active {{
                transform: scale(0.987) !important;
            }}
        }}

        div[data-testid="column"] .stButton button, [data-testid="stSidebar"] .stButton button {{
             min-height: var(--dv-input-height) !important;
             height: var(--dv-input-height) !important;
             font-size: var(--dv-body-font-size) !important;
        }}

        /* Botões primários = gradiente vermelho (ficha Vendas RJ) */
        .stButton button[kind="primary"] {{
            background: linear-gradient(180deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%) !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            border: none !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 4px 20px -4px rgba({RGB_VERMELHO_CSS}, 0.42) !important;
        }}
        .stButton button[kind="primary"]:hover {{
            background: linear-gradient(180deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%) !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22),
                0 10px 28px -6px rgba({RGB_VERMELHO_CSS}, 0.48) !important;
        }}
        .stButton button[kind="primary"] *,
        .stButton button[kind="primary"] span,
        .stButton button[kind="primary"] p {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }}
        .stButton button[kind="primary"]:hover *,
        .stButton button[kind="primary"]:hover span,
        .stButton button[kind="primary"]:hover p {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }}
        .stButton button[kind="primary"] svg,
        .stButton button[kind="primary"]:hover svg {{
            fill: #ffffff !important;
            color: #ffffff !important;
        }}
        @media (hover: hover) and (prefers-reduced-motion: no-preference) {{
            .stButton button[kind="primary"]:hover {{
                transform: translateY(-2px) scale(1.01) !important;
            }}
            .stButton button:not([kind="primary"]):hover,
            .stDownloadButton button:hover {{
                transform: translateY(-1px) !important;
            }}
            a[data-testid="stLinkButton"][href*="whatsapp.com"]:hover,
            a[data-testid="stLinkButton"][href*="wa.me"]:hover,
            a[data-testid="stLinkButton"][href*="api.whatsapp.com"]:hover {{
                transform: translateY(-1px) !important;
            }}
            .block-container .stFormSubmitButton > button:hover,
            .block-container [data-testid="stFormSubmitButton"] > button:hover {{
                transform: translateY(-2px) scale(1.01) !important;
            }}
        }}

        /* st.form_submit_button: vermelho Direcional + texto branco (inclui variantes sem kind no DOM) */
        .block-container .stFormSubmitButton > button,
        .block-container [data-testid="stFormSubmitButton"] > button {{
            background: linear-gradient(180deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%) !important;
            background-color: {COR_VERMELHO} !important;
            background-image: linear-gradient(180deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%) !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            border: none !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 4px 20px -4px rgba({RGB_VERMELHO_CSS}, 0.42) !important;
            border-radius: var(--dv-radius-sm) !important;
            width: 100% !important;
            min-height: var(--dv-input-height) !important;
            height: var(--dv-input-height) !important;
            font-weight: 600 !important;
            font-size: var(--dv-body-font-size) !important;
            transition: background-color var(--dv-duration) var(--dv-ease-out),
                border-color var(--dv-duration) var(--dv-ease-out),
                box-shadow var(--dv-duration) var(--dv-ease-out),
                transform 0.12s var(--dv-ease-out),
                color var(--dv-duration) var(--dv-ease-out) !important;
        }}
        .block-container .stFormSubmitButton > button *,
        .block-container .stFormSubmitButton > button span,
        .block-container .stFormSubmitButton > button p,
        .block-container .stFormSubmitButton > button div,
        .block-container [data-testid="stFormSubmitButton"] > button *,
        .block-container [data-testid="stFormSubmitButton"] > button span,
        .block-container [data-testid="stFormSubmitButton"] > button p,
        .block-container [data-testid="stFormSubmitButton"] > button div {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }}
        .block-container .stFormSubmitButton > button:hover,
        .block-container [data-testid="stFormSubmitButton"] > button:hover {{
            background: linear-gradient(180deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%) !important;
            background-color: {COR_VERMELHO} !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22),
                0 10px 28px -6px rgba({RGB_VERMELHO_CSS}, 0.48) !important;
        }}
        .block-container .stFormSubmitButton > button:hover *,
        .block-container .stFormSubmitButton > button:hover span,
        .block-container .stFormSubmitButton > button:hover p,
        .block-container .stFormSubmitButton > button:hover div,
        .block-container [data-testid="stFormSubmitButton"] > button:hover *,
        .block-container [data-testid="stFormSubmitButton"] > button:hover span,
        .block-container [data-testid="stFormSubmitButton"] > button:hover p,
        .block-container [data-testid="stFormSubmitButton"] > button:hover div {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }}
        .block-container .stFormSubmitButton > button svg,
        .block-container .stFormSubmitButton > button:hover svg,
        .block-container [data-testid="stFormSubmitButton"] > button svg,
        .block-container [data-testid="stFormSubmitButton"] > button:hover svg {{
            fill: #ffffff !important;
            color: #ffffff !important;
        }}

        /* Botões secundários = branco, texto escuro (primários continuam vermelhos) */
        .stButton button:not([kind="primary"]) {{
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08) !important;
        }}
        .stButton button:not([kind="primary"]):hover {{
            background: #f1f5f9 !important;
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            border-color: #94a3b8 !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1) !important;
        }}
        .stButton button:not([kind="primary"]) *,
        .stButton button:not([kind="primary"]) span,
        .stButton button:not([kind="primary"]) p {{
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
        }}
        .stButton button:not([kind="primary"]) svg {{
            fill: #0f172a !important;
            color: #0f172a !important;
        }}
        /* Links WhatsApp em markdown (não são o botão link_button) */
        a[href*="whatsapp.com"]:not([data-testid="stLinkButton"]),
        a[href*="wa.me"]:not([data-testid="stLinkButton"]) {{
            color: #128c7e !important;
            font-weight: 600 !important;
            text-decoration: underline !important;
        }}
        a[href*="whatsapp.com"]:not([data-testid="stLinkButton"]):hover,
        a[href*="wa.me"]:not([data-testid="stLinkButton"]):hover {{
            color: #075e54 !important;
        }}
        /* Botão WhatsApp (link_button): mesmo padrão secundário - branco, texto escuro */
        a[data-testid="stLinkButton"][href*="api.whatsapp.com"],
        a[data-testid="stLinkButton"][href*="whatsapp.com"],
        a[data-testid="stLinkButton"][href*="wa.me"] {{
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            box-sizing: border-box !important;
            min-height: var(--dv-input-height) !important;
            height: var(--dv-input-height) !important;
            padding: 0 1rem !important;
            border-radius: var(--dv-radius-sm) !important;
            transition: background-color var(--dv-duration) var(--dv-ease-out),
                border-color var(--dv-duration) var(--dv-ease-out),
                box-shadow var(--dv-duration) var(--dv-ease-out),
                transform var(--dv-duration) var(--dv-ease-spring) !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
            background-image: none !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            font-weight: 700 !important;
            text-decoration: none !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08) !important;
        }}
        a[data-testid="stLinkButton"][href*="api.whatsapp.com"] *,
        a[data-testid="stLinkButton"][href*="whatsapp.com"] *,
        a[data-testid="stLinkButton"][href*="wa.me"] * {{
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
        }}
        a[data-testid="stLinkButton"][href*="api.whatsapp.com"]:hover,
        a[data-testid="stLinkButton"][href*="whatsapp.com"]:hover,
        a[data-testid="stLinkButton"][href*="wa.me"]:hover {{
            background: #f1f5f9 !important;
            background-color: #f1f5f9 !important;
            background-image: none !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            border-color: #94a3b8 !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1) !important;
        }}
        /* Reforço no st.dialog: Streamlit às vezes aplica cores invertidas no link_button */
        [data-testid="stDialog"] a[data-testid="stLinkButton"][href*="api.whatsapp.com"],
        [data-testid="stDialog"] a[data-testid="stLinkButton"][href*="whatsapp.com"],
        [data-testid="stDialog"] a[data-testid="stLinkButton"][href*="wa.me"] {{
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            box-sizing: border-box !important;
            min-height: var(--dv-input-height) !important;
            height: var(--dv-input-height) !important;
            padding: 0 1rem !important;
            border-radius: 8px !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
            background-image: none !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            font-weight: 700 !important;
            text-decoration: none !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08) !important;
        }}
        [data-testid="stDialog"] a[data-testid="stLinkButton"][href*="api.whatsapp.com"] *,
        [data-testid="stDialog"] a[data-testid="stLinkButton"][href*="whatsapp.com"] *,
        [data-testid="stDialog"] a[data-testid="stLinkButton"][href*="wa.me"] * {{
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
        }}
        [data-testid="stDialog"] a[data-testid="stLinkButton"][href*="api.whatsapp.com"]:hover,
        [data-testid="stDialog"] a[data-testid="stLinkButton"][href*="whatsapp.com"]:hover,
        [data-testid="stDialog"] a[data-testid="stLinkButton"][href*="wa.me"]:hover {{
            background: #f1f5f9 !important;
            background-color: #f1f5f9 !important;
            background-image: none !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            border-color: #94a3b8 !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1) !important;
        }}
        /* st.dialog: data-testid="stDialog" fica no ROOT do modal (full screen), não num filho - :has() no baseweb nunca casava */
        [data-testid="stDialog"] {{
            position: fixed !important;
            inset: 0 !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            width: 100vw !important;
            min-width: 100% !important;
            max-width: none !important;
            min-height: 100vh !important;
            min-height: 100dvh !important;
            height: 100vh !important;
            height: 100dvh !important;
            max-height: none !important;
            margin: 0 !important;
            padding: clamp(10px, 3vh, 24px) clamp(8px, 2.5vw, 16px) !important;
            box-sizing: border-box !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: rgba(15, 23, 42, 0.78) !important;
            backdrop-filter: blur(10px) saturate(140%) !important;
            -webkit-backdrop-filter: blur(10px) saturate(140%) !important;
            z-index: 2147483000 !important;
        }}
        [data-testid="stDialog"] > div {{
            width: 100% !important;
            max-width: none !important;
            margin: 0 !important;
            max-height: none !important;
            overflow-y: visible !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        /* Painel interior dos modais Streamlit: cartão flutuante + entrada */
        [data-testid="stDialog"] > div > div {{
            border-radius: var(--dv-radius-xl) !important;
            border: 1px solid rgba(255, 255, 255, 0.7) !important;
            box-shadow: 0 25px 60px -15px rgba(15, 23, 42, 0.2), var(--dv-shadow-sm) !important;
            background: var(--dv-surface-glass-strong) !important;
            backdrop-filter: blur(14px) saturate(165%) !important;
            -webkit-backdrop-filter: blur(14px) saturate(165%) !important;
            overflow: auto !important;
        }}
        @media (prefers-reduced-motion: no-preference) {{
            [data-testid="stDialog"] > div > div {{
                animation: dvModalShell 0.38s var(--dv-ease-spring) both;
            }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            [data-testid="stDialog"] > div > div {{
                animation: none !important;
            }}
        }}
        html[data-dv-reduced-motion="1"] [data-testid="stDialog"] > div > div {{
            animation: none !important;
        }}
        /* Painel do popup de exportação: largura confortável (o Root continua em tela cheia) */
        [data-testid="stDialog"]:has(#dv-export-resumo-modal-marker) > div > div {{
            max-width: min(920px, 96vw) !important;
            width: 100% !important;
        }}
        /* X do fechar (st.dialog): só o ícone gira */
        div[data-testid="stDialog"] button[aria-label="Close"] svg,
        [data-testid="stDialog"] button[aria-label="Close"] svg {{
            transition: transform 0.3s ease !important;
            transform: rotate(0deg);
        }}
        div[data-testid="stDialog"] button[aria-label="Close"]:hover svg,
        div[data-testid="stDialog"] button[aria-label="Close"]:focus-visible svg,
        [data-testid="stDialog"] button[aria-label="Close"]:hover svg,
        [data-testid="stDialog"] button[aria-label="Close"]:focus-visible svg {{
            transform: rotate(90deg) !important;
        }}
        /* stAlert: mesma largura dos inputs; avisos/erros/info = vermelho Direcional + texto branco */
        .block-container div[data-testid="stAlert"] {{
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            border-radius: var(--dv-input-radius) !important;
            transition: box-shadow var(--dv-duration) var(--dv-ease-out), transform var(--dv-duration) var(--dv-ease-out) !important;
        }}
        .block-container div[data-testid="stAlert"][kind="warning"],
        .block-container div[data-testid="stAlert"][kind="error"],
        .block-container div[data-testid="stAlert"][kind="info"],
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="warning"]),
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="negative"]),
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="info"]) {{
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
            background: linear-gradient(135deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%) !important;
            box-shadow: var(--dv-shadow-sm), inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
        }}
        @media (hover: hover) {{
            .block-container div[data-testid="stAlert"][kind="warning"]:hover,
            .block-container div[data-testid="stAlert"][kind="error"]:hover,
            .block-container div[data-testid="stAlert"][kind="info"]:hover,
            .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="warning"]):hover,
            .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="negative"]):hover,
            .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="info"]):hover {{
                box-shadow: 0 10px 28px -6px rgba({RGB_VERMELHO_CSS}, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.14) !important;
            }}
        }}
        .block-container div[data-testid="stAlert"][kind="warning"] p,
        .block-container div[data-testid="stAlert"][kind="warning"] span,
        .block-container div[data-testid="stAlert"][kind="warning"] div[data-testid="stMarkdownContainer"],
        .block-container div[data-testid="stAlert"][kind="warning"] div[data-testid="stMarkdownContainer"] *,
        .block-container div[data-testid="stAlert"][kind="error"] p,
        .block-container div[data-testid="stAlert"][kind="error"] span,
        .block-container div[data-testid="stAlert"][kind="error"] div[data-testid="stMarkdownContainer"],
        .block-container div[data-testid="stAlert"][kind="error"] div[data-testid="stMarkdownContainer"] *,
        .block-container div[data-testid="stAlert"][kind="info"] p,
        .block-container div[data-testid="stAlert"][kind="info"] span,
        .block-container div[data-testid="stAlert"][kind="info"] div[data-testid="stMarkdownContainer"],
        .block-container div[data-testid="stAlert"][kind="info"] div[data-testid="stMarkdownContainer"] *,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="warning"]) p,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="warning"]) span,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="warning"]) div[data-testid="stMarkdownContainer"],
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="warning"]) div[data-testid="stMarkdownContainer"] *,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="negative"]) p,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="negative"]) span,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="negative"]) div[data-testid="stMarkdownContainer"],
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="negative"]) div[data-testid="stMarkdownContainer"] *,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="info"]) p,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="info"]) span,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="info"]) div[data-testid="stMarkdownContainer"],
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="info"]) div[data-testid="stMarkdownContainer"] * {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }}
        .block-container div[data-testid="stAlert"][kind="warning"] svg,
        .block-container div[data-testid="stAlert"][kind="error"] svg,
        .block-container div[data-testid="stAlert"][kind="info"] svg,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="warning"]) svg,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="negative"]) svg,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="info"]) svg {{
            fill: #ffffff !important;
            color: #ffffff !important;
        }}
        .block-container div[data-testid="stAlert"][kind="warning"] [data-baseweb="notification"],
        .block-container div[data-testid="stAlert"][kind="error"] [data-baseweb="notification"],
        .block-container div[data-testid="stAlert"][kind="info"] [data-baseweb="notification"],
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="warning"]) [data-baseweb="notification"],
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="negative"]) [data-baseweb="notification"],
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="info"]) [data-baseweb="notification"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}
        /* st.success: mantém verde (feedback positivo), texto branco */
        .block-container div[data-testid="stAlert"][kind="success"],
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="positive"]) {{
            border: 1px solid rgba(255, 255, 255, 0.16) !important;
            background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
            box-shadow: var(--dv-shadow-sm), inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
        }}
        .block-container div[data-testid="stAlert"][kind="success"] p,
        .block-container div[data-testid="stAlert"][kind="success"] span,
        .block-container div[data-testid="stAlert"][kind="success"] div[data-testid="stMarkdownContainer"],
        .block-container div[data-testid="stAlert"][kind="success"] div[data-testid="stMarkdownContainer"] *,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="positive"]) p,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="positive"]) span,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="positive"]) div[data-testid="stMarkdownContainer"],
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="positive"]) div[data-testid="stMarkdownContainer"] * {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }}
        .block-container div[data-testid="stAlert"][kind="success"] svg,
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="positive"]) svg {{
            fill: #ffffff !important;
            color: #ffffff !important;
        }}
        .block-container div[data-testid="stAlert"][kind="success"] [data-baseweb="notification"],
        .block-container div[data-testid="stAlert"]:has([data-baseweb="notification"][kind="positive"]) [data-baseweb="notification"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}

        .stDownloadButton button {{
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            min-height: var(--dv-input-height) !important;
            height: var(--dv-input-height) !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08) !important;
            border-radius: var(--dv-radius-sm) !important;
            transition: background-color var(--dv-duration) var(--dv-ease-out),
                border-color var(--dv-duration) var(--dv-ease-out),
                box-shadow var(--dv-duration) var(--dv-ease-out) !important;
        }}
        .stDownloadButton button:hover {{
            background: #f1f5f9 !important;
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            border-color: #94a3b8 !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1) !important;
        }}
        .stDownloadButton button *,
        .stDownloadButton button svg {{
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            fill: #0f172a !important;
        }}

        [data-testid="stSidebar"] .stButton button {{
            padding: 8px 12px !important;
            font-size: var(--dv-body-font-size) !important;
            margin-bottom: 2px !important;
            height: auto !important;
            min-height: 30px !important;
        }}

        /* Expanders: superfície em vidro fosco + hierarquia clara */
        [data-testid="stExpander"] details {{
            border-radius: var(--dv-radius-md) !important;
            border: 1px solid rgba(226, 232, 240, 0.95) !important;
            background: var(--dv-surface-glass) !important;
            backdrop-filter: blur(12px) saturate(160%) !important;
            -webkit-backdrop-filter: blur(12px) saturate(160%) !important;
            box-shadow: var(--dv-shadow-xs) !important;
            overflow: hidden !important;
            transition: box-shadow var(--dv-duration) var(--dv-ease-out),
                border-color var(--dv-duration) var(--dv-ease-out) !important;
        }}
        [data-testid="stExpander"] details[open] {{
            box-shadow: var(--dv-shadow-sm) !important;
        }}
        [data-testid="stExpander"] summary {{
            font-size: var(--dv-body-font-size) !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em !important;
            cursor: pointer !important;
            transition: background-color var(--dv-duration) var(--dv-ease-out), color var(--dv-duration) var(--dv-ease-out) !important;
            border-radius: calc(var(--dv-radius-md) - 2px) !important;
        }}
        [data-testid="stExpander"] summary:hover {{
            background-color: rgba(255, 255, 255, 0.55) !important;
        }}

        .header-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            gap: var(--dv-stack-gap);
            text-align: center;
            width: 100%;
            max-width: 1100px;
            margin: 0 auto var(--dv-stack-gap);
            padding: 0 clamp(0.75rem, 2vw, 1rem) 0;
            position: relative;
            box-sizing: border-box;
        }}
        /* Barra tipo pill: cor alterna azul ↔ vermelho (opacidade total) */
        .header-brand-bar-wrap {{
            width: 100%;
            max-width: 100%;
            margin-left: 0;
            margin-right: 0;
            position: relative;
            left: auto;
            transform: none;
            margin-bottom: var(--dv-stack-gap);
            margin-top: 0;
            box-sizing: border-box;
            height: 4px;
            border-radius: 999px;
            overflow: hidden;
            background-color: {COR_AZUL_ESC};
            background-image: none;
            box-shadow: 0 1px 3px rgba({RGB_AZUL_CSS}, 0.12);
            animation: none;
        }}
        @media (prefers-reduced-motion: no-preference) {{
            .header-brand-bar-wrap {{
                animation: dvFadeRise var(--dv-duration-slow) var(--dv-ease-out) 0.08s both,
                    fichaBarBrandOscillate 3.5s ease-in-out 0.45s infinite;
            }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            .header-brand-bar-wrap {{
                animation: none !important;
                background-color: {COR_AZUL_ESC} !important;
                will-change: auto !important;
            }}
        }}
        html[data-dv-reduced-motion="1"] .header-brand-bar-wrap {{
            animation: none !important;
            background-color: {COR_AZUL_ESC} !important;
            will-change: auto !important;
        }}
        html[data-dv-reduced-motion="1"] .header-container,
        html[data-dv-reduced-motion="1"] .home-banners-wrap {{
            animation: none !important;
        }}
        .home-banners-wrap {{
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
            max-width: 100vw;
            position: relative;
            margin: 0 auto 0 !important;
            padding: 0 0.75rem;
            box-sizing: border-box;
            text-align: center;
        }}
        .home-banners-section-title {{
            font-family: 'Montserrat', 'Inter', sans-serif !important;
            font-size: var(--dv-title-font-size) !important;
            font-weight: 700 !important;
            color: {COR_AZUL_ESC} !important;
            text-align: center !important;
            margin: 0 0 0.35rem 0 !important;
            padding: 0 0.25rem !important;
            letter-spacing: -0.02em !important;
            line-height: 1.25 !important;
            width: 100%;
            order: 0;
        }}
        /* Campanhas comerciais → iframe popup → Perfil: cola ao bloco seguinte */
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(
            + div[data-testid="stElementContainer"] .dv-perfil-simulacao-anchor
        ) {{
            margin-top: calc(-0.5 * var(--dv-stack-gap)) !important;
            margin-bottom: calc(-0.85 * var(--dv-stack-gap)) !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            min-height: 0 !important;
        }}
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(
            + div[data-testid="stElementContainer"] .dv-perfil-simulacao-anchor
        ) > div {{
            min-height: 0 !important;
        }}
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(
            + div[data-testid="stElementContainer"] .dv-perfil-simulacao-anchor
        ) [data-testid="stIFrame"],
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(
            + div[data-testid="stElementContainer"] .dv-perfil-simulacao-anchor
        ) iframe {{
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            border: 0 !important;
            overflow: hidden !important;
        }}
        .block-container [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(.dv-perfil-simulacao-anchor) {{
            margin-top: calc(-0.65 * var(--dv-stack-gap)) !important;
        }}
        .home-campanhas-copy {{
            width: 100%;
            max-width: min(920px, calc(100vw - clamp(1.5rem, 8vw, 4rem)));
            margin: 0.5rem auto 0;
            padding: 0 clamp(1.25rem, 6vw, 3.25rem) 0.5rem;
            box-sizing: border-box;
            text-align: center;
            font-size: var(--dv-body-font-size);
            order: 2;
        }}
        .home-campanhas-copy-list {{
            margin: 0;
            padding: 0 clamp(0.5rem, 2vw, 1.25rem) 0 clamp(1.35rem, 3.5vw, 2rem);
            list-style: disc;
            color: {COR_TEXTO_LABEL};
            font-size: var(--dv-body-font-size);
            line-height: 1.5;
        }}
        .home-campanhas-copy-list li {{
            margin: 0.4rem 0;
            padding-right: clamp(0.25rem, 1.5vw, 0.75rem);
        }}
        .home-campanhas-copy-titulo {{
            font-weight: 700;
            color: {COR_AZUL_ESC};
        }}
        .home-banners-strip-outer {{
            display: flex;
            justify-content: center;
            width: 100%;
            max-width: 100%;
            overflow-x: auto;
            overflow-y: hidden;
            padding: 0 0.15rem;
            box-sizing: border-box;
            -webkit-overflow-scrolling: touch;
            order: 1;
        }}
        .home-banners-strip {{
            display: flex;
            flex-direction: row;
            flex-wrap: nowrap;
            gap: 1rem;
            padding: 0.35rem 0.25rem 0.75rem;
            scroll-snap-type: x proximity;
            margin-left: auto;
            margin-right: auto;
        }}
        .home-banner-card {{
            flex: 0 0 auto;
            scroll-snap-align: start;
            text-align: center;
            background: var(--dv-surface-glass);
            border-radius: var(--dv-radius-md);
            padding: 6px;
            box-shadow: var(--dv-shadow-sm);
            border: 1px solid rgba(226, 232, 240, 0.92);
            backdrop-filter: blur(10px) saturate(150%);
            -webkit-backdrop-filter: blur(10px) saturate(150%);
            transition: transform var(--dv-duration) var(--dv-ease-out),
                box-shadow var(--dv-duration) var(--dv-ease-out),
                border-color var(--dv-duration) var(--dv-ease-out);
        }}
        @media (hover: hover) and (prefers-reduced-motion: no-preference) {{
            .home-banner-card:hover {{
                transform: translateY(-2px);
                box-shadow: var(--dv-shadow-md);
                border-color: rgba(148, 163, 184, 0.55);
            }}
        }}
        .home-banner-card.home-banner-card--thumb {{
            width: 96px;
            height: 96px;
            padding: 4px;
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .home-banner-thumb-frame {{
            display: block;
            width: 88px;
            height: 88px;
            flex-shrink: 0;
            border-radius: 10px;
            overflow: hidden;
            background: rgba(248, 250, 252, 0.95);
            margin: 0 auto;
        }}
        .home-banner-card.home-banner-card--thumb img {{
            display: block;
            width: 88px;
            height: 88px;
            object-fit: cover;
            object-position: center;
            border-radius: 0;
            margin: 0;
        }}
        .home-banner-lb-root {{
            flex: 0 0 auto;
        }}
        .home-banner-card--fs {{
            cursor: pointer;
        }}
        a.home-banner-card--thumb {{
            text-decoration: none;
            color: inherit;
        }}
        button.home-banner-card.home-banner-card--thumb {{
            font: inherit;
            -webkit-appearance: none;
            appearance: none;
            border: 1px solid rgba(226, 232, 240, 0.95);
            margin: 0;
            text-align: inherit;
        }}
        .home-banner-card--fs:focus-visible {{
            outline: 2px solid {COR_AZUL_ESC};
            outline-offset: 3px;
        }}
        /* Popup campanha: largura/altura seguem a imagem + margem pequena; descrição abaixo com a mesma largura */
        .dv-campanha-overlay {{
            position: fixed !important;
            inset: 0 !important;
            z-index: 999999 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 8px !important;
            box-sizing: border-box !important;
            pointer-events: auto !important;
        }}
        .dv-campanha-overlay-backdrop {{
            position: absolute !important;
            inset: 0 !important;
            background: rgba(15, 23, 42, 0.92) !important;
            cursor: pointer !important;
        }}
        .dv-campanha-overlay-panel {{
            position: relative !important;
            z-index: 1 !important;
            display: inline-block !important;
            width: max-content !important;
            max-width: calc(100vw - 16px) !important;
            max-height: calc(100dvh - 16px) !important;
            overflow: hidden !important;
            background: #ffffff !important;
            border-radius: 12px !important;
            box-shadow: 0 24px 64px rgba(0, 0, 0, 0.45) !important;
            border: 1px solid rgba(255, 255, 255, 0.5) !important;
            padding: 10px !important;
            box-sizing: border-box !important;
            vertical-align: top !important;
        }}
        .dv-campanha-overlay-inner {{
            display: inline-block !important;
            vertical-align: top !important;
            max-width: calc(100vw - 36px) !important;
            max-height: calc(100dvh - 52px) !important;
            overflow-x: hidden !important;
            overflow-y: auto !important;
            box-sizing: border-box !important;
            text-align: center !important;
        }}
        .dv-campanha-overlay-close {{
            position: absolute !important;
            top: max(6px, env(safe-area-inset-top, 0px)) !important;
            right: max(6px, env(safe-area-inset-right, 0px)) !important;
            z-index: 4 !important;
            width: 2.45rem !important;
            height: 2.45rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            border-radius: 8px !important;
            background: #ffffff !important;
            border: 1px solid rgba(15, 23, 42, 0.18) !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15) !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        .dv-campanha-overlay-close svg {{
            display: block !important;
            transition: transform 0.28s var(--dv-ease-out) !important;
        }}
        @media (hover: hover) and (prefers-reduced-motion: no-preference) {{
            .dv-campanha-overlay-close:hover svg,
            .dv-campanha-overlay-close:focus-visible svg {{
                transform: rotate(90deg) !important;
            }}
        }}
        html[data-dv-reduced-motion="1"] .dv-campanha-overlay-close svg {{
            transition: none !important;
        }}
        .dv-campanha-overlay-img-wrap {{
            display: inline-block !important;
            line-height: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }}
        .dv-campanha-overlay-img {{
            display: block !important;
            width: auto !important;
            height: auto !important;
            max-width: calc(100vw - 36px) !important;
            object-fit: contain !important;
            border-radius: 10px !important;
            vertical-align: top !important;
        }}
        .dv-campanha-overlay-text {{
            color: #1e293b !important;
            font-size: var(--dv-body-font-size) !important;
            line-height: 1.55 !important;
            text-align: center !important;
            margin-top: 10px !important;
            padding: 0 2px 2px !important;
            box-sizing: border-box !important;
        }}
        .dv-campanha-overlay-title {{
            margin: 0 0 0.5rem 0 !important;
            font-size: var(--dv-title-font-size) !important;
            font-weight: 700 !important;
            color: {COR_AZUL_ESC} !important;
            font-family: 'Montserrat', 'Inter', sans-serif !important;
        }}
        .dv-campanha-overlay-body {{
            margin: 0 !important;
            white-space: pre-wrap !important;
            word-break: break-word !important;
        }}
        .header-logo-wrap {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
            flex-shrink: 0;
        }}
        .header-logo-wrap img {{
            display: block;
            margin: 0 auto;
            max-height: 72px;
            width: auto;
            max-width: min(300px, 88vw);
            height: auto;
            object-fit: contain;
            filter: drop-shadow(0 2px 10px rgba(15, 23, 42, 0.07));
            transition: transform var(--dv-duration) var(--dv-ease-spring), filter var(--dv-duration) var(--dv-ease-out);
        }}
        @media (hover: hover) and (prefers-reduced-motion: no-preference) {{
            .header-logo-wrap:hover img {{
                transform: scale(1.02);
                filter: drop-shadow(0 6px 18px rgba(15, 23, 42, 0.1));
            }}
        }}
        .header-title {{
            font-family: 'Montserrat', 'Inter', sans-serif;
            font-size: var(--dv-hero-title-font-size) !important;
            font-weight: 800;
            line-height: 1.15;
            margin: 0;
            color: {COR_AZUL_ESC};
            text-align: center;
            text-transform: none !important;
            letter-spacing: -0.03em !important;
        }}
        /* Cabeçalho injetado: wrapper do Streamlit às vezes força alinhamento à esquerda */
        div[data-testid="stMarkdown"] .header-container {{
            text-align: center !important;
            width: 100%;
            max-width: 100%;
        }}
        div[data-testid="stMarkdown"] .header-container .header-title {{
            text-align: center !important;
            font-size: var(--dv-hero-title-font-size) !important;
            font-weight: 800 !important;
            line-height: 1.15 !important;
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            text-transform: none !important;
            letter-spacing: -0.03em !important;
        }}
        /* Login: mesmo cabeçalho + barra; largura = área útil do simulador */
        .dv-login-page {{
            width: 100% !important;
            max-width: 100% !important;
            margin-left: auto !important;
            margin-right: auto !important;
            box-sizing: border-box !important;
        }}
        .dv-login-page .header-container {{
            margin-bottom: 0.35rem;
            max-width: 100% !important;
        }}
        .dv-login-page .header-brand-bar-wrap {{
            margin-bottom: clamp(0.85rem, 2vw, 1.45rem);
        }}
        .dv-login-page .dv-login-acesso-h2 {{
            font-family: 'Montserrat', 'Inter', sans-serif !important;
            font-size: var(--dv-title-font-size) !important;
            font-weight: 700 !important;
            color: {COR_AZUL_ESC} !important;
            text-align: center !important;
            margin: 0 0 clamp(0.75rem, 2vw, 1.1rem) 0 !important;
            letter-spacing: -0.02em !important;
            line-height: 1.25 !important;
        }}
        /* Centrar o bloco de login no viewport; mesma lateralidade que o resto (padding do .block-container) */
        .block-container:has(.dv-login-page) > div > [data-testid="stVerticalBlock"],
        .block-container:has(.dv-login-page) > [data-testid="stVerticalBlock"] {{
            min-height: calc(100dvh - clamp(4.5rem, 12vh, 8rem)) !important;
            justify-content: center !important;
        }}
        .block-container:has(.dv-login-page) [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+2) {{
            margin-bottom: 0 !important;
        }}
        .block-container:has(.dv-login-page) [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(-n+3) {{
            margin-bottom: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            min-height: 0 !important;
        }}
        .block-container:has(.dv-login-page) .footer.dv-login-page-footer {{
            margin-top: clamp(1.25rem, 4vh, 2.5rem) !important;
        }}

        .card, .fin-box, .recommendation-card, .login-card {{
            background: #ffffff;
            font-size: var(--dv-body-font-size);
            padding: clamp(1rem, 2.5vw, 1.35rem);
            border-radius: var(--dv-radius-md);
            border: 1px solid rgba(226, 232, 240, 0.98);
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            box-shadow: var(--dv-shadow-sm);
            transition: transform var(--dv-duration) var(--dv-ease-out),
                box-shadow var(--dv-duration) var(--dv-ease-out),
                border-color var(--dv-duration) var(--dv-ease-out);
        }}
        @media (hover: hover) and (prefers-reduced-motion: no-preference) {{
            .recommendation-card:hover,
            .login-card:hover,
            .card:hover,
            .fin-box:hover {{
                transform: translateY(-3px);
                box-shadow: var(--dv-shadow-md);
                border-color: rgba(148, 163, 184, 0.45);
            }}
        }}

        .summary-header {{
            font-family: 'Montserrat', 'Inter', sans-serif;
            background: {COR_AZUL_ESC};
            color: #ffffff !important;
            padding: 20px;
            border-radius: var(--dv-radius-md) var(--dv-radius-md) 0 0;
            font-weight: 800;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            font-size: var(--dv-title-font-size) !important;
        }}
        .dv-summary-stack {{
            display: flex;
            flex-direction: column;
            gap: var(--dv-stack-gap);
            margin-bottom: var(--dv-stack-gap);
        }}
        .dv-summary-card {{
            margin: 0;
        }}
        .summary-body {{
            background: #ffffff;
            padding: clamp(1.25rem, 3.5vw, 2.25rem);
            border: 1px solid {COR_BORDA};
            border-radius: 0 0 var(--dv-radius-md) var(--dv-radius-md);
            margin-bottom: 0;
            color: #111111;
            text-align: center !important;
            box-shadow: var(--dv-shadow-xs);
        }}
        .dv-prosa-secao {{
            color: #000000 !important;
            margin: 0 0 var(--dv-stack-gap) 0 !important;
            text-align: center !important;
        }}
        .finan-subsidios-note {{
            color: #000000;
            margin: 0 0 var(--dv-stack-gap) 0 !important;
            opacity: 1;
            text-align: center !important;
        }}
        /* Tabela financiamentos/subsídios: quebra linhas na largura disponível (sem esprem texto nem scroll horizontal). */
        .finan-subsidios-table-bleed {{
            box-sizing: border-box;
            width: 100%;
            max-width: 100%;
            margin: var(--dv-stack-gap) 0;
            padding: 0;
            overflow-x: visible;
            container-type: inline-size;
            container-name: finansubs;
        }}
        .finan-subsidios-table-bleed .finan-subsidios-tbl {{
            width: 100%;
            min-width: 0;
            max-width: 100%;
            border-collapse: collapse;
            table-layout: auto;
            color: #111111;
            font-size: clamp(0.8125rem, 2.1vw, 0.9375rem);
        }}
        .finan-subsidios-table-bleed .finan-subsidios-tbl caption {{
            caption-side: top;
            padding: 0 0 0.65rem 0;
            font-weight: 700;
            color: #111111;
            text-align: center;
            font-size: clamp(0.875rem, 2.2vw, 1rem);
            line-height: 1.4;
            white-space: normal;
            word-break: break-word;
            overflow-wrap: break-word;
        }}
        .finan-subsidios-table-bleed .finan-subsidios-tbl th,
        .finan-subsidios-table-bleed .finan-subsidios-tbl td {{
            box-sizing: border-box;
            padding: 8px 8px;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: middle;
            white-space: normal;
            word-break: break-word;
            overflow-wrap: break-word;
            line-height: 1.4;
        }}
        .finan-subsidios-table-bleed .finan-subsidios-tbl thead th {{
            border-color: #cbd5e1;
        }}
        .finan-subsidios-table-bleed .finan-subsidios-tbl thead tr:last-child th {{
            border-bottom: 2px solid #cbd5e1;
        }}
        .finan-subsidios-table-bleed .finan-subsidios-tbl th:not(.finan-subs-num) {{
            text-align: center;
            font-weight: 700;
            color: #000000;
            -webkit-text-fill-color: #000000;
        }}
        .finan-subsidios-table-bleed .finan-subsidios-tbl td.finan-subs-flag,
        .finan-subsidios-table-bleed .finan-subsidios-tbl th.finan-subs-flag {{
            text-align: center;
            font-weight: 600;
            color: #334155;
            -webkit-text-fill-color: #334155;
        }}
        .finan-subsidios-table-bleed .finan-subsidios-tbl td.finan-subs-num,
        .finan-subsidios-table-bleed .finan-subsidios-tbl th.finan-subs-num {{
            text-align: right;
            white-space: nowrap;
            font-weight: 600;
            color: #000000;
            -webkit-text-fill-color: #000000;
        }}
        /* Vista estreita: legenda dos campos + tabela Faixa 2 + tabela Faixa 3 */
        .finan-subs-narrow {{
            display: none;
        }}
        .finan-subs-wide {{
            display: block;
        }}
        @supports (container-type: inline-size) {{
            @container finansubs (max-width: 560px) {{
                .finan-subs-wide {{ display: none !important; }}
                .finan-subs-narrow {{ display: block !important; }}
            }}
            @container finansubs (min-width: 561px) {{
                .finan-subs-wide {{ display: block !important; }}
                .finan-subs-narrow {{ display: none !important; }}
            }}
        }}
        @media not (supports (container-type: inline-size)) {{
            @media (max-width: 720px) {{
                .finan-subs-wide {{ display: none !important; }}
                .finan-subs-narrow {{ display: block !important; }}
            }}
        }}
        .finan-subs-mini-heading {{
            text-align: center;
            font-weight: 700;
            font-size: clamp(0.85rem, 2.2vw, 0.95rem);
            color: #111111;
            margin: 0.85rem 0 0.35rem 0;
            line-height: 1.35;
        }}
        .finan-subs-narrow > .finan-subs-mini-heading:first-of-type {{
            margin-top: 0;
        }}
        .finan-subs-narrow .finan-subsidios-tbl {{
            margin-bottom: 0.15rem;
        }}
        .dv-sinal-com-prosa {{
            color: #111111;
            margin: 0 0 var(--dv-stack-gap) 0 !important;
            line-height: 1.45;
            text-align: center !important;
        }}
        .dv-page-tail-spacer {{
            height: calc(var(--dv-stack-gap) * 2);
            margin: 0;
            pointer-events: none;
        }}
        .custom-alert {{
            background: linear-gradient(135deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%);
            box-sizing: border-box !important;
            width: 100% !important;
            max-width: 100% !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            margin-bottom: var(--dv-stack-gap) !important;
            padding: 0.65rem 0.85rem !important;
            border-radius: var(--dv-input-radius) !important;
            text-align: center;
            font-weight: 600;
            color: #ffffff !important;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: var(--dv-input-height) !important;
            overflow: visible !important;
            line-height: 1.35 !important;
            box-shadow: var(--dv-shadow-sm), inset 0 1px 0 rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.14);
        }}
        .dv-alert-direcional {{
            background: linear-gradient(135deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%);
            color: #ffffff !important;
            box-sizing: border-box !important;
            width: 100% !important;
            max-width: 100% !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            margin-bottom: var(--dv-stack-gap) !important;
            border-radius: var(--dv-input-radius) !important;
            padding: 0.65rem 0.85rem !important;
            min-height: var(--dv-input-height) !important;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            overflow: visible !important;
            box-shadow: var(--dv-shadow-sm), inset 0 1px 0 rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.14);
        }}
        .dv-alert-direcional-inner {{
            font-weight: 600;
            font-size: var(--dv-body-font-size) !important;
            color: #ffffff !important;
            line-height: 1.35 !important;
            width: 100%;
            overflow: visible;
            text-align: center;
        }}
        .dv-alert-direcional-inner strong {{
            color: #ffffff !important;
            font-weight: 800;
        }}
        .dv-alert-direcional-inner a {{
            color: #ffffff !important;
            text-decoration: underline;
        }}
        .price-tag {{
            color: {COR_VERMELHO};
            font-weight: 900;
            font-size: var(--dv-body-font-size) !important;
            margin-top: 5px;
        }}
        .inline-ref {{
            font-size: var(--dv-body-font-size) !important;
            color: #000000 !important;
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            padding-top: 0.05rem;
            padding-bottom: 0.12rem;
            font-weight: 400;
            letter-spacing: 0.02em;
            display: block;
            width: 100%;
            text-align: center !important;
            opacity: 1;
            position: relative;
            z-index: 0;
        }}
        .dv-campo-resumo-movel {{
            text-align: center !important;
        }}
        /* Volta ao Caixa: duas referências empilhadas (sem barra no meio) em qualquer largura */
        .inline-ref-vcx-linhas {{
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            gap: 0.2rem !important;
            text-align: center !important;
        }}
        .inline-ref-vcx-linha {{
            text-align: center !important;
            width: 100%;
        }}
        .inline-ref-vcx-sep {{
            display: none !important;
        }}

        /* Telemóvel / ecrã fino: apoios e referências em várias linhas ficam justificados; desktop mantém centro */
        @media (max-width: 768px) {{
            .block-container div[data-testid="stMarkdown"] p,
            .block-container div[data-testid="stMarkdownContainer"] p {{
                text-align: justify !important;
                text-align-last: center !important;
                hyphens: auto;
                -webkit-hyphens: auto;
            }}
            .block-container .inline-ref,
            .block-container .dv-sug-min-ato,
            .block-container .dv-campo-resumo-movel,
            .block-container .dv-ref-prox-campo,
            .block-container .dv-prosa-secao,
            .block-container .finan-subsidios-note,
            .block-container .dv-sinal-com-prosa,
            .block-container .home-campanhas-copy {{
                text-align: justify !important;
                text-align-last: center !important;
                hyphens: auto;
                -webkit-hyphens: auto;
            }}
            .block-container .home-campanhas-copy-list li {{
                text-align: justify !important;
                text-align-last: center !important;
            }}
            .block-container .inline-ref-vcx-linhas {{
                align-items: stretch !important;
                text-align: justify !important;
            }}
            .block-container .inline-ref-vcx-linha {{
                text-align: justify !important;
                text-align-last: center !important;
            }}
        }}

        .metric-label {{
            color: #000000 !important;
            opacity: 1;
            font-size: var(--dv-body-font-size) !important;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-bottom: 8px;
        }}
        .metric-value {{
            color: #000000 !important;
            font-size: var(--dv-body-font-size) !important;
            font-weight: 800;
            font-family: 'Montserrat', 'Inter', sans-serif;
        }}

        .badge-ideal, .badge-seguro, .badge-multi {{
            background: linear-gradient(135deg, {COR_VERMELHO} 0%, {COR_VERMELHO_ESCURO} 100%) !important;
            color: white;
            padding: 6px 14px;
            border-radius: 999px;
            font-weight: bold;
            font-size: var(--dv-body-font-size) !important;
            margin-top: 10px;
            letter-spacing: 0.02em;
            line-height: 1.25;
            box-shadow: 0 2px 10px -2px rgba({RGB_VERMELHO_CSS}, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.2);
            transition: transform var(--dv-duration) var(--dv-ease-spring), box-shadow var(--dv-duration) var(--dv-ease-out);
        }}
        @media (hover: hover) and (prefers-reduced-motion: no-preference) {{
            .badge-ideal:hover, .badge-seguro:hover, .badge-multi:hover {{
                transform: scale(1.04);
                box-shadow: 0 6px 18px -4px rgba({RGB_VERMELHO_CSS}, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.22);
            }}
        }}
        
        [data-testid="stSidebar"] {{ background-color: #fff; border-right: 1px solid {COR_BORDA}; }}

        .footer {{
            text-align: center;
            margin-top: var(--dv-stack-gap) !important;
            padding: var(--dv-stack-gap) 1rem calc(var(--dv-stack-gap) + 0.25rem);
            font-family: 'Inter', system-ui, sans-serif;
            color: #64748b !important;
            font-size: var(--dv-body-font-size) !important;
            line-height: 1.5;
            border-top: 1px solid transparent;
            border-image: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.45), transparent) 1;
        }}
        .footer em {{
            display: block;
            margin-top: 0.35rem;
            font-style: italic !important;
            font-weight: normal;
        }}

        /* Foco visível consistente (acessibilidade) */
        .stButton button:focus-visible,
        .stDownloadButton button:focus-visible,
        a[data-testid="stLinkButton"]:focus-visible {{
            outline: 2px solid rgba({RGB_AZUL_CSS}, 0.65) !important;
            outline-offset: 2px !important;
        }}
        </style>
    """, unsafe_allow_html=True)


def _html_cartao_resumo_secao(titulo: str, corpo_html: str) -> str:
    """Uma secção do resumo na tela (título + corpo; corpo_html já com escapes onde necessário)."""
    return (
        '<div class="dv-summary-card">'
        f'<div class="summary-header">{html_std.escape(titulo)}</div>'
        f'<div class="summary-body">{corpo_html}</div>'
        "</div>"
    )


def gerar_resumo_pdf(d, volta_caixa_val: float = 0.0):
    if not PDF_ENABLED:
        return None

    try:
        try:
            vc_apl = max(0.0, float(volta_caixa_val or 0))
        except (TypeError, ValueError):
            vc_apl = 0.0
        v_total = max(0.0, float(d.get("imovel_valor", 0) or 0))
        try:
            outros_pdf = max(0.0, float(d.get("outros_descontos", 0) or 0))
        except (TypeError, ValueError):
            outros_pdf = 0.0
        v_prop = max(0.0, v_total - vc_apl - outros_pdf)
        _pol_pdf = str(d.get("politica", "Direcional") or "Direcional").strip()
        _pol_pdf_label = "Emcash" if _politica_emcash(_pol_pdf) else "Direcional"

        pdf = FPDF()
        pdf.add_page()

        # Margens
        pdf.set_margins(12, 12, 12)
        pdf.set_auto_page_break(auto=True, margin=12)

        largura_util = pdf.w - pdf.l_margin - pdf.r_margin

        AZUL = _hex_para_rgb_uint8(COR_AZUL_ESC)
        VERMELHO = (227, 6, 19)
        BRANCO = (255, 255, 255)
        FUNDO_SECAO = (248, 250, 252)

        # Barra superior
        pdf.set_fill_color(*AZUL)
        pdf.rect(0, 0, pdf.w, 3, 'F')

        # Logo (mesmo ficheiro do favicon da página)
        _ico_pdf = None
        _p_fav = _resolver_png_raiz(FAVICON_ARQUIVO)
        if _p_fav and _p_fav.is_file():
            _ico_pdf = str(_p_fav)
        elif os.path.exists("favicon.png"):
            _ico_pdf = "favicon.png"
        if _ico_pdf:
            try:
                pdf.image(_ico_pdf, pdf.l_margin, 8, 10)
            except Exception:
                pass

        # Título
        pdf.ln(8)
        pdf.set_text_color(*AZUL)
        _nome_topo_pdf = (d.get("nome") or "").strip()
        if _nome_topo_pdf:
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(0, 6, _pdf_text_seguro(_nome_topo_pdf), ln=True, align='C')
            pdf.ln(2)
        pdf.set_font("Helvetica", 'B', 20)
        pdf.cell(0, 10, _pdf_text_seguro("Resumo da simulação - Direcional"), ln=True, align='C')

        pdf.set_font("Helvetica", '', 9)
        pdf.cell(0, 5, _pdf_text_seguro("Simulador imobiliário Direcional"), ln=True, align='C')
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
        # CONTEÚDO (alinhado ao texto WhatsApp / resumo na tela)
        # ===============================
        secao("Renda")
        linha("Renda familiar total", f"R$ {fmt_br(d.get('renda', 0))}")
        _cpf_pdf_d = re.sub(r"\D", "", str(d.get("cpf") or ""))
        if len(_cpf_pdf_d) == 11:
            linha("CPF", _sf_cpf_mascarado_br(_cpf_pdf_d))
        elif str(d.get("cpf") or "").strip():
            linha("CPF", _pdf_text_seguro(str(d.get("cpf") or "").strip()))
        _rank_pdf_s = str(d.get("ranking") or "").strip()
        if _rank_pdf_s:
            linha("Ranking do cliente", _pdf_text_seguro(_rank_pdf_s))

        pdf.ln(2)
        secao("Dados do imóvel")
        linha("Empreendimento", _pdf_text_seguro(d.get("empreendimento_nome")))
        linha("Unidade", _pdf_text_seguro(d.get("unidade_id")))
        linha("Valor de venda (lista)", f"R$ {fmt_br(v_total)}", True)
        _desc_pdf = vc_apl + outros_pdf
        if _desc_pdf > 0.009:
            linha("Descontos Concedidos", f"R$ {fmt_br(_desc_pdf)}")
        _mot_pdf = str(d.get("outros_descontos_motivo") or "").strip()
        if outros_pdf > 0.009 and _mot_pdf:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(70, 80, 95)
            pdf.multi_cell(
                largura_util,
                4,
                _pdf_text_seguro(f"Origem dos outros descontos: {_mot_pdf}"),
                ln=True,
            )
            pdf.ln(1)
            pdf.set_text_color(*AZUL)
        linha("Valor final da unidade", f"R$ {fmt_br(v_prop)}", True)
        if d.get("unid_entrega"):
            linha("Previsão de entrega", _pdf_text_seguro(d.get("unid_entrega")))
        if d.get("unid_area"):
            linha("Área privativa", _pdf_text_seguro(f"{d.get('unid_area')} m²"))
        if d.get("unid_tipo"):
            linha("Tipologia", _pdf_text_seguro(d.get("unid_tipo")))
        if d.get("unid_endereco") and d.get("unid_bairro"):
            linha(
                "Localização",
                _pdf_text_seguro(f"{d.get('unid_endereco')} - {d.get('unid_bairro')}"),
            )

        pdf.ln(2)
        secao("Financiamento")
        linha("Financiamento utilizado", f"R$ {fmt_br(d.get('finan_usado', 0))}")
        prazo = d.get('prazo_financiamento', 360)
        linha(
            "Sistema de amortização e prazo",
            f"{nome_sistema_amortizacao_completo(str(d.get('sistema_amortizacao', 'SAC')))} - {prazo} meses",
        )
        linha("Parcela estimada do financiamento", f"R$ {fmt_br(d.get('parcela_financiamento', 0))}")
        linha("FGTS + subsídio", f"R$ {fmt_br(d.get('fgts_sub_usado', 0))}")

        pdf.ln(2)
        secao("Entrada e Pro Soluto")
        if _politica_emcash(d.get("politica")):
            linha(
                "Política de Pro Soluto",
                _pdf_text_seguro(f"{_pol_pdf_label} ({_EMCASH_NOTA_PARCELAS})"),
            )
        else:
            linha("Política de Pro Soluto", _pdf_text_seguro(_pol_pdf_label))
        linha("Pro Soluto (valor)", f"R$ {fmt_br(d.get('ps_usado', 0))}")
        linha("Número de parcelas do Pro Soluto", _pdf_text_seguro(d.get("ps_parcelas")))
        linha("Mensalidade do Pro Soluto", f"R$ {fmt_br(d.get('ps_mensal', 0))}")
        linha("Ato 1 (Entrada Imediata)", f"R$ {fmt_br(d.get('ato_final', 0))}")
        if _politica_emcash(d.get("politica")):
            linha("Ato 30", f"R$ {fmt_br(d.get('ato_30', 0))}")
            linha("Ato 60", f"R$ {fmt_br(d.get('ato_60', 0))}")
        else:
            linha("Ato 30", f"R$ {fmt_br(d.get('ato_30', 0))}")
            linha("Ato 60", f"R$ {fmt_br(d.get('ato_60', 0))}")
            linha("Ato 90", f"R$ {fmt_br(d.get('ato_90', 0))}")
        _ent_ps = float(d.get('entrada_total', 0) or 0) + float(d.get('ps_usado', 0) or 0)
        linha("Entrada total (atos e Pro Soluto)", f"R$ {fmt_br(_ent_ps)}", True)

        # ===============================
        # RODAPÉ (DADOS CORRETOR)
        # ===============================
        pdf.ln(4)

        cn = (d.get("corretor_nome") or "").strip()
        if cn:
            pdf.set_font("Helvetica", 'B', 9)
            pdf.set_text_color(*AZUL)
            pdf.cell(0, 5, _pdf_text_seguro("Consultor"), ln=True, align='L')
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(0, 6, _pdf_text_seguro(cn), ln=True)

        pdf.ln(2)

        # Aviso Legal e Data
        pdf.set_font("Helvetica", 'I', 7)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            0,
            4,
            _pdf_text_seguro(
                f"Simulação em {d.get('data_simulacao', date.today().strftime('%d/%m/%Y'))}. "
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
    nome_cliente_fmt = str(nome_cliente or dados_cliente.get("nome") or "Cliente").strip() or "Cliente"
    emp = str(dados_cliente.get('empreendimento_nome', 'Seu Imóvel') or 'Seu Imóvel').strip()
    unid = str(dados_cliente.get('unidade_id', '') or '').strip()
    produto_ref = f"{emp} - Unidade {unid}" if unid else emp
    try:
        _vc_mail = max(0.0, float(dados_cliente.get("volta_caixa_aplicado", 0) or 0))
    except (TypeError, ValueError):
        _vc_mail = 0.0
    try:
        _out_mail = max(0.0, float(dados_cliente.get("outros_descontos", 0) or 0))
    except (TypeError, ValueError):
        _out_mail = 0.0
    _v_raw = float(dados_cliente.get("imovel_valor", 0) or 0)
    try:
        _vf_mail = dados_cliente.get("valor_final_unidade")
        _vf_num = float(_vf_mail) if _vf_mail is not None else (max(0.0, _v_raw - _vc_mail - _out_mail))
    except (TypeError, ValueError):
        _vf_num = max(0.0, _v_raw - _vc_mail - _out_mail)
    val_venda = fmt_br(max(0.0, _vf_num))
    _out_fmt_mail = fmt_br(_out_mail)
    _mot_mail_raw = str(dados_cliente.get("outros_descontos_motivo") or "").strip()
    _mot_mail_esc = html_std.escape(_mot_mail_raw)
    _html_outros_corretor = (
        f'<tr><td>Outros descontos</td><td align="right">R$ {_out_fmt_mail}</td></tr>\n'
        f'<tr><td colspan="2" style="font-size:12px;color:#475569;padding-top:4px;">'
        f"<strong>Origem dos outros descontos:</strong> {_mot_mail_esc}</td></tr>\n"
        if _mot_mail_raw
        else f'<tr><td>Outros descontos</td><td align="right">R$ {_out_fmt_mail}</td></tr>\n'
    )
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
    _lbl_cor_ato30 = "&nbsp;&nbsp;↳ Ato 30"
    _lbl_cor_ato60 = "&nbsp;&nbsp;↳ Ato 60"
    _html_nota_emcash_entrada = ""

    corretor_nome = dados_cliente.get('corretor_nome', 'Direcional')
    corretor_tel = dados_cliente.get('corretor_telefone', '')
    corretor_email = dados_cliente.get('corretor_email', '')
    
    corretor_tel_clean = re.sub(r'\D', '', corretor_tel)
    if not corretor_tel_clean.startswith('55'):
        corretor_tel_clean = '55' + corretor_tel_clean # Assuming Brazil

    wa_msg = f"Olá {corretor_nome}, sou {nome_cliente_fmt}. Realizei uma simulação para {produto_ref} e gostaria de saber mais detalhes."
    wa_link = f"https://wa.me/{corretor_tel_clean}?text={urllib.parse.quote(wa_msg)}"

    _nm_mail_show = str(dados_cliente.get("nome") or "").strip()
    _html_mail_nome = ""
    if _nm_mail_show:
        _html_mail_nome = (
            '<p style="text-align:center; margin:0 0 6px 0; font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:0.08em;">Cliente ou Imobiliária</p>'
            f'<p style="text-align:center; margin:0 0 18px 0; font-size:24px; font-weight:700; color:{COR_AZUL_ESC}; line-height:1.25;">{html_std.escape(_nm_mail_show)}</p>'
        )
    _cpf_mail_d2 = re.sub(r"\D", "", str(dados_cliente.get("cpf") or ""))
    _linhas_id_mail: list[str] = []
    if len(_cpf_mail_d2) == 11:
        _linhas_id_mail.append(f"CPF: {html_std.escape(_sf_cpf_mascarado_br(_cpf_mail_d2))}")
    elif str(dados_cliente.get("cpf") or "").strip():
        _linhas_id_mail.append(
            f"CPF: {html_std.escape(str(dados_cliente.get('cpf') or '').strip())}"
        )
    _rk_m = str(dados_cliente.get("ranking") or "").strip()
    if _rk_m:
        _linhas_id_mail.append(f"Ranking: {html_std.escape(_rk_m)}")
    _html_mail_ident = ""
    if _linhas_id_mail:
        _html_mail_ident = (
            '<p style="text-align:center;margin:0 0 22px 0;font-size:14px;color:#334155;line-height:1.55;">'
            + "<br>".join(_linhas_id_mail)
            + "</p>"
        )
    _nome_cor_td = html_std.escape(_nm_mail_show) if _nm_mail_show else ""
    _html_cor_extras = ""
    if _linhas_id_mail:
        _html_cor_extras = (
            '<p style="margin:6px 0 0 0;font-size:13px;color:#475569;line-height:1.45;">'
            + "<br>".join(_linhas_id_mail)
            + "</p>"
        )

    # TEMPLATE CLIENTE (Foco no sonho, design limpo, usando Tabelas para evitar sobreposição)
    if tipo == 'cliente':
        msg['Subject'] = f"Simulação Direcional - {nome_cliente_fmt} - {produto_ref}"
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
                            <!-- Cabeçalho (sem imagem) -->
                            <tr>
                                <td align="center" style="background-color: {COR_AZUL_ESC}; padding: 14px 30px; border-bottom: 4px solid #e30613;">&nbsp;</td>
                            </tr>
                            <!-- Corpo -->
                            <tr>
                                <td style="padding: 40px;">
                                    {_html_mail_nome}
                                    {_html_mail_ident}
                                    <h2 style="color: {COR_AZUL_ESC}; margin: 0 0 20px 0; font-weight: 300; text-align: center;">Olá!</h2>
                                    <p style="font-size: 16px; line-height: 1.6; text-align: center; color: #555;">
                                        Foi ótimo apresentar as oportunidades da Direcional para você. Preparamos a condição para <strong>{produto_ref}</strong>.
                                    </p>
                                    
                                    <!-- Card Destaque -->
                                    <table width="100%" border="0" cellspacing="0" cellpadding="20" style="background-color: #f0f4f8; border-left: 5px solid #e30613; margin: 30px 0; border-radius: 4px;">
                                        <tr>
                                            <td>
                                                <p style="margin: 0; font-weight: bold; color: {COR_AZUL_ESC}; font-size: 18px;">{emp}</p>
                                                <p style="margin: 5px 0 0 0; color: #777;">{('Unidade: ' + unid) if unid else ''}</p>
                                                <p style="margin: 15px 0 0 0; font-size: 24px; font-weight: bold; color: #e30613;">Valor final da unidade: R$ {val_venda}</p>
                                            </td>
                                        </tr>
                                    </table>

                                    <div style="text-align: center; margin: 35px 0;">
                                        <a href="{wa_link}" style="background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; padding: 15px 30px; text-decoration: none; font-weight: bold; border-radius: 5px; font-size: 16px; display: inline-block;">Falar com o corretor pelo WhatsApp</a>
                                        <p style="font-size: 12px; color: #999; margin-top: 10px;">(Abra o documento em formato PDF em anexo para ver todos os detalhes.)</p>
                                    </div>
                                    
                                    <!-- Rodapé Interno -->
                                    <table width="100%" border="0" cellspacing="0" cellpadding="20" style="margin-top: 40px; background-color: {COR_AZUL_ESC}; color: #ffffff;">
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
        msg['Subject'] = f"Simulação Direcional - {nome_cliente_fmt} - {produto_ref}"
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
                            <!-- Cabeçalho (sem imagem) -->
                            <tr>
                                <td align="center" style="background-color: {COR_AZUL_ESC}; padding: 14px 30px; border-bottom: 4px solid #e30613;">&nbsp;</td>
                            </tr>
                            <tr>
                                <td style="padding: 30px;">
                                    {_html_mail_nome}
                                    {_html_mail_ident}
                                    <h3 style="color: {COR_AZUL_ESC}; border-bottom: 2px solid #e30613; padding-bottom: 10px; margin-top: 0;">RESUMO DE ATENDIMENTO</h3>
                                    
                                    <!-- Info Header -->
                                    <table width="100%" border="0" cellspacing="0" cellpadding="15" style="margin-bottom: 20px; background: #f9f9f9;">
                                        <tr>
                                            <td width="50%" valign="top">
                                                <p style="margin: 0 0 5px 0; font-size: 12px; color: #666;">CLIENTE / IMOBILIÁRIA</p>
                                                <p style="margin: 0; font-weight: bold; font-size: 16px;">{_nome_cor_td if _nome_cor_td else "&nbsp;"}</p>
                                                {_html_cor_extras}
                                                <p style="margin: 5px 0 0 0; font-size: 14px;">Renda: R$ {renda_cli}</p>
                                            </td>
                                            <td width="50%" valign="top">
                                                <p style="margin: 0 0 5px 0; font-size: 12px; color: #666;">PRODUTO</p>
                                                <p style="margin: 0; font-weight: bold; font-size: 16px;">{emp}</p>
                                                <p style="margin: 5px 0 0 0;">{('Unid: ' + unid) if unid else ''}</p>
                                            </td>
                                        </tr>
                                    </table>

                                    <h4 style="color: {COR_AZUL_ESC}; margin-top: 0;">Valores do Imóvel</h4>
                                    <table width="100%" border="1" cellspacing="0" cellpadding="8" style="border-collapse: collapse; border-color: #ddd; margin-bottom: 20px; font-size: 14px;">
                                        {_html_outros_corretor}
                                        <tr style="background-color: #f2f2f2;">
                                            <td>Valor final da unidade (após descontos)</td>
                                            <td align="right" style="color: #e30613;"><b>R$ {val_venda}</b></td>
                                        </tr>
                                        <tr>
                                            <td>Avaliação Bancária</td>
                                            <td align="right">R$ {val_aval}</td>
                                        </tr>
                                    </table>

                                    <h4 style="color: {COR_AZUL_ESC};">Plano de Pagamento</h4>
                                    <table width="100%" border="1" cellspacing="0" cellpadding="8" style="border-collapse: collapse; border-color: #ddd; margin-bottom: 20px; font-size: 14px;">
                                        <tr style="background-color: #f2f2f2;">
                                            <td>Entrada Total</td>
                                            <td align="right" style="color: {COR_AZUL_ESC};"><b>R$ {entrada}</b></td>
                                        </tr>
                                        <tr>
                                             <td>&nbsp;&nbsp;↳ Ato 1 (Entrada Imediata)</td>
                                             <td align="right">R$ {a0}</td>
                                        </tr>
                                        <tr>
                                             <td>{_lbl_cor_ato30}</td>
                                             <td align="right">R$ {a30}</td>
                                        </tr>
                                        <tr>
                                             <td>{_lbl_cor_ato60}</td>
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
        _safe_prod = re.sub(r"[^a-zA-Z0-9_-]+", "_", produto_ref)[:60]
        _safe_nome = re.sub(r"[^a-zA-Z0-9_-]+", "_", nome_cliente_fmt)[:40]
        _pdf_name = f"Resumo_{_safe_nome}_{_safe_prod}.pdf"
        part = MIMEApplication(pdf_bytes, Name=_pdf_name)
        part['Content-Disposition'] = f'attachment; filename="{_pdf_name}"'
        msg.attach(part)
    try:
        server = smtplib.SMTP(smtp_server, smtp_port); server.ehlo(); server.starttls(); server.ehlo()
        server.login(sender_email, sender_password); server.sendmail(sender_email, destinatario, msg.as_string()); server.quit()
        return True, "E-mail enviado com sucesso!"
    except smtplib.SMTPAuthenticationError:
        return False, "Erro de Autenticacao (535). Verifique Senha de App."
    except Exception as e: return False, f"Erro envio: {e}"


try:
    _dialog_export_deco = st.dialog("Resumo: PDF, e-mail e WhatsApp", width="large")
except TypeError:
    _dialog_export_deco = st.dialog("Resumo: PDF, e-mail e WhatsApp")


@_dialog_export_deco
def show_export_dialog(d):
    st.markdown(
        '<span id="dv-export-resumo-modal-marker" aria-hidden="true" '
        'style="position:absolute;width:0;height:0;overflow:hidden;clip:rect(0,0,0,0)"></span>',
        unsafe_allow_html=True,
    )
    st.markdown(f"<h3 style='text-align: center; color: {COR_AZUL_ESC}; margin: 0;'>Resumo da Simulação</h3>", unsafe_allow_html=True)

    d["corretor_nome"] = st.session_state.get("user_name", "")
    d["corretor_email"] = st.session_state.get("user_email", "")
    d["corretor_telefone"] = st.session_state.get("user_phone", "")

    _vc_dialog = texto_moeda_para_float(st.session_state.get("volta_caixa_key"))
    pdf_data = gerar_resumo_pdf(d, volta_caixa_val=_vc_dialog)

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
        _dv_alerta_vermelho_texto("Geração do documento PDF indisponível.")

    st.markdown("---")
    st.markdown("**2. Enviar por e-mail (cliente)**")
    email = st.text_input(
        "Endereço de e-mail do cliente (e-mail)",
        placeholder="cliente@exemplo.com",
        key="export_dialog_email_cliente",
    )
    if st.button("Enviar e-mail para o cliente", use_container_width=True, key="export_dialog_btn_email"):
        if email and "@" in email:
            sucesso, msg = enviar_email_smtp(
                email,
                d.get("nome", "Cliente"),
                pdf_data,
                {**d, "volta_caixa_aplicado": _vc_dialog},
                tipo="cliente",
            )
            if sucesso:
                st.success(msg)
            else:
                _dv_alerta_vermelho_texto(str(msg))
        else:
            _dv_alerta_vermelho_texto("E-mail inválido")

    st.markdown("---")
    st.markdown("**3. WhatsApp**")
    _wa_msg = montar_mensagem_whatsapp_resumo(
        d,
        volta_caixa_val=_vc_dialog,
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
        )
    else:
        _dv_alerta_vermelho_texto(
            "A mensagem ficou grande demais para abrir pelo link automático do WhatsApp. "
            "Use o envio por e-mail ou o PDF neste mesmo painel."
        )

# =============================================================================
# APLICAÇÃO PRINCIPAL
# =============================================================================

def aba_simulador_automacao(
    df_finan,
    df_estoque,
    df_politicas,
    premissas_dict=None,
    df_home_banners: pd.DataFrame | None = None,
    df_campanhas_texto: pd.DataFrame | None = None,
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
        '<div class="header-brand-bar-wrap" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    # Resumo da simulação: sem faixa de campanhas comerciais nem iframe do popup de miniaturas
    if passo != "summary":
        render_secao_campanhas_comerciais(
            df_home_banners if df_home_banners is not None else pd.DataFrame(),
            df_campanhas_texto if df_campanhas_texto is not None else pd.DataFrame(),
            user_is_adm=bool(st.session_state.get("user_is_adm")),
        )
        inject_home_banner_dialog_modal()

    # --- PÁGINA ÚNICA: perfil → valores → recomendações → unidade → distribuição (ordem fixa) ---
    if passo == 'sim':
        st.markdown(
            '<div class="dv-perfil-simulacao-anchor"><h3 class="dv-titulo-secao">Perfil da simulação</h3></div>',
            unsafe_allow_html=True,
        )
        _nome_ref = st.text_input(
            "Nome do Cliente ou Imobiliária (opcional) (texto)",
            value=str(st.session_state.dados_cliente.get("nome", "") or ""),
            key="nome_cliente_imobiliaria_opt_v1",
            placeholder="Exemplo: João da Silva ou Imobiliária Exemplo",
        )

        _dc_in = st.session_state.dados_cliente
        if "renda_familiar_total_v1" not in st.session_state:
            _lista_ant = list(_dc_in.get("rendas_lista") or [])
            _soma_ant = float(_dc_in.get("renda", 0) or 0)
            if _lista_ant:
                try:
                    _soma_ant = sum(float(x or 0) for x in _lista_ant[:4])
                except (TypeError, ValueError):
                    pass
            st.session_state["renda_familiar_total_v1"] = float_para_campo_texto(
                max(0.0, _soma_ant), vazio_se_zero=True
            )
        st.text_input(
            "Renda familiar total (R$)",
            key="renda_familiar_total_v1",
            placeholder="R$ 0,00",
        )
        renda_total_calc = max(0.0, texto_moeda_para_float(st.session_state.get("renda_familiar_total_v1")))
        if "cpf_classificar_clientes_sf" not in st.session_state:
            st.session_state["cpf_classificar_clientes_sf"] = str(
                st.session_state.dados_cliente.get("cpf") or ""
            ).strip()
        st.text_input(
            "CPF - Classificar Clientes (opcional) (CPF)",
            key="cpf_classificar_clientes_sf",
            placeholder="000.000.000-00",
        )
        cpf_digits = re.sub(r"\D", "", st.session_state.get("cpf_classificar_clientes_sf") or "")
        rank_opts = ["DIAMANTE", "OURO", "PRATA", "BRONZE", "AÇO"]
        _sf_rs: str | None = None
        _sf_code: str | None = None
        if len(cpf_digits) == 11:
            _sf_rank_prog_ph = st.empty()
            _memo_hit = _dv_sf_rank_memo_get(cpf_digits)
            if _memo_hit is not None:
                _sf_rs, _sf_code = _memo_hit
                _sf_rank_prog_ph.markdown(
                    _sf_ranking_progress_markup(
                        1.0,
                        _SF_RANK_PROGRESS_MSG_SUCESSO if _sf_rs else "Verificação concluída.",
                        elapsed_s=0.0,
                        meter_n=100,
                        meter_total=100,
                    ),
                    unsafe_allow_html=True,
                )
            else:
                _injetar_secrets_salesforce_no_env()

                def _sf_prog_cb(frac: float, msg: str, elapsed: float) -> None:
                    _sf_rank_prog_ph.markdown(
                        _sf_ranking_progress_markup(
                            frac,
                            msg,
                            elapsed_s=elapsed,
                            meter_n=int(round(frac * 100)),
                            meter_total=100,
                        ),
                        unsafe_allow_html=True,
                    )

                try:
                    _sf_rs, _sf_code = _sf_classificar_ranking_cpf_11(
                        cpf_digits,
                        progress=_sf_prog_cb,
                    )
                except Exception as _sf_ex:
                    _sf_logger.exception("Classificação ranking Salesforce: %s", _sf_ex)
                    _sf_rs, _sf_code = None, "sem_registo"
                finally:
                    _sf_rank_prog_ph.markdown(
                        _sf_ranking_progress_markup(
                            1.0,
                            _SF_RANK_PROGRESS_MSG_SUCESSO if _sf_rs else "Verificação concluída.",
                            elapsed_s=0.0,
                            meter_n=100,
                            meter_total=100,
                        ),
                        unsafe_allow_html=True,
                    )
                _dv_sf_rank_memo_set(cpf_digits, _sf_rs, _sf_code)
            if _sf_rs and _sf_rs in rank_opts and st.session_state.get("_sf_rank_applied_cpf") != cpf_digits:
                st.session_state["in_rank_v28"] = _sf_rs
                st.session_state["_sf_rank_applied_cpf"] = cpf_digits
                st.session_state["_sf_rank_naoencontrado_toast_cpf"] = ""
                if hasattr(st, "toast"):
                    try:
                        st.toast(f"Ranking encontrado: {_sf_rs}", icon="✅")
                    except Exception:
                        pass
            elif (
                not _sf_rs
                and _sf_code in ("sem_registo", "sem_conexao", "erro_sf")
                and st.session_state.get("_sf_rank_naoencontrado_toast_cpf") != cpf_digits
            ):
                st.session_state["_sf_rank_naoencontrado_toast_cpf"] = cpf_digits
                if hasattr(st, "toast"):
                    try:
                        st.toast("Ranking não encontrado.", icon="❌")
                    except Exception:
                        pass
        else:
            # CPF incompleto ou vazio: permite nova consulta ao voltar a 11 dígitos
            st.session_state["_sf_rank_applied_cpf"] = ""
            st.session_state["_sf_rank_naoencontrado_toast_cpf"] = ""
            # Ao apagar/editar o CPF, remove o ranking aplicado pela consulta Salesforce anterior
            st.session_state["in_rank_v28"] = rank_opts[0]
            if cpf_digits:
                st.markdown(
                    '<p class="inline-ref" style="margin-top:0;margin-bottom:0;line-height:1.45;">'
                    "CPF não cadastrado. Contate o Comercial.</p>",
                    unsafe_allow_html=True,
                )
        if len(cpf_digits) == 11:
            if _sf_rs:
                st.markdown(
                    f'<p class="inline-ref" style="margin-top:0;margin-bottom:0;line-height:1.45;">'
                    f"Ranking encontrado: <strong>{html_std.escape(str(_sf_rs))}</strong></p>",
                    unsafe_allow_html=True,
                )
            elif _sf_code == "cpf_incompleto":
                st.markdown(
                    '<p class="inline-ref" style="margin-top:0;margin-bottom:0;line-height:1.45;">'
                    "CPF não cadastrado. Contate o Comercial.</p>",
                    unsafe_allow_html=True,
                )
            elif _sf_code in ("sem_registo", "sem_conexao", "erro_sf"):
                st.markdown(
                    '<p class="inline-ref" style="margin-top:0;margin-bottom:0;line-height:1.45;">'
                    "CPF não encontrado. Um novo contato deve ser criado no salesforce</p>",
                    unsafe_allow_html=True,
                )
        _rank_now = st.session_state.get("in_rank_v28", st.session_state.dados_cliente.get("ranking", "DIAMANTE"))
        curr_ranking = _rank_now
        idx_ranking = rank_opts.index(curr_ranking) if curr_ranking in rank_opts else 0
        ranking = st.selectbox(
            "Ranking do Cliente (lista)",
            options=rank_opts,
            index=idx_ranking,
            key="in_rank_v28",
        )
        _pol_saved = st.session_state.dados_cliente.get("politica")
        _pol_idx = 0 if _pol_saved == "Direcional" else 1
        politica_ps = st.selectbox(
            "Política de Pro Soluto (lista)",
            ["Direcional", "Emcash"],
            index=_pol_idx,
            key="in_pol_v28",
        )

        prazo_ps_max = 84 if politica_ps == "Emcash" else 84
        st.session_state.dados_cliente.update({
            'nome': str(_nome_ref or "").strip(),
            'nome_imobiliaria': "",
            'cpf': cpf_digits,
            'data_nascimento': None,
            'renda': renda_total_calc,
            'rendas_lista': [renda_total_calc, 0.0, 0.0, 0.0],
            'ranking': ranking,
            'politica': politica_ps,
            'qtd_participantes': 1,
            'finan_usado_historico': 0.0,
            'ps_usado_historico': 0.0,
            'fgts_usado_historico': 0.0,
            'prazo_ps_max': prazo_ps_max,
            'limit_ps_renda': 0.30,
        })

        st.markdown("---")
        # --- ETAPA 2: VALORES APROVADOS (FECHAMENTO FINANCEIRO) ---
        d = st.session_state.dados_cliente
        st.markdown(
            '<h3 class="dv-titulo-secao">Valores Aprovados</h3>',
            unsafe_allow_html=True,
        )

        renda_cli = float(d.get("renda", 0) or 0)
        _val_bruto_faixa = float(d.get("imovel_avaliacao") or 0) or 240000.0
        # Sinal com: só no fechamento, se a avaliação bancária estiver até ~30k acima de 275k ou de 400k
        _avaliacao_gate_fech = max(0.0, float(d.get("imovel_avaliacao") or 0))
        _mostrar_sinal_com = (275_000.0 < _avaliacao_gate_fech <= 305_000.0) or (
            400_000.0 < _avaliacao_gate_fech <= 430_000.0
        )

        _matriz_bd = motor.obter_quatro_combinacoes_f2_f3_f4(renda_cli)
        _ix_sim_sim = next(
            (i for i, rowq in enumerate(_matriz_bd) if rowq["social"] and rowq["cotista"]),
            max(0, len(_matriz_bd) - 1),
        )
        _row_sim_cot = _matriz_bd[_ix_sim_sim]

        def _sim_nao(v):
            return "Sim" if v else "Não"

        _tbl_rows = "".join(
            f"<tr>"
            f"<td class='finan-subs-flag'>{_sim_nao(it['social'])}</td>"
            f"<td class='finan-subs-flag'>{_sim_nao(it['cotista'])}</td>"
            f"<td class='finan-subs-num'>{reais_streamlit_html(fmt_br(it['fin_F2']))}</td>"
            f"<td class='finan-subs-num'>{reais_streamlit_html(fmt_br(it['sub_F2']))}</td>"
            f"<td class='finan-subs-num'>{reais_streamlit_html(fmt_br(it['fin_F3']))}</td>"
            f"<td class='finan-subs-num'>{reais_streamlit_html(fmt_br(it['sub_F3']))}</td>"
            f"</tr>"
            for it in _matriz_bd
        )
        _tbl_rows_f2 = "".join(
            f"<tr>"
            f"<td class='finan-subs-flag'>{_sim_nao(it['social'])}</td>"
            f"<td class='finan-subs-flag'>{_sim_nao(it['cotista'])}</td>"
            f"<td class='finan-subs-num'>{reais_streamlit_html(fmt_br(it['fin_F2']))}</td>"
            f"<td class='finan-subs-num'>{reais_streamlit_html(fmt_br(it['sub_F2']))}</td>"
            f"</tr>"
            for it in _matriz_bd
        )
        _tbl_rows_f3 = "".join(
            f"<tr>"
            f"<td class='finan-subs-flag'>{_sim_nao(it['social'])}</td>"
            f"<td class='finan-subs-flag'>{_sim_nao(it['cotista'])}</td>"
            f"<td class='finan-subs-num'>{reais_streamlit_html(fmt_br(it['fin_F3']))}</td>"
            f"<td class='finan-subs-num'>{reais_streamlit_html(fmt_br(it['sub_F3']))}</td>"
            f"</tr>"
            for it in _matriz_bd
        )
        st.markdown(
            f"""<div class="finan-subsidios-table-bleed">
<div class="finan-subs-wide">
<table class="finan-subsidios-tbl">
<caption>Financiamentos e subsídios (base de dados - Financiamentos) - Faixas 2 e 3</caption>
<thead>
<tr>
<th rowspan="2">Fator Social</th>
<th rowspan="2">Cotista FGTS</th>
<th colspan="2">Faixa 2 - Imóveis até 275k</th>
<th colspan="2">Faixa 3 - Imóveis até 400k</th>
</tr>
<tr>
<th class="finan-subs-num">Financiamento</th>
<th class="finan-subs-num">Subsídios</th>
<th class="finan-subs-num">Financiamento</th>
<th class="finan-subs-num">Subsídios</th>
</tr>
</thead>
<tbody>{_tbl_rows}</tbody>
</table>
</div>
<div class="finan-subs-narrow">
<div class="finan-subs-mini-heading">Faixa 2 — imóveis até 275 mil (referência curva)</div>
<table class="finan-subsidios-tbl">
<thead>
<tr>
<th>Fator Social</th>
<th>Cotista FGTS</th>
<th class="finan-subs-num">Financiamento</th>
<th class="finan-subs-num">Subsídios</th>
</tr>
</thead>
<tbody>{_tbl_rows_f2}</tbody>
</table>
<div class="finan-subs-mini-heading">Faixa 3 — imóveis até 400 mil (referência curva)</div>
<table class="finan-subsidios-tbl">
<thead>
<tr>
<th>Fator Social</th>
<th>Cotista FGTS</th>
<th class="finan-subs-num">Financiamento</th>
<th class="finan-subs-num">Subsídios</th>
</tr>
</thead>
<tbody>{_tbl_rows_f3}</tbody>
</table>
</div>
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p class="finan-subsidios-note">Subsídios da curva inferiores a '
            f"<strong>{reais_streamlit_html(fmt_br(SUBSIDIO_MINIMO_CURVA))}</strong> são desconsiderados (tratados como "
            f"<strong>{reais_streamlit_html('0,00')}</strong>). "
            f"A tabela acima é só referência; financiamento e subsídio aprovados podem ser outros valores.</p>",
            unsafe_allow_html=True,
        )

        if _mostrar_sinal_com:
            if "sinal_com_key" not in st.session_state:
                st.session_state["sinal_com_key"] = float_para_campo_texto(
                    max(0.0, float(d.get("sinal_com", 0) or 0)), vazio_se_zero=True
                )
            _sinal_raw = texto_moeda_para_float(st.session_state.get("sinal_com_key"))
            _sinal_apl = max(0.0, float(_sinal_raw or 0))
            if _sinal_apl > _val_bruto_faixa:
                _sinal_apl = float(_val_bruto_faixa)
                st.session_state["sinal_com_key"] = float_para_campo_texto(_sinal_apl, vazio_se_zero=True)
        else:
            _sinal_apl = 0.0
            st.session_state.dados_cliente["sinal_com"] = 0.0
            st.session_state["sinal_com_key"] = float_para_campo_texto(0.0, vazio_se_zero=True)

        _val_aval_para_faixa = max(0.0, _val_bruto_faixa - _sinal_apl)
        st.session_state.dados_cliente["sinal_com"] = float(_sinal_apl)
        st.session_state.dados_cliente["imovel_avaliacao_curva_efetiva"] = float(_val_aval_para_faixa)
        _, _, _faixa_pre_sinal = motor.obter_enquadramento(
            renda_cli, True, True, valor_avaliacao=_val_bruto_faixa
        )
        _, _, _faixa_curva = motor.obter_enquadramento(
            renda_cli, True, True, valor_avaliacao=_val_aval_para_faixa
        )
        if str(_faixa_curva) not in ("F2", "F3", "F4"):
            _faixa_curva = "F2"
        _fin_ref_sim_cot = float(_row_sim_cot.get(f"fin_{_faixa_curva}", 0) or 0)
        _sub_ref_sim_cot = float(_row_sim_cot.get(f"sub_{_faixa_curva}", 0) or 0)

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
        st.text_input(
            "Financiamento aprovado (R$)",
            key="fin_aprovado_key",
            placeholder="Exemplo: 250000 ou 250.000,00",
        )
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
            "FGTS e subsídio aprovados (R$)",
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
        st.text_input(
            "Prazo do financiamento (inteiro — meses)",
            key="prazo_aprovado_key",
            placeholder="360",
        )
        _pz = texto_inteiro(st.session_state.get("prazo_aprovado_key"), default=360, min_v=12, max_v=600)
        prazo_sel = _pz if _pz is not None else 360
        st.session_state.dados_cliente['prazo_financiamento'] = int(prazo_sel)

        _opcoes_amort = list(_AMORTIZACAO_NOME_COMPLETO.values())
        _cod_amort_atual = str(d.get("sistema_amortizacao", "SAC")).strip().upper()
        _idx_amort = 1 if _cod_amort_atual == "PRICE" else 0
        sist_sel_label = st.selectbox(
            "Sistema de amortização do financiamento (lista)",
            options=_opcoes_amort,
            index=_idx_amort,
            key="sist_aprovado_ui_v1",
        )
        sist_sel = "PRICE" if sist_sel_label == _AMORTIZACAO_NOME_COMPLETO["PRICE"] else "SAC"
        st.session_state.dados_cliente['sistema_amortizacao'] = sist_sel
        taxa_padrao = taxa_fin_vigente(d)
        _comp_sac_price = calcular_comparativo_sac_price(f_u, int(prazo_sel), taxa_padrao)
        sac_details = _comp_sac_price["SAC"]
        price_details = _comp_sac_price["PRICE"]
        if sist_sel == "PRICE":
            _ref_comp_html = (
                f"Valor estimado da parcela: <strong>{reais_streamlit_html(fmt_br(price_details['parcela']))}</strong> "
                f"parcelas fixas (juros totais: <strong>{reais_streamlit_html(fmt_br(price_details['juros']))}</strong>)"
            )
        else:
            _ref_comp_html = (
                f"Valor estimado da parcela: <strong>{reais_streamlit_html(fmt_br(sac_details['primeira']))}</strong> "
                f"a <strong>{reais_streamlit_html(fmt_br(sac_details['ultima']))}</strong> "
                f"(juros totais: <strong>{reais_streamlit_html(fmt_br(sac_details['juros']))}</strong>)"
            )
        st.markdown(
            f'<div class="dv-ref-prox-campo">{_ref_comp_html}</div>',
            unsafe_allow_html=True,
        )
        _parc_fin_ref = calcular_parcela_financiamento(f_u, int(prazo_sel), taxa_padrao, sist_sel)
        taxa_v = float(taxa_padrao or 0.0)
        _parc_sig_now = (round(float(f_u or 0), 2), int(prazo_sel), str(sist_sel), round(taxa_v, 6))
        _parc_sig_prev = st.session_state.get("_parc_fin_auto_sig")
        _parc_ref_prev = st.session_state.get("_parc_fin_auto_ref_prev")
        _tol_parc = 0.05
        # Campo editável: começa (ou volta) com a referência automática se ainda vazio/zero; qualquer outro valor respeita a edição.
        if float(_parc_fin_ref or 0) > 0.02:
            _ui_seed = texto_moeda_para_float(st.session_state.get("parcela_fin_edit_key"))
            if "parcela_fin_edit_key" not in st.session_state or abs(float(_ui_seed or 0)) < 0.02:
                st.session_state["parcela_fin_edit_key"] = float_para_campo_texto(_parc_fin_ref, vazio_se_zero=True)
        _ui_parc = texto_moeda_para_float(st.session_state.get("parcela_fin_edit_key"))
        _parc_fin_amort_ant = st.session_state.get("_parc_fin_last_sistema")
        if _parc_fin_amort_ant != sist_sel:
            st.session_state["parcela_fin_edit_key"] = float_para_campo_texto(_parc_fin_ref, vazio_se_zero=True)
            st.session_state["_parc_fin_last_sistema"] = sist_sel
        elif _parc_sig_prev != _parc_sig_now:
            _alinha_auto = False
            if _parc_ref_prev is not None and abs(float(_ui_parc) - float(_parc_ref_prev)) < _tol_parc:
                _alinha_auto = True
            elif abs(float(_ui_parc)) < 0.02 and float(_parc_fin_ref) > 0.02:
                _alinha_auto = True
            if _alinha_auto:
                st.session_state["parcela_fin_edit_key"] = float_para_campo_texto(_parc_fin_ref, vazio_se_zero=True)
        st.session_state["_parc_fin_auto_sig"] = _parc_sig_now
        st.session_state["_parc_fin_auto_ref_prev"] = float(_parc_fin_ref)
        st.text_input(
            "Parcela estimada do financiamento (editável) (R$)",
            key="parcela_fin_edit_key",
            placeholder="0,00",
        )
        _parc_fin_ui = clamp_moeda_positiva(texto_moeda_para_float(st.session_state.get("parcela_fin_edit_key")), None)
        if _parc_fin_ui <= 0:
            _parc_fin_ui = _parc_fin_ref
        st.session_state.dados_cliente["parcela_financiamento"] = float(_parc_fin_ui)
        st.markdown(
            f'<span class="inline-ref">Referência automática: <strong>{reais_streamlit_html(fmt_br(_parc_fin_ref))}</strong></span>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        # --- ETAPA 3: RECOMENDAÇÃO (filtro empreendimento + cards; sem abas) ---
        d = st.session_state.dados_cliente
        st.markdown(
            '<h3 class="dv-titulo-secao">Recomendação de Imóveis</h3>',
            unsafe_allow_html=True,
        )

        df_disp_total = df_estoque_com_poder_compra(df_estoque.copy(), d, df_politicas, _prem)

        if df_disp_total.empty:
            st.markdown('<div class="custom-alert">Sem estoque carregado para recomendações.</div>', unsafe_allow_html=True)
        else:
            df_disp_total = df_disp_total.sort_values(["Valor de Venda", "Identificador"], ascending=[True, True])

            emp_names_rec = sorted(df_disp_total["Empreendimento"].unique().tolist())
            emp_rec = st.selectbox(
                "Filtrar por empreendimento: (lista)",
                options=["Todos"] + emp_names_rec,
                key="sel_emp_rec_v28",
            )
            df_pool = df_disp_total if emp_rec == "Todos" else df_disp_total[df_disp_total["Empreendimento"] == emp_rec]

            if df_pool.empty:
                st.markdown('<div class="custom-alert">Nenhuma unidade encontrada para o filtro.</div>', unsafe_allow_html=True)
            else:
                final_cards = []
                cand_rec = candidatos_df_recomendados(df_pool)
                if emp_rec == "Todos" and not df_pool.empty:
                    fit_all = df_pool[df_pool.get("Unidade_Compativel", False) == True].copy()
                    if not fit_all.empty and "Empreendimento" in fit_all.columns:
                        fit_all["Lucro_Recomendacao"] = pd.to_numeric(
                            fit_all.get("Lucro_Recomendacao", 0), errors="coerce"
                        ).fillna(-1e18)
                        fit_all = fit_all.sort_values(
                            ["Empreendimento", "Lucro_Recomendacao", "Valor de Venda", "Identificador"],
                            ascending=[True, False, False, True],
                        )
                        cand_rec = fit_all.groupby("Empreendimento", as_index=False).head(1)
                comp_col = pd.to_numeric(df_pool.get("Unidade_Compativel", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
                alguma_cabe = (comp_col > 0).any()
                label_rec, css_rec = ("MAIOR LUCRO", "badge-ideal") if alguma_cabe else ("MENOR PREÇO", "badge-seguro")

                def add_cards_group(label, df_group, css_class):
                    if df_group is None or df_group.empty:
                        return
                    df_u = df_group.drop_duplicates(subset=["Empreendimento", "Identificador"])
                    df_u = df_u.sort_values(
                        ["Lucro_Recomendacao", "Valor de Venda", "Empreendimento", "Identificador"],
                        ascending=[False, False, True, True],
                    )
                    for _, row in df_u.iterrows():
                        final_cards.append({"label": label, "row": row, "css": css_class})

                add_cards_group(label_rec, cand_rec, css_rec)

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
                         lucro_fmt = fmt_br(float(row.get("Lucro_Recomendacao", 0) or 0))
                         vcx_usado_fmt = fmt_br(float(row.get("VCX_Usado_Fechamento", 0) or 0))
                         vcx_pres_fmt = fmt_br(float(row.get("VCX_Preservado", 0) or 0))
                         label = card['label']
                         css_badge = card['css']
                         
                         cards_html += f"""
                         <div class="card-item">
                            <div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC}; height: 100%; justify-content: flex-start;">
                                <span style="color:#111111; opacity:0.95;">Perfil</span><br>
                                <div style="margin-top:5px; margin-bottom:15px;"><span class="{css_badge}">{label}</span></div>
                                <b style="color:#111111;">{emp_name}</b><br>
                                <div style="color:#111111; text-align:center; border-top:1px solid #eee; padding-top:10px; width:100%;">
                                    <b>Unidade: {unid_name}</b>
                                </div>
                                <div style="margin: 10px 0; width: 100%;">
                                    <div style="color:#111111;">Avaliação</div>
                                    <div style="font-weight:bold; color:#111111;">{reais_streamlit_html(aval_fmt)}</div>
                                    <div style="color:#111111; margin-top:5px;">Valor de venda</div>
                                    <div class="price-tag" style="margin-top:0;">{reais_streamlit_html(val_fmt)}</div>
                                    <div style="color:#111111; margin-top:8px;">Retorno estimado</div>
                                    <div style="font-weight:800; color:#111111;">{reais_streamlit_html(lucro_fmt)}</div>
                                    <div style="color:#111111; opacity:0.75; margin-top:5px;">
                                      VCX a ser usado: {reais_streamlit_html(vcx_usado_fmt)} | VCX preservado: {reais_streamlit_html(vcx_pres_fmt)}
                                    </div>
                                </div>
                            </div>
                         </div>"""
                    cards_html += "</div></div>"
                    st.markdown(cards_html, unsafe_allow_html=True)

        st.markdown("---")
        # --- ETAPA 4: ESCOLHA DE UNIDADE (lista por preço crescente) ---
        d = st.session_state.dados_cliente
        st.markdown(
            '<h3 class="dv-titulo-secao">Escolha de Unidade</h3>',
            unsafe_allow_html=True,
        )
        uni_escolhida_id = None
        df_disponiveis = df_estoque.copy()
        if df_disponiveis.empty:
            _dv_alerta_vermelho_texto("Sem estoque disponível.")
        else:
            emp_names = sorted(df_disponiveis['Empreendimento'].unique())
            meses_entrega_emp: dict[str, int] = {}
            for _emp in emp_names:
                _sub_emp = df_disponiveis[df_disponiveis["Empreendimento"] == _emp]
                _meses_validos: list[int] = []
                for _dt in _sub_emp.get("Data Entrega", pd.Series(dtype=object)).tolist():
                    _m = meses_ate_entrega(_dt)
                    _meses_validos.append(_m)
                if _meses_validos:
                    meses_entrega_emp[_emp] = min(_meses_validos)
            idx_emp = 0
            if 'empreendimento_nome' in st.session_state.dados_cliente:
                try:
                    idx_emp = emp_names.index(st.session_state.dados_cliente['empreendimento_nome'])
                except Exception:
                    idx_emp = 0
            def _fmt_emp_com_prazo(nome_emp: str) -> str:
                m = meses_entrega_emp.get(nome_emp)
                if m is None:
                    return f"{nome_emp} - prazo de entrega: n/d"
                return f"{nome_emp} - prazo de entrega: {m} mes(es)"

            emp_escolhido = st.selectbox(
                "Escolha o Empreendimento: (lista)",
                options=emp_names,
                index=idx_emp,
                key="sel_emp_new_v3",
                format_func=_fmt_emp_com_prazo,
            )
            st.session_state.dados_cliente['empreendimento_nome'] = emp_escolhido
            unidades_disp = df_disponiveis[(df_disponiveis['Empreendimento'] == emp_escolhido)].copy()
            unidades_disp = unidades_disp.sort_values(['Valor de Venda', 'Identificador'], ascending=[True, True])
            if unidades_disp.empty:
                _dv_alerta_vermelho_texto("Sem unidades disponíveis.")
            else:
                _rec_ids_emp = ids_unidades_recomendadas_empreendimento(
                    df_disponiveis, emp_escolhido, d, df_politicas, _prem
                )
                uni_ordered = unidades_disp.drop_duplicates(subset=['Identificador'], keep='first').copy()
                uni_ordered["_vv_sort"] = pd.to_numeric(
                    uni_ordered["Valor de Venda"], errors="coerce"
                ).fillna(0.0)
                uni_ordered["_id_norm"] = uni_ordered["Identificador"].map(
                    lambda x: str(x).strip() if x is not None else ""
                )
                uo_rec = uni_ordered[uni_ordered["_id_norm"].isin(_rec_ids_emp)].sort_values(
                    ["_vv_sort", "Identificador"], ascending=[True, True]
                )
                uo_out = uni_ordered[~uni_ordered["_id_norm"].isin(_rec_ids_emp)].sort_values(
                    ["_vv_sort", "Identificador"], ascending=[True, True]
                )
                current_uni_ids = uo_rec["Identificador"].tolist() + uo_out["Identificador"].tolist()
                _str_current = [str(_cid).strip() for _cid in current_uni_ids]
                _last_emp_fe = st.session_state.get("_sim_fechar_last_emp")
                if _last_emp_fe != emp_escolhido:
                    idx_uni = 0
                else:
                    idx_uni = 0
                    if current_uni_ids and "unidade_id" in st.session_state.dados_cliente:
                        try:
                            _u_norm = str(st.session_state.dados_cliente["unidade_id"]).strip()
                            if _u_norm in _str_current:
                                idx_uni = _str_current.index(_u_norm)
                        except Exception:
                            pass
                st.session_state["_sim_fechar_last_emp"] = emp_escolhido
                # Chave do widget por empreendimento (não pelo índice na lista ordenada):
                # índices podem coincidir entre empreendimentos e o Streamlit reutilizava o estado
                # da unidade anterior quando ambos tinham o mesmo Identificador.
                _emp_widget_slug = hashlib.sha1(
                    str(emp_escolhido).encode("utf-8", errors="replace")
                ).hexdigest()[:14]

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
                    corpo = (
                        f"{uid} | Avaliação: R$ {v_aval} | Venda: R$ {v_venda} | "
                        f"Desconto Volta ao Caixa: R$ {v_vc_fmt}"
                    )
                    if str(uid).strip() in _rec_ids_emp:
                        return f"RECOMENDADA: {corpo}"
                    return corpo

                uni_escolhida_id = st.selectbox(
                    "Escolha a Unidade: (lista)",
                    options=current_uni_ids,
                    index=min(idx_uni, len(current_uni_ids) - 1) if current_uni_ids else 0,
                    format_func=label_uni,
                    key=f"sel_uni_emp_{_emp_widget_slug}",
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
                    prazo_max_ps = 84 if pol == 'Emcash' else 84
                    st.session_state.dados_cliente['prazo_ps_max'] = prazo_max_ps

        _d_sinal_pos = st.session_state.dados_cliente
        _vu_sinal_pos = max(0.0, float(_d_sinal_pos.get("imovel_valor", 0) or 0))
        _avaliacao_gate_sinal = max(0.0, float(_d_sinal_pos.get("imovel_avaliacao") or 0))
        _mostrar_sinal_pos = (275_000.0 < _avaliacao_gate_sinal <= 305_000.0) or (
            400_000.0 < _avaliacao_gate_sinal <= 430_000.0
        )
        _val_bruto_sinal = float(_d_sinal_pos.get("imovel_avaliacao") or 0) or _vu_sinal_pos or 240000.0
        _renda_sinal_pos = float(_d_sinal_pos.get("renda", 0) or 0)
        if _mostrar_sinal_pos and _avaliacao_gate_sinal > 0.0 and str(_d_sinal_pos.get("unidade_id") or "").strip():
            if "sinal_com_key" not in st.session_state:
                st.session_state["sinal_com_key"] = float_para_campo_texto(
                    max(0.0, float(_d_sinal_pos.get("sinal_com", 0) or 0)), vazio_se_zero=True
                )
            st.markdown(
                '<p class="dv-sinal-com-prosa">'
                "O campo Sinal com tem a finalidade de abater da avaliação bancária "
                "unidades pouco acima do limite da faixa anterior, a fim de que o cliente possa pegar maior financiamento. "
                "Os valores de financiamento e subsídio automáticos seguirão o valor da unidade após abatimento "
                "(caso seja feito), não só o valor da unidade cheio. "
                "Faixa 2: imóveis até <strong>275 mil</strong>; Faixa 3: imóveis até <strong>400 mil</strong>. "
                "Caso o valor seja pouco acima disso, use o campo para abater.</p>",
                unsafe_allow_html=True,
            )
            st.text_input(
                "Sinal com (R$)",
                key="sinal_com_key",
                placeholder="0,00",
                help="Opcional. Reduz a avaliação usada na leitura da faixa F2/F3/F4 na base Financiamentos.",
            )
            _sinal_raw_pos = texto_moeda_para_float(st.session_state.get("sinal_com_key"))
            _sinal_apl_pos = max(0.0, float(_sinal_raw_pos or 0))
            if _sinal_apl_pos > _val_bruto_sinal:
                _sinal_apl_pos = float(_val_bruto_sinal)
                st.session_state["sinal_com_key"] = float_para_campo_texto(_sinal_apl_pos, vazio_se_zero=True)
            _val_ef_sinal = max(0.0, _val_bruto_sinal - _sinal_apl_pos)
            if _val_bruto_sinal > 400000.0:
                _sug_sinal = max(0.0, _val_bruto_sinal - 400000.0)
                st.markdown(
                    f'<p class="inline-ref" style="margin-top:0;margin-bottom:0.35rem;line-height:1.45;">'
                    f"Imóvel na faixa 4 na avaliação cheia (acima de <strong>400 mil</strong>). É necessário "
                    f"<strong>{reais_streamlit_html(fmt_br(_sug_sinal))}</strong>"
                    f" de abatimento para que a avaliação efetiva fique na faixa 3"
                    f" (limite <strong>400 mil</strong>).</p>"
                    f'<p class="inline-ref" style="margin:0.9rem 0 0;line-height:1.45;">'
                    f"Valor de Avaliação com Sinal Com: "
                    f"<strong>{reais_streamlit_html(fmt_br(_val_ef_sinal))}</strong></p>",
                    unsafe_allow_html=True,
                )
            elif _val_bruto_sinal > 275000.0:
                _sug_sinal = max(0.0, _val_bruto_sinal - 275000.0)
                st.markdown(
                    f'<p class="inline-ref" style="margin-top:0;margin-bottom:0.35rem;line-height:1.45;">'
                    f"Imóvel faixa 3 no preço cheio. É necessário "
                    f"<strong>{reais_streamlit_html(fmt_br(_sug_sinal))}</strong>"
                    f" de abatimento para que seja classificado como faixa 2.</p>"
                    f'<p class="inline-ref" style="margin:0.9rem 0 0;line-height:1.45;">'
                    f"Valor de Avaliação com Sinal Com: "
                    f"<strong>{reais_streamlit_html(fmt_br(_val_ef_sinal))}</strong></p>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<p class="inline-ref" style="margin-top:0;margin-bottom:0.35rem;line-height:1.45;">'
                    "Avaliação na faixa 2 (até <strong>275 mil</strong>). O Sinal com"
                    " é opcional se quiser ajuste fino da referência da curva.</p>"
                    f'<p class="inline-ref" style="margin:0.9rem 0 0;line-height:1.45;">'
                    f"Valor de Avaliação com Sinal Com: "
                    f"<strong>{reais_streamlit_html(fmt_br(_val_ef_sinal))}</strong></p>",
                    unsafe_allow_html=True,
                )
            st.session_state.dados_cliente["sinal_com"] = float(_sinal_apl_pos)
            st.session_state.dados_cliente["imovel_avaliacao_curva_efetiva"] = float(_val_ef_sinal)

        st.markdown("---")
        # --- ETAPA 5: DISTRIBUIÇÃO DA ENTRADA (FECHAMENTO) ---
        d = st.session_state.dados_cliente
        st.markdown(
            '<h3 class="dv-titulo-secao">Distribuição da Entrada</h3>',
            unsafe_allow_html=True,
        )
        if float(d.get('imovel_valor', 0) or 0) <= 0 or not d.get('unidade_id'):
            st.markdown(
                '<p style="color:#111111;margin:0 0 0.5rem 0;">Selecione empreendimento e '
                "unidade na seção acima para calcular a distribuição da entrada.</p>",
                unsafe_allow_html=True,
            )
        # Valores da unidade vêm do cadastro (Valor de Venda); demais valores do fluxo anterior
        u_valor = float(d.get('imovel_valor', 0) or 0)
        vc_ref_top = float(d.get('volta_caixa_ref', 0) or 0)
        if 'volta_caixa_key' not in st.session_state:
            st.session_state['volta_caixa_key'] = ""
        if 'outros_descontos_key' not in st.session_state:
            st.session_state['outros_descontos_key'] = ""
        if "outros_descontos_motivo_key" not in st.session_state:
            st.session_state["outros_descontos_motivo_key"] = str(
                st.session_state.dados_cliente.get("outros_descontos_motivo") or ""
            )
        vc_input_val = 0.0
        outros_desc = 0.0
        v_liquido = 0.0
        if u_valor > 0:
            _vc_raw_top = texto_moeda_para_float(st.session_state.get('volta_caixa_key'))
            vc_input_val = (
                max(0.0, min(_vc_raw_top, vc_ref_top)) if vc_ref_top > 0 else max(0.0, _vc_raw_top)
            )
            if abs(_vc_raw_top - vc_input_val) > 0.009:
                st.session_state['volta_caixa_key'] = float_para_campo_texto(vc_input_val, vazio_se_zero=True)
            _out_raw_top = texto_moeda_para_float(st.session_state.get("outros_descontos_key"))
            outros_desc = max(0.0, _out_raw_top)
            _max_out_top = max(0.0, u_valor - vc_input_val)
            if outros_desc > _max_out_top + 0.009:
                outros_desc = _max_out_top
                st.session_state["outros_descontos_key"] = float_para_campo_texto(
                    outros_desc, vazio_se_zero=True
                )
            v_liquido = max(0.0, u_valor - vc_input_val - outros_desc)
        st.session_state.dados_cliente["outros_descontos"] = outros_desc
        st.session_state.dados_cliente["outros_descontos_motivo"] = str(
            st.session_state.get("outros_descontos_motivo_key") or ""
        ).strip()
        st.session_state.dados_cliente["valor_final_unidade"] = v_liquido
        st.session_state.dados_cliente["volta_caixa_aplicado"] = vc_input_val

        f_u_input = clamp_moeda_positiva(float(d.get('finan_usado', 0) or 0), None)
        fgts_u_input = clamp_moeda_positiva(float(d.get('fgts_sub_usado', 0) or 0), None)
        if u_valor > 0:
            f_u_input = min(f_u_input, v_liquido)
            fgts_u_input = min(fgts_u_input, max(0.0, v_liquido - f_u_input))
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

        vc_ref_num = vc_ref_top

        if 'parc_ps_key' not in st.session_state:
            try:
                _p0 = int(d.get('ps_parcelas', min(84, parc_max_ui)) or 1)
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

        ps_limite_ui = float(mps.get("ps_max_efetivo", 0) or 0)

        if 'ps_u_key' not in st.session_state:
            st.session_state['ps_u_key'] = float_para_campo_texto(st.session_state.dados_cliente.get('ps_usado', 0.0), vazio_se_zero=True)
        _ps0 = texto_moeda_para_float(st.session_state.get('ps_u_key'))
        _teto_ps_opts = []
        if ps_limite_ui > 0:
            _teto_ps_opts.append(ps_limite_ui)
        if u_valor > 0:
            _teto_ps_opts.append(max(0.0, v_liquido - f_u_input - fgts_u_input))
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

        _teto_cap = []
        if ps_limite_ui > 0:
            _teto_cap.append(ps_limite_ui)
        if u_valor > 0:
            _teto_cap.append(max(0.0, v_liquido - f_u_input - fgts_u_input))
        _teto_ps_cap = min(_teto_cap) if _teto_cap else None
        _ps_cap = clamp_moeda_positiva(texto_moeda_para_float(st.session_state.get('ps_u_key')), _teto_ps_cap)
        cap_atos = max(0.0, v_liquido - f_u_input - fgts_u_input - _ps_cap)

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
            _opts_ps_btn.append(max(0.0, v_liquido - f_u_input - fgts_u_input))
        _teto_ps_btn = min(_opts_ps_btn) if _opts_ps_btn else 0.0
        st.session_state["_ps_teto_para_botao"] = float(_teto_ps_btn or 0)

        def _preencher_ps_restante() -> None:
            du = st.session_state.dados_cliente
            try:
                v_alvo = float(du.get("valor_final_unidade", 0) or 0)
            except (TypeError, ValueError):
                v_alvo = 0.0
            if v_alvo <= 0:
                v_alvo = float(du.get("imovel_valor", 0) or 0)
            fi = float(du.get("finan_usado", 0) or 0)
            su = float(du.get("fgts_sub_usado", 0) or 0)
            em = _politica_emcash(du.get("politica"))
            a1 = max(0.0, texto_moeda_para_float(st.session_state.get("ato_1_key")))
            a2 = max(0.0, texto_moeda_para_float(st.session_state.get("ato_2_key")))
            a3 = max(0.0, texto_moeda_para_float(st.session_state.get("ato_3_key")))
            a4 = 0.0 if em else max(0.0, texto_moeda_para_float(st.session_state.get("ato_4_key")))
            gap = max(0.0, v_alvo - fi - su - a1 - a2 - a3 - a4)
            teto_b = float(st.session_state.get("_ps_teto_para_botao", 0) or 0)
            novo = min(gap, teto_b) if teto_b > 0 else gap
            st.session_state["ps_u_key"] = float_para_campo_texto(novo, vazio_se_zero=True)

        _renda_cli = max(0.0, float(d.get("renda", 0) or 0))
        _sug_min_ato1 = 2.0 * _renda_cli
        _sug_min_meio = _renda_cli / 2.0
        _dv_sug_min_style = (
            "margin:0 0 0.35rem 0;padding:0;font-size:0.8125rem;line-height:1.35;"
            "color:#000000;text-align:center;"
        )

        def _dv_linha_sug_min_apos_campo(val_fmt: str) -> None:
            st.markdown(
                f'<p class="dv-sug-min-ato" style="{_dv_sug_min_style}">Tente pegar no mínimo '
                f"<strong>{reais_streamlit_html(html_std.escape(val_fmt))}</strong>.</p>",
                unsafe_allow_html=True,
            )

        # --- Ato 1 (Entrada Imediata): só key + session_state (evita conflito value/key) ---
        st.text_input(
            "Ato 1 (Entrada Imediata) (R$)",
            key="ato_1_key",
            placeholder="0,00",
        )
        if _renda_cli > 0:
            _dv_linha_sug_min_apos_campo(fmt_br(_sug_min_ato1))
        r1 = max(0.0, texto_moeda_para_float(st.session_state.get("ato_1_key")))
        st.session_state.dados_cliente['ato_final'] = r1
        
        # Função para distribuir o restante (usa PS atual da session)
        def distribuir_restante(n_parcelas):
            a1_atual = max(0.0, texto_moeda_para_float(st.session_state.get('ato_1_key')))
            ps_atual_cb = texto_moeda_para_float(st.session_state.get('ps_u_key'))
            _opts_cb = []
            if ps_limite_ui > 0:
                _opts_cb.append(ps_limite_ui)
            if u_valor > 0:
                _opts_cb.append(max(0.0, v_liquido - f_u_input - fgts_u_input))
            _teto_cb = min(_opts_cb) if _opts_cb else None
            ps_atual_cb = clamp_moeda_positiva(ps_atual_cb, _teto_cb)
            gap_total = max(0.0, v_liquido - f_u_input - fgts_u_input - ps_atual_cb)
            
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
            st.button(
                "Distribuir saldo restante em duas parcelas (30 e 60 dias)",
                use_container_width=True,
                key="btn_rest_2x",
                on_click=distribuir_restante,
                args=(2,),
            )
            st.button(
                "Distribuir saldo restante em três parcelas (30, 60 e 90 dias)",
                use_container_width=True,
                key="btn_rest_3x",
                on_click=distribuir_restante,
                args=(3,),
            )

        st.write("")
        if is_emcash:
            st.text_input(
                "Ato 30 (R$)",
                key="ato_2_key",
                placeholder="0,00",
            )
            if _renda_cli > 0:
                _dv_linha_sug_min_apos_campo(fmt_br(_sug_min_meio))
            st.session_state.dados_cliente["ato_30"] = max(
                0.0, texto_moeda_para_float(st.session_state.get("ato_2_key"))
            )
            st.text_input(
                "Ato 60 (R$)",
                key="ato_3_key",
                placeholder="0,00",
            )
            if _renda_cli > 0:
                _dv_linha_sug_min_apos_campo(fmt_br(_sug_min_meio))
            st.session_state.dados_cliente["ato_60"] = max(
                0.0, texto_moeda_para_float(st.session_state.get("ato_3_key"))
            )
        else:
            st.text_input("Ato 30 (R$)", key="ato_2_key", placeholder="0,00")
            if _renda_cli > 0:
                _dv_linha_sug_min_apos_campo(fmt_br(_sug_min_meio))
            st.session_state.dados_cliente["ato_30"] = max(
                0.0, texto_moeda_para_float(st.session_state.get("ato_2_key"))
            )
            st.text_input("Ato 60 (R$)", key="ato_3_key", placeholder="0,00")
            if _renda_cli > 0:
                _dv_linha_sug_min_apos_campo(fmt_br(_sug_min_meio))
            st.session_state.dados_cliente["ato_60"] = max(
                0.0, texto_moeda_para_float(st.session_state.get("ato_3_key"))
            )
            st.text_input("Ato 90 (R$)", key="ato_4_key", placeholder="0,00")
            if _renda_cli > 0:
                _dv_linha_sug_min_apos_campo(fmt_br(_sug_min_meio))
            st.session_state.dados_cliente["ato_90"] = max(
                0.0, texto_moeda_para_float(st.session_state.get("ato_4_key"))
            )

        st.write("")
        st.button(
            "Preencher valor restante no Pro Soluto",
            key="btn_ps_preencher_restante",
            use_container_width=True,
            on_click=_preencher_ps_restante,
            help="Usa o saldo ainda não coberto (valor líquido da unidade após descontos, menos financiamento, FGTS + subsídio e atos), limitado ao teto de Pro Soluto.",
        )
        st.write("")
        j8_ui = float(mps.get("parcela_max_j8") or 0)
        pol_ui = str(d.get("politica", "Direcional"))
        ps_limite_ui2 = float(mps.get("ps_max_efetivo", 0) or 0)
        meses_entrega_unid = meses_ate_entrega(d.get("unid_entrega", ""))
        st.session_state.dados_cliente["meses_ate_entrega"] = meses_entrega_unid
        _ps_opts_f: list[float] = []
        if ps_limite_ui2 > 0:
            _ps_opts_f.append(ps_limite_ui2)
        if u_valor > 0:
            _ps_opts_f.append(max(0.0, v_liquido - f_u_input - fgts_u_input))
        _teto_ps_final = min(_ps_opts_f) if _ps_opts_f else None

        if "_dv_ps_u_key_deferred" in st.session_state:
            st.session_state["ps_u_key"] = st.session_state.pop("_dv_ps_u_key_deferred")

        st.text_input("Valor do Pro Soluto (R$)", key="ps_u_key", placeholder="0,00")
        ps_input_val = clamp_moeda_positiva(
            texto_moeda_para_float(st.session_state.get("ps_u_key")), _teto_ps_final
        )
        st.session_state.dados_cliente["ps_usado"] = ps_input_val
        st.markdown(
            '<p class="inline-ref" style="margin-top:0;margin-bottom:0;line-height:1.45;">'
            "Limite máximo de Pro Soluto: "
            f"<strong>{reais_streamlit_html(fmt_br(ps_limite_ui2))}</strong></p>",
            unsafe_allow_html=True,
        )
        n_min_j8 = None
        if float(ps_input_val or 0) > 0 and j8_ui > 0:
            n_min_j8 = menor_prazo_parcelas_ps_respeitando_j8(
                float(ps_input_val or 0),
                j8_ui,
                pol_ui,
                _prem,
                prazo_max=parc_max_ui,
                meses_entrega=meses_entrega_unid,
            )
        _ps_cmp = round(float(ps_input_val or 0), 2)
        _prev_ps = st.session_state.get("_ps_val_sync_parc_prev")
        if _prev_ps is None or abs(float(_prev_ps) - _ps_cmp) > 0.009:
            st.session_state["_ps_val_sync_parc_prev"] = _ps_cmp
            if n_min_j8 is not None:
                _nm_sync = int(max(1, min(int(n_min_j8), parc_max_ui)))
                st.session_state["parc_ps_key"] = str(_nm_sync)
        if n_min_j8 is not None:
            _n_need = int(max(1, min(int(n_min_j8), parc_max_ui)))
            _cur_pq = texto_inteiro(
                st.session_state.get("parc_ps_key"), default=_n_need, min_v=1, max_v=parc_max_ui
            )
            _cur_pq = int(_cur_pq if _cur_pq is not None else _n_need)
            if _cur_pq < _n_need:
                st.session_state["parc_ps_key"] = str(_n_need)

        st.text_input(
            "Número de parcelas do Pro Soluto (inteiro)",
            key="parc_ps_key",
            placeholder=f"1 a {parc_max_ui}",
        )
        _parc_i = texto_inteiro(st.session_state.get("parc_ps_key"), default=1, min_v=1, max_v=parc_max_ui)
        parc = _parc_i if _parc_i is not None else 1
        st.session_state.dados_cliente["ps_parcelas"] = parc
        v_parc = parcela_ps_para_valor(
            float(ps_input_val or 0),
            parc,
            pol_ui,
            _prem,
            parcela_max_j8=j8_ui if j8_ui > 0 else None,
            meses_entrega=meses_entrega_unid,
        )
        st.session_state.dados_cliente['ps_mensal'] = v_parc
        st.session_state.dados_cliente['ps_mensal_simples'] = (float(ps_input_val or 0) / parc) if parc > 0 else 0.0
        _ps_parc_fmt = reais_streamlit_html(fmt_br(v_parc))
        _ps_j8_fmt = reais_streamlit_html(fmt_br(j8_ui))
        _pmin_par = int(n_min_j8) if n_min_j8 is not None else 1
        _pmax_par = int(parc_max_ui)
        _combo_par_ref: list[str] = [
            "Deve ter, no mínimo, ",
            f"<strong>{html_std.escape(str(_pmin_par))}</strong>",
            " parcelas e, no máximo, ",
            f"<strong>{html_std.escape(str(_pmax_par))}</strong>",
            " parcelas.",
        ]
        if j8_ui > 0:
            _combo_par_ref.extend(
                [
                    " As parcelas devem ser limitadas em ",
                    f"<strong>{_ps_j8_fmt}</strong>",
                    ".",
                ]
            )
        _combo_par_ref.extend(
            [
                " Atualmente, está sendo dividido em ",
                f"<strong>{html_std.escape(str(int(parc)))}x</strong>",
                " de ",
                f"<strong>{_ps_parc_fmt}</strong>",
                ".",
            ]
        )
        st.markdown(
            f'<p class="inline-ref" style="margin:0;line-height:1.45;">{"".join(_combo_par_ref)}</p>',
            unsafe_allow_html=True,
        )
        if float(ps_input_val or 0) > 0 and j8_ui > 0:
            if n_min_j8 is None:
                _dv_alerta_vermelho(
                    "Com este valor de Pro Soluto e o prazo máximo permitido, a prestação pode "
                    "ultrapassar o teto J8. Reduza o PS ou ajuste o perfil."
                )
        ps_capacidade = max(0.0, float(v_parc) * float(parc))
        ps_efetivo = min(float(ps_input_val or 0.0), ps_capacidade)
        aj8 = (
            float(ps_input_val or 0) > 0
            and j8_ui > 0
            and n_min_j8 is not None
            and int(parc) < int(n_min_j8)
        )
        acap = ps_efetivo + 0.01 < float(ps_input_val or 0.0)
        if aj8 or acap:
            if aj8 and acap:
                _dv_alerta_vermelho(
                    f"Com {html_std.escape(str(parc))} parcelas, a mensalidade do Pro Soluto "
                    f"(<strong>{reais_streamlit_html(fmt_br(v_parc))}</strong>/mês) ultrapassa o teto J8 "
                    f"(<strong>{reais_streamlit_html(fmt_br(j8_ui))}</strong>/mês). "
                    f"São necessárias pelo menos {html_std.escape(str(int(n_min_j8)))} parcelas "
                    "para este valor (ou reduza o Pro Soluto). "
                    f"Com essas parcelas, a arrecadação máxima é "
                    f"<strong>{reais_streamlit_html(fmt_br(ps_capacidade))}</strong> "
                    f"(valor informado: <strong>{reais_streamlit_html(fmt_br(ps_input_val))}</strong>)."
                )
            elif aj8:
                _dv_alerta_vermelho(
                    f"Com {html_std.escape(str(parc))} parcelas, a mensalidade do Pro Soluto "
                    f"(<strong>{reais_streamlit_html(fmt_br(v_parc))}</strong>/mês) ultrapassa o teto J8 "
                    f"(<strong>{reais_streamlit_html(fmt_br(j8_ui))}</strong>/mês). "
                    f"Use pelo menos {html_std.escape(str(int(n_min_j8)))} parcelas "
                    "(ou reduza o valor do Pro Soluto)."
                )
            else:
                _dv_alerta_vermelho(
                    f"O valor de Pro Soluto informado é <strong>{reais_streamlit_html(fmt_br(ps_input_val))}</strong>, "
                    f"mas com {html_std.escape(str(parc))} parcelas e mensalidade <strong>{reais_streamlit_html(fmt_br(v_parc))}</strong> "
                    f"a arrecadação máxima é <strong>{reais_streamlit_html(fmt_br(ps_capacidade))}</strong>."
                )
        st.session_state.dados_cliente["ps_usado"] = ps_efetivo

        if u_valor > 0:
            st.markdown("---")
            st.markdown(
                '<h3 class="dv-titulo-secao">Condições comerciais: Volta ao Caixa</h3>',
                unsafe_allow_html=True,
            )
            if "_dv_volta_caixa_key_deferred" in st.session_state:
                st.session_state["volta_caixa_key"] = st.session_state.pop("_dv_volta_caixa_key_deferred")
            st.text_input(
                "Desconto Volta ao Caixa (R$)",
                key="volta_caixa_key",
                placeholder="0,00",
                help="Limitado à folga Volta ao Caixa cadastrada na unidade.",
            )
            _vc_raw_ui = texto_moeda_para_float(st.session_state.get("volta_caixa_key"))
            vc_input_val = (
                max(0.0, min(_vc_raw_ui, vc_ref_top)) if vc_ref_top > 0 else max(0.0, _vc_raw_ui)
            )
            if abs(_vc_raw_ui - vc_input_val) > 0.009:
                st.session_state["_dv_volta_caixa_key_deferred"] = float_para_campo_texto(
                    vc_input_val, vazio_se_zero=True
                )
                st.rerun()
            _vc_pres_ui = max(0.0, vc_ref_top - vc_input_val)
            _v_pos_vcx_ui = max(0.0, u_valor - vc_input_val)
            _vcx_lim = reais_streamlit_html(fmt_br(vc_ref_top))
            _vcx_pres = reais_streamlit_html(fmt_br(_vc_pres_ui))
            _vcx_preco = reais_streamlit_html(fmt_br(u_valor))
            _vcx_pos = reais_streamlit_html(fmt_br(_v_pos_vcx_ui))
            if vc_input_val <= 0.009 and vc_ref_top > 0.009:
                st.markdown(
                    f'<p class="inline-ref" style="margin:0;line-height:1.45;">'
                    f"Foi preservado todo o Volta ao Caixa, no total de <strong>{_vcx_lim}</strong>, "
                    f"gerando um valor final de <strong>{_vcx_pos}</strong>.</p>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<p class="inline-ref" style="margin:0;line-height:1.45;">Há um limite de Volta ao Caixa de '
                    f"<strong>{_vcx_lim}</strong> e está sendo preservado <strong>{_vcx_pres}</strong>. Além disso, a unidade custa <strong>{_vcx_preco}</strong> e, "
                    f"então, seu valor após o Volta ao Caixa é de <strong>{_vcx_pos}</strong>.</p>",
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown(
                '<h3 class="dv-titulo-secao">Condições comerciais: demais descontos</h3>',
                unsafe_allow_html=True,
            )
            if "_dv_outros_descontos_key_deferred" in st.session_state:
                st.session_state["outros_descontos_key"] = st.session_state.pop(
                    "_dv_outros_descontos_key_deferred"
                )
            st.text_input(
                "Outros descontos (R$)",
                key="outros_descontos_key",
                placeholder="0,00",
                help="Descontos adicionais; limitados ao saldo após o Volta ao Caixa.",
            )
            st.text_area(
                "Origem / justificativa dos outros descontos (opcional) (texto)",
                key="outros_descontos_motivo_key",
                height=88,
                placeholder="Ex.: campanha comercial X, ajuste de tabela, condição especial aprovada por…",
                help="Aparece nos resumos (tela, PDF, WhatsApp) para documentar a origem do valor.",
            )
            _out_raw_ui = texto_moeda_para_float(st.session_state.get("outros_descontos_key"))
            outros_desc = max(0.0, _out_raw_ui)
            _max_out_ui = max(0.0, u_valor - vc_input_val)
            if outros_desc > _max_out_ui + 0.009:
                outros_desc = _max_out_ui
                st.session_state["_dv_outros_descontos_key_deferred"] = float_para_campo_texto(
                    outros_desc, vazio_se_zero=True
                )
                st.rerun()
            v_liquido = max(0.0, u_valor - vc_input_val - outros_desc)
            st.markdown(
                f'<div class="dv-campo-resumo-movel" style="margin:0;font-weight:400;color:#111111;text-align:center;line-height:1.45;">'
                f"Valor final da unidade (após todos os descontos): "
                f"<strong>{reais_streamlit_html(fmt_br(v_liquido))}</strong></div>",
                unsafe_allow_html=True,
            )
            st.session_state.dados_cliente["outros_descontos"] = outros_desc
            st.session_state.dados_cliente["outros_descontos_motivo"] = str(
                st.session_state.get("outros_descontos_motivo_key") or ""
            ).strip()
            st.session_state.dados_cliente["valor_final_unidade"] = v_liquido
            st.session_state.dados_cliente["volta_caixa_aplicado"] = vc_input_val

        # Desconto comercial no final: se o fechamento já cobria o líquido anterior, baixar o PS pelo delta do desconto.
        if u_valor > 0:
            # Chave em string (tuplas em session_state podem falhar na igualdade entre reruns).
            _uid_fe = f"{str(d.get('unidade_id') or '').strip()}|{round(float(u_valor or 0), 2)}"
            if str(st.session_state.get("_dv_vliq_trace_uid") or "") != _uid_fe:
                st.session_state.pop("_dv_v_liquido_fechamento_prev", None)
            st.session_state["_dv_vliq_trace_uid"] = _uid_fe
            _ra_fe = max(0.0, texto_moeda_para_float(st.session_state.get("ato_1_key")))
            _rb_fe = max(0.0, texto_moeda_para_float(st.session_state.get("ato_2_key")))
            _rc_fe = max(0.0, texto_moeda_para_float(st.session_state.get("ato_3_key")))
            _rd_fe = (
                max(0.0, texto_moeda_para_float(st.session_state.get("ato_4_key")))
                if not is_emcash
                else 0.0
            )
            _sum_atos_fe = _ra_fe + _rb_fe + _rc_fe + _rd_fe
            _vl_prev_fe = st.session_state.get("_dv_v_liquido_fechamento_prev")
            if _vl_prev_fe is not None:
                try:
                    _vlp = float(_vl_prev_fe)
                except (TypeError, ValueError):
                    _vlp = None
                if _vlp is not None and _vlp > float(v_liquido) + 0.01:
                    _delta_desc_fe = _vlp - float(v_liquido)
                    _T_fe = float(f_u_input) + float(fgts_u_input) + float(ps_efetivo) + _sum_atos_fe
                    if _T_fe >= _vlp - 1.0 and _delta_desc_fe > 0.01:
                        _cut_ps_desc = min(float(ps_efetivo), float(_delta_desc_fe))
                        if _cut_ps_desc > 0.01:
                            ps_efetivo = max(0.0, float(ps_efetivo) - float(_cut_ps_desc))
            st.session_state["_dv_v_liquido_fechamento_prev"] = float(v_liquido)
        else:
            st.session_state.pop("_dv_v_liquido_fechamento_prev", None)
            st.session_state.pop("_dv_vliq_trace_uid", None)

        # Recalcular entrada: quando houver excedente, reduzir primeiro o Pro Soluto.
        # Só ajustar atos se o excedente remanescente continuar positivo após reduzir PS.
        r1_val = max(0.0, texto_moeda_para_float(st.session_state.get("ato_1_key")))
        r2_val = max(0.0, texto_moeda_para_float(st.session_state.get("ato_2_key")))
        r3_val = max(0.0, texto_moeda_para_float(st.session_state.get("ato_3_key")))
        r4_val = max(0.0, texto_moeda_para_float(st.session_state.get("ato_4_key"))) if not is_emcash else 0.0
        sum_ent = r1_val + r2_val + r3_val + r4_val
        excedente_total = (f_u_input + fgts_u_input + ps_efetivo + sum_ent) - v_liquido
        if excedente_total > 0.01:
            reduzir_ps = min(ps_efetivo, excedente_total)
            ps_efetivo = max(0.0, ps_efetivo - reduzir_ps)
            excedente_total -= reduzir_ps
            if excedente_total > 0.01:
                sum_ent = r1_val + r2_val + r3_val + r4_val
                alvo_atos = max(0.0, sum_ent - excedente_total)
                if sum_ent > 0 and alvo_atos >= 0:
                    _kf2 = alvo_atos / sum_ent
                    r1_val *= _kf2
                    r2_val *= _kf2
                    r3_val *= _kf2
                    r4_val *= _kf2
                else:
                    r1_val = r2_val = r3_val = r4_val = 0.0
            _ps_show = float_para_campo_texto(ps_efetivo, vazio_se_zero=True)
            if str(st.session_state.get("ps_u_key") or "") != str(_ps_show):
                st.session_state["_dv_ps_u_key_deferred"] = _ps_show
                st.rerun()
        else:
            # Ex.: PS baixado pelo desconto comercial e excedente já zerado — o input ainda mostrava o PS antigo.
            _ps_show_else = float_para_campo_texto(ps_efetivo, vazio_se_zero=True)
            if str(st.session_state.get("ps_u_key") or "") != str(_ps_show_else):
                st.session_state["_dv_ps_u_key_deferred"] = _ps_show_else
                st.rerun()

        st.session_state.dados_cliente['ato_final'] = r1_val
        st.session_state.dados_cliente['ato_30'] = r2_val
        st.session_state.dados_cliente['ato_60'] = r3_val
        st.session_state.dados_cliente['ato_90'] = r4_val
        total_entrada_cash = r1_val + r2_val + r3_val + r4_val
        st.session_state.dados_cliente['entrada_total'] = total_entrada_cash
        st.session_state.dados_cliente['ps_usado'] = ps_efetivo

        gap_final = v_liquido - f_u_input - fgts_u_input - ps_efetivo - total_entrada_cash
        if abs(gap_final) > 1.0:
            _dv_alerta_vermelho(
                f"Atenção: {'Falta cobrir' if gap_final > 0 else 'Valor excedente de'} "
                f"<strong>{reais_streamlit_html(fmt_br(abs(gap_final)))}</strong>."
            )
        parcela_fin_auto = calcular_parcela_financiamento(f_u_input, prazo_finan, taxa_fin_vigente(d), tab_fin)
        _parc_fin_ui_raw = clamp_moeda_positiva(texto_moeda_para_float(st.session_state.get("parcela_fin_edit_key")), None)
        st.session_state.dados_cliente['parcela_financiamento'] = (
            _parc_fin_ui_raw if _parc_fin_ui_raw > 0 else parcela_fin_auto
        )
        st.markdown('<hr class="dv-avancar-rule" />', unsafe_allow_html=True)
        if st.button(
            "Avançar para Resumo da Simulação",
            type="primary",
            use_container_width=True,
            key="dv_btn_avancar_resumo",
        ):
            if abs(gap_final) <= 1.0:
                st.session_state.passo_simulacao = "summary"
                scroll_to_top()
                st.rerun()
            else:
                _dv_alerta_vermelho(
                    f"Não é possível avançar. Saldo pendente: <strong>{reais_streamlit_html(fmt_br(abs(gap_final)))}</strong>."
                )
        st.markdown('<hr class="dv-avancar-rule" />', unsafe_allow_html=True)
    elif passo == 'summary':
        d = st.session_state.dados_cliente
        _vc_sum = texto_moeda_para_float(st.session_state.get("volta_caixa_key"))
        _vc_sum = max(0.0, _vc_sum)
        try:
            _out_sum = max(0.0, float(d.get("outros_descontos", 0) or 0))
        except (TypeError, ValueError):
            _out_sum = 0.0
        v_emp_total = max(0.0, float(d.get("imovel_valor", 0) or 0))
        try:
            v_final_sum = float(d.get("valor_final_unidade", 0) or 0)
        except (TypeError, ValueError):
            v_final_sum = max(0.0, v_emp_total - _vc_sum - _out_sum)
        _pol_sum_label = "Emcash" if _politica_emcash(d.get("politica")) else "Direcional"

        st.markdown(
            '<h3 class="dv-titulo-secao">Resumo da simulação</h3>',
            unsafe_allow_html=True,
        )
        _nome_cli = str(d.get("nome", "") or "").strip()
        if _nome_cli:
            st.markdown(
                f'<p style="text-align:center;margin:0 0 var(--dv-stack-gap) 0;line-height:1.5;color:#111;font-weight:600;">'
                f"<b>Nome do Cliente ou Imobiliária:</b> {html_std.escape(_nome_cli)}</p>",
                unsafe_allow_html=True,
            )
        _cpf_d = re.sub(r"\D", "", str(d.get("cpf") or ""))
        _cpf_linha = ""
        if len(_cpf_d) == 11:
            _cpf_linha = f"<b>CPF:</b> {_sf_cpf_mascarado_br(_cpf_d)}<br>"
        elif str(d.get("cpf") or "").strip():
            _cpf_linha = f"<b>CPF:</b> {html_std.escape(str(d.get('cpf') or '').strip())}<br>"
        _rank_s = str(d.get("ranking") or "").strip()
        _rank_linha = (
            f"<b>Ranking do cliente:</b> {html_std.escape(_rank_s)}<br>" if _rank_s else ""
        )
        _cliente_inner = (
            f"{_cpf_linha}"
            f"{_rank_linha}"
            f"<b>Renda familiar total:</b> {reais_streamlit_html(fmt_br(d.get('renda', 0)))}<br>"
        )
        _imovel_inner = (
            f"<b>Empreendimento:</b> {html_std.escape(str(d.get('empreendimento_nome') or '—'))}<br>"
            f"<b>Unidade:</b> {html_std.escape(str(d.get('unidade_id') or '—'))}<br>"
            f"<b>Valor de venda (lista):</b> <span style=\"color: #111111; font-weight: 700;\">"
            f"{reais_streamlit_html(fmt_br(v_emp_total))}</span><br>"
        )
        _desc_combinado = _vc_sum + _out_sum
        if _desc_combinado > 0.009:
            _imovel_inner += (
                f"<b>Descontos Concedidos:</b> {reais_streamlit_html(fmt_br(_desc_combinado))}<br>"
            )
        _mot_sum = str(d.get("outros_descontos_motivo") or "").strip()
        if _out_sum > 0.009 and _mot_sum:
            _imovel_inner += (
                f"<b>Origem dos outros descontos:</b> "
                f"<span style=\"color:#334155;\">{html_std.escape(_mot_sum)}</span><br>"
            )
        _imovel_inner += (
            f"<b>Valor final da unidade:</b> <span style=\"color: #111111; font-weight: 700;\">"
            f"{reais_streamlit_html(fmt_br(v_final_sum))}</span><br>"
        )
        if d.get("unid_entrega"):
            _imovel_inner += (
                f"<b>Previsão de entrega:</b> {html_std.escape(str(d.get('unid_entrega')))}<br>"
            )
        if d.get("unid_area"):
            _imovel_inner += (
                f"<b>Área privativa:</b> {html_std.escape(str(d.get('unid_area')))} m²<br>"
            )
        if d.get("unid_tipo"):
            _imovel_inner += f"<b>Tipologia:</b> {html_std.escape(str(d.get('unid_tipo')))}<br>"
        if d.get("unid_endereco") and d.get("unid_bairro"):
            _imovel_inner += (
                f"<b>Localização:</b> {html_std.escape(str(d.get('unid_endereco')))} — "
                f"{html_std.escape(str(d.get('unid_bairro')))}"
            )

        prazo_txt = d.get("prazo_financiamento", 360)
        _amort_res = nome_sistema_amortizacao_completo(str(d.get("sistema_amortizacao", "SAC")))
        _fin_inner = (
            f"<b>Financiamento utilizado:</b> {reais_streamlit_html(fmt_br(d.get('finan_usado', 0)))}<br>"
            f"<b>Sistema de amortização e prazo:</b> {_amort_res} — {prazo_txt} meses<br>"
            f"<b>Parcela estimada do financiamento:</b> "
            f"{reais_streamlit_html(fmt_br(d.get('parcela_financiamento', 0)))}<br>"
            f"<b>FGTS + subsídio:</b> {reais_streamlit_html(fmt_br(d.get('fgts_sub_usado', 0)))}<br>"
        )

        _em_sum = _politica_emcash(d.get("politica"))
        _linha_resumo_ato_90 = (
            ""
            if _em_sum
            else f"<b>Ato 90:</b> {reais_streamlit_html(fmt_br(d.get('ato_90', 0)))}<br>"
        )
        _a1 = float(d.get("ato_final", 0) or 0)
        _a2 = float(d.get("ato_30", 0) or 0)
        _a3 = float(d.get("ato_60", 0) or 0)
        _ent_resumo = float(d.get("entrada_total", 0) or 0) + float(d.get("ps_usado", 0) or 0)
        _nota_emcash_paren = html_std.escape(_EMCASH_NOTA_PARCELAS)
        _entrada_pro_inner = ""
        if _em_sum:
            _entrada_pro_inner += (
                f"<b>Política de Pro Soluto:</b> {html_std.escape(_pol_sum_label)} "
                f"<span style=\"color:#334155;font-weight:400;\">({_nota_emcash_paren})</span><br>"
            )
        else:
            _entrada_pro_inner += f"<b>Política de Pro Soluto:</b> {html_std.escape(_pol_sum_label)}<br>"
        _entrada_pro_inner += (
            f"<b>Pro Soluto (valor):</b> {reais_streamlit_html(fmt_br(d.get('ps_usado', 0)))}<br>"
            f"<b>Número de parcelas do Pro Soluto:</b> {html_std.escape(str(d.get('ps_parcelas')))}<br>"
            f"<b>Mensalidade do Pro Soluto:</b> {reais_streamlit_html(fmt_br(d.get('ps_mensal', 0)))}<br>"
            f"<b>Ato 1 (Entrada Imediata):</b> {reais_streamlit_html(fmt_br(_a1))}<br>"
            f"<b>Ato 30:</b> {reais_streamlit_html(fmt_br(_a2))}<br>"
            f"<b>Ato 60:</b> {reais_streamlit_html(fmt_br(_a3))}<br>"
            f"{_linha_resumo_ato_90}"
            f"<hr style=\"border:0;border-top:1px solid #e2e8f0;margin:var(--dv-stack-gap) 0;\">"
            f"<b>Entrada total (atos e Pro Soluto):</b> {reais_streamlit_html(fmt_br(_ent_resumo))}<br>"
        )

        _cartoes = (
            _html_cartao_resumo_secao("Dados do cliente", _cliente_inner)
            + _html_cartao_resumo_secao("Dados do imóvel", _imovel_inner)
            + _html_cartao_resumo_secao("Financiamento", _fin_inner)
            + _html_cartao_resumo_secao("Entrada e Pro Soluto", _entrada_pro_inner)
        )
        st.markdown(
            f'<div class="dv-summary-stack">{_cartoes}</div>',
            unsafe_allow_html=True,
        )
        _cn_sum = (st.session_state.get("user_name", "") or "").strip()
        if _cn_sum:
            st.markdown(
                f'<p style="text-align:center;margin:0 0 var(--dv-stack-gap) 0;font-weight:600;color:{COR_AZUL_ESC};">'
                f"Consultor: {html_std.escape(_cn_sum)}</p>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<p style="text-align:center;margin:0;color:#64748b;font-style:italic;">'
            f"Simulação em {html_std.escape(str(d.get('data_simulacao', date.today().strftime('%d/%m/%Y'))))}</p>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        if st.button("Opções de resumo (PDF, e-mail e WhatsApp)", use_container_width=True):
            show_export_dialog(d)
        st.markdown("---")
        if st.button("Concluir e salvar simulação", type="primary", use_container_width=True):
            broker_email = st.session_state.get('user_email')
            if broker_email:
                with st.spinner("Gerando documento PDF e enviando para o seu e-mail..."):
                    _vc_save = texto_moeda_para_float(st.session_state.get("volta_caixa_key"))
                    pdf_bytes_auto = gerar_resumo_pdf(d, volta_caixa_val=_vc_save)
                    if pdf_bytes_auto:
                        sucesso_email, msg_email = enviar_email_smtp(
                            broker_email,
                            d.get("nome", "Cliente"),
                            pdf_bytes_auto,
                            {**d, "volta_caixa_aplicado": _vc_save},
                            tipo="corretor",
                        )
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
            except Exception as e:
                _dv_alerta_vermelho_texto(f"Erro ao salvar: {e}")
        if st.button("Voltar à simulação", use_container_width=True):
            st.session_state.passo_simulacao = 'sim'
            scroll_to_top()
            st.rerun()

    st.markdown(
        '<div class="dv-page-tail-spacer" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )


def _secret_opt(key: str) -> str:
    try:
        return str(st.secrets[key] or "").strip()
    except Exception:
        return ""


def _dv_jwt_secret() -> str:
    s = _secret_opt("SIMULADOR_SESSION_SECRET")
    if s:
        return s
    return "dv-dev-insecure-" + hashlib.sha256(b"dv-simulador-dv-v1").hexdigest()[:40]


def _dv_issue_session_token(row: dict, remember_long: bool) -> tuple[str, datetime]:
    """JWT HS256; devolve (token, expires_at_utc) para o cookie."""
    now = datetime.now(timezone.utc)
    ttl = timedelta(days=30) if remember_long else timedelta(hours=10)
    exp_dt = now + ttl
    payload = {
        "sub": str(row.get("Email", "")).strip().lower(),
        "v": 1,
        "exp": int(exp_dt.timestamp()),
        "iat": int(now.timestamp()),
    }
    tok = jwt_lib.encode(payload, _dv_jwt_secret(), algorithm="HS256")
    if isinstance(tok, bytes):
        tok = tok.decode("ascii")
    return str(tok), exp_dt


def _dv_decode_session_token(token: str) -> dict | None:
    try:
        return jwt_lib.decode(
            token,
            _dv_jwt_secret(),
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
            leeway=120,
        )
    except Exception:
        return None


def _dv_row_by_email(df_logins: pd.DataFrame, email: str) -> dict | None:
    em = (email or "").strip().lower()
    if not em or df_logins is None or getattr(df_logins, "empty", True):
        return None
    if "Email" not in df_logins.columns:
        return None
    for _, r in df_logins.iterrows():
        if str(r.get("Email", "")).strip().lower() != em:
            continue
        return {
            "Nome": str(r.get("Nome", "") or "").strip(),
            "Email": str(r.get("Email", "") or "").strip(),
            "Telefone": str(r.get("Telefone", "") or "").strip(),
            "Imobiliaria": str(r.get("Imobiliaria", "") or "").strip(),
            "Cargo": str(r.get("Cargo", "") or "").strip(),
        }
    return None


def _dv_apply_session_from_row(row: dict) -> None:
    st.session_state["logged_in"] = True
    st.session_state["user_name"] = row.get("Nome") or ""
    st.session_state["user_email"] = row.get("Email") or ""
    st.session_state["user_phone"] = row.get("Telefone") or ""
    st.session_state["user_imobiliaria"] = row.get("Imobiliaria") or "Geral"
    st.session_state["user_cargo"] = row.get("Cargo") or ""
    adm_raw = _secret_opt("SIMULADOR_ADM").lower()
    st.session_state["user_is_adm"] = adm_raw in ("1", "true", "yes", "sim")


def _dv_cookie_manager():
    from extra_streamlit_components import CookieManager

    return CookieManager(key=_DV_COOKIE_CM_KEY)


def _dv_persist_after_login(
    row: dict,
    *,
    remember_long: bool,
    remember_email: bool,
    cookie_manager,
) -> None:
    if cookie_manager is None:
        return
    try:
        cm = cookie_manager
        cm.get_all()
        tok, exp_sess = _dv_issue_session_token(row, remember_long)
        cm.set(
            _DV_COOKIE_SESS,
            tok,
            key="dv_ck_set_sess",
            expires_at=exp_sess,
            same_site="lax",
        )
        if remember_email:
            em = str(row.get("Email", "") or "").strip()
            cm.set(
                _DV_COOKIE_EMAIL,
                em,
                key="dv_ck_set_email",
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                same_site="lax",
            )
        else:
            cm.delete(_DV_COOKIE_EMAIL, key="dv_ck_del_email")
    except Exception:
        pass


def _dv_clear_auth_cookies() -> None:
    try:
        cm = _dv_cookie_manager()
        cm.get_all()
        cm.delete(_DV_COOKIE_SESS)
        cm.delete(_DV_COOKIE_EMAIL)
    except Exception:
        pass


def _dv_try_restore_session_from_cookie(df_logins: pd.DataFrame, cookie_manager) -> bool:
    if st.session_state.get("logged_in"):
        return False
    if cookie_manager is None:
        return False
    if df_logins is None or getattr(df_logins, "empty", True):
        return False
    try:
        cm = cookie_manager
        cm.get_all()
        raw = cm.get(_DV_COOKIE_SESS)
        if not raw:
            return False
        pl = _dv_decode_session_token(str(raw))
        if not pl:
            cm.delete(_DV_COOKIE_SESS, key="dv_ck_del_sess_bad")
            return False
        row = _dv_row_by_email(df_logins, str(pl.get("sub") or ""))
        if not row:
            cm.delete(_DV_COOKIE_SESS, key="dv_ck_del_sess_user")
            return False
        _dv_apply_session_from_row(row)
        return True
    except Exception:
        return False


def _sessao_sem_login_defaults() -> None:
    """Acesso direto ao simulador (sem ecrã de login). Corretor/admin opcionais via secrets."""
    st.session_state["logged_in"] = True
    st.session_state.setdefault("user_name", _secret_opt("SIMULADOR_CORRETOR_NOME"))
    st.session_state.setdefault("user_email", _secret_opt("SIMULADOR_CORRETOR_EMAIL"))
    st.session_state.setdefault("user_imobiliaria", "Geral")
    st.session_state.setdefault("user_cargo", "")
    st.session_state.setdefault("user_phone", _secret_opt("SIMULADOR_CORRETOR_TELEFONE"))
    adm_raw = _secret_opt("SIMULADOR_ADM").lower()
    st.session_state["user_is_adm"] = adm_raw in ("1", "true", "yes", "sim")


def main():
    configurar_layout()
    inject_modern_ui_runtime()
    inject_enter_confirma_campo()

    with st.spinner("A carregar o simulador…"):
        (
            df_finan,
            df_estoque,
            df_politicas,
            df_logins,
            _df_cad_hist,
            df_home_banners,
            premissas_dict,
            df_campanhas_texto,
        ) = carregar_dados_sistema()

    _dv_auth_cm = None
    if not st.session_state.get("logged_in"):
        _dv_auth_cm = _dv_try_init_auth_cookie_manager()
        if _dv_try_restore_session_from_cookie(df_logins, _dv_auth_cm):
            st.rerun()

    if not st.session_state.get("logged_in"):
        _render_login_section(df_logins, cookie_manager=_dv_auth_cm)
        st.markdown(
            '<div class="footer dv-login-page-footer">Direcional Engenharia - Rio de Janeiro<br><em>developed by Lucas Maia</em></div>',
            unsafe_allow_html=True,
        )
        return

    with st.sidebar:
        st.caption("Sessão")
        st.caption(str(st.session_state.get("user_email") or ""))
        if st.button("Sair", key="dv_logout_btn"):
            st.session_state["logged_in"] = False
            for _k in (
                "user_name",
                "user_email",
                "user_imobiliaria",
                "user_cargo",
                "user_phone",
                "user_is_adm",
            ):
                st.session_state.pop(_k, None)
            _dv_clear_auth_cookies()
            st.rerun()

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

    aba_simulador_automacao(
        df_finan,
        df_estoque,
        df_politicas,
        premissas_dict,
        df_home_banners=df_home_banners,
        df_campanhas_texto=df_campanhas_texto,
    )

    st.markdown(
        '<div class="footer">Direcional Engenharia - Rio de Janeiro<br><em>developed by Lucas Maia</em></div>',
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    main()
