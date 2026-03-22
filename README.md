# Simulador STREAMLIT

Cópia organizada do simulador **Streamlit** (pacote `simulador_dv` + assets `static/`).

## Como executar

```bash
cd "Simulador STREAMLIT"
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Copie `.streamlit/secrets.toml.example` para `secrets.toml` e preencha (Google Sheets, etc.), ou use as variáveis esperadas pelo app.

```bash
streamlit run diresimulator.py
```

## Layout

| Caminho | Descrição |
|---------|-----------|
| `diresimulator.py` | Entrada: chama `simulador_dv.app:main`. |
| `simulador_dv/` | Código do simulador (cópia espelhando o pacote na raiz do repositório). |
| `static/` | Imagens/catálogos referenciados pelo app (ex.: galeria). |
| `.streamlit/` | `config.toml` e `secrets.toml` (não versionar segredos). |

A pasta **pai** do pacote deve ser o diretório de trabalho ao rodar o Streamlit, para que caminhos como `static/img/galeria/` resolvam corretamente.

## Nota

O código espelhado em `simulador_dv/` nesta pasta deve ser **sincronizado** manualmente ou por script com o pacote principal na raiz do repositório, quando houver alterações.
