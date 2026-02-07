# Instalação das bibliotecas necessárias para o ambiente Colab
!pip install pandas numpy openpyxl gspread google-auth

import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
import warnings
import gspread
from google.auth import default

# Tenta importar google.colab para autenticação
try:
    from google.colab import auth
except ImportError:
    auth = None

# Suprimir avisos de formatação do Excel
warnings.simplefilter(action='ignore', category=UserWarning)

def limpar_moeda(valor):
    """
    Função auxiliar para limpar e converter valores monetários.
    Converte strings formatadas (ex: 'R$ 200.000,00') para float.
    """
    if isinstance(valor, pd.Series):
        return valor.apply(limpar_moeda)

    if pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)

    valor = str(valor).replace('R$', '').replace(' ', '').strip()
    valor = valor.replace('.', '') # Remove milhar
    valor = valor.replace(',', '.') # Virgula para ponto
    try:
        return float(valor)
    except ValueError:
        return 0.0

def identificar_origem(val):
    """Identifica se a unidade é Disponível ou Mirror baseado no texto do status."""
    val = str(val).lower()
    if 'mirror' in val: return 'Mirror'
    if 'dispon' in val: return 'Disponível'
    return 'Outro'

def processar_aba_bd_estoque(df):
    """
    Processa a aba BD Estoque procurando pelas colunas específicas solicitadas.
    """
    print(f"   -> Normalizando dados...")

    mapa_colunas = {}
    col_vagas = None
    col_preco_associativo = None
    col_status = None
    
    # DEBUG: Mostra as primeiras colunas encontradas para ajudar a diagnosticar erro
    cols_encontradas = list(df.columns)
    print(f"   -> DEBUG: Colunas encontradas no arquivo (primeiras 5): {cols_encontradas[:5]}")

    for col in df.columns:
        # Normalização robusta: remove espaços duplos internos e espaços nas pontas
        col_str = " ".join(str(col).strip().split()).lower()

        # Mapeamento exato baseado na lista fornecida pelo usuário
        if col_str == 'identificador':
            mapa_colunas[col] = 'Identificador'
        elif col_str == 'nome do empreendimento':
            mapa_colunas[col] = 'Empreendimento'
        elif col_str == 'quantidade de vagas':
            mapa_colunas[col] = 'Qtd_Vagas'
        elif col_str == 'status da unidade':
            mapa_colunas[col] = 'Status'
        elif col_str == 'preço associativo' or col_str == 'preco associativo':
            mapa_colunas[col] = 'Preco_Associativo'
        elif 'valor final campanha associativo g' in col_str:
            mapa_colunas[col] = 'Valor_Campanha_Fallback'

        # Fallback (caso haja pequenas variações de espaço ou caixa) se ainda não encontrou
        elif 'identificador' in col_str and 'Identificador' not in mapa_colunas.values():
            mapa_colunas[col] = 'Identificador'
        elif 'nome do empreendimento' in col_str and 'Empreendimento' not in mapa_colunas.values():
            mapa_colunas[col] = 'Empreendimento'
        elif 'quantidade de vagas' in col_str and 'Qtd_Vagas' not in mapa_colunas.values():
            mapa_colunas[col] = 'Qtd_Vagas'
        
        # Garante que 'Status da unidade' seja pego com prioridade
        elif 'status da unidade' in col_str and 'Status' not in mapa_colunas.values():
            mapa_colunas[col] = 'Status'
            
        elif ('preço associativo' in col_str or 'preco associativo' in col_str) and 'Preco_Associativo' not in mapa_colunas.values():
             mapa_colunas[col] = 'Preco_Associativo'

    df.rename(columns=mapa_colunas, inplace=True)
    print(f"   -> Colunas mapeadas com sucesso: {list(mapa_colunas.values())}")

    # Define coluna final de valor
    if 'Preco_Associativo' in df.columns:
        df['Valor_Final'] = df['Preco_Associativo']
    elif 'Valor_Campanha_Fallback' in df.columns:
        df['Valor_Final'] = df['Valor_Campanha_Fallback']
    else:
        df['Valor_Final'] = 0.0

    cols_finais = ['Empreendimento', 'Identificador', 'Qtd_Vagas', 'Status', 'Valor_Final']
    for c in cols_finais:
        if c not in df.columns:
            # print(f"Aviso: Coluna {c} não encontrada, preenchendo com NaN")
            df[c] = np.nan

    return df[cols_finais].copy()

