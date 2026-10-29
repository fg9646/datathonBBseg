# Guia para o Garrido — unificação das tabelas

**Objetivo:** construir uma base consolidada que a Bússola e o motor do Pippo possam consultar de forma consistente, aproveitando os dados antes de fazer perguntas ao cliente.

**Este documento orienta a construção do script.** Os nomes de novas colunas e os formatos de saída abaixo são propostas para combinar com a equipe. As chaves, as colunas de origem e as contagens apresentadas foram verificadas nos dois arquivos ZIP fornecidos.

## 1. O que o script deve entregar

```text
Cinco tabelas originais
          ↓
Validar chaves, tipos e ausências
          ↓
Resumir bens por cliente + imóvel
          ↓
Juntar sem multiplicar imóveis
          ↓
Base consolidada + dicionário + relatório de conferência
          ↓
Bússola esclarece lacunas → motor calcula a recomendação
```

**Uma linha representa um par cliente + imóvel.** Um cliente com dois imóveis terá duas linhas. As bases originais devem ser preservadas.

A consolidação prepara informações; a escolha entre **Essencial, Prático e Total**, as regras de elegibilidade e o dimensionamento das coberturas pertencem aos módulos responsáveis por essas decisões.

## 2. O que existe nos arquivos

| Arquivo | Desenvolvimento | Teste comum | Papel |
|---|---:|---:|---|
| `clientes.csv` | 2.200 | 120 | Perfil do cliente |
| `enderecos_imoveis.csv` | 2.578 | 138 | Base principal: imóveis vinculados aos clientes |
| `sinais_imobiliarios.csv` | 2.578 | 138 | Pagamentos, créditos e gastos associados ao imóvel |
| `bens_compras.csv` | 8.988 | 494 | Registros de bens e estimativas de vínculo com o imóvel |
| `territorio.csv` | 2.578 | 138 | Localização e referências para enriquecimento |

**Resultado esperado, mantendo todos os imóveis:** 2.578 linhas na base de desenvolvimento e 138 na base de teste.

Na inspeção dos dois pacotes, não apareceram duplicidades nas chaves indicadas abaixo, imóveis sem cliente ou território, pares sem sinais, nem bens sem referência válida a um par cliente + imóvel. O script deve repetir essas verificações em cada execução.

## 3. Como ligar as tabelas

**Chave principal da consolidação: `cliente_id` + `imovel_id`.**

Embora `imovel_id` seja único nos arquivos atuais, usar o par deixa explícito de quem é o imóvel e reduz o risco de associar informações à pessoa errada.

| Ordem | Operação | Chave | Relação esperada |
|---|---|---|---|
| 1 | Começar por `enderecos_imoveis.csv` | `cliente_id`, `imovel_id` | Uma linha por par |
| 2 | Acrescentar `clientes.csv` | `cliente_id` | Vários imóveis para um cliente |
| 3 | Acrescentar `sinais_imobiliarios.csv` | `cliente_id`, `imovel_id` | Um registro de sinais por par |
| 4 | Acrescentar `territorio.csv` | `territorio_id` | Um registro territorial por identificador |
| 5 | Acrescentar **bens já agregados** | `cliente_id` + referência do imóvel | Um resumo de bens por par |

Nas junções, preservar todos os registros da base principal — comportamento de **junção à esquerda / left join**. Falhas de associação devem aparecer no relatório, sem excluir imóveis silenciosamente.

**Não juntar os bens diretamente à base principal:** isso criaria uma linha por bem e repetiria renda, imóvel e demais informações.

Também não usar município, CEP ou endereço textual como substitutos automáticos das chaves existentes. Um município pode ter vários imóveis e registros territoriais.

## 4. Como tratar os bens

Em `bens_compras.csv`, o imóvel aparece em **`imovel_id_referencia`**. Agrupar primeiro por:

```text
cliente_id + imovel_id_referencia
```

Depois, ligar esse resumo ao `cliente_id` + `imovel_id` da base principal.

| Resumo proposto | Colunas de origem | Utilidade |
|---|---|---|
| Quantidade de registros de bens | `bem_id` | Entender o volume de informação disponível |
| Quantidade por categoria | `tipo_bem` | Identificar composição dos bens |
| Soma dos valores cadastrados | `valor_cadastrado` | Referência do valor registrado |
| Soma dos valores ponderados | `valor_bem_ponderado_referencia` | Referência estimada, considerando o vínculo informado na base |
| Somas por categoria | `tipo_bem` e campos de valor | Apoiar o dimensionamento das coberturas |
| Quantidade por confiança de vínculo | `nivel_confianca_vinculo` | Mostrar a qualidade das associações |

Categorias encontradas: `ELETRODOMESTICO`, `ELETRONICO`, `MOVEL` e `ITEM_LAZER`. Confianças encontradas: `ALTA`, `MEDIA` e `BAIXA`.

Cuidados:

