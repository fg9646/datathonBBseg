# Alinhamento da base, Bússola e motor — pacote 0.2.0

Esta revisão aplica as correções técnicas do checklist e documenta a proposta atualizada.
O schema CSV 0.2.0 tem 200 colunas. Ele é diferente da versão proposta para a troca JSON, proposta-0.2.
A classificação de P0–P3 segue o Markdown atualizado; formatos, gatilhos comerciais e contrato com o Pippo continuam em alinhamento.

## Camadas e responsabilidade

| Camada | Função nesta entrega |
| --- | --- |
| Base consolidada | Uma linha por cliente–imóvel, fontes e estados técnicos de qualidade |
| Perfil da conversa | A ser implementado pela integração; reúne dados selecionados e declarações com revisão própria |
| Resultado do motor | A ser produzido pelo motor e vinculado à revisão do perfil, versões de regras e catálogo |

conf_ continua reservado por compatibilidade e representa uma futura informação DECLARADA pelo cliente.
A declaração não é laudo nem confiança estatística de 100%.
motor_ continua reservado e vazio, exceto NAO_EXECUTADO no status.
Os hashes atuais identificam a base e o perfil original; não implementam um histórico de conversa ou descarte automático de resultados antigos.
As 200 colunas não são uma lista aprovada de atributos para ML. Identificadores, controles e resultados não entram automaticamente no treinamento.

## Classificação compartilhada atual

| Nível | Significado | Separação necessária |
| --- | --- | --- |
| P0 | Encaminhamento para avaliação humana | Estado/ação; nunca prioridade de pergunta nem rejeição automática |
| P1 | Pergunta sobre condição necessária para seguir | Depende da decisão e da regra aplicável |
| P2 | Pergunta com efeito material no plano, proteção ou dimensionamento | Também pode bloquear conclusão quando a decisão não estiver sustentada |
| P3 | Refinamento opcional | Não bloqueia conclusão já sustentada |

Uma ausência, baixa confiança, recusa, não sei ou erro técnico não aciona P0 por si só.
A base registra ocorrências; a relevância de uma pergunta e o encaminhamento pertencem à Bússola/motor e às regras ou políticas identificadas.
Não foram criados gatilhos comerciais, scores, seleção de plano, cálculo de coberturas ou um estimador de área.

## O que foi preparado

- Dicionário com naturezas OBSERVADO, DERIVADO, ESTIMADO e DECLARADO para os respectivos dados.
- Contagens completas de confiança e validade da probabilidade.
- Ocorrencias_Qualidade_Dados.csv e controles por perfil com origem, campo, valor original e motivo.
- Detalhe de bens com status da probabilidade e da confiança, inclusive para bens órfãos.
- Estimativas copiadas ou agregadas com pendência são identificadas na proveniência, sem mudar seus valores.
- Estados de ausência cadastral separados de pendências de validação; ambos separados de elegibilidade.

## Decisões ainda necessárias

| Tema | Responsável pelo alinhamento | Entrega esperada |
| --- | --- | --- |
| Campos efetivamente consumidos | Pippo + Garrido | Seleção explícita de entradas, tipos, unidades e categorias |
| Valor efetivo e conflitos | Pippo + Bússola | Política por campo, mantendo cadastro, estimativa e declaração |
| Qualidade e continuidade | Pippo + Bússola + Garrido | Definir quais falhas impedem consumo de campo/perfil e quais permitem seguir com ressalva |
| Atualização e resultados antigos | Pippo + Bússola + Garrido | Sessão, revisão de conversa, reavaliação e vínculo da resposta à revisão avaliada |
| Layout para mais bens/categorias | Pippo + Bússola + Garrido | Estratégia acordada para extensão; o script agora interrompe com erro de schema em vez de alterar colunas sozinho |
| P0, P1 e P2 | Pippo + Bússola + produto | Gatilhos, condições necessárias, impacto material, suficiência e fonte/versão de regras ou políticas |
| Saída por cobertura | Pippo + Bússola | Cobertura, faixa mínima/máxima, unidade, confiança, dados utilizados, método, justificativa e pendências |
| Estimativas e ML | Pippo + responsável pelo método | Método, calibração somente no desenvolvimento, validação e registro de limitações |

Os exemplos e a lista de casos do Markdown de referência são propostas para validação conjunta.
O script verifica consolidação e qualidade técnica. Não simula os estados ou as decisões comerciais desses exemplos.
