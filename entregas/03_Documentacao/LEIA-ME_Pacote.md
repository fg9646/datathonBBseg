# Seguro Residencial — pacote 0.2.0

- Desenvolvimento: 2578 linhas.
- Teste comum: 138 linhas.
- Layout técnico: 200 colunas idênticas nas duas bases; uma linha por cliente–imóvel.
- As fontes originais foram preservadas. Não foram estimadas áreas nem executadas recomendações do motor.

## Ler primeiro

1. Alteracoes_por_Markdown.md: o que foi feito para cada documento recebido.
2. Relatorio_Qualidade.md: contagens, estados e limitações.
3. Dicionario_Colunas.csv e Mapeamento_Origem_Destino.csv: significado e transformação dos campos.
4. Alinhamento_Integracao.md: classificação P0–P3 atual e decisões pendentes.
5. Registro_Proveniencia_Estimativas_e_Area.csv: origem exata e método conhecido de cada valor rastreado.

Ocorrencias_Qualidade_Dados.csv lista ausências cadastrais e pendências de validação.
Bens_Detalhados_*.csv preservam cada bem e seus estados técnicos de probabilidade/confiança.
Alertas_Valores_Extremos.csv contém somente alertas estatísticos, sem alterar nenhum valor.
Politica_Validacao_Dados.json e Schema_Base_Consolidada.json documentam a versão técnica do layout.
Manifesto_SHA256.json verifica os arquivos do pacote.

## Reproduzir

Python 3.10 ou superior, somente biblioteca padrão.
Colocar os dois ZIPs originais numa pasta e executar o comando indicado em Relatorio_Qualidade.md.
O script ativo está na raiz: consolidar_seguro_residencial.py.
verificar_ajustes.py recria os testes artificiais sem modificar os ZIPs originais.
O script antigo em historico/ serve somente para reproduzir os problemas anteriores.

## Limites da entrega

P0 é encaminhamento para avaliação humana, não pergunta nem rejeição.
P1–P3 são prioridades de perguntas. A consolidação não atribui essas prioridades aos perfis.
Falhas técnicas e ausências não acionam P0. Contrato de consumo, fontes efetivas e impacto das lacunas dependem de Pippo/Bússola.
O schema CSV 0.2.0 não significa que o contrato JSON proposta-0.2 ou as regras de produto já foram aprovados.
Campos conf_ são reservas para futuras declarações; campos motor_ são reservas para resultados e não entram automaticamente em treinamento.
