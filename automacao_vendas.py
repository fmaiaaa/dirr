# Instalação das bibliotecas (Para o Colab)
!pip install schedule

import urllib.parse
import webbrowser
from datetime import datetime
from IPython.display import Javascript, display

# ==============================================================================
# CONFIGURAÇÃO DA MENSAGEM
# ==============================================================================

# O WhatsApp utiliza '*' para deixar o texto em negrito
MENSAGEM_TEXTO = (
    "*Previsão de Vendas*\n\n"
    "Fala Pessoal, boa noite, tudo bem?\n\n"
    "Passando para lembrar de mandar as previsões do final de semana até amanhã às *10:30* POR FAVOR:\n\n"
    "Segue o link para o forms para previsão de vendas do final de semana: https://forms.gle/HbRBttoVdWWYhrG56"
)

# ==============================================================================
# EXECUÇÃO E REDIRECIONAMENTO
# ==============================================================================

def enviar_agora():
    """Gera o link e abre o WhatsApp imediatamente."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Processando envio...")
    
    # Codifica a mensagem
    texto_encoded = urllib.parse.quote(MENSAGEM_TEXTO)
    link_wa = f"https://api.whatsapp.com/send?text={texto_encoded}"
    
    # Abre no navegador do seu PC
    try:
        webbrowser.open(link_wa)
        print("✅ Navegador aberto com o WhatsApp!")
    except Exception as e:
        print(f"Erro: {e}")

    # Compatibilidade com Colab
    try:
        display(Javascript(f"window.open('{link_wa}', '_blank');"))
    except:
        pass

if __name__ == "__main__":
    enviar_agora()
