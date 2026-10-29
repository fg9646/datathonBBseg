# Contrato da API Território — 1.0.0

API de contexto municipal, funcional e validada localmente. Publicação e integração são futuras. O serviço fornece indicadores; pontuação, recomendações e elegibilidade pertencem aos consumidores e não são implementadas aqui.

## Acesso e entrada

`POST /v1/enriquecimento/consulta`, com `Content-Type: application/json` e `X-API-Key: <chave-do-consumidor>`. Acesso entre backends por HTTPS; HTTP é permitido apenas em desenvolvimento explícito em loopback. Não enviar chave em URL ou frontend.

| Campo | Regra |
|---|---|
| `codigo_ibge` | Obrigatório, texto com sete dígitos ASCII, presente no cadastro municipal da edição. Refere-se ao município do imóvel, não ao CEP mascarado. |
| `versao_base` | Opcional, texto de 1 a 128 caracteres. Omitido, resolve uma única edição ativa para toda a chamada. |
| `consultas` | Opcional, lista de 1 a 100 pares indicador/período. Omitida, retorna os 18 indicadores nos períodos padrão. |
| `consultas[].indicador` | Texto do catálogo, de 1 a 128 caracteres. |
| `consultas[].periodo` | Opcional, objeto com `inicio` e `fim` inclusivos em `AAAA-MM-DD`. Omitido, usa o período padrão do indicador. |

Opcionais devem ser omitidos ou preenchidos; `null` explícito é inválido. Campos desconhecidos, pares repetidos (inclusive período padrão explícito/implícito), datas impossíveis, início posterior ao fim, tipos incorretos e chaves JSON duplicadas retornam 400. A primeira edição atende somente aos períodos completos do [catálogo](DADOS.md); outro intervalo válido não é interpolado nem substituído silenciosamente.

## Resposta de sucesso — 200

Todos os campos abaixo são obrigatórios. Os anuláveis permanecem presentes como `null` quando não aplicáveis. O [OpenAPI](../openapi.json) detalha todos os objetos e enumerações.

| Campo | Tipo e significado |
|---|---|
| `versao_contrato` | Texto `1.0.0`; formato e significado da interface. |
| `versao_base` | Texto; edição dos dados efetivamente utilizada. |
| `consultado_em` | Instante real da consulta em ISO 8601 UTC. |
| `territorio` | `codigo_ibge`, `municipio`, `uf` e `abrangencia`, todos textos. Abrangência `municipio` ou `distrito_federal`. |
| `atualizacao` | `ultima_coleta_em`, data/instante ou `null` sem fontes aplicáveis; `situacao`, enumeração descrita abaixo. |
| `indicadores` | Lista de objetos correspondentes aos pares solicitados, inclusive ausentes. Consumidores reconhecem os itens por `id` e período, sem depender de posição. |

| Campo do indicador | Tipo e regra |
|---|---|
| `id` | Texto estável do catálogo. |
| `valor` | Número ou `null`. Contagens: inteiros não negativos; médias e taxas admitem decimais. |
| `unidade` | Texto exato do catálogo, sem conversão implícita. |
| `periodo` | Datas `inicio` e `fim` solicitadas ou padrão. |
| `disponibilidade` | `DISPONIVEL` ou `AUSENTE`; baixa completude não implica ausência do valor. |
| `motivo_ausencia` | `null` quando disponível; um dos quatro motivos abaixo quando ausente. |
| `fontes` | Lista de objetos com `instituicao`, `url`, `coletado_em`, todos textos. Taxas referenciam criminalidade e população. Vazia apenas quando não há fonte aplicável, como território/período sem cobertura. |
| `metodo` | Texto com filtros, transformações e recorte, ou explicação da ausência. |
| `estacao` | Objeto com `codigo` e `nome`, textos, ou `null`. |
| `cobertura` | Objeto com `numerador` inteiro não negativo, `denominador` inteiro positivo, `proporcao` numérica de 0 a 1 e `unidade: "dias"`; ou `null`. |
| `limitacoes` | Lista de textos, podendo ser vazia. |

`coletado_em` preserva a precisão original: dia `AAAA-MM-DD` ou instante ISO 8601 UTC conhecido, sem criar meia-noite ou fuso. Para `ultima_coleta_em`, selecionar o dia mais recente das fontes retornadas: se alguma fonte desse dia só tem data, devolver a data; se todas têm instante, devolver o mais recente. A primeira edição usa `2026-10-27`. Consultar hoje não atualiza as fontes.

`situacao` admite `SEM_FALHA_REGISTRADA` e `FALHA_NA_ULTIMA_TENTATIVA`. A implementação atual informa a primeira: não existe coletor periódico ou monitor de atualização. O segundo estado é reservado à futura manutenção; não foi exercido por atualização real.

## Ausências, cobertura e falhas

| Motivo | Quando usar |
|---|---|
| `FONTE_SEM_VALOR` | Fonte sem valor utilizável para o recorte, inclusive publicação apenas estadual; caso de Goiânia e da normal de chuva ≥50 mm de Fortaleza. |
| `SEM_RECORTE_RESIDENCIAL` | Fonte consultada não separa ocorrências residenciais. |
| `SEM_COBERTURA_TERRITORIAL` | Município válido no cadastro IBGE, fora da edição. |
| `PERIODO_NAO_DISPONIVEL` | Município coberto, mas intervalo válido não processado para o indicador. |

