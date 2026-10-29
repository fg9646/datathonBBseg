"""Teste de TLS real com certificado temporário confiado apenas pelo cliente do teste."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import unittest

import httpx
from api_territorio.armazenamento import preparar_base, RAIZ
from api_territorio.http import ROTA

OPENSSL = shutil.which('openssl') or ('C:/Program Files/Git/usr/bin/openssl.exe' if Path('C:/Program Files/Git/usr/bin/openssl.exe').is_file() else None)


@unittest.skipUnless(OPENSSL, 'OpenSSL local necessário apenas para o teste de TLS real.')
class TLSRealTests(unittest.TestCase):
    def test_servidor_cli_https_com_certificado_validado(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            db = root / 'base.sqlite3'
            preparar_base(destino=db)
            cert, key = root / 'servidor.crt', root / 'servidor.key'
            conf = root / 'openssl.cnf'
            conf.write_text('[req]\ndistinguished_name=dn\nx509_extensions=v3\nprompt=no\n[dn]\nCN=localhost\n[v3]\nsubjectAltName=DNS:localhost,IP:127.0.0.1\nbasicConstraints=critical,CA:TRUE\nkeyUsage=critical,digitalSignature,keyEncipherment,keyCertSign\nextendedKeyUsage=serverAuth\n', encoding='ascii')
            subprocess.run([OPENSSL, 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-config', str(conf), '-keyout', str(key), '-out', str(cert)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            with closing(socket.socket()) as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            token = secrets.token_urlsafe(32)
            env = {**os.environ, 'TERRITORIO_BASE': str(db), 'TERRITORIO_HTTP_LOCAL': '0', 'TERRITORIO_CONSUMIDORES': json.dumps({'teste-tls': {'sha256': hashlib.sha256(token.encode()).hexdigest()}})}
            child = subprocess.Popen([sys.executable, '-m', 'api_territorio.servidor', '--porta', str(port), '--certificado', str(cert), '--chave-privada', str(key)], cwd=RAIZ, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            try:
                context = ssl.create_default_context(cafile=str(cert))
                with httpx.Client(base_url=f'https://127.0.0.1:{port}', verify=context, trust_env=False, timeout=3) as client:
                    deadline = time.monotonic() + 10
                    while True:
                        try:
                            response = client.get('/health')
                            self.assertEqual(response.status_code, 200)
                            break
                        except httpx.TransportError:
                            if child.poll() is not None:
                                self.fail('Servidor HTTPS encerrou antes do teste.')
                            if time.monotonic() > deadline:
                                self.fail('Servidor HTTPS não iniciou no prazo.')
                            time.sleep(0.05)
                    response = client.post(ROTA, json={'codigo_ibge': '3550308'}, headers={'X-API-Key': token})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(len(response.json()['indicadores']), 18)
                    self.assertIn('strict-transport-security', response.headers)
                    missing = client.post(ROTA, json={'codigo_ibge': '3550308'})
                    self.assertEqual(missing.status_code, 401)
                    self.assertNotIn(token, response.text)
            finally:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
                child.stderr.close()


if __name__ == '__main__':
    unittest.main()
