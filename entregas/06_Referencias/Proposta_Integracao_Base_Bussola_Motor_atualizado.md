# Proposta de alinhamento — base unificada, Bússola e motor

**Para discussão entre Garrido, Pippo e a frente da Bússola. Ainda sem implementação.**

**Objetivo:** os três componentes trabalharem com o mesmo perfil de cliente + imóvel, fazendo somente as perguntas que possam melhorar uma decisão relevante.

**Revisão de alinhamento: 28/10/2026.** Esta versão substitui a classificação P0–P3 anterior deste documento: **P0 é encaminhamento para avaliação humana; P1–P3 são prioridades de perguntas.** Essa é a classificação adotada nesta frente para alinhar a equipe; não significa que o Pippo já validou o contrato ou as regras de produto.

Os nomes de campos, estados e formatos continuam sendo **propostas de contrato**. Os exemplos são fictícios e usam `proposta-0.2` para distinguir esta revisão. Scores, valores e gatilhos ilustrativos não representam regras oficiais, modelos treinados ou condições comerciais.

## 1. O fluxo que precisamos combinar

```text
GARRIDO — BASE UNIFICADA
Uma linha por cliente + imóvel, com origem e qualidade dos dados
                        ↓
BÚSSOLA
Consolida o perfil disponível e identifica contradições
                        ↓
MOTOR DO PIPPO
Avalia regras, necessidades, score e dimensionamento
                        ↓
Há lacuna que pode mudar uma decisão relevante?
       ├─ Não → recomendação explicada, se as condições estiverem resolvidas
       └─ Sim → motor informa campo necessário e motivo
                         ↓
              Bússola seleciona a próxima pergunta
                         ↓
              Cliente responde ou diz que não sabe
                         ↓
              Nova revisão do perfil → motor reavalia

Antes das perguntas: dados suficientes dispensam esclarecimento
P1 → resolver condições necessárias para seguir
P2 → resolver lacunas materiais de adequação e dimensionamento
P3 → refinamento opcional; dispensar se não houver benefício claro

Em qualquer avaliação: condição que exige análise humana
→ P0 / ENCAMINHAR_GERENTE: suspender recomendação automática
→ encaminhar com contexto, sem rejeição automática
```

**A Bússola conduz a conversa. O motor escolhe o plano e dimensiona as coberturas. A base fornece os dados de partida.** Não pedir ao cliente que escolha entre Essencial, Prático e Total.

## 2. Responsabilidade de cada parte

| Parte | Entrega | Alinhamento necessário |
|---|---|---|
| **Garrido: base unificada** | Chaves, dados de origem, resumos dos bens, dicionário e relatório de qualidade | Quais campos cada módulo precisa e como interpretar ausências |
| **Bússola** | Perfil para avaliação, perguntas adaptativas, respostas e histórico de alterações | Como interpretar a necessidade devolvida pelo motor e quando parar de perguntar |
| **Pippo: motor + ML** | Avaliação das regras, score dos planos, dimensionamento, justificativas e lacunas relevantes | Campos obrigatórios, métodos, critérios de suficiência e estados do resultado |
| **Equipe: validação do produto** | Catálogo e regras revisados, com responsável e versão | Coberturas, limites, combinações, exceções e critérios ainda em rascunho |
| **Henrique: interface** | Exibição das perguntas, resultado, pendências e encaminhamento | Quais estados e mensagens a interface precisa apresentar |

**Uma regra deve ter um responsável e uma versão.** Se a Bússola precisar identificar um gatilho de encaminhamento P0, deve consumir a mesma definição compartilhada usada pelo motor. Evitar duas cópias independentes de regras. **P0 não é uma pergunta:** uma pergunta P1 ou P2 pode revelar uma condição de encaminhamento, e um dado já disponível também pode acioná-la sem nova pergunta. Gatilhos comerciais ainda em rascunho precisam de validação; eventual encaminhamento por precaução deve ser identificado como política do projeto, não como impedimento oficial.

