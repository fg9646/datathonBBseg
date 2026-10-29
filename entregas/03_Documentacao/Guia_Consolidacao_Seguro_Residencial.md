# Consolidação do Seguro Residencial

Foram geradas duas visões de trabalho, a partir dos ZIPs originais, sem modificar as fontes.
O arquivo recebido chama-se Desenvolvimento. Ele corresponde à primeira base mencionada como Demonstração na solicitação.
A consolidação foi feita com auxílio de IA (ChatGPT/Codex).

- Seguro_Residencial_Desenvolvimento_Consolidado.csv: 2,578 linhas, 200 colunas; 8,988 bens preservados.
- Seguro_Residencial_Teste_Comum_Consolidado.csv: 138 linhas, 200 colunas; 494 bens preservados.

## Unidade de registro e chaves

Uma linha representa exatamente um par cliente–imóvel. ID = cliente_id + '__' + imovel_id.
Exemplo: CLI_00001__IMO_CLI_00001_01. Os códigos originais e territorio_id continuam disponíveis.
Clientes com mais de um imóvel têm uma linha para cada imóvel.
Clientes são unidos por cliente_id; sinais são unidos por cliente_id + imovel_id; território por territorio_id.
Bens são associados exclusivamente por cliente_id + imovel_id_referencia, antes de qualquer resumo.
O cadastro de imóveis determina o universo e a ordem das linhas.
Os dois CSVs têm exatamente as mesmas colunas, na mesma ordem.

## Grupos de colunas

| Grupo | Colunas |
| --- | ---: |
| Identificação | 4 |
| Dados observados | 77 |
| Dados derivados | 23 |
| Estimativas | 25 |
| Respostas confirmadas | 7 |
| Controle | 50 |
| Resultado do motor | 14 |

Os prefixos obs_, der_, est_, conf_, ctl_ e motor_ identificam a natureza do campo.
A classificação considera o dicionário da base e, no caso da renda, a origem informada em cada registro.
Renda INFORMADA fica em obs_renda_mensal_informada.
Renda PRESUMIDA_COM_BASE_EM_MOVIMENTACAO fica em est_renda_mensal_presumida.
A outra coluna de renda permanece vazia. Isso não representa renda zero.
Índice de maturidade digital é derivado. Coordenadas aproximadas, probabilidades e valores ponderados são estimativas existentes na fonte.

## Bens

Os 6 blocos numerados preservam todos os atributos dos bens, em ordem crescente de bem_id dentro do par.
O número do bloco é apenas uma posição. O tipo do bem está na própria coluna tipo_bem.
Quando um imóvel tem menos bens, os blocos restantes ficam vazios, sem inventar bens ou valores.
A confiança de cada vínculo fica em ctl_bem_N_nivel_confianca_vinculo.
Contagens e somas por imóvel e por tipo são campos derivados.
Somente valores_cadastrados da mesma tabela são somados: compras de 36 meses e gastos de outras tabelas não entram nessa soma.
O total cadastrado de bens associados não comprova que todos estejam fisicamente no imóvel.
O total ponderado é a soma exata de valor_bem_ponderado_referencia da fonte, sem recalcular nem arredondar.
Esse total não é um limite inferior de faixa, nem o preço de reposição.
est_valor_bens_min e est_valor_bens_max ficam vazios, com status NAO_CALCULADO, até existir um método de estimação definido.

## Ausência e estados

- NAO: resposta negativa explícita existente na fonte; não equivale a falta de informação.
- DESCONHECIDO: informação indisponível ou dúvida explícita. Para material, padrão e área, há um status cadastral próprio.
- NAO_COLETADO: respostas de confirmação ainda não coletadas pela Bússola.
- NAO_CALCULADO: inferência ou faixa ainda não produzida.
- NAO_EXECUTADO / NAO_EXECUTADA: motor / Bússola ainda não executados.
- DISPONIVEL: valor cadastral está disponível conforme sua origem.

Os marcadores originais NAO_DISPONIVEL e os zeros das fontes foram preservados.
Em particular, area_cadastrada_m2 = 0 com origem_area = NAO_DISPONIVEL significa área desconhecida.
Um campo numérico vazio deve ser lido como nulo, nunca convertido automaticamente em zero.
Para os blocos de bens inexistentes, vazio significa que não existe aquele registro, não um bem desconhecido.
obs_complemento = SEM_COMPLEMENTO, quando presente, continua sendo o valor original.

## Confirmação, avaliação e motor

