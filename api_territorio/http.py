"""Endpoint HTTP da API Território, sem integrações com motor/Bússola."""
import asyncio
import json
import logging
from typing import Annotated, Any

from fastapi import FastAPI, Request, Security, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.security import APIKeyHeader
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from .armazenamento import (
    Repositorio, EntradaInvalida, MunicipioInexistente, EdicaoInexistente, BaseIndisponivel,
)
from .modelos import Pedido, RespostaConsulta, RespostaErro
from .validadores import MAX_CONSULTAS
from .seguranca import Configuracao, LimiteConsumidor, identificar, loopback

ROTA = '/v1/enriquecimento/consulta'
MAX_CORPO = 16384
TEMPO_CORPO = 3.0
TEMPO_CONSULTA = 2.0
logger = logging.getLogger('territorio')


def erro(status: int, codigo: str, mensagem: str, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        {'erro': {'codigo': codigo, 'mensagem': mensagem}}, status_code=status,
        headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', **(headers or {})},
    )


def _objeto_sem_duplicatas(pares: list[tuple[str, Any]]) -> dict[str, Any]:
    resultado = {}
    for chave, valor in pares:
        if chave in resultado:
            raise ValueError('Campo JSON duplicado.')
        resultado[chave] = valor
    return resultado


class ProtecoesHTTP:
    def __init__(self, app, config):
        self.app, self.config = app, config

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)

        async def seguro(message):
            if message['type'] == 'http.response.start':
                message = dict(message)
                security = {b'cache-control': b'no-store', b'x-content-type-options': b'nosniff'}
                if scope.get('scheme') == 'https':
                    security[b'strict-transport-security'] = b'max-age=31536000'
                message['headers'] = [(k, v) for k, v in message.get('headers', []) if k.lower() not in security] + list(security.items())
            await send(message)

        protected = scope['path'].startswith('/v1/') or scope['path'] == '/ready'
        client = scope.get('client')
        local = self.config.permitir_http_local and client and loopback(client[0])
        if protected and scope.get('scheme') != 'https' and not local:
            return await erro(403, 'HTTPS_OBRIGATORIO', 'Use HTTPS para acessar a API.')(scope, receive, seguro)

        if scope['path'] == ROTA and scope['method'] == 'POST':
            headers = {}
            for k, v in scope['headers']:
                headers.setdefault(k.lower(), []).append(v.decode('latin-1'))
            tipos = headers.get(b'content-type', [])
            tipo_json = len(tipos) == 1 and tipos[0].split(';')[0].strip().lower() == 'application/json'
            sem_compressao = headers.get(b'content-encoding', ['identity']) == ['identity']
            if not tipo_json or not sem_compressao:
                resposta = erro(
                    415, 'TIPO_CONTEUDO_INVALIDO',
                    'Envie JSON sem compressão com Content-Type application/json.',
                )
                return await resposta(scope, receive, seguro)
            lengths = headers.get(b'content-length', [])
            if lengths and (
                len(lengths) != 1 or not lengths[0].isascii()
                or not lengths[0].isdigit() or len(lengths[0]) > 9
            ):
                return await erro(400, 'ENTRADA_INVALIDA', 'Content-Length inválido.')(scope, receive, seguro)
            declared = int(lengths[0]) if lengths else None
            if declared is not None and declared > MAX_CORPO:
                return await erro(413, 'REQUISICAO_MUITO_GRANDE', 'O corpo excede 16 KiB.')(scope, receive, seguro)

            async def ler():
                chunks, total = [], 0
                while True:
                    message = await receive()
                    if message['type'] == 'http.disconnect':
                        raise ConnectionError()
                    chunk = message.get('body', b'')
                    total += len(chunk)
                    if total > MAX_CORPO:
                        raise OverflowError()
                    chunks.append(chunk)
                    if not message.get('more_body', False):
                        return b''.join(chunks)
            try:
                raw = await asyncio.wait_for(ler(), timeout=TEMPO_CORPO)
                if declared is not None and len(raw) != declared:
                    raise ValueError()
                def invalida_constante(value):
                    raise ValueError('Constante JSON inválida.')
                json.loads(raw.decode('utf-8'), object_pairs_hook=_objeto_sem_duplicatas, parse_constant=invalida_constante)
            except OverflowError:
                return await erro(413, 'REQUISICAO_MUITO_GRANDE', 'O corpo excede 16 KiB.')(scope, receive, seguro)
            except asyncio.TimeoutError:
                return await erro(408, 'TEMPO_REQUISICAO_EXCEDIDO', 'Tempo excedido ao receber a requisição.')(scope, receive, seguro)
            except (ValueError, UnicodeError, RecursionError):
                return await erro(400, 'ENTRADA_INVALIDA', 'JSON inválido, ambíguo ou incompleto.')(scope, receive, seguro)
            except ConnectionError:
                return
            sent = False
            original_receive = receive
            async def replay():
                nonlocal sent
                if not sent:
                    sent = True
                    return {'type': 'http.request', 'body': raw, 'more_body': False}
                return await original_receive()
            receive = replay
        return await self.app(scope, receive, seguro)


