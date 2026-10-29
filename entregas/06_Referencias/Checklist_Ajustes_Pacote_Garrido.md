# Checklist de ajustes — pacote de unificação

**Para Garrido e equipe | 28/10/2026 | Sem implementação nesta etapa**

O pacote atual passou na conferência dos dados fornecidos: pares cliente + imóvel, bens e valores foram preservados, e os CSVs foram reproduzidos exatamente. As falhas de validação abaixo apareceram em testes com **cópias contendo entradas artificiais**, não nos dados originais entregues.

## 1. Correções necessárias — Garrido

- [ ] **Corrigir a identificação de ausências.** Material e padrão construtivo vazios devem ser classificados como desconhecidos, nunca como `DISPONIVEL`. Interpretar outros marcadores de ausência conforme o dicionário, preservando o valor original.
- [ ] **Validar probabilidades.** Valores informados devem estar entre **0 e 1**, inclusive. Registrar valores inválidos, sem recortá-los automaticamente para esse intervalo. Ausência deve continuar diferente de zero.
- [ ] **Validar categorias de confiança do vínculo dos bens.** Identificar valores diferentes de `ALTA`, `MEDIA` e `BAIXA`, incluindo ausência. Preservar o original e registrar a pendência; não ignorar categorias desconhecidas silenciosamente.
- [ ] **Reconciliar as contagens de confiança.** Categorias reconhecidas mais eventuais registros desconhecidos ou inválidos devem explicar todos os bens considerados no resumo. Bens sem vínculo válido devem continuar separados e contabilizados no detalhe.
- [ ] **Ajustar o relatório de qualidade.** As situações acima precisam aparecer como erro ou pendência explícita. Não manter `VALIDADO` sem ressalva quando houver valores inválidos ou informações rotuladas incorretamente. Não confundir validade técnica com elegibilidade do produto.
- [ ] **Reexecutar as conferências com os pacotes originais.** Verificar preservação das chaves, das linhas, do detalhe dos bens e das somas, mantendo desenvolvimento e teste separados.
- [ ] **Repetir os casos artificiais que revelaram as falhas.** Conferir material/padrão vazios, probabilidade fora do intervalo e categoria de confiança inexistente. Usar cópias, sem alterar os arquivos originais.
- [ ] **Atualizar o pacote de entrega.** Incrementar a versão do script e atualizar documentação, relatórios, verificações e manifesto de hashes dos arquivos alterados. Alterações no contrato de colunas também exigem revisão do esquema.

### Referências para a conferência dos pacotes atuais

| Verificação | Desenvolvimento | Teste comum |
|---|---:|---:|
| Linhas cliente + imóvel | 2.578 | 138 |
| Registros de bens preservados | 8.988 | 494 |
| Colunas na versão recebida | 192 | 192 |
| Duplicação ou perda de pares | Zero | Zero |
| Diferença nas somas dos bens | Zero | Zero |

As 192 colunas descrevem a entrega recebida; não significam que esse será obrigatoriamente o contrato final de integração.

## 2. Decisões que dependem de alinhamento com o Pippo

| Checklist | Decisão a fechar | Participantes |
|---|---|---|
| ☐ | **Layout estável:** definir as colunas do contrato e como representar mais bens ou novas categorias sem mudar o layout silenciosamente | Garrido + Pippo + Bússola |
| ☐ | **Entradas do motor:** selecionar os campos necessários. Não enviar automaticamente as 192 colunas ao ML, especialmente identificadores e resultados reservados | Pippo + Garrido |
| ☐ | **Nomes, tipos e ausências:** fechar unidades, categorias e significado de vazio, zero, desconhecido e não coletado | Garrido + Pippo + Bússola |
| ☐ | **Valor efetivo:** definir como escolher entre cadastro, estimativa e declaração, preservando origens e tratando conflitos | Pippo + Bússola; Garrido garante os campos |
| ☐ | **Qualidade e continuidade:** definir quais falhas impedem o consumo de um campo ou perfil e quais permitem seguir com pendência | Garrido + Pippo + Bússola |
| ☐ | **Lacunas relevantes:** definir quais informações exigem P1, quais afetam adequação/dimensionamento em P2 e quais podem ser dispensadas | Pippo + Bússola, com validação do produto quando aplicável |
| ☐ | **Estados da avaliação:** separar encaminhamento P0, necessidade de informação, resultado preliminar, conclusão e erro técnico | Pippo + Bússola; informar Garrido e Henrique |
| ☐ | **Atualização do perfil:** definir quem incorpora respostas, gera nova revisão e invalida ou recalcula resultados antigos | Pippo + Bússola + Garrido |
| ☐ | **Saída por cobertura:** definir faixa mínima/máxima, unidade, confiança, dados utilizados, método, justificativa e pendências, respeitando os templates e o catálogo | Pippo + Bússola; Garrido apoia o formato |

## 3. Classificação única para evitar ambiguidades

| Nível | Significado | Observação |
|---|---|---|
| **P0** | Encaminhamento para avaliação humana | É estado/ação, não pergunta nem rejeição automática |
| **P1** | Perguntas sobre condições necessárias para seguir | Elegibilidade, identificação do caso ou encaminhamento |
| **P2** | Perguntas que podem alterar materialmente plano, coberturas ou dimensionamento | Podem ser necessárias para concluir |
| **P3** | Refinamento opcional de recomendação já sustentada | Não bloqueia conclusão |

Campo vazio, baixa confiança, recusa ou “não sei” não acionam P0 sozinhos. A necessidade de perguntar depende da decisão afetada e da regra aplicável. Uma falha técnica de integração também não equivale a impedimento comercial.

Os gatilhos, exceções e regras comerciais ainda precisam de validação. A proposta de integração atualizada contém os exemplos e as responsabilidades detalhadas.

## 4. Ordem sugerida

```text
Corrigir as validações
        ↓
Reexecutar as conferências dos dados e os casos artificiais
        ↓
Fechar o contrato de dados com Pippo e Bússola
        ↓
Gerar a versão do pacote para integração
```

**Limite da responsabilidade da unificação:** estimar áreas, treinar modelos, calcular scores, escolher entre Essencial, Prático e Total e dimensionar coberturas não são correções da consolidação. Essas atividades precisam de método, responsável e contrato definidos com o Pippo.
