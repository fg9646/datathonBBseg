# Seguro Residencial — v2

Comece pelas tabelas finais. As demais pastas servem para documentação e conferência.
Esta entrega reorganiza os arquivos da v2. O script e o schema de dados continuam em 0.2.0.
Os CSVs, seus valores e as evidências anteriores foram preservados byte a byte; não houve novo cálculo.

## Tabelas para uso

- [Desenvolvimento: 2.578 linhas](01_Tabelas_Finais/Seguro_Residencial_Desenvolvimento_Consolidado.csv)
- [Teste comum: 138 linhas](01_Tabelas_Finais/Seguro_Residencial_Teste_Comum_Consolidado.csv)
- Ambas têm 200 colunas e uma linha por cliente + imóvel.

## Onde encontrar cada coisa

| Pasta | Conteúdo |
| --- | --- |
| 01_Tabelas_Finais/ | Os dois CSVs consolidados |
| 02_Scripts/ | Geração, conferência, testes e empacotamento |
| 03_Documentacao/ | Guias, dicionário, mapeamento, política e schema |
| 04_Qualidade/ | Relatórios, ocorrências, alertas e resultados dos testes |
| 05_Detalhes_e_Proveniencia/ | Bens detalhados e rastreabilidade dos valores |
| 06_Referencias/ | Markdown recebidos da equipe |
| 07_Historico/ | Script antigo para reproduzir as falhas já corrigidas |

## Documentos principais

- [Alterações por Markdown](03_Documentacao/Alteracoes_por_Markdown.md)
- [Guia da consolidação](03_Documentacao/Guia_Consolidacao_Seguro_Residencial.md)
- [Dicionário das colunas](03_Documentacao/Dicionario_Colunas.csv)
- [Alinhamento de integração](03_Documentacao/Alinhamento_Integracao.md)
- [Relatório de qualidade](04_Qualidade/Relatorio_Qualidade.md)
- [Verificação independente](04_Qualidade/Verificacao_Independente.md)

## Executar os scripts

Os comandos abaixo partem da raiz do ZIP extraído. Coloque os dois ZIPs originais numa pasta chamada originais.
A geração produz uma pasta de trabalho plana; a organização do ZIP é uma etapa posterior.
Nos documentos técnicos preservados, comandos com nomes curtos de scripts usam a pasta 02_Scripts como ponto de partida; ajuste os caminhos de entrada e saída.

```bash
python 02_Scripts/consolidar_seguro_residencial.py --entrada originais --saida resultados_reproduzidos --data-consolidacao 2026-10-28T18:58:38+00:00
python 02_Scripts/verificar_ajustes.py --script 02_Scripts/consolidar_seguro_residencial.py --originais originais --trabalho testes
```

Para conferir um pacote recebido, conferir_atualizacao.py compara a pasta plana de resultados reproduzidos com o ZIP anterior.
montar_pacote.py reúne resultados, referências e evidências num pacote intermediário.
organizar_pacote.py separa esse pacote nas pastas e gera o manifesto com os caminhos finais:

```bash
python 02_Scripts/organizar_pacote.py --entrada pacote_intermediario.zip --saida Pacote_Completo_Seguro_Residencial_v2.zip --versao v2
```

## Conferência e histórico

Manifesto_SHA256.json está na raiz e contém o tamanho e o hash de cada arquivo, usando o novo caminho.
O script ativo de consolidação está em 02_Scripts. O script antigo está em 07_Historico e serve somente para reproduzir os defeitos anteriores.
A organização não executa o motor, não estima áreas e não altera os resultados de validação.