## 3. A base e o perfil da conversa são coisas diferentes

| Camada | Conteúdo | Atualização |
|---|---|---|
| **Base consolidada** | Uma linha por `cliente_id` + `imovel_id`, preservando dados e suas origens | Nova versão da consolidação |
| **Perfil da conversa** | Dados selecionados, inferências identificadas e respostas do cliente | Nova revisão a cada alteração relevante |
| **Resultado do motor** | Plano, dimensionamento, pendências e explicações | Sempre vinculado à revisão do perfil avaliada |

A base pode ser plana, em CSV ou Parquet. A troca entre módulos pode ser organizada em JSON. Não precisamos colocar a conversa inteira, as regras e todas as coberturas em uma única linha da base.

### Identificação mínima compartilhada

| Campo proposto | Finalidade |
|---|---|
| `cliente_id` + `imovel_id` | Garantir que todos tratam o mesmo cliente e imóvel |
| `versao_base` | Identificar a consolidação de origem e separar desenvolvimento de teste |
| `sessao_id` | Identificar a conversa |
| `revisao_perfil` | Identificar exatamente quais informações foram avaliadas |
| `versao_contrato` | Identificar o formato da troca |
| `versao_motor`, `versao_regras`, `versao_catalogo` | Reproduzir e explicar o resultado |

Se chegar um resultado para uma revisão anterior à atual, não apresentá-lo como resultado atualizado. Se mudar o imóvel, abrir o contexto correto e não reaproveitar automaticamente declarações específicas do imóvel anterior.

## 4. Campos e significados a combinar

Os campos da coluna “Origem disponível” existem nos arquivos fornecidos. As interpretações e variáveis adicionais precisam de definição compartilhada.

| Informação necessária | Origem disponível | O que precisamos alinhar |
|---|---|---|
| Tipo de imóvel | `complemento`, `possui_termo_apartamento`, `possui_termo_casa` e outros indícios do endereço | Quando o indício é suficiente e quando há conflito que exige pergunta |
| Área | `area_cadastrada_m2`, `origem_area`, `confianca_area` | Tratamento de indisponibilidade e impacto da incerteza no dimensionamento |
| Material construtivo | `material_parede_externa_cadastrado` | Categorias, atualidade e condições que exigem avaliação humana |
| Vínculo e uso do imóvel | Sinais de aluguel, financiamento e endereço principal | Sinais não confirmam sozinhos propriedade, ocupação ou finalidade de uso |
| Perfil financeiro | `renda_mensal`, `origem_renda`, `confianca_renda` | Uso permitido no método e o que fazer quando houver incerteza |
| Bens e conteúdo | `bens_compras.csv`, agregado por cliente + imóvel | Somas, composição, qualidade do vínculo e consulta ao detalhe |
| Seguro existente | `possui_seguro_residencial` | Não assumir que a informação identifica qual imóvel está segurado |
| Contexto territorial | `territorio_id`, município, IBGE, CEP agregado e coordenadas aproximadas | Precisão do enriquecimento e limites de interpretação |
| Necessidades ainda desconhecidas | Não há garantia de cobertura completa na base | Quais precisam ser perguntadas porque alteram a decisão |

**Ponto essencial:** a lista de campos de elegibilidade deve vir das regras revisadas. Não presumir que os dados disponíveis cobrem todas as condições.

### Para cada informação utilizada

Combinar: **valor, unidade, natureza, fonte, referência temporal quando conhecida, qualidade disponível e conflito/ausência**.

- Naturezas propostas: `OBSERVADO`, `DERIVADO`, `ESTIMADO` e `DECLARADO`.
- `null` significa valor indisponível; o motivo deve indicar se não veio na base, não foi perguntado, houve recusa ou o cliente não soube responder.
- Zero válido, resposta negativa e não aplicável continuam diferentes de ausência.
- Confiança deve ser definida por campo. Não inventar porcentagens nem chamar score de probabilidade.
- A declaração relevante do cliente pode atualizar o valor usado, preservando o original. Conflitos críticos exigem tratamento explícito, não uma sobrescrita silenciosa.

