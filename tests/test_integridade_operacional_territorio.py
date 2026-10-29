"""Regressões em cópias temporárias; nenhum arquivo congelado é modificado."""
from contextlib import closing, contextmanager
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api_territorio.armazenamento import preparar_base, Repositorio, RAIZ
from api_territorio.http import criar_app, ROTA
from api_territorio.seguranca import Configuracao, Consumidor


class IntegridadeOperacionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporario = tempfile.TemporaryDirectory()
        cls.original = Path(cls.temporario.name) / 'original.sqlite3'
        preparar_base(destino=cls.original)
        cls.chave = 's' * 43  # Credencial sintética, sem consumidor habilitado por padrão.

    @classmethod
    def tearDownClass(cls):
        cls.temporario.cleanup()

    @contextmanager
    def base_modificada(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'modificada.sqlite3'
            shutil.copyfile(self.original, caminho)
            with closing(sqlite3.connect(caminho)) as banco:
                yield banco, caminho

    def consulta(self, banco, caminho, pedido=None):
        banco.commit()
        consumidor = Consumidor('regressao', hashlib.sha256(self.chave.encode()).hexdigest())
        config = Configuracao((consumidor,), base=caminho)
        with TestClient(criar_app(config=config), base_url='https://testserver', raise_server_exceptions=False) as cliente:
            return cliente.post(
                ROTA, json=pedido or {'codigo_ibge': '3550308'}, headers={'X-API-Key': self.chave},
            )

    def assertIndisponivel(self, resposta):
        self.assertEqual(resposta.status_code, 503, resposta.text)
        self.assertEqual(resposta.json()['erro']['codigo'], 'SERVICO_INDISPONIVEL')
        self.assertEqual(resposta.headers['retry-after'], '1')
        self.assertNotIn('indicadores', resposta.json())
        self.assertNotIn(self.chave, resposta.text)

    def alterar_registro(self, banco, alteracao, indicador='clima.chuva_normal'):
        consulta = "SELECT dados FROM indicadores WHERE municipio='3550308' AND indicador=?"
        registro = json.loads(banco.execute(consulta, (indicador,)).fetchone()[0])
        alteracao(registro)
        banco.execute(
            "UPDATE indicadores SET dados=? WHERE municipio='3550308' AND indicador=?",
            (json.dumps(registro), indicador),
        )

    def test_catalogo_incompleto_falha_em_consulta_completa_e_explicita(self):
        for pedido in [
            {'codigo_ibge': '3550308'},
            {'codigo_ibge': '3550308', 'consultas': [{'indicador': 'clima.chuva_normal'}]},
        ]:
            with self.subTest(pedido=pedido), self.base_modificada() as (banco, caminho):
                banco.execute("DELETE FROM catalogo WHERE indicador='clima.minima_media_normal'")
                self.assertIndisponivel(self.consulta(banco, caminho, pedido))

    def test_catalogo_vazio_falha_inclusive_fora_da_cobertura(self):
        for codigo in ('3550308', '3509502'):
            with self.subTest(codigo=codigo), self.base_modificada() as (banco, caminho):
                banco.execute('DELETE FROM catalogo')
                self.assertIndisponivel(self.consulta(banco, caminho, {'codigo_ibge': codigo}))

    def test_catalogo_com_18_linhas_e_id_substituido_nao_e_aceito(self):
        with self.base_modificada() as (banco, caminho):
            banco.execute("UPDATE catalogo SET indicador='clima.inventado' WHERE indicador='clima.chuva_normal'")
            self.assertEqual(banco.execute('SELECT COUNT(*) FROM catalogo').fetchone()[0], 18)
            self.assertIndisponivel(self.consulta(banco, caminho))

    def test_ready_detecta_catalogo_corrompido_e_health_continua_de_processo(self):
        with self.base_modificada() as (banco, caminho):
            banco.execute('DELETE FROM catalogo')
            banco.commit()
            consumidor = Consumidor('regressao', hashlib.sha256(self.chave.encode()).hexdigest())
            config = Configuracao((consumidor,), base=caminho)
            with TestClient(criar_app(config=config), base_url='https://testserver') as cliente:
                self.assertIndisponivel(cliente.get('/ready', headers={'X-API-Key': self.chave}))
                self.assertEqual(cliente.get('/health').status_code, 200)

    def test_registro_padrao_removido_nao_se_converte_em_lacuna(self):
        with self.base_modificada() as (banco, caminho):
            banco.execute("DELETE FROM indicadores WHERE municipio='3550308' AND indicador='clima.chuva_normal'")
            self.assertIndisponivel(self.consulta(banco, caminho))

    def test_catalogo_com_estrutura_unidade_ou_periodo_invalidos(self):
        itens = [[], None, {}, {'id': 'clima.chuva_normal', 'unidade': 'mm/ano'},
                 {'id': 'outro', 'unidade': 'mm/ano', 'periodo': {'inicio': '1991-01-01', 'fim': '2020-12-31'}},
                 {'id': 'clima.chuva_normal', 'unidade': '°C', 'periodo': {'inicio': '1991-01-01', 'fim': '2020-12-31'}},
                 {'id': 'clima.chuva_normal', 'unidade': 'mm/ano', 'periodo': {'inicio': '2025-02-30', 'fim': '2025-12-31'}}]
        for item in itens:
            with self.subTest(item=item), self.base_modificada() as (banco, caminho):
                banco.execute("UPDATE catalogo SET dados=? WHERE indicador='clima.chuva_normal'", (json.dumps(item),))
                self.assertIndisponivel(self.consulta(banco, caminho))

    def test_numeros_nao_finitos_nao_viram_null_disponivel(self):
        for numero in (float('nan'), float('inf'), -float('inf')):
            with self.subTest(numero=numero), self.base_modificada() as (banco, caminho):
                self.alterar_registro(banco, lambda r: r.update(valor=numero))
                self.assertIndisponivel(self.consulta(banco, caminho))

    def test_overflow_numerico_no_json_operacional_e_503(self):
        for literal in ('1e999', '9' * 5000):
            with self.subTest(literal=literal[:12]), self.base_modificada() as (banco, caminho):
                bruto = banco.execute(
                    "SELECT dados FROM indicadores WHERE municipio='3550308' AND indicador='clima.chuva_normal'",
                ).fetchone()[0]
                valor = json.loads(bruto)['valor']
                alterado = bruto.replace('"valor":' + str(valor), '"valor":' + literal)
                self.assertNotEqual(bruto, alterado)
                banco.execute(
                    "UPDATE indicadores SET dados=? WHERE municipio='3550308' AND indicador='clima.chuva_normal'",
                    (alterado,),
                )
                self.assertIndisponivel(self.consulta(banco, caminho))

    def test_json_sintaxe_tipo_profundidade_e_duplicatas_invalidos(self):
        for bruto in ('{', '[]', 'null', '123', '"texto"', '[' * 1200 + ']' * 1200, '{"id":"a","id":"b"}'):
            with self.subTest(bruto=bruto[:30]), self.base_modificada() as (banco, caminho):
                banco.execute(
                    "UPDATE indicadores SET dados=? WHERE municipio='3550308' AND indicador='clima.chuva_normal'", (bruto,),
                )
                self.assertIndisponivel(self.consulta(banco, caminho))

    def test_payload_divergente_da_chave_ou_com_campos_ausentes(self):
        alteracoes = [
            lambda r: r.update(id='clima.maxima_media_normal'),
            lambda r: r.update(unidade='°C'),
            lambda r: r.update(periodo={'inicio': '2025-01-01', 'fim': '2025-12-31'}),
            lambda r: r.pop('valor'), lambda r: r.pop('fontes'), lambda r: r.update(campo_extra=True),
        ]
        for indice, alterar in enumerate(alteracoes):
            with self.subTest(indice=indice), self.base_modificada() as (banco, caminho):
                self.alterar_registro(banco, alterar)
                self.assertIndisponivel(self.consulta(banco, caminho))

    def test_estados_de_ausencia_incoerentes_sao_falha_tecnica(self):
        alteracoes = [
            {'valor': None}, {'disponibilidade': 'AUSENTE'}, {'motivo_ausencia': 'FONTE_SEM_VALOR'},
            {'valor': None, 'disponibilidade': 'AUSENTE', 'motivo_ausencia': 'INVENTADO'},
            {'valor': None, 'disponibilidade': 'AUSENTE', 'motivo_ausencia': []},
            {'valor': True}, {'valor': '1584'}, {'valor': []},
        ]
        for alteracao in alteracoes:
            with self.subTest(alteracao=alteracao), self.base_modificada() as (banco, caminho):
                self.alterar_registro(banco, lambda r: r.update(alteracao))
                self.assertIndisponivel(self.consulta(banco, caminho))

    def test_metadados_estruturalmente_invalidos_sao_503(self):
        alteracoes = [
            {'fontes': {}}, {'fontes': []}, {'fontes': [{}]},
            {'fontes': [{'instituicao': 'INMET', 'url': 'https://portal.inmet.gov.br', 'coletado_em': '2025-02-30'}]},
            {'fontes': [{'instituicao': 'INMET', 'url': 'sem-url', 'coletado_em': '2026-10-27'}]},
            {'fontes': [{'instituicao': 'INMET', 'url': 'https://portal.inmet.gov.br', 'coletado_em': '2026-10-27T12:00:00'}]},
            {'estacao': []}, {'estacao': {'codigo': 123, 'nome': 'Estação'}},
            {'metodo': None}, {'limitacoes': [1]}, {'cobertura': []},
        ]
        for indice, alteracao in enumerate(alteracoes):
            with self.subTest(indice=indice), self.base_modificada() as (banco, caminho):
                self.alterar_registro(banco, lambda r: r.update(alteracao))
                self.assertIndisponivel(self.consulta(banco, caminho))

    def test_contagens_invalidas_e_cobertura_incoerente(self):
        for valor in (-1, 1.5, True):
            with self.subTest(contagem=valor), self.base_modificada() as (banco, caminho):
                self.alterar_registro(banco, lambda r: r.update(valor=valor), 'seguranca.roubo_residencial')
                self.assertIndisponivel(self.consulta(banco, caminho))
        coberturas = [
            {'numerador': 2, 'denominador': 1, 'proporcao': 0.5, 'unidade': 'dias'},
            {'numerador': 1, 'denominador': 0, 'proporcao': 0.5, 'unidade': 'dias'},
            {'numerador': 1, 'denominador': 2, 'proporcao': float('inf'), 'unidade': 'dias'},
            {'numerador': 1, 'denominador': 2, 'proporcao': 0.7, 'unidade': 'dias'},
            {'numerador': 1, 'denominador': 2, 'proporcao': 0.5, 'unidade': '%'},
        ]
        for cobertura in coberturas:
            with self.subTest(cobertura=cobertura), self.base_modificada() as (banco, caminho):
                self.alterar_registro(banco, lambda r: r.update(cobertura=cobertura), 'clima.cobertura_chuva')
                self.assertIndisponivel(self.consulta(banco, caminho))

    def test_erro_de_programacao_continua_500(self):
        with self.base_modificada() as (banco, caminho):
            with patch('api_territorio.armazenamento._ultima_coleta', side_effect=RuntimeError('falha simulada')):
                resposta = self.consulta(banco, caminho)
            self.assertEqual(resposta.status_code, 500)
            self.assertEqual(resposta.json()['erro']['codigo'], 'ERRO_INTERNO')
            self.assertNotIn('falha simulada', resposta.text)

    def test_edicao_ativa_inexistente_e_falha_e_explicita_continua_404(self):
        with self.base_modificada() as (banco, caminho):
            banco.execute("UPDATE configuracao SET valor='inexistente' WHERE chave='edicao_ativa'")
            self.assertIndisponivel(self.consulta(banco, caminho))
            resposta = self.consulta(banco, caminho, {'codigo_ibge': '3550308', 'versao_base': 'inexistente'})
            self.assertEqual(resposta.status_code, 404)
            self.assertEqual(resposta.json()['erro']['codigo'], 'EDICAO_INEXISTENTE')

    def test_importacao_reverte_gravacoes_se_falhar_no_meio(self):
        class ConexaoComFalha(sqlite3.Connection):
            def executemany(self, sql, parametros):
                if sql.startswith('INSERT INTO indicadores'):
                    raise sqlite3.IntegrityError('Falha simulada antes da ativação')
                return super().executemany(sql, parametros)

        conectar = sqlite3.connect
        def conexao_com_falha(*args, **kwargs):
            return conectar(*args, factory=ConexaoComFalha, **kwargs)

        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'transacao.sqlite3'
            with patch('api_territorio.armazenamento.sqlite3.connect', side_effect=conexao_com_falha):
                with self.assertRaises(sqlite3.IntegrityError):
                    preparar_base(destino=caminho)
            with closing(sqlite3.connect(caminho)) as banco:
                for tabela in ('edicoes', 'municipios', 'catalogo', 'indicadores', 'configuracao'):
                    self.assertEqual(banco.execute('SELECT COUNT(*) FROM ' + tabela).fetchone()[0], 0)
            self.assertTrue(preparar_base(destino=caminho)['importada'])
            self.assertEqual(len(Repositorio(caminho).consultar('3550308')['indicadores']), 18)

    def test_armazenamento_continua_usando_so_biblioteca_padrao(self):
        programa = '''
from pathlib import Path
import tempfile
from api_territorio.armazenamento import preparar_base, Repositorio
with tempfile.TemporaryDirectory() as pasta:
    caminho = Path(pasta) / 'stdlib.sqlite3'
    preparar_base(destino=caminho)
    assert len(Repositorio(caminho).consultar('3550308')['indicadores']) == 18
'''
        resultado = subprocess.run(
            [sys.executable, '-S', '-c', programa], cwd=RAIZ, capture_output=True, text=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)


if __name__ == '__main__':
    unittest.main()
