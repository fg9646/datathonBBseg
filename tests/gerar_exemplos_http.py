"""Gera exemplos pela aplicação real, com chave temporária que não é serializada."""
import hashlib
import json
import secrets
from pathlib import Path

from fastapi.testclient import TestClient
from api_territorio.armazenamento import Repositorio, RAIZ
from api_territorio.http import criar_app, ROTA
from api_territorio.seguranca import Configuracao, Consumidor


def main():
    key = secrets.token_urlsafe(32)
    app = criar_app(config=Configuracao((Consumidor('exemplos', hashlib.sha256(key.encode()).hexdigest()),)))
    folder = RAIZ / 'api_territorio/exemplos'
    folder.mkdir(exist_ok=True)
    cases = {
        'dados_disponiveis': {'codigo_ibge': '3550308'},
        'dados_com_lacunas': {'codigo_ibge': '2611606', 'consultas': [{'indicador': 'clima.cobertura_chuva'}, {'indicador': 'seguranca.furto_residencial'}]},
        'sem_cobertura': {'codigo_ibge': '3509502'},
        'credencial_ausente': {'codigo_ibge': '3550308'},
    }
    with TestClient(app, base_url='https://testserver') as client:
        for name, body in cases.items():
            missing = name == 'credencial_ausente'
            response = client.post(ROTA, json=body, headers={} if missing else {'X-API-Key': key})
            expected = 401 if missing else 200
            if response.status_code != expected:
                raise RuntimeError('Exemplo retornou estado inesperado: ' + name)
            headers = {'Content-Type': 'application/json'}
            if not missing:
                headers['X-API-Key'] = '<chave-do-consumidor>'
            result = {'observacao': 'Gerado localmente pela implementação; não representa publicação na internet.', 'requisicao': {'metodo': 'POST', 'caminho': ROTA, 'headers': headers, 'corpo': body}, 'http_status': response.status_code, 'resposta': response.json()}
            output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
            if key in output:
                raise RuntimeError('Credencial temporária não pode constar do exemplo.')
            (folder / (name + '.json')).write_text(output, encoding='utf-8')
    schema = app.openapi()
    # A validação do contrato retorna 400, não o 422 automático do framework.
    schema['paths'][ROTA]['post']['responses'].pop('422', None)
    (RAIZ / 'api_territorio/openapi.json').write_text(json.dumps(schema, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Quatro exemplos e esquema OpenAPI gerados, sem credenciais reais.')


if __name__ == '__main__':
    main()
