"""Importação validada de edições imutáveis e consulta local, sem rede ou Excel."""
from contextlib import closing
import csv
from datetime import date, datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[1]
BASE_PADRAO = RAIZ / 'api_territorio/var/territorio.sqlite3'
EDICAO_PADRAO = RAIZ / 'dados/edicoes/territorio-2026-10-28-r1'
CADASTRO_PADRAO = RAIZ / 'api_territorio/referencias/municipios_ibge.json'


class EntradaInvalida(ValueError): pass
class MunicipioInexistente(LookupError): pass
class EdicaoInexistente(LookupError): pass
class BaseIndisponivel(RuntimeError): pass


def _json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _serializar(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def _ultima_coleta(valores):
    if not valores:
        return None
    ultimo_dia = max(v[:10] for v in valores)
    candidatos = [v for v in valores if v[:10] == ultimo_dia]
    return ultimo_dia if any(len(v) == 10 for v in candidatos) else max(candidatos, key=lambda v: datetime.fromisoformat(v.replace('Z', '+00:00')))


def _instituicao(url):
    host = (urlparse(url).hostname or '').removeprefix('www.')
    names = {
        'portal.inmet.gov.br': 'INMET', 'apisidra.ibge.gov.br': 'IBGE/SIDRA',
        'atlasdigital.mdr.gov.br': 'Atlas Digital de Desastres no Brasil',
        'ssp.sp.gov.br': 'SSP-SP', 'seguranca.pr.gov.br': 'SESP-PR/CAPE',
        'dados.mg.gov.br': 'SEJUSP-MG', 'ssp.df.gov.br': 'SSP-DF',
        'ce.gov.br': 'SSPDS-CE', 'ssp.rs.gov.br': 'SSP-RS',
        'sds.pe.gov.br': 'SDS-PE', 'ispdados.rj.gov.br': 'ISP-RJ',
        'ba.gov.br': 'SSP-BA', 'goias.gov.br': 'SSP-GO',
    }
    if host not in names:
        raise ValueError('Instituição não mapeada: ' + host)
    return names[host]


def _validar_snapshot(pasta):
    pasta = Path(pasta).resolve()
    manifesto = _json(pasta / 'manifesto.json')
    expected = {'manifesto.json', 'SHA256SUMS'}
    for item in manifesto['arquivos']:
        path = (pasta / item['arquivo']).resolve()
        if not path.is_relative_to(pasta) or not path.is_file():
            raise ValueError('Arquivo inválido no manifesto: ' + item['arquivo'])
        if path.stat().st_size != item['bytes'] or _hash(path) != item['sha256']:
            raise ValueError('Integridade divergente: ' + item['arquivo'])
        expected.add(item['arquivo'])
    for line in (pasta / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        path = (pasta / name).resolve()
        if not path.is_relative_to(pasta) or _hash(path) != digest:
            raise ValueError('SHA256SUMS divergente: ' + name)
    actual = {p.relative_to(pasta).as_posix() for p in pasta.rglob('*') if p.is_file()}
    if actual != expected:
        raise ValueError('Lista de arquivos divergente da edição congelada.')
    return manifesto


def preparar_base(edicao=EDICAO_PADRAO, destino=BASE_PADRAO, cadastro=CADASTRO_PADRAO):
    """Importa atomicamente uma edição; mesma edição nunca é sobrescrita."""
    edicao, destino, cadastro = Path(edicao).resolve(), Path(destino).resolve(), Path(cadastro).resolve()
    if destino.is_relative_to(edicao):
        raise ValueError('A base operacional não pode ser gravada dentro da edição congelada.')
    manifest = _validar_snapshot(edicao)
    rows = _json(edicao / 'indicadores.json')
    municipios = _json(cadastro)
    meta = _json(cadastro.with_name('municipios_ibge.fonte.json'))
    if _hash(cadastro) != meta['sha256_cadastro_normalizado'] or len(municipios) != meta['quantidade']:
        raise ValueError('Cadastro IBGE com integridade divergente.')
    municipalities = {r['codigo_ibge']: r for r in municipios}
    if len(municipalities) != len(municipios):
        raise ValueError('Município duplicado no cadastro IBGE.')
    sources = {}
    with (edicao / 'fontes.csv').open(encoding='utf-8-sig', newline='') as f:
        for source in csv.DictReader(f):
            sources[source['fonte_id']] = {'instituicao': _instituicao(source['url']), 'url': source['url'], 'coletado_em': source['data_extracao']}
    covered = {r['codigo_ibge'] for r in rows}
    if covered != set(manifest['municipios']) or len(rows) != manifest['indicadores']:
        raise ValueError('Cobertura ou quantidade de indicadores divergente.')
    catalog, keys, normalized = {}, set(), []
    reasons = {'FONTE_SEM_VALOR', 'SEM_RECORTE_RESIDENCIAL', 'SEM_COBERTURA_TERRITORIAL', 'PERIODO_NAO_DISPONIVEL'}
    for row in rows:
        municipality = municipalities.get(row['codigo_ibge'])
        if not municipality or any(row[k] != municipality[k] for k in ['municipio', 'uf', 'abrangencia']):
            raise ValueError('Identificação municipal divergente do IBGE: ' + row['codigo_ibge'])
        key = (row['codigo_ibge'], row['id'], row['periodo']['inicio'], row['periodo']['fim'])
        if key in keys:
            raise ValueError('Indicador duplicado: ' + str(key))
        keys.add(key)
        item = {'id': row['id'], 'unidade': row['unidade'], 'periodo': row['periodo']}
        if catalog.setdefault(row['id'], item) != item:
            raise ValueError('Catálogo inconsistente entre municípios.')
        value = row['valor']
        if value is None:
            if row['disponibilidade'] != 'AUSENTE' or row['motivo_ausencia'] not in reasons:
                raise ValueError('Ausência sem motivo válido.')
        elif isinstance(value, bool) or not math.isfinite(value) or row['disponibilidade'] != 'DISPONIVEL' or row['motivo_ausencia'] is not None:
            raise ValueError('Valor ou estado de disponibilidade inválido.')
        payload = {k: row[k] for k in ['id', 'valor', 'unidade', 'periodo', 'disponibilidade', 'motivo_ausencia', 'metodo', 'estacao', 'cobertura', 'limitacoes']}
        payload['fontes'] = [sources[s] for s in row['fontes_ids']]
        normalized.append((key, payload))
    if len(catalog) != 18 or any(sum(r['codigo_ibge'] == code for r in rows) != 18 for code in covered):
        raise ValueError('Esperados 18 indicadores por município nesta primeira versão.')
    edition_hash, register_hash = _hash(edicao / 'manifesto.json'), _hash(cadastro)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(destino)) as db:
        if db.execute('PRAGMA user_version').fetchone()[0] not in (0, 1):
            raise ValueError('Esquema operacional incompatível; não sobrescrever a base existente.')
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript('''
            CREATE TABLE IF NOT EXISTS edicoes (
                versao TEXT PRIMARY KEY, contrato TEXT NOT NULL, manifesto_sha256 TEXT NOT NULL,
                cadastro_sha256 TEXT NOT NULL, importado_em TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS configuracao (chave TEXT PRIMARY KEY, valor TEXT NOT NULL REFERENCES edicoes(versao));
            CREATE TABLE IF NOT EXISTS municipios (
                edicao TEXT NOT NULL REFERENCES edicoes(versao), codigo TEXT NOT NULL,
                municipio TEXT NOT NULL, uf TEXT NOT NULL, abrangencia TEXT NOT NULL,
                coberto INTEGER NOT NULL CHECK(coberto IN (0,1)), PRIMARY KEY(edicao,codigo));
            CREATE TABLE IF NOT EXISTS catalogo (
                edicao TEXT NOT NULL REFERENCES edicoes(versao), indicador TEXT NOT NULL,
                dados TEXT NOT NULL, PRIMARY KEY(edicao,indicador));
            CREATE TABLE IF NOT EXISTS indicadores (
                edicao TEXT NOT NULL, municipio TEXT NOT NULL, indicador TEXT NOT NULL,
                inicio TEXT NOT NULL, fim TEXT NOT NULL, dados TEXT NOT NULL,
                PRIMARY KEY(edicao,municipio,indicador,inicio,fim),
                FOREIGN KEY(edicao,municipio) REFERENCES municipios(edicao,codigo),
                FOREIGN KEY(edicao,indicador) REFERENCES catalogo(edicao,indicador));
            PRAGMA user_version=1;
        ''')
        db.execute('BEGIN IMMEDIATE')
        try:
            previous = db.execute('SELECT manifesto_sha256,cadastro_sha256 FROM edicoes WHERE versao=?', (manifest['versao_base'],)).fetchone()
            if previous:
                if previous != (edition_hash, register_hash):
                    raise ValueError('Edição já importada com outra origem: criar nova edição, sem sobrescrever.')
                db.rollback()
                return {'versao_base': manifest['versao_base'], 'importada': False, 'indicadores': len(rows)}
            db.execute('INSERT INTO edicoes VALUES(?,?,?,?,?)', (manifest['versao_base'], manifest['versao_contrato_referencia'], edition_hash, register_hash, datetime.now(timezone.utc).isoformat()))
            db.executemany('INSERT INTO municipios VALUES(?,?,?,?,?,?)', [(manifest['versao_base'], r['codigo_ibge'], r['municipio'], r['uf'], r['abrangencia'], int(r['codigo_ibge'] in covered)) for r in municipios])
            db.executemany('INSERT INTO catalogo VALUES(?,?,?)', [(manifest['versao_base'], r['id'], _serializar(r)) for r in catalog.values()])
            db.executemany('INSERT INTO indicadores VALUES(?,?,?,?,?,?)', [(manifest['versao_base'], *key, _serializar(payload)) for key, payload in normalized])
            # Ativação explícita da primeira edição. Novas importações não mudam a edição ativa.
            db.execute("INSERT OR IGNORE INTO configuracao VALUES('edicao_ativa',?)", (manifest['versao_base'],))
            db.commit()
        except Exception:
            db.rollback()
            raise
    return {'versao_base': manifest['versao_base'], 'importada': True, 'municipios_cobertos': len(covered), 'municipios_cadastrados': len(municipios), 'indicadores': len(rows), 'disponiveis': manifest['disponiveis'], 'ausentes': manifest['ausentes']}


def _periodo(value):
    if not isinstance(value, dict) or set(value) != {'inicio', 'fim'}:
        raise EntradaInvalida('Período exige inicio e fim.')
    for field in ['inicio', 'fim']:
        if not isinstance(value[field], str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value[field]):
            raise EntradaInvalida('Datas devem usar AAAA-MM-DD.')
        try:
            date.fromisoformat(value[field])
        except ValueError as exc:
            raise EntradaInvalida('Data inválida.') from exc
    if value['inicio'] > value['fim']:
        raise EntradaInvalida('Início posterior ao fim.')
    return value


class Repositorio:
    def __init__(self, caminho=BASE_PADRAO):
        self.caminho = Path(caminho).resolve()

    def consultar(self, codigo_ibge, versao_base=None, consultas=None):
        """Consulta indexada somente leitura; sem autenticação ou serviço HTTP."""
        if not isinstance(codigo_ibge, str) or not re.fullmatch(r'\d{7}', codigo_ibge):
            raise EntradaInvalida('Código IBGE deve ser texto com sete dígitos.')
        if versao_base is not None and (not isinstance(versao_base, str) or not versao_base):
            raise EntradaInvalida('Edição deve ser texto não vazio.')
        if consultas is not None and (not isinstance(consultas, list) or not consultas):
            raise EntradaInvalida('Consultas deve ser lista não vazia.')
        try:
            with closing(sqlite3.connect(self.caminho.as_uri() + '?mode=ro', uri=True, timeout=1.0)) as db:
                db.row_factory = sqlite3.Row
                if db.execute('PRAGMA user_version').fetchone()[0] != 1:
                    raise BaseIndisponivel('Esquema operacional incompatível.')
                edition = versao_base
                if edition is None:
                    active = db.execute("SELECT valor FROM configuracao WHERE chave='edicao_ativa'").fetchone()
                    if active is None: raise BaseIndisponivel('Nenhuma edição ativa.')
                    edition = active[0]
                info = db.execute('SELECT contrato FROM edicoes WHERE versao=?', (edition,)).fetchone()
                if info is None: raise EdicaoInexistente(edition)
                city = db.execute('SELECT * FROM municipios WHERE edicao=? AND codigo=?', (edition, codigo_ibge)).fetchone()
                if city is None: raise MunicipioInexistente(codigo_ibge)
                catalog = {r['indicador']: json.loads(r['dados']) for r in db.execute('SELECT indicador,dados FROM catalogo WHERE edicao=? ORDER BY indicador', (edition,))}
                requested = consultas if consultas is not None else [{'indicador': ident} for ident in catalog]
                output, seen = [], set()
                for request in requested:
                    if not isinstance(request, dict) or set(request) - {'indicador', 'periodo'} or not isinstance(request.get('indicador'), str) or request['indicador'] not in catalog:
                        raise EntradaInvalida('Consulta ou indicador inválido.')
                    ident = request['indicador']
                    period = _periodo(request['periodo']) if 'periodo' in request else catalog[ident]['periodo']
                    key = (ident, period['inicio'], period['fim'])
                    if key in seen: raise EntradaInvalida('Consulta duplicada.')
                    seen.add(key)
                    if not city['coberto']:
                        result = {'id': ident, 'valor': None, 'unidade': catalog[ident]['unidade'], 'periodo': period, 'disponibilidade': 'AUSENTE', 'motivo_ausencia': 'SEM_COBERTURA_TERRITORIAL', 'fontes': [], 'metodo': 'Município válido no cadastro IBGE, fora da cobertura desta edição.', 'estacao': None, 'cobertura': None, 'limitacoes': ['Nenhum valor estimado a partir de vizinhos ou médias estaduais.']}
                    else:
                        stored = db.execute('SELECT dados FROM indicadores WHERE edicao=? AND municipio=? AND indicador=? AND inicio=? AND fim=?', (edition, codigo_ibge, *key)).fetchone()
                        if stored:
                            result = json.loads(stored[0])
                        else:
                            if period == catalog[ident]['periodo']:
                                raise BaseIndisponivel('Indicador padrão ausente da base operacional.')
                            result = {'id': ident, 'valor': None, 'unidade': catalog[ident]['unidade'], 'periodo': period, 'disponibilidade': 'AUSENTE', 'motivo_ausencia': 'PERIODO_NAO_DISPONIVEL', 'fontes': [], 'metodo': 'Não há valor processado para o intervalo solicitado nesta edição.', 'estacao': None, 'cobertura': None, 'limitacoes': ['Sem substituição silenciosa do período solicitado.']}
                    output.append(result)
                collected = [s['coletado_em'] for r in output for s in r['fontes']]
                return {'versao_contrato': info['contrato'], 'versao_base': edition, 'consultado_em': datetime.now(timezone.utc).isoformat(), 'territorio': {'codigo_ibge': codigo_ibge, **{k: city[k] for k in ['municipio', 'uf', 'abrangencia']}}, 'atualizacao': {'ultima_coleta_em': _ultima_coleta(collected), 'situacao': 'SEM_FALHA_REGISTRADA'}, 'indicadores': output}
        except (sqlite3.Error, json.JSONDecodeError) as exc:
            raise BaseIndisponivel('Base operacional indisponível ou inconsistente.') from exc
