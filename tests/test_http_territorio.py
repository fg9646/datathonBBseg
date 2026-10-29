from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
import uvicorn

from api_territorio.armazenamento import preparar_base, EDICAO_PADRAO
from api_territorio.credenciais import gerar
from api_territorio.http import criar_app, ROTA, MAX_CORPO
from api_territorio.seguranca import Configuracao, Consumidor, LimiteConsumidor

# Somente credenciais sintéticas de teste; não habilitadas por padrão no servidor.
CHAVE = 't' * 43
OUTRA = 'u' * 43


def consumidor(nome='teste', chave=CHAVE, permitido=True):
    return Consumidor(nome, hashlib.sha256(chave.encode()).hexdigest(), permitido)


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.temp.name) / 'teste.sqlite3'
        preparar_base(destino=cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def config(self, **kwargs):
        return Configuracao(kwargs.pop('consumidores', (consumidor(),)), kwargs.pop('base', self.db), **kwargs)

    def cliente(self, **kwargs):
        app = criar_app(config=self.config(**kwargs))
        return TestClient(app, base_url='https://testserver')

    def pedir(self, client, body=None, chave=CHAVE):
        headers = {'X-API-Key': chave} if chave is not None else {}
        return client.post(ROTA, json=body if body is not None else {'codigo_ibge': '3550308'}, headers=headers)

    def assertErro(self, response, status, code):
        self.assertEqual(response.status_code, status, response.text)
        self.assertEqual(response.json()['erro']['codigo'], code)
        self.assertEqual(set(response.json()), {'erro'})
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertNotIn(CHAVE, response.text)

    def test_resposta_completa_autenticada_preserva_contrato(self):
        with self.cliente() as client:
            response = self.pedir(client)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['versao_contrato'], '1.0.0')
        self.assertEqual(result['versao_base'], 'territorio-2026-10-28-r1')
        self.assertEqual(result['atualizacao']['ultima_coleta_em'], '2026-10-27')
        self.assertEqual(len(result['indicadores']), 18)
        values = {r['id']: r['valor'] for r in result['indicadores']}
        self.assertEqual(values['seguranca.roubo_residencial'], 657)
        self.assertEqual(values['seguranca.furto_residencial'], 5193)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertIn('strict-transport-security', response.headers)
        self.assertNotIn(CHAVE, response.text)

    def test_http_preserva_os_180_registros_dos_dez_municipios(self):
        records = json.loads((EDICAO_PADRAO / 'indicadores.json').read_text(encoding='utf-8'))
        with self.cliente() as client:
            for code in sorted({r['codigo_ibge'] for r in records}):
                response = self.pedir(client, {'codigo_ibge': code})
                self.assertEqual(response.status_code, 200, code)
                items = {r['id']: r for r in response.json()['indicadores']}
                self.assertEqual(len(items), 18)
                for original in [r for r in records if r['codigo_ibge'] == code]:
                    for field in ['valor', 'unidade', 'periodo', 'disponibilidade', 'motivo_ausencia', 'cobertura', 'estacao']:
                        self.assertEqual(items[original['id']][field], original[field], (code, original['id'], field))

    def test_lacunas_e_sem_cobertura_sao_200_nao_404(self):
        with self.cliente() as client:
            recife = self.pedir(client, {'codigo_ibge': '2611606'}).json()
            campinas = self.pedir(client, {'codigo_ibge': '3509502'})
        theft = next(r for r in recife['indicadores'] if r['id'] == 'seguranca.furto_residencial')
        self.assertIsNone(theft['valor'])
        self.assertEqual(theft['motivo_ausencia'], 'SEM_RECORTE_RESIDENCIAL')
        self.assertEqual(campinas.status_code, 200)
        self.assertTrue(all(r['motivo_ausencia'] == 'SEM_COBERTURA_TERRITORIAL' for r in campinas.json()['indicadores']))

    def test_periodo_valido_sem_dado_preserva_intervalo(self):
        period = {'inicio': '2024-01-01', 'fim': '2024-12-31'}
        with self.cliente() as client:
            result = self.pedir(client, {'codigo_ibge': '3550308', 'consultas': [{'indicador': 'seguranca.roubo_residencial', 'periodo': period}]})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['indicadores'][0]['periodo'], period)
        self.assertEqual(result.json()['indicadores'][0]['motivo_ausencia'], 'PERIODO_NAO_DISPONIVEL')

    def test_chave_ausente_incorreta_ou_duplicada(self):
        with self.cliente() as client:
            for key in [None, OUTRA, 'curta']:
                with self.subTest(key=key is None):
                    response = self.pedir(client, chave=key)
                    self.assertErro(response, 401, 'CREDENCIAL_INVALIDA')
                    self.assertEqual(response.headers['www-authenticate'], 'ApiKey')
            self.assertErro(client.post(ROTA, json={'codigo_ibge': '3550308'}, headers=[('X-API-Key', CHAVE), ('X-API-Key', CHAVE)]), 401, 'CREDENCIAL_INVALIDA')

    def test_chave_valida_sem_permissao(self):
        with self.cliente(consumidores=(consumidor(permitido=False),)) as client:
            self.assertErro(self.pedir(client), 403, 'ACESSO_NEGADO')

    def test_limitacao_por_consumidor_com_retry_after(self):
        with self.cliente(consumidores=(consumidor(), consumidor('segundo', OUTRA)), limite_por_minuto=1) as client:
            self.assertEqual(self.pedir(client).status_code, 200)
            response = self.pedir(client)
            self.assertErro(response, 429, 'LIMITE_EXCEDIDO')
            self.assertGreaterEqual(int(response.headers['retry-after']), 1)
            self.assertEqual(self.pedir(client, chave=OUTRA).status_code, 200)

    def test_janela_de_limite_expira_sem_sleep(self):
        clock = [100.0]
        limiter = LimiteConsumidor(1, lambda: clock[0])
        self.assertIsNone(limiter.consumir('a'))
        self.assertEqual(limiter.consumir('a'), 60)
        clock[0] = 160.0
        self.assertIsNone(limiter.consumir('a'))

    def test_http_e_header_de_proxy_nao_confiavel_sao_rejeitados(self):
        with TestClient(criar_app(config=self.config()), base_url='http://testserver') as client:
            response = client.post(ROTA, json={'codigo_ibge': '3550308'}, headers={'X-API-Key': CHAVE, 'X-Forwarded-Proto': 'https'})
            self.assertErro(response, 403, 'HTTPS_OBRIGATORIO')

    def test_http_local_exige_opt_in_e_cliente_loopback(self):
        app = criar_app(config=self.config(permitir_http_local=True))
        with TestClient(app, base_url='http://testserver', client=('127.0.0.1', 50000)) as client:
            self.assertEqual(self.pedir(client).status_code, 200)
        with TestClient(app, base_url='http://testserver', client=('192.0.2.8', 50000)) as client:
            self.assertErro(self.pedir(client), 403, 'HTTPS_OBRIGATORIO')

    def test_campos_desconhecidos_tipos_e_null_sao_400(self):
        bodies = [[], {}, {'codigo_ibge': 3550308}, {'codigo_ibge': '3550308', 'cep': '00000000'}, {'codigo_ibge': '3550308', 'consultas': []}, {'codigo_ibge': '3550308', 'consultas': None}, {'codigo_ibge': '3550308', 'versao_base': None}, {'codigo_ibge': '3550308', 'consultas': [{'indicador': 'clima.chuva_normal', 'periodo': None}]}, {'codigo_ibge': '3550308', 'consultas': [{'indicador': 'clima.chuva_normal', 'periodo': {'inicio': '2025-02-30', 'fim': '2025-03-01'}}]}, {'codigo_ibge': '3550308', 'consultas': [{'indicador': 'clima.chuva_normal'}] * 2}, {'codigo_ibge': '3550308', 'consultas': [{'indicador': 'nao-existe'}]}]
        with self.cliente() as client:
            for body in bodies:
                with self.subTest(body=body):
                    self.assertErro(self.pedir(client, body), 400, 'ENTRADA_INVALIDA')

    def test_json_invalido_duplicado_nao_finito_ou_profundo(self):
        inputs = [b'{', b'{"codigo_ibge":"3550308","codigo_ibge":"4106902"}', b'{"codigo_ibge":NaN}', b'\xff', b'[' * 1200 + b']' * 1200]
        with self.cliente() as client:
            for raw in inputs:
                self.assertErro(client.post(ROTA, content=raw, headers={'Content-Type': 'application/json', 'X-API-Key': CHAVE}), 400, 'ENTRADA_INVALIDA')

    def test_corpo_excessivo_e_content_type(self):
        with self.cliente() as client:
            self.assertErro(client.post(ROTA, content=b' ' * (MAX_CORPO + 1), headers={'Content-Type': 'application/json', 'X-API-Key': CHAVE}), 413, 'REQUISICAO_MUITO_GRANDE')
            self.assertErro(client.post(ROTA, content=iter([b' ' * 9000, b' ' * 9000]), headers={'Content-Type': 'application/json', 'X-API-Key': CHAVE}), 413, 'REQUISICAO_MUITO_GRANDE')
            self.assertErro(client.post(ROTA, content='{}', headers={'Content-Type': 'text/plain', 'X-API-Key': CHAVE}), 415, 'TIPO_CONTEUDO_INVALIDO')

    def test_codigo_e_edicao_inexistentes(self):
        with self.cliente() as client:
            self.assertErro(self.pedir(client, {'codigo_ibge': '9999999'}), 404, 'MUNICIPIO_INEXISTENTE')
            self.assertErro(self.pedir(client, {'codigo_ibge': '3550308', 'versao_base': 'nao-existe'}), 404, 'EDICAO_INEXISTENTE')

    def test_base_ausente_e_indisponibilidade_sao_503(self):
        with self.cliente(base=Path(self.temp.name) / 'inexistente.sqlite3') as client:
            self.assertErro(self.pedir(client), 503, 'SERVICO_INDISPONIVEL')
            self.assertErro(client.get('/ready', headers={'X-API-Key': CHAVE}), 503, 'SERVICO_INDISPONIVEL')
            self.assertEqual(client.get('/health').status_code, 200)

    def test_falha_inesperada_nao_expoe_detalhes(self):
        class Falha:
            def consultar(self, **kwargs):
                raise RuntimeError('Detalhe interno que não deve ser exposto')
        with TestClient(criar_app(config=self.config(), repositorio=Falha()), base_url='https://testserver', raise_server_exceptions=False) as client:
            response = self.pedir(client)
            self.assertErro(response, 500, 'ERRO_INTERNO')
            self.assertNotIn('Detalhe interno', response.text)

    def test_timeout_de_consulta_e_503(self):
        class Lenta:
            def consultar(self, **kwargs):
                time.sleep(0.05)
                return {}
        with patch('api_territorio.http.TEMPO_CONSULTA', 0.001), TestClient(criar_app(config=self.config(), repositorio=Lenta()), base_url='https://testserver') as client:
            self.assertErro(self.pedir(client), 503, 'SERVICO_INDISPONIVEL')

    def test_rotas_metodos_e_documentacao_nao_exposta(self):
        with self.cliente() as client:
            self.assertErro(client.get(ROTA), 405, 'METODO_NAO_PERMITIDO')
            for path in ['/docs', '/openapi.json', '/arquivo-inexistente']:
                self.assertErro(client.get(path), 404, 'ROTA_INEXISTENTE')
            self.assertErro(client.get('/ready'), 401, 'CREDENCIAL_INVALIDA')
            self.assertEqual(client.get('/ready', headers={'X-API-Key': CHAVE}).json(), {'status': 'pronto'})

    def test_sem_credenciais_ou_chaves_repetidas_nao_inicia(self):
        for env in [{}, {'TERRITORIO_CONSUMIDORES': '{'}, {'TERRITORIO_CONSUMIDORES': '{"pipo":{"sha256":"invalido"}}'}]:
            with patch.dict(os.environ, env, clear=True), self.assertRaises(ValueError):
                criar_app()
        with self.assertRaises(ValueError):
            self.config(consumidores=(consumidor('a'), consumidor('b')))

    def test_geracao_de_chave_e_configuracao_por_hash(self):
        output = gerar('cliente-teste')
        self.assertGreaterEqual(len(output['chave']), 32)
        config = output['configuracao_servidor']
        self.assertNotIn(output['chave'], json.dumps(config))
        with patch.dict(os.environ, {'TERRITORIO_CONSUMIDORES': json.dumps(config), 'TERRITORIO_BASE': str(self.db)}, clear=True):
            with TestClient(criar_app(), base_url='https://testserver') as client:
                self.assertEqual(self.pedir(client, chave=output['chave']).status_code, 200)

    def test_openapi_documenta_resposta_e_autenticacao_sem_chaves(self):
        schema = criar_app(config=self.config()).openapi()
        operation = schema['paths'][ROTA]['post']
        self.assertTrue(operation['security'])
        self.assertEqual(operation['responses']['200']['content']['application/json']['schema']['$ref'], '#/components/schemas/RespostaConsulta')
        self.assertEqual(schema['components']['securitySchemes']['APIKeyHeader']['name'], 'X-API-Key')
        self.assertNotIn(CHAVE, json.dumps(schema))

    def test_socket_real_com_uvicorn_em_http_local(self):
        app = criar_app(config=self.config(permitir_http_local=True))
        with closing(socket.socket()) as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
            server = uvicorn.Server(uvicorn.Config(app, log_level='critical', access_log=False, proxy_headers=False))
            thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
            thread.start()
            try:
                deadline = time.monotonic() + 8
                while not server.started and thread.is_alive() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(server.started, 'Servidor local não iniciou.')
                with httpx.Client(base_url=f'http://127.0.0.1:{port}', trust_env=False, timeout=3) as client:
                    self.assertEqual(self.pedir(client).status_code, 200)
                    self.assertErro(self.pedir(client, chave=None), 401, 'CREDENCIAL_INVALIDA')
            finally:
                server.should_exit = True
                thread.join(timeout=8)
                self.assertFalse(thread.is_alive(), 'Servidor de teste não encerrou.')


if __name__ == '__main__':
    unittest.main()
