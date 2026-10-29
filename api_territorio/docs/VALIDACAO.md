# Validação local e limites da entrega

**API funcional validada localmente**, sem serviço hospedado, integração real ou aceite de produção. Este relatório separa novas verificações dos registros históricos; não atribui aprovações humanas.

## Referência e resultados atuais

<!-- RESULTADO_ATUAL -->
Execução em `2026-10-29T05:35:35.988714+00:00` (UTC), Windows/Python 3.12.14: **53 testes aprovados, zero falhas, erros ou ignorados**. `pip check`, auditor de integridade dos 21 arquivos, manifesto dos 32 itens de `entregas/`, ZIP e comparação completa dos 180 registros/metadados aprovados. Foram conferidos 76 links locais e os quatro exemplos/OpenAPI.

[Evidência desta revisão](../validacao/revisao-documental-2026-10-29.json): referência Git anterior e hashes dos fontes efetivamente testados. Comparação de AST dos arquivos Python confirmou execução idêntica à `main`, ignorando somente docstrings; outras seções do README geral foram preservadas. A evidência registra a versão testada, sem substituir os registros anteriores.
<!-- FIM_RESULTADO_ATUAL -->

Critérios conferidos: fidelidade dos 180 registros e metadados, três cenários de dados/cobertura, entrada e erros, autenticação, HTTPS local real, limites, SQLite e perfil opcional de hospedagem. O teste TLS gera certificado temporário com OpenSSL e valida certificado/nome do servidor; não usa `verify=False`. Arquivos temporários são removidos ao final.

## Reprodução

No ambiente de [execução local](EXECUCAO_LOCAL.md), na raiz do repositório:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\python.exe -X utf8 auditoria/validar_congelar_base.py --verificar-integridade dados/edicoes/territorio-2026-10-28-r1
git diff --exit-code origin/main -- dados/edicoes/territorio-2026-10-28-r1 entregas
```

A suíte usa bancos temporários e credenciais sintéticas; testa conexões em loopback, incluindo o processo do perfil Render com metadados simulados. Não acessa conta de hospedagem ou coleta novas fontes. O auditor acima só verifica integridade; não reexecuta a auditoria completa do acervo original.

## Preservação e resultados de dados

- Edição `territorio-2026-10-28-r1`: **21 arquivos**, 180 registros, 153 valores e 27 ausências (5 `FONTE_SEM_VALOR`, 22 `SEM_RECORTE_RESIDENCIAL`). Contagens por município em [dados](DADOS.md).
- Árvore Git da edição: `df17da987013eff027e352788a98cb68b1646f57`.
- `entregas/`: **32 itens** do manifesto conferidos por tamanho/SHA-256, mais o ZIP original; árvore Git `3b702720e8dde39616d37f97c83bc4d2ddd06768`.
- SHA-256 do ZIP: `5039ab35224fe2e209f814166847dbf4cf0b041ffecac98dbd71dcb53a180c3f`.
- JSONs históricos de validação preservados integralmente, sem alteração de `etapa`, commits ou hashes.

Conferência de exemplos: São Paulo roubo/furto 657/5.193 e Curitiba 208/3.222 em 2025; Recife 2.371/4.018 dias completos de chuva (59,0%); Goiânia mantém quatro ausências residenciais. Fontes, unidades, períodos, estações, métodos, cobertura e limitações são confrontados com a edição, sem reestimar valores.

## Registros históricos

| Registro preservado | O que comprova |
|---|---|
| [Relatório inicial](historico/VALIDACAO_INICIAL.md) e [JSON de evidências](../validacao/evidencias-ponto-6.json) | Execução original de 43 testes e cinco conferências complementares, com data/commit próprios. |
| [Preparação Render](../validacao/preparacao-render-2026-10-29.json) | Execução original de 53 testes (43 anteriores + 10 do perfil opcional), sem deploy. |
| [Auditoria congelada](../../dados/edicoes/territorio-2026-10-28-r1/validacao.json) | 1.925 verificações originais das fontes, não reexecutadas nesta reorganização. |

Campos `etapa` existem nesses registros de desenvolvimento; **não fazem parte da resposta pública da API**. Correções posteriores de docstrings/código não invalidam a origem histórica, mas mudam os hashes da versão atual. Novas execuções devem registrar referência e resultado próprios. O [checklist antigo](historico/ACEITE_EQUIPE.md) é histórico; aprovações não foram fabricadas e não são requisito da entrega atual.

## Limitações identificadas para correção separada

Simulações anteriores sobre cópias temporárias do SQLite identificaram catálogo incompleto/vazio aceito como sucesso, números não finitos serializados como `null` disponível e estruturas JSON inválidas retornando erro genérico. Os 53 testes desta revisão não cobrem essas regressões. A edição canônica permanece íntegra; a correção e novos testes pertencem a um PR de código separado. Não apresentar esta revisão documental como correção dessas falhas.

## O que esta validação não comprova

- Publicação/HTTPS de borda reais, isolamento de provedor, carga, capacidade ou SLA. Metadados simulados não provam a infraestrutura real.
- Integração, continuidade em falha, apresentação das limitações ou melhora de score nos consumidores.
- Atualização automática, monitor de fontes ou nova disponibilidade de dados posteriores ao levantamento.
- Localização do imóvel, identificação de comunidade/área de risco ou elegibilidade a partir de CEP/coordenadas mascarados.

Nenhum serviço pago é necessário. O aviso de depreciação do TestClient/HTTPX é conhecido; os resultados registram separadamente falhas e testes ignorados. O erro interno simulado gera log genérico esperado, sem dados de clientes. Se HTTPS for ignorado em outro ambiente por falta de OpenSSL, registrar a diferença. Reuso em ambiente real exige as verificações de [implantação](IMPLANTACAO.md).
