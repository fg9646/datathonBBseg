# Relatório de qualidade da consolidação

Script e schema: 0.2.0. Data de consolidação parametrizada: 2026-10-28T18:58:38+00:00.

| Base | Clientes | Imóveis / linhas finais | Bens preservados | Áreas ausentes | Áreas estimadas |
| --- | ---: | ---: | ---: | ---: | ---: |
| Seguro_Residencial_Desenvolvimento.zip | 2200 | 2578 | 8988 | 1562 | 0 |
| Seguro_Residencial_Teste_Comum.zip | 120 | 138 | 494 | 92 | 0 |

As verificações não encontraram IDs duplicados, pares perdidos ou multiplicação de registros nos pacotes fornecidos.
Os totais cadastrado e ponderado dos bens foram reconciliados exatamente, por base e por categoria, sem arredondamento.
As confianças ALTA, MEDIA, BAIXA, DESCONHECIDA e INVALIDA explicam todos os bens com vínculo válido.
Probabilidades VÁLIDAS, AUSENTES e INVÁLIDAS também foram reconciliadas; 0 e 1 são válidos.
Bens órfãos permanecem separados, com suas próprias contagens de confiança e probabilidade.

## Limitações registradas

Não foram estimadas áreas, faixas de bens, tipos, vínculos ou resultados do motor.
As estimativas existentes foram copiadas com referência ao ZIP, arquivo, chave e linha de dados.
Os pacotes não documentam suas fórmulas geradoras, parâmetros ou datas; essa limitação está registrada, sem atribuir uma fórmula presumida.
Para área conhecida, a origem conceitual é preservada. Não é possível conferir um laudo ou cadastro original que não veio no pacote.
O arquivo Alertas_Valores_Extremos.csv apenas sinaliza observações fora da regra de 1,5 IQR calibrada no desenvolvimento.
Outlier não significa erro, inelegibilidade ou categoria de risco. Nenhum valor foi cortado, substituído ou removido.

## Reprodutibilidade

As linhas seguem o cadastro de imóveis e os bens são ordenados por bem_id no par.
Com os mesmos ZIPs e parâmetros, os CSVs são determinísticos. Para reproduzir os arquivos desta execução, use:

```bash
python consolidar_seguro_residencial.py --entrada . --saida resultados --data-consolidacao 2026-10-28T18:58:38+00:00
```

Sem --data-consolidacao, o campo de processamento fica vazio, para não inserir um relógio variável nos CSVs.
Hashes SHA-256 dos ZIPs e das saídas estão em Relatorio_Qualidade.json.

## Estados de qualidade desta revisão

| Base | Estado técnico | Ausências cadastrais | Pendências de validação |
| --- | --- | ---: | ---: |
| Seguro_Residencial_Desenvolvimento.zip | VALIDADO_COM_AUSENCIAS | 5459 | 0 |
| Seguro_Residencial_Teste_Comum.zip | VALIDADO_COM_AUSENCIAS | 299 | 0 |

VALIDADO_COM_AUSENCIAS registra lacunas cadastrais sem erro de probabilidade/confiança detectado.
VALIDADO_COM_PENDENCIAS registra valores inválidos, ausências de probabilidade/confiança ou outras falhas de associação/consistência.
Nenhum desses estados significa aprovação ou rejeição comercial. Não acionam P0 automaticamente.
DISPONIVEL significa que existe um valor cadastral; não significa material aceito pelo produto.
Ocorrencias_Qualidade_Dados.csv contém cada ocorrência com o original e a referência da fonte.
