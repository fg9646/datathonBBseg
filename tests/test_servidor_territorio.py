from contextlib import redirect_stderr
import hashlib
import io
import json
import os
import unittest
from unittest.mock import patch

from api_territorio.servidor import main


class InicializacaoTests(unittest.TestCase):
    def ambiente(self):
        return {'TERRITORIO_CONSUMIDORES': json.dumps({'teste': {'sha256': hashlib.sha256(b't' * 43).hexdigest()}})}

    def test_recusa_configuracoes_de_transporte_inseguras(self):
        casos = [[], ['--permitir-http-local', '--host', '0.0.0.0'], ['--proxy-confiavel', '*'], ['--certificado', 'ausente.pem'], ['--permitir-http-local', '--proxy-confiavel', '127.0.0.1']]
        for args in casos:
            with self.subTest(args=args), patch.dict(os.environ, self.ambiente(), clear=True), patch('sys.argv', ['servidor', *args]), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
                main()
            self.assertEqual(result.exception.code, 2)

    def test_proxy_confiavel_e_worker_unico_explicitos(self):
        with patch.dict(os.environ, self.ambiente(), clear=True), patch('sys.argv', ['servidor', '--proxy-confiavel', '127.0.0.1']), patch('api_territorio.servidor.uvicorn.run') as run:
            main()
            self.assertTrue(run.call_args.kwargs['proxy_headers'])
            self.assertEqual(run.call_args.kwargs['forwarded_allow_ips'], '127.0.0.1')
            self.assertEqual(run.call_args.kwargs['workers'], 1)
            self.assertFalse(run.call_args.kwargs['access_log'])

    def test_modo_local_nao_confia_em_headers_de_proxy(self):
        with patch.dict(os.environ, self.ambiente(), clear=True), patch('sys.argv', ['servidor', '--permitir-http-local']), patch('api_territorio.servidor.uvicorn.run') as run:
            main()
            self.assertFalse(run.call_args.kwargs['proxy_headers'])
            self.assertEqual(run.call_args.kwargs['host'], '127.0.0.1')

    def test_nao_abre_servidor_sem_consumidores(self):
        with patch.dict(os.environ, {}, clear=True), patch('sys.argv', ['servidor', '--permitir-http-local']), patch('api_territorio.servidor.uvicorn.run') as run, self.assertRaises(ValueError):
            main()
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
