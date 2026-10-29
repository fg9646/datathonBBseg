# Implantação futura em infraestrutura própria

**Não há serviço hospedado ou integração nesta entrega.** Este guia permite retomar o extra sem depender de um provedor. Código/configuração disponíveis não comprovam prontidão para produção. Manter a opção gratuita; não provisionar recursos pagos automaticamente.

## Componentes e inicialização

1. Disponibilizar o repositório, incluindo `api_territorio/` e `dados/edicoes/territorio-2026-10-28-r1/`, com integridade conferida. Não é necessário expor ou executar `entregas/`.
2. Preparar Python 3.12.14 e instalar `api_territorio/requirements.txt`, com suas versões fixadas. Python/SQLite, FastAPI (MIT) e Uvicorn (BSD) não exigem licença paga. Não adicionar banco externo/autenticação comercial para esta versão.
3. Configurar consumidores e caminho de SQLite conforme [execução local](EXECUCAO_LOCAL.md). Guardar apenas hashes SHA-256 no servidor; compartilhar a chave original por canal seguro com o responsável pelo backend consumidor. Sem chave padrão ou segredos no Git/frontend/URL. `.env.example` não é carregado automaticamente.
4. Executar `python -m api_territorio.preparar_base` antes de abrir a porta e verificar uma consulta completa. Se usar destino alternativo, configurar `TERRITORIO_BASE` para o mesmo arquivo. O servidor genérico não prepara o banco sozinho.
5. Iniciar `python -m api_territorio.servidor` com TLS nativo ou proxy explícito, em uma única instância/worker. Configurar host/porta segundo a infraestrutura e manter a origem protegida.

O SQLite é derivado e pode ser recriado da edição versionada, sem nova coleta. Pode ficar em armazenamento efêmero se o procedimento de start sempre o reconstruir/verificar após perda; caso contrário, garantir que exista antes de atender. Fora do Git, com acesso limitado ao processo autorizado, nunca dentro de `dados/`, referências ou `entregas/`. As consultas abrem o arquivo em modo somente leitura; preparação requer escrita. Não disponibilizar banco, snapshot ou repositório como arquivos estáticos.

Reimportar edição existente com origem divergente é rejeitado. Novas coletas/correções geram novas edições com validação própria. Não existe ativação automática de nova edição ou coletor periódico implementado.

## Transporte e fronteira de confiança

Escolher um dos modos do inicializador genérico:

- **TLS nativo:** `--certificado caminho --chave-privada caminho`. Proteger arquivos fora do Git; configurar renovação e confiança do certificado no cliente.
- **Proxy que termina HTTPS:** `--proxy-confiavel IP`, repetido para cada IP de proxy autorizado. Sem `*`. A infraestrutura deve restringir a origem a esses proxies e garantir HTTPS externo; clientes não podem acessar diretamente a porta interna. Cabeçalhos encaminhados de outros clientes não são prova de HTTPS.

`--permitir-http-local`/`TERRITORIO_HTTP_LOCAL=1` são exclusivos da demonstração em loopback e não substituem TLS externo. O serviço falha sem modo de transporte e credenciais válidos. Logs de acesso estão desativados; não registrar chaves ou corpos de requisição.

Um adaptador dependente de plataforma só pode ser usado se sua premissa de isolamento for satisfeita e verificada. O perfil [Render Free](exemplos/RENDER.md) é **exemplo opcional** já preparado no repositório; não é requisito de execução nem caminho genérico para outros provedores. Seus metadados/Host não provam origem criptograficamente.

## Capacidade, saúde e operação

- Uma instância/worker: 60 chamadas/minuto por consumidor, configurável, controle em memória que reinicia com o processo. Múltiplas instâncias teriam cotas independentes; controle distribuído fica fora desta versão.
- Corpo JSON até 16 KiB, até 100 pares indicador/período; recebimento até 3 segundos e consulta à base até 2 segundos. Uvicorn: concorrência 100, keep-alive 5 segundos. Proxy/provedor pode aplicar limites adicionais e produzir erros fora do envelope da API.
- `/health` verifica processo, publicamente, sem consulta territorial. `/ready` exige chave, consulta a base e consome a cota; usar consumidor de monitoramento próprio se necessário.
- Não prometer latência, SLA ou disponibilidade contínua com base nos testes locais. Hibernação de hospedagem gratuita pode exceder o orçamento previsto de até seis segundos do consumidor.
- Dependências e edições precisam de responsáveis por revisão/manutenção. Suporte, rotação/revogação de chaves, capacidade e frequência por fonte serão alinhados na retomada, sem atribuir obrigações atuais a pessoas específicas.

## Verificações na retomada

- [ ] Conferir gratuidade, cotas e possíveis cobranças da infraestrutura escolhida; sem contratação automática.
- [ ] Definir responsáveis pela API, enriquecimento e backend consumidor; validar uso permitido e correspondência do município real com dados mascarados.
- [ ] Identificar commit, contrato, edição, ambiente, URL HTTPS e data reais. Não inventar URL de serviço ainda não criado.
- [ ] Reproduzir testes e integridade local; confirmar configuração, segredo fora do Git, origem isolada e certificado válido.
- [ ] Verificar HTTPS externo, rejeição de proxy/cabeçalhos não confiáveis, `/health`, `/ready`, 401/403 e limite 429; nunca enviar a chave em uma sonda HTTP público.
- [ ] Conferir dados completos, lacunas e município sem cobertura; testar reinício e recriação do SQLite. Registrar somente evidências sem segredos.
- [ ] Validar no consumidor tempo limite, repetição, continuidade sem enriquecimento e apresentação das limitações. Ausência ou falha não vira risco zero.

Essas verificações são para eventual uso real. Nenhuma publicação, integração, avaliação de carga ou homologação externa ocorreu nesta entrega; o histórico de aceite não é uma exigência atual.

Referências técnicas: [FastAPI — API key](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyHeader), [FastAPI — HTTPS](https://fastapi.tiangolo.com/deployment/https/), [Uvicorn — configuração](https://uvicorn.dev/settings/).
