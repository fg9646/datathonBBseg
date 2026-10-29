# Dados e limites de interpretação

Edição imutável **`territorio-2026-10-28-r1`**, contrato **1.0.0**: 10 municípios × 18 indicadores, com **153 valores e 27 ausências**. Consultas utilizam o SQLite derivado, sem ler planilha ou acessar fontes externas durante o atendimento.

## Fontes oficiais e acesso

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

As fontes são oficiais, mas **a API Território é um serviço da equipe, não uma API governamental**. Parte dos órgãos publica arquivos, sem uma API própria adequada ao uso. Licenças e condições de redistribuição deverão ser respeitadas por fonte.

## Catálogo dos 18 indicadores

| Identificador | Significado | Unidade | Período padrão |
|---|---|---|---|
| `clima.chuva_normal` | Precipitação média anual da normal climatológica | mm/ano | 1991–2020 |
| `clima.dias_chuva_ge50_normal` | Média anual de dias com chuva de pelo menos 50 mm | dias/ano | 1991–2020 |
| `clima.maxima_media_normal` | Média das temperaturas máximas diárias | °C | 1991–2020 |
| `clima.minima_media_normal` | Média das temperaturas mínimas diárias | °C | 1991–2020 |
| `clima.dias_minima_le10_normal` | Média anual de dias com mínima de até 10 °C | dias/ano | 1991–2020 |
| `clima.cobertura_chuva` | Proporção de dias com 24 observações horárias válidas de chuva | `fracao` (0 a 1) | 2015–2025 |
| `clima.cobertura_rajada` | Proporção de dias com 24 observações horárias válidas de rajada | `fracao` (0 a 1) | 2015–2025 |
| `clima.rajada_max_observada` | Maior rajada válida observada na estação | km/h | 2015–2025 |
| `desastres.protocolos_granizo` | Protocolos únicos de granizo | protocolos | 2015–2025 |
| `desastres.protocolos_vendaval` | Protocolos únicos de vendaval, COBRADE 13215 | protocolos | 2015–2025 |
| `desastres.protocolos_alagamento` | Protocolos únicos de alagamento | protocolos | 2015–2025 |
| `desastres.protocolos_inundacao` | Protocolos únicos de inundação | protocolos | 2015–2025 |
| `desastres.protocolos_enxurrada` | Protocolos únicos de enxurrada | protocolos | 2015–2025 |
| `desastres.protocolos_chuva_intensa` | Protocolos únicos de chuvas intensas | protocolos | 2015–2025 |
| `seguranca.roubo_residencial` | Ocorrências de roubo residencial conforme a classificação da fonte | `ocorrencias` | 2025 |
| `seguranca.furto_residencial` | Ocorrências de furto residencial conforme a classificação da fonte | `ocorrencias` | 2025 |
| `seguranca.taxa_roubo_residencial` | Roubo residencial dividido pela população IBGE do mesmo ano, multiplicado por 100 mil | `ocorrencias/100mil_habitantes` | 2025 |
| `seguranca.taxa_furto_residencial` | Furto residencial dividido pela população IBGE do mesmo ano, multiplicado por 100 mil | `ocorrencias/100mil_habitantes` | 2025 |

**Regras de interpretação:**

- As normais representam a estação e o período de referência, não uma previsão para o imóvel.
- A cobertura climática mede completude das observações, não confiança estatística. Deve informar dias válidos e dias esperados; os dias são agrupados em UTC.
- A rajada máxima observada não equivale a vento de projeto de telhado ou instalação solar.
- Os desastres usam a data do evento e protocolos únicos. Vendaval corresponde ao COBRADE 13215; não inclui outras categorias de ciclone. O identificador anterior, `desastres.protocolos_vendaval_ciclone`, foi substituído neste contrato antes da implementação; o mapeamento de rótulos históricos está preservado no arquivo de correspondências abaixo.
- As taxas de criminalidade são por habitantes, não por residências seguradas, e não representam probabilidade individual de sinistro.
- Métodos estaduais diferentes impedem tratar os números como um ranking homogêneo de risco entre municípios.

Os intervalos são inclusivos: normais `1991-01-01` a `2020-12-31`; observações e desastres `2015-01-01` a `2025-12-31`; segurança/população `2025-01-01` a `2025-12-31`. Não há um único ano para toda a resposta. Unidades são as do JSON; frações não são multiplicadas por 100.

## Municípios e estações

| Código IBGE | Município / UF | Abrangência | Disponíveis | Ausentes | Estação normal / automática |
|---|---|---|---:|---:|---|
| 2304400 | Fortaleza / CE | municipio | 13 | 5 | 82397 / A305 |
| 2611606 | Recife / PE | municipio | 14 | 4 | 82900 / A301 |
| 2927408 | Salvador / BA | municipio | 16 | 2 | 83229 / A401 |
| 3106200 | Belo Horizonte / MG | municipio | 14 | 4 | 83587 / A521 |
| 3304557 | Rio de Janeiro / RJ | municipio | 16 | 2 | 83007 / A621 |
| 3550308 | São Paulo / SP | municipio | 18 | 0 | 83781 / A701 |
| 4106902 | Curitiba / PR | municipio | 18 | 0 | 83842 / A807 |
| 4314902 | Porto Alegre / RS | municipio | 14 | 4 | 83967 / A801 |
| 5208707 | Goiânia / GO | municipio | 14 | 4 | 83423 / A002 |
| 5300108 | Brasília / DF | distrito_federal | 16 | 2 | 83377 / A001 |

Brasília representa todo o Distrito Federal. A seleção é municipal; não localiza endereço/bairro e não identifica comunidades ou inelegibilidade. As normais e a série recente usam estações distintas; no Rio de Janeiro, Alto da Boa Vista e Vila Militar. Nomes e códigos de estação acompanham cada indicador, sem média espacial.

