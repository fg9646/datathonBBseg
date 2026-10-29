# Território — contexto para o seguro residencial

**Extra funcional e documentado, validado localmente. Publicação e integração são evoluções futuras.** Não há serviço externo publicado, credenciais de produção ou participação nas decisões do motor/Bússola.

A API permite consultar contexto municipal de clima, desastres e criminalidade com fonte, período, método e limitações junto de cada valor. Pode apoiar uma futura personalização do seguro, desde que o consumidor defina como interpretar esses dados. Não há benefício de score comprovado nesta entrega.

## O que está disponível

- Interface JSON `1.0.0`: `POST /v1/enriquecimento/consulta`, com chave por consumidor e HTTPS fora do modo de desenvolvimento em loopback.
- Dez municípios e 18 indicadores: **180 registros, 153 valores e 27 ausências explícitas** na edição `territorio-2026-10-28-r1`.
- SQLite local, preparado a partir de dados versionados; a consulta não lê planilha nem chama fontes externas.
- Fontes oficiais: INMET, Atlas Digital de Desastres, IBGE e órgãos estaduais de segurança. A API Território é da equipe; não é uma API governamental.
- Código, testes, OpenAPI, exemplos e configuração opcional de hospedagem. Execução sem licença paga, autenticação terceirizada ou cobrança por consulta.

## Como ler e reutilizar

| Preciso entender… | Documento |
|---|---|
| Entrada, resposta, ausências, erros e exemplos | [Contrato](docs/CONTRATO.md) e [OpenAPI completo](openapi.json) |
| Indicadores, municípios, fontes e métodos | [Dados](docs/DADOS.md) |
| Como executar e testar no Windows | [Execução local em PowerShell](docs/EXECUCAO_LOCAL.md) |
| O que foi verificado e seus limites | [Validação](docs/VALIDACAO.md) |
| Como preparar uma infraestrutura própria no futuro | [Implantação](docs/IMPLANTACAO.md) |

## Limites essenciais

CEPs, endereços e coordenadas do desafio são mascarados. A entrada usa **código IBGE real do município**, cuja correspondência deve ser validada pelo consumidor. Brasília abrange todo o DF. Não é possível localizar um imóvel, identificar favela/comunidade ou comprovar risco e elegibilidade por estes indicadores.

Períodos e classificações variam por tema e estado. Ausência permanece `null` com motivo; não vira zero ou baixo risco. Estação meteorológica não representa todos os bairros; protocolos de desastres e taxas criminais não são probabilidades de sinistro.

Os testes são locais. Hospedagem, capacidade, latência de rede e uso real nos consumidores não foram validados. Não há atualização automática das fontes. A edição congelada e o pacote residencial em `entregas/` são preservados, em frentes distintas.

Decisões por etapas e registros antigos ficam no [histórico](docs/historico/README.md); sua leitura não é necessária para executar ou avaliar a API.