Campos conf_ estão vazios, com ctl_status_conf_CAMPO = NAO_COLETADO. Não há entrevistas nos ZIPs.
Campos sugeridos e resultados do motor também ficam vazios. Não foram inferidos tipo, uso, vínculo, elegibilidade, plano ou scores.
O grupo deve definir no motor a política de escolha entre cadastro, estimativa e confirmação.
A consolidação preserva as alternativas; não cria silenciosamente uma regra de negócio ou escolhe um valor efetivo.
Uma resposta coletada com conteúdo desconhecido deve usar status DESCONHECIDO.
Uma resposta negativa explícita usa valor NAO e status INFORMADO.
Valores confirmados devem ser adicionados em conf_ sem apagar obs_ ou est_.
Os campos scores_json e pendencias_json, quando preenchidos, devem conter JSON válido; inicialmente ficam vazios, sem simular uma lista vazia de pendências.
Catálogo de produtos e regras continuam separados e não são repetidos por perfil.
Dicionário original, catálogo e templates são arquivos de apoio, não fontes de observações a juntar como novas linhas.

## Revisões e datas

ctl_versao_schema = 0.2.0.
ctl_revisao_base identifica os bytes exatos do ZIP por SHA-256.
ctl_revisao_perfil identifica o conteúdo original de cada perfil e a versão do schema por SHA-256 canônico.
ctl_consolidado_em registra o processamento em UTC. Não é a data de atualização dos dados originais.
A atualização na origem não foi informada: ctl_dados_atualizados_em fica vazio.
Bússola e motor devem registrar a revisão consumida nos campos próprios.
Estes CSVs são snapshots estáticos. O hash inicial não muda sozinho ao editar o arquivo.
Ao incorporar confirmações ou alterar um perfil, a aplicação deve gerar uma nova revisão do conteúdo completo, incluindo confirmações e estados, e invalidar ou recalcular resultados antigos.
A validação mecânica das junções não equivale a revisão de negócio: ctl_status_revisao começa em NAO_REVISADO.
Não foi criada uma confiança geral artificial; permanecem as confianças específicas da fonte.

## Formato

CSV separado por vírgula, UTF-8 com BOM e quebras de linha CRLF.
Decimais usam ponto. Aspas e vírgulas em texto seguem o padrão CSV.
Não foi gerado XLSX. Para abrir no Excel, importar como UTF-8 e selecionar o separador vírgula.
Código IBGE, número do endereço e todos os IDs devem ser tratados como texto.
As fontes são fictícias conforme o LEIA-ME dos pacotes. Não houve enriquecimento externo.

## Dicionário das colunas finais

