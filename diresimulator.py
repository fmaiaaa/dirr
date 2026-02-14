# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V68 (FIX HTML - MAPA FOLIUM - JERIVA VIDEO)
=============================================================================
"""

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
import pytz
import altair as alt
import folium
from streamlit_folium import st_folium

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
# 0. CONSTANTES E UTILITÁRIOS
# =============================================================================
# ID ÚNICO DA PLANILHA "BD Streamlit"
ID_GERAL = "1N00McOjO1O_MuKyQhp-CVhpAet_9Lfq-VqVm1FmPV00"

URL_FINAN = f"https://docs.google.com/spreadsheets/d/{ID_GERAL}/edit#gid=0"
URL_RANKING = f"https://docs.google.com/spreadsheets/d/{ID_GERAL}/edit#gid=0"
URL_ESTOQUE = f"https://docs.google.com/spreadsheets/d/{ID_GERAL}/edit#gid=0"

URL_FAVICON_RESERVA = "https://direcional.com.br/wp-content/uploads/2021/04/cropped-favicon-direcional-32x32.png"

# Paleta de Cores
COR_AZUL_ESC = "#002c5d"
COR_VERMELHO = "#e30613"
COR_FUNDO = "#fcfdfe"
COR_BORDA = "#eef2f6"
COR_TEXTO_MUTED = "#64748b"
COR_INPUT_BG = "#f0f2f6"

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

def fmt_br(valor):
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

def limpar_cpf_visual(valor):
    if pd.isnull(valor) or valor == "": return ""
    v_str = str(valor).strip()
    if v_str.endswith('.0'): v_str = v_str[:-2]
    v_nums = re.sub(r'\D', '', v_str)
    if v_nums: return v_nums.zfill(11)
    return ""

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
            'Mês': m,
            'Valor': parc_fin,
            'Tipo': 'Financiamento',
            'Total': parc_fin + parc_ps + val_ato
        })
        
        # Pro Soluto (se houver)
        if parc_ps > 0:
            fluxo.append({
                'Mês': m,
                'Valor': parc_ps,
                'Tipo': 'Pro Soluto',
                'Total': parc_fin + parc_ps + val_ato
            })
            
        # Atos (se houver)
        if val_ato > 0:
            fluxo.append({
                'Mês': m,
                'Valor': val_ato,
                'Tipo': 'Entrada/Ato',
                'Total': parc_fin + parc_ps + val_ato
            })
    
    return pd.DataFrame(fluxo)

def formatar_link_drive(url):
    """
    Retorna uma tupla: (link_thumbnail, link_full_direct)
    - link_thumbnail: usado na galeria (menor, carrega rápido)
    - link_full_direct: usado no lightbox (link direto do drive, suporta arquivos grandes)
    """
    if "drive.google.com" in url and "/d/" in url:
        try:
            file_id = url.split("/d/")[1].split("/")[0]
            # Thumbnail para o slider
            thumb_link = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
            # Link direto para visualização raw (export=view)
            # Isso é necessário para o lightbox funcionar sem redirecionar para a página HTML do Drive
            full_link = f"https://drive.google.com/uc?export=view&id={file_id}"
            return thumb_link, full_link
        except:
            return url, url
    return url, url

def scroll_to_top():
    js = """<script>var body = window.parent.document.querySelector(".main"); if (body) { body.scrollTop = 0; } window.scrollTo(0, 0);</script>"""
    st.components.v1.html(js, height=0)

# =============================================================================
# 1. CARREGAMENTO DE DADOS
# =============================================================================

@st.cache_data(ttl=300)
def carregar_dados_sistema():
    try:
        if "connections" not in st.secrets:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        conn = st.connection("gsheets", type=GSheetsConnection)
        def limpar_moeda(val): return safe_float_convert(val)

        try:
            df_logins = conn.read(spreadsheet=ID_GERAL, worksheet="BD Logins")
            df_logins.columns = [str(c).strip() for c in df_logins.columns]
            mapa = {}
            for col in df_logins.columns:
                c_low = col.lower()
                if "senha" in c_low: mapa[col] = 'Senha'
                elif "imob" in c_low or "canal" in c_low: mapa[col] = 'Imobiliaria'
                elif "email" in c_low: mapa[col] = 'Email'
                elif "nome" in c_low: mapa[col] = 'Nome'
                elif "cargo" in c_low: mapa[col] = 'Cargo'
                elif "telefone" in c_low: mapa[col] = 'Telefone'
            df_logins = df_logins.rename(columns=mapa)
            df_logins['Email'] = df_logins['Email'].astype(str).str.strip().str.lower()
            df_logins['Senha'] = df_logins['Senha'].astype(str).str.strip()
        except: df_logins = pd.DataFrame(columns=['Email', 'Senha'])

        try: df_cadastros = conn.read(spreadsheet=ID_GERAL, worksheet="BD Simulações")
        except: df_cadastros = pd.DataFrame()
        
        try:
            df_politicas = conn.read(spreadsheet=ID_GERAL, worksheet="BD Ranking")
            df_politicas.columns = [str(c).strip() for c in df_politicas.columns]
            col_class = next((c for c in df_politicas.columns if 'CLASSIFICA' in c.upper() or 'RANKING' in c.upper()), 'CLASSIFICAÇÃO')
            df_politicas = df_politicas.rename(columns={col_class: 'CLASSIFICAÇÃO', 'FAIXA RENDA': 'FAIXA_RENDA', 'FX RENDA 1': 'FX_RENDA_1', 'FX RENDA 2': 'FX_RENDA_2'})
        except: df_politicas = pd.DataFrame()

        try:
            df_finan = conn.read(spreadsheet=ID_GERAL, worksheet="BD Financiamentos")
            df_finan.columns = [str(c).strip() for c in df_finan.columns]
            for col in df_finan.columns: df_finan[col] = df_finan[col].apply(limpar_moeda)
        except: df_finan = pd.DataFrame()

        try:
            df_raw = conn.read(spreadsheet=ID_GERAL, worksheet="BD Estoque Filtrada")
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            
            mapa_estoque = {
                'Nome do Empreendimento': 'Empreendimento',
                'Valor Final Com Kit': 'Valor de Venda',
                'Status da unidade': 'Status',
                'Identificador': 'Identificador',
                'Bairro': 'Bairro',
                'Valor de Avaliação Bancária': 'Valor de Avaliação Bancária'
            }
            
            df_estoque = df_raw.rename(columns=mapa_estoque)
            
            if 'Valor de Venda' not in df_estoque.columns: df_estoque['Valor de Venda'] = 0.0
            if 'Valor de Avaliação Bancária' not in df_estoque.columns: df_estoque['Valor de Avaliação Bancária'] = df_estoque['Valor de Venda']
            if 'Status' not in df_estoque.columns: df_estoque['Status'] = 'Disponível'
            if 'Empreendimento' not in df_estoque.columns: df_estoque['Empreendimento'] = 'N/A'
            
            df_estoque['Valor de Venda'] = df_estoque['Valor de Venda'].apply(limpar_moeda)
            df_estoque['Valor de Avaliação Bancária'] = df_estoque['Valor de Avaliação Bancária'].apply(limpar_moeda)
            
            if 'Status' in df_estoque.columns:
                 df_estoque['Status'] = df_estoque['Status'].astype(str).str.strip()
                 df_estoque['Status'] = df_estoque['Status'].apply(lambda x: 'Disponível' if 'Dispon' in x or 'dispon' in x else x)

            df_estoque = df_estoque[(df_estoque['Valor de Venda'] > 1000)].copy()
            if 'Empreendimento' in df_estoque.columns:
                 df_estoque = df_estoque[df_estoque['Empreendimento'].notnull()]
            
            if 'Identificador' not in df_estoque.columns: 
                df_estoque['Identificador'] = df_estoque.index.astype(str)
            if 'Bairro' not in df_estoque.columns: 
                df_estoque['Bairro'] = 'Rio de Janeiro'

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

        return df_finan, df_estoque, df_politicas, df_logins, df_cadastros
    except Exception as e:
        st.error(f"Erro dados: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# =============================================================================
# 2. MOTOR E FUNÇÕES
# =============================================================================

class MotorRecomendacao:
    def __init__(self, df_finan, df_estoque, df_politicas):
        self.df_finan = df_finan
        self.df_estoque = df_estoque
        self.df_politicas = df_politicas

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

    def calcular_poder_compra(self, renda, finan, fgts_sub, perc_ps, valor_unidade):
        ps = valor_unidade * perc_ps
        return (2 * renda) + finan + fgts_sub + ps, ps

def configurar_layout():
    favicon = URL_FAVICON_RESERVA
    if os.path.exists("favicon.png") and Image:
        try: favicon = Image.open("favicon.png")
        except: pass
    st.set_page_config(page_title="Simulador Direcional Elite", page_icon=favicon, layout="wide")

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', sans-serif;
            color: {COR_AZUL_ESC};
            background-color: {COR_FUNDO};
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
        
        /* LIGHTBOX MODAL CSS */
        .modal {{
            display: none; 
            position: fixed; 
            z-index: 99999; 
            padding-top: 50px; 
            left: 0;
            top: 0;
            width: 100%; 
            height: 100%; 
            overflow: auto; 
            background-color: rgb(0,0,0); 
            background-color: rgba(0,0,0,0.9); 
        }}
        .modal-content {{
            margin: auto;
            display: block;
            width: auto;
            max-width: 95%;
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
            background-color: {COR_INPUT_BG} !important;
            transition: all 0.2s ease-in-out !important;
        }}

        div[data-baseweb="input"]:focus-within {{
            border-color: {COR_VERMELHO} !important;
            box-shadow: 0 0 0 1px {COR_VERMELHO} !important;
            background-color: #ffffff !important;
        }}

        /* --- ALTURA E ALINHAMENTO UNIFICADOS PARA INPUTS --- */
        .stTextInput input, .stNumberInput input, .stDateInput input, div[data-baseweb="select"] > div {{
            height: 48px !important;
            min-height: 48px !important;
            padding: 0 15px !important;
            color: {COR_AZUL_ESC} !important;
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
            background-color: {COR_INPUT_BG} !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            display: flex;
            align-items: center;
        }}

        div[data-testid="stDateInput"] div[data-baseweb="input"] {{
            border: none !important;
            background-color: transparent !important;
        }}

        div[data-testid="stNumberInput"] button {{
             height: 48px !important;
             border-color: #e2e8f0 !important;
             background-color: {COR_INPUT_BG} !important;
             color: {COR_AZUL_ESC} !important;
        }}

        div[data-testid="stNumberInput"] button:hover {{ background-color: #e2e8f0 !important; }}

        .stButton button {{
            font-family: 'Inter', sans-serif;
            border-radius: 8px !important;
            padding: 0 20px !important;
            width: 100% !important;
            height: 60px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 1rem !important;
            transition: all 0.2s ease !important;
        }}
        
        .stButton button:active {{
            transform: scale(0.98);
        }}

        div[data-testid="column"] .stButton button, [data-testid="stSidebar"] .stButton button {{
             min-height: 48px !important;
             height: 48px !important;
             font-size: 0.9rem !important;
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
            background: {COR_INPUT_BG} !important;
            color: {COR_AZUL_ESC} !important;
            border: 1px solid #e2e8f0 !important;
        }}
        .stButton button:not([kind="primary"]:hover) {{
            border-color: #e2e8f0 !important;
        }}
        .stButton button:not([kind="primary"]):hover {{
            border-color: {COR_VERMELHO} !important;
            color: {COR_VERMELHO} !important;
            background: #ffffff !important;
        }}
        
        .stDownloadButton button {{
            background: {COR_INPUT_BG} !important;
            color: {COR_AZUL_ESC} !important;
            border: 1px solid #e2e8f0 !important;
            height: 48px !important;
        }}
        .stDownloadButton button:hover {{
            border-color: {COR_VERMELHO} !important;
            color: {COR_VERMELHO} !important;
            background: #ffffff !important;
        }}

        [data-testid="stSidebar"] .stButton button {{
            padding: 8px 12px !important;
            font-size: 0.75rem !important;
            margin-bottom: 2px !important;
            height: auto !important;
            min-height: 30px !important;
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
            box-shadow: 0 10px 30px -10px rgba(227,6,19,0.1);
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
        .metric-value {{ color: {COR_AZUL_ESC} !important; font-size: 1.8rem; font-weight: 800; font-family: 'Montserrat', sans-serif; }}

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
            box-shadow: 0 12px 24px rgba(0, 44, 93, 0.15);
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
            box-shadow: 0 4px 10px rgba(0, 44, 93, 0.3);
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
            box-shadow: 0 0 0 6px rgba(0, 44, 93, 0.15);
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

        .footer {{ text-align: center; padding: 80px 0; color: {COR_AZUL_ESC} !important; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; opacity: 0.6; }}
        </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step_name):
    steps = [
        {"id": "input", "label": "Dados"},
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
        linha("Valor de Venda", f"R$ {fmt_br(d.get('imovel_valor', 0))}", True)

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
        # SEÇÃO ANOTAÇÕES (preenche espaço)
        # ===============================
        pdf.ln(4)
        secao("ANOTAÇÕES")

        y_inicio = pdf.get_y()
        altura_rodape = 45 # Aumentado para comportar dados do corretor
        altura_disponivel = pdf.h - pdf.b_margin - y_inicio - altura_rodape

        if altura_disponivel > 10:
            pdf.set_fill_color(250, 252, 255)
            pdf.rect(pdf.l_margin, y_inicio, largura_util, altura_disponivel, 'F')

            pdf.set_draw_color(220, 225, 230)
            linha_y = y_inicio + 6
            while linha_y < y_inicio + altura_disponivel - 4:
                pdf.line(
                    pdf.l_margin + 4,
                    linha_y,
                    pdf.l_margin + largura_util - 4,
                    linha_y
                )
                linha_y += 7

            pdf.set_y(y_inicio + altura_disponivel)

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

def enviar_email_smtp(destinatario, nome_cliente, pdf_bytes, dados_cliente):
    if "email" not in st.secrets: return False, "Configuracoes de e-mail nao encontradas."
    try:
        smtp_server = st.secrets["email"]["smtp_server"].strip()
        smtp_port = int(st.secrets["email"]["smtp_port"])
        sender_email = st.secrets["email"]["sender_email"].strip()
        sender_password = st.secrets["email"]["sender_password"].strip().replace(" ", "")
    except Exception as e: return False, f"Erro config: {e}"

    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email; msg['To'] = destinatario; msg['Subject'] = f"Resumo da Simulação - {nome_cliente}"
    
    # Extrair dados para o email
    emp = dados_cliente.get('empreendimento_nome', 'Seu Imóvel')
    unid = dados_cliente.get('unidade_id', '')
    val_venda = fmt_br(dados_cliente.get('imovel_valor', 0))
    entrada = fmt_br(dados_cliente.get('entrada_total', 0))
    finan = fmt_br(dados_cliente.get('finan_usado', 0))
    ps = fmt_br(dados_cliente.get('ps_mensal', 0))
    
    corretor_nome = dados_cliente.get('corretor_nome', 'Direcional')
    corretor_tel = dados_cliente.get('corretor_telefone', '')
    corretor_email = dados_cliente.get('corretor_email', '')
    
    # HTML Content - ESTILIZADO E DETALHADO
    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #002c5d; background-color: #f4f6f8; margin: 0; padding: 20px;">
        <div style="max-width: 650px; margin: auto; background-color: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border-top: 6px solid #e30613;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #002c5d; margin: 0; text-transform: uppercase; letter-spacing: 2px;">Resumo de Simulação</h2>
                <p style="color: #64748b; font-size: 0.9em; margin-top: 5px;">O sonho da sua casa própria está mais perto!</p>
            </div>

            <p>Olá, <strong>{nome_cliente}</strong>!</p>
            <p>Foi um prazer apresentar as oportunidades da Direcional. Veja abaixo um resumo exclusivo da proposta que desenhamos para você:</p>
            
            <div style="background-color: #f8fafc; border-radius: 8px; padding: 20px; margin: 25px 0; border: 1px solid #e2e8f0;">
                <h3 style="color: #002c5d; margin-top: 0; border-bottom: 2px solid #e30613; padding-bottom: 10px; display: inline-block;">{emp}</h3>
                <p style="margin: 5px 0 0 0; color: #64748b; font-weight: bold;">Unidade: {unid}</p>
            </div>

            <table style="width: 100%; border-collapse: separate; border-spacing: 0; margin-bottom: 30px;">
                <tr>
                    <td style="padding: 15px; border-bottom: 1px solid #e2e8f0; color: #64748b;">Valor do Imóvel</td>
                    <td style="padding: 15px; border-bottom: 1px solid #e2e8f0; font-weight: bold; font-size: 1.2em; color: #e30613; text-align: right;">R$ {val_venda}</td>
                </tr>
                <tr>
                    <td style="padding: 15px; border-bottom: 1px solid #e2e8f0; color: #64748b;">Entrada Total</td>
                    <td style="padding: 15px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #002c5d; text-align: right;">R$ {entrada}</td>
                </tr>
                <tr>
                    <td style="padding: 15px; border-bottom: 1px solid #e2e8f0; color: #64748b;">Financiamento Bancário</td>
                    <td style="padding: 15px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #002c5d; text-align: right;">R$ {finan}</td>
                </tr>
                <tr>
                    <td style="padding: 15px; border-bottom: 1px solid #e2e8f0; color: #64748b;">Mensalidade Pro Soluto</td>
                    <td style="padding: 15px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #002c5d; text-align: right;">R$ {ps}</td>
                </tr>
            </table>
            
            <div style="text-align: center; margin: 30px 0;">
                <p style="background-color: #e30613; color: white; display: inline-block; padding: 10px 20px; border-radius: 50px; font-weight: bold; font-size: 0.9em;">ANEXO: PDF DETALHADO DA SIMULAÇÃO</p>
            </div>

            <p style="font-size: 0.9em; color: #64748b; line-height: 1.6;">Este documento é uma simulação preliminar sujeita a análise de crédito e disponibilidade da unidade. Analise com carinho e conte comigo para tirar qualquer dúvida.</p>
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; display: flex; align-items: center;">
                <div style="flex-grow: 1;">
                    <p style="margin: 0; font-weight: bold; color: #002c5d; font-size: 1.1em;">{corretor_nome}</p>
                    <p style="margin: 2px 0; font-size: 0.9em; color: #e30613;">Consultor(a) Direcional</p>
                    <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #64748b;">{corretor_tel}</p>
                    <p style="margin: 2px 0; font-size: 0.9em; color: #64748b;">{corretor_email}</p>
                </div>
                <div style="text-align: right;">
                    <img src="https://direcional.com.br/wp-content/uploads/2021/04/cropped-favicon-direcional-32x32.png" width="40" alt="Direcional">
                </div>
            </div>
        </div>
        <div style="text-align: center; margin-top: 20px; font-size: 0.8em; color: #94a3b8;">
            &copy; {datetime.now().year} Direcional Engenharia. Todos os direitos reservados.
        </div>
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

def tela_login(df_logins):
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br><h3 style='text-align:center;'>LOGIN</h3>", unsafe_allow_html=True)
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_pass")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ACESSAR SISTEMA", type="primary", use_container_width=True):
            if df_logins.empty: st.error("Base de usuários vazia.")
            else:
                user = df_logins[(df_logins['Email'] == email.strip().lower()) & (df_logins['Senha'] == senha.strip())]
                if not user.empty:
                    data = user.iloc[0]
                    st.session_state.update({
                        'logged_in': True, 'user_email': email,
                        'user_name': str(data.get('Nome', '')).strip(),
                        'user_imobiliaria': str(data.get('Imobiliaria', 'Geral')).strip(),
                        'user_cargo': str(data.get('Cargo', '')).strip(),
                        'user_phone': str(data.get('Telefone', '')).strip() # Salva telefone
                    })
                    st.success("Login realizado!"); st.rerun()
                else: st.error("Credenciais inválidas.")

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
    st.markdown("**Enviar por E-mail**")
    email = st.text_input("Endereço de e-mail", placeholder="cliente@exemplo.com")
    if st.button("Enviar Email", use_container_width=True):
        if email and "@" in email:
            # Passando DADOS COMPLETOS para o email HTML
            sucesso, msg = enviar_email_smtp(email, d.get('nome', 'Cliente'), pdf_data, d)
            if sucesso: st.success(msg)
            else: st.error(msg)
        else:
            st.error("E-mail inválido")

# =============================================================================
# APLICAÇÃO PRINCIPAL
# =============================================================================

@st.dialog("Cadastrar Novo Cliente")
def dialog_novo_cliente(motor):
    # Formulário de Cadastro de Novo Cliente
    st.markdown("Preencha os dados do cliente para iniciar a simulação.")
    
    # Recuperar valores da sessão ou usar defaults
    curr_nome = st.session_state.dados_cliente.get('nome', "")
    curr_cpf = st.session_state.dados_cliente.get('cpf', "")
    
    nome = st.text_input("Nome Completo", value=curr_nome, placeholder="Nome Completo", key="in_nome_v28")
    cpf_val = st.text_input("CPF", value=curr_cpf, placeholder="000.000.000-00", key="in_cpf_v3", max_chars=14)
    
    if cpf_val and not validar_cpf(cpf_val):
        st.markdown(f"<small style='color: {COR_VERMELHO};'>CPF inválido</small>", unsafe_allow_html=True)

    d_nasc_default = st.session_state.dados_cliente.get('data_nascimento', date(1990, 1, 1))
    if isinstance(d_nasc_default, str):
        try: d_nasc_default = datetime.strptime(d_nasc_default, '%Y-%m-%d').date()
        except: 
            try: d_nasc_default = datetime.strptime(d_nasc_default, '%d/%m/%Y').date()
            except: d_nasc_default = date(1990, 1, 1)

    data_nasc = st.date_input("Data de Nascimento", value=d_nasc_default, min_value=date(1900, 1, 1), max_value=datetime.now().date(), format="DD/MM/YYYY", key="in_dt_nasc_v3")

    st.markdown("---")
    qtd_part = st.number_input("Participantes na Renda", min_value=1, max_value=4, value=st.session_state.dados_cliente.get('qtd_participantes', 1), step=1, key="qtd_part_v3")

    cols_renda = st.columns(qtd_part)
    renda_total_calc = 0.0
    lista_rendas_input = []
    rendas_anteriores = st.session_state.dados_cliente.get('rendas_lista', [])
    
    # Helper to clear input on empty
    def get_val(idx, default):
        v = float(rendas_anteriores[idx]) if idx < len(rendas_anteriores) else default
        return None if v == 0.0 else v

    for i in range(qtd_part):
        with cols_renda[i]:
            def_val = 3500.0 if i == 0 and not rendas_anteriores else 0.0
            current_val = get_val(i, def_val)
            val_r = st.number_input(f"Renda Part. {i+1}", min_value=0.0, value=current_val, step=100.0, key=f"renda_part_{i}_v3", placeholder="0,00")
            if val_r is None: val_r = 0.0
            renda_total_calc += val_r; lista_rendas_input.append(val_r)

    rank_opts = ["DIAMANTE", "OURO", "PRATA", "BRONZE", "AÇO"]
    curr_ranking = st.session_state.dados_cliente.get('ranking', "DIAMANTE")
    idx_ranking = rank_opts.index(curr_ranking) if curr_ranking in rank_opts else 0
    ranking = st.selectbox("Ranking do Cliente", options=rank_opts, index=idx_ranking, key="in_rank_v28")
    
    politica_ps = st.selectbox("Política de Pro Soluto", ["Direcional", "Emcash"], index=0 if st.session_state.dados_cliente.get('politica') != "Emcash" else 1, key="in_pol_v28")
    social = st.toggle("Fator Social", value=st.session_state.dados_cliente.get('social', False), key="in_soc_v28")
    cotista = st.toggle("Cotista FGTS", value=st.session_state.dados_cliente.get('cotista', True), key="in_cot_v28")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Confirmar e Avançar", type="primary", use_container_width=True):
        # Validação básica
        if not nome.strip(): st.error("Por favor, informe o Nome do Cliente."); return
        if not cpf_val.strip(): st.error("Por favor, informe o CPF do Cliente."); return
        if not validar_cpf(cpf_val): st.error("CPF Inválido."); return
        if renda_total_calc <= 0: st.error("A renda total deve ser maior que zero."); return

        # Salvar estado
        st.session_state.dados_cliente.update({
            'nome': nome, 
            'cpf': limpar_cpf_visual(cpf_val), 
            'data_nascimento': data_nasc, 
            'renda': renda_total_calc, 
            'rendas_lista': lista_rendas_input,
            'social': social, 
            'cotista': cotista, 
            'ranking': ranking, 
            'politica': politica_ps,
            'qtd_participantes': qtd_part
        })

        # Processar lógica de negócio (enquadramento inicial)
        class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
        map_ps_percent = {'EMCASH': 0.25, 'DIAMANTE': 0.25, 'OURO': 0.20, 'PRATA': 0.18, 'BRONZE': 0.15, 'AÇO': 0.12}
        perc_ps_max = map_ps_percent.get(class_b, 0.12)
        prazo_ps_max = 66 if politica_ps == "Emcash" else 84
        limit_ps_r = 0.30
        f_faixa_ref, s_faixa_ref, fx_nome_ref = motor.obter_enquadramento(renda_total_calc, social, cotista, valor_avaliacao=240000)

        st.session_state.dados_cliente.update({
            'perc_ps': perc_ps_max, 
            'prazo_ps_max': prazo_ps_max,
            'limit_ps_renda': limit_ps_r, 
            'finan_f_ref': f_faixa_ref, 
            'sub_f_ref': s_faixa_ref
        })
        
        # Avançar
        st.session_state.passo_simulacao = 'guide'
        st.rerun()

@st.dialog("Buscar Cliente Cadastrado")
def dialog_buscar_cliente(df_cadastros, motor):
    if df_cadastros.empty:
        st.warning("A base de clientes está vazia.")
        return

    clientes_list = df_cadastros['Nome'].unique().tolist() if 'Nome' in df_cadastros.columns else []
    clientes_list.insert(0, "Selecione um cliente...")
    cliente_sel = st.selectbox("Selecione o Cliente:", clientes_list, key="busca_cliente_base")
    
    if cliente_sel != "Selecione um cliente..." and st.button("Carregar Dados", type="primary", use_container_width=True):
        row_cli = df_cadastros[df_cadastros['Nome'] == cliente_sel].iloc[0]
        
        # Helper para extrair float
        def safe_get_float_row(r, k):
            return safe_float_convert(r.get(k, 0))
        
        # Carregar dados na sessão
        rs_load = [safe_get_float_row(row_cli, f'Renda Part. {i}') for i in range(1, 5)]
        qtd_p_load = 1
        for i in range(4, 0, -1):
            if rs_load[i-1] > 0:
                qtd_p_load = i
                break
        
        # Calcula o total da renda
        renda_total_calc = sum(rs_load)

        # Helper para data
        dn_load = row_cli.get('Data de Nascimento')
        try:
            if isinstance(dn_load, str):
                dn_load = datetime.strptime(dn_load, '%Y-%m-%d').date()
        except:
            dn_load = date(1990, 1, 1)

        ranking = row_cli.get('Ranking')
        politica_ps = row_cli.get('Política de Pro Soluto')
        social = str(row_cli.get('Fator Social', '')).lower() == 'sim'
        cotista = str(row_cli.get('Cotista FGTS', '')).lower() == 'sim'

        st.session_state.dados_cliente.update({
            'nome': row_cli.get('Nome'),
            'cpf': row_cli.get('CPF'),
            'data_nascimento': dn_load,
            'qtd_participantes': qtd_p_load,
            'rendas_lista': rs_load,
            'renda': renda_total_calc,
            'ranking': ranking,
            'politica': politica_ps,
            'social': social,
            'cotista': cotista
        })

        # Processar lógica de negócio (enquadramento inicial)
        class_b = 'EMCASH' if politica_ps == "Emcash" else ranking
        map_ps_percent = {'EMCASH': 0.25, 'DIAMANTE': 0.25, 'OURO': 0.20, 'PRATA': 0.18, 'BRONZE': 0.15, 'AÇO': 0.12}
        perc_ps_max = map_ps_percent.get(class_b, 0.12)
        prazo_ps_max = 66 if politica_ps == "Emcash" else 84
        limit_ps_r = 0.30
        f_faixa_ref, s_faixa_ref, fx_nome_ref = motor.obter_enquadramento(renda_total_calc, social, cotista, valor_avaliacao=240000)

        st.session_state.dados_cliente.update({
            'perc_ps': perc_ps_max, 
            'prazo_ps_max': prazo_ps_max,
            'limit_ps_renda': limit_ps_r, 
            'finan_f_ref': f_faixa_ref, 
            'sub_f_ref': s_faixa_ref
        })

        st.toast(f"Dados de {cliente_sel} carregados!", icon="✅")
        st.session_state.passo_simulacao = 'guide'
        st.rerun()

def aba_simulador_automacao(df_finan, df_estoque, df_politicas, df_cadastros):
    passo = st.session_state.get('passo_simulacao', 'input')
    motor = MotorRecomendacao(df_finan, df_estoque, df_politicas)
    if 'dados_cliente' not in st.session_state: st.session_state.dados_cliente = {}

    # --- SIDEBAR PERFIL (ATUALIZADA) ---
    with st.sidebar:
        user_name = st.session_state.get('user_name', 'Corretor').upper()
        user_cargo = st.session_state.get('user_cargo', 'Consultor').upper()
        user_imob = st.session_state.get('user_imobiliaria', 'Direcional').upper()

        st.markdown(f"""
        <div class="sidebar-profile">
            <div class="profile-avatar">{user_name[0] if user_name else 'C'}</div>
            <div class="profile-name" style="font-weight: 800; color: {COR_AZUL_ESC}; font-size: 1.1rem; margin-bottom: 5px;">{user_name}</div>
            <div class="profile-role" style="color: {COR_VERMELHO}; font-weight: 700; font-size: 0.9rem;">{user_cargo}</div>
            <div class="profile-sub" style="color: {COR_AZUL_ESC}; font-size: 0.85rem;">{user_imob}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Navegação")
        if st.button("Simulador", use_container_width=True):
            st.session_state.passo_simulacao = 'input'
            st.rerun()
        if st.button("Galeria de Produtos", use_container_width=True):
            st.session_state.passo_simulacao = 'gallery'
            st.rerun()

        st.markdown("---")
        st.markdown("#### Histórico de Simulações")

        search_term = st.text_input("Buscar cliente...", placeholder="Digite o nome", label_visibility="collapsed")

        try:
            df_h = df_cadastros.copy()
            if not df_h.empty:
                col_corretor = next((c for c in df_h.columns if 'Nome do Corretor' in c), None)
                col_nome_cliente = next((c for c in df_h.columns if c == 'Nome'), None)
                col_data_sim = next((c for c in df_h.columns if 'Data' in c and '/' in str(df_h[c].iloc[0])), None)

                if col_corretor:
                    my_hist = df_h[df_h[col_corretor].astype(str).str.strip().str.upper() == user_name.strip()]
                    if search_term and col_nome_cliente:
                        my_hist = my_hist[my_hist[col_nome_cliente].astype(str).str.contains(search_term, case=False, na=False)]
                    my_hist = my_hist.tail(15).iloc[::-1]

                    if not my_hist.empty:
                        for idx, row in my_hist.iterrows():
                            c_nome = row.get('Nome', 'Cli')
                            c_emp = row.get('Empreendimento Final', 'Emp')
                            c_data = ""
                            if col_data_sim and pd.notnull(row.get(col_data_sim)):
                                try: c_data = str(row.get(col_data_sim)).split('.')[0]
                                except: pass

                            label = f"{c_nome} | {c_emp}"
                            if c_data: label += f" | {c_data}"

                            if st.button(label, key=f"hist_{idx}", use_container_width=True):
                                # Helper para tratamento seguro de floats
                                def safe_get_float(r, k):
                                    return safe_float_convert(r.get(k, 0))
                                
                                # FIX CPF: Remove .0 e zfill 11
                                def fix_cpf_from_row(val):
                                    if pd.isnull(val): return ""
                                    s = str(val)
                                    if s.endswith('.0'): s = s[:-2]
                                    s = re.sub(r'\D', '', s)
                                    if 0 < len(s) < 11:
                                        s = s.zfill(11)
                                    return s

                                # Reconstrução de Rendas e Participantes
                                rs = [safe_get_float(row, f'Renda Part. {i}') for i in range(1, 5)]
                                qtd_p = 1
                                for i in range(4, 0, -1):
                                    if rs[i-1] > 0:
                                        qtd_p = i
                                        break
                                
                                # Calcula o total da renda (CORREÇÃO DO BUG R$ 0,00)
                                renda_total = sum(rs)

                                soc = str(row.get('Fator Social', '')).strip().lower() in ['sim', 's', 'true']
                                cot = str(row.get('Cotista FGTS', '')).strip().lower() in ['sim', 's', 'true']
                                
                                # Recupera Sistema de Amortização com fallback
                                sist_amort = row.get('Sistema de Amortização', 'SAC')
                                if pd.isnull(sist_amort) or str(sist_amort).strip() == '':
                                     sist_amort = 'SAC'

                                st.session_state.dados_cliente = {
                                    'nome': row.get('Nome'), 
                                    'cpf': fix_cpf_from_row(row.get('CPF')),
                                    'data_nascimento': row.get('Data de Nascimento'),
                                    'qtd_participantes': qtd_p,
                                    'rendas_lista': rs,
                                    'renda': renda_total,  # Chave adicionada explicitamente
                                    'ranking': row.get('Ranking'),
                                    'politica': row.get('Política de Pro Soluto'),
                                    'social': soc,
                                    'cotista': cot,
                                    
                                    'empreendimento_nome': row.get('Empreendimento Final'),
                                    'unidade_id': row.get('Unidade Final'),
                                    'imovel_valor': safe_get_float(row, 'Preço Unidade Final'),
                                    'finan_estimado': safe_get_float(row, 'Financiamento Aprovado'),
                                    'fgts_sub': safe_get_float(row, 'Subsídio Máximo'),
                                    
                                    'finan_usado': safe_get_float(row, 'Financiamento Final'),
                                    'fgts_sub_usado': safe_get_float(row, 'FGTS + Subsídio Final'),
                                    'ps_usado': safe_get_float(row, 'Pro Soluto Final'),
                                    
                                    'ps_parcelas': int(float(str(row.get('Número de Parcelas do Pro Soluto', 0)).replace(',','.'))),
                                    'ps_mensal': safe_get_float(row, 'Mensalidade PS'),
                                    'ato_final': safe_get_float(row, 'Ato'),
                                    'ato_30': safe_get_float(row, 'Ato 30'),
                                    'ato_60': safe_get_float(row, 'Ato 60'),
                                    'ato_90': safe_get_float(row, 'Ato 90'),
                                    'prazo_financiamento': int(float(str(row.get('Prazo Financiamento', 360)).replace(',','.'))) if row.get('Prazo Financiamento') else 360,
                                    'sistema_amortizacao': sist_amort # Recupera sistema
                                }
                                
                                st.session_state.dados_cliente['entrada_total'] = sum([
                                    st.session_state.dados_cliente['ato_final'],
                                    st.session_state.dados_cliente['ato_30'],
                                    st.session_state.dados_cliente['ato_60'],
                                    st.session_state.dados_cliente['ato_90']
                                ])

                                keys_to_reset = [
                                    'in_nome_v28', 'in_cpf_v3', 'in_dt_nasc_v3', 'in_genero_v3', 
                                    'qtd_part_v3', 'in_rank_v28', 'in_pol_v28', 'in_soc_v28', 'in_cot_v28',
                                    'fin_u_key', 'fgts_u_key', 'ps_u_key', 'parc_ps_key', 
                                    'ato_1_key', 'ato_2_key', 'ato_3_key', 'ato_4_key'
                                ]
                                for i in range(5): keys_to_reset.append(f"renda_part_{i}_v3")
                                for k in keys_to_reset:
                                    if k in st.session_state: del st.session_state[k]

                                st.session_state.passo_simulacao = 'client_analytics'
                                scroll_to_top()
                                st.rerun()
                    else: st.caption("Nenhum histórico recente.")
                else: st.caption("Coluna de corretor não encontrada.")
            else: st.caption("Sem dados cadastrados.")
        except Exception as e: st.caption(f"Erro histórico: {str(e)}")

    # RENDER PROGRESS BAR
    if passo != 'client_analytics' and passo != 'gallery':
        render_stepper(passo)
        
    # --- GALERIA DE PRODUTOS ---
    if passo == 'gallery':
        st.markdown("### Galeria de Produtos")
        st.markdown("---")
        
        # Obter lista de produtos
        lista_produtos = sorted(list(CATALOGO_PRODUTOS.keys()))
        
        # TABS PARA SELEÇÃO HORIZONTAL (SLIDER-LIKE)
        if not lista_produtos:
            st.warning("Nenhum produto cadastrado na galeria.")
        else:
            # INJETAR JAVASCRIPT E HTML DO MODAL APENAS UMA VEZ
            st.markdown("""
            <div id="myModal" class="modal">
              <span class="close" onclick="closeModal()">&times;</span>
              <img class="modal-content" id="img01">
            </div>

            <script>
            function openModal(src) {
              var modal = document.getElementById("myModal");
              var modalImg = document.getElementById("img01");
              modal.style.display = "block";
              modalImg.src = src;
            }

            function closeModal() {
              document.getElementById("myModal").style.display = "none";
            }
            
            // Fechar ao clicar fora da imagem
            window.onclick = function(event) {
              var modal = document.getElementById("myModal");
              if (event.target == modal) {
                modal.style.display = "none";
              }
            }
            </script>
            """, unsafe_allow_html=True)

            tabs_produtos = st.tabs(lista_produtos)
            
            for aba, prod_key in zip(tabs_produtos, lista_produtos):
                with aba:
                    # Recupera metadados
                    meta = CATALOGO_PRODUTOS[prod_key]
                    
                    st.markdown(f"#### {prod_key}")
                    
                    # SEÇÃO 1: VÍDEO E MAPA (Lado a Lado 50/50)
                    col_vid, col_map = st.columns(2)
                    
                    with col_vid:
                        if meta.get("video"):
                            st.video(meta["video"])
                        else:
                            st.info("Vídeo indisponível.")
                            
                    with col_map:
                        if meta.get("lat") and meta.get("lon"):
                            # Mapa Folium com OpenStreetMap (Mostra ruas e referências)
                            m = folium.Map(location=[meta['lat'], meta['lon']], zoom_start=15, tiles="OpenStreetMap")
                            folium.Marker(
                                [meta['lat'], meta['lon']], 
                                popup=prod_key, 
                                tooltip=prod_key,
                                icon=folium.Icon(color="red", icon="home")
                            ).add_to(m)
                            
                            # Renderiza o mapa com altura fixa para alinhar com o vídeo
                            st_folium(m, height=360, use_container_width=True)
                        else:
                            st.info("Mapa indisponível.")
                    
                    st.markdown("---")
                    
                    # Organizar imagens por categoria (Seções Verticais)
                    imagens_raw = meta.get("imagens", [])
                    categorias = {"IMAGENS ILUSTRATIVAS": [], "PLANTAS": [], "OUTROS": []}
                    link_ficha = None

                    for item in imagens_raw:
                        nome_up = item['nome'].upper()
                        # Identificar Ficha Técnica para o botão
                        if "FICHA" in nome_up or "PDF" in nome_up:
                            link_ficha = item['link']
                            continue
                        
                        # Categorizar
                        if "PLANTA" in nome_up or "MASTERPLAN" in nome_up:
                            categorias["PLANTAS"].append(item)
                        elif "LOGO" in nome_up or "MAPA" in nome_up:
                            categorias["OUTROS"].append(item)
                        else:
                            categorias["IMAGENS ILUSTRATIVAS"].append(item)

                    # SEÇÃO 2: IMAGENS (SLIDER HORIZONTAL COM MINIATURAS E LIGHTBOX)
                    if categorias["IMAGENS ILUSTRATIVAS"]:
                        st.markdown("##### Imagens Ilustrativas")
                        slider_html = '<div class="scrolling-images">'
                        for img in categorias["IMAGENS ILUSTRATIVAS"]:
                            link_thumb, link_full = formatar_link_drive(img['link'])
                            # Usamos onclick para abrir o modal sem redirecionar
                            slider_html += f'<img src="{link_thumb}" alt="{img["nome"]}" title="{img["nome"]}" onclick="openModal(\'{link_full}\')">'
                        slider_html += '</div>'
                        st.markdown(slider_html, unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

                    # SEÇÃO 3: PLANTAS
                    if categorias["PLANTAS"]:
                        st.markdown("##### Plantas e Implantação")
                        slider_html = '<div class="scrolling-images">'
                        for img in categorias["PLANTAS"]:
                            link_thumb, link_full = formatar_link_drive(img['link'])
                            slider_html += f'<img src="{link_thumb}" alt="{img["nome"]}" title="{img["nome"]}" onclick="openModal(\'{link_full}\')">'
                        slider_html += '</div>'
                        st.markdown(slider_html, unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

                    st.markdown("---")
                    
                    # SEÇÃO 4: FICHA TÉCNICA (BOTÃO CENTRALIZADO)
                    if link_ficha:
                        c1, c2, c3 = st.columns([1, 2, 1])
                        with c2:
                            st.link_button("BAIXAR FICHA TÉCNICA", link_ficha, use_container_width=True)

    # --- ABA ANALYTICS (SECURE TAB - ALTAIR) ---
    elif passo == 'client_analytics':
        d = st.session_state.dados_cliente
        
        st.markdown(f"### Painel do Cliente: {d.get('nome', 'Não Informado')}")

        # --- SEÇÃO 1: FICHA DO CLIENTE ---
        with st.container():
            col1, col2, col3 = st.columns(3)
            
            # Format Data Nascimento
            dn = str(d.get('data_nascimento', ''))
            if '-' in dn:
                try: dn = datetime.strptime(dn, '%Y-%m-%d').strftime('%d/%m/%Y')
                except: pass
            
            # Format CPF
            cpf_show = d.get('cpf', '')
            if len(cpf_show) == 11:
                cpf_show = f"{cpf_show[:3]}.{cpf_show[3:6]}.{cpf_show[6:9]}-{cpf_show[9:]}"

            with col1:
                st.markdown(f"""
                <div class="hover-card" style="border-left: 5px solid {COR_AZUL_ESC};">
                    <p style="font-weight: bold; margin-bottom: 10px; color: {COR_AZUL_ESC};">Dados Pessoais</p>
                    <p style="font-size: 0.9rem; margin: 0;">CPF: {cpf_show}</p>
                    <p style="font-size: 0.9rem; margin: 0;">Nascimento: {dn}</p>
                    <p style="font-size: 0.9rem; margin: 0;">Ranking: {d.get('ranking')}</p>
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
            df_fluxo = calcular_fluxo_pagamento_detalhado(v_fin, p_fin, 8.16, sist, v_ps_mensal, p_ps, atos_dict_calc)
            
            # Projeção completa solicitada
            df_view = df_fluxo.copy() 
            
            # Gráfico de Barras Empilhadas com Zoom
            # Cores para cada tipo
            domain_tipo = ['Financiamento', 'Pro Soluto', 'Entrada/Ato']
            range_tipo = [COR_AZUL_ESC, '#f59e0b', COR_VERMELHO] # Azul, Laranja, Vermelho

            zoom = alt.selection_interval(bind='scales')

            bar_chart = alt.Chart(df_view).mark_bar().encode(
                x=alt.X('Mês', title='Mês do Financiamento', axis=alt.Axis(tickMinStep=1)),
                y=alt.Y('Valor', title='Valor (R$)', stack='zero'),
                color=alt.Color('Tipo', scale=alt.Scale(domain=domain_tipo, range=range_tipo), legend=alt.Legend(title="Composição")),
                tooltip=['Mês', 'Tipo', alt.Tooltip('Valor', format=",.2f"), alt.Tooltip('Total', format=",.2f")]
            ).add_params(
                zoom
            ).properties(
                height=400
            )

            st.altair_chart(bar_chart, use_container_width=True)
            st.caption("Use o mouse para dar zoom e arrastar o gráfico. A linha do tempo mostra a soma mensal de todos os componentes.")

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
                    (df_estoque['Empreendimento'] != d.get('empreendimento_nome')) &
                    (df_estoque['Status'] == 'Disponível')
                ].sort_values('Valor de Venda').head(10)
                
                if not similares.empty:
                    # Custom HTML Table without leading indentation - FIX HTML RENDERING
                    # O Streamlit renderiza strings markdown. Se for HTML puro, precisa ser wrapped e unsafe_allow_html=True
                    
                    # Vamos montar o HTML completo de uma só vez para garantir a estrutura
                    cards_html = f"""<div class="scrolling-wrapper">"""
                    
                    for idx, row in similares.iterrows():
                         # Escaping de aspas simples para evitar conflito na f-string
                         emp_name = row['Empreendimento']
                         unid_name = row['Identificador']
                         val_fmt = fmt_br(row['Valor de Venda'])
                         
                         cards_html += f"""<div class="card-item"><div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC}; height: 100%; justify-content: flex-start;"><b style="color:{COR_AZUL_ESC}; font-size:1.1rem;">{emp_name}</b><br><div style="font-size:0.85rem; color:{COR_TEXTO_MUTED}; text-align:center; border-top:1px solid #eee; padding-top:10px; width:100%;"><b>Unidade: {unid_name}</b></div><div class="price-tag" style="font-size:1.4rem; margin:10px 0;">R$ {val_fmt}</div></div></div>"""
                    cards_html += "</div>"
                    
                    # Renderiza o HTML corrigido
                    st.markdown(cards_html, unsafe_allow_html=True)
                else:
                    st.info("Nenhuma outra unidade encontrada nessa faixa de preço (+/- 2500).")
            else:
                st.info("Dados de estoque indisponíveis para comparação.")
        except Exception:
             st.info("Não foi possível carregar oportunidades semelhantes.")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # --- BOTÃO VOLTAR (FULL WIDTH) ---
        st.markdown("""
            <style>
            div.stButton > button {
                width: 100%;
                border-radius: 0px;
                height: 60px;
                font-size: 16px;
                font-weight: bold;
                text-transform: uppercase;
            }
            </style>
        """, unsafe_allow_html=True)

        if st.button("VOLTAR AO SIMULADOR", type="primary", use_container_width=True):
             st.session_state.passo_simulacao = 'input'
             scroll_to_top()
             st.rerun()

    # --- ETAPA 1: INPUT ---
    elif passo == 'input':
        st.markdown("### Selecione uma Opção")
        
        # Estilo para os botões quadrados grandes
        st.markdown(f"""
        <style>
        .big-button {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background-color: white;
            border: 2px solid {COR_BORDA};
            border-radius: 16px;
            padding: 40px 20px;
            height: 250px;
            width: 100%;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        .big-button:hover {{
            transform: translateY(-5px);
            border-color: {COR_VERMELHO};
            box-shadow: 0 10px 20px rgba(227, 6, 19, 0.15);
        }}
        .big-button-icon {{
            font-size: 3rem;
            margin-bottom: 20px;
            color: {COR_VERMELHO};
        }}
        .big-button-text {{
            font-size: 1.2rem;
            font-weight: 700;
            color: {COR_AZUL_ESC};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .big-button-sub {{
            font-size: 0.9rem;
            color: {COR_TEXTO_MUTED};
            margin-top: 10px;
        }}
        </style>
        """, unsafe_allow_html=True)

        col_new, col_search = st.columns(2, gap="large")

        with col_new:
            # Botão Visual (Card)
            st.markdown(f"""
            <div class="big-button">
                <div class="big-button-icon">📝</div>
                <div class="big-button-text">Cadastrar Novo Cliente</div>
                <div class="big-button-sub">Iniciar uma nova simulação do zero</div>
            </div>
            """, unsafe_allow_html=True)
            # Botão Funcional (Invisible overlay logic or simple button below)
            # Streamlit não permite clicar em HTML puro facilmente sem componentes extras.
            # Vamos usar um botão nativo abaixo do card ou apenas o botão nativo estilizado.
            # Para manter simples e funcional, usamos o st.button logo abaixo que aciona o dialog.
            if st.button("Iniciar Cadastro", key="btn_new_client_main", use_container_width=True):
                dialog_novo_cliente(motor)

        with col_search:
            st.markdown(f"""
            <div class="big-button">
                <div class="big-button-icon">🔍</div>
                <div class="big-button-text">Buscar Cliente Cadastrado</div>
                <div class="big-button-sub">Carregar dados de simulação anterior</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Buscar na Base", key="btn_search_client_main", use_container_width=True):
                dialog_buscar_cliente(df_cadastros, motor)

    # --- ETAPA 2: RECOMENDAÇÃO ---
    elif passo == 'guide':
        d = st.session_state.dados_cliente
        st.markdown(f"### Recomendação de Imóveis")

        df_disp_total = df_estoque[df_estoque['Status'] == 'Disponível'].copy()

        if df_disp_total.empty: st.markdown('<div class="custom-alert">Sem produtos viaveis no perfil selecionado.</div>', unsafe_allow_html=True); df_viaveis = pd.DataFrame()
        else:
            def calcular_viabilidade_unidade(row):
                v_venda = row['Valor de Venda']
                v_aval = row['Valor de Avaliação Bancária']
                try: v_venda = float(v_venda)
                except: v_venda = 0.0
                try: v_aval = float(v_aval)
                except: v_aval = v_venda

                fin, sub, fx_n = motor.obter_enquadramento(d.get('renda', 0), d.get('social', False), d.get('cotista', True), v_aval)
                ps_max_val = v_aval * d.get('perc_ps', 0.10)
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
                    # HORIZONTAL SCROLL IMPLEMENTATION - CORRIGIDO PARA RENDERIZAR O HTML CORRETAMENTE
                    # O Streamlit renderiza strings markdown. Se for HTML puro, precisa ser wrapped e unsafe_allow_html=True
                    
                    # Vamos montar o HTML completo de uma só vez para garantir a estrutura
                    cards_html = f"""<div class="scrolling-wrapper">"""
                    
                    for card in final_cards:
                         row = card['row']
                         # Escaping de aspas simples para evitar conflito na f-string
                         emp_name = row['Empreendimento']
                         unid_name = row['Identificador']
                         val_fmt = fmt_br(row['Valor de Venda'])
                         label = card['label']
                         css_badge = card['css']
                         
                         cards_html += f"""<div class="card-item"><div class="recommendation-card" style="border-top: 4px solid {COR_AZUL_ESC}; height: 100%; justify-content: flex-start;"><span style="font-size:0.65rem; color:{COR_AZUL_ESC}; opacity:0.8;">PERFIL</span><br><div style="margin-top:5px; margin-bottom:15px;"><span class="{css_badge}">{label}</span></div><b style="color:{COR_AZUL_ESC}; font-size:1.1rem;">{emp_name}</b><br><div style="font-size:0.85rem; color:{COR_TEXTO_MUTED}; text-align:center; border-top:1px solid #eee; padding-top:10px; width:100%;"><b>Unidade: {unid_name}</b></div><div class="price-tag" style="font-size:1.4rem; margin:10px 0;">R$ {val_fmt}</div></div></div>"""
                    cards_html += "</div>"
                    
                    # Renderiza o HTML corrigido
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
                with f_cols[4]: f_pmax = st.number_input("Preço Máx:", value=None, key="f_pmax_tab_v28", placeholder="0,00")

                df_tab = df_disp_total.copy()
                if f_bairro: df_tab = df_tab[df_tab['Bairro'].isin(f_bairro)]
                if f_emp: df_tab = df_tab[df_tab['Empreendimento'].isin(f_emp)]
                df_tab = df_tab[df_tab['Cobertura'] >= cob_min_val]
                if f_pmax: df_tab = df_tab[df_tab['Valor de Venda'] <= f_pmax]

                if f_ordem == "Menor Preço": df_tab = df_tab.sort_values('Valor de Venda', ascending=True)
                else: df_tab = df_tab.sort_values('Valor de Venda', ascending=False)

                df_tab_view = df_tab.copy()
                df_tab_view['Valor de Venda'] = df_tab_view['Valor de Venda'].apply(fmt_br)
                df_tab_view['Poder_Compra'] = df_tab_view['Poder_Compra'].apply(fmt_br)
                df_tab_view['Cobertura'] = df_tab_view['Cobertura'].apply(lambda x: f"{x:.1f}%")

                st.dataframe(
                    df_tab_view[['Identificador', 'Bairro', 'Empreendimento', 'Valor de Venda', 'Poder_Compra', 'Cobertura']],
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Identificador": st.column_config.TextColumn("Unidade"),
                        "Valor de Venda": st.column_config.TextColumn("Preço (R$)"),
                        "Poder_Compra": st.column_config.TextColumn("Poder Real (R$)"),
                        "Cobertura": st.column_config.TextColumn("Cobertura"),
                    }
                )

        st.markdown("---")
        if st.button("Avançar para Escolha de Unidade", type="primary", use_container_width=True, key="btn_goto_selection"): st.session_state.passo_simulacao = 'selection'; scroll_to_top(); st.rerun()
        st.write("");
        if st.button("Voltar para Dados do Cliente", use_container_width=True, key="btn_pot_v28"): st.session_state.passo_simulacao = 'input'; scroll_to_top(); st.rerun()

    elif passo == 'selection':
         d = st.session_state.dados_cliente
         st.markdown(f"### Escolha de Unidade")
         
         df_disponiveis = df_estoque[df_estoque['Status'] == 'Disponível'].copy()
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
                    return f"{uid} - R$ {fmt_br(u['Valor de Venda'])}"
                uni_escolhida_id = st.selectbox("Escolha a Unidade:", options=current_uni_ids, index=idx_uni, format_func=label_uni, key="sel_uni_new_v3")
                st.session_state.dados_cliente['unidade_id'] = uni_escolhida_id
                if uni_escolhida_id:
                    u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                    v_aval = u_row['Valor de Avaliação Bancária']; v_venda = u_row['Valor de Venda']
                    fin_t, sub_t, _ = motor.obter_enquadramento(d.get('renda', 0), d.get('social', False), d.get('cotista', True), v_aval)
                    poder_t, _ = motor.calcular_poder_compra(d.get('renda', 0), fin_t, sub_t, d.get('perc_ps', 0), v_aval)
                    percentual_cobertura = min(100, max(0, (poder_t / v_venda) * 100))
                    cor_term = calcular_cor_gradiente(percentual_cobertura)
                    st.markdown(f"""<div style="margin-top: 20px; padding: 15px; border: 1px solid #e2e8f0; border-radius: 10px; background-color: #f8fafc; text-align: center;"><p style="margin: 0; font-weight: 700; font-size: 0.9rem; color: #002c5d;">TERMÔMETRO DE VIABILIDADE</p><div style="width: 100%; background-color: #e2e8f0; border-radius: 5px; height: 10px; margin: 10px 0;"><div style="width: {percentual_cobertura}%; background: linear-gradient(90deg, #e30613 0%, #002c5d 100%); height: 100%; border-radius: 5px; transition: width 0.5s;"></div></div><small>{percentual_cobertura:.1f}% Coberto</small></div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Avançar para Fechamento Financeiro", type="primary", use_container_width=True):
                if uni_escolhida_id:
                    u_row = unidades_disp[unidades_disp['Identificador'] == uni_escolhida_id].iloc[0]
                    fin, sub, _ = motor.obter_enquadramento(d.get('renda', 0), d.get('social', False), d.get('cotista', True), u_row['Valor de Avaliação Bancária'])
                    st.session_state.dados_cliente.update({'unidade_id': uni_escolhida_id, 'empreendimento_nome': emp_escolhido, 'imovel_valor': u_row['Valor de Venda'], 'imovel_avaliacao': u_row['Valor de Avaliação Bancária'], 'finan_estimado': fin, 'fgts_sub': sub})
                    st.session_state.passo_simulacao = 'payment_flow'; scroll_to_top(); st.rerun()
            if st.button("Voltar para Recomendação de Imóveis", use_container_width=True): st.session_state.passo_simulacao = 'guide'; scroll_to_top(); st.rerun()

    elif passo == 'payment_flow':
        d = st.session_state.dados_cliente
        st.markdown(f"### Fechamento Financeiro")
        u_valor = d.get('imovel_valor', 0); u_nome = d.get('empreendimento_nome', 'N/A'); u_unid = d.get('unidade_id', 'N/A')
        st.markdown(f'<div class="custom-alert">{u_nome} - {u_unid} (R$ {fmt_br(u_valor)})</div>', unsafe_allow_html=True)
        def get_float_or_none(val): return None if val == 0.0 else val
        if 'finan_usado' not in st.session_state.dados_cliente: st.session_state.dados_cliente['finan_usado'] = d.get('finan_estimado', 0.0)
        if 'fgts_sub_usado' not in st.session_state.dados_cliente: st.session_state.dados_cliente['fgts_sub_usado'] = d.get('fgts_sub', 0.0)
        if 'ps_usado' not in st.session_state.dados_cliente: st.session_state.dados_cliente['ps_usado'] = 0.0
        if 'ato_final' not in st.session_state.dados_cliente: st.session_state.dados_cliente['ato_final'] = 0.0
        if 'ato_30' not in st.session_state.dados_cliente: st.session_state.dados_cliente['ato_30'] = 0.0
        if 'ato_60' not in st.session_state.dados_cliente: st.session_state.dados_cliente['ato_60'] = 0.0
        if 'ato_90' not in st.session_state.dados_cliente: st.session_state.dados_cliente['ato_90'] = 0.0
        
        # Ajuste para campos vazios iniciarem limpos (value=None) se a session não estiver setada
        # Mas queremos persistir os dados se já foram digitados.
        # Estratégia: Se na sessão for 0.0 e o usuário não interagiu, value=None.
        # Porém, para manter a consistência com "voltar", vamos apenas usar value=None se for 0.0 E for a primeira vez.
        # Simplificação solicitada: "não precise apagar os 0,00". Basta iniciar com None se for 0.
        
        def val_input(k):
            v = st.session_state.get(k, 0.0)
            return None if v == 0.0 else v

        # Atualizar session_state com chaves fixas se não existirem
        if 'fin_u_key' not in st.session_state: st.session_state['fin_u_key'] = st.session_state.dados_cliente['finan_usado']
        
        f_val_display = val_input('fin_u_key')
        f_u_input = st.number_input("Financiamento", value=f_val_display, key="fin_u_key", step=1000.0, placeholder="0,00")
        if f_u_input is None: f_u_input = 0.0
        st.session_state.dados_cliente['finan_usado'] = f_u_input
        st.markdown(f'<span class="inline-ref">Financiamento Máximo: R$ {fmt_br(d.get("finan_estimado", 0))}</span>', unsafe_allow_html=True)
        
        idx_prazo = 0 if d.get('prazo_financiamento', 360) == 360 else 1
        prazo_finan = st.selectbox("Prazo Financiamento (Meses)", [360, 420], index=idx_prazo, key="prazo_v3_closed")
        st.session_state.dados_cliente['prazo_financiamento'] = prazo_finan
        idx_tab = 0 if d.get('sistema_amortizacao', "SAC") == "SAC" else 1
        tab_fin = st.selectbox("Sistema de Amortização", ["SAC", "PRICE"], index=idx_tab, key="tab_fin_v28")
        st.session_state.dados_cliente['sistema_amortizacao'] = tab_fin
        taxa_padrao = 8.16; sac_details = calcular_comparativo_sac_price(f_u_input, prazo_finan, taxa_padrao)["SAC"]; price_details = calcular_comparativo_sac_price(f_u_input, prazo_finan, taxa_padrao)["PRICE"]
        st.markdown(f"""<div style="display: flex; justify-content: space-around; margin-bottom: 20px; font-size: 0.85rem; color: #64748b;"><span><b>SAC:</b> R$ {fmt_br(sac_details['primeira'])} a R$ {fmt_br(sac_details['ultima'])} (Juros: R$ {fmt_br(sac_details['juros'])})</span><span><b>PRICE:</b> R$ {fmt_br(price_details['parcela'])} fixas (Juros: R$ {fmt_br(price_details['juros'])})</span></div>""", unsafe_allow_html=True)
        
        if 'fgts_u_key' not in st.session_state: st.session_state['fgts_u_key'] = st.session_state.dados_cliente['fgts_sub_usado']
        fgts_val_display = val_input('fgts_u_key')
        fgts_u_input = st.number_input("FGTS + Subsídio", value=fgts_val_display, key="fgts_u_key", step=1000.0, placeholder="0,00")
        if fgts_u_input is None: fgts_u_input = 0.0
        st.session_state.dados_cliente['fgts_sub_usado'] = fgts_u_input
        st.markdown(f'<span class="inline-ref">Subsídio Máximo: R$ {fmt_br(d.get("fgts_sub", 0))}</span>', unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        st.markdown("#### Distribuição da Entrada (Saldo a Pagar)")
        
        if 'ps_u_key' not in st.session_state: st.session_state['ps_u_key'] = st.session_state.dados_cliente['ps_usado']
        ps_atual = st.session_state.get('ps_u_key', 0.0)
        
        # Calcular saldo considerando o PS atual também como parte da equação se não for atualizado aqui, 
        # mas aqui calculamos o saldo para ATOS.
        # Saldo para atos = Valor - Finan - FGTS - PS
        saldo_para_atos = max(0.0, u_valor - f_u_input - fgts_u_input - ps_atual)
        
        if 'ato_1_key' not in st.session_state: st.session_state['ato_1_key'] = st.session_state.dados_cliente['ato_final']
        if 'ato_2_key' not in st.session_state: st.session_state['ato_2_key'] = st.session_state.dados_cliente['ato_30']
        if 'ato_3_key' not in st.session_state: st.session_state['ato_3_key'] = st.session_state.dados_cliente['ato_60']
        if 'ato_4_key' not in st.session_state: st.session_state['ato_4_key'] = st.session_state.dados_cliente['ato_90']
        is_emcash = (d.get('politica') == 'Emcash')
        
        def distribuir_callback(n_parcelas):
            # Obter valores atuais
            a1 = st.session_state.get('ato_1_key', 0.0) or 0.0
            a2 = st.session_state.get('ato_2_key', 0.0) or 0.0
            a3 = st.session_state.get('ato_3_key', 0.0) or 0.0
            a4 = st.session_state.get('ato_4_key', 0.0) or 0.0
            
            # Verificar se há algum valor preenchido
            total_preenchido = a1 + a2 + a3 + a4
            
            # Mapear quais campos são elegíveis para receber valor (dentro do N solicitado)
            # e quais estão vazios (zerados)
            # A lógica solicitada: "Se todos forem zero, redistribua para todos e se tiver algum diferente de zero, redistribua para o restante."
            
            targets = [] # Lista de keys para distribuir
            current_sum = 0.0
            
            # Definir chaves disponíveis baseado em n_parcelas
            keys_available = ['ato_1_key']
            if n_parcelas >= 2: keys_available.append('ato_2_key')
            if n_parcelas >= 3: keys_available.append('ato_3_key')
            if n_parcelas >= 4 and not is_emcash: keys_available.append('ato_4_key')
            
            # Checar valores atuais nessas chaves
            for k in keys_available:
                val = st.session_state.get(k, 0.0) or 0.0
                if val > 0:
                    current_sum += val
                else:
                    targets.append(k)
            
            if len(targets) == 0 and total_preenchido > 0:
                # Todos os slots do N selecionado estão cheios. 
                # Opção: Redistribuir tudo igualmente (reset) ou avisar?
                # Pelo prompt "Se todos forem zero... se tiver algum diferente... redistribua para o restante".
                # Se não tem restante (todos cheios), vamos assumir redistribuição total (comportamento padrão de reset).
                targets = keys_available
                current_sum = 0.0
            
            if total_preenchido == 0:
                # Caso base: tudo zero, distribui igual
                targets = keys_available
                current_sum = 0.0

            # Saldo a distribuir = Saldo Total Necessário - Já preenchido nos fixos
            # O "Saldo Total Necessário" é o gap original antes de qualquer ato.
            # Gap Original = u_valor - f_u_input - fgts_u_input - ps_atual
            # Mas cuidado: ps_atual vem do input. Se ps mudar, gap muda.
            # O `saldo_para_atos` calculado fora já é (Total - Fin - FGTS - PS).
            # Então o valor total alvo para atos é `saldo_para_atos` (assumindo que o que está digitado no PS é o que fica).
            # Mas se eu já preenchi 1000 num ato, o `saldo_para_atos` visualizado ali no código anterior 
            # é apenas uma var auxiliar. O objetivo é que Soma(Atos) == Gap.
            
            gap_total_atos = max(0.0, u_valor - f_u_input - fgts_u_input - ps_atual)
            remainder = max(0.0, gap_total_atos - current_sum)
            
            if len(targets) > 0:
                val_per_target = remainder / len(targets)
                for k in targets:
                    st.session_state[k] = val_per_target
            
            # Zerar os que estão fora do N (ex: clicou 2x, zera 3 e 4)
            all_keys = ['ato_1_key', 'ato_2_key', 'ato_3_key', 'ato_4_key']
            for k in all_keys:
                if k not in keys_available:
                    st.session_state[k] = 0.0

            # Atualizar dados_cliente para persistência
            st.session_state.dados_cliente['ato_final'] = st.session_state['ato_1_key']
            st.session_state.dados_cliente['ato_30'] = st.session_state['ato_2_key']
            st.session_state.dados_cliente['ato_60'] = st.session_state['ato_3_key']
            st.session_state.dados_cliente['ato_90'] = st.session_state['ato_4_key']

        st.markdown('<label style="font-size: 0.8rem; font-weight: 600;">Distribuir Atos Automaticamente:</label>', unsafe_allow_html=True)
        col_dist1, col_dist2, col_dist3, col_dist4 = st.columns(4)
        with col_dist1: st.button("1x", use_container_width=True, key="btn_d1", on_click=distribuir_callback, args=(1,))
        with col_dist2: st.button("2x", use_container_width=True, key="btn_d2", on_click=distribuir_callback, args=(2,))
        with col_dist3: st.button("3x", use_container_width=True, key="btn_d3", on_click=distribuir_callback, args=(3,))
        with col_dist4: st.button("4x", use_container_width=True, disabled=is_emcash, key="btn_d4", on_click=distribuir_callback, args=(4,))
        
        st.write("") 
        col_a, col_b = st.columns(2)
        with col_a:
            # Usando value=None para limpar visualmente se for 0
            v_a1 = val_input('ato_1_key'); v_a3 = val_input('ato_3_key')
            r1 = st.number_input("Ato (Imediato)", value=v_a1, key="ato_1_key", step=100.0, placeholder="0,00")
            r3 = st.number_input("Ato 60 Dias", value=v_a3, key="ato_3_key", step=100.0, placeholder="0,00")
            if r1 is None: r1 = 0.0
            if r3 is None: r3 = 0.0
            st.session_state.dados_cliente['ato_final'] = r1
            st.session_state.dados_cliente['ato_60'] = r3
        with col_b:
            v_a2 = val_input('ato_2_key'); v_a4 = val_input('ato_4_key')
            r2 = st.number_input("Ato 30 Dias", value=v_a2, key="ato_2_key", step=100.0, placeholder="0,00")
            r4 = st.number_input("Ato 90 Dias", value=v_a4, key="ato_4_key", step=100.0, disabled=is_emcash, placeholder="0,00")
            if r2 is None: r2 = 0.0
            if r4 is None: r4 = 0.0
            st.session_state.dados_cliente['ato_30'] = r2
            st.session_state.dados_cliente['ato_90'] = r4
            
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_ps_val, col_ps_parc = st.columns(2)
        
        u_aval = d.get('imovel_avaliacao', u_valor)
        ps_max_real = u_aval * d.get('perc_ps', 0)
        
        with col_ps_val:
            v_ps_disp = val_input('ps_u_key')
            ps_input_val = st.number_input("Pro Soluto Direcional", value=v_ps_disp, key="ps_u_key", step=1000.0, placeholder="0,00")
            if ps_input_val is None: ps_input_val = 0.0
            st.session_state.dados_cliente['ps_usado'] = ps_input_val
            st.markdown(f'<span class="inline-ref">Limite Permitido ({d.get("perc_ps", 0)*100:.0f}%): R$ {fmt_br(ps_max_real)}</span>', unsafe_allow_html=True)
        with col_ps_parc:
            if 'parc_ps_key' not in st.session_state: st.session_state['parc_ps_key'] = d.get('ps_parcelas', min(60, d.get("prazo_ps_max", 60)))
            parc = st.number_input("Parcelas Pro Soluto", min_value=1, max_value=d.get("prazo_ps_max", 60), key="parc_ps_key"); st.session_state.dados_cliente['ps_parcelas'] = parc
            st.markdown(f'<span class="inline-ref">Prazo Máximo: {d.get("prazo_ps_max", 0)} meses</span>', unsafe_allow_html=True)
        
        v_parc = ps_input_val / parc if parc > 0 else 0
        st.session_state.dados_cliente['ps_mensal'] = v_parc
        total_entrada_cash = r1 + r2 + r3 + r4
        st.session_state.dados_cliente['entrada_total'] = total_entrada_cash
        gap_final = u_valor - f_u_input - fgts_u_input - ps_input_val - total_entrada_cash
        
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        fin1, fin2, fin3 = st.columns(3)
        with fin1: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_AZUL_ESC};"><b>VALOR DO IMÓVEL</b><br>R$ {fmt_br(u_valor)}</div>""", unsafe_allow_html=True)
        with fin2: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {COR_VERMELHO};"><b>MENSALIDADE PS</b><br>R$ {fmt_br(v_parc)} ({parc}x)</div>""", unsafe_allow_html=True)
        cor_saldo = COR_AZUL_ESC if abs(gap_final) <= 1.0 else COR_VERMELHO
        with fin3: st.markdown(f"""<div class="fin-box" style="border-top: 6px solid {cor_saldo};"><b>SALDO A COBRIR</b><br>R$ {fmt_br(gap_final)}</div>""", unsafe_allow_html=True)
        if abs(gap_final) > 1.0: st.error(f"Atenção: {'Falta cobrir' if gap_final > 0 else 'Valor excedente de'} R$ {fmt_br(abs(gap_final))}.")
        parcela_fin = calcular_parcela_financiamento(f_u_input, prazo_finan, 8.16, tab_fin)
        st.session_state.dados_cliente['parcela_financiamento'] = parcela_fin
        st.markdown("---")
        if st.button("Avançar para Resumo da Simulação", type="primary", use_container_width=True):
            if abs(gap_final) <= 1.0: st.session_state.passo_simulacao = 'summary'; scroll_to_top(); st.rerun()
            else: st.error(f"Não é possível avançar. Saldo pendente: R$ {fmt_br(gap_final)}")
        if st.button("Voltar para Escolha de Unidade", use_container_width=True): st.session_state.passo_simulacao = 'selection'; scroll_to_top(); st.rerun()

    elif passo == 'summary':
        d = st.session_state.dados_cliente
        st.markdown(f"### Resumo da Simulação - {d.get('nome', 'Cliente')}")
        st.markdown(f'<div class="summary-header">DADOS DO IMÓVEL</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="summary-body"><b>Empreendimento:</b> {d.get('empreendimento_nome')}<br><b>Unidade:</b> {d.get('unidade_id')}<br><b>Valor de Venda:</b> <span style="color: {COR_VERMELHO}; font-weight: 800;">R$ {fmt_br(d.get('imovel_valor', 0))}</span></div>""", unsafe_allow_html=True)
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
                        sucesso_email, msg_email = enviar_email_smtp(broker_email, d.get('nome', 'Cliente'), pdf_bytes_auto, d)
                        if sucesso_email: st.toast("PDF enviado para seu e-mail com sucesso!", icon="📧")
                        else: st.toast(f"Falha no envio automático: {msg_email}", icon="⚠️")
            try:
                conn_save = st.connection("gsheets", type=GSheetsConnection)
                aba_destino = 'BD Simulações' # Corrigido para a nova aba
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
                    "Quantidade Parcelas Pro Soluto": d.get('ps_parcelas', 0)
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
        if st.button("Voltar para Fechamento Financeiro", use_container_width=True): st.session_state.passo_simulacao = 'payment_flow'; scroll_to_top(); st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Botão Sair fora da coluna para herdar estilo grande
    if st.button("Sair do Sistema", key="btn_logout_bottom", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

def main():
    configurar_layout()
    df_finan, df_estoque, df_politicas, df_logins, df_cadastros = carregar_dados_sistema()
    logo_src = URL_FAVICON_RESERVA
    if os.path.exists("favicon.png"):
        try:
            with open("favicon.png", "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                logo_src = f"data:image/png;base64,{encoded}"
        except: pass
    st.markdown(f'''<div class="header-container"><img src="{logo_src}" style="position: absolute; top: 30px; left: 40px; height: 50px;"><div class="header-title">SIMULADOR IMOBILIÁRIO DV</div><div class="header-subtitle">Sistema de Gestão de Vendas e Viabilidade Imobiliária</div></div>''', unsafe_allow_html=True)

    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

    if not st.session_state['logged_in']: tela_login(df_logins)
    else: aba_simulador_automacao(df_finan, df_estoque, df_politicas, df_cadastros)

    st.markdown(f'<div class="footer">Direcional Engenharia - Rio de Janeiro | Developed by Lucas Maia</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