## 5. Como o motor pede informação à Bússola

O motor deve devolver **a lacuna e o motivo**, não apenas “faltam dados”.

| Item proposto | Exemplo |
|---|---|
| Campo necessário | `material_parede_externa` |
| Motivo | Cadastro indisponível; condição pode alterar o encaminhamento |
| Prioridade da pergunta | `P1` |
| Decisão afetada | Elegibilidade/avaliação humana |
| Bloqueia conclusão? | Sim, enquanto essa condição necessária estiver sem resolução |
| Próxima ação | Perguntar; se não for possível resolver, encaminhar conforme regra validada |

### Classificação única desta versão

| Nível | Significado | Quando usar | Conduta |
|---|---|---|---|
| **P0 — Avaliação humana** | Encaminhamento, não prioridade de pergunta | Condição identificada exige análise humana conforme regra ou política identificada | Suspender recomendação automática e encaminhar com contexto; não rejeitar automaticamente |
| **P1 — Condições necessárias** | Esclarecer se e como podemos seguir | Informação necessária à elegibilidade, identificação do caso ou encaminhamento está ausente ou contraditória | Usar o dado suficiente; esclarecer somente a lacuna necessária |
| **P2 — Adequação e dimensionamento** | Definir proteção e valores | Resposta pode mudar materialmente plano, coberturas ou faixas | Perguntar quando a evidência atual não sustenta a decisão; priorizar impacto e menor esforço |
| **P3 — Refinamento opcional** | Melhorar uma recomendação já sustentada | Detalhe pode refinar a experiência ou a estimativa sem alteração material | Opcional; dispensar quando não houver benefício claro |

**P2 não significa dispensável.** Área ou bens podem ser necessários para concluir o dimensionamento. P3 não pode esconder uma pergunta cuja resposta mudaria materialmente a proteção: nesse caso, a pergunta é P2.

A classificação depende da **decisão afetada**, não apenas do assunto. Uso do imóvel pode ser P1 quando condiciona aceitação ou P2 quando, já resolvida essa condição, resta uma dúvida sobre adequação. Se a avaliação revelar necessidade de análise humana, aciona P0. Baixa confiança, campo vazio, recusa e “não sei” não acionam P0 sozinhos.

Dentro da mesma prioridade, a Bússola escolhe a pergunta de maior impacto e menor esforço. No início, esse impacto pode ser qualitativo e explicado por regras; não precisa ser uma probabilidade calculada por ML. P1 necessário à continuidade vem antes dos refinamentos de P2 e P3. Se uma resposta resolver vários campos, aproveitá-los e reavaliar antes da próxima pergunta.

**Nunca perguntar apenas porque uma coluna está vazia.** Perguntar quando a ausência ou a contradição afetar uma decisão. E não dispensar uma condição obrigatória só porque o score parece estável.

### Usar, confirmar ou perguntar

| Evidência disponível | Ação |
|---|---|
| Informação suficiente, com origem e atualidade adequadas à decisão | Usar sem perguntar |
| Informação plausível, mas uma correção pode mudar a decisão | Fazer confirmação curta, aproveitando o que já sabemos |
| Informação ausente ou contraditória e necessária à decisão | Perguntar o que falta, com prioridade P1 ou P2 conforme o efeito |
| Informação sem efeito material e sem benefício claro de refinamento | Dispensar |

**Confirmar também conta como pergunta.** Confiança média, sozinha, não exige confirmação; o impacto de uma possível correção e a exigência da regra também precisam ser considerados.

### Exemplos de classificação

