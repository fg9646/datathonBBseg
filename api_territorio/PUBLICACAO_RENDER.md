# Território — preparação do Render Free (ponto 7)

**Configuração preparada na `feat/api-territorio`; API ainda não publicada.** Não houve criação de serviço, contratação, emissão de chave de produção ou merge. A autorização do aplicativo Render no repositório privado depende do Garrido.

## Arquivos e escolhas

- [render.yaml](render.yaml): Blueprint de um único Web Service **Free**, Python 3.12.14, uma instância, sem banco externo ou disco persistente. Usa sintaxe JSON, que também é YAML válido, para permitir conferência com a biblioteca padrão. Estrutura validada contra o [schema oficial do Render](https://render.com/schema/render.yaml.json).
- [servidor_render.py](servidor_render.py): inicializador exclusivo da origem isolada pelo Render Free. Prepara/verifica o SQLite antes de abrir a porta; se o arquivo efêmero desaparecer, recria a base a partir da edição congelada no próximo início.
- [test_render_territorio.py](../tests/test_render_territorio.py): testes do perfil, proteção dos destinos, limites da configuração, recriação da base, autenticação, fidelidade dos 180 registros e processo local real.

Publicação automática e previews estão desligados. O Blueprint aponta para `main`, mas esses novos arquivos só estarão nela após revisão e merge autorizado. Nesta etapa eles permanecem na feature; não criar o serviço antes de liberar essa etapa.

## Como conectar e configurar depois da autorização

O Garrido deve instalar/autorizar o aplicativo Render para `fg9646/datathonBBseg`. Como o repositório é privado, a opção de URL pública não atende. Depois, verificar se ele aparece nas credenciais Git da conta Render responsável pela publicação.

Há dois caminhos equivalentes; usar somente um para evitar serviços duplicados:

1. **Blueprint:** no fluxo de criação de Blueprint, escolher o repositório e informar o caminho `api_territorio/render.yaml` em **Blueprint Path**. Conferir o plano Free antes de confirmar. O campo `TERRITORIO_CONSUMIDORES`, com `sync: false`, será solicitado pelo painel.
2. **Web Service manual:** escolher o repositório e preencher os campos abaixo. O arquivo Blueprint serve como referência; criar um Web Service manual não o importa automaticamente.

| Campo | Valor |
|---|---|
| Nome sugerido | `api-territorio` (URL definitiva será a atribuída pelo Render) |
| Runtime / Language | Python 3 |
| Branch | `main`, somente quando esta configuração estiver revisada e integrada |
| Root Directory | Deixar em branco: executar na raiz do repositório, pois a API precisa de `dados/edicoes/` |
| Build Command | `python -m pip install -r api_territorio/requirements.txt` |
| Start Command | `python -m api_territorio.servidor_render` |
| Instance Type / Plan | **Free**, uma instância |
| Auto-Deploy | **Off** |
| Health Check Path | `/health` |
| Banco / disco / previews | Nenhum recurso adicional |

Variáveis para os dois caminhos:

| Variável | Valor / origem |
|---|---|
| `PYTHON_VERSION` | `3.12.14`, versão testada; não depender do Python padrão do provedor |
| `TERRITORIO_CONSUMIDORES` | JSON com nomes e hashes SHA-256, produzido conforme [HTTP.md](HTTP.md); preencher no painel, fora do Git |
| `TERRITORIO_LIMITE_MINUTO` | `60` por consumidor |
| `TERRITORIO_HTTP_LOCAL` | `0` |
| `FORWARDED_ALLOW_IPS` | Vazio; o inicializador desliga a interpretação desses cabeçalhos explicitamente |
| `PORT` | Usar o valor fornecido pelo Render, normalmente `10000` |
| `RENDER`, `RENDER_SERVICE_TYPE`, `RENDER_EXTERNAL_HOSTNAME`, `RENDER_EXTERNAL_URL` | Metadados fornecidos pela plataforma; não preencher manualmente para imitar o Render |
| `TERRITORIO_BASE` | Omitir; o padrão é `api_territorio/var/territorio.sqlite3`, regenerável e fora do Git |

Gerar a chave original apenas no momento autorizado de configurar os consumidores. O servidor recebe seu hash; Pipo recebe a chave por canal seguro. O Blueprint não contém credencial, hash padrão nem segredo gerado automaticamente. Alterar uma variável `sync: false` em um serviço já criado exige edição manual no painel.

## HTTPS e fronteira de confiança

O [Render termina TLS na borda e encaminha HTTP para o processo](https://render.com/docs/web-services#connecting-from-the-public-internet). A plataforma também [redireciona HTTP público para HTTPS](https://render.com/docs/tls). O plano Free [não recebe tráfego pela rede privada](https://render.com/docs/free). Esse isolamento é a premissa do perfil preparado aqui.

O servidor genérico `servidor.py` continua exigindo TLS, proxy com IP explícito ou desenvolvimento em loopback. O novo perfil não habilita seu modo HTTP local nem passa `*` ao Uvicorn, mesmo que o provedor defina `FORWARDED_ALLOW_IPS=*` por padrão.

O inicializador Render:

- Exige metadados coerentes de Web Service Render e URL `https://<hostname>.onrender.com`.
- Aceita somente o `Host` exato desse serviço (também com porta explícita `:443`); rejeita host ausente, desconhecido ou duplicado com 400 `HOST_NAO_PERMITIDO`.
- Desliga proxy headers no Uvicorn e remove `Forwarded`, `X-Forwarded-*` e `X-Real-IP` antes da aplicação. Esses cabeçalhos não determinam protocolo, host ou identidade do cliente.
- Representa como HTTPS o tráfego recebido pela origem isolada, com base na garantia da borda Render, e preserva a autenticação por chave, os limites e os cabeçalhos de segurança da API.

**Limite dessa confiança:** variáveis de ambiente e `Host` não provam criptograficamente a origem. Este perfil só pode ser usado sob a borda isolada do Render Free, sem domínio customizado, proxy paralelo, porta de origem acessível diretamente ou migração automática para outro tipo de serviço. Em outra infraestrutura, usar o servidor genérico com TLS/proxy explícito. Se essas premissas mudarem, revisar o perfil antes de publicar. O comportamento real da borda ainda precisa ser verificado no primeiro deploy.

## Dados, reinícios e saúde

O start valida configuração e credenciais, prepara a edição e faz uma consulta completa antes de escutar. O build instala somente as dependências de execução. O SQLite é derivado e local: sua perda não exige novo download de indicadores nem banco pago. A preparação rejeita destinos dentro de `dados/`, `entregas/` ou das referências da API.

`/health` é público e verifica o processo; não consulta a base a cada sonda. `/ready` exige chave e consulta a base, consumindo o limite do consumidor. A preparação antes de abrir a porta verifica a base no início; a verificação autenticada após o deploy continua necessária.

A edição congelada e `entregas/` não são modificadas nem servidas como arquivos estáticos. Motor e Bússola continuam fora desta frente.

## Gratuidade e limitações

Conferido em **29/10/2026** na [documentação oficial do plano gratuito](https://render.com/docs/free):

- Usar **Free**, sem cartão cadastrado e sem complementos pagos. O YAML não controla cobranças de outros serviços existentes na conta; conferir o painel antes de criar.
- A franquia é de **750 horas por workspace/mês**, compartilhada entre serviços gratuitos. Sem meio de pagamento, exceder tráfego/build pode suspender serviços ou novos builds; não contratar excedentes.
- Após **15 minutos** sem tráfego, o serviço hiberna. Reativação pode levar cerca de **um minuto**, excedendo as tentativas de três segundos combinadas com Pipo. O consumidor deve seguir o comportamento de falha já definido. Aquecimento antes de uma demonstração é uma ação manual, sem prometer disponibilidade contínua.
- O disco local é efêmero; a base é preparada no start. Não usar Postgres gratuito com prazo de expiração nem disco pago.
- Limite em memória reinicia com o processo e exige uma única instância. Capacidade, latência externa e cotas não foram homologadas.

## Checklist antes de publicar e aceite externo

- [ ] Garrido autoriza o aplicativo; conta Render da publicação consegue selecionar o repositório.
- [ ] Revisão/merge desta preparação autorizado; conferir commit e branch escolhidos no painel.
- [ ] Plano Free, ausência de cartão/complementos, uma instância, auto-deploy Off e variáveis conferidos.
- [ ] Hashes dos consumidores configurados no painel; chaves originais entregues fora dos documentos.
- [ ] Autorizar separadamente a criação do serviço. Nenhum deploy foi realizado nesta preparação.
- [ ] Registrar URL HTTPS, commit, região e data reais, sem inventar endereço antes da criação.
- [ ] Sem credencial, verificar redirecionamento de `http://.../health` para HTTPS; depois testar somente URLs HTTPS com credencial.
- [ ] `/health` 200, `/ready` autenticado 200, consulta sem chave 401, host inesperado rejeitado; testar cabeçalhos encaminhados sem afetar acesso/autenticação.
- [ ] Conferir consulta completa, lacunas e município sem cobertura contra a edição congelada; guardar somente respostas sem segredos.
- [ ] Verificar reinício/reativação e preparar a demonstração considerando hibernação. Não declarar SLA de três segundos.
- [ ] Atualizar o quadro para ponto 7 publicado apenas após esses resultados; entrega e integração com Pipo continuam nos pontos 8 e 9.

## Testes locais desta preparação

**Resultado em 29/10/2026: 53 testes aprovados, zero falhas/erros/ignorados** (43 anteriores e dez do perfil Render). `pip check`, integridade dos 21 arquivos congelados, hashes de `entregas/` e validação do Blueprint contra o schema oficial também conferidos. Registro da preparação em [validacao/preparacao-render-2026-10-29.json](validacao/preparacao-render-2026-10-29.json); as evidências históricas do ponto 6 permanecem com sua referência original.

Reprodução: `python -m unittest discover -s tests -v`, no ambiente descrito em [HTTP.md](HTTP.md). O processo real de teste simula os metadados Render e escuta somente em loopback; não acessa a conta Render nem publica serviço. TLS público, autorização do repositório e limites reais do provedor permanecem sem teste externo.

Referências adicionais: [Blueprint](https://render.com/docs/blueprint-spec), [variáveis padrão](https://render.com/docs/environment-variables), [Python](https://render.com/docs/python-version), [health checks](https://render.com/docs/health-checks). Consultar novamente as condições gratuitas antes do deploy.
