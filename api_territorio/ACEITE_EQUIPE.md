# Território — checklist de aceite da equipe

**Ponto 6: validação técnica concluída; aceite humano pendente.** Este documento acompanha o [relatório de validação](VALIDACAO.md) e o [registro das evidências](validacao/evidencias-ponto-6.json). Marcar uma verificação técnica não equivale à aprovação de uma pessoa.

Referência: contrato `1.0.0`, edição `territorio-2026-10-28-r1`, código validado `f1adf83c7b56464dd7b53203a88212fe7a786735`. As mudanças desta etapa são documentais. A equipe pode registrar a decisão neste arquivo ou no PR; neste último caso, incluir aqui o link da revisão quando o aceite for consolidado.

## Evidências técnicas já conferidas

- [x] 43 testes locais aprovados, sem falhas, erros ou testes ignorados, incluindo conexão HTTPS real.
- [x] Dez municípios e 180 registros conferidos: 153 valores, 27 ausências explícitas, períodos e metadados preservados.
- [x] Lacuna, município sem cobertura e falha técnica distinguíveis; ausência não convertida em zero.
- [x] Autenticação, restrição de transporte, limite por consumidor e erros conferidos conforme a matriz do relatório.
- [x] OpenAPI e quatro exemplos versionados conferidos com respostas da implementação local.
- [x] Edição congelada e `entregas/` preservadas; integridade e hashes documentados.
- [x] Nenhum serviço pago ou nova dependência; hospedagem externa ainda pendente.
- [x] Nenhuma alteração no motor ou na Bússola; nenhum segredo de produção publicado.

## Revisão humana a registrar

Responsáveis abaixo são papéis propostos, não aprovações atribuídas a pessoas.

- [ ] **Enriquecimento:** confirmar catálogo, unidades e períodos, as 27 ausências e as limitações de Recife, Fortaleza e Goiânia.
- [ ] **Responsável pela API:** revisar as evidências de consulta, acesso, HTTPS e falhas; confirmar os limites de uma única instância e o procedimento de preparação local.
- [ ] **Pipo / representante dos consumidores:** revisar formato, exemplos e significado de `null`, 200 sem cobertura, 404, 429 e 503. Esta leitura não comprova integração do consumidor.
- [ ] **Equipe:** reconhecer abrangência municipal/DF e ausência de validação de endereço ou elegibilidade, especialmente com localização mascarada.
- [ ] **Equipe:** confirmar que a publicação seguirá gratuita; a escolha de hospedagem, URL, capacidade e credenciais pertence ao ponto 7.
- [ ] **Responsável pelo aceite:** registrar decisão, data, edição/commit e eventuais ressalvas na tabela abaixo ou em revisão vinculada do PR.

| Papel | Nome | Decisão | Data | Evidência / ressalvas |
|---|---|---|---|---|
| Enriquecimento | A preencher | Pendente | — | — |
| Responsável pela API | A preencher | Pendente | — | — |
| Pipo / representante dos consumidores | A preencher | Pendente | — | — |
| Consolidação do aceite | A preencher | Pendente | — | — |

Decisões possíveis: **aprovado**, **aprovado com ressalvas** ou **ajustes necessários**. Ressalvas devem ter responsável, impacto e próxima ação. Se afetarem formato ou significado, alinhar e versionar o contrato; se afetarem valores, criar nova edição, sem alterar o snapshot congelado. Mudanças executáveis exigem nova validação dos critérios afetados.

## Próximas entregas, fora do aceite técnico local

- [ ] **Ponto 7:** publicar ambiente gratuito com HTTPS; definir limites e verificar o acesso externo e o proxy, quando aplicável.
- [ ] **Ponto 8:** entregar URL, instruções e credenciais por canal seguro ao Pipo; definir contatos de suporte.
- [ ] **Ponto 9:** validar nos consumidores o tempo limite, até uma repetição transitória e continuidade sem enriquecimento, sem interpretar falha ou ausência como risco zero.
- [ ] **Ponto 10:** registrar responsáveis e rotina de manutenção/atualização.

**Situação atual:** evidências e checklist preparados para revisão. Nenhuma confirmação humana foi recebida ou fabricada nesta etapa; aprovar este checklist não realiza merge, publicação ou integração.
