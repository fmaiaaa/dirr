# -*- coding: utf-8 -*-
"""Secrets do Streamlit → os.environ e cache de consulta ranking Salesforce por CPF."""

from __future__ import annotations

import os
from typing import Optional, Tuple

import streamlit as st


def injetar_secrets_salesforce_no_env() -> None:
    try:
        sec = getattr(st, "secrets", None)
        if sec is None:
            return

        def _set(key: str, val) -> None:
            if val is not None and str(val).strip():
                os.environ.setdefault(key, str(val).strip())

        for key in (
            "SALESFORCE_USER",
            "SALESFORCE_PASSWORD",
            "SALESFORCE_TOKEN",
            "SALESFORCE_CPF_FIELD",
            "SALESFORCE_RANKING_FIELD",
        ):
            if hasattr(sec, "get"):
                _set(key, sec.get(key))
        blk = sec.get("salesforce") if hasattr(sec, "get") else None
        if isinstance(blk, dict):
            for k, v in blk.items():
                if str(k).strip():
                    _set(str(k).strip(), v)
    except Exception:
        pass


@st.cache_data(ttl=300, show_spinner=False)
def lookup_ranking_salesforce_cached(cpf11: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Devolve (ranking_ui, código_erro).
    códigos: cpf_incompleto, pacote_ausente, sem_conexao, sem_registo ou None se OK.
    """
    injetar_secrets_salesforce_no_env()
    from simulador_dv.salesforce_api import classificar_ranking_cpf_11

    return classificar_ranking_cpf_11(cpf11)
