# API Território — tarefas para o quadro

**Status:** somente os pontos 1 e 2 concluídos, no âmbito documental. Pontos 3 a 10 pendentes. Sem implementação, congelamento da edição dos dados ou integração. Hospedagem, limite numérico de chamadas e responsáveis nominais serão definidos na etapa operacional.

| Ordem | Tarefa curta | Responsável proposto | Pronto quando… |
|---|---|---|---|
| 1 — concluído | Fechar consulta, acesso e falhas | Enriquecimento + Pipo | POST/JSON por código IBGE, HTTPS/chave por consumidor, três segundos por tentativa e no máximo uma repetição transitória; continuar sem enriquecimento em caso de falha, sinalizando-a. |
| 2 — concluído | Finalizar e versionar contrato e catálogo | Enriquecimento + consumidores | Contrato documental 1.0.0, 18 indicadores, campos, períodos, ausências e erros definidos; vendaval corrigido. |
| 3 — pendente | Validar e congelar a edição inicial dos dados | Enriquecimento | Dez municípios, períodos, valores, fontes, métodos e lacunas conferidos e identificados por edição. |
| 4 — pendente | Preparar a base de consulta | Enriquecimento / responsável pela API | Base permitir consultar município e edição sem ler a planilha durante o atendimento; mapeamentos documentados. |
| 5 — pendente | Construir a API | Responsável pela API | Consulta devolver indicadores e metadados conforme o contrato, com acesso protegido. |
| 6 — pendente | Validar dados e comportamentos | Enriquecimento + responsável pela API | Valores conferirem com a edição validada e cenários de lacunas, cobertura e erros passarem. |
| 7 — pendente | Publicar ambiente de teste | Responsável pela API | Hospedagem, limite de chamadas e acesso definidos; endereço acessível ao backend do Pipo. |
| 8 — pendente | Entregar pacote ao Pipo | Enriquecimento + responsável pela API | Lista abaixo entregue, com pendências e responsáveis registrados. |
| 9 — pendente | Validar integração com Pipo | Pipo + equipes do motor/Bússola; apoio do enriquecimento | Consumidores respeitarem unidades, períodos, lacunas e falhas, sem atribuir precisão de endereço aos dados municipais. |
| 10 — pendente | Registrar manutenção e mudanças | Responsáveis pela base, API e consumidores | Frequência de revisão por fonte, suporte e processo de mudanças definidos. |

## Pacote para o Pipo

- [ ] Contrato e especificação técnica final versionados.
- [ ] Endereço do ambiente de teste e instruções de acesso; credenciais por canal seguro.
- [ ] Catálogo, dez municípios/códigos IBGE, períodos, unidades, fontes e limitações.
- [ ] Edição inicial dos dados e referência para conferir os valores.
- [ ] Mapeamento do nome antigo de vendaval para o identificador corrigido.
- [ ] Exemplos completos: dados disponíveis, lacunas, município sem cobertura e erros.
- [ ] Resultado da validação e lista de pendências conhecidas.
- [ ] Acordo de falhas, limites e contatos de suporte/atualização.

## Regra de trabalho

Pipo pode ajustar a implementação interna preservando o contrato. Alterações no significado dos dados ou na interface devem ser combinadas, documentadas e versionadas com as equipes afetadas. Falha técnica e ausência de dado são situações distintas; nenhuma delas significa risco zero.

**Escopo atual:** documentação e planejamento. Estas tarefas não autorizam, por si só, iniciar a implementação ou alterar o motor e a Bússola.