| Coluna | Grupo | Origem | Regra ou significado |
| --- | --- | --- | --- |
| ID | Identificação | enderecos_imoveis.csv | cliente_id + '__' + imovel_id |
| cliente_id | Identificação | enderecos_imoveis.csv | Identificador original, preservado como texto |
| imovel_id | Identificação | enderecos_imoveis.csv | Identificador original, preservado como texto |
| territorio_id | Identificação | enderecos_imoveis.csv | Identificador original, preservado como texto |
| obs_idade | Dados observados | clientes.csv.idade | Valor original; sem recálculo |
| obs_renda_mensal_informada | Dados observados | clientes.csv.renda_mensal | Somente quando origem_renda = INFORMADA |
| obs_usuario_app | Dados observados | clientes.csv.usuario_app | Valor original; sem recálculo |
| obs_frequencia_acesso_app_90d | Dados observados | clientes.csv.frequencia_acesso_app_90d | Valor original; sem recálculo |
| obs_quantidade_dependentes | Dados observados | clientes.csv.quantidade_dependentes | Valor original; sem recálculo |
| obs_possui_pet_informado | Dados observados | clientes.csv.possui_pet_informado | Valor original; sem recálculo |
| obs_qtd_produtos_seguridade | Dados observados | clientes.csv.qtd_produtos_seguridade | Valor original; sem recálculo |
| obs_possui_seguro_residencial | Dados observados | clientes.csv.possui_seguro_residencial | Valor original; sem recálculo |
| obs_logradouro | Dados observados | enderecos_imoveis.csv.logradouro | Valor original; sem recálculo |
| obs_numero | Dados observados | enderecos_imoveis.csv.numero | Valor original; sem recálculo |
| obs_complemento | Dados observados | enderecos_imoveis.csv.complemento | Valor original; sem recálculo |
| obs_bairro | Dados observados | enderecos_imoveis.csv.bairro | Valor original; sem recálculo |
| obs_municipio_real | Dados observados | enderecos_imoveis.csv.municipio_real | Valor original; sem recálculo |
| obs_uf_real | Dados observados | enderecos_imoveis.csv.uf_real | Valor original; sem recálculo |
| obs_codigo_ibge_municipio | Dados observados | enderecos_imoveis.csv.codigo_ibge_municipio | Valor original; sem recálculo |
| obs_cep_agregado | Dados observados | enderecos_imoveis.csv.cep_agregado | Valor original; sem recálculo |
| obs_endereco_principal_compativel | Dados observados | enderecos_imoveis.csv.endereco_principal_compativel | Valor original; sem recálculo |
| obs_possui_termo_apartamento | Dados observados | enderecos_imoveis.csv.possui_termo_apartamento | Valor original; sem recálculo |
| obs_possui_termo_casa | Dados observados | enderecos_imoveis.csv.possui_termo_casa | Valor original; sem recálculo |
| obs_possui_termo_bloco | Dados observados | enderecos_imoveis.csv.possui_termo_bloco | Valor original; sem recálculo |
| obs_possui_termo_condominio | Dados observados | enderecos_imoveis.csv.possui_termo_condominio | Valor original; sem recálculo |
| obs_area_cadastrada_m2 | Dados observados | enderecos_imoveis.csv.area_cadastrada_m2 | Valor original; sem recálculo |
| obs_padrao_construtivo_cadastrado | Dados observados | enderecos_imoveis.csv.padrao_construtivo_cadastrado | Valor original; sem recálculo |
| obs_material_parede_externa_cadastrado | Dados observados | enderecos_imoveis.csv.material_parede_externa_cadastrado | Valor original; sem recálculo |
| obs_situacao_imovel_cadastral | Dados observados | enderecos_imoveis.csv.situacao_imovel_cadastral | Valor original; sem recálculo |
| obs_pagamento_aluguel_recorrente | Dados observados | sinais_imobiliarios.csv.pagamento_aluguel_recorrente | Valor original; sem recálculo |
| obs_valor_aluguel_recorrente | Dados observados | sinais_imobiliarios.csv.valor_aluguel_recorrente | Valor original; sem recálculo |
| obs_credito_recorrente_compativel_aluguel | Dados observados | sinais_imobiliarios.csv.credito_recorrente_compativel_aluguel | Valor original; sem recálculo |
| obs_valor_medio_credito_recorrente | Dados observados | sinais_imobiliarios.csv.valor_medio_credito_recorrente | Valor original; sem recálculo |
| obs_quantidade_creditos_recorrentes_12m | Dados observados | sinais_imobiliarios.csv.quantidade_creditos_recorrentes_12m | Valor original; sem recálculo |
| obs_parcela_financiamento_imobiliario | Dados observados | sinais_imobiliarios.csv.parcela_financiamento_imobiliario | Valor original; sem recálculo |
| obs_pagamento_condominio_mensal | Dados observados | sinais_imobiliarios.csv.pagamento_condominio_mensal | Valor original; sem recálculo |
| obs_pagamento_iptu_anual | Dados observados | sinais_imobiliarios.csv.pagamento_iptu_anual | Valor original; sem recálculo |
| obs_energia_media_mensal_6m | Dados observados | sinais_imobiliarios.csv.energia_media_mensal_6m | Valor original; sem recálculo |
| obs_agua_media_mensal_6m | Dados observados | sinais_imobiliarios.csv.agua_media_mensal_6m | Valor original; sem recálculo |
| obs_internet_mensal | Dados observados | sinais_imobiliarios.csv.internet_mensal | Valor original; sem recálculo |
| obs_compras_moveis_36m | Dados observados | sinais_imobiliarios.csv.compras_moveis_36m | Valor original; sem recálculo |
| obs_compras_eletrodomesticos_36m | Dados observados | sinais_imobiliarios.csv.compras_eletrodomesticos_36m | Valor original; sem recálculo |
| obs_compras_eletronicos_36m | Dados observados | sinais_imobiliarios.csv.compras_eletronicos_36m | Valor original; sem recálculo |
| obs_gastos_material_construcao_24m | Dados observados | sinais_imobiliarios.csv.gastos_material_construcao_24m | Valor original; sem recálculo |
| obs_gastos_vidracaria_24m | Dados observados | sinais_imobiliarios.csv.gastos_vidracaria_24m | Valor original; sem recálculo |
| obs_bem_1_id | Dados observados | bens_compras.csv.bem_id | 1º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_1_tipo_bem | Dados observados | bens_compras.csv.tipo_bem | 1º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_1_valor_cadastrado | Dados observados | bens_compras.csv.valor_cadastrado | 1º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_1_mesma_uf_imovel | Dados observados | bens_compras.csv.mesma_uf_imovel | 1º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_1_mesmo_municipio_imovel | Dados observados | bens_compras.csv.mesmo_municipio_imovel | 1º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_1_bem_financiado_pelo_banco | Dados observados | bens_compras.csv.bem_financiado_pelo_banco | 1º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_2_id | Dados observados | bens_compras.csv.bem_id | 2º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_2_tipo_bem | Dados observados | bens_compras.csv.tipo_bem | 2º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_2_valor_cadastrado | Dados observados | bens_compras.csv.valor_cadastrado | 2º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_2_mesma_uf_imovel | Dados observados | bens_compras.csv.mesma_uf_imovel | 2º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_2_mesmo_municipio_imovel | Dados observados | bens_compras.csv.mesmo_municipio_imovel | 2º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_2_bem_financiado_pelo_banco | Dados observados | bens_compras.csv.bem_financiado_pelo_banco | 2º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_3_id | Dados observados | bens_compras.csv.bem_id | 3º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_3_tipo_bem | Dados observados | bens_compras.csv.tipo_bem | 3º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_3_valor_cadastrado | Dados observados | bens_compras.csv.valor_cadastrado | 3º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_3_mesma_uf_imovel | Dados observados | bens_compras.csv.mesma_uf_imovel | 3º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_3_mesmo_municipio_imovel | Dados observados | bens_compras.csv.mesmo_municipio_imovel | 3º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_3_bem_financiado_pelo_banco | Dados observados | bens_compras.csv.bem_financiado_pelo_banco | 3º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_4_id | Dados observados | bens_compras.csv.bem_id | 4º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_4_tipo_bem | Dados observados | bens_compras.csv.tipo_bem | 4º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_4_valor_cadastrado | Dados observados | bens_compras.csv.valor_cadastrado | 4º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_4_mesma_uf_imovel | Dados observados | bens_compras.csv.mesma_uf_imovel | 4º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_4_mesmo_municipio_imovel | Dados observados | bens_compras.csv.mesmo_municipio_imovel | 4º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_4_bem_financiado_pelo_banco | Dados observados | bens_compras.csv.bem_financiado_pelo_banco | 4º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_5_id | Dados observados | bens_compras.csv.bem_id | 5º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_5_tipo_bem | Dados observados | bens_compras.csv.tipo_bem | 5º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_5_valor_cadastrado | Dados observados | bens_compras.csv.valor_cadastrado | 5º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_5_mesma_uf_imovel | Dados observados | bens_compras.csv.mesma_uf_imovel | 5º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_5_mesmo_municipio_imovel | Dados observados | bens_compras.csv.mesmo_municipio_imovel | 5º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_5_bem_financiado_pelo_banco | Dados observados | bens_compras.csv.bem_financiado_pelo_banco | 5º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_6_id | Dados observados | bens_compras.csv.bem_id | 6º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_6_tipo_bem | Dados observados | bens_compras.csv.tipo_bem | 6º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_6_valor_cadastrado | Dados observados | bens_compras.csv.valor_cadastrado | 6º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_6_mesma_uf_imovel | Dados observados | bens_compras.csv.mesma_uf_imovel | 6º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_6_mesmo_municipio_imovel | Dados observados | bens_compras.csv.mesmo_municipio_imovel | 6º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| obs_bem_6_bem_financiado_pelo_banco | Dados observados | bens_compras.csv.bem_financiado_pelo_banco | 6º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| der_indice_maturidade_digital | Dados derivados | clientes.csv.indice_maturidade_digital | Valor original; sem recálculo |
| der_quantidade_bens_referencia | Dados derivados | bens_compras.csv | Contagem por cliente_id + imovel_id_referencia |
| der_valor_bens_cadastrado_total_referencia | Dados derivados | bens_compras.csv.valor_cadastrado | Soma por cliente_id + imovel_id_referencia; não comprova presença física |
| der_quantidade_bens_eletrodomestico_referencia | Dados derivados | bens_compras.csv | Contagem do tipo por cliente–imóvel |
| der_valor_bens_eletrodomestico_cadastrado_referencia | Dados derivados | bens_compras.csv | Soma de valor_cadastrado do tipo por cliente–imóvel |
| der_quantidade_bens_eletronico_referencia | Dados derivados | bens_compras.csv | Contagem do tipo por cliente–imóvel |
| der_valor_bens_eletronico_cadastrado_referencia | Dados derivados | bens_compras.csv | Soma de valor_cadastrado do tipo por cliente–imóvel |
| der_quantidade_bens_item_lazer_referencia | Dados derivados | bens_compras.csv | Contagem do tipo por cliente–imóvel |
| der_valor_bens_item_lazer_cadastrado_referencia | Dados derivados | bens_compras.csv | Soma de valor_cadastrado do tipo por cliente–imóvel |
| der_quantidade_bens_movel_referencia | Dados derivados | bens_compras.csv | Contagem do tipo por cliente–imóvel |
| der_valor_bens_movel_cadastrado_referencia | Dados derivados | bens_compras.csv | Soma de valor_cadastrado do tipo por cliente–imóvel |
| der_quantidade_bens_confianca_alta | Dados derivados | bens_compras.csv.nivel_confianca_vinculo | Contagem por nível de confiança do vínculo no par cliente–imóvel |
| der_quantidade_bens_confianca_media | Dados derivados | bens_compras.csv.nivel_confianca_vinculo | Contagem por nível de confiança do vínculo no par cliente–imóvel |
| der_quantidade_bens_confianca_baixa | Dados derivados | bens_compras.csv.nivel_confianca_vinculo | Contagem por nível de confiança do vínculo no par cliente–imóvel |
| der_quantidade_bens_confianca_desconhecida | Dados derivados | bens_compras.csv.nivel_confianca_vinculo | Contagem de confiança ausente/desconhecida ou categoria inválida; preserva a categoria original |
| der_quantidade_bens_confianca_invalida | Dados derivados | bens_compras.csv.nivel_confianca_vinculo | Contagem de confiança ausente/desconhecida ou categoria inválida; preserva a categoria original |
| der_quantidade_bens_probabilidade_valida | Dados derivados | bens_compras.csv.probabilidade_bem_no_imovel_referencia | Contagem por validade da probabilidade no par; 0 e 1 são válidos; ausência não é zero |
| der_quantidade_bens_probabilidade_ausente | Dados derivados | bens_compras.csv.probabilidade_bem_no_imovel_referencia | Contagem por validade da probabilidade no par; 0 e 1 são válidos; ausência não é zero |
| der_quantidade_bens_probabilidade_invalida | Dados derivados | bens_compras.csv.probabilidade_bem_no_imovel_referencia | Contagem por validade da probabilidade no par; 0 e 1 são válidos; ausência não é zero |
| der_area_cadastral_utilizavel_m2 | Dados derivados | enderecos_imoveis.csv.area_cadastrada_m2 + origem_area | Cópia da área cadastral positiva com origem disponível; nulo quando indisponível; não é estimativa |
| der_tipo_imovel_sugerido | Dados derivados |  | Reservado para inferência posterior; status em ctl_status_inferencias |
| der_uso_imovel_sugerido | Dados derivados |  | Reservado para inferência posterior; status em ctl_status_inferencias |
| der_tipo_vinculo_sugerido | Dados derivados |  | Reservado para inferência posterior; status em ctl_status_inferencias |
| est_renda_mensal_presumida | Estimativas | clientes.csv.renda_mensal | Somente quando origem_renda = PRESUMIDA_COM_BASE_EM_MOVIMENTACAO |
| est_latitude_aproximada | Estimativas | territorio.csv.latitude_aproximada | Valor original; sem recálculo |
| est_longitude_aproximada | Estimativas | territorio.csv.longitude_aproximada | Valor original; sem recálculo |
| est_bem_1_probabilidade_bem_no_imovel_referencia | Estimativas | bens_compras.csv.probabilidade_bem_no_imovel_referencia | 1º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_bem_1_valor_bem_ponderado_referencia | Estimativas | bens_compras.csv.valor_bem_ponderado_referencia | 1º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_bem_2_probabilidade_bem_no_imovel_referencia | Estimativas | bens_compras.csv.probabilidade_bem_no_imovel_referencia | 2º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_bem_2_valor_bem_ponderado_referencia | Estimativas | bens_compras.csv.valor_bem_ponderado_referencia | 2º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_bem_3_probabilidade_bem_no_imovel_referencia | Estimativas | bens_compras.csv.probabilidade_bem_no_imovel_referencia | 3º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_bem_3_valor_bem_ponderado_referencia | Estimativas | bens_compras.csv.valor_bem_ponderado_referencia | 3º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_bem_4_probabilidade_bem_no_imovel_referencia | Estimativas | bens_compras.csv.probabilidade_bem_no_imovel_referencia | 4º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_bem_4_valor_bem_ponderado_referencia | Estimativas | bens_compras.csv.valor_bem_ponderado_referencia | 4º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_bem_5_probabilidade_bem_no_imovel_referencia | Estimativas | bens_compras.csv.probabilidade_bem_no_imovel_referencia | 5º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_bem_5_valor_bem_ponderado_referencia | Estimativas | bens_compras.csv.valor_bem_ponderado_referencia | 5º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_bem_6_probabilidade_bem_no_imovel_referencia | Estimativas | bens_compras.csv.probabilidade_bem_no_imovel_referencia | 6º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_bem_6_valor_bem_ponderado_referencia | Estimativas | bens_compras.csv.valor_bem_ponderado_referencia | 6º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| est_valor_bens_ponderado_total_referencia | Estimativas | bens_compras.csv.valor_bem_ponderado_referencia | Soma dos valores ponderados já fornecidos; não é limite inferior nem faixa de valor |
| est_valor_bens_eletrodomestico_ponderado_referencia | Estimativas | bens_compras.csv.valor_bem_ponderado_referencia | Soma dos valores ponderados já fornecidos, do tipo e do par; sem ponderar novamente |
| est_valor_bens_eletronico_ponderado_referencia | Estimativas | bens_compras.csv.valor_bem_ponderado_referencia | Soma dos valores ponderados já fornecidos, do tipo e do par; sem ponderar novamente |
| est_valor_bens_item_lazer_ponderado_referencia | Estimativas | bens_compras.csv.valor_bem_ponderado_referencia | Soma dos valores ponderados já fornecidos, do tipo e do par; sem ponderar novamente |
| est_valor_bens_movel_ponderado_referencia | Estimativas | bens_compras.csv.valor_bem_ponderado_referencia | Soma dos valores ponderados já fornecidos, do tipo e do par; sem ponderar novamente |
| est_valor_bens_min | Estimativas |  | Reservado para estimativa de faixa; não calculado nesta consolidação |
| est_valor_bens_max | Estimativas |  | Reservado para estimativa de faixa; não calculado nesta consolidação |
| est_area_m2 | Estimativas |  | Reservado; nenhuma área é estimada nesta consolidação. Exige método e proveniência por perfil |
| est_area_min_m2 | Estimativas |  | Reservado; nenhuma área é estimada nesta consolidação. Exige método e proveniência por perfil |
| est_area_max_m2 | Estimativas |  | Reservado; nenhuma área é estimada nesta consolidação. Exige método e proveniência por perfil |
| conf_tipo_imovel | Respostas confirmadas |  | Resposta futura da Bússola, sem sobrescrever o cadastro; status individual em ctl_status_conf_tipo_imovel |
| conf_uso_imovel | Respostas confirmadas |  | Resposta futura da Bússola, sem sobrescrever o cadastro; status individual em ctl_status_conf_uso_imovel |
| conf_tipo_vinculo | Respostas confirmadas |  | Resposta futura da Bússola, sem sobrescrever o cadastro; status individual em ctl_status_conf_tipo_vinculo |
| conf_material_parede_externa | Respostas confirmadas |  | Resposta futura da Bússola, sem sobrescrever o cadastro; status individual em ctl_status_conf_material_parede_externa |
| conf_area_m2 | Respostas confirmadas |  | Resposta futura da Bússola, sem sobrescrever o cadastro; status individual em ctl_status_conf_area_m2 |
| conf_valor_bens | Respostas confirmadas |  | Resposta futura da Bússola, sem sobrescrever o cadastro; status individual em ctl_status_conf_valor_bens |
| conf_imovel_possui_seguro_residencial | Respostas confirmadas |  | Resposta futura da Bússola, sem sobrescrever o cadastro; status individual em ctl_status_conf_imovel_possui_seguro_residencial |
| ctl_origem_renda | Controle | clientes.csv.origem_renda | Valor original; sem recálculo |
| ctl_confianca_renda | Controle | clientes.csv.confianca_renda | Valor original; sem recálculo |
| ctl_origem_area | Controle | enderecos_imoveis.csv.origem_area | Valor original; sem recálculo |
| ctl_confianca_area | Controle | enderecos_imoveis.csv.confianca_area | Valor original; sem recálculo |
| ctl_chave_enriquecimento_publico | Controle | territorio.csv.chave_enriquecimento_publico | Valor original; sem recálculo |
| ctl_observacao_privacidade | Controle | territorio.csv.observacao_privacidade | Valor original; sem recálculo |
| ctl_orientacao_enriquecimento | Controle | territorio.csv.orientacao_enriquecimento | Valor original; sem recálculo |
| ctl_bem_1_nivel_confianca_vinculo | Controle | bens_compras.csv.nivel_confianca_vinculo | 1º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| ctl_bem_2_nivel_confianca_vinculo | Controle | bens_compras.csv.nivel_confianca_vinculo | 2º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| ctl_bem_3_nivel_confianca_vinculo | Controle | bens_compras.csv.nivel_confianca_vinculo | 3º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| ctl_bem_4_nivel_confianca_vinculo | Controle | bens_compras.csv.nivel_confianca_vinculo | 4º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| ctl_bem_5_nivel_confianca_vinculo | Controle | bens_compras.csv.nivel_confianca_vinculo | 5º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| ctl_bem_6_nivel_confianca_vinculo | Controle | bens_compras.csv.nivel_confianca_vinculo | 6º bem do par, em ordem de bem_id; vazio quando não existe esse bem |
| ctl_status_conf_tipo_imovel | Controle |  | NAO_COLETADO inicialmente; INFORMADO ou DESCONHECIDO após coleta |
| ctl_status_conf_uso_imovel | Controle |  | NAO_COLETADO inicialmente; INFORMADO ou DESCONHECIDO após coleta |
| ctl_status_conf_tipo_vinculo | Controle |  | NAO_COLETADO inicialmente; INFORMADO ou DESCONHECIDO após coleta |
| ctl_status_conf_material_parede_externa | Controle |  | NAO_COLETADO inicialmente; INFORMADO ou DESCONHECIDO após coleta |
| ctl_status_conf_area_m2 | Controle |  | NAO_COLETADO inicialmente; INFORMADO ou DESCONHECIDO após coleta |
| ctl_status_conf_valor_bens | Controle |  | NAO_COLETADO inicialmente; INFORMADO ou DESCONHECIDO após coleta |
| ctl_status_conf_imovel_possui_seguro_residencial | Controle |  | NAO_COLETADO inicialmente; INFORMADO ou DESCONHECIDO após coleta |
| ctl_versao_schema | Controle |  | Versão do contrato de colunas |
| ctl_revisao_base | Controle |  | SHA-256 dos bytes do ZIP original |
| ctl_revisao_perfil | Controle |  | SHA-256 canônico de schema, base e todos os registros originais do par |
| ctl_fonte_base | Controle |  | Nome do ZIP original |
| ctl_fontes_dados | Controle |  | Tabelas que alimentaram o perfil, separadas por / |
| ctl_consolidado_em | Controle |  | Instante de processamento UTC; não é a data de atualização dos dados |
| ctl_dados_atualizados_em | Controle |  | Não fornecido nas fontes; vazio |
| ctl_status_data_atualizacao | Controle |  | NAO_INFORMADO_NA_FONTE |
| ctl_status_revisao | Controle |  | NAO_REVISADO; validação mecânica não equivale à revisão de negócio |
| ctl_status_inferencias | Controle |  | NAO_CALCULADO |
| ctl_status_faixa_bens | Controle |  | NAO_CALCULADO |
| ctl_status_area_cadastrada | Controle |  | DESCONHECIDO quando origem_area = NAO_DISPONIVEL; DISPONIVEL nos demais |
| ctl_status_material_cadastrado | Controle |  | Vazio, espaços e marcadores documentados -> DESCONHECIDO; NAO_SE_APLICA é estado próprio; original preservado |
| ctl_status_padrao_cadastrado | Controle |  | Vazio, espaços e marcadores documentados -> DESCONHECIDO; NAO_SE_APLICA é estado próprio; original preservado |
| ctl_status_bussola | Controle |  | NAO_EXECUTADA |
| ctl_revisao_perfil_usada_bussola | Controle |  | Vazio até execução da Bússola; registrar revisão exata consumida |
| ctl_status_integridade_juncoes | Controle |  | VALIDADA após verificações de chaves, vínculos e duplicações |
| ctl_estimativa_area_status | Controle |  | NAO_CALCULADO quando falta área; NAO_NECESSARIO quando há área cadastral utilizável |
| ctl_estimativa_area_metodo | Controle |  | Vazio; preencher somente quando houver estimativa calculada |
| ctl_estimativa_area_formula | Controle |  | Vazio; fórmula exata ou identificação do modelo utilizado |
| ctl_estimativa_area_versao_metodo | Controle |  | Vazio; versão do método ou modelo |
| ctl_estimativa_area_dados_utilizados_json | Controle |  | Vazio; valores e identificadores exatos dos dados usados na estimativa |
| ctl_estimativa_area_parametros_json | Controle |  | Vazio; coeficientes ou parâmetros do método |
| ctl_estimativa_area_fonte_referencia | Controle |  | Vazio; arquivo/documento/URL e versão da referência |
| ctl_estimativa_area_data_referencia | Controle |  | Vazio; data dos dados/referências usados |
| ctl_estimativa_area_confianca | Controle |  | Vazio; não foi inventado um nível de confiança |
| ctl_estimativa_area_limitacoes | Controle |  | Vazio; hipóteses e limitações do método quando existir |
| ctl_status_qualidade_dados | Controle |  | SEM_PENDENCIAS_IDENTIFICADAS, COM_AUSENCIAS_CADASTRAIS ou COM_PENDENCIAS; não é elegibilidade |
| ctl_quantidade_ocorrencias_qualidade | Controle |  | Número de ocorrências técnicas ou ausências no perfil; não é quantidade de perguntas |
| ctl_ocorrencias_qualidade_json | Controle |  | Lista de ocorrências com origem, campo, valor original e motivo; não atribui P0, P1, P2 ou P3 |
| motor_elegivel | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_motivo_inelegibilidade | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_plano_recomendado | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_coberturas_recomendadas | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_confianca_geral | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_justificativa_recomendacao | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_perguntas_confirmacao | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_fontes_publicas_adicionais | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_scores_json | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_pendencias_json | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_versao_regras | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_revisao_perfil_avaliada | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_avaliado_em | Resultado do motor |  | Reservado para execução posterior; vazio |
| motor_status | Resultado do motor |  | NAO_EXECUTADO |

