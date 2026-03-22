Constantes e funções de taxas alinhadas ao COMPARADOR TX EMCASH / PREMISSAS.

E4 = (1 + IPCA a.a.)^(1/12) - 1
E1 = B5 (TX EMCASH) + E4 → usado em (1+E1) na parcela do PS (célula I5).
Offset 30% sobre λ (POLITICAS) antes da renda: (K3 - 30%) como no Excel.
Tabela POLITICAS (Excel): colunas A–F usadas no comparador. A: CLASSIFICAÇÃO | B: PROSOLUTO (% VU) | C: FAIXA RENDA | D/E: FX RENDA 1/2 | F: PARCELAS (máx)

Cada linha (EMCASH, DIAMANTE, OURO, …) alimenta o λ da linha 3 do bloco correspondente no COMPARADOR TX EMCASH (ex.: K3 Emcash, X3 Diamante, AJ3 Ouro): IF(B4 < faixa, FX1, FX2). O app usa resolve_politica_row + k3_lambda para reproduzir esse λ por classificação.

Premissas alinhadas à aba PREMISSAS do Excel (SIMULADOR PS DIRE RIO V2). B2/B3: taxas mensais pré/pós (Direcional, encadeamentos PV no Comparador). B4: taxa mensal financiamento Emcash (célula E2 do Comparador TX Emcash). B5, B6: componentes E1 = B5 + E4, E4 = (1+B6)^(1/12)-1 (IPCA a.a. em decimal).

Pro Soluto alinhado ao COMPARADOR TX EMCASH + SIMULADOR PS + POLITICAS.

Referências (excel_extracao_celulas.txt):

I5: (PMT(E2, CF2, B41)-1)(1+E1)
J8: B4 * (K3 - 30%) * (1 - E1)
L8: PV(E2, K2, J8) * -1 (valor presente do fluxo de parcela máxima J8 em K2 meses)
G15: min(int(L), POLITICAS col B * valor unidade)
G14/C43: (K3 - 30%) * B4 (teto parcela simplificado, sem 1-E1)
Lógica em Python espelhando trechos da aba COMPARADOR TX EMCASH + PREMISSAS.

Referências principais (Excel):

E2 = PREMISSAS!B4 (taxa mensal financiamento Emcash)
E3 = PREMISSAS!B6, E4 = (1+E3)^(1/12)-1
E1 = PREMISSAS!B5 + E4
B3: IF(B41=0,0.99, B41 + B41*((1+0.5%)^4-1)) — valor PS ajustado no comparador
PMT(E2, CF2, pv) no Excel usa taxa MENSAL E2 diretamente.
O app legado usa taxa anual em % e converte para mensal com (1+aa/100)^(1/12)-1. Aqui normalizamos: calculamos taxa mensal efetiva do financiamento e convertemos para % a.a. equivalente para alimentar calcular_parcela_financiamento / fluxo.

============================================================================= SISTEMA DE SIMULAÇÃO IMOBILIÁRIA - DIRE RIO V69 (SINGLE SOURCE - UPDATE)
Alinhado com o app Flask (SimuladorDV): mesmo catálogo (JSON), normalização de estoque (Empreendimento, PS_Diamante/PS_Ouro/.../PS_Aco), viabilidade (2*renda + finan + sub + PS_rank) e recomendações IDEAL/SEGURO/FACILITADO.