| Situação | Classificação e ação |
|---|---|
| Endereço indica apartamento de forma suficiente para a decisão | Usar sem perguntar; isso não resolve uso, vínculo ou material |
| Material desconhecido e necessário à regra aplicável | **P1:** perguntar ou confirmar, conforme a evidência disponível |
| Material já informado exige avaliação humana | **P0:** encaminhar sem perguntar novamente o que está resolvido |
| Material é alvenaria, resolvendo aquela condição específica | Encerrar essa pendência; não concluir elegibilidade global sem avaliar as demais condições |
| Área incerta pode alterar a faixa de reconstrução | **P2:** esclarecer se não houver estimativa suficientemente sustentada |
| Estimativa dos bens não basta para dimensionar | **P2:** confirmar a referência, aceitar valor aproximado ou abrir inventário progressivo |
| Característica de um computador pode alterar materialmente a faixa | **P2:** detalhar somente o necessário |
| Detalhe do item apenas refina uma faixa já adequada | **P3:** opcional; não prolongar a conversa sem benefício |
| Cliente diz que não sabe o material | Manter a pendência **P1**; buscar alternativa válida. Encaminhar somente se a regra/política aplicável exigir análise humana |

No inventário progressivo, usar primeiro os bens já registrados, verificar o vínculo quando relevante e detalhar somente categorias ou itens que possam mudar a avaliação. Referências de reposição, fonte/data, abrangência dos conteúdos e prevenção de dupla contagem precisam ser combinadas com o Pippo. Não confundir “não possuo”, “não quero considerar” e “não sei”, nem prometer seleção de bens que o produto não permita.

### Separação proposta no contrato

- `lacunas[].prioridade_pergunta`: **P1, P2 ou P3**; nunca P0.
- `estado = ENCAMINHAR_GERENTE` e `encaminhamento.nivel = P0`: indicam avaliação humana.
- `bloqueia_conclusao`: informação separada da prioridade; uma lacuna P2 também pode impedir a conclusão do dimensionamento.
- O motor informa campo, motivo, decisão afetada e condição de conclusão; a Bússola seleciona e redige a pergunta.
- O resultado deve identificar a regra/política e sua versão, inclusive quando o gatilho ainda estiver pendente de validação do produto.

Os nomes acima são exemplos de estrutura, não código implementado. O formato exato será alinhado com o Pippo.

## 6. Exemplo de entrada — base para Bússola

Trecho ilustrativo de um perfil. O exemplo não contém todos os campos necessários à elegibilidade. Nomes de agregados e normalizações ainda são propostas.

```json
{
  "versao_contrato": "proposta-0.2",
  "versao_base": "desenvolvimento-exemplo-01",
  "cliente_id": "CLIENTE_EXEMPLO_01",
  "imovel_id": "IMOVEL_EXEMPLO_01",
  "dados_origem": {
    "complemento": "Bloco B, apartamento 512",
    "possui_termo_apartamento": true,
    "area_cadastrada_m2": 72,
    "material_parede_externa_cadastrado": null
  },
  "resumo_bens": {
    "quantidade_registros": 8,
    "soma_valor_cadastrado_brl": 50000,
    "soma_valor_ponderado_referencia_brl": 38000
  },
  "pendencias_dados": [
    {
      "campo": "material_parede_externa_cadastrado",
      "motivo": "NAO_DISPONIVEL_NA_BASE"
    }
  ]
}
```

**Leitura esperada:** há indícios de apartamento; não é preciso perguntar isso por rotina. Os R$ 38 mil são uma referência ponderada dos registros, não uma comprovação do conteúdo total. O material desconhecido precisa ser avaliado conforme as regras aplicáveis.

## 7. Exemplo de saída — motor pede um esclarecimento

Após receber o perfil organizado pela Bússola, o motor devolve uma necessidade de informação **P1**. A necessidade de resolver o material antes da conclusão, neste exemplo, depende da validação da regra aplicável. Material ausente não significa encaminhamento P0 automático.