def criar_app(config: Configuracao | None = None, repositorio: Repositorio | None = None) -> FastAPI:
    config = config if config is not None else Configuracao.ambiente()
    repo = repositorio if repositorio is not None else Repositorio(config.base)
    limite = LimiteConsumidor(config.limite_por_minuto)
    app = FastAPI(
        title='Território — enriquecimento residencial', version='1.0.0',
        docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False,
    )
    app.add_middleware(ProtecoesHTTP, config=config)
    chave_header = APIKeyHeader(name='X-API-Key', auto_error=False)

    async def autenticar(request: Request, chave: Annotated[str | None, Security(chave_header)]) -> str:
        consumidor = identificar(chave, config.consumidores) if len(request.headers.getlist('x-api-key')) == 1 else None
        if consumidor is None:
            raise HTTPException(
                401, detail={'codigo': 'CREDENCIAL_INVALIDA', 'mensagem': 'Credencial ausente ou inválida.'},
                headers={'WWW-Authenticate': 'ApiKey'},
            )
        if not consumidor.permitido:
            raise HTTPException(403, detail={'codigo': 'ACESSO_NEGADO', 'mensagem': 'Consumidor sem autorização.'})
        espera = limite.consumir(consumidor.nome)
        if espera is not None:
            raise HTTPException(
                429, detail={'codigo': 'LIMITE_EXCEDIDO', 'mensagem': 'Limite de consultas excedido.'},
                headers={'Retry-After': str(espera)},
            )
        return consumidor.nome

    @app.exception_handler(RequestValidationError)
    async def validacao(request, exc):
        return erro(400, 'ENTRADA_INVALIDA', 'Verifique os campos, tipos e períodos da consulta.')

    @app.exception_handler(StarletteHTTPException)
    async def http_erro(request, exc):
        if isinstance(exc.detail, dict) and {'codigo', 'mensagem'} <= set(exc.detail):
            return erro(exc.status_code, exc.detail['codigo'], exc.detail['mensagem'], exc.headers)
        codes = {404: ('ROTA_INEXISTENTE', 'Rota inexistente.'), 405: ('METODO_NAO_PERMITIDO', 'Método não permitido.')}
        code, message = codes.get(exc.status_code, ('REQUISICAO_INVALIDA', 'Requisição inválida.'))
        return erro(exc.status_code, code, message, exc.headers)

    @app.exception_handler(Exception)
    async def inesperado(request, exc):
        logger.error('Falha interna na consulta territorial; verifique o serviço.')
        return erro(500, 'ERRO_INTERNO', 'Falha interna do serviço.')

    async def consultar_dados(**kwargs: Any) -> dict[str, Any] | JSONResponse:
        try:
            return await asyncio.wait_for(run_in_threadpool(repo.consultar, **kwargs), timeout=TEMPO_CONSULTA)
        except EntradaInvalida:
            return erro(400, 'ENTRADA_INVALIDA', 'Consulta, indicador ou período inválido.')
        except MunicipioInexistente:
            return erro(404, 'MUNICIPIO_INEXISTENTE', 'Código de município inexistente no cadastro da edição.')
        except EdicaoInexistente:
            return erro(404, 'EDICAO_INEXISTENTE', 'Edição solicitada inexistente.')
        except (BaseIndisponivel, asyncio.TimeoutError):
            return erro(503, 'SERVICO_INDISPONIVEL', 'Base de consulta temporariamente indisponível.', {'Retry-After': '1'})

    descricoes_erro = {
        400: 'Entrada inválida', 401: 'Credencial inválida',
        403: 'Acesso negado ou HTTPS obrigatório', 404: 'Município ou edição inexistente',
        408: 'Tempo de recebimento excedido', 413: 'Corpo excessivo',
        415: 'Content-Type inválido', 429: 'Limite excedido',
        500: 'Falha interna', 503: 'Serviço indisponível',
    }
    respostas_erro = {
        status: {'model': RespostaErro, 'description': descricao}
        for status, descricao in descricoes_erro.items()
    }

    @app.post(ROTA, response_model=RespostaConsulta, responses=respostas_erro)
    async def consulta(payload: Pedido, consumidor: Annotated[str, Security(autenticar)]):
        return await consultar_dados(**payload.model_dump(exclude_unset=True))

    @app.get('/health', include_in_schema=False)
    async def health():
        return {'status': 'ok'}

    @app.get('/ready', include_in_schema=False)
    async def ready(consumidor: Annotated[str, Security(autenticar)]):
        result = await consultar_dados(codigo_ibge='3550308', consultas=[{'indicador': 'clima.chuva_normal'}])
        return result if isinstance(result, JSONResponse) else {'status': 'pronto'}

    return app
