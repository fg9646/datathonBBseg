"""Preparação Render Free sem chamar o provedor ou publicar um serviço."""
import asyncio
from collections import Counter
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import httpx

from api_territorio.armazenamento import EDICAO_PADRAO, RAIZ, preparar_base
from api_territorio.http import criar_app, ROTA
from api_territorio.servidor_render import ambiente_render, BordaRender, main

HOST = 'territorio-teste.onrender.com'


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'render.sqlite3'
        self.key = secrets.token_urlsafe(32)
        self.env = {
            'RENDER': 'true', 'RENDER_SERVICE_TYPE': 'web',
            'RENDER_EXTERNAL_HOSTNAME': HOST, 'RENDER_EXTERNAL_URL': 'https://' + HOST,
            'PORT': '10000', 'TERRITORIO_HTTP_LOCAL': '0',
            'TERRITORIO_BASE': str(self.db),
            'TERRITORIO_CONSUMIDORES': json.dumps({'teste': {'sha256': hashlib.sha256(self.key.encode()).hexdigest()}}),
            # O Render define este curinga; o inicializador deve ignorá-lo.
            'FORWARDED_ALLOW_IPS': '*',
        }

    def app(self):
        with patch.dict(os.environ, self.env, clear=True):
            config, hostname, _ = ambiente_render()
        preparar_base(destino=self.db)
        return BordaRender(criar_app(config=config), hostname)

    def test_recusa_ambiente_fora_do_perfil_antes_de_gravar_ou_servir(self):
        cases = [
            {'RENDER': ''}, {'RENDER_SERVICE_TYPE': 'pserv'},
            {'RENDER_EXTERNAL_HOSTNAME': 'malicioso.example'},
            {'RENDER_EXTERNAL_URL': 'http://' + HOST},
            {'RENDER_EXTERNAL_URL': 'https://outro.onrender.com'},
            {'TERRITORIO_HTTP_LOCAL': '1'}, {'PORT': '0'}, {'PORT': '65536'},
            {'PORT': '18012'}, {'PORT': '19099'}, {'PORT': 'abc'},
            {'TERRITORIO_CONSUMIDORES': '{}'},
        ]
        for changes in cases:
            with self.subTest(campos=list(changes)), patch.dict(os.environ, {**self.env, **changes}, clear=True), \
                    patch('api_territorio.servidor_render.preparar_base') as prepare, \
                    patch('api_territorio.servidor_render.uvicorn.run') as serve, self.assertRaises(ValueError):
                main()
            prepare.assert_not_called()
            serve.assert_not_called()
        self.assertFalse(self.db.exists())

    def test_nao_grava_base_em_dados_entregas_ou_referencias(self):
        for folder in ['dados', 'entregas', 'api_territorio/referencias']:
            with self.subTest(folder=folder), patch.dict(os.environ, {**self.env, 'TERRITORIO_BASE': str(RAIZ / folder / 'nao-criar.sqlite3')}, clear=True), \
                    patch('api_territorio.servidor_render.preparar_base') as prepare, \
                    patch('api_territorio.servidor_render.uvicorn.run') as serve, self.assertRaises(ValueError):
                main()
            prepare.assert_not_called()
            serve.assert_not_called()

    def test_inicia_so_apos_base_pronta_e_ignora_curinga_do_provedor(self):
        with patch.dict(os.environ, self.env, clear=True), patch('api_territorio.servidor_render.uvicorn.run') as serve:
            main()
        self.assertTrue(self.db.is_file())
        kwargs = serve.call_args.kwargs
        self.assertEqual((kwargs['host'], kwargs['port'], kwargs['workers']), ('0.0.0.0', 10000, 1))
        self.assertFalse(kwargs['proxy_headers'])
        self.assertEqual(kwargs['forwarded_allow_ips'], '')
        self.assertFalse(kwargs['access_log'])
        with TestClient(serve.call_args.args[0], base_url='http://' + HOST) as client:
            result = client.post(ROTA, json={'codigo_ibge': '3550308'}, headers={'X-API-Key': self.key})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.json()['indicadores']), 18)

    def test_reconstroi_base_apos_perda_do_arquivo_efemero(self):
        with patch.dict(os.environ, self.env, clear=True), patch('api_territorio.servidor_render.uvicorn.run') as serve:
            main()
            self.db.unlink()  # Arquivo único no TemporaryDirectory deste teste.
            main()
        self.assertEqual(serve.call_count, 2)
        with TestClient(serve.call_args.args[0], base_url='http://' + HOST) as client:
            result = client.post(ROTA, json={'codigo_ibge': '4106902'}, headers={'X-API-Key': self.key})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.json()['indicadores']), 18)

    def test_falha_na_preparacao_nao_abre_porta(self):
        with patch.dict(os.environ, self.env, clear=True), \
                patch('api_territorio.servidor_render.preparar_base', side_effect=ValueError('Origem inválida')), \
                patch('api_territorio.servidor_render.uvicorn.run') as serve, self.assertRaises(ValueError):
            main()
        serve.assert_not_called()

    def test_host_incorreto_ausente_ou_duplicado_e_rejeitado(self):
        app = self.app()
        with TestClient(app, base_url='http://' + HOST) as client:
            cases = [[('Host', 'outro.example')], [('Host', HOST), ('Host', HOST)]]
            for headers in cases:
                result = client.get('/health', headers=headers)
                self.assertEqual(result.status_code, 400)
                self.assertEqual(result.json()['erro']['codigo'], 'HOST_NAO_PERMITIDO')
        messages = []
        async def receive():
            return {'type': 'http.request', 'body': b''}
        async def send(message):
            messages.append(message)
        asyncio.run(app({'type': 'http', 'headers': [], 'scheme': 'http'}, receive, send))
        self.assertEqual(messages[0]['status'], 400)

    def test_cabecalhos_encaminhados_nao_definem_host_protocolo_ou_cliente(self):
        received = []
        async def downstream(scope, receive, send):
            received.append(scope)
        async def no_op(*args):
            pass
        headers = [(b'host', HOST.encode()), (b'x-forwarded-proto', b'http'),
                   (b'x-forwarded-host', b'outro.example'), (b'x-forwarded-for', b'127.0.0.1'),
                   (b'forwarded', b'proto=https;for=127.0.0.1'), (b'x-real-ip', b'127.0.0.1')]
        scope = {'type': 'http', 'scheme': 'http', 'headers': headers, 'client': ('192.0.2.10', 40000)}
        asyncio.run(BordaRender(downstream, HOST)(scope, no_op, no_op))
        self.assertEqual(received[0]['scheme'], 'https')
        self.assertEqual(received[0]['client'], scope['client'])
        self.assertEqual(received[0]['headers'], [(b'host', HOST.encode())])
        self.assertEqual(scope['scheme'], 'http')
        self.assertEqual(scope['headers'], headers)

    def test_consulta_no_perfil_render_preserva_180_registros_e_exige_chave(self):
        originals = json.loads((EDICAO_PADRAO / 'indicadores.json').read_text(encoding='utf-8'))
        states = Counter()
        with TestClient(self.app(), base_url='http://' + HOST) as client:
            denied = client.post(ROTA, json={'codigo_ibge': '3550308'})
            self.assertEqual(denied.status_code, 401)
            self.assertEqual(client.get('/health').status_code, 200)
            self.assertEqual(client.get('/ready').status_code, 401)
            for code in sorted({r['codigo_ibge'] for r in originals}):
                response = client.post(ROTA, json={'codigo_ibge': code}, headers={'X-API-Key': self.key})
                self.assertEqual(response.status_code, 200)
                self.assertIn('strict-transport-security', response.headers)
                actual = {r['id']: r for r in response.json()['indicadores']}
                for original in [r for r in originals if r['codigo_ibge'] == code]:
                    for field in ['valor', 'unidade', 'periodo', 'disponibilidade', 'motivo_ausencia', 'estacao', 'cobertura', 'metodo', 'limitacoes']:
                        self.assertEqual(actual[original['id']][field], original[field])
                    states[actual[original['id']]['disponibilidade']] += 1
        self.assertEqual(states, {'DISPONIVEL': 153, 'AUSENTE': 27})

    def test_blueprint_so_instancia_gratuita_e_segredo_fornecido_fora_do_git(self):
        blueprint = json.loads((RAIZ / 'api_territorio/render.yaml').read_text(encoding='utf-8'))
        self.assertEqual(set(blueprint), {'services', 'previews'})
        self.assertEqual(len(blueprint['services']), 1)
        service = blueprint['services'][0]
        self.assertEqual((service['type'], service['runtime'], service['plan']), ('web', 'python', 'free'))
        self.assertEqual(service['numInstances'], 1)
        self.assertEqual(service['branch'], 'main')
        self.assertEqual(service['autoDeployTrigger'], 'off')
        self.assertEqual(blueprint['previews'], {'generation': 'off'})
        self.assertNotIn('disk', service)
        self.assertNotIn('scaling', service)
        variables = {v['key']: v for v in service['envVars']}
        self.assertEqual(variables['TERRITORIO_CONSUMIDORES'], {'key': 'TERRITORIO_CONSUMIDORES', 'sync': False})
        self.assertEqual(variables['TERRITORIO_HTTP_LOCAL']['value'], '0')

    def test_processo_real_simula_origem_render_sem_publicar(self):
        with closing(socket.socket()) as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        env = {**os.environ, **self.env, 'PORT': str(port)}
        script = """import uvicorn
from unittest.mock import patch
from api_territorio.servidor_render import main
run = uvicorn.run
with patch('api_territorio.servidor_render.uvicorn.run', side_effect=lambda app, **kwargs: run(app, **{**kwargs, 'host': '127.0.0.1'})):
    main()
"""
        # O perfil real escuta em 0.0.0.0; a simulação só abre loopback.
        child = subprocess.Popen([sys.executable, '-c', script],
                                 cwd=RAIZ, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            with httpx.Client(base_url=f'http://127.0.0.1:{port}', headers={'Host': HOST}, trust_env=False, timeout=3) as client:
                deadline = time.monotonic() + 10
                while True:
                    try:
                        self.assertEqual(client.get('/health').status_code, 200)
                        break
                    except httpx.TransportError:
                        if child.poll() is not None or time.monotonic() > deadline:
                            self.fail('Simulação local do perfil Render não iniciou.')
                        time.sleep(0.05)
                self.assertEqual(client.post(ROTA, json={'codigo_ibge': '3550308'}).status_code, 401)
                result = client.post(ROTA, json={'codigo_ibge': '3550308'}, headers={'X-API-Key': self.key})
                self.assertEqual(result.status_code, 200)
                self.assertEqual(len(result.json()['indicadores']), 18)
        finally:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
            logs = child.stderr.read().decode('utf-8', errors='replace')
            child.stderr.close()
            self.assertNotIn(self.key, logs)


if __name__ == '__main__':
    unittest.main()