```json
{
  "versao_contrato": "proposta-0.2",
  "cliente_id": "CLIENTE_EXEMPLO_01",
  "imovel_id": "IMOVEL_EXEMPLO_01",
  "sessao_id": "SESSAO_EXEMPLO_01",
  "revisao_perfil_avaliada": 1,
  "estado": "PRECISA_INFORMACAO",
  "plano_recomendado": null,
  "lacunas": [
    {
      "campo": "material_parede_externa",
      "prioridade_pergunta": "P1",
      "decisao_afetada": "ENCAMINHAMENTO",
      "motivo": "Material indisponivel no cadastro",
      "bloqueia_conclusao": true,
      "acao": "PERGUNTAR"
    }
  ]
}
```

A Bússola transforma a necessidade em linguagem simples, por exemplo: **“Qual é o principal material das paredes externas deste imóvel?”** As opções precisam respeitar as categorias das regras e incluir “não sei”.

Se a resposta indicar madeira ou outro material inflamável, **suspender a recomendação automática e encaminhar para análise humana das regras e exceções**. Isso não equivale a rejeitar o cliente. O documento de elegibilidade atual é rascunho.

Esse encaminhamento é a política de tratamento adotada pelo projeto para esses casos, não uma afirmação de inelegibilidade oficial. O gatilho exato, suas exceções e a fonte da regra precisam ser validados com o Pippo e o responsável pelo produto.

Exemplo da ramificação para análise humana, diferente da solicitação de informação P1:

```json
{
  "versao_contrato": "proposta-0.2",
  "cliente_id": "CLIENTE_EXEMPLO_01",
  "imovel_id": "IMOVEL_EXEMPLO_01",
  "sessao_id": "SESSAO_EXEMPLO_01",
  "revisao_perfil_avaliada": 2,
  "estado": "ENCAMINHAR_GERENTE",
  "plano_recomendado": null,
  "pode_concluir": false,
  "encaminhamento": {
    "nivel": "P0",
    "motivo": "Material informado exige avaliacao humana",
    "campo_utilizado": "material_parede_externa",
    "valor_utilizado": "MADEIRA",
    "origem_gatilho": "POLITICA_DO_PROJETO",
    "status_validacao_produto": "PENDENTE",
    "regra_id": null,
    "versao_regra": null
  }
}
```

Na integração definitiva, preencher a identificação/versionamento da política ou regra responsável. Não encerrar a análise com `elegivel = false` apenas porque ocorreu P0; encaminhamento e decisão de aceitação são resultados diferentes. Suspender as perguntas de recomendação, preservando apenas as informações necessárias para o atendimento humano.

## 8. Exemplo de retorno — Bússola envia perfil atualizado

No caminho em que a pendência sobre material foi resolvida, o motor pode pedir uma informação de dimensionamento. Exemplo de lacuna P2 na revisão 2:

```json
{
  "versao_contrato": "proposta-0.2",
  "cliente_id": "CLIENTE_EXEMPLO_01",
  "imovel_id": "IMOVEL_EXEMPLO_01",
  "sessao_id": "SESSAO_EXEMPLO_01",
  "revisao_perfil_avaliada": 2,
  "estado": "PRECISA_INFORMACAO",
  "lacunas": [
    {
      "campo": "valor_conteudo_referencia",
      "prioridade_pergunta": "P2",
      "decisao_afetada": "DIMENSIONAMENTO",
      "motivo": "Registros de bens nao sustentam a faixa necessaria neste exemplo",
      "bloqueia_conclusao": true,
      "acao": "CONFIRMAR_REFERENCIA_OU_LEVANTAR_BENS"
    }
  ]
}
```

O bloqueio neste exemplo vem da insuficiência para dimensionar, não da classificação P2 sozinha. Se a faixa já for defensável e uma resposta não mudar materialmente a decisão, usar a informação disponível. Um detalhe apenas opcional seria P3, sem bloqueio de conclusão.

Para começar, propomos enviar o **perfil efetivo completo a cada reavaliação**, em vez de exigir que o motor reconstrua a conversa a partir de alterações soltas. O trecho abaixo mostra somente dois campos; o envio real incluiria os demais dados necessários.

