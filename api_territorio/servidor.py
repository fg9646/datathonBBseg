"""Inicialização de uma instância Uvicorn; TLS nativo ou proxy explícito."""
import argparse
import ipaddress
import os
from pathlib import Path
import uvicorn

from .seguranca import Configuracao, loopback


def main():
    parser = argparse.ArgumentParser(description='API Território. Sem modo público inseguro por padrão.')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--porta', type=int, default=8000)
    parser.add_argument('--certificado')
    parser.add_argument('--chave-privada')
    parser.add_argument('--proxy-confiavel', action='append', default=[], help='IP explícito do proxy que termina HTTPS; nunca use *.')
    parser.add_argument('--permitir-http-local', action='store_true', help='Somente desenvolvimento em endereço loopback.')
    args = parser.parse_args()
    local = args.permitir_http_local or os.environ.get('TERRITORIO_HTTP_LOCAL') == '1'
    if local and not loopback(args.host):
        parser.error('HTTP local só pode escutar em endereço loopback.')
    if local and args.proxy_confiavel:
        parser.error('Modo HTTP local não deve ser combinado com proxy.')
    if bool(args.certificado) != bool(args.chave_privada):
        parser.error('Informe certificado e chave privada juntos.')
    if not (args.certificado or args.proxy_confiavel or local):
        parser.error('Configure TLS, proxy HTTPS confiável ou modo local explícito.')
    for path in [args.certificado, args.chave_privada]:
        if path and not Path(path).is_file():
            parser.error('Arquivo TLS não encontrado.')
    for host in args.proxy_confiavel:
        try:
            ipaddress.ip_address(host)
        except ValueError:
            parser.error('Proxy confiável deve ser um IP explícito, sem curingas.')
    if not 0 <= args.porta <= 65535:
        parser.error('Porta inválida.')
    os.environ['TERRITORIO_HTTP_LOCAL'] = '1' if local else '0'
    Configuracao.ambiente()  # Falhar antes de abrir o socket quando faltarem credenciais.
    uvicorn.run('api_territorio.http:criar_app', factory=True, host=args.host, port=args.porta,
                ssl_certfile=args.certificado, ssl_keyfile=args.chave_privada,
                proxy_headers=bool(args.proxy_confiavel), forwarded_allow_ips=','.join(args.proxy_confiavel),
                workers=1, access_log=False, timeout_keep_alive=5, limit_concurrency=100)


if __name__ == '__main__':
    main()
