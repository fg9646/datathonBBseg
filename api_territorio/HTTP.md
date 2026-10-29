# Território — endpoint e autenticação (ponto 5)

**Implementado na `feat/api-territorio`:** `POST /v1/enriquecimento/consulta`, autenticação por chave exclusiva por consumidor, HTTPS, limite local de chamadas e respostas de erro do contrato 1.0.0. A publicação de uma URL externa e a integração com Pipo continuam pendentes. Nenhuma alteração no motor, na Bússola ou em `entregas/`.

## Gratuidade e dependências

Python, SQLite, FastAPI (MIT) e Uvicorn (BSD) são usados sem licença paga, provedor externo de autenticação ou cobrança por consulta. O serviço consulta o SQLite local. Não foi contratado ou provisionado nenhum serviço de nuvem; hospedagem gratuita e seus limites serão definidos no ponto 7.

As versões diretas e transitivas testadas estão fixadas em `requirements.txt`, `requirements-dev.txt` e `constraints.txt`. HTTPX é usado somente nos testes. As dependências são instaladas em ambiente virtual do projeto, sem alterar os dados ou o runtime do motor.

Referências oficiais: [FastAPI — segurança por API key](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyHeader), [FastAPI — HTTPS](https://fastapi.tiangolo.com/deployment/https/) e [Uvicorn — configuração](https://uvicorn.dev/settings/). Os serviços comerciais opcionais citados nesses sites não são utilizados.

## Preparação local

Na raiz do repositório, criar/ativar um ambiente virtual Python 3.10+ e instalar:

```bash
python -m pip install -r api_territorio/requirements-dev.txt
python -m api_territorio.preparar_base
```

Em um ambiente que apenas executará o serviço, usar `requirements.txt`. `requirements-dev.txt` inclui as ferramentas para testes e exemplos. O SQLite regenerável fica em `api_territorio/var/` e não entra no Git.

## Chaves por consumidor

O backend recebe **somente o hash SHA-256** de cada chave em `TERRITORIO_CONSUMIDORES`. A chave aleatória original deve ficar apenas com o backend consumidor e ser enviada pelo cabeçalho `X-API-Key`. Não colocar em URL, frontend, arquivos compartilhados ou commits.

O gerador local produz uma chave com 32 bytes de aleatoriedade e a configuração do hash. Exemplo de preparação no PowerShell, sem imprimir a chave:

```powershell
$credencial = python -m api_territorio.credenciais --consumidor pipo | ConvertFrom-Json
$env:TERRITORIO_CONSUMIDORES = $credencial.configuracao_servidor | ConvertTo-Json -Depth 4 -Compress
```

Entregar o valor de `chave` ao responsável pelo consumidor por canal seguro. A saída do gerador contém segredo: não salvar em documentos nem logs. Nenhuma credencial real foi emitida ou publicada nesta entrega; os testes usam credenciais temporárias/sintéticas.

A configuração pode conter vários consumidores com hashes diferentes. `permitido: false` nega acesso ao consumidor correspondente (403). Para revogar uma chave, remover sua entrada e reiniciar o serviço. Para substituir a chave, gerar outra e substituir o hash. Não há endpoint administrativo de chaves nesta versão.

O serviço falha antes de abrir o socket quando as credenciais estão ausentes ou inválidas. Não existe senha/chave padrão. `.env.example` mostra as variáveis; não é carregado automaticamente.

## Inicialização e HTTPS

Somente para desenvolvimento na própria máquina:

```bash
python -m api_territorio.servidor --permitir-http-local
```

Esse modo exige endereço loopback (padrão `127.0.0.1:8000`); não permite escutar em `0.0.0.0` e não aceita chamadas HTTP de clientes externos. Ele não substitui a publicação HTTPS prevista no contrato.

Com certificado e chave privada configurados no ambiente de execução:

```bash
python -m api_territorio.servidor --certificado caminho/certificado.pem --chave-privada caminho/chave.pem
```

Também é possível usar um proxy que termine HTTPS: informar seu IP com `--proxy-confiavel IP`. Cabeçalhos encaminhados só são aceitos dos IPs declarados; curingas são rejeitados pelo inicializador. A infraestrutura deve garantir que o proxy indicado termine HTTPS e isole o acesso ao processo interno. Um `X-Forwarded-Proto` enviado por cliente sem proxy confiável não libera HTTP.

O serviço não inicia sem TLS, proxy explícito ou modo local autorizado. Certificados e chaves privadas ficam fora do Git. O teste HTTPS usa certificado temporário confiado somente pelo cliente do teste, valida TLS e nome do servidor e apaga os arquivos ao terminar; não usa `verify=False`.

## Consulta

- Método/caminho: `POST /v1/enriquecimento/consulta`.
- Cabeçalhos: `Content-Type: application/json` e `X-API-Key: <chave-do-consumidor>`.
- Corpo: `codigo_ibge` obrigatório; `versao_base` e `consultas` opcionais. Opcionais devem ser omitidos ou preenchidos; `null` explícito é inválido.
- Sem `consultas`, retorna os 18 indicadores. Não há acesso a arquivos arbitrários ou seleção de caminho do banco pelo cliente.
- Campos desconhecidos, consultas duplicadas, datas inválidas e JSON com chaves duplicadas são rejeitados. Os períodos e os quatro motivos de ausência seguem o contrato.
- Os dados preservam 153 valores e 27 ausências; fontes incluem instituição, URL e a precisão original de data.

Exemplos reais da implementação local estão em `exemplos/`: dados disponíveis (São Paulo), lacunas (Recife), município sem cobertura (Campinas) e credencial ausente. O cabeçalho dos exemplos contém somente placeholder. `openapi.json` descreve a interface; `/docs`, `/redoc` e `/openapi.json` não ficam expostos no servidor.

## Respostas e limites

| HTTP | Situação |
|---|---|
| 200 | Dados disponíveis, parciais ou município válido sem cobertura. |
| 400 | Campos, tipos, datas, JSON ou consultas inválidos. |
| 401 | Chave ausente, incorreta ou cabeçalho de chave duplicado. |
| 403 | Consumidor sem permissão ou HTTPS obrigatório. |
| 404 | Município/edição inexistente ou rota inexistente, com códigos distintos. |
| 405 | Método não permitido. |
| 408 | Tempo excedido para receber o corpo. |
| 413 | Corpo maior que 16 KiB. |
| 415 | Content-Type diferente de JSON ou corpo comprimido não suportado. |
| 429 | Limite por consumidor atingido; informa `Retry-After`. |
| 500 | Falha inesperada, sem detalhes internos na resposta. |
| 503 | Base ausente, inconsistente, bloqueada ou consulta sem conclusão no prazo; não é ausência na fonte. |

Os erros da aplicação seguem `erro.codigo` e `erro.mensagem`. Cabeçalhos impedem cache das respostas; não são registrados corpo ou chave de requisição. Logs de acesso do inicializador estão desativados.

Padrão inicial configurável: **60 chamadas por minuto por consumidor**, janela deslizante em memória. Executar uma única instância/worker: várias instâncias teriam limites independentes. Esse controle não usa Redis ou serviço pago e reinicia com o processo. A capacidade e o limite definitivo da hospedagem ainda pertencem ao ponto 7. O Uvicorn limita conexões simultâneas a 100; uma rejeição de infraestrutura, antes de chegar à aplicação, pode devolver 503 sem o envelope JSON.

Máximo de 100 pares indicador/período por chamada; até 3 segundos para receber o corpo e 2 segundos para consultar a base. O cliente mantém a política acordada de 3 segundos por tentativa e até uma repetição transitória; não existe promessa de latência de rede ou de hospedagem nesta etapa.

`GET /health` é uma verificação simples de processo, sem chave e sem dados territoriais. `GET /ready` exige chave e verifica a base; usa o limite do consumidor, portanto monitoramento frequente deve utilizar consumidor próprio. Não existe atualização automática dos dados implementada nesta etapa.

## Testes e reprodução

```bash
python -m unittest discover -s tests -v
python -m tests.gerar_exemplos_http
```

Nesta entrega, **43 testes passaram**: os 16 da base e 27 de endpoint/autenticação, comparação dos 180 registros por HTTP, limites, validação, erros, inicialização, OpenAPI e conexões reais HTTP/HTTPS. O teste TLS real exige OpenSSL local (inclusive o que acompanha o Git no Windows); sem ele, esse único teste é explicitamente marcado como não executado. Nenhuma dependência de OpenSSL CLI é exigida para executar a API; o teste precisa dela apenas para gerar seu certificado temporário.

Os testes não publicam serviço externo, não emitem credenciais reais e não alteram a edição congelada ou o pacote residencial. A validação integral para o uso da equipe e publicação continuam como pontos 6 e 7.
