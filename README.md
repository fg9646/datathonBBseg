# Datathon Proteção Inteligente — BB Seguros

Projeto do desafio Seguro Residencial do Datathon Ibmec / BB Seguros / Brasilseg.

## Branches

- main: base para versões validadas.
- dev: integração do desenvolvimento.
- feat/banco-dados: preparação e documentação dos dados da v2.
- feat/api-territorio: desenvolvimento da API territorial.

## Dados

A versão ativa da camada de dados é a v2, schema 0.2.0: 2.578 pares cliente–imóvel no Desenvolvimento e 138 no Teste Comum, ambos com 200 colunas. A v3 experimental foi descartada.

O pacote está em entregas/Pacote_Completo_Seguro_Residencial_v2.zip na branch feat/banco-dados. Extraia-o para acessar as sete pastas com tabelas, scripts, documentação, qualidade, proveniência, referências e histórico. Leia o LEIA-ME.md interno.

## Reprodução

Requer Python 3.10 ou superior. A consolidação usa somente a biblioteca padrão. Após extrair o pacote, coloque os dois ZIPs originais recebidos da organização na pasta originais e execute:

```bash
python 02_Scripts/consolidar_seguro_residencial.py --entrada originais --saida resultados_reproduzidos
```

Os resultados do motor permanecem reservados na v2. A preparação dos dados não comprova execução do motor nem substitui os templates oficiais de resultado e coberturas.

## Uso de IA e documentação

ChatGPT foi utilizado como apoio à consolidação, scripts, documentação e verificações técnicas desta camada de dados. As limitações, origens e transformações estão no pacote. A equipe deve compreender, revisar e defender a entrega. Novas alterações devem registrar fonte, método, versão e evidências.
