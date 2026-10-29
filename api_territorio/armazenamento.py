"""Importação validada de edições imutáveis e consulta local, sem rede ou Excel."""
from contextlib import closing
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any
from urllib.parse import urlparse

from .validadores import (
    DadoInconsistente, EntradaInvalida, validar_catalogo, validar_indicador, validar_periodo,
)

RAIZ = Path(__file__).resolve().parents[1]
BASE_PADRAO = RAIZ / 'api_territorio/var/territorio.sqlite3'
EDICAO_PADRAO = RAIZ / 'dados/edicoes/territorio-2026-10-28-r1'
CADASTRO_PADRAO = RAIZ / 'api_territorio/referencias/municipios_ibge.json'
ChaveIndicador = tuple[str, str, str, str]
Registro = dict[str, Any]


class MunicipioInexistente(LookupError):
    """Código não encontrado no cadastro da edição."""


class EdicaoInexistente(LookupError):
    """Edição solicitada não importada."""


class BaseIndisponivel(RuntimeError):
    """Falha técnica da base, distinta de ausência na fonte."""


def _json(caminho: str | Path) -> Any:
    return json.loads(Path(caminho).read_text(encoding='utf-8-sig'))


def _hash(caminho: str | Path) -> str:
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def _serializar(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def _ultima_coleta(valores: list[str]) -> str | None:
    if not valores:
        return None
    ultimo_dia = max(v[:10] for v in valores)
    candidatos = [v for v in valores if v[:10] == ultimo_dia]
    if any(len(v) == 10 for v in candidatos):
        return ultimo_dia
    return max(candidatos, key=lambda v: datetime.fromisoformat(v.replace('Z', '+00:00')))


def _instituicao(url: str) -> str:
    host = (urlparse(url).hostname or '').removeprefix('www.')
    nomes = {
        'portal.inmet.gov.br': 'INMET', 'apisidra.ibge.gov.br': 'IBGE/SIDRA',
        'atlasdigital.mdr.gov.br': 'Atlas Digital de Desastres no Brasil',
        'ssp.sp.gov.br': 'SSP-SP', 'seguranca.pr.gov.br': 'SESP-PR/CAPE',
        'dados.mg.gov.br': 'SEJUSP-MG', 'ssp.df.gov.br': 'SSP-DF',
        'ce.gov.br': 'SSPDS-CE', 'ssp.rs.gov.br': 'SSP-RS',
        'sds.pe.gov.br': 'SDS-PE', 'ispdados.rj.gov.br': 'ISP-RJ',
        'ba.gov.br': 'SSP-BA', 'goias.gov.br': 'SSP-GO',
    }
    if host not in nomes:
        raise ValueError('Instituição não mapeada: ' + host)
    return nomes[host]


def _validar_snapshot(pasta: Path) -> dict[str, Any]:
    pasta = Path(pasta).resolve()
    manifesto = _json(pasta / 'manifesto.json')
    esperados = {'manifesto.json', 'SHA256SUMS'}
    for item in manifesto['arquivos']:
        path = (pasta / item['arquivo']).resolve()
        if not path.is_relative_to(pasta) or not path.is_file():
            raise ValueError('Arquivo inválido no manifesto: ' + item['arquivo'])
        if path.stat().st_size != item['bytes'] or _hash(path) != item['sha256']:
            raise ValueError('Integridade divergente: ' + item['arquivo'])
        esperados.add(item['arquivo'])
    for line in (pasta / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        path = (pasta / name).resolve()
        if not path.is_relative_to(pasta) or _hash(path) != digest:
            raise ValueError('SHA256SUMS divergente: ' + name)
    encontrados = {p.relative_to(pasta).as_posix() for p in pasta.rglob('*') if p.is_file()}
    if encontrados != esperados:
        raise ValueError('Lista de arquivos divergente da edição congelada.')
    return manifesto


def _ler_origem(edicao: Path, cadastro: Path) -> tuple[Registro, list[Registro], list[Registro], Registro]:
    manifesto = _validar_snapshot(edicao)
    registros = _json(edicao / 'indicadores.json')
    municipios = _json(cadastro)
    metadados = _json(cadastro.with_name('municipios_ibge.fonte.json'))
    if (_hash(cadastro) != metadados['sha256_cadastro_normalizado']
            or len(municipios) != metadados['quantidade']):
        raise ValueError('Cadastro IBGE com integridade divergente.')
    fontes = {}
    with (edicao / 'fontes.csv').open(encoding='utf-8-sig', newline='') as arquivo:
        for fonte in csv.DictReader(arquivo):
            fontes[fonte['fonte_id']] = {
                'instituicao': _instituicao(fonte['url']), 'url': fonte['url'],
                'coletado_em': fonte['data_extracao'],
            }
    return manifesto, registros, municipios, fontes


def _normalizar_registros(
    manifesto: Registro, registros: list[Registro], municipios: list[Registro], fontes: Registro,
) -> tuple[Registro, set[str], list[tuple[ChaveIndicador, Registro]]]:
    cadastro = {r['codigo_ibge']: r for r in municipios}
    if len(cadastro) != len(municipios):
        raise ValueError('Município duplicado no cadastro IBGE.')
    cobertos = {r['codigo_ibge'] for r in registros}
    if cobertos != set(manifesto['municipios']) or len(registros) != manifesto['indicadores']:
        raise ValueError('Cobertura ou quantidade de indicadores divergente.')
    catalogo, chaves, normalizados = {}, set(), []
    for registro in registros:
        municipio = cadastro.get(registro['codigo_ibge'])
        if not municipio or any(registro[c] != municipio[c] for c in ('municipio', 'uf', 'abrangencia')):
            raise ValueError('Identificação municipal divergente do IBGE: ' + registro['codigo_ibge'])
        periodo = validar_periodo(registro['periodo'])
        chave = (registro['codigo_ibge'], registro['id'], periodo['inicio'], periodo['fim'])
        if chave in chaves:
            raise ValueError('Indicador duplicado: ' + str(chave))
        chaves.add(chave)
        item = {c: registro[c] for c in ('id', 'unidade', 'periodo')}
        if catalogo.setdefault(registro['id'], item) != item:
            raise ValueError('Catálogo inconsistente entre municípios.')
        indicador = {c: registro[c] for c in (
            'id', 'valor', 'unidade', 'periodo', 'disponibilidade', 'motivo_ausencia',
            'metodo', 'estacao', 'cobertura', 'limitacoes',
        )}
        indicador['fontes'] = [fontes[f] for f in registro['fontes_ids']]
        validar_indicador(indicador, registro['id'], periodo, registro['unidade'])
        normalizados.append((chave, indicador))
    validar_catalogo(catalogo)
    if any(sum(r['codigo_ibge'] == codigo for r in registros) != 18 for codigo in cobertos):
        raise ValueError('Esperados 18 indicadores por município nesta primeira versão.')
    return catalogo, cobertos, normalizados


ESQUEMA_SQL = '''
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
        '''


def _gravar_edicao(
    destino: Path, manifesto: Registro, municipios: list[Registro], cobertos: set[str],
    catalogo: Registro, normalizados: list[tuple[ChaveIndicador, Registro]],
    manifesto_hash: str, cadastro_hash: str,
) -> bool:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(destino)) as banco:
        if banco.execute('PRAGMA user_version').fetchone()[0] not in (0, 1):
            raise ValueError('Esquema operacional incompatível; não sobrescrever a base existente.')
        banco.execute('PRAGMA foreign_keys=ON')
        banco.executescript(ESQUEMA_SQL)
        banco.execute('BEGIN IMMEDIATE')
        try:
            versao = manifesto['versao_base']
            anterior = banco.execute(
                'SELECT manifesto_sha256,cadastro_sha256 FROM edicoes WHERE versao=?', (versao,),
            ).fetchone()
            if anterior:
                if anterior != (manifesto_hash, cadastro_hash):
                    raise ValueError('Edição já importada com outra origem: criar nova edição, sem sobrescrever.')
                banco.rollback()
                return False
            banco.execute('INSERT INTO edicoes VALUES(?,?,?,?,?)', (
                versao, manifesto['versao_contrato_referencia'], manifesto_hash,
                cadastro_hash, datetime.now(timezone.utc).isoformat(),
            ))
            banco.executemany('INSERT INTO municipios VALUES(?,?,?,?,?,?)', [
                (versao, r['codigo_ibge'], r['municipio'], r['uf'], r['abrangencia'], int(r['codigo_ibge'] in cobertos))
                for r in municipios
            ])
            banco.executemany('INSERT INTO catalogo VALUES(?,?,?)', [
                (versao, r['id'], _serializar(r)) for r in catalogo.values()
            ])
            banco.executemany('INSERT INTO indicadores VALUES(?,?,?,?,?,?)', [
                (versao, *chave, _serializar(indicador)) for chave, indicador in normalizados
            ])
            # Novas importações não mudam a edição ativa.
            banco.execute("INSERT OR IGNORE INTO configuracao VALUES('edicao_ativa',?)", (versao,))
            banco.commit()
        except Exception:
            banco.rollback()
            raise
    return True


def preparar_base(
    edicao: str | Path = EDICAO_PADRAO, destino: str | Path = BASE_PADRAO,
    cadastro: str | Path = CADASTRO_PADRAO,
) -> Registro:
    """Valida, normaliza e importa atomicamente, sem sobrescrever uma edição."""
    edicao, destino, cadastro = Path(edicao).resolve(), Path(destino).resolve(), Path(cadastro).resolve()
    if destino.is_relative_to(edicao):
        raise ValueError('A base operacional não pode ser gravada dentro da edição congelada.')
    manifesto, registros, municipios, fontes = _ler_origem(edicao, cadastro)
    catalogo, cobertos, normalizados = _normalizar_registros(manifesto, registros, municipios, fontes)
    importada = _gravar_edicao(
        destino, manifesto, municipios, cobertos, catalogo, normalizados,
        _hash(edicao / 'manifesto.json'), _hash(cadastro),
    )
    resultado = {'versao_base': manifesto['versao_base'], 'importada': importada, 'indicadores': len(registros)}
    if importada:
        resultado.update({
            'municipios_cobertos': len(cobertos), 'municipios_cadastrados': len(municipios),
            'disponiveis': manifesto['disponiveis'], 'ausentes': manifesto['ausentes'],
        })
    return resultado


def _carregar_registro(bruto: Any) -> Any:
    """Interpreta somente a fronteira de dados, sem mascarar erros de programação."""
    if not isinstance(bruto, str):
        raise DadoInconsistente('Registro operacional deve conter JSON textual.')

    def objeto(pares: list[tuple[str, Any]]) -> Registro:
        resultado = {}
        for chave, valor in pares:
            if chave in resultado:
                raise DadoInconsistente('Campo duplicado no JSON operacional.')
            resultado[chave] = valor
        return resultado

    def constante_invalida(valor: str) -> None:
        raise DadoInconsistente('Constante não finita no JSON operacional.')

    try:
        return json.loads(bruto, object_pairs_hook=objeto, parse_constant=constante_invalida)
    except (ValueError, RecursionError) as exc:
        raise DadoInconsistente('JSON operacional inválido.') from exc


def _indicador_ausente(
    identificador: str, item_catalogo: Registro, periodo: dict[str, str], motivo: str,
) -> Registro:
    explicacoes = {
        'SEM_COBERTURA_TERRITORIAL': (
            'Município válido no cadastro IBGE, fora da cobertura desta edição.',
            'Nenhum valor estimado a partir de vizinhos ou médias estaduais.',
        ),
        'PERIODO_NAO_DISPONIVEL': (
            'Não há valor processado para o intervalo solicitado nesta edição.',
            'Sem substituição silenciosa do período solicitado.',
        ),
    }
    metodo, limitacao = explicacoes[motivo]
    return {
        'id': identificador, 'valor': None, 'unidade': item_catalogo['unidade'], 'periodo': periodo,
        'disponibilidade': 'AUSENTE', 'motivo_ausencia': motivo, 'fontes': [],
        'metodo': metodo, 'estacao': None, 'cobertura': None, 'limitacoes': [limitacao],
    }


def _consultar_indicador(
    banco: sqlite3.Connection, edicao: str, municipio: sqlite3.Row,
    identificador: str, periodo: dict[str, str], item_catalogo: Registro,
) -> Registro:
    if not municipio['coberto']:
        return _indicador_ausente(identificador, item_catalogo, periodo, 'SEM_COBERTURA_TERRITORIAL')
    armazenado = banco.execute(
        'SELECT dados FROM indicadores WHERE edicao=? AND municipio=? AND indicador=? AND inicio=? AND fim=?',
        (edicao, municipio['codigo'], identificador, periodo['inicio'], periodo['fim']),
    ).fetchone()
    if armazenado:
        return validar_indicador(
            _carregar_registro(armazenado[0]), identificador, periodo, item_catalogo['unidade'],
        )
    if periodo == item_catalogo['periodo']:
        raise BaseIndisponivel('Indicador padrão ausente da base operacional.')
    return _indicador_ausente(identificador, item_catalogo, periodo, 'PERIODO_NAO_DISPONIVEL')


class Repositorio:
    def __init__(self, caminho: str | Path = BASE_PADRAO):
        self.caminho = Path(caminho).resolve()

    def consultar(
        self, codigo_ibge: str, versao_base: str | None = None,
        consultas: list[Registro] | None = None,
    ) -> Registro:
        """Consulta indexada somente leitura; sem autenticação ou serviço HTTP."""
        if not isinstance(codigo_ibge, str) or not re.fullmatch(r'[0-9]{7}', codigo_ibge):
            raise EntradaInvalida('Código IBGE deve ser texto com sete dígitos.')
        if versao_base is not None and (not isinstance(versao_base, str) or not versao_base):
            raise EntradaInvalida('Edição deve ser texto não vazio.')
        if consultas is not None and (not isinstance(consultas, list) or not consultas):
            raise EntradaInvalida('Consultas deve ser lista não vazia.')
        try:
            with closing(sqlite3.connect(self.caminho.as_uri() + '?mode=ro', uri=True, timeout=1.0)) as banco:
                banco.row_factory = sqlite3.Row
                if banco.execute('PRAGMA user_version').fetchone()[0] != 1:
                    raise BaseIndisponivel('Esquema operacional incompatível.')
                edicao = versao_base
                if edicao is None:
                    ativa = banco.execute("SELECT valor FROM configuracao WHERE chave='edicao_ativa'").fetchone()
                    if ativa is None:
                        raise BaseIndisponivel('Nenhuma edição ativa.')
                    edicao = ativa[0]
                info = banco.execute('SELECT contrato FROM edicoes WHERE versao=?', (edicao,)).fetchone()
                if info is None:
                    if versao_base is None:
                        raise BaseIndisponivel('Edição ativa não encontrada.')
                    raise EdicaoInexistente(edicao)
                if info['contrato'] != '1.0.0':
                    raise BaseIndisponivel('Contrato da base operacional incompatível.')
                municipio = banco.execute(
                    'SELECT * FROM municipios WHERE edicao=? AND codigo=?', (edicao, codigo_ibge),
                ).fetchone()
                if municipio is None:
                    raise MunicipioInexistente(codigo_ibge)
                if (any(not isinstance(municipio[c], str) or not municipio[c] for c in ('municipio', 'uf'))
                        or municipio['abrangencia'] not in ('municipio', 'distrito_federal')
                        or municipio['coberto'] not in (0, 1)):
                    raise BaseIndisponivel('Cadastro municipal inconsistente.')
                catalogo = validar_catalogo({
                    r['indicador']: _carregar_registro(r['dados'])
                    for r in banco.execute('SELECT indicador,dados FROM catalogo WHERE edicao=? ORDER BY indicador', (edicao,))
                })
                solicitadas = consultas if consultas is not None else [{'indicador': ident} for ident in catalogo]
                saida, vistas = [], set()
                for consulta in solicitadas:
                    if (not isinstance(consulta, dict) or set(consulta) - {'indicador', 'periodo'}
                            or not isinstance(consulta.get('indicador'), str) or consulta['indicador'] not in catalogo):
                        raise EntradaInvalida('Consulta ou indicador inválido.')
                    identificador = consulta['indicador']
                    item = catalogo[identificador]
                    periodo = validar_periodo(consulta['periodo']) if 'periodo' in consulta else item['periodo']
                    chave = (identificador, periodo['inicio'], periodo['fim'])
                    if chave in vistas:
                        raise EntradaInvalida('Consulta duplicada.')
                    vistas.add(chave)
                    saida.append(_consultar_indicador(banco, edicao, municipio, identificador, periodo, item))
                coletas = [f['coletado_em'] for r in saida for f in r['fontes']]
                return {
                    'versao_contrato': info['contrato'], 'versao_base': edicao,
                    'consultado_em': datetime.now(timezone.utc).isoformat(),
                    'territorio': {'codigo_ibge': codigo_ibge, **{
                        c: municipio[c] for c in ('municipio', 'uf', 'abrangencia')
                    }},
                    'atualizacao': {'ultima_coleta_em': _ultima_coleta(coletas), 'situacao': 'SEM_FALHA_REGISTRADA'},
                    'indicadores': saida,
                }
        except (sqlite3.Error, DadoInconsistente) as exc:
            raise BaseIndisponivel('Base operacional indisponível ou inconsistente.') from exc