- Manter separadas as somas de valor cadastrado e valor ponderado. Nenhuma delas comprova o inventário completo do imóvel.
- `valor_bem_ponderado_referencia` já vem ponderado. Não multiplicá-lo novamente por `probabilidade_bem_no_imovel_referencia`.
- Não somar automaticamente esses valores às colunas `compras_moveis_36m`, `compras_eletrodomesticos_36m` e `compras_eletronicos_36m`: pode haver sobreposição, além da diferença de período.
- Preservar o detalhe por bem em uma tabela auxiliar. A linha consolidada resume, mas a Bússola pode precisar consultar ou corrigir um vínculo específico.
- Se aparecer bem sem vínculo válido, registrar a pendência. Não distribuir o bem entre todos os imóveis do cliente.
- Zero registros associados significa ausência de registros encontrados; não comprova que o imóvel esteja sem bens.

## 5. Quais informações cada módulo precisa encontrar

Os nomes desta tabela são **campos existentes**, não novas variáveis já aprovadas.

| Grupo | Principais campos de origem | Como ajudam |
|---|---|---|
| Identificação | `cliente_id`, `imovel_id`, `territorio_id` | Localizar o perfil e evitar mistura entre imóveis |
| Capacidade financeira | `renda_mensal`, `origem_renda`, `confianca_renda` | Apoiar avaliação de capacidade e qualidade da informação pelo motor |
| Perfil e relacionamento | `idade`, `quantidade_dependentes`, `possui_pet_informado`, `possui_seguro_residencial`, `qtd_produtos_seguridade` | Contextualizar necessidades sem repetir perguntas já respondidas |
| Canal digital | `indice_maturidade_digital`, `usuario_app`, `frequencia_acesso_app_90d` | Apoiar a experiência de atendimento |
| Endereço e indícios de tipo | `complemento`, `possui_termo_apartamento`, `possui_termo_casa`, `possui_termo_bloco`, `possui_termo_condominio` | Sugerir tipo de imóvel e evitar perguntas desnecessárias |
| Área | `area_cadastrada_m2`, `origem_area`, `confianca_area` | Apoiar estimativas de reconstrução e indicar necessidade de confirmação |
| Construção e cadastro | `padrao_construtivo_cadastrado`, `material_parede_externa_cadastrado`, `situacao_imovel_cadastral` | Alimentar verificações e identificar possíveis esclarecimentos |
| Indícios de vínculo e uso | `pagamento_aluguel_recorrente`, `credito_recorrente_compativel_aluguel`, `parcela_financiamento_imobiliario`, `endereco_principal_compativel` | Fornecer sinais ao motor e à Bússola; não equivalem a vínculo confirmado |
| Despesas e intervenções | `pagamento_condominio_mensal`, `pagamento_iptu_anual`, `energia_media_mensal_6m`, `agua_media_mensal_6m`, `gastos_material_construcao_24m`, `gastos_vidracaria_24m` | Contextualizar o imóvel e orientar esclarecimentos quando relevantes |
| Bens | Resumos da seção 4 | Apoiar estimativas de conteúdo e perguntas sobre lacunas relevantes |
| Localização | `codigo_ibge_municipio`, `municipio_real`, `uf_real`, `cep_agregado`, `latitude_aproximada`, `longitude_aproximada`, `chave_enriquecimento_publico` | Permitir enriquecimento territorial com o nível de precisão disponível |

As demais colunas também precisam constar no dicionário, mesmo que não sejam usadas inicialmente. Nenhuma deve desaparecer sem uma decisão documentada.

## 6. Regras de qualidade que evitam erros

| Situação | Tratamento recomendado |
|---|---|
| Identificadores, CEP e código IBGE | Ler como texto, preservando zeros à esquerda |
| Valores monetários e área | Ler como números, com unidade registrada no dicionário |
| Área igual a zero com origem `NAO_DISPONIVEL` | Tratar como área indisponível para consumo; preservar o valor original e a origem |
| Gastos iguais a zero | Não converter automaticamente em ausência: zero pode ser válido |
| Vazio, `NAO`, `NAO_DISPONIVEL` e `NAO_SE_APLICA` | Interpretar por campo; não transformar tudo em uma mesma resposta |
| Chave duplicada onde deveria ser única | Registrar erro e interromper a saída final até resolver; não escolher uma linha arbitrariamente |
| Município, UF, CEP ou IBGE presentes em imóveis e território | Comparar as fontes, manter origem explícita e registrar divergências antes de escolher um valor canônico |
| Categoria ou formato inesperado | Registrar para revisão, sem correção silenciosa |
| Valores extremos | Sinalizar; não apagar ou limitar o dado original automaticamente |

O script deve validar a leitura do CSV, incluindo codificação, separador e formato decimal. Evitar conversões que funcionem sem erro, mas alterem o significado dos dados.

### Um indício não deve virar uma confirmação