Ausência legítima retorna **200, `valor: null`, `disponibilidade: AUSENTE` e motivo explícito**, preservando os demais indicadores. Fora da cobertura territorial, esse motivo prevalece sobre o período. Zero só é retornado quando sustentado pela fonte e pelo método. Dados gerais de crimes não substituem campos residenciais.

Base indisponível ou inconsistente é falha técnica 503; não se transforma em motivo de ausência, risco zero ou condição favorável. Se uma atualização futura falhar, conservar a última edição válida e sinalizar a falha exige implementação e validação próprias.

## Três cenários

| Pedido resumido | Comportamento local | Exemplo completo |
|---|---|---|
| `{"codigo_ibge":"3550308"}` — São Paulo | 18 indicadores; roubo/furto residencial de 2025: 657/5.193. | [Pedido e resposta](../exemplos/dados_disponiveis.json) |
| Recife `2611606`, chuva e furto residencial | Chuva: 2.371/4.018 dias completos (59,0%); furto `null`/`SEM_RECORTE_RESIDENCIAL`. | [Pedido e resposta](../exemplos/dados_com_lacunas.json) |
| `{"codigo_ibge":"3509502"}` — Campinas | Município válido; 18 ausências `SEM_COBERTURA_TERRITORIAL`, sem estimar valores de vizinhos. | [Pedido e resposta](../exemplos/sem_cobertura.json) |

Esses JSONs foram gerados pela implementação local. `consultado_em` é o instante da geração, não uma promessa de atualização. Há também [exemplo sem credencial](../exemplos/credencial_ausente.json).

## Erros e limites

Envelope da aplicação: `{"erro":{"codigo":"ENTRADA_INVALIDA","mensagem":"..."}}`. Mensagens não expõem detalhes internos nem credenciais.

| HTTP | Código estável / condição |
|---|---|
| 400 | `ENTRADA_INVALIDA` — entrada, indicador ou período inválido. |
| 401 | `CREDENCIAL_INVALIDA` — chave ausente, incorreta ou duplicada; `WWW-Authenticate: ApiKey`. |
| 403 | `ACESSO_NEGADO` ou `HTTPS_OBRIGATORIO`. |
| 404 | `MUNICIPIO_INEXISTENTE`, `EDICAO_INEXISTENTE` ou `ROTA_INEXISTENTE`. |
| 405 | `METODO_NAO_PERMITIDO`. |
| 408 | `TEMPO_REQUISICAO_EXCEDIDO` — corpo não recebido em até 3 segundos. |
| 413 | `REQUISICAO_MUITO_GRANDE` — corpo acima de 16 KiB. |
| 415 | `TIPO_CONTEUDO_INVALIDO` — JSON sem Content-Type adequado ou compressão não suportada. |
| 429 | `LIMITE_EXCEDIDO` — inclui `Retry-After`. |
| 500 | `ERRO_INTERNO` — falha inesperada. |
| 503 | `SERVICO_INDISPONIVEL` — base ausente/inconsistente/bloqueada ou consulta excedeu 2 segundos; inclui `Retry-After: 1`. |

Padrão configurável: 60 chamadas/minuto por consumidor, janela em memória de uma única instância/worker, reiniciada com o processo. Uvicorn limita concorrência a 100 e keep-alive a 5 segundos. Rejeições anteriores à aplicação (servidor/proxy) podem não ter o envelope JSON. Não há SLA de latência.

`GET /health` é público e verifica processo. `GET /ready` exige chave, consulta a base e consome cota. `/docs`, `/redoc` e `/openapi.json` não são servidos; a especificação é entregue como arquivo.

## Reutilização e integração futura

O caminho `/v1` identifica a versão principal. Mudanças incompatíveis exigem nova versão principal e alinhamento com consumidores; acréscimos compatíveis também são documentados e versionados. Valores/fontes/métodos corrigidos exigem nova edição, sem sobrescrever a congelada. `consultado_em` é dinâmico; valores e metadados de origem de uma mesma edição são reproduzíveis.

Política prevista para consumidores: três segundos por tentativa, no máximo uma repetição transitória, orçamento total de até seis segundos incluindo espera. Não repetir entrada/autenticação; respeitar `Retry-After` e desistir se não couber no orçamento. Continuar o fluxo sem enriquecimento, sinalizando sua ausência, sem converter falha em zero. Esse comportamento foi alinhado como proposta e **ainda não foi validado em integração**. Uma futura regra que torne o contexto obrigatório precisa de acordo explícito entre equipes.

Na retomada, entregar ao responsável pelo backend consumidor: contrato/OpenAPI, catálogo/edição, exemplos, relatório de validação, URL real, instruções e chave por canal seguro. Equipe de enriquecimento responde por fontes/edições; responsável pela API, operação e acesso; responsáveis pelos consumidores, uso e interpretação. Atribuir suporte e frequência de atualização por fonte antes do uso real. Publicação, credenciais e integração não são obrigações da entrega atual. Ver [implantação](IMPLANTACAO.md).
