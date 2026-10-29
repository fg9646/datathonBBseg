> **Registro histórico.** Preserva decisões, resultados e linguagem da época; não define o estado atual nem exige novas aprovações. Os guias atuais começam no [README da API](../../README.md). Os links foram ajustados para esta localização.

# Território — relatório de validação do ponto 6

**Resultado: validação técnica local aprovada.** O checklist de aceite está preparado; a aprovação humana da equipe ainda não foi registrada. Publicação e integração continuam nos pontos 7 a 9.

## Referência validada

- Execução: **28/10/2026, 22:02:03, horário de São Paulo** (`2026-10-29T01:02:03.122027+00:00` em UTC).
- Código: commit `f1adf83c7b56464dd7b53203a88212fe7a786735`, merge do [PR #5](https://github.com/fg9646/datathonBBseg/pull/5) na `main`, incorporado à `feat/api-territorio` antes desta documentação.
- Contrato: `1.0.0`; edição: `territorio-2026-10-28-r1`.
- Ambiente: Windows, Python **3.12.14**, dependências instaladas iguais às versões de `constraints.txt`; `pip check` aprovado.
- Evidência detalhada: [registro JSON](../../validacao/evidencias-ponto-6.json), com os nomes e resultados dos testes, versões, contagens e hashes. Não contém chaves ou registros de clientes.

Este PR altera apenas documentação e evidências da API. O código executável e os testes são os do commit validado.

## Resultados

**43 testes aprovados, zero falhas, zero erros e zero testes ignorados:** 16 da base, 22 de HTTP/autenticação, quatro de inicialização e um de HTTPS real. Cinco conferências complementares da sessão também passaram; elas são registradas separadamente e não aumentam a contagem da suíte versionada.

| Critério | Resultado e evidência |
|---|---|
| Fidelidade dos dados | 180 registros, 153 valores e 27 ausências preservados. Suíte da base e comparação HTTP dos dez municípios aprovadas. A conferência complementar comparou também método, limitações, estações, cobertura, URLs e datas das fontes. |
| Períodos e datas | Períodos originais mantidos; intervalo válido sem valor usa `PERIODO_NAO_DISPONIVEL`, sem trocar o ano. Data de coleta continua `2026-10-27`, sem inventar horário. |
| Lacunas | Cinco ausências `FONTE_SEM_VALOR` e 22 `SEM_RECORTE_RESIDENCIAL`. Recife e Goiânia mantêm suas limitações; ausência não vira zero. |
| Cobertura territorial | Campinas (`3509502`), válida e fora da cobertura, retorna 200 e 18 ausências `SEM_COBERTURA_TERRITORIAL`. Código inexistente retorna 404; Brasília representa o Distrito Federal. |
| Entrada e contrato | Campos, tipos, datas, consultas duplicadas, JSON inválido e limites verificados. OpenAPI versionado igual ao esquema gerado após a retirada documentada do 422 automático. |
| Autenticação | Chave ausente, errada ou duplicada: 401; consumidor sem permissão: 403. Configuração inválida/ausente impede inicialização. Chaves temporárias ou sintéticas nos testes. |
| Transporte | HTTP externo e cabeçalho de proxy não confiável rejeitados. Conexões reais HTTP local e HTTPS passaram; TLS com certificado temporário validado pelo cliente, sem `verify=False`. Configuração do inicializador para proxy conferida, sem publicar proxy real. |
| Limites | 429 por consumidor com `Retry-After`; janela de limite e independência dos consumidores verificadas. Corpos acima de 16 KiB rejeitados. Conferência complementar: 100 pares aceitos e 101 rejeitados com 400. |
| Falhas técnicas | Base ausente e tempo de consulta excedido: 503; falha inesperada: 500 sem detalhe interno na resposta. JSON operacional corrompido testado na camada da base. Não são convertidos em ausência de dado na fonte. |
| Prazo do corpo | Conferência ASGI direta retornou 408 sem chamar a aplicação seguinte, com prazo reduzido para 1 ms durante a simulação. Não mede a latência de uma rede real. |
| Saúde e exemplos | `/health` e `/ready` verificados. Quatro exemplos versionados coincidiram com novas respostas locais, desconsiderando apenas o instante dinâmico `consultado_em`. |
| Importação e isolamento | Reimportação idempotente, rejeição de edição adulterada e preservação da edição ativa aprovadas. Consulta local indexada, sem acesso às fontes externas ou à planilha. |

Os cenários da suíte estão em [base](../../../tests/test_base_territorio.py), [HTTP](../../../tests/test_http_territorio.py), [inicialização](../../../tests/test_servidor_territorio.py) e [HTTPS](../../../tests/test_https_territorio.py). As cinco conferências complementares foram executadas na sessão local e estão descritas no JSON; não constituem novos testes versionados.

### Cobertura por município

| Código IBGE | Município | Disponíveis | Ausentes |
|---|---|---:|---:|
| 2304400 | Fortaleza | 13 | 5 |
| 2611606 | Recife | 14 | 4 |
| 2927408 | Salvador | 16 | 2 |
| 3106200 | Belo Horizonte | 14 | 4 |
| 3304557 | Rio de Janeiro | 16 | 2 |
| 3550308 | São Paulo | 18 | 0 |
| 4106902 | Curitiba | 18 | 0 |
| 4314902 | Porto Alegre | 14 | 4 |
| 5208707 | Goiânia | 14 | 4 |
| 5300108 | Brasília / DF | 16 | 2 |
| **Total** | **10 municípios, 18 indicadores cada** | **153** | **27** |

Exemplos de conferência: roubo/furto residencial de 2025 em São Paulo **657/5.193**; Curitiba **208/3.222**. Recife mantém **2.371/4.018 dias completos de chuva (59,0%)**. Os quatro indicadores de segurança de Goiânia continuam ausentes, sem receber números estaduais.

## Preservação

| Conjunto | Conferência |
|---|---|
| Edição congelada | Integridade dos **21 arquivos** e 180 indicadores aprovada pelo auditor em modo `--verificar-integridade`. Árvore Git igual à `main` validada: `df17da987013eff027e352788a98cb68b1646f57`. |
| `entregas/` | **32 itens** do manifesto conferidos por tamanho e SHA-256, mais o ZIP original. Árvore Git igual à `main` validada: `3b702720e8dde39616d37f97c83bc4d2ddd06768`. |
| ZIP residencial | SHA-256 `5039ab35224fe2e209f814166847dbf4cf0b041ffecac98dbd71dcb53a180c3f`. Apenas leitura para conferência; scripts do pacote não foram executados. |

As **1.925 verificações da auditoria original** continuam como evidência histórica do ponto 3. Não foram reexecutadas nesta etapa: aqui se verificaram integridade do snapshot, reprodução pela API e comportamentos do serviço. Nenhuma nova coleta foi feita.

## Gratuidade e limites do aceite

Não foram adicionadas dependências, serviços pagos, infraestrutura, credenciais de produção ou cobrança por consulta. A solução permanece com Python/SQLite, FastAPI e Uvicorn; hospedagem pública gratuita ainda será escolhida no ponto 7, com seus limites documentados.

- Limite em memória: uma única instância/worker; reiniciar o processo reinicia a janela. Não há controle distribuído.
- Sem teste de carga, garantia de latência de hospedagem, proxy real ou URL externa nesta validação. Os três segundos por tentativa são uma política do cliente, não um SLA comprovado.
- Não existe atualização automática da coleta; `SEM_FALHA_REGISTRADA` não significa que as fontes foram atualizadas hoje.
- Dados municipais não validam endereço, comunidade, área de risco ou elegibilidade do imóvel. CEPs e coordenadas mascarados não ganham precisão por usar a API. Taxas criminais não são probabilidades individuais de sinistro.
- Não foi testado o comportamento interno do motor/Bússola nem a continuidade dos consumidores em falha. Isso será validado com Pipo no ponto 9.
- A suíte emitiu um aviso de depreciação do TestClient com HTTPX; não houve falha nem alteração de dependências. Uma falha interna simulada também gera a mensagem genérica esperada no log.
- Os testes foram executados localmente; este resultado não representa uma execução automática no GitHub ou um aceite humano.

## Reprodução e decisão

Na raiz do repositório, com o ambiente de [HTTP.md](../EXECUCAO_LOCAL.md) preparado:

```bash
python -m unittest discover -s tests -v
python -m pip check
python auditoria/validar_congelar_base.py --verificar-integridade dados/edicoes/territorio-2026-10-28-r1
git diff --exit-code origin/main...HEAD -- dados/edicoes/territorio-2026-10-28-r1 entregas
```

Esses comandos reproduzem a suíte, a checagem de dependências, a integridade e a comparação de mudanças do PR; não reexecutam as cinco conferências complementares nem a auditoria histórica completa. O teste TLS exige OpenSSL local; se aparecer como ignorado em outro ambiente, registrar essa diferença em vez de declarar cobertura HTTPS completa.

**Conclusão técnica:** nenhum impedimento identificado nos critérios locais avaliados. Relatório e checklist entregues na feature para revisão. A equipe deve registrar sua decisão em [ACEITE_EQUIPE.md](ACEITE_EQUIPE.md), referenciando este commit/edição. Não há aceite presumido, publicação ou autorização de merge neste documento.
