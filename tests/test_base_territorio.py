import hashlib
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from api_territorio.armazenamento import (
    preparar_base, Repositorio, EDICAO_PADRAO, CADASTRO_PADRAO,
    EntradaInvalida, MunicipioInexistente, EdicaoInexistente, BaseIndisponivel, _ultima_coleta,
)


class BaseTerritorioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.temp.name) / 'territorio.sqlite3'
        cls.resultado = preparar_base(destino=cls.db)
        cls.repo = Repositorio(cls.db)
        cls.originais = json.loads((EDICAO_PADRAO / 'indicadores.json').read_text(encoding='utf-8'))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_todos_os_180_valores_periodos_lacunas_e_metadados_preservados(self):
        presentes = ausentes = 0
        for code in sorted({r['codigo_ibge'] for r in self.originais}):
            resultado = self.repo.consultar(code)
            self.assertEqual(resultado['versao_base'], 'territorio-2026-10-28-r1')
            self.assertEqual(resultado['atualizacao']['ultima_coleta_em'], '2026-10-27')
            items = {r['id']: r for r in resultado['indicadores']}
            self.assertEqual(len(items), 18)
            for original in [r for r in self.originais if r['codigo_ibge'] == code]:
                atual = items[original['id']]
                for field in ['valor', 'unidade', 'periodo', 'disponibilidade', 'motivo_ausencia', 'estacao', 'cobertura', 'limitacoes', 'metodo']:
                    self.assertEqual(atual[field], original[field], (code, original['id'], field))
                self.assertTrue(atual['fontes'])
                self.assertTrue(all(s['instituicao'] and s['url'].startswith('https://') and s['coletado_em'] == '2026-10-27' for s in atual['fontes']))
                presentes += atual['valor'] is not None
                ausentes += atual['valor'] is None
        self.assertEqual((presentes, ausentes), (153, 27))

    def test_sao_paulo_totais_e_taxas(self):
        result = {r['id']: r for r in self.repo.consultar('3550308')['indicadores']}
        self.assertEqual(result['seguranca.roubo_residencial']['valor'], 657)
        self.assertEqual(result['seguranca.furto_residencial']['valor'], 5193)
        self.assertAlmostEqual(result['seguranca.taxa_roubo_residencial']['valor'], 657 / 11904961 * 100000)
        self.assertEqual(len(result['seguranca.taxa_roubo_residencial']['fontes']), 2)

    def test_lacunas_recife_e_goiania(self):
        recife = {r['id']: r for r in self.repo.consultar('2611606')['indicadores']}
        self.assertAlmostEqual(recife['clima.cobertura_chuva']['valor'], 2371 / 4018)
        self.assertEqual(recife['seguranca.furto_residencial']['motivo_ausencia'], 'SEM_RECORTE_RESIDENCIAL')
        for r in self.repo.consultar('5208707')['indicadores']:
            if r['id'].startswith('seguranca.'):
                self.assertIsNone(r['valor'])
                self.assertEqual(r['motivo_ausencia'], 'FONTE_SEM_VALOR')

    def test_df_representa_distrito_federal(self):
        self.assertEqual(self.repo.consultar('5300108')['territorio']['abrangencia'], 'distrito_federal')

    def test_municipio_valido_sem_cobertura_e_codigo_inexistente_sao_distintos(self):
        result = self.repo.consultar('3509502')  # Campinas, fora dos dez municípios.
        self.assertEqual(result['territorio']['municipio'], 'Campinas')
        self.assertIsNone(result['atualizacao']['ultima_coleta_em'])
        self.assertEqual(len(result['indicadores']), 18)
        self.assertTrue(all(r['valor'] is None and r['motivo_ausencia'] == 'SEM_COBERTURA_TERRITORIAL' for r in result['indicadores']))
        with self.assertRaises(MunicipioInexistente):
            self.repo.consultar('9999999')

    def test_periodo_valido_ausente_nao_substitui_ano(self):
        period = {'inicio': '2024-01-01', 'fim': '2024-12-31'}
        result = self.repo.consultar('3550308', consultas=[{'indicador': 'seguranca.roubo_residencial', 'periodo': period}, {'indicador': 'clima.chuva_normal'}])
        self.assertEqual(result['indicadores'][0]['periodo'], period)
        self.assertEqual(result['indicadores'][0]['motivo_ausencia'], 'PERIODO_NAO_DISPONIVEL')
        self.assertIsNotNone(result['indicadores'][1]['valor'])

    def test_entradas_invalidas_e_consultas_duplicadas(self):
        for code in [3550308, '355030', 'abcdefg', None]:
            with self.subTest(code=code), self.assertRaises(EntradaInvalida):
                self.repo.consultar(code)
        for queries in [[], {}, [{'indicador': 'desconhecido'}], [{'indicador': 'clima.chuva_normal', 'extra': 1}], [{'indicador': 'clima.chuva_normal'}] * 2, [{'indicador': 'clima.chuva_normal', 'periodo': {'inicio': '2025-02-30', 'fim': '2025-03-01'}}], [{'indicador': 'clima.chuva_normal', 'periodo': {'inicio': '20250101', 'fim': '2025-12-31'}}]]:
            with self.subTest(queries=queries), self.assertRaises(EntradaInvalida):
                self.repo.consultar('3550308', consultas=queries)

    def test_edicao_inexistente_e_base_ausente(self):
        with self.assertRaises(EdicaoInexistente):
            self.repo.consultar('3550308', versao_base='nao-existe')
        nonexistent = Path(self.temp.name) / 'nao-criar.sqlite3'
        with self.assertRaises(BaseIndisponivel):
            Repositorio(nonexistent).consultar('3550308')
        self.assertFalse(nonexistent.exists())

    def test_consulta_nao_le_fontes_planilha_ou_rede(self):
        with patch.object(Path, 'read_text', side_effect=AssertionError('Leitura de arquivo externo')), patch('urllib.request.urlopen', side_effect=AssertionError('Chamada de rede')):
            self.assertEqual(len(self.repo.consultar('4106902')['indicadores']), 18)

    def test_importacao_idempotente(self):
        self.assertFalse(preparar_base(destino=self.db)['importada'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM indicadores').fetchone()[0], 180)

    def test_nova_edicao_nao_muda_ativa_e_consulta_explicita_e_preservada(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            db_path = folder / 'isolada.sqlite3'
            preparar_base(destino=db_path)
            copy = folder / 'segunda-edicao'
            shutil.copytree(EDICAO_PADRAO, copy)
            manifest = json.loads((copy / 'manifesto.json').read_text(encoding='utf-8'))
            manifest['versao_base'] = 'edicao-simulada-para-teste'
            (copy / 'manifesto.json').write_bytes(json.dumps(manifest).encode())
            sums = (copy / 'SHA256SUMS').read_text().splitlines()
            sums = [(hashlib.sha256((copy / 'manifesto.json').read_bytes()).hexdigest() + '  manifesto.json') if line.endswith('  manifesto.json') else line for line in sums]
            (copy / 'SHA256SUMS').write_bytes(('\n'.join(sums) + '\n').encode())
            preparar_base(edicao=copy, destino=db_path)
            repo = Repositorio(db_path)
            current = repo.consultar('3550308')
            pinned = repo.consultar('3550308', versao_base='edicao-simulada-para-teste')
            self.assertEqual(current['versao_base'], 'territorio-2026-10-28-r1')
            self.assertEqual(pinned['versao_base'], 'edicao-simulada-para-teste')
            self.assertEqual(current['indicadores'], pinned['indicadores'])

    def test_rejeita_snapshot_adulterado_e_preserva_edicao_existente(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / 'adulterada'
            shutil.copytree(EDICAO_PADRAO, copy)
            with (copy / 'indicadores.json').open('ab') as f:
                f.write(b' ')
            with self.assertRaisesRegex(ValueError, 'Integridade divergente'):
                preparar_base(edicao=copy, destino=self.db)
        self.assertEqual(len(self.repo.consultar('3550308')['indicadores']), 18)

    def test_mesma_edicao_com_cadastro_diferente_nao_sobrescreve(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            rows = json.loads(CADASTRO_PADRAO.read_text(encoding='utf-8'))
            next(r for r in rows if r['codigo_ibge'] == '3509502')['municipio'] = 'Nome alterado para teste'
            payload = json.dumps(rows, ensure_ascii=False).encode()
            path = folder / 'municipios_ibge.json'
            path.write_bytes(payload)
            meta = json.loads(CADASTRO_PADRAO.with_name('municipios_ibge.fonte.json').read_text(encoding='utf-8'))
            meta['sha256_cadastro_normalizado'] = hashlib.sha256(payload).hexdigest()
            (folder / 'municipios_ibge.fonte.json').write_text(json.dumps(meta), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Edição já importada'):
                preparar_base(destino=self.db, cadastro=path)
        self.assertEqual(self.repo.consultar('3509502')['territorio']['municipio'], 'Campinas')

    def test_consulta_utiliza_indice_composto(self):
        with closing(sqlite3.connect(self.db)) as db:
            plan = db.execute('EXPLAIN QUERY PLAN SELECT dados FROM indicadores WHERE edicao=? AND municipio=? AND indicador=? AND inicio=? AND fim=?', ('territorio-2026-10-28-r1', '3550308', 'clima.chuva_normal', '1991-01-01', '2020-12-31')).fetchall()
            self.assertTrue(any('SEARCH' in row[-1] and 'INDEX' in row[-1] for row in plan))

    def test_ultima_coleta_preserva_precisao(self):
        self.assertEqual(_ultima_coleta(['2026-10-27', '2026-10-27T12:00:00+00:00']), '2026-10-27')
        self.assertEqual(_ultima_coleta(['2026-10-26', '2026-10-27T12:00:00+00:00']), '2026-10-27T12:00:00+00:00')
        self.assertIsNone(_ultima_coleta([]))
        self.assertEqual(_ultima_coleta(['2026-10-27T12:00:00Z', '2026-10-27T12:00:00.1Z']), '2026-10-27T12:00:00.1Z')

    def test_json_operacional_corrompido_e_falha_tecnica(self):
        with tempfile.TemporaryDirectory() as temp:
            damaged = Path(temp) / 'corrompida.sqlite3'
            shutil.copyfile(self.db, damaged)
            with closing(sqlite3.connect(damaged)) as db:
                db.execute("UPDATE indicadores SET dados='{' WHERE municipio='3550308' AND indicador='clima.chuva_normal'")
                db.commit()
            with self.assertRaises(BaseIndisponivel):
                Repositorio(damaged).consultar('3550308')


if __name__ == '__main__':
    unittest.main()
