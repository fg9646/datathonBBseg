# Território — proposta da API de enriquecimento residencial

**Status:** pontos 1, 2 e 3 concluídos: definições de integração confirmadas pelo Pipo, contrato documental 1.0.0 com catálogo finalizado e edição dos dados `territorio-2026-10-28-r1` validada e congelada. Pontos 4 a 10 pendentes. Sem implementação ou integração ao motor e à Bússola. Hospedagem, endereço do servidor, limite numérico de chamadas e responsáveis nominais permanecem pendentes.

## 1. Objetivo e limites

Fornecer contexto municipal de clima, desastres e criminalidade para apoiar a personalização do seguro residencial.

A API entrega indicadores e suas limitações. As decisões de pontuação, recomendação de plano e elegibilidade pertencem aos sistemas consumidores.

Como os CEPs, endereços e coordenadas dos dados do desafio são fictícios ou mascarados, a unidade de consulta será o **município do imóvel, identificado pelo código IBGE real**. Não será possível atribuir risco ao endereço, bairro ou imóvel específico. Brasília representa todo o Distrito Federal, código 5300108.

A identificação de favelas ou comunidades fica fora desta versão, enquanto a equipe esclarece a questão com os organizadores.

## 2. De onde vêm os dados

| Tema | Fonte e acesso | Uso e limitações |
|---|---|---|
| População | [IBGE — API de Agregados, utilizada pelo SIDRA](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3), tabela 6579, variável 9324 | População municipal do ano escolhido; denominador das taxas de criminalidade. |
| Clima observado | [INMET — dados históricos](https://portal.inmet.gov.br/dadoshistoricos/) | Arquivos anuais das estações automáticas. Há falhas de medição e anos ausentes; uma estação não representa todos os bairros. |
| Clima de referência | [INMET — normais climatológicas](https://portal.inmet.gov.br/normais) | Referência 1991–2020. Estações convencionais podem diferir das estações automáticas usadas na série recente. |
| Desastres | [Atlas Digital de Desastres no Brasil — downloads](https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml) | Protocolos administrativos por município e tipo de desastre. Ausência de registro não comprova ausência de eventos. |
| Criminalidade | Órgãos estaduais de segurança, detalhados abaixo | Disponibilidade e classificação variam por estado. Dados gerais não substituem ocorrências residenciais. |

### Fontes de criminalidade por município

| Município | Fonte oficial | Cobertura identificada no levantamento |
|---|---|---|
| São Paulo | [SSP-SP — consultas e dados criminais](https://www.ssp.sp.gov.br/estatistica/consultas) | Roubo e furto residencial extraídos dos microdados, com filtros e deduplicação documentados. |
| Curitiba | [SESP-PR/CAPE — estatísticas](https://www.seguranca.pr.gov.br/CAPE/Estatisticas) | Roubo e furto residencial; recorte AISP 1, correspondente a Curitiba. |
| Belo Horizonte | [SEJUSP-MG — dados abertos de furto consumado](https://www.dados.mg.gov.br/dataset/sejusp_furto_consumado) e bases de crimes violentos do órgão | Indicadores gerais disponíveis; recorte residencial não identificado nas bases consultadas. |
| Brasília/DF | [SSP-DF — dados por região administrativa](https://www.ssp.df.gov.br/dados-por-regiao-administrativa/) | Roubo residencial disponível para o DF; furto residencial ausente no levantamento. |
| Fortaleza | [SSPDS-CE — estatísticas de 2025](https://www.ce.gov.br/sspds/html/estatisticas-2025/) | Furto geral e crimes violentos contra o patrimônio; sem recorte residencial nas bases consultadas. |
| Porto Alegre | [SSP-RS — indicadores criminais](https://ssp.rs.gov.br/indicadores-criminais) | Furto e roubo gerais; sem recorte residencial nas bases consultadas. |
| Recife | [SDS-PE — crimes contra o patrimônio](https://www.sds.pe.gov.br/estatisticas/indicadores-criminais/crimes-contra-o-patrimonio) | Crimes violentos contra o patrimônio; sem recorte residencial nas bases consultadas. |
| Rio de Janeiro | [ISP-RJ — dados abertos](https://www.ispdados.rj.gov.br/) | Roubo residencial disponível; furto residencial não identificado. |
| Salvador | [SSP-BA — estatísticas](https://www.ba.gov.br/ssp/node/85613) | Roubo residencial disponível; furto residencial não identificado. |
| Goiânia | [SSP-GO — estatísticas](https://goias.gov.br/seguranca/estatisticas/) | Publicação consultada com dados estaduais. Esses números não serão atribuídos a Goiânia. |

As fontes são oficiais, mas **a API Território será um serviço da equipe, não uma API governamental**. Parte dos órgãos publica arquivos, sem uma API própria adequada ao uso. Licenças e condições de redistribuição deverão ser respeitadas por fonte.

## 3. Onde a API entra

Há dois fluxos separados:

**Atualização dos dados:** fontes oficiais → coleta programada → validação e padronização → base de dados versionada → API Território.

**Consulta durante o atendimento:** backend consumidor → API Território → indicadores municipais → uso pelo motor e pela Bússola, conforme as regras de cada equipe.

Em termos simples: primeiro preparamos uma base confiável; depois a API permite consultá-la. O atendimento não dependerá de baixar arquivos governamentais naquele momento.

A planilha permanece como referência de conferência e auditoria. A operação proposta consulta a base de dados por meio da API, sem depender da leitura da planilha a cada atendimento.

## 4. Como entra tecnicamente

- Um serviço de backend da equipe disponibiliza a API por HTTP e responde em JSON.
- O backend consumidor envia o código IBGE do município do imóvel e, opcionalmente, os indicadores, períodos e a versão da base desejados.
- A API consulta a base previamente preparada e devolve valores, fontes, períodos e estados de disponibilidade.
- Os consumidores reconhecem os indicadores por identificadores estáveis, sem depender da posição de colunas de uma planilha.
- A comunicação será entre backends autorizados, por HTTPS e chave de API exclusiva por consumidor. Pipo confirmou as definições gerais do ponto 1, registradas na seção 13; a seção 16 detalha os campos para construção. Hospedagem, limite numérico de chamadas e frequência de atualização permanecem pendentes.

Esta proposta define o comportamento esperado. Não estabelece ainda uma URL operacional nem implementa chamadas nos sistemas consumidores.

## 5. Entrada da consulta

| Campo | Obrigatório? | Regra |
|---|---|---|
| `codigo_ibge` | Sim | Texto com sete dígitos, referente ao município do imóvel. |
| `versao_base` | Não | Edição específica da base. Se omitida, usa a edição ativa e informa qual foi utilizada. |
| `consultas` | Não | Lista de indicadores e períodos desejados. Se omitida, retorna o catálogo completo com seus períodos padrão. |

Não haverá um único ano de referência para toda a resposta: normais climáticas, séries recentes, desastres e criminalidade têm períodos diferentes.

CEP fictício, rua e coordenadas mascaradas não serão usados para localizar o imóvel.

## 6. Catálogo inicial de indicadores

| Identificador | Significado | Unidade | Período padrão |
|---|---|---|---|
| `clima.chuva_normal` | Precipitação média anual da normal climatológica | mm/ano | 1991–2020 |
| `clima.dias_chuva_ge50_normal` | Média anual de dias com chuva de pelo menos 50 mm | dias/ano | 1991–2020 |
| `clima.maxima_media_normal` | Média das temperaturas máximas diárias | °C | 1991–2020 |
| `clima.minima_media_normal` | Média das temperaturas mínimas diárias | °C | 1991–2020 |
| `clima.dias_minima_le10_normal` | Média anual de dias com mínima de até 10 °C | dias/ano | 1991–2020 |
| `clima.cobertura_chuva` | Proporção de dias com 24 observações horárias válidas de chuva | fração de 0 a 1 | 2015–2025 |
| `clima.cobertura_rajada` | Proporção de dias com 24 observações horárias válidas de rajada | fração de 0 a 1 | 2015–2025 |
| `clima.rajada_max_observada` | Maior rajada válida observada na estação | km/h | 2015–2025 |
| `desastres.protocolos_granizo` | Protocolos únicos de granizo | protocolos | 2015–2025 |
| `desastres.protocolos_vendaval` | Protocolos únicos de vendaval, COBRADE 13215 | protocolos | 2015–2025 |
| `desastres.protocolos_alagamento` | Protocolos únicos de alagamento | protocolos | 2015–2025 |
| `desastres.protocolos_inundacao` | Protocolos únicos de inundação | protocolos | 2015–2025 |
| `desastres.protocolos_enxurrada` | Protocolos únicos de enxurrada | protocolos | 2015–2025 |
| `desastres.protocolos_chuva_intensa` | Protocolos únicos de chuvas intensas | protocolos | 2015–2025 |
| `seguranca.roubo_residencial` | Ocorrências de roubo residencial conforme a classificação da fonte | ocorrências | 2025 |
| `seguranca.furto_residencial` | Ocorrências de furto residencial conforme a classificação da fonte | ocorrências | 2025 |
| `seguranca.taxa_roubo_residencial` | Roubo residencial dividido pela população IBGE do mesmo ano, multiplicado por 100 mil | ocorrências/100 mil habitantes | 2025 |
| `seguranca.taxa_furto_residencial` | Furto residencial dividido pela população IBGE do mesmo ano, multiplicado por 100 mil | ocorrências/100 mil habitantes | 2025 |

**Regras de interpretação:**

- As normais representam a estação e o período de referência, não uma previsão para o imóvel.
- A cobertura climática mede completude das observações, não confiança estatística. Deve informar dias válidos e dias esperados; os dias são agrupados em UTC.
- A rajada máxima observada não equivale a vento de projeto de telhado ou instalação solar.
- Os desastres usam a data do evento e protocolos únicos. Vendaval corresponde ao COBRADE 13215; não inclui outras categorias de ciclone. O identificador anterior, `desastres.protocolos_vendaval_ciclone`, foi substituído neste contrato antes da implementação; nomes antigos nos arquivos de análise deverão ter seu mapeamento documentado.
- As taxas de criminalidade são por habitantes, não por residências seguradas, e não representam probabilidade individual de sinistro.
- Métodos estaduais diferentes impedem tratar os números como um ranking homogêneo de risco entre municípios.

## 7. Saída da consulta

A resposta identifica o município, UF, abrangência geográfica, versão da base utilizada e data da consulta.

Cada indicador traz:

- Identificador, valor, unidade e período efetivo.
- Estado de disponibilidade e motivo de ausência, quando houver.
- Fonte oficial: instituição, endereço de acesso e data da coleta.
- Método: filtros, transformações, estação ou recorte territorial utilizado.
- Cobertura: numerador, denominador e proporção, quando aplicável.
- Limitações que influenciam a interpretação.

Datas de consulta e de coleta são distintas: consultar hoje não significa que a fonte foi atualizada hoje.

## 8. Tratamento de lacunas e ausência de cobertura

Valor ausente será `null`, acompanhado de um motivo explícito:

| Motivo | Significado |
|---|---|
| `SEM_COBERTURA_TERRITORIAL` | Município fora da cobertura da edição consultada. |
| `SEM_RECORTE_RESIDENCIAL` | Fonte consultada não permite separar ocorrências residenciais. |
| `PERIODO_NAO_DISPONIVEL` | Período solicitado não existe na base para aquele indicador e território. |
| `FONTE_SEM_VALOR` | A fonte consultada não fornece valor utilizável para o indicador, território e período, inclusive quando publica apenas um agregado estadual sem recorte municipal. |

Respostas parciais são permitidas: a ausência de um indicador não elimina os demais. Zero só será usado quando o método e a fonte sustentarem o valor zero. Ausência de dado nunca será convertida automaticamente em zero, baixo risco ou condição favorável.

Dados gerais de criminalidade podem ser mantidos como contexto auxiliar, com identificação própria. Não preencherão os campos residenciais.

Para distinguir os motivos: município fora da edição usa `SEM_COBERTURA_TERRITORIAL`; fonte com recorte municipal, mas sem separação residencial, usa `SEM_RECORTE_RESIDENCIAL`. Goiânia está coberta pela edição, porém a publicação consultada só apresenta totais estaduais: seus indicadores residenciais usam `FONTE_SEM_VALOR`. Esse motivo também cobre a normal anual ausente de Fortaleza. As explicações específicas acompanham cada indicador.

## 9. Exemplos de comportamento

Exemplos baseados no levantamento consolidado em 28/10/2026; não representam chamadas a uma API já implementada.

### Exemplo A — recorte disponível

**Consulta:** São Paulo, código 3550308; roubo e furto residencial, ano 2025.

**Retorno esperado:** roubo residencial = 657; furto residencial = 5.193; ambos disponíveis. Informar SSP-SP como fonte, ano 2025, edição utilizada e método de extração dos microdados, incluindo filtros e deduplicação. A disponibilidade desses dois valores não significa que todos os indicadores do município estejam completos.

### Exemplo B — dados com lacunas

**Consulta:** Recife, código 2611606; cobertura de chuva em 2015–2025 e furto residencial em 2025.

**Retorno esperado:** cobertura de chuva = aproximadamente 0,590, com 2.371 dias completos de 4.018 esperados; furto residencial = `null`, motivo `SEM_RECORTE_RESIDENCIAL`. Informar a ausência dos arquivos da estação selecionada para 2024 e 2025 no levantamento. Os indicadores disponíveis continuam na resposta.

### Exemplo C — município sem cobertura

**Consulta:** código IBGE válido de município fora dos dez municípios cobertos na edição inicial.

**Retorno esperado:** território identificado, indicadores solicitados com valor `null` e motivo `SEM_COBERTURA_TERRITORIAL`. Sem estimar valores a partir de município vizinho ou média estadual.

## 10. Versionamento e operação

- Cada publicação terá uma edição identificável e reproduzível, com fontes e métodos registrados.
- Nova coleta ou correção gera nova edição. Consultas com uma edição explícita devem preservar o resultado daquela edição.
- O período solicitado será respeitado. Não substituir 2025 por outro ano silenciosamente.
- Se uma atualização falhar, a última edição válida poderá continuar disponível, com data da coleta e falha de atualização sinalizadas.
- Entrada malformada ou indicador desconhecido gera erro de consulta. Edição inexistente gera erro de versão. Serviço sem edição utilizável informa indisponibilidade.
- A frequência de coleta será definida por fonte, conforme sua publicação; não se presume atualização em tempo real.

## 11. Decisões antes da implementação — recomendações para a equipe

A equipe confirmou a proposta geral e Pipo confirmou as definições do ponto 1. A especificação documental está fechada na seção 16. A tabela mantém o histórico das recomendações e das decisões operacionais ainda necessárias; hospedagem, emissão das credenciais e limite numérico de chamadas permanecem pendentes.

| Decisão | Recomendação para a primeira versão | O que precisamos fechar juntos |
|---|---|---|
| Abrangência geográfica | Cobrir os dez municípios do levantamento, consultados pelo código IBGE do imóvel. | Confirmar o campo real de município recebido de cada consumidor e sua validação. |
| Catálogo | Adotar os 18 indicadores da seção 6. Manter criminalidade geral como contexto separado, sem substituir dados residenciais. | Validar nomes, unidades e quais indicadores cada consumidor utilizará. |
| Períodos | Fixar normais em 1991–2020; clima observado e desastres em 2015–2025; criminalidade e população em 2025 na primeira edição. | Confirmar esses períodos e o processo de aprovação das próximas edições, sem substituição silenciosa de anos. |
| Dados ausentes | Retornar `null` com motivo explícito e preservar os demais indicadores disponíveis. | O responsável pelo motor deve definir e documentar seu comportamento para cada ausência, sem convertê-la em zero ou baixo risco. |
| Uso dos indicadores | Território fornece contexto; motor calcula score; Bússola apresenta a explicação. Contexto municipal não determina diagnóstico do imóvel nem bloqueio de elegibilidade. | Alinhar quais usos são permitidos, as limitações exibidas e as regras de interpretação dos consumidores. |
| Integração técnica | Adotar as definições gerais confirmadas pelo Pipo na seção 13 e os campos documentados na seção 16, apoiados em base previamente coletada e validada. | Definir hospedagem e limite numérico de chamadas e validar o comportamento na futura integração. |
| Atualização e rastreabilidade | Publicar edições reproduzíveis, com fonte, data, método e cobertura; manter a última edição válida em caso de falha, sinalizando a situação. | Atribuir frequência de revisão por fonte e responsável pela publicação e correção de cada edição. |
| Responsáveis e aceite | Separar responsabilidades de dados, serviço da API e consumidores; validar os três cenários da seção 9. | Nomear os responsáveis e confirmar critérios de aceite antes da primeira integração. |

**Prioridade de alinhamento:** fechar primeiro o catálogo, o tratamento de lacunas e a interpretação pelo motor. Essas decisões orientam o formato final do contrato.

### Responsabilidades propostas

- **Equipe de enriquecimento:** coleta, padronização, validação, documentação de fontes e limitações e preparação das edições da base.
- **Responsável pelo serviço da API, a nomear:** hospedagem, autenticação, disponibilidade, publicação e manutenção do serviço.
- **Equipe do motor:** escolha e interpretação dos indicadores, regras de score e comportamento diante de dados ausentes ou serviço indisponível.
- **Equipe da Bússola:** uso das informações no atendimento e apresentação de explicações compatíveis com a abrangência municipal e as limitações dos dados.

### Aceite proposto para a primeira versão

- **Dados disponíveis:** devolver valores, unidades, períodos e fontes coerentes com a edição validada do levantamento.
- **Dados com lacunas:** devolver os valores disponíveis e os motivos de ausência, sem imputação automática e sem interromper toda a resposta.
- **Município sem cobertura:** identificar a ausência de cobertura, sem copiar dados de municípios vizinhos ou médias estaduais.
- **Reprodutibilidade:** a mesma consulta na mesma edição deve devolver os mesmos indicadores e valores.
- **Falha do serviço:** consumidores devem seguir um comportamento previamente combinado, distinguindo falha técnica de ausência de dado na fonte.

## 12. Escopo desta etapa

Este documento registra a proposta e as recomendações para alinhamento. A escolha de responsáveis e as decisões técnicas pendentes serão concluídas com a equipe antes da implementação.

**Nenhuma implementação, alteração no motor ou integração à Bússola faz parte desta entrega.**

## 13. Fechamento técnico e controle de mudanças

### Definições registradas para o ponto 1

Pipo confirmou as definições gerais do ponto 1, conforme relato do responsável. O detalhamento da seção 16 finaliza o ponto 2. Não há serviço publicado.

| Item | Definição |
|---|---|
| Consulta | `POST /v1/enriquecimento/consulta`, entre backends, com corpo e resposta em JSON. |
| Entrada obrigatória | `codigo_ibge`: texto de sete dígitos, referente ao município do imóvel. Sem dados pessoais, CEP ou coordenadas. |
| Entrada opcional | `consultas`: indicadores e períodos desejados; `versao_base`: edição dos dados. Se omitidos, devolver o catálogo completo nos períodos padrão da edição ativa e informar a edição utilizada. |
| Saída | Município, UF e abrangência; versão do contrato, edição dos dados e data da consulta; indicadores com valor, unidade, período, disponibilidade, motivo de ausência, fonte, método, cobertura quando aplicável e limitações. |
| Autenticação | HTTPS com chave de API exclusiva por consumidor, armazenada apenas no backend. Credenciais por canal seguro, fora dos arquivos compartilhados e do frontend. |
| Dados ausentes | HTTP 200, com `null` e motivo explícito para cada ausência; preservar os demais indicadores disponíveis. Município válido sem cobertura também retorna 200. |
| Tempo limite | Três segundos por tentativa, confirmado pelo Pipo. |
| Novas tentativas | No máximo uma nova tentativa para falha transitória de conexão, tempo limite ou indisponibilidade temporária. Não repetir erros de entrada ou autenticação. Em 429, respeitar a indicação de espera do serviço, sem repetir imediatamente, dentro do orçamento total de até seis segundos registrado abaixo. |

### Respostas de erro

| HTTP | Situação |
|---|---|
| 400 | Entrada malformada, indicador desconhecido ou período inválido. Período válido sem dados retorna 200 com motivo de ausência. |
| 401 | Credencial ausente ou inválida. |
| 403 | Consumidor autenticado sem autorização para o recurso. |
| 404 | Código de município inexistente ou edição inexistente, diferenciados no motivo do erro. |
| 429 | Limite de chamadas excedido. |
| 503 | Serviço temporariamente indisponível ou sem edição utilizável. |

Os erros devem informar código identificável e mensagem clara. Erros internos inesperados são falhas técnicas; não devem ser convertidos em ausência de dado na fonte.

### Registro de confirmação e pendências

- **Confirmado pelo Pipo, conforme relato:** formato geral de consulta e resposta, acesso HTTPS/chave no backend, três segundos por tentativa, no máximo uma repetição transitória e continuidade sem enriquecimento em caso de falha, com sinalização e sem risco zero.
- **Detalhamento do ponto 2:** campos e tipos definidos na seção 16. Orçamento de rede de até seis segundos, somando as duas tentativas; não repetir um 429 quando a espera indicada ultrapassar esse orçamento.
- **Na definição da hospedagem:** endereço do servidor e limite numérico de chamadas.

A versão do contrato será separada da edição dos dados: a primeira identifica o formato e o significado da interface; a segunda identifica os dados publicados. O caminho `/v1` identifica a versão principal da interface.

**Controle de mudanças:** Pipo pode ajustar a implementação interna preservando o contrato. Mudanças de nomes, tipos, unidades, períodos padrão, significado dos indicadores ou tratamento de ausências precisam ser combinadas com o responsável pelo enriquecimento e os consumidores afetados, documentadas e versionadas. Correções nos valores geram nova edição dos dados.

## 14. Serviço indisponível e dados ausentes

| Situação | Comportamento proposto |
|---|---|
| Indicador sem dado na fonte | Resposta normal com `null` e motivo de ausência; os demais indicadores permanecem disponíveis. |
| Atualização da coleta falhou, mas existe edição válida | Servir a última edição válida, identificando sua data e a falha de atualização. |
| API indisponível ou chamada excedeu o tempo limite | Consumidor identifica falha técnica; não fabrica uma resposta com indicadores zerados ou motivos de ausência na fonte. |

**Comportamento confirmado pelo Pipo, conforme relato do responsável:** manter o fluxo já existente sem enriquecimento quando a consulta falhar e sinalizar que o contexto territorial não foi obtido. Não recalcular indicadores como zero nem tratar a falha como condição favorável. A execução desse comportamento será validada na integração com os consumidores. Se uma regra futura tornar o contexto obrigatório para alguma decisão, a exceção deverá ser alinhada e documentada com as equipes antes de ser aplicada.

## 15. Entrega ao Pipo

A entrega para integração deverá conter:

1. Contrato e especificação técnica final, com versões e histórico de alterações.
2. Endereço do ambiente de teste, instruções de acesso e credenciais enviadas por canal seguro, fora dos documentos compartilhados.
3. Catálogo dos 18 indicadores, dez municípios e códigos IBGE, períodos, unidades, fontes e limitações.
4. Identificação da edição inicial e referência de conferência dos valores; documentar o mapeamento do nome antigo de vendaval.
5. Exemplos completos de consulta e resposta para dados disponíveis, lacunas e município sem cobertura; exemplos de erro e indisponibilidade.
6. Resultado da validação dos valores e do comportamento da API, com pendências conhecidas.
7. Acordo sobre tempo limite, novas tentativas e continuidade sem enriquecimento, além dos responsáveis por suporte, atualização e integração.

Esses itens são entregáveis futuros. Nesta etapa, apenas o contrato e o planejamento estão sendo atualizados. Pipo integra os consumidores; nossa frente permanece responsável pelo enriquecimento e pela entrega da API conforme o contrato.

## 16. Especificação documental 1.0.0 — ponto 2 finalizado

Esta seção fixa os detalhes da interface para construção. Havendo descrição anterior genérica de campo ainda pendente, prevalece esta seção. A confirmação do Pipo refere-se ao ponto 1; o detalhamento abaixo foi fechado nesta revisão por autorização do responsável, sem atribuir ao Pipo uma revisão adicional.

### Entrada e acesso

- Chave enviada no cabeçalho `X-API-Key`, exclusivamente por HTTPS.
- `codigo_ibge`: texto obrigatório com sete dígitos; deve existir no cadastro municipal de referência.
- `versao_base`: texto opcional com identificador imutável da edição. Omitido, resolve uma única edição ativa para toda a consulta.
- `consultas`: lista opcional, não vazia quando enviada. Cada item contém `indicador` (texto obrigatório do catálogo) e `periodo` (opcional).
- `periodo`: objeto com `inicio` e `fim` no formato de data AAAA-MM-DD, ambos inclusivos. Omitido, usa o período padrão do indicador. Datas impossíveis, início posterior ao fim, campo desconhecido ou consulta duplicada geram 400.
- A primeira edição atende apenas aos períodos completos do catálogo; outro intervalo válido retorna ausência `PERIODO_NAO_DISPONIVEL`, sem recorte ou interpolação automática.
- Omitir `consultas` retorna exatamente os 18 indicadores da seção 6. Dados gerais auxiliares não integram esse catálogo.

### Resposta de sucesso — HTTP 200

Todos os campos listados são obrigatórios; campos explicitamente anuláveis usam `null` quando não aplicáveis, sem desaparecer da resposta.

| Campo | Tipo e regra |
|---|---|
| `versao_contrato` | Texto, `1.0.0` nesta versão documental. |
| `versao_base` | Texto, edição dos dados efetivamente utilizada. |
| `consultado_em` | Data e hora UTC em formato ISO 8601. |
| `territorio` | Objeto com `codigo_ibge`, `municipio`, `uf` e `abrangencia`, todos textos; abrangência `municipio` ou `distrito_federal`. |
| `atualizacao` | Objeto com `ultima_coleta_em` (texto com a maior data de coleta entre as fontes retornadas, preservando a precisão disponível conforme a regra abaixo; `null` quando não houver fontes aplicáveis) e `situacao` (`SEM_FALHA_REGISTRADA` ou `FALHA_NA_ULTIMA_TENTATIVA`). Não significa que a fonte publicou dados hoje. |
| `indicadores` | Lista com um objeto por indicador e período solicitado, inclusive os ausentes. |

### Campos de cada indicador

| Campo | Tipo e regra |
|---|---|
| `id` | Texto do catálogo estável. |
| `valor` | Número ou `null`; contagens são inteiros não negativos, taxas e médias admitem decimais. |
| `unidade` | Texto estável: `mm/ano`, `dias/ano`, `°C`, `fracao`, `km/h`, `protocolos`, `ocorrencias` ou `ocorrencias/100mil_habitantes`, conforme o catálogo. |
| `periodo` | Objeto com datas `inicio` e `fim` solicitadas ou padrão. Não substituir por outro intervalo disponível. |
| `disponibilidade` | Texto `DISPONIVEL` ou `AUSENTE`. Completude baixa pode coexistir com valor disponível e deve ser descrita em cobertura e limitações. |
| `motivo_ausencia` | `null` quando disponível; caso ausente, um dos quatro motivos da seção 8. |
| `fontes` | Lista de objetos com `instituicao`, `url` e `coletado_em` (texto com data ou data/hora UTC, conforme a precisão original). Taxas devem referenciar criminalidade e população. Lista vazia apenas quando não há fonte aplicável, como território sem cobertura. |
| `metodo` | Texto explicando filtros, transformações e recorte; para ausência, explicar a verificação realizada. |
| `estacao` | Objeto com `codigo` e `nome` (textos), quando aplicável; caso contrário, `null`. Fontes e método distinguem a estação de normais da estação automática. |
| `cobertura` | Objeto com `numerador` e `denominador` inteiros, `proporcao` numérica entre 0 e 1 e `unidade` textual (`dias`), quando calculável; caso contrário, `null`. |
| `limitacoes` | Lista de textos, podendo ser vazia; registrar limitações relevantes mesmo quando o valor estiver disponível. |

Cobertura de chuva e rajada, quando disponível, aparece tanto como indicador próprio quanto nos metadados dos indicadores observados pertinentes. Não calcular confiança ou probabilidade individual a partir dessa proporção.

**Precisão das datas de coleta:** `coletado_em` e `ultima_coleta_em` aceitam data `AAAA-MM-DD` quando somente o dia foi registrado, ou data/hora ISO 8601 em UTC quando o instante original for conhecido. Uma data sem horário não deve ser convertida para meia-noite nem receber um fuso presumido. Para `ultima_coleta_em`, comparar primeiro os dias de coleta das fontes retornadas; se alguma fonte do dia mais recente tiver somente data, devolver somente essa data. Se todas as fontes desse dia tiverem instante conhecido, devolver o mais recente em UTC. Na edição inicial, as fontes têm precisão de dia: usar `2026-10-27`, sem horário inventado. `consultado_em` continua sendo o instante real da consulta, em UTC, e não substitui a data da coleta.

### Formato dos erros

Resposta com objeto `erro`, contendo `codigo` e `mensagem`, ambos textos. Códigos estáveis: `ENTRADA_INVALIDA` (400), `CREDENCIAL_INVALIDA` (401), `ACESSO_NEGADO` (403), `MUNICIPIO_INEXISTENTE` ou `EDICAO_INEXISTENTE` (404), `LIMITE_EXCEDIDO` (429), `SERVICO_INDISPONIVEL` (503) e `ERRO_INTERNO` (500). Não expor credenciais nem detalhes internos na mensagem.

### Versões e reprodutibilidade

- Catálogo inicial: os 18 indicadores da seção 6, incluindo `desastres.protocolos_vendaval`, sem pesos, score ou regras de recomendação.
- Contrato `1.0.0` descreve formato e significado; a edição inicial dos dados, identificada separadamente no ponto 3, é `territorio-2026-10-28-r1`.
- Mudanças incompatíveis exigem nova versão principal e alinhamento com consumidores; acréscimos compatíveis são documentados e versionados. Correção de valor exige nova edição dos dados.
- Na mesma edição, valores e metadados de origem são reproduzíveis; `consultado_em` e a situação operacional de atualização podem mudar entre chamadas.
- Implementar preferencialmente em uma branch do repositório compartilhado, após verificar sua estrutura e instruções. Hospedagem e limite de chamadas ficam para a publicação. A reunião posterior poderá evoluir o contrato sem bloquear a construção desta primeira interface.

## 17. Edição inicial congelada — ponto 3 concluído

**Edição:** `territorio-2026-10-28-r1`, em `dados/edicoes/territorio-2026-10-28-r1`. O arquivo `LEIA-ME.md` da edição contém relatório, cobertura por município, métodos e limitações. `manifesto.json` e `SHA256SUMS` permitem conferir a integridade dos arquivos.

- Dez municípios, 180 pares município/indicador: 153 valores disponíveis e 27 ausências explícitas. Ausência não foi convertida em zero.
- 1.925 verificações aprovadas: 151 fontes com tamanho e SHA-256 conferidos, 108 arquivos horários reprocessados, 80 normais conferidas, 60 indicadores Atlas recalculados, sete totais residenciais reextraídos e 49 grupos mensais conciliados.
- Valores comparados com a planilha entregue, sem alteração numérica. Nomes, unidades e estados normalizados para o catálogo, com mapeamento documentado.
- Treze totais residenciais e suas treze taxas permanecem ausentes. A outra lacuna é a normal de dias de chuva ≥50 mm de Fortaleza.
- Goiânia é município coberto, mas a publicação criminal consultada é estadual. Seus indicadores residenciais usam `FONTE_SEM_VALOR`, com explicação da falta do recorte municipal; não recebem valores do estado.
- Recife mantém 59,0% de completude de chuva e dois arquivos anuais ausentes no acervo. A listagem integral dos ZIPs da coleta anterior não foi preservada; a ausência na listagem oficial não foi reconfirmada nesta auditoria.
- Datas históricas de coleta têm precisão de dia, sem horário conhecido. A edição permanece preservada; os campos da futura API aceitarão essa precisão conforme a seção 16, sem inventar horários de coleta.
- Nenhuma nova coleta foi feita. As fontes brutas anteriores permanecem arquivadas localmente e referenciadas por URL/hash; microdados criminais e registros individuais de clientes e imóveis não são publicados na edição.

O congelamento é um snapshot analítico, não uma base operacional de consulta nem uma resposta pronta da API. Os próximos passos continuam no quadro. Qualquer correção ou atualização dos dados deverá gerar outra edição; esta deve permanecer preservada com seus hashes e histórico Git.