## Área e proveniência

Não foi estimada nenhuma área. est_area_m2, est_area_min_m2 e est_area_max_m2 estão vazios.
der_area_cadastral_utilizavel_m2 copia a área positiva quando sua origem está disponível; nos demais casos fica nulo.
Os campos ctl_estimativa_area_* reservam método, fórmula, versão, dados utilizados, parâmetros, referência, data, confiança e limitações.
O registro de proveniência inclui cada área original e cada campo estimado ou reservado, com ZIP, arquivo, chave e linha.
Quando a fórmula geradora de uma estimativa da fonte não foi fornecida, o registro informa NAO_DOCUMENTADA_NA_FONTE.
Uma área estimada futura exige definir o método, registrar seus dados e validar o erro nos imóveis com área conhecida.
Se houver treinamento ou calibração, usar somente Desenvolvimento para ajustar parâmetros; aplicar o método fixo no Teste Comum.
Não foi criada uma imputação por mediana, uma regressão nem uma relação presumida entre IPTU e área.

## Uso e arquivos de apoio

O script usa somente a biblioteca padrão do Python 3.10 ou superior, sem dependências externas.
As verificações são explícitas e permanecem ativas em todas as execuções do script.
Exemplo: python consolidar_seguro_residencial.py --entrada . --saida resultados
Para repetir a mesma data de processamento, informar o parâmetro mostrado no relatório de qualidade.
Nomes de novas colunas e schema 0.2.0 formam o layout técnico desta revisão; o contrato de integração continua pendente de alinhamento com a equipe.
conf_ significa resposta declarada pelo cliente, sem comprovação pericial nem confiança de 100%; confiança estatística usa nomes explícitos em ctl_.
O seguro no cadastro do cliente não é convertido em confirmação de seguro para cada imóvel.

