"""Perfil exclusivo do Render Free, cuja borda termina TLS e isola a origem.

Não usar este perfil como servidor HTTP público fora da plataforma. Os metadados
validam a configuração, não autenticam a origem de uma requisição. A fronteira de
confiança é a infraestrutura Render documentada em docs/exemplos/RENDER.md.
"""
import os
from pathlib import Path
import re

import uvicorn

from .armazenamento import RAIZ, Repositorio, preparar_base
from .http import criar_app, erro
from .seguranca import Configuracao


def ambiente_render():
    """Falhar antes de preparar a base/abrir a porta se o perfil for incompatível."""
    host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
    if (os.environ.get('RENDER') != 'true'
            or os.environ.get('RENDER_SERVICE_TYPE') != 'web'
            or not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.onrender\.com', host)
            or os.environ.get('RENDER_EXTERNAL_URL') != 'https://' + host):
        raise ValueError('Use este inicializador somente no Web Service Render com hostname HTTPS válido.')
    config = Configuracao.ambiente()
    if config.permitir_http_local:
        raise ValueError('O perfil Render não permite o modo HTTP local.')
    raw_port = os.environ.get('PORT', '10000')
    if not re.fullmatch(r'[0-9]{1,5}', raw_port) or not 1 <= int(raw_port) <= 65535 or int(raw_port) in (18012, 18013, 19099):
        raise ValueError('PORT inválida ou reservada no Render.')
    base = Path(config.base).resolve()
    protected = [RAIZ / 'dados', RAIZ / 'entregas', RAIZ / 'api_territorio/referencias']
    if any(base.is_relative_to(path.resolve()) for path in protected):
        raise ValueError('A base operacional não pode ser gravada nas fontes ou em entregas.')
    return config, host, int(raw_port)


class BordaRender:
    """Apenas para origem isolada por Render Free e seu hostname onrender.com.

    HTTPS externo é garantido pela borda do provedor; o hop interno é HTTP.
    Não interpretar Forwarded/X-Forwarded-* como prova de protocolo ou identidade.
    """
    def __init__(self, app, hostname):
        self.app, self.hostname = app, hostname

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        hosts = [value.decode('latin-1').lower() for key, value in scope['headers'] if key.lower() == b'host']
        if len(hosts) != 1 or hosts[0] not in (self.hostname, self.hostname + ':443'):
            return await erro(400, 'HOST_NAO_PERMITIDO', 'Use o hostname HTTPS do serviço.')(scope, receive, send)
        headers = [(key, value) for key, value in scope['headers']
                   if key.lower() != b'forwarded' and key.lower() != b'x-real-ip'
                   and not key.lower().startswith(b'x-forwarded-')]
        external_scope = {**scope, 'scheme': 'https', 'headers': headers}
        return await self.app(external_scope, receive, send)


def main():
    config, hostname, port = ambiente_render()
    preparar_base(destino=config.base)
    # A origem só escuta depois de a edição ativa permitir uma consulta completa.
    Repositorio(config.base).consultar('3550308')
    app = BordaRender(criar_app(config=config), hostname)
    uvicorn.run(app, host='0.0.0.0', port=port, workers=1,
                proxy_headers=False, forwarded_allow_ips='', access_log=False,
                timeout_keep_alive=5, limit_concurrency=100)


if __name__ == '__main__':
    main()