## Métodos, completude e lacunas

- **Observações INMET:** dia UTC completo exige 24 horas válidas por variável. Denominador de 4.018 dias em 2015–2025. Sem imputação ou troca automática de estação. Rajada máxima usa todas as horas válidas, inclusive dias incompletos; unidade final km/h. Cobertura é proporção de dias completos, não confiança estatística nem filtro do máximo.
- **Normais:** valor anual publicado da estação convencional, sem reconstruir climatologia municipal. Cinco parâmetros entram no catálogo; os arquivos de suporte preservam os demais conferidos na auditoria.
- **Atlas:** contar protocolos únicos por município, data do evento e tipologia. Vendaval somente COBRADE 13215. Zero registro administrativo não comprova ausência do fenômeno.
- **Segurança:** preservar recorte, classificação, filtros e deduplicação da fonte estadual, descritos por indicador. Taxa = ocorrências residenciais / população IBGE 2025 × 100.000. Não é taxa por imóveis segurados, probabilidade individual nem ranking comparável entre estados.
- **Recife:** chuva com 2.371/4.018 dias completos (59,0%). Arquivos A301 de 2024 e 2025 ausentes do acervo usado. A listagem integral dos ZIPs da coleta anterior não foi preservada; ausência na listagem oficial não foi reconfirmada na auditoria. Não afirmar que esses dados nunca foram publicados.
- **Fortaleza:** normal de dias de chuva ≥50 mm ausente, `FONTE_SEM_VALOR`.
- **Segurança residencial:** 13 dos 20 totais e suas 13 taxas ausentes. Roubo disponível em São Paulo, Curitiba, DF, Rio e Salvador; furto apenas em São Paulo e Curitiba. Goiânia tem quatro ausências `FONTE_SEM_VALOR`, pois a publicação consultada é estadual; não atribuir totais de Goiás ao município. Demais ausências residenciais usam `SEM_RECORTE_RESIDENCIAL`. Isso descreve as fontes consultadas, não inexistência de qualquer outra publicação.

As 27 ausências se dividem em **5 `FONTE_SEM_VALOR` e 22 `SEM_RECORTE_RESIDENCIAL`**. Outros dois motivos atendem consultas fora de território/período, conforme o [contrato](CONTRATO.md). Ausência não vira zero. Completude baixa pode coexistir com valor disponível e permanece documentada.

## Arquivos e rastreabilidade

| Referência preservada | Uso |
|---|---|
| [indicadores.json](../../dados/edicoes/territorio-2026-10-28-r1/indicadores.json) e [CSV](../../dados/edicoes/territorio-2026-10-28-r1/indicadores.csv) | Snapshot canônico e versão de conferência, sem dados individuais. |
| [fontes.csv](../../dados/edicoes/territorio-2026-10-28-r1/fontes.csv) | URLs, datas de coleta, identificação e hashes das fontes. |
| [mapeamento_catalogo.csv](../../dados/edicoes/territorio-2026-10-28-r1/mapeamento_catalogo.csv) | Rótulos anteriores para IDs/unidades atuais; “Vendavais e ciclones” e o antigo ID `desastres.protocolos_vendaval_ciclone` não ampliam o recorte atual de vendaval. |
| [manifesto.json](../../dados/edicoes/territorio-2026-10-28-r1/manifesto.json) e [SHA256SUMS](../../dados/edicoes/territorio-2026-10-28-r1/SHA256SUMS) | Edição, arquivos, tamanhos e hashes; não sobrescrever. |
| [Relatório do congelamento](../../dados/edicoes/territorio-2026-10-28-r1/LEIA-ME.md) | Métodos e auditoria originais; linguagem de etapas registra o momento do congelamento, não o estado atual do software. |

O acervo bruto anterior está referenciado por URL/hash e arquivado localmente; não é incluído integralmente no GitHub. Microdados criminais e dados individuais de clientes/imóveis não são publicados nesta edição. Downloads futuros podem ter mudado na fonte; respeitar condições de redistribuição de cada órgão.

O cadastro auxiliar de **5.571 municípios** da [API de Localidades do IBGE](https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=id) distingue município sem cobertura de código inexistente. Estão versionados [cadastro](../referencias/municipios_ibge.json) e [origem, transformação e hashes](../referencias/municipios_ibge.fonte.json). Não altera indicadores da edição e não é consultado em tempo real. Mudanças cadastrais exigem revisão e nova edição operacional.

## Preparação e versionamento

O importador verifica manifesto, hashes, lista de arquivos, cadastro, chaves e consistência entre municípios; resolve fontes com instituição, URL e data. Importa em transação. Reimportar a mesma edição/origem é idempotente; origem divergente para edição existente é rejeitada. Primeira importação ativa a edição; outras não a substituem silenciosamente. Não há comando de ativação/rotina automática de coleta nesta versão.

O SQLite tem tabelas `edicoes` (versão e hashes), `municipios` (cadastro/cobertura por edição), `catalogo` (18 IDs/unidades/períodos), `indicadores` (registros com índice composto) e `configuracao` (edição ativa), esquema `user_version=1`. As consultas são parametrizadas, somente leitura, por edição, município, indicador e período. A camada local `Repositorio.consultar` não depende da autenticação HTTP. Não há caminho de banco na entrada pública.

Correções de valores ou fontes geram nova edição preservando as anteriores. Contrato e edição são versões distintas. O serviço não monitora novas publicações; `SEM_FALHA_REGISTRADA` descreve a preparação inicial, não atualização em tempo real. Datas históricas mantêm precisão de dia. Para preparar e conferir, ver [execução local](EXECUCAO_LOCAL.md) e [validação](VALIDACAO.md).
