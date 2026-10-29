# API Território — tarefas para o quadro

**Status:** pontos 1 a 5 concluídos na feature da API: contrato, edição congelada, SQLite e endpoint autenticado. Pontos 6 a 10 pendentes. Testes locais executados; publicação externa e integração ainda não realizadas. A API deve continuar gratuita, inclusive na escolha da hospedagem.

| Ordem | Tarefa curta | Responsável proposto | Pronto quando… |
|---|---|---|---|
| 1 — concluído | Fechar consulta, acesso e falhas | Enriquecimento + Pipo | POST/JSON por código IBGE, HTTPS/chave por consumidor, três segundos por tentativa e no máximo uma repetição transitória; continuar sem enriquecimento em caso de falha, sinalizando-a. |
| 2 — concluído | Finalizar e versionar contrato e catálogo | Enriquecimento + consumidores | Contrato documental 1.0.0, 18 indicadores, campos, períodos, ausências e erros definidos; vendaval corrigido. |
| 3 — concluído | Validar e congelar a edição inicial dos dados | Enriquecimento | Edição `territorio-2026-10-28-r1`: 180 pares município/indicador, 153 valores disponíveis, 27 ausências explícitas; 1.925 verificações aprovadas, fontes e hashes registrados. |
| 4 — concluído | Preparar a base de consulta | Enriquecimento / responsável pela API | SQLite regenerável com 180 registros, consultas indexadas por município/edição, fontes resolvidas, lacunas preservadas e cadastro auxiliar IBGE. Importação e testes documentados em `api_territorio/README.md`. |
| 5 — concluído | Construir a API | Responsável pela API | Endpoint POST/JSON implementado com chave por consumidor, HTTPS, validação, limites e erros; testes e exemplos em `api_territorio/HTTP.md`. Sem publicação ou integração. |
| 6 — pendente | Validar dados e comportamentos | Enriquecimento + responsável pela API | Valores conferirem com a edição validada e cenários de lacunas, cobertura e erros passarem. |
| 7 — pendente | Publicar ambiente de teste | Responsável pela API | Hospedagem, limite de chamadas e acesso definidos; endereço acessível ao backend do Pipo. |
| 8 — pendente | Entregar pacote ao Pipo | Enriquecimento + responsável pela API | Lista abaixo entregue, com pendências e responsáveis registrados. |
| 9 — pendente | Validar integração com Pipo | Pipo + equipes do motor/Bússola; apoio do enriquecimento | Consumidores respeitarem unidades, períodos, lacunas e falhas, sem atribuir precisão de endereço aos dados municipais. |
| 10 — pendente | Registrar manutenção e mudanças | Responsáveis pela base, API e consumidores | Frequência de revisão por fonte, suporte e processo de mudanças definidos. |

## Pacote para o Pipo

- [x] Contrato 1.0.0 e implementação HTTP na feature; publicação ainda pendente.
- [ ] Endereço do ambiente de teste e instruções de acesso; credenciais por canal seguro.
- [x] Catálogo, dez municípios/códigos IBGE, períodos, unidades, fontes e limitações documentados na edição.
- [x] Edição inicial dos dados e referência para conferir os valores: `dados/edicoes/territorio-2026-10-28-r1`.
- [x] Mapeamento do nome antigo de vendaval para o identificador corrigido, em `mapeamento_catalogo.csv`.
- [x] Exemplos completos gerados pela implementação: dados disponíveis, lacunas, município sem cobertura e credencial ausente; esquema OpenAPI entregue como arquivo.
- [x] Validação dos dados e lacunas documentadas; 43 testes locais da base e da API aprovados. A validação de aceite com a equipe permanece pendente no ponto 6.
- [ ] Acordo de falhas, limites e contatos de suporte/atualização.

## Regra de trabalho

Pipo pode ajustar a implementação interna preservando o contrato. Alterações no significado dos dados ou na interface devem ser combinadas, documentadas e versionadas com as equipes afetadas. Falha técnica e ausência de dado são situações distintas; nenhuma delas significa risco zero.

**Escopo atual:** ponto 5 implementado e testado localmente por autorização do responsável, sem merge desta etapa. Validação de aceite, publicação gratuita e integração continuam como próximos pontos; motor, Bússola, pacote em `entregas/` e edição congelada não foram alterados.
