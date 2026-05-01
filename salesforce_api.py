# -*- coding: utf-8 -*-
"""
Integração Salesforce (simple_salesforce) para classificação de clientes.

Variáveis de ambiente (ou secção [salesforce] no secrets.toml do Streamlit,
injetada por salesforce_streamlit antes das consultas):

  SALESFORCE_USER, SALESFORCE_PASSWORD
  SALESFORCE_TOKEN (opcional — Security Token separado)
  SALESFORCE_CPF_FIELD — API Name do campo CPF (default: CPF_Classificar_Clientes__c)
  SALESFORCE_RANKING_FIELD — API Name do campo que devolve o ranking (default: Ranking_Cliente__c)

Requisito: pip install simple-salesforce
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from simple_salesforce import Salesforce, SalesforceAuthenticationFailed
except ImportError:  # pragma: no cover
    Salesforce = None  # type: ignore[misc, assignment]
    SalesforceAuthenticationFailed = Exception  # type: ignore[misc, assignment]


def normalizar_cpf(cpf: str | None) -> str:
    """Apenas dígitos; vazio se inválido."""
    if cpf is None:
        return ""
    return re.sub(r"\D", "", str(cpf).strip())


def conectar_salesforce(verbose: bool = False) -> Optional[Any]:
    """
    Conexão username/password (+ token opcional), domain login.
    """
    if Salesforce is None:
        if verbose:
            logger.warning("Pacote simple_salesforce não instalado.")
        return None

    username = (os.environ.get("SALESFORCE_USER") or "").strip()
    password = (os.environ.get("SALESFORCE_PASSWORD") or "").strip()
    token = (os.environ.get("SALESFORCE_TOKEN") or "").strip()

    if not username or not password:
        if verbose:
            logger.info("Salesforce: SALESFORCE_USER ou SALESFORCE_PASSWORD ausentes.")
        return None

    try:
        if token:
            sf = Salesforce(
                username=username,
                password=password,
                security_token=token,
                domain="login",
            )
        else:
            sf = Salesforce(username=username, password=password, domain="login")
        if verbose:
            logger.info("Salesforce: conectado como %s", username)
        return sf
    except SalesforceAuthenticationFailed as e:
        logger.warning("Salesforce: falha de autenticação: %s", e)
        return None
    except Exception as e:
        logger.warning("Salesforce: erro ao conectar: %s", e)
        return None


def mapear_ranking_salesforce_para_ui(valor: Any) -> Optional[str]:
    """
    Converte valor vindo do Salesforce (picklist/texto) para uma das opções do simulador.
    """
    if valor is None:
        return None
    s = str(valor).strip()
    if not s:
        return None
    key = re.sub(r"\s+", " ", s.lower())
    # normaliza acentos comuns
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
    # match exato ou substring
    for needle, rank in mapping.items():
        if needle in key_norm or needle in key:
            return rank
    # já vem como DIAMANTE etc.
    up = s.upper().strip()
    opts = ("DIAMANTE", "OURO", "PRATA", "BRONZE", "AÇO", "ACO")
    for o in opts:
        if up == o or up.replace("Ç", "C") == "ACO" and o == "AÇO":
            return "AÇO" if o == "ACO" else o
    if up == "ACO":
        return "AÇO"
    return None


def buscar_ranking_por_cpf(sf: Any, cpf_11: str) -> Optional[str]:
    """
    Consulta um Contact pelo campo de CPF e devolve o ranking mapeado para a UI.
    """
    if len(cpf_11) != 11 or not cpf_11.isdigit():
        return None

    cpf_field = (os.environ.get("SALESFORCE_CPF_FIELD") or "CPF_Classificar_Clientes__c").strip()
    rank_field = (os.environ.get("SALESFORCE_RANKING_FIELD") or "Ranking_Cliente__c").strip()

    # SOQL: CPF só com dígitos — seguro para interpolação
    soql = f"SELECT {rank_field} FROM Contact WHERE {cpf_field} = '{cpf_11}' LIMIT 1"
    try:
        res = sf.query(soql)
        recs = res.get("records") or []
        if not recs:
            return None
        raw = recs[0].get(rank_field)
        return mapear_ranking_salesforce_para_ui(raw)
    except Exception as e:
        logger.warning("Salesforce SOQL falhou (%s): %s", soql[:80], e)
        return None


def classificar_ranking_cpf_11(cpf_11: str) -> tuple[Optional[str], Optional[str]]:
    """
    Conecta (se credenciais existirem), busca ranking pelo CPF já normalizado (11 dígitos).

    Retorna (ranking_ui_ou_None, código_informativo_ou_None).
    Códigos: cpf_incompleto, pacote_ausente, sem_conexao, sem_registo
    """
    cpf = normalizar_cpf(cpf_11)
    if len(cpf) != 11:
        return None, "cpf_incompleto"

    if Salesforce is None:
        return None, "pacote_ausente"

    sf = conectar_salesforce(verbose=False)
    if sf is None:
        return None, "sem_conexao"

    rank = buscar_ranking_por_cpf(sf, cpf)
    if rank is None:
        return None, "sem_registo"
    return rank, None


def classificar_ranking_por_cpf(cpf_raw: str | None) -> tuple[Optional[str], Optional[str]]:
    """Aceita CPF com ou sem máscara; delega a classificar_ranking_cpf_11."""
    cpf = normalizar_cpf(cpf_raw)
    if not cpf:
        return None, None
    return classificar_ranking_cpf_11(cpf)
