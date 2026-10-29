# Execução local — Windows / PowerShell

Executar na raiz do repositório. Esta sequência prepara uma demonstração local, sem conta de nuvem, custo de consulta ou integração. Python **3.12.14** foi testado; as dependências fixadas exigem no mínimo Python 3.11. Use ambiente virtual próprio da API.

## Ambiente e SQLite

```powershell
py -3.12 -m venv .venv
$python = Join-Path $PWD '.venv\Scripts\python.exe'
& $python -m pip install -r api_territorio/requirements-dev.txt
& $python -m pip check
& $python -m api_territorio.preparar_base
```

Não é necessário ativar o ambiente nem mudar a política do PowerShell. Se `.venv` já existir, use-a apenas se for o ambiente da API com versão compatível. Um ambiente de execução sem testes pode instalar `api_territorio/requirements.txt`; `requirements-dev.txt` acrescenta HTTPX. Versões diretas/transitivas estão em [constraints.txt](../constraints.txt). Nenhuma mudança de dependências do motor é necessária.

A preparação cria `api_territorio/var/territorio.sqlite3`, regenerável e ignorado pelo Git. Aceita `--edicao`, `--destino`, `--cadastro`; caminhos alternativos não devem apontar para fontes, referências ou `entregas/`. O importador recusa destino dentro da edição congelada. Se usar `--destino`, definir também `TERRITORIO_BASE` com o mesmo caminho absoluto para o servidor.

Reimportação com a mesma origem é idempotente. Primeira edição fica ativa, importações seguintes não trocam a ativa. Consulte [dados](DADOS.md) para esquema, origem e limites.

## Credencial temporária da demonstração

O gerador cria 32 bytes aleatórios. O servidor recebe somente SHA-256; a chave original é enviada pelo consumidor em `X-API-Key`. Os comandos abaixo mantêm o segredo em memória e não o imprimem:

```powershell
$credencial = & $python -m api_territorio.credenciais --consumidor demonstracao | ConvertFrom-Json
$env:TERRITORIO_CONSUMIDORES = $credencial.configuracao_servidor | ConvertTo-Json -Depth 4 -Compress
$env:TERRITORIO_LIMITE_MINUTO = '60'
$cabecalhos = @{ 'X-API-Key' = $credencial.chave }
```

Não salvar a saída do gerador em documentos, commits, transcrições ou logs. Nenhuma chave real acompanha o repositório. Para múltiplos consumidores, juntar as entradas de configuração com nomes e hashes exclusivos. `permitido: false` nega acesso (403); remover uma entrada revoga a chave após reiniciar. Para rotação, gerar outra chave, substituir o hash e reiniciar. Não existe endpoint de administração.

As variáveis disponíveis são `TERRITORIO_CONSUMIDORES` (obrigatória), `TERRITORIO_BASE` (opcional), `TERRITORIO_LIMITE_MINUTO` (padrão 60) e `TERRITORIO_HTTP_LOCAL` (`0`/`1`, padrão `0`). O arquivo [.env.example](../.env.example) ilustra o formato, **não é carregado automaticamente**. Serviço não inicia sem configuração válida e não tem chave padrão.

## Iniciar e consultar na mesma sessão

O exemplo inicia um processo filho na própria máquina, que herda as variáveis de ambiente. Aguardar o início antes de consultar. HTTP local exige opção explícita e cliente/endereço loopback; não expor esse modo na rede.

```powershell
$servidor = Start-Process -FilePath $python -ArgumentList '-m','api_territorio.servidor','--permitir-http-local' -WorkingDirectory $PWD -WindowStyle Hidden -PassThru
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health'

$pedido = @{ codigo_ibge = '3550308' } | ConvertTo-Json
$resposta = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/v1/enriquecimento/consulta' -ContentType 'application/json' -Headers $cabecalhos -Body $pedido
$resposta | ConvertTo-Json -Depth 12
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/ready' -Headers $cabecalhos
```

Se a primeira consulta ocorrer antes de o processo estar pronto, aguardar e repetir `/health`. Ao terminar a demonstração:

```powershell
Stop-Process -Id $servidor.Id
Remove-Item Env:TERRITORIO_CONSUMIDORES
Remove-Variable credencial,cabecalhos
```

Os [três exemplos completos](CONTRATO.md) permitem repetir a consulta com lacunas e sem cobertura. Não copiar chaves para os arquivos JSON. Saúde de processo não comprova acesso à base; `/ready` consulta dados e consome a cota do consumidor.

Para operação com HTTPS nativo, certificado e chave privada devem existir fora do Git:

```powershell
& $python -m api_territorio.servidor --certificado 'C:\certificados\servidor.pem' --chave-privada 'C:\certificados\servidor.key'
```

O inicializador também aceita `--host`, `--porta` e `--proxy-confiavel IP` (repetível, sem curingas), conforme as premissas de [implantação](IMPLANTACAO.md). Não inicia sem TLS, proxy explícito ou desenvolvimento autorizado em loopback. Cabeçalho de proxy de cliente não confiável não libera HTTP.

## Testes e conferência

```powershell
& $python -m unittest discover -s tests -v
& $python -m pip check
& $python -X utf8 auditoria/validar_congelar_base.py --verificar-integridade dados/edicoes/territorio-2026-10-28-r1
```

Os testes usam bancos e credenciais de teste e conexões locais; não publicam serviço nem executam scripts do pacote residencial. O teste HTTPS precisa de OpenSSL CLI local para gerar certificado temporário (inclusive o fornecido com Git no Windows). Sem ele, esse teste é marcado como ignorado: registrar essa limitação, sem declarar cobertura TLS completa. A API em execução não depende de OpenSSL CLI.

Para gerar novamente exemplos/OpenAPI, executar `& $python -m tests.gerar_exemplos_http` após preparar o SQLite. Esse comando **reescreve** os quatro exemplos e `api_territorio/openapi.json`; é ferramenta de manutenção, não requisito de consulta. Não executá-lo sobre evidências históricas para “atualizar” datas. O schema gerado remove o 422 automático do framework, pois a interface retorna 400.

Resultados reais e limites da conferência ficam no [relatório de validação](VALIDACAO.md). Um resultado técnico não substitui decisão de publicação ou validação dos consumidores.
