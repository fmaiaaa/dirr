# -*- coding: utf-8 -*-
"""
Integração Salesforce (simple_salesforce) para classificação de clientes.

Variáveis de ambiente (ou secção [salesforce] no secrets.toml do Streamlit,
injetada por diresimulator antes das consultas):

  No TOML, pode usar chaves curtas: USER, PASSWORD, TOKEN (mapeiam para SALESFORCE_*)
  ou os nomes completos: SALESFORCE_USER, SALESFORCE_PASSWORD,
  SALESFORCE_TOKEN (opcional - Security Token separado),
  SALESFORCE_CPF_FIELD, SALESFORCE_RANKING_FIELD.

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


_SALESFORCE_TOML_ALIAS: dict[str, str] = {
    "USER": "SALESFORCE_USER",
    "PASSWORD": "SALESFORCE_PASSWORD",
    "TOKEN": "SALESFORCE_TOKEN",
    "CPF_FIELD": "SALESFORCE_CPF_FIELD",
    "RANKING_FIELD": "SALESFORCE_RANKING_FIELD",
}


def chave_env_desde_salesforce_toml(k: str) -> str:
    """Mapeia chaves do bloco [salesforce] (USER, PASSWORD, …) para nomes em os.environ."""
    k0 = str(k).strip()
    if not k0:
        return k0
    return _SALESFORCE_TOML_ALIAS.get(k0.upper(), k0)


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


def _cpf_mascarado_br(cpf_digitos: str) -> str:
    """XXX.XXX.XXX-XX a partir de 11 dígitos."""
    return f"{cpf_digitos[0:3]}.{cpf_digitos[3:6]}.{cpf_digitos[6:9]}-{cpf_digitos[9:11]}"


def _soql_escape_literal(val: str) -> str:
    """Evita quebra de SOQL por aspas ou barras no literal."""
    return str(val).replace("\\", "\\\\").replace("'", "\\'")


def consultar_opportunity_ranking_por_cpf(sf: Any, cpf_bruto: str) -> tuple[Optional[dict], Optional[str]]:
    """
    Oportunidade mais recente ligada à Conta cujo Account.CPF__c coincide com o CPF.

    Tenta primeiro o CPF com máscara (comum no SF) e, se não houver registos, só dígitos.
    Retorna (registo_opportunity_ou_None, mensagem_erro_ou_None).
    """
    cpf_digitos = normalizar_cpf(cpf_bruto)
    if not cpf_digitos or len(cpf_digitos) != 11 or not cpf_digitos.isdigit():
        return None, "Informe um CPF válido com 11 dígitos."

    tentativas = [_cpf_mascarado_br(cpf_digitos), cpf_digitos]
    seen: set[str] = set()
    ultimo_erro: Optional[str] = None

    for cpf_lit in tentativas:
        if cpf_lit in seen:
            continue
        seen.add(cpf_lit)
        lit = _soql_escape_literal(cpf_lit)
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
            if registros:
                return registros[0], None
        except Exception as e:
            ultimo_erro = str(e)
            continue

    if ultimo_erro is not None:
        return None, f"Erro ao consultar o Salesforce: {ultimo_erro}"
    return None, "Nenhum registro encontrado para o CPF informado."


def extrair_ranking_ui_de_opportunity(opp: Any) -> dict[str, Any]:
    """
    Normaliza campos da Opportunity (e Account aninhada) para exibição no simulador.
    """
    conta = opp.get("Account") or {}
    raw_acc = conta.get("Ranking__c")
    raw_opp = opp.get("Ranking__c")
    m_acc = mapear_ranking_salesforce_para_ui(raw_acc)
    m_opp = mapear_ranking_salesforce_para_ui(raw_opp)
    texto = m_acc or m_opp or (raw_acc if raw_acc else None) or (raw_opp if raw_opp else None)
    return {
        "ranking_exibir": texto,
        "ranking_score_conta": conta.get("Ranking_Score__c"),
        "ranking_score_opp": opp.get("Ranking_Score__c"),
        "nome_conta": conta.get("Name"),
        "nome_opp": opp.get("Name"),
    }
