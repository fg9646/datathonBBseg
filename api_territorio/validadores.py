"""Regras do domínio compartilhadas pelo armazenamento e pela interface HTTP.

Somente biblioteca padrão: a preparação e a consulta local não dependem do HTTP.
"""
from datetime import date, datetime, timedelta
import math
import re
from typing import Any
from urllib.parse import urlparse


class EntradaInvalida(ValueError):
    """Consulta incompatível com o contrato."""


class DadoInconsistente(ValueError):
    """Registro operacional incompatível com o contrato da edição."""


MAX_CONSULTAS = 100
MOTIVOS_AUSENCIA = frozenset({
    'FONTE_SEM_VALOR', 'SEM_RECORTE_RESIDENCIAL',
    'SEM_COBERTURA_TERRITORIAL', 'PERIODO_NAO_DISPONIVEL',
})

# IDs e unidades públicos de 1.0.0; a edição fornece os períodos e valores.
UNIDADES_INDICADORES = {
    'clima.chuva_normal': 'mm/ano',
    'clima.dias_chuva_ge50_normal': 'dias/ano',
    'clima.maxima_media_normal': '°C',
    'clima.minima_media_normal': '°C',
    'clima.dias_minima_le10_normal': 'dias/ano',
    'clima.cobertura_chuva': 'fracao',
    'clima.cobertura_rajada': 'fracao',
    'clima.rajada_max_observada': 'km/h',
    'desastres.protocolos_granizo': 'protocolos',
    'desastres.protocolos_vendaval': 'protocolos',
    'desastres.protocolos_alagamento': 'protocolos',
    'desastres.protocolos_inundacao': 'protocolos',
    'desastres.protocolos_enxurrada': 'protocolos',
    'desastres.protocolos_chuva_intensa': 'protocolos',
    'seguranca.roubo_residencial': 'ocorrencias',
    'seguranca.furto_residencial': 'ocorrencias',
    'seguranca.taxa_roubo_residencial': 'ocorrencias/100mil_habitantes',
    'seguranca.taxa_furto_residencial': 'ocorrencias/100mil_habitantes',
}


