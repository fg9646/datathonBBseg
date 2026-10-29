# Território — base de consulta (ponto 4)

**Entregue no ponto 4:** importação validada em SQLite e consultas locais indexadas por edição, município, indicador e período. O ponto 5 acrescentou endpoint HTTP e autenticação, documentados em [HTTP.md](HTTP.md). A hospedagem continua pendente. Esta camada não altera o motor, a Bússola ou o pacote em `entregas/`.

## Preparar e conferir

Na raiz do repositório, com Python 3.10 ou superior e sem instalar pacotes adicionais:

```bash
python -m api_territorio.preparar_base
python -m unittest tests.test_base_territorio -v
```

O primeiro comando cria `api_territorio/var/territorio.sqlite3`. O banco é um artefato regenerável e não é versionado: cada ambiente executa esse comando durante a preparação, antes do atendimento. As fontes de entrada e o importador são versionados. Reexecutar a importação da mesma edição é idempotente; origem divergente para a mesma edição é rejeitada.

O comando também aceita `--edicao`, `--destino` e `--cadastro`. O destino não pode ficar dentro da edição congelada. A primeira edição importada torna-se a ativa; importações posteriores não trocam silenciosamente essa escolha. Procedimento de ativação de outras edições ficará para a manutenção.

## O que está no banco

| Componente | Conteúdo e uso |
|---|---|
| `edicoes` | Identificador da edição, versão do contrato e hashes do manifesto e cadastro usados na importação. |
| `municipios` | Cadastro IBGE por edição, com nome, UF e sinalização de cobertura dos indicadores. |
| `catalogo` | Dezoito IDs estáveis, unidades e períodos padrão por edição. |
| `indicadores` | 180 registros com valores ou ausências, períodos, métodos, estações, cobertura, limitações e fontes resolvidas. Índice composto para consulta. |
| `configuracao` | Identificação da edição ativa. |

O endpoint usa `Repositorio.consultar`, desta camada, com código IBGE e, opcionalmente, edição e lista de consultas no formato do contrato. O resultado organiza os dados e metadados previstos no contrato 1.0.0. A função local permanece separada do serviço HTTP e da autenticação.

As consultas abrem o SQLite em modo somente leitura. Não leem Excel, CSVs de origem, JSONs de referência ou fontes externas durante a consulta. Não contêm dados individuais de clientes ou imóveis.

## Preservação e lacunas

- Edição importada: `territorio-2026-10-28-r1`, com 10 municípios, 153 valores disponíveis e 27 ausências explícitas. Snapshot original preservado byte a byte.
- Antes de importar, são verificados o manifesto, os hashes, a lista de arquivos, as chaves, o catálogo e as correspondências com o cadastro IBGE. Importação dos registros ocorre em transação, sem sobrescrever edições já registradas.
- Cada indicador recebe instituição, URL e data de coleta de suas fontes; a precisão original de dia permanece `2026-10-27`, sem horário inventado.
- Goiânia continua sem os quatro valores residenciais, com `FONTE_SEM_VALOR`. Recife mantém a completude original e as lacunas documentadas. Nenhum valor é estimado ou substituído por média estadual.
- Município válido fora da cobertura: indicadores ausentes com `SEM_COBERTURA_TERRITORIAL`. Código inexistente no cadastro: erro distinto. Intervalo válido não processado: `PERIODO_NAO_DISPONIVEL`, preservando o período solicitado.
- No intervalo sem dados processados, não há fonte aplicável de valor: `fontes` vazia, sem substituir o período pelo padrão. Os outros indicadores da consulta continuam disponíveis.
- `SEM_FALHA_REGISTRADA` descreve a importação inicial válida. Não existe coletor periódico nem monitor de atualização implementado nesta etapa.

## Cadastro auxiliar oficial

Para distinguir município válido sem cobertura de código inexistente, foi coletado um cadastro auxiliar de **5.571 municípios** da [API de Localidades do IBGE](https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=id). A origem, o instante real de coleta, a transformação e os hashes estão em `referencias/municipios_ibge.fonte.json`.

Esse cadastro pertence à preparação operacional e não altera a edição congelada de clima, desastres e criminalidade. Só nome, código e UF foram selecionados. Ele também fica armazenado por edição no banco para preservar consultas históricas. A consulta não chama o IBGE em tempo real. Códigos novos ou mudanças cadastrais posteriores exigirão revisão do cadastro e nova edição operacional, sem sobrescrever a origem registrada para a edição atual.

## Tratamento de erros no serviço HTTP

| Exceção da camada | Mapeamento previsto pelo contrato |
|---|---|
| `EntradaInvalida` | HTTP 400. |
| `MunicipioInexistente` | HTTP 404, `MUNICIPIO_INEXISTENTE`. |
| `EdicaoInexistente` | HTTP 404, `EDICAO_INEXISTENTE`. |
| `BaseIndisponivel` | Falha técnica; HTTP 503, sem transformar em risco zero. |

O ponto 5 implementa esse mapeamento HTTP e a autenticação. A camada usa parâmetros SQL e consultas somente leitura. O arquivo SQLite deve ser acessível somente ao serviço autorizado, sem expor um caminho de banco como parâmetro de requisição.

## Evidência de aceite

Nesta entrega, 16 testes passaram. Eles cobrem os 180 registros, SP e taxas, Recife/Goiânia, DF, município válido sem cobertura versus inexistente, períodos ausentes, entradas inválidas, edição inexistente, base indisponível ou com JSON corrompido, ausência de rede/arquivos externos na consulta, importação idempotente, rejeição de snapshot adulterado, bloqueio de sobrescrita, consulta por edição e preservação da edição ativa, índice SQL e precisão das datas. Os testes não exigem rede nem bibliotecas externas e usam bancos temporários.

O serviço HTTP está implementado, com detalhes de inicialização e segurança em [HTTP.md](HTTP.md). Ainda não há URL externa publicada para o Pipo conectar.
