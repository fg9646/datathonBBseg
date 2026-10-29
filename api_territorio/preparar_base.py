"""Executar a partir da raiz: python -m api_territorio.preparar_base."""
import argparse
import json
from .armazenamento import preparar_base, EDICAO_PADRAO, BASE_PADRAO, CADASTRO_PADRAO


def main():
    parser = argparse.ArgumentParser(description='Prepara a base local; não inicia API HTTP.')
    parser.add_argument('--edicao', default=EDICAO_PADRAO)
    parser.add_argument('--destino', default=BASE_PADRAO)
    parser.add_argument('--cadastro', default=CADASTRO_PADRAO)
    args = parser.parse_args()
    print(json.dumps(preparar_base(args.edicao, args.destino, args.cadastro), ensure_ascii=False))


if __name__ == '__main__':
    main()
