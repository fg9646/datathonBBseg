# Auditoria da primeira edição

Este diretório contém somente o processamento de validação e congelamento dos dados. Não contém implementação da API.

## Resultado

Edição: `dados/edicoes/territorio-2026-10-28-r1`. O relatório e as limitações estão no `LEIA-ME.md` da edição; resultados detalhados em `validacao.json`.

## Verificação portátil de integridade

Com Python, executar `auditoria/validar_congelar_base.py` com a opção `--verificar-integridade` e o caminho da edição. Essa operação usa apenas a biblioteca padrão: confere hashes, tamanhos, lista de arquivos e 18 indicadores por município.

## Reprodução completa da auditoria

Requer Python, pandas, openpyxl (somente leitura de Excel) e pypdf. Informar ao script:

- `--origem`: diretório do levantamento anterior, contendo `dados_consolidados.json`, `originais_locais.json`, CSVs e inventário de fontes.
- `--piloto`: diretório do piloto anterior, para identificação do acervo.
- `--planilha`: arquivo `Enriquecimento_10_Municipios.xlsx` entregue anteriormente.
- `--destino`: diretório novo para o resultado. O script recusa sobrescrever uma edição existente.

Nesta execução foram utilizados `C:/Datathon/output/enriquecimento_10_municipios`, `C:/Datathon/output/piloto_localizacao` e a planilha em `C:/Users/NoteFelipe/Downloads/Enriquecimento_10_Municipios.xlsx`. Os brutos estão nos dois acervos locais e são localizados por `originais_locais.json`; para executar em outro computador, é necessário disponibilizar esses arquivos e ajustar esse inventário local. Eles não são necessários para verificar a integridade portátil do snapshot.

A coleta original tem precisão de data, sem horário; URLs e hashes estão no inventário de fontes da edição. A auditoria não consulta fontes externas. Download posterior pode divergir dos hashes se o órgão tiver revisado a publicação.

## Preservação

O manifesto registra também o hash do script executado. Os CSVs/JSONs de evidência e os relatórios da edição são protegidos contra normalização automática de quebras de linha pelo Git, para preservar os hashes em clones Windows/Linux. Não editar uma edição congelada: correções devem gerar nova edição.
