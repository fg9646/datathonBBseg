# API Território — tarefas para o quadro

**Status:** pontos 1 a 4 concluídos: contrato, edição congelada e base local de consulta em SQLite. Pontos 5 a 10 pendentes. Serviço HTTP, autenticação e integração ainda não implementados. Hospedagem, limite numérico de chamadas e responsáveis nominais permanecem pendentes.

| Ordem | Tarefa curta | Responsável proposto | Pronto quando… |
|---|---|---|---|
| 1 — concluído | Fechar consulta, acesso e falhas | Enriquecimento + Pipo | POST/JSON por código IBGE, HTTPS/chave por consumidor, três segundos por tentativa e no máximo uma repetição transitória; continuar sem enriquecimento em caso de falha, sinalizando-a. |
| 2 — concluído | Finalizar e versionar contrato e catálogo | Enriquecimento + consumidores | Contrato documental 1.0.0, 18 indicadores, campos, períodos, ausências e erros definidos; vendaval corrigido. |
| 3 — concluído | Validar e congelar a edição inicial dos dados | Enriquecimento | Edição `territorio-2026-10-28-r1`: 180 pares município/indicador, 153 valores disponíveis, 27 ausências explícitas; 1.925 verificações aprovadas, fontes e hashes registrados. |
| 4 — concluído | Preparar a base de consulta | Enriquecimento / responsável pela API | SQLite regenerável com 180 registros, consultas indexadas por município/edição, fontes resolvidas, lacunas preservadas e cadastro auxiliar IBGE. Importação e testes documentados em `api_territorio/README.md`. |
| 5 — pendente | Construir a API | Responsável pela API | Consulta devolver indicadores e metadados conforme o contrato, com acesso protegido. |
| 6 — pendente | Validar dados e comportamentos | Enriquecimento + responsável pela API | Valores conferirem com a edição validada e cenários de lacunas, cobertura e erros passarem. |
| 7 — pendente | Publicar ambiente de teste | Responsável pela API | Hospedagem, limite de chamadas e acesso definidos; endereço acessível ao backend do Pipo. |
| 8 — pendente | Entregar pacote ao Pipo | Enriquecimento + responsável pela API | Lista abaixo entregue, com pendências e responsáveis registrados. |
| 9 — pendente | Validar integração com Pipo | Pipo + equipes do motor/Bússola; apoio do enriquecimento | Consumidores respeitarem unidades, períodos, lacunas e falhas, sem atribuir precisão de endereço aos dados municipais. |
| 10 — pendente | Registrar manutenção e mudanças | Responsáveis pela base, API e consumidores | Frequência de revisão por fonte, suporte e processo de mudanças definidos. |

## Pacote para o Pipo

- [x] Contrato documental 1.0.0 versionado; serviço ainda não implementado.
- [ ] Endereço do ambiente de teste e instruções de acesso; credenciais por canal seguro.
- [x] Catálogo, dez municípios/códigos IBGE, períodos, unidades, fontes e limitações documentados na edição.
- [x] Edição inicial dos dados e referência para conferir os valores: `dados/edicoes/territorio-2026-10-28-r1`.
- [x] Mapeamento do nome antigo de vendaval para o identificador corrigido, em `mapeamento_catalogo.csv`.
- [ ] Exemplos completos: dados disponíveis, lacunas, município sem cobertura e erros.
- [x] Validação dos dados e lacunas documentadas; testes da API permanecem pendentes.
- [ ] Acordo de falhas, limites e contatos de suporte/atualização.

## Regra de trabalho

Pipo pode ajustar a implementação interna preservando o contrato. Alterações no significado dos dados ou na interface devem ser combinadas, documentadas e versionadas com as equipes afetadas. Falha técnica e ausência de dado são situações distintas; nenhuma delas significa risco zero.

**Escopo atual:** concluída a preparação da camada local de consulta por autorização do responsável. Construção do serviço HTTP e integração continuam como próximos pontos; motor, Bússola, pacote em `entregas/` e edição congelada não foram alterados.