```json
{
  "versao_contrato": "proposta-0.2",
  "cliente_id": "CLIENTE_EXEMPLO_01",
  "imovel_id": "IMOVEL_EXEMPLO_01",
  "sessao_id": "SESSAO_EXEMPLO_01",
  "versao_base": "desenvolvimento-exemplo-01",
  "revisao_perfil": 3,
  "perfil_efetivo": {
    "material_parede_externa": {
      "valor": "ALVENARIA",
      "natureza": "DECLARADO",
      "fonte": "RESPOSTA_CLIENTE",
      "qualidade": null
    },
    "valor_conteudo_referencia": {
      "valor": 48000,
      "unidade": "BRL",
      "natureza": "DECLARADO",
      "fonte": "RESPOSTA_CLIENTE",
      "qualidade": null
    }
  }
}
```

Este é o caminho alternativo ao encaminhamento: a revisão 2 registrou **ALVENARIA** e resolveu aquela pendência P1, sem dispensar outras condições necessárias. Depois, o motor identificou que a incerteza do conteúdo justificava uma pergunta **P2**. A revisão 3 registra a estimativa declarada pelo cliente. **Uma declaração não vira avaliação pericial nem confiança estatística de 100%.**

Esse valor deve representar um total definido na pergunta, por exemplo, bens dentro daquele imóvel. Não somá-lo automaticamente aos R$ 38 mil da base: são referências alternativas para o mesmo objeto, não parcelas independentes.

## 9. Exemplo de saída — recomendação preliminar explicada

Scores e valores abaixo são fictícios. A escala de 0 a 100 serve apenas para ilustrar; pesos, critérios e desempates ainda precisam ser definidos pelo Pippo e discutidos pela equipe.

```json
{
  "versao_contrato": "proposta-0.2",
  "cliente_id": "CLIENTE_EXEMPLO_01",
  "imovel_id": "IMOVEL_EXEMPLO_01",
  "sessao_id": "SESSAO_EXEMPLO_01",
  "revisao_perfil_avaliada": 3,
  "versao_motor": "exemplo-nao-implementado",
  "versao_regras": "rascunho-a-validar",
  "versao_catalogo": null,
  "estado": "RECOMENDACAO_PRELIMINAR",
  "scores_demonstrativos": {
    "Essencial": 64,
    "Pratico": 82,
    "Total": 76
  },
  "plano_recomendado": "Pratico",
  "justificativas": [
    "Maior adequacao no criterio demonstrativo",
    "Necessidades adicionais do Total nao justificaram sua priorizacao neste exemplo"
  ],
  "dimensionamento": {
    "conteudo_referencia_brl": 48000,
    "origem": "DECLARADO_PELO_CLIENTE",
    "limites_por_cobertura": null,
    "pendencia": "Aplicar coberturas e limites do catalogo oficial validado"
  },
  "pode_concluir": false,
  "pendencias": [
    "Validar regras e catalogo antes de uma recomendacao definitiva"
  ]
}
```

**Prático é a apresentação ao cliente; `Pratico` é apenas uma proposta de código interno.** Os três códigos e seus nomes de exibição devem ser combinados.

O exemplo mostra uma recomendação preliminar porque não temos aqui o catálogo validado. Na saída definitiva, o dimensionamento deve identificar cada **cobertura oficial**, sua aplicabilidade, limite recomendado, unidade, método, premissas e pendências. Valor de reconstrução, valor de conteúdo e limite por cobertura não são intercambiáveis. Preço só deve aparecer se vier de uma fonte ou método válido e identificado.

## 10. Como evitar que o motor recomende Total para todos

Precisamos fechar com o Pippo:

1. **O que o score mede:** adequação às necessidades e ao contexto, com critérios explicáveis. Não assumir que mais coberturas sempre significam melhor recomendação.
2. **Restrições anteriores à comparação:** elegibilidade, aplicabilidade, disponibilidade no produto e limites oficiais.
3. **O benefício adicional de cada plano:** o que melhora para aquele perfil ao passar de Essencial para Prático ou Total.
4. **Critério de desempate:** proposta de preferência pelo plano suficiente de menor complexidade/custo quando os benefícios relevantes forem equivalentes. Comparar custo somente se houver informação válida.
5. **Tratamento da incerteza:** uma pendência relevante pode exigir pergunta ou resultado preliminar; não deve ser compensada por um score alto.

Sem um rótulo de “plano correto”, o ML pode apoiar estimativas ou classificações com alvos disponíveis e validados. **Não apresentar o plano escolhido por uma regra como uma verdade aprendida da base.** Estimativas do ML entram identificadas, com método e limitações; a decisão continua explicável pelo motor.

## 11. Quando perguntar, parar ou encaminhar

| Estado proposto | Significado | Conduta |
|---|---|---|
| `PRECISA_INFORMACAO` | Há lacuna P1 ou P2 que a conversa pode resolver | Fazer a próxima pergunta selecionada, sem repetir dados suficientes |
| `RECOMENDACAO_PRELIMINAR` | Há uma indicação, mas falta condição para conclusão | Mostrar ressalva concreta e a pendência; não apresentar como contratação liberada |
| `CONCLUIDO` | Condições necessárias resolvidas e recomendação/dimensionamento sustentados | Apresentar plano, coberturas, valores e justificativas |
| `ENCAMINHAR_GERENTE` | **P0:** condição exige avaliação humana | Suspender a conclusão automática e enviar contexto, regra/política e revisão avaliada; sem rejeição automática |
| `ERRO_DADOS` | Chave, formato ou integridade impedem avaliação confiável | Corrigir a integração; não transformar falha técnica em rejeição |

Critério proposto de parada: não há P0 ativo, as condições necessárias de P1 estão resolvidas e as decisões de adequação/dimensionamento de P2 estão suficientemente sustentadas. Nenhuma pergunta restante pode mudar materialmente o resultado. **P3 é opcional e não bloqueia a conclusão.** Definir “impacto material” por decisão/cobertura, com critérios acordados; não inventar um limiar universal de confiança.

Perguntas P3 podem refinar uma recomendação já sustentada sem reabrir a coleta obrigatória. Não criar um estado obrigatório `PRECISA_INFORMACAO` apenas porque existe um refinamento opcional disponível.

Se o cliente não souber responder, registrar isso, não repetir a mesma pergunta indefinidamente e seguir para alternativa válida, resultado preliminar ou análise humana. Um limite de perguntas pode proteger a experiência, mas não autoriza pular condições necessárias.

## 12. Casos para validar juntos antes de programar

| Caso | Comportamento esperado |
|---|---|
| Dados suficientes para a avaliação | Seguir sem perguntas redundantes |
| Endereço sugere apartamento de forma suficiente | Aproveitar o indício; não perguntar por rotina |
| Cadastro e declaração entram em conflito | Preservar origens e tratar o conflito conforme seu impacto |
| Material indisponível e necessário à regra aplicável | **P1:** esclarecer antes da conclusão; ausência sozinha não aciona P0 |
| Madeira ou outro material inflamável | **P0:** análise humana conforme política do projeto; validar regras/exceções, sem rejeição automática |
| Área ausente altera materialmente o dimensionamento | **P2:** aproveitar estimativa defensável ou perguntar; manter pendência se insuficiente |
| Detalhe de item altera materialmente a faixa | **P2**, mesmo que o assunto pareça um refinamento |
| Detalhe apenas melhora uma faixa já sustentada | **P3:** opcional; não bloquear conclusão |
| Cliente possui dois imóveis | Não misturar bens, respostas ou resultados específicos |
| Cliente corrige o valor dos bens | Nova revisão e reavaliação das decisões dependentes |
| Cliente não sabe ou prefere não responder | Registrar motivos separadamente e aplicar alternativa prevista; sem P0 automático |
| Resultado chega para revisão antiga | Não substituir o resultado da revisão atual |
| Necessidades não justificam benefício adicional do Total | Permitir Essencial ou Prático conforme critério acordado |
| Mesma entrada e mesmas versões | Resultado reproduzível, salvo componente aleatório controlado e documentado |

