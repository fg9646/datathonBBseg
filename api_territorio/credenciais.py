"""Gera chave para entrega segura e hash para configuração do backend."""
import argparse
import hashlib
import json
import re
import secrets


def gerar(consumidor):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', consumidor):
        raise ValueError('Nome de consumidor inválido.')
    chave = secrets.token_urlsafe(32)
    return {'consumidor': consumidor, 'chave': chave, 'configuracao_servidor': {consumidor: {'sha256': hashlib.sha256(chave.encode()).hexdigest(), 'permitido': True}}}


def main():
    parser = argparse.ArgumentParser(description='Não publique a saída: ela contém uma chave secreta nova.')
    parser.add_argument('--consumidor', required=True)
    args = parser.parse_args()
    print(json.dumps(gerar(args.consumidor), ensure_ascii=False))


if __name__ == '__main__':
    main()