- Dicionario_Colunas.csv: tipo, unidade, nível, origem, transformação, ausência, natureza e consumidor.
- Mapeamento_Origem_Destino.csv: mapeamento de todas as colunas das cinco fontes.
- Relatorio_Qualidade.json e .md: conferências e limitações.
- Registro_Proveniencia_Estimativas_e_Area.csv: linhagem das estimativas e da área, incluindo as que não foram calculadas.
- Alertas_Valores_Extremos.csv: alertas estatísticos para revisão, sem modificar valores.
- Bens_Detalhados_Desenvolvimento.csv e Bens_Detalhados_Teste_Comum.csv: todos os bens originais, com o par e o status do vínculo.

Os blocos numerados na base principal atendem à opção escolhida nesta conversa.
O detalhe auxiliar também atende ao guia e permite consultar um bem pelo identificador.
Os CSVs não implementam atualizações automáticas: a aplicação deve gerar nova revisão ao incorporar respostas.

## Correções da versão 0.2.0

Material e padrão vazios, com espaços ou marcadores de ausência são desconhecidos; o original é preservado.
NAO_SE_APLICA é mantido como estado próprio, sem confundir com NAO ou zero.
Probabilidades têm limites inclusivos 0 e 1. Não há recorte ou substituição de inválidos.
Confianças não reconhecidas não desaparecem: os totais incluem DESCONHECIDA e INVALIDA.
Cada bem tem status técnico no detalhe e cada perfil contém ocorrências de qualidade.
Quando um bloco tem bem_id, um campo vazio é dado ausente desse bem; somente um bloco sem bem_id representa ausência do registro.
A soma do valor ponderado fornecido continua sendo apenas reconciliação aritmética, não aprovação da estimativa original.
O layout tem 200 colunas fixas; mais de seis bens ou uma nova categoria vinculada requer revisão explícita do schema.
Consultar Politica_Validacao_Dados.json, Schema_Base_Consolidada.json, Alteracoes_por_Markdown.md e Alinhamento_Integracao.md.