## 13. O que validar com o Pippo antes de implementar

| Tema | Decisão a fechar | Participação necessária |
|---|---|---|
| **Classificação compartilhada** | Adotar esta versão: P0 encaminhamento; P1 condições necessárias; P2 adequação/dimensionamento; P3 opcional. Remover a definição antiga dos contratos ativos | Pippo + Bússola; informar Garrido e Henrique |
| **Gatilhos P0** | Evidências suficientes, exceções, origem/versão da regra ou política, destino e contexto do atendimento. Confirmar especialmente material, obra e atividades | Pippo + Bússola + responsável pelo produto |
| **Campos necessários de P1** | Quais condições realmente precisam ser resolvidas, quais dados bastam e quando uma declaração é exigida. Não transformar todo campo ausente em obrigação | Pippo + Bússola + produto |
| **Impacto material de P2** | O que muda plano, cobertura ou faixa o suficiente para justificar perguntar; quais lacunas impedem concluir | Pippo + Bússola |
| **Uso direto e confirmação** | Fonte, atualidade, qualidade por campo e tratamento de conflito. Confiança média não obriga confirmação por rotina | Pippo + Garrido + Bússola |
| **Inventário progressivo** | Categorias abrangidas, referência de reposição com fonte/data, vínculo dos bens, móveis e demais conteúdos, dupla contagem e limites por cobertura | Pippo + Bússola + Garrido; produto quando necessário |
| **P3 e experiência** | Quando oferecer refinamento opcional e quando encerrar; preço e assistências somente se houver dados oficiais e efeito real | Pippo + Bússola + Henrique |
| **Estados e formato da troca** | Separar prioridade da pergunta, encaminhamento e bloqueio de conclusão; definir identificadores e versão das regras/políticas | Pippo + Bússola; Garrido e Henrique na integração |
| **Revisões e erros** | Nova revisão após correções; descartar resultados antigos. Falha técnica não é P0 comercial nem rejeição | Pippo + Garrido + Bússola + Henrique |

Nenhum score alto supera uma condição necessária pendente. Nenhuma P3 é obrigatória para liberar uma conclusão já sustentada. O catálogo oficial de Essencial, Prático e Total e as regras de produto permanecem sujeitos à validação dos responsáveis.

## 14. Pauta objetiva para a conversa com Pippo e Garrido

- [ ] Confirmar chave cliente + imóvel e campos necessários ao motor.
- [ ] Fechar nomes, tipos, unidades, categorias, ausências e origens no dicionário.
- [ ] Definir quem gera cada inferência/estimativa, evitando cálculos duplicados.
- [ ] Validar quais condições podem ser resolvidas com os dados disponíveis.
- [ ] Fechar o formato do perfil, das lacunas e do resultado, com exemplos compartilhados.
- [ ] Confirmar a classificação única da seção 5 e substituir a definição anterior nos materiais ativos de integração.
- [ ] Validar gatilhos de P0, campos necessários de P1 e critérios de impacto/suficiência de P2; manter P3 opcional.
- [ ] Definir prioridade entre fontes e tratamento de conflitos.
- [ ] Revisar regras e catálogo, responsáveis e versões.
- [ ] Fechar score, desempate e dimensionamento sem favorecer Total por padrão.
- [ ] Definir revisão do perfil, reavaliação e tratamento de falhas.
- [ ] Validar os casos da seção 12 e só então iniciar a implementação.

**Saída esperada dessa conversa:** um dicionário compartilhado, exemplos de entrada e saída acordados e uma lista explícita do que ainda depende de validação. Este documento é o ponto de partida para essa discussão.
