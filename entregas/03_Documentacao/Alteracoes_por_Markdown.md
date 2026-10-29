# Alterações por Markdown

Script e schema: 0.1.0 -> 0.2.0. Layout: 192 -> 200 colunas.
Os registros originais são preservados. Nenhuma estimativa nova ou resultado do motor foi inventado.

## Checklist_Ajustes_Pacote_Garrido.md

| Item | Alteração realizada | Evidência |
| --- | --- | --- |
| Ausências | Vazio, espaços e marcadores documentados classificam material/padrão como desconhecidos; NAO_SE_APLICA é estado próprio | Estados ctl_status_* e ocorrências com o valor original |
| Probabilidades | Validação de formato e domínio [0,1], inclusive; ausência separada de zero; inválidos preservados | Detalhe por bem, ocorrências e três contagens por perfil |
| Confiança | Categorias exatas ALTA/MEDIA/BAIXA; ausentes e inválidas identificadas | Duas novas contagens e status no detalhe |
| Reconciliação | Categorias reconhecidas + desconhecidas + inválidas explicam todos os bens considerados | Relatório JSON por base; órfãos contados separadamente |
| Relatório | Ausências e pendências explícitas, sem VALIDADO irrestrito quando há ressalvas | VALIDADO_COM_AUSENCIAS ou VALIDADO_COM_PENDENCIAS, conforme o caso |
| Pacotes originais | Chaves, linhas, bens e somas conferidos novamente, sem misturar desenvolvimento e teste | Relatorio_Qualidade e verificação independente |
| Casos artificiais | Testes reproduzíveis com cópias mínimas das entradas | verificar_ajustes.py; resultados antes/depois no pacote |
| Atualização | Versão do script/schema, documentação e manifesto atualizados | Política, schema, dicionário e Manifesto_SHA256 |

As escolhas de consumo, prioridade de fontes, suficiência, score e dimensionamento permanecem pendentes de alinhamento.
O layout técnico foi congelado nesta versão em seis blocos e quatro categorias: mudanças inesperadas geram erro explícito antes da saída final. Isso não aprova a estratégia futura de integração.

## Proposta_Integracao_Base_Bussola_Motor_atualizado.md

| Tema | Tratamento nesta entrega |
| --- | --- |
| P0–P3 | Documentação ativa usa P0 como encaminhamento, P1 como condição necessária, P2 como adequação/dimensionamento e P3 como refinamento opcional |
| Qualidade versus decisão | Ocorrências de dados não atribuem P0, prioridade de pergunta, elegibilidade ou plano |
| Camadas | Base, perfil da conversa e resultado do motor documentados separadamente; campos reservados continuam vazios |
| Natureza e ausência | Dicionário usa DECLARADO para futuras respostas; ausência, negativo e zero permanecem distintos |
| Rastreabilidade | Valores originais e métodos conhecidos preservados; fórmulas da fonte não fornecidas continuam explicitamente desconhecidas |
| Integração e produto | Campos do motor/ML, revisão da conversa, prioridades por decisão, gatilhos, catálogo e saídas por cobertura continuam para alinhamento com responsáveis |

Alinhamento_Integracao.md detalha responsabilidades e pendências; os dois Markdown fornecidos foram preservados em referencias/.

## Oito colunas adicionadas

- der_quantidade_bens_confianca_desconhecida
- der_quantidade_bens_confianca_invalida
- der_quantidade_bens_probabilidade_valida
- der_quantidade_bens_probabilidade_ausente
- der_quantidade_bens_probabilidade_invalida
- ctl_status_qualidade_dados
- ctl_quantidade_ocorrencias_qualidade
- ctl_ocorrencias_qualidade_json
