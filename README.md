# Base de Dados Residenciais - Time Vector

Datathon Proteção Inteligente - Ibmec / BB Seguros / Brasilseg. Desafio escolhido: Seguro Residencial.

Esta documentação trata exclusivamente da preparação e consolidação dos dados residenciais. O motor de recomendação e a jornada Bússola estão no [repositório do MVP](https://github.com/tmzhenrique/BBDW-X-IBMEC).

## 1. Base residencial vigente

A referência ativa dos dados é a **v2**, com schema **0.2.0**. Cada linha representa um par cliente + imóvel; clientes com mais de um imóvel possuem linhas distintas.

| Base | Clientes na origem | Pares cliente + imóvel | Colunas |
| --- | ---: | ---: | ---: |
| Desenvolvimento | 2.200 | 2.578 | 200 |
| Teste Comum | 120 | 138 | 200 |

Os identificadores originais foram preservados. Os bens foram resumidos antes das junções, evitando multiplicação dos imóveis. Dados observados, derivados, estimados, declarados e controles mantêm suas naturezas e fontes identificadas.

Não foi estimada nova área na consolidação v2. Área ausente permanece desconhecida. Métodos de estimação implementados posteriormente no MVP devem ser avaliados por suas próprias versões e evidências. O experimento v3 descartado não integra a base ativa.

## 2. Organização dos arquivos

O pacote extraído está em [entregas/](https://github.com/fg9646/datathonBBseg/tree/main/entregas):

| Pasta | Conteúdo |
| --- | --- |
| 01_Tabelas_Finais | CSVs consolidados de Desenvolvimento e Teste Comum |
| 02_Scripts | Consolidação, verificações e organização do pacote |
| 03_Documentacao | Guia, dicionário, mapeamento, política e alinhamento de integração |
| 04_Qualidade | Relatórios e evidências da preparação dos dados |
| 05_Detalhes_e_Proveniencia | Bens detalhados e rastreabilidade dos valores |
| 06_Referencias | Orientações recebidas da equipe |
| 07_Historico | Código anterior preservado para rastreabilidade |

Comece pelo [LEIA-ME da v2](https://github.com/fg9646/datathonBBseg/blob/main/entregas/LEIA-ME.md) e pelo [guia de consolidação](https://github.com/fg9646/datathonBBseg/blob/main/entregas/03_Documentacao/Guia_Consolidacao_Seguro_Residencial.md).

## 3. Reprodução da consolidação

Requer **Python 3.10 ou superior**. Este componente utiliza somente a biblioteca padrão; suas dependências estão documentadas separadamente das da API.

No Windows/PowerShell, habilite UTF-8 na sessão antes de executar os comandos abaixo:

```powershell
$env:PYTHONUTF8 = '1'
```

Essa configuração também é herdada pelos processos Python iniciados pelos testes e evita falhas na leitura dos relatórios com acentos. Ela vale apenas para a sessão atual.

Na raiz do repositório, coloque os dois ZIPs originais recebidos da organização na pasta `originais/`, sem modificar seus arquivos:

- Seguro_Residencial_Desenvolvimento.zip
- Seguro_Residencial_Teste_Comum.zip

Execute:

```bash
python entregas/02_Scripts/consolidar_seguro_residencial.py --entrada originais --saida resultados_reproduzidos
```

Para conferir os casos de regressão:

```bash
python entregas/02_Scripts/verificar_ajustes.py --script entregas/02_Scripts/consolidar_seguro_residencial.py --originais originais --trabalho testes_consolidacao
```

Para comparação byte a byte, use a mesma data de consolidação indicada no relatório de qualidade. As verificações do pacote demonstram integridade da preparação dos dados; não certificam as decisões do motor de seguros.

## 4. Uso e limitações dos dados

Os dados do desafio são sintéticos. Município, UF e código IBGE são referências reais; os demais componentes do endereço são fictícios ou perturbados. Ausência não equivale a zero, resposta negativa ou condição de inelegibilidade.

Estimativas recebidas da fonte permanecem identificadas com suas limitações. Declarações do cliente não são laudos nem confiança estatística de 100%. O seguro cadastrado no nível do cliente não comprova seguro no mesmo imóvel.

As tabelas consolidadas são insumos. Plano, faixas e templates de resultado são saídas do motor e devem ser avaliados por suas próprias versões e evidências.

## 5. Documentação da base

O guia, o dicionário de colunas, o mapeamento das fontes, a política de validação, o schema e os relatórios de qualidade estão em entregas/. A documentação da API territorial é independente e fica em api_territorio/; suas instruções não fazem parte deste guia de dados.

## 6. Uso de IA e alterações

ChatGPT apoiou a estruturação da base, scripts, documentação e verificações. A equipe deve compreender, revisar, executar e defender a solução. Registrar fonte, método, versão e evidências de novas mudanças.

Atualização documental de 29/10/2026: organização e instruções da base v2, com separação explícita da documentação da API. Nenhum CSV, cálculo, indicador ou regra do motor foi alterado.