def gerar_mensagem_promocional():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando processamento...")

    # IDs da Planilha e da Aba
    sheet_id = '1oPsPhTPo8_w3i9q6akFW4Rov_vxCmr7At94SIn7kwB0'
    gid_alvo = '241609131' 

    df_final = pd.DataFrame()

    # Autenticação Google Colab
    if auth:
        print("Solicitando autenticação do usuário Google (verifique o popup)...")
        try:
            auth.authenticate_user()
            creds, _ = default()
            gc = gspread.authorize(creds)
            
            print(f"Acessando Planilha ID: {sheet_id}")
            sh = gc.open_by_key(sheet_id)
            
            # Localizar a aba correta pelo GID
            worksheet = None
            for ws in sh.worksheets():
                if str(ws.id) == gid_alvo:
                    worksheet = ws
                    print(f"Aba encontrada: {ws.title}")
                    break
            
            if worksheet:
                rows = worksheet.get_all_values()
                if not rows:
                    print("ERRO: A aba selecionada está vazia.")
                    return
                    
                # A primeira linha é o cabeçalho
                df_raw = pd.DataFrame.from_records(rows[1:], columns=rows[0])
                df_final = processar_aba_bd_estoque(df_raw)
                print("Dados carregados com sucesso via Autenticação Google.")
            else:
                print(f"ERRO: Aba com GID {gid_alvo} não encontrada na planilha.")
                return

        except Exception as e:
            print(f"ERRO de autenticação ou leitura: {e}")
            return
    else:
        print("Ambiente não parece ser Google Colab ou biblioteca ausente.")
        return

    if df_final.empty:
        print("Nenhum dado válido extraído.")
        return

    # 3. Limpeza e Filtros
    mask_status = df_final['Status'].astype(str).str.contains(r'Dispon|Mirror', case=False, na=False)
    df_final = df_final[mask_status].copy()
    
    # [FIX] Verifica se o filtro de status retornou vazio
    if df_final.empty:
        print("="*50)
        print("AVISO: Nenhuma unidade encontrada com status 'Disponível' ou 'Mirror'.")
        print("Verifique se a coluna de 'Status' foi identificada corretamente no passo de normalização.")
        print("="*50)
        return

    df_final['Origem'] = df_final['Status'].apply(identificar_origem)
    df_final['Valor_Final'] = df_final['Valor_Final'].apply(limpar_moeda)
    df_final['Qtd_Vagas'] = pd.to_numeric(df_final['Qtd_Vagas'], errors='coerce').fillna(0)
    df_final['Qtd_Final'] = 1

    # 4. Classificação dos Projetos
    def extrair_andar_do_id(identificador):
        match = re.search(r'-(\d{2})', str(identificador))
        if match: return match.group(1)
        return '00'

    def classificar_tipo(row):
        nome = str(row.get('Empreendimento', ''))
        identificador = str(row.get('Identificador', ''))
        vagas = float(row.get('Qtd_Vagas', 0))
        andar = extrair_andar_do_id(identificador)

        if "Nova Caxias Fun" in nome:
            if andar in ['01', '00', '1', '0']: return "Nova Caxias Fun – Garden"
            else: return "Nova Caxias Fun – Tipo"
        if "Norte Clube" in nome: return "Norte Clube"
        if "Florianópolis" in nome: return "Florianópolis"
        if "Itanhangá Green" in nome: return "Itanhangá Green"
        if "Oceânica" in nome: return "Oceânica (com vaga)"
        if "Jerivá" in nome: return "Jerivá Garden"
        if "Parque Iguaçu" in nome: return "Parque Iguaçu"
        if "Recanto Clube" in nome:
            if vagas > 0: return "Recanto Clube (com vaga)"
            return "Recanto Clube (sem vaga)"
        return nome

    df_final['Nome Display'] = df_final.apply(classificar_tipo, axis=1)

    # 5. Configuração de Preços Promocionais
    PRECOS_ALVO = {
        "Parque Iguaçu": 222000,
        "Norte Clube": 213200,
        "Florianópolis": 206000,
        "Itanhangá Green": 239000,
        "Nova Caxias Fun – Tipo": 222000,
        "Nova Caxias Fun – Garden": 235000,
        "Oceânica (com vaga)": 190000,
        "Recanto Clube (com vaga)": 208000,
        "Recanto Clube (sem vaga)": 199000,
        "Jerivá Garden": 265000
    }

    MAPA_TEXTOS = {
        "Parque Iguaçu": "222k",
        "Norte Clube": "de 241k → 213,2k",
        "Florianópolis": "de 226k → 206k",
        "Itanhangá Green": "de 266k → 239k",
        "Nova Caxias Fun – Tipo": "de 238k → 222k",
        "Nova Caxias Fun – Garden": "de 268k → 235k",
        "Oceânica (com vaga)": "de 213k → 190k",
        "Recanto Clube (com vaga)": "de 230k → 208k",
        "Recanto Clube (sem vaga)": "de 227k → 199k (repasse a partir de 2026)",
        "Jerivá Garden": "de 272k → 265k"
    }

    def checar_preco_promocional(row):
        projeto = row['Nome Display']
        valor = row['Valor_Final']
        if projeto in PRECOS_ALVO:
            alvo = PRECOS_ALVO[projeto]
            return abs(valor - alvo) <= 500
        return False

    mask_preco = df_final.apply(checar_preco_promocional, axis=1)
    df_filtrado = df_final[mask_preco].copy()
    
    # [FIX] Verifica se o filtro de preços retornou vazio
    if df_filtrado.empty:
        print("="*50)
        print("AVISO: Nenhuma unidade encontrada dentro das faixas de preço promocionais.")
        print("="*50)
        return

    # 6. Agrupamento
    resumo = df_filtrado.groupby(['Nome Display', 'Origem'])['Qtd_Final'].sum().unstack(fill_value=0)
    if 'Disponível' not in resumo.columns: resumo['Disponível'] = 0
    if 'Mirror' not in resumo.columns: resumo['Mirror'] = 0
    resumo['Total'] = resumo['Disponível'] + resumo['Mirror']
    resumo = resumo.reset_index()

    # 7. Construção da Mensagem
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    # Cabeçalho atualizado conforme solicitado
    texto_intro = f"Bom dia, pessoal! Atualizando as nossas unidades promocionais:\n\n🏷️ Unidades Promocionais\n\n"

    lista_ordenada = [
        "Parque Iguaçu", "Norte Clube", "Florianópolis", "Itanhangá Green",
        "Nova Caxias Fun – Tipo", "Nova Caxias Fun – Garden",
        "Oceânica (com vaga)", "Recanto Clube (com vaga)",
        "Recanto Clube (sem vaga)", "Jerivá Garden"
    ]

    bloco_principal = ""
    for item in lista_ordenada:
        preco_texto = MAPA_TEXTOS.get(item, "")
        dados = resumo[resumo['Nome Display'] == item]

        if not dados.empty:
            total = int(dados['Total'].values[0])
            # FILTRO: Só escreve se houver 1+ unidades
            if total > 0:
                disp = int(dados['Disponível'].values[0])
                mirror = int(dados['Mirror'].values[0])
                bloco_principal += f"* {item}: {preco_texto} ({total} unids: {disp} disponivel + {mirror} mirror)\n"

    texto_regras = """
📌 Regras

* Não válido com VCX
* Não válido com Ato em Triplo
* Exclusivo para vendas normais
* Cliente deve pagar o ato e assinar na hora
"""

    mensagem_final = texto_intro + bloco_principal + texto_regras

    print("=" * 60)
    print("MENSAGEM GERADA AUTOMATICAMENTE:")
    print("=" * 60)
    print(mensagem_final)
    print("=" * 60)

if __name__ == "__main__":
    gerar_mensagem_promocional()