| Informação disponível | Limite da interpretação |
|---|---|
| “Bloco B, apartamento 512” | Sugere apartamento; não comprova propriedade, ocupação ou uso |
| Ausência de parcela de financiamento | Não comprova imóvel quitado |
| Gasto com construção nos últimos 24 meses | Não comprova obra em andamento |
| `possui_seguro_residencial` no cliente | Não identifica automaticamente o imóvel segurado, a seguradora ou a cobertura |
| Situação cadastral regular | Não comprova condições estruturais ou toda a regularidade jurídica |
| Código de município | Não comprova localização urbana do imóvel |

## 7. Separar fato, estimativa e resposta do cliente

A consolidação não deve sobrescrever um dado de origem com uma inferência sem deixar rastro.

Exemplo de organização **proposta**:

| Informação | Exemplo de nome novo | Observação |
|---|---|---|
| Indício calculado | `der_tipo_imovel` | Apartamento sugerido pelo endereço |
| Estimativa | `est_valor_conteudo` | Valor calculado por método documentado |
| Resposta do cliente | `decl_tipo_imovel` | Informação declarada durante a Bússola |
| Controle | `ctrl_versao_perfil` | Revisão do perfil usada na avaliação |

**Combinar os nomes com o Pippo antes de fixar o contrato.** Se a equipe preferir `conf_` para respostas confirmadas, documentar isso e usar outro nome para confiança estatística. Não manter duas convenções para o mesmo conceito.

Para informações importantes, guardar a origem, a data de referência quando disponível e a confiança aplicável ao campo. Não inventar uma confiança única para toda a linha.

Dados de cliente, como renda, aparecerão repetidos nos seus imóveis. Essas repetições são esperadas para consulta, mas **não devem ser somadas como se representassem clientes diferentes** em análises posteriores.

## 8. Dicionário mínimo de colunas

Entregar um dicionário junto com a base:

| Item | O que registrar |
|---|---|
| Nome final | Nome exato da coluna entregue |
| Significado e nível | O que representa; se é do cliente, imóvel ou item |
| Tipo e unidade | Texto, número, categoria; reais, m², quantidade etc. |
| Origem | Arquivo e coluna original |
| Transformação | Cópia, conversão, agrupamento ou cálculo aplicado |
| Ausência e categorias | Como interpretar vazio, zero e valores especiais |
| Natureza | Observado, derivado, estimado ou declarado |
| Consumidor | Bússola, motor, ambos ou apenas auditoria |

Se houver mudança de nome, manter o mapeamento de origem para destino. Se houver cálculo, registrar sua fórmula e versão.

## 9. Conferências obrigatórias na saída

- [ ] Uma linha por `cliente_id` + `imovel_id`, sem duplicidades.
- [ ] Todos os pares da tabela principal foram preservados.
- [ ] Desenvolvimento com **2.578 linhas** e teste com **138 linhas**, para os pacotes atuais.
- [ ] Cada junção mantém a quantidade de linhas da base principal.
- [ ] Chaves sem correspondência são identificadas e contabilizadas.
- [ ] Quantidades e somas dos bens antes e depois da agregação são reconciliadas, considerando arredondamentos documentados.
- [ ] Não há multiplicação de valores causada por junções.
- [ ] Ausência de informação continua diferente de uma resposta negativa ou de zero válido.
- [ ] Todas as colunas finais estão descritas no dicionário.
- [ ] Reexecução com a mesma entrada produz o mesmo resultado, com ordenação e regras determinísticas.
- [ ] O relatório informa pacote de origem, versão do script/esquema, contagens e alertas.

**Desenvolvimento e teste devem gerar saídas separadas.** Aplicar o mesmo esquema e transformações determinísticas nos dois. Se houver pré-processamento aprendido, como imputação por mediana, seus parâmetros devem ser ajustados somente no desenvolvimento e depois aplicados ao teste. Previsões e resultados do motor não devem voltar como atributos de entrada do treinamento.

## 10. O que combinar com a equipe antes de fechar

| Combinar | Proposta inicial |
|---|---|
| Unidade da linha | Cliente + imóvel |
| Formato de consumo | CSV ou Parquet, conforme necessidade dos módulos |
| Nomes novos | Uma convenção compartilhada, documentada |
| Acesso ao detalhe dos bens | Manter tabela auxiliar consultável |
| Atualizações da Bússola | Guardar declarações sem alterar os arquivos originais e identificar a revisão do perfil |
| Resultados do motor | Guardar com a revisão do perfil e a versão do motor; preferencialmente separados da entrada |
| Regras e catálogo | Manter separados da consolidação, evitando repetição de linhas por produto ou cobertura |

### Entrega esperada do Garrido

1. **Script de unificação**, com entrada e saída definidas.
2. **Base consolidada de desenvolvimento** e **base consolidada de teste**.
3. **Dicionário de colunas e transformações**.
4. **Relatório de qualidade**, com contagens, duplicidades, ausências, divergências e reconciliação dos bens.
5. **Detalhe dos bens preservado**, para consulta e revisão de vínculos.

**Responsabilidades:** Garrido consolida e valida os dados; a Bússola resolve lacunas relevantes; Pippo aplica o motor de score e machine learning; Henrique apresenta a experiência na interface.
