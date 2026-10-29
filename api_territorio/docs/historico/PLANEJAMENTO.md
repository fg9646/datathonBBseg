> **Registro histórico.** Preserva decisões, resultados e linguagem da época; não define o estado atual nem exige novas aprovações. Os guias atuais começam no [README da API](../../README.md). Os links foram ajustados para esta localização.

# API Território — quadro do extra validado localmente

**Decisão de escopo em 29/10/2026:** entregar a API como **extra funcional, documentado no GitHub e validado localmente com 53 testes aprovados**. Os pontos 1 a 6 técnicos e a preparação do Render Free estão integrados à `main`. Publicação externa e integração com motor/Bússola ficam como evolução futura, sem prazo assumido; não bloqueiam a entrega atual. Nenhum serviço foi publicado ou integrado. A execução local não exige serviços pagos; uma eventual publicação também deverá continuar gratuita.

| Ordem | Tarefa curta | Responsável proposto | Pronto quando… |
|---|---|---|---|
| 1 — concluído | Fechar consulta, acesso e falhas | Enriquecimento + Pipo | POST/JSON por código IBGE, HTTPS/chave por consumidor, três segundos por tentativa e no máximo uma repetição transitória; continuar sem enriquecimento em caso de falha, sinalizando-a. |
| 2 — concluído | Finalizar e versionar contrato e catálogo | Enriquecimento + consumidores | Contrato documental 1.0.0, 18 indicadores, campos, períodos, ausências e erros definidos; vendaval corrigido. |
| 3 — concluído | Validar e congelar a edição inicial dos dados | Enriquecimento | Edição `territorio-2026-10-28-r1`: 180 pares município/indicador, 153 valores disponíveis, 27 ausências explícitas; 1.925 verificações aprovadas, fontes e hashes registrados. |
| 4 — concluído | Preparar a base de consulta | Enriquecimento / responsável pela API | SQLite regenerável com 180 registros, consultas indexadas por município/edição, fontes resolvidas, lacunas preservadas e cadastro auxiliar IBGE. Importação e testes documentados em `api_territorio/README.md`. |
| 5 — concluído | Construir a API | Responsável pela API | Endpoint POST/JSON implementado com chave por consumidor, HTTPS, validação, limites e erros; testes e exemplos em `api_territorio/HTTP.md`. Sem publicação ou integração. |
| 6 — técnico concluído | Validar dados e comportamentos localmente | Enriquecimento + responsável pela API | 43 testes da validação inicial e dez da preparação Render aprovados; relatórios e checklist disponíveis, sem presumir aceite humano ou integração. |
| 7 — evolução futura; configuração pronta | Publicar ambiente gratuito | Responsável a alinhar na retomada; acesso ao repositório pelo Garrido | Se retomado: conferir condições gratuitas, autorizar publicação, registrar URL e passar verificações externas de `api_territorio/PUBLICACAO_RENDER.md`. |
| 8 — evolução futura | Entregar acesso operacional ao Pipo | Responsáveis a alinhar na retomada | Se retomado: entregar URL, instruções e credenciais por canal seguro, além dos documentos já disponíveis. |
| 9 — evolução futura | Integrar e validar com os consumidores | Pipo + equipes do motor/Bússola, se a integração for retomada | Validar uso dos indicadores, lacunas, tempo limite e falhas nos consumidores; sem atribuir precisão de endereço aos dados municipais. |
| 10 — evolução futura | Definir manutenção do serviço | Responsáveis a alinhar na retomada | Se retomado: definir suporte, frequência de revisão das fontes e processo de novas edições; nenhuma coleta automática atual. |

## Entrega atual do extra — disponível no GitHub

- [x] Contrato 1.0.0, implementação HTTP autenticada, SQLite e instruções de execução local.
- [x] Catálogo, dez municípios/códigos IBGE, períodos, unidades, fontes e limitações documentados na edição.
- [x] Edição inicial dos dados e referência para conferir os valores: `dados/edicoes/territorio-2026-10-28-r1`.
- [x] Mapeamento do nome antigo de vendaval para o identificador corrigido, em `mapeamento_catalogo.csv`.
- [x] Exemplos completos gerados pela implementação: dados disponíveis, lacunas, município sem cobertura e credencial ausente; esquema OpenAPI entregue como arquivo.
- [x] Relatório consolidado do ponto 6, com 43 testes locais aprovados, cinco conferências complementares e preservação documentada em `api_territorio/VALIDACAO.md`.
- [x] Checklist de aceite da equipe preparado em `api_territorio/ACEITE_EQUIPE.md`.
- [x] Configuração Render Free e dez testes adicionais preparados; **53 testes locais aprovados** no total, com evidência em `api_territorio/validacao/preparacao-render-2026-10-29.json`.
- [x] Extra delimitado: sem URL pública, credenciais de produção, integração ou impacto comprovado nas decisões do motor/Bússola.

O checklist humano permanece disponível para eventual revisão da equipe; não registra aprovações que não recebemos e não é uma exigência externa nem bloqueio para a entrega deste extra. As evidências históricas dos pontos 6 e 7 continuam preservadas, com os resultados de cada execução.

## Evolução futura — fora do escopo desta entrega

- [ ] Retomar a publicação apenas por nova decisão de escopo, mantendo gratuidade, uma instância e sem complementos pagos. Auto-deploy permanece desligado.
- [ ] Se houver retomada, obter a autorização do repositório pelo Garrido, configurar a hospedagem/credenciais e validar HTTPS, reinício, hibernação e acesso externo.
- [ ] Entregar ao Pipo o acesso operacional e alinhar responsáveis/limites/suporte, quando a integração for planejada.
- [ ] Integrar e testar os consumidores antes de afirmar qualquer uso dos dados em pontuação, planos, elegibilidade ou explicações da Bússola.

Estes itens compõem um roteiro de evolução; não são tarefas a executar agora nem dependências para concluir a entrega local.

## Regra de trabalho

Em eventual retomada, Pipo pode ajustar a implementação interna preservando o contrato. Alterações no significado dos dados ou na interface devem ser combinadas, documentadas e versionadas com as equipes afetadas. Falha técnica e ausência de dado são situações distintas; nenhuma delas significa risco zero.

**Escopo atual:** extra desenvolvido, documentado e validado localmente. Publicação e integração futuras. Esta atualização muda apenas contrato e quadro na `feat/api-territorio`; não altera código, configuração, testes, edição congelada, `entregas/`, motor ou Bússola e não realiza deploy ou merge.