def validar_periodo(valor: Any) -> dict[str, str]:
    if not isinstance(valor, dict) or set(valor) != {'inicio', 'fim'}:
        raise EntradaInvalida('Período exige inicio e fim.')
    for campo in ('inicio', 'fim'):
        if not isinstance(valor[campo], str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', valor[campo]):
            raise EntradaInvalida('Datas devem usar AAAA-MM-DD.')
        try:
            date.fromisoformat(valor[campo])
        except ValueError as exc:
            raise EntradaInvalida('Data inválida.') from exc
    if valor['inicio'] > valor['fim']:
        raise EntradaInvalida('Início posterior ao fim.')
    return valor


def _objeto(valor: Any, campos: set[str]) -> dict[str, Any]:
    if not isinstance(valor, dict) or set(valor) != campos:
        raise DadoInconsistente('Objeto com estrutura inválida na base operacional.')
    return valor


def _texto(valor: Any) -> None:
    if not isinstance(valor, str) or not valor:
        raise DadoInconsistente('Texto inválido na base operacional.')


def _numero_finito(valor: Any) -> bool:
    if type(valor) not in (int, float):
        return False
    try:
        return math.isfinite(valor)
    except OverflowError:
        return False


def _periodo_armazenado(valor: Any) -> dict[str, str]:
    try:
        return validar_periodo(valor)
    except EntradaInvalida as exc:
        raise DadoInconsistente('Período inválido na base operacional.') from exc


def validar_catalogo(catalogo: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if set(catalogo) != set(UNIDADES_INDICADORES):
        raise DadoInconsistente('Catálogo não contém os 18 IDs do contrato 1.0.0.')
    for identificador, bruto in catalogo.items():
        item = _objeto(bruto, {'id', 'unidade', 'periodo'})
        if item['id'] != identificador or item['unidade'] != UNIDADES_INDICADORES[identificador]:
            raise DadoInconsistente('Identificador ou unidade divergente no catálogo.')
        _periodo_armazenado(item['periodo'])
    return catalogo


def validar_estado_valor(valor: Any, disponibilidade: Any, motivo: Any) -> None:
    if valor is None:
        if disponibilidade != 'AUSENTE' or not isinstance(motivo, str) or motivo not in MOTIVOS_AUSENCIA:
            raise DadoInconsistente('Ausência sem motivo explícito válido.')
    elif not _numero_finito(valor) or disponibilidade != 'DISPONIVEL' or motivo is not None:
        raise DadoInconsistente('Valor ou estado de disponibilidade inválido.')


def _validar_coleta(valor: Any) -> None:
    _texto(valor)
    try:
        if re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', valor):
            date.fromisoformat(valor)
        else:
            instante = datetime.fromisoformat(valor.replace('Z', '+00:00'))
            if instante.utcoffset() != timedelta(0):
                raise ValueError('Instante deve ser UTC.')
    except ValueError as exc:
        raise DadoInconsistente('Data de coleta inválida na base operacional.') from exc


def _validar_fontes(fontes: Any) -> None:
    if not isinstance(fontes, list):
        raise DadoInconsistente('Fontes devem ser lista.')
    for fonte in fontes:
        _objeto(fonte, {'instituicao', 'url', 'coletado_em'})
        _texto(fonte['instituicao'])
        _texto(fonte['url'])
        try:
            url = urlparse(fonte['url'])
            if url.scheme not in ('https', 'http') or not url.hostname:
                raise ValueError('URL inválida.')
        except ValueError as exc:
            raise DadoInconsistente('URL de fonte inválida.') from exc
        _validar_coleta(fonte['coletado_em'])


def _validar_cobertura(cobertura: Any) -> None:
    if cobertura is None:
        return
    _objeto(cobertura, {'numerador', 'denominador', 'proporcao', 'unidade'})
    numerador, denominador = cobertura['numerador'], cobertura['denominador']
    proporcao = cobertura['proporcao']
    if (type(numerador) is not int or type(denominador) is not int
            or not 0 <= numerador <= denominador or denominador <= 0
            or not _numero_finito(proporcao) or not 0 <= proporcao <= 1
            or cobertura['unidade'] != 'dias'
            or not math.isclose(proporcao, numerador / denominador, rel_tol=1e-12, abs_tol=1e-12)):
        raise DadoInconsistente('Cobertura inválida ou incoerente.')


def validar_indicador(
    bruto: Any, identificador: str, periodo: dict[str, str], unidade: str,
) -> dict[str, Any]:
    item = _objeto(bruto, {
        'id', 'valor', 'unidade', 'periodo', 'disponibilidade', 'motivo_ausencia',
        'fontes', 'metodo', 'estacao', 'cobertura', 'limitacoes',
    })
    if item['id'] != identificador or item['unidade'] != unidade:
        raise DadoInconsistente('Identificador ou unidade divergente do registro solicitado.')
    if _periodo_armazenado(item['periodo']) != periodo:
        raise DadoInconsistente('Período divergente do registro solicitado.')
    validar_estado_valor(item['valor'], item['disponibilidade'], item['motivo_ausencia'])
    valor = item['valor']
    if valor is not None:
        if unidade in ('protocolos', 'ocorrencias') and (type(valor) is not int or valor < 0):
            raise DadoInconsistente('Contagem deve ser inteiro não negativo.')
        if unidade == 'fracao' and not 0 <= valor <= 1:
            raise DadoInconsistente('Fração fora do intervalo permitido.')
    _validar_fontes(item['fontes'])
    if valor is not None and not item['fontes']:
        raise DadoInconsistente('Valor disponível sem fonte.')
    _texto(item['metodo'])
    if item['estacao'] is not None:
        _objeto(item['estacao'], {'codigo', 'nome'})
        _texto(item['estacao']['codigo'])
        _texto(item['estacao']['nome'])
    _validar_cobertura(item['cobertura'])
    if (identificador in ('clima.cobertura_chuva', 'clima.cobertura_rajada')
            and valor is not None and item['cobertura'] is not None
            and valor != item['cobertura']['proporcao']):
        raise DadoInconsistente('Valor de cobertura divergente dos metadados.')
    if not isinstance(item['limitacoes'], list) or any(not isinstance(v, str) for v in item['limitacoes']):
        raise DadoInconsistente('Limitações devem ser lista de textos.')
    return item
