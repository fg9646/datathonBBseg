"""Chaves de alta entropia por consumidor, sem provedor externo de autenticação."""
from collections import deque
from dataclasses import dataclass, field
import hashlib
import hmac
import ipaddress
import json
import math
import os
from pathlib import Path
import re
from threading import Lock
import time

from .armazenamento import BASE_PADRAO


@dataclass(frozen=True)
class Consumidor:
    nome: str
    sha256: str = field(repr=False)
    permitido: bool = True


@dataclass(frozen=True)
class Configuracao:
    consumidores: tuple[Consumidor, ...] = field(repr=False)
    base: Path = BASE_PADRAO
    limite_por_minuto: int = 60
    permitir_http_local: bool = False

    def __post_init__(self):
        if not self.consumidores:
            raise ValueError('Configure pelo menos um consumidor; não há chave padrão.')
        if type(self.limite_por_minuto) is not int or not 1 <= self.limite_por_minuto <= 60000:
            raise ValueError('Limite por minuto inválido.')
        if type(self.permitir_http_local) is not bool:
            raise ValueError('Configuração de HTTP local inválida.')
        nomes, hashes = set(), set()
        for c in self.consumidores:
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', c.nome) or not re.fullmatch(r'[0-9a-f]{64}', c.sha256) or type(c.permitido) is not bool:
                raise ValueError('Configuração de consumidor inválida.')
            if c.nome in nomes or c.sha256 in hashes:
                raise ValueError('Consumidores precisam de nomes e chaves exclusivos.')
            nomes.add(c.nome)
            hashes.add(c.sha256)

    @classmethod
    def ambiente(cls):
        try:
            raw = json.loads(os.environ.get('TERRITORIO_CONSUMIDORES', '{}'))
            if not isinstance(raw, dict):
                raise ValueError()
            consumidores = []
            for nome, item in raw.items():
                if not isinstance(item, dict) or set(item) - {'sha256', 'permitido'}:
                    raise ValueError()
                consumidores.append(Consumidor(nome, item['sha256'], item.get('permitido', True)))
            local = os.environ.get('TERRITORIO_HTTP_LOCAL', '0')
            if local not in ('0', '1'):
                raise ValueError()
            return cls(tuple(consumidores), Path(os.environ.get('TERRITORIO_BASE', str(BASE_PADRAO))), int(os.environ.get('TERRITORIO_LIMITE_MINUTO', '60')), local == '1')
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError('Configuração inválida: revise TERRITORIO_CONSUMIDORES, base, limite e modo local. Não há credenciais padrão.') from None


def loopback(host):
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def identificar(chave, consumidores):
    if not isinstance(chave, str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,128}', chave):
        return None
    digest = hashlib.sha256(chave.encode('ascii')).hexdigest()
    found = None
    for consumidor in consumidores:
        if hmac.compare_digest(digest, consumidor.sha256):
            found = consumidor
    return found


class LimiteConsumidor:
    """Janela deslizante local; executar uma única instância/worker nesta versão."""
    def __init__(self, quantidade, relogio=time.monotonic):
        self.quantidade = quantidade
        self.relogio = relogio
        self.historico = {}
        self.lock = Lock()

    def consumir(self, nome):
        now = self.relogio()
        with self.lock:
            queue = self.historico.setdefault(nome, deque())
            while queue and queue[0] <= now - 60:
                queue.popleft()
            if len(queue) >= self.quantidade:
                return max(1, math.ceil(queue[0] + 60 - now))
            queue.append(now)
            return None
