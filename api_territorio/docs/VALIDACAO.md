# Validação local e limites da entrega

**API funcional validada localmente**, sem serviço hospedado, integração real ou aceite de produção. Este relatório separa novas verificações dos registros históricos; não atribui aprovações humanas.

## Referência e resultados atuais

<!-- RESULTADO_ATUAL -->
Execução em `2026-10-29T05:40:54.260748+00:00` (UTC), Windows/Python 3.12.14: **70 testes aprovados, zero falhas, erros ou ignorados**. São os 53 testes existentes mais 17 regressões de integridade e preservação da transação. `pip check`, auditor de integridade dos 21 arquivos, manifesto dos 32 itens de `entregas/`, ZIP e comparação completa dos 180 registros/metadados aprovados.

[Evidência desta versão](../validacao/qualidade-2026-10-29.json): referência Git anterior e hashes dos fontes efetivamente testados. Os quatro exemplos, o OpenAPI e o esquema SQLite permanecem iguais. Endpoints, campos, unidades, períodos, autenticação, limites e dependências foram preservados; nenhuma nova infraestrutura ou integração foi adicionada.

A [revisão documental anterior](../validacao/revisao-documental-2026-10-29.json) registrou 53 testes aprovados e 76 links locais, com execução Python idêntica à `main` após ignorar duas docstrings. Esse resultado pertence à versão documental; esta versão inclui as correções funcionais e suas novas evidências.
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

## Regressões corrigidas nesta versão

Testes em cópias temporárias do SQLite confirmam 503 `SERVICO_INDISPONIVEL` para catálogo incompleto/vazio ou com ID substituído, números não finitos/overflow, JSON inválido e registros com campos, tipos ou estados incoerentes. A leitura valida o catálogo completo e os registros consultados; não é uma varredura integral do banco a cada chamada. `/ready` detecta catálogo danificado; `/health` continua verificando somente o processo.

Ausências legítimas continuam 200 com `null`/motivo; consultas e códigos inexistentes preservam 400/404, enquanto falhas inesperadas de programação continuam 500. Edição ativa quebrada é 503; edição inexistente pedida explicitamente é 404. Testes também confirmam rollback integral de uma importação que falha durante a gravação e consulta/preparação sem dependência de frameworks HTTP. A edição canônica permaneceu íntegra durante todos os testes.

Os modelos foram separados em `modelos.py`, as regras compartilhadas em `validadores.py`, e a preparação foi dividida em leitura, normalização e gravação. A validação da estrutura ocorre na fronteira dos dados; não existe conversão genérica de toda exceção para 503.

## O que esta validação não comprova

- Publicação/HTTPS de borda reais, isolamento de provedor, carga, capacidade ou SLA. Metadados simulados não provam a infraestrutura real.
- Integração, continuidade em falha, apresentação das limitações ou melhora de score nos consumidores.
- Atualização automática, monitor de fontes ou nova disponibilidade de dados posteriores ao levantamento.
- Localização do imóvel, identificação de comunidade/área de risco ou elegibilidade a partir de CEP/coordenadas mascarados.

Nenhum serviço pago é necessário. O aviso de depreciação do TestClient/HTTPX é conhecido; os resultados registram separadamente falhas e testes ignorados. O erro interno simulado gera log genérico esperado, sem dados de clientes. Se HTTPS for ignorado em outro ambiente por falta de OpenSSL, registrar a diferença. Reuso em ambiente real exige as verificações de [implantação](IMPLANTACAO.md).
