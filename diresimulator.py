# -*- coding: utf-8 -*-
"""
Ponto de entrada do Simulador DV (Streamlit).

Execute a partir desta pasta:
  cd "Simulador STREAMLIT"
  streamlit run diresimulator.py

Requer: pasta `simulador_dv` e `static/` ao lado (mesma raiz que este arquivo).
"""
from simulador_dv.app import main

if __name__ == "__main__":
    main()
