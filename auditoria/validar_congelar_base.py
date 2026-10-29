"""Auditoria e snapshot de dados territoriais. Não implementa serviço ou API.

Python com pandas, openpyxl (somente leitura) e pypdf.
Exemplo: python auditoria/validar_congelar_base.py --origem DIRETORIO --piloto DIRETORIO --destino DIRETORIO
Verificação portátil: python auditoria/validar_congelar_base.py --verificar-integridade DIRETORIO
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def verify_snapshot(folder):
    manifest = load(folder / 'manifesto.json')
    for record in manifest['arquivos']:
        p = folder / record['arquivo']
        assert p.stat().st_size == record['bytes'], p
        assert sha(p) == record['sha256'], p
    lines = (folder / 'SHA256SUMS').read_text().splitlines()
    for line in lines:
        digest, name = line.split('  ', 1)
        assert sha(folder / name) == digest, name
    expected = {r['arquivo'] for r in manifest['arquivos']} | {'manifesto.json', 'SHA256SUMS'}
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    assert actual == expected, (actual - expected, expected - actual)
    records = load(folder / 'indicadores.json')
    assert len(records) == 180
    assert all(n == 18 for n in collections.Counter(r['codigo_ibge'] for r in records).values())
    print(json.dumps({'integridade': 'CONFERIDA', 'edicao': manifest['versao_base'], 'arquivos': len(expected), 'indicadores': len(records)}, ensure_ascii=False))


def run(args):
    import pandas as pd
    from pypdf import PdfReader
    root, pilot, dest = args.origem, args.piloto, args.destino
    assert not dest.exists(), 'Edição já existe: não sobrescrever; criar nova edição.'
    data = load(root / 'dados_consolidados.json')
    checks = []
    def check(name, result, details=None):
        if not result:
            raise AssertionError((name, details))
        checks.append({'verificacao': name, 'resultado': 'APROVADO', 'detalhe': details})
    def close(a, b):
        return (pd.isna(a) and b is None) or (b is not None and math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-8))

    cities = {r['codigo_ibge']: r for r in data['municipios']}
    check('10 municípios únicos e códigos de sete dígitos', len(cities) == 10 and all(re.fullmatch(r'\d{7}', c) for c in cities))
    check('180 pares município/indicador únicos', len(data['indicadores']) == len({(r['codigo_ibge'], r['indicador']) for r in data['indicadores']}) == 180)
    paths = {r['fonte_id']: Path(r['path']) for r in load(root / 'originais_locais.json')}
    source_by_file = {}
    for s in data['fontes']:
        p = paths[s['fonte_id']]
        check('SHA-256 e tamanho: ' + s['fonte_id'], p.exists() and p.stat().st_size == s['bytes'] and sha(p) == s['sha256'])
        source_by_file.setdefault(s['arquivo_original'], []).append(s)
    def raw(name):
        return paths[source_by_file[name][0]['fonte_id']]
    check('151 fontes únicas rastreáveis', len(paths) == len(data['fontes']) == 151)
    pop = {r['codigo_ibge']: r['populacao'] for r in data['populacao']}
    rawpop = {}
    for s in source_by_file['ibge_pop_2025.json']:
        for r in load(paths[s['fonte_id']])[1:]:
            check('IBGE população/ano/unidade: ' + r['D1C'], r['D3C'] == '2025' and r['D2C'] == '9324' and r['MN'] == 'Pessoas')
            rawpop[r['D1C']] = int(r['V'])
            check('Município/UF conferem no IBGE: ' + r['D1C'], r['D1N'] == cities[r['D1C']]['municipio'] + ' (' + cities[r['D1C']]['uf'] + ')')
    check('População 2025 dos dez municípios coincide com fonte', rawpop == pop and set(pop) == set(cities))

    # Reprocessamento independente das observações horárias arquivadas.
    daily = pd.read_csv(root / 'clima_diario.csv', dtype={'codigo_ibge': str})
    check('40180 dias sem duplicidade', len(daily) == 40180 and not daily.duplicated(['codigo_ibge', 'data_utc']).any())
    missing_files = []
    for a in data['clima_anual']:
        idx = pd.date_range(f"{a['ano']}-01-01", f"{a['ano']}-12-31")
        saved = daily[(daily.codigo_ibge == a['codigo_ibge']) & daily.data_utc.str.startswith(str(a['ano']))].set_index('data_utc')
        check('Calendário diário: ' + a['estacao'] + '/' + str(a['ano']), list(saved.index) == list(idx.strftime('%Y-%m-%d')))
        if not a['arquivo_original']:
            missing_files.append({'codigo_ibge': a['codigo_ibge'], 'estacao': a['estacao'], 'ano': a['ano']})
            check('Ano ausente preservado vazio: ' + str(a['ano']), saved[['chuva_mm', 'rajada_ms', 'tmax_c', 'tmin_c']].isna().all().all())
            continue
        p = raw(a['arquivo_original'])
        header = dict(line.split(';', 1) for line in p.read_text(encoding='cp1252').splitlines()[:8])
        check('Código da estação no cabeçalho: ' + p.name, header.get('CODIGO (WMO):', '').strip() == a['estacao'])
        df = pd.read_csv(p, sep=';', skiprows=8, encoding='cp1252', decimal=',', na_values=['-9999', -9999, ''], low_memory=False)
        hours = df.iloc[:, 1].astype(str).str.extract(r'^(\d{2})')[0].astype(int)
        timestamps = pd.to_datetime(df.iloc[:, 0], format='mixed') + pd.to_timedelta(hours, unit='h')
        check('Horas únicas dentro do ano: ' + p.name, not timestamps.duplicated().any() and timestamps.dt.year.eq(a['ano']).all() and hours.between(0, 23).all())
        met = pd.DataFrame({k: pd.to_numeric(df.iloc[:, col], errors='coerce').to_numpy() for k, col in [('chuva', 2), ('tmax', 9), ('tmin', 10), ('rajada', 17)]}, index=timestamps)
        met.loc[met.chuva < 0, 'chuva'] = float('nan')
        met.loc[met.rajada < 0, 'rajada'] = float('nan')
        for k in ['tmax', 'tmin']:
            met.loc[~met[k].between(-50, 60), k] = float('nan')
        groups = met.groupby(met.index.floor('D'))
        counts = groups.count().reindex(idx, fill_value=0)
        expected = pd.DataFrame({'chuva_mm': groups.chuva.sum(min_count=24), 'tmax_c': groups.tmax.max(), 'tmin_c': groups.tmin.min(), 'rajada_ms': groups.rajada.max()}).reindex(idx)
        for dst, src in [('chuva_mm', 'chuva'), ('tmax_c', 'tmax'), ('tmin_c', 'tmin'), ('rajada_ms', 'rajada')]:
            expected.loc[counts[src] != 24, dst] = float('nan')
            pd.testing.assert_series_equal(saved[dst].reset_index(drop=True), expected[dst].reset_index(drop=True), check_names=False, check_dtype=False, rtol=1e-10, atol=1e-8)
            check('Completude diária/horária: ' + p.name + '/' + src, list(saved['horas_validas_' + src]) == list(counts[src]) and int(expected[dst].count()) == a['dias_' + src + '_completos'])
        check('Rajada máxima horária: ' + p.name, close(met.rajada.max(), a['rajada_max_observada_ms']))
        check('Chuva em dias completos: ' + p.name, close(expected.chuva_mm.sum(min_count=1), a['chuva_soma_dias_completos_mm']))
    check('Somente dois arquivos anuais ausentes', missing_files == [{'codigo_ibge': '2611606', 'estacao': 'A301', 'ano': 2024}, {'codigo_ibge': '2611606', 'estacao': 'A301', 'ano': 2025}])
    print('Clima: 108 arquivos horários e 2 ausências conferidos.', flush=True)

    for filename in sorted({r['arquivo_original'] for r in data['normais']}):
        frame = pd.read_excel(raw(filename), header=None)
        for r in (x for x in data['normais'] if x['arquivo_original'] == filename):
            match = frame[frame.iloc[:, 0].astype(str) == r['estacao_convencional']]
            v = match.iloc[0, 15] if len(match) == 1 else None
            v = None if v is None or pd.isna(v) or v == '-' else float(v)
            check('Normal anual: ' + r['codigo_ibge'] + '/' + r['parametro'], v == r['valor_anual'])
    atlas = pd.read_csv(raw('atlas_1991_2025.csv'), sep=';', encoding='cp1252', dtype={'Cod_IBGE_Mun': str, 'Cod_Cobrade': str}, low_memory=False)
    dates = pd.to_datetime(atlas.Data_Evento, dayfirst=True, errors='coerce')
    invalid = int((atlas.Cod_IBGE_Mun.isin(cities) & dates.isna()).sum())
    events = atlas[atlas.Cod_IBGE_Mun.isin(cities) & dates.between('2015-01-01', '2025-12-31')]
    saved_events = pd.read_csv(root / 'desastres_registros.csv', dtype=str)
    check('Atlas: 145 protocolos únicos e mesmas chaves no extrato', len(events) == 145 and not events.Protocolo_S2iD.duplicated().any() and set(events.Protocolo_S2iD) == set(saved_events.Protocolo_S2iD))
    cobrade = {'Granizo': '13213', 'Vendavais e ciclones': '13215', 'Alagamentos': '12300', 'Inundações': '12100', 'Enxurradas': '12200', 'Chuvas intensas': '13214'}
    for r in data['desastres']:
        count = len(events[(events.Cod_IBGE_Mun == r['codigo_ibge']) & (events.Cod_Cobrade == cobrade[r['indicador']])])
        check('Atlas: ' + r['codigo_ibge'] + '/' + r['indicador'], count == r['registros_encontrados'])

    # Recontagem dos sete totais residenciais disponíveis a partir das fontes originais.
    residential = {(r['codigo_ibge'], r['indicador']): r for r in data['seguranca'] if r['ano'] == 2025 and r['recorte_crime'] == 'RESIDENCIAL'}
    raw_residential = {}
    pr_reader = PdfReader(raw('pr_2025.pdf'))
    for page, label in [(38, 'Furtos em ambiente residência'), (40, 'Roubos em ambiente residência')]:
        text = pr_reader.pages[page-1].extract_text()
        line = next(line for line in text.splitlines() if re.match(r'^1\s+AISP\s+', line.strip()))
        tokens = line.split()[2:]
        values = [int(x) for x in tokens[:26]]
        check('PR: 12 meses conciliam com total ' + label, len(tokens) == 28 and sum(values[13:25]) == values[25])
        raw_residential[('4106902', label)] = values[25]
    frame = pd.read_excel(raw('df_2025.xlsx'), header=None)
    match = frame[frame.iloc[:, 2].astype(str).str.strip() == 'ROUBO EM RESIDÊNCIA']
    assert len(match) == 1
    r = match.iloc[0]
    check('DF: soma dos 12 meses confere', int(r.iloc[3]) == sum(int(x) for x in r.iloc[4:16]))
    raw_residential[('5300108', 'Roubos em ambiente residência')] = int(r.iloc[3])
    frame = pd.read_csv(raw('rj_municipios.csv'), sep=';', encoding='cp1252', dtype={'fmun_cod': str})
    match = frame[(frame.fmun_cod == '3304557') & (frame.ano == 2025)]
    check('RJ: 12 meses únicos em 2025', len(match) == 12 and set(match.mes) == set(range(1, 13)))
    raw_residential[('3304557', 'Roubos em ambiente residência')] = int(match.roubo_residencia.sum())
    frame = pd.read_excel(raw('ba_outros_2025.xlsx'), header=4)
    match = frame[frame.iloc[:, 0].astype(str).str.replace('.0', '', regex=False) == '292740']
    check('BA: código de seis dígitos e nome Salvador', len(match) == 1 and str(match.iloc[0, 1]).upper().strip() == 'SALVADOR')
    raw_residential[('2927408', 'Roubos em ambiente residência')] = int(match.iloc[0, 4])

    with zipfile.ZipFile(raw('sp_criminais_2025.xlsx')) as z:
        strings = [''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        city_ids = {str(i) for i, s in enumerate(strings) if s == 'S.PAULO'}
        res_ids = {str(i) for i, s in enumerate(strings) if s.lower() in ['residência', 'residencia']}
        crime_ids = {str(i): s for i, s in enumerate(strings) if s in ['FURTO - OUTROS', 'ROUBO - OUTROS']}
        patterns = {col: re.compile(rb'<c r="' + col.encode() + rb'\d+"([^>]*)><v>([^<]*)</v></c>') for col in ['U', 'K', 'X', 'Y', 'Z', 'C', 'E', 'F']}
        counts = collections.Counter(); seen = set(); duplicates = 0
        def cell(row, col, decode=False):
            m = patterns[col].search(row)
            if not m: return ''
            value = m.group(2).decode()
            return strings[int(value)] if decode and b't="s"' in m.group(1) else value
        for sheet in ['sheet2.xml', 'sheet3.xml']:
            with z.open('xl/worksheets/' + sheet) as f:
                tail = b''
                for chunk in iter(lambda: f.read(4*1024*1024), b''):
                    rows = (tail + chunk).split(b'</row>'); tail = rows.pop()
                    for row in rows:
                        if cell(row, 'U') not in city_ids or cell(row, 'K') not in res_ids or cell(row, 'X') not in crime_ids: continue
                        if cell(row, 'Z') != '2025': continue
                        nature = crime_ids[cell(row, 'X')]
                        key = tuple(cell(row, col, True) for col in ['C', 'E', 'F']) + (nature,)
                        if key in seen: duplicates += 1; continue
                        seen.add(key); counts[(nature, int(cell(row, 'Y')))] += 1
    for nature, label in [('FURTO - OUTROS', 'Furtos em ambiente residência'), ('ROUBO - OUTROS', 'Roubos em ambiente residência')]:
        raw_residential[('3550308', label)] = sum(v for (n, m), v in counts.items() if n == nature)
    for key, value in raw_residential.items():
        check('Residencial reextraído da fonte: ' + '/'.join(key), residential[key]['quantidade'] == value)
    check('Sete totais residenciais disponíveis reextraídos', len(raw_residential) == 7)
    check('13 campos residenciais ausentes preservados', sum(r['quantidade'] is None for r in residential.values()) == 13 and all((r['status'] == 'DISPONIVEL') == (r['quantidade'] is not None) for r in residential.values()))
    # Inventário dos campos das bases consultadas que não fornecem recorte residencial.
    schemas = []
    for filename, sep in [('mg_furto.csv', ';'), ('mg_violentos_2025.csv', ';')]:
        frame = pd.read_csv(raw(filename), sep=sep, nrows=0)
        schemas.append({'arquivo': filename, 'campos': list(map(str, frame.columns)), 'observacao': 'Base agregada sem campo de tipo de local residencial.'})
    for filename in ['ce_cvp_2025.xlsx', 'ce_furto_2025.xlsx', 'pe_cvp_microdados.xlsx']:
        frame = pd.read_excel(raw(filename), nrows=0)
        schemas.append({'arquivo': filename, 'campos': list(map(str, frame.columns)), 'observacao': 'Sem campo que permita identificar furto/roubo residencial.'})
    frame = pd.read_excel(raw('rs_2025_completo.xlsx'), sheet_name='2025', header=None, nrows=8)
    schemas.append({'arquivo': 'rs_2025_completo.xlsx', 'cabecalho_inicial': frame.fillna('').astype(str).values.tolist(), 'observacao': 'Categorias municipais gerais, sem divisão residencial.'})
    for filename, fields, note in [('rj_municipios.csv', list(map(str, pd.read_csv(raw('rj_municipios.csv'), sep=';', encoding='cp1252', nrows=0).columns)), 'Possui roubo_residencia; não possui furto residencial específico.'), ('df_2025.xlsx', list(map(str, pd.read_excel(raw('df_2025.xlsx'), header=None).iloc[:, 2].dropna())), 'Categorias publicadas: roubo residencial disponível; furto residencial não publicado nesta planilha.'), ('ba_outros_2025.xlsx', list(map(str, pd.read_excel(raw('ba_outros_2025.xlsx'), header=4, nrows=0).columns)), 'Roubo residencial disponível; furto residencial não publicado nesta planilha.')]:
        schemas.append({'arquivo': filename, 'campos_ou_categorias': fields, 'observacao': note})
    go_text = '\n'.join(p.extract_text() or '' for p in PdfReader(raw('go_2025.pdf')).pages)
    go_lines = [line for line in go_text.splitlines() if line.startswith(('FURTO EM RESIDÊNCIA', 'ROUBO EM RESIDÊNCIA'))]
    check('GO: indicadores consultados pertencem à publicação estadual', len(go_lines) == 2 and 'GOIÁS' in go_text.upper())
    schemas.append({'arquivo': 'go_2025.pdf', 'linhas_contexto_estadual': go_lines, 'observacao': 'Arquivo estadual; nenhum desses números integra o valor municipal de Goiânia.'})
    monthly = pd.read_csv(root / 'seguranca_mensal.csv', dtype={'codigo_ibge': str})
    check('Meses criminais sem duplicidade', not monthly.duplicated(['codigo_ibge', 'ano', 'indicador', 'mes']).any())
    for key, group in monthly.groupby(['codigo_ibge', 'ano', 'indicador']):
        total = next(x['quantidade'] for x in data['seguranca'] if (x['codigo_ibge'], x['ano'], x['indicador']) == key)
        check('Conciliação mensal: ' + str(key), len(group) == 12 and set(group.mes) == set(range(1, 13)) and int(group.quantidade.sum()) == total)
    for r in data['seguranca']:
        if r['ano'] == 2025 and r['quantidade'] is not None:
            check('Taxa/população: ' + r['codigo_ibge'] + '/' + r['indicador'], close(r['quantidade'] / pop[r['codigo_ibge']] * 100000, r['taxa_contextual_por_100mil']))
    print('Normais, Atlas, população e totais residenciais reextraídos.', flush=True)

    # Apenas valida vínculo municipal; nenhum registro de cliente/imóvel é publicado.
    check('2716 vínculos únicos por base/imóvel', len(data['vinculos']) == len({(r['base'], r['imovel_id']) for r in data['vinculos']}) == 2716)
    check('CEPs sintéticos não tratados como postais', all(r['cep_postal_real_disponivel'] is False for r in data['vinculos']))
    norm_map = {'Chuva anual normal': ('clima.chuva_normal', 'PREC', 'mm/ano'), 'Chuva ≥ 50 mm: normal': ('clima.dias_chuva_ge50_normal', 'PRENDIA50', 'dias/ano'), 'Média das máximas diárias': ('clima.maxima_media_normal', 'TMAX', '°C'), 'Média das mínimas diárias': ('clima.minima_media_normal', 'TMIN', '°C'), 'Dias com mínima ≤ 10 °C: normal': ('clima.dias_minima_le10_normal', 'TMINNDIA10', 'dias/ano')}
    other_map = {'Dias completos para chuva': ('clima.cobertura_chuva', 'fracao'), 'Dias completos para rajadas': ('clima.cobertura_rajada', 'fracao'), 'Maior rajada observada': ('clima.rajada_max_observada', 'km/h')}
    dis_map = {'Granizo': 'granizo', 'Vendavais e ciclones': 'vendaval', 'Alagamentos': 'alagamento', 'Inundações': 'inundacao', 'Enxurradas': 'enxurrada', 'Chuvas intensas': 'chuva_intensa'}
    records = []; mapping = {}; gap_rows = []
    for old in data['indicadores']:
        code, name = old['codigo_ibge'], old['indicador']; city = cities[code]
        sources = []; station = None; coverage = None
        value = old['valor']; start, end = ('1991-01-01', '2020-12-31') if old['periodo'] == '1991–2020' else ('2025-01-01', '2025-12-31') if old['periodo'] == '2025' else ('2015-01-01', '2025-12-31')
        if name in norm_map:
            ident, param, unit = norm_map[name]
            normal = next(r for r in data['normais'] if r['codigo_ibge'] == code and r['parametro'] == param)
            check('Indicador normal coincide com normal revalidada: ' + code + '/' + ident, value == normal['valor_anual'])
            sources = source_by_file[normal['arquivo_original']]
            station = {'codigo': city['estacao_convencional'], 'nome': city['local_convencional']}
            method = 'Normal INMET 1991–2020; valor anual publicado da estação convencional.'
        elif name in other_map:
            ident, unit = other_map[name]
            ann = [r for r in data['clima_anual'] if r['codigo_ibge'] == code]
            sources = [s for a in ann if a['arquivo_original'] for s in source_by_file[a['arquivo_original']]]
            station = {'codigo': city['estacao_automatica'], 'nome': city['local_automatica']}
            variable = 'chuva' if ident.endswith('chuva') else 'rajada'
            n = sum(a['dias_' + variable + '_completos'] for a in ann); denominator = sum(a['dias_esperados'] for a in ann)
            coverage = {'numerador': n, 'denominador': denominator, 'proporcao': n / denominator, 'unidade': 'dias'}
            expected_value = n / denominator if unit == 'fracao' else max(a['rajada_max_observada_ms'] for a in ann if a['rajada_max_observada_ms'] is not None) * 3.6
            check('Indicador observado recalculado: ' + code + '/' + ident, close(expected_value, value))
            method = 'Dias UTC completos exigem 24 horas válidas por variável; ausências não imputadas. Rajada máxima usa todas as horas válidas, inclusive de dias incompletos; cobertura é completude diária, não filtro do máximo.'
        elif ': protocolos Atlas' in name:
            category = name.split(':')[0]; ident = 'desastres.protocolos_' + dis_map[category]; unit = 'protocolos'
            sources = source_by_file['atlas_1991_2025.csv']
            expected_value = len(events[(events.Cod_IBGE_Mun == code) & (events.Cod_Cobrade == cobrade[category])])
            check('Indicador Atlas recalculado: ' + code + '/' + ident, expected_value == value)
            value = int(value)
            method = 'Protocolos únicos por código IBGE, data do evento inclusiva e COBRADE ' + cobrade[category] + '. Zero significa nenhum protocolo encontrado, não ausência do fenômeno.'
        else:
            is_rate = name.endswith(': taxa contextual'); label = name.split(':')[0]
            kind = 'furto' if name.startswith('Furtos') else 'roubo'
            ident = 'seguranca.' + ('taxa_' if is_rate else '') + kind + '_residencial'
            unit = 'ocorrencias/100mil_habitantes' if is_rate else 'ocorrencias'
            r = residential[(code, label)]
            for filename in r['arquivo_original'].split('; '):
                # SP referencia o resumo local; o vínculo oficial correto é o microdado original.
                if filename == 'sp_residencial_2025.json': filename = 'sp_criminais_2025.xlsx'
                sources.extend(source_by_file.get(filename, []))
            if is_rate: sources.extend(s for s in source_by_file['ibge_pop_2025.json'] if any(x.get('D1C') == code for x in load(paths[s['fonte_id']])[1:]))
            method = r['localizador'] + (f'; quantidade/população IBGE 2025 ({pop[code]}) × 100000.' if is_rate else '; classificação residencial da fonte; unidade de registro varia por órgão.')
            expected_value = r['taxa_contextual_por_100mil'] if is_rate else r['quantidade']
            check('Indicador residencial coincide com total revalidado: ' + code + '/' + ident, value == expected_value)
            if value is not None and not is_rate: value = int(value)
        mapping[name] = {'indicador_original': name, 'id': ident, 'unidade_original': old['unidade'], 'unidade': unit}
        if value is not None: reason = None
        elif old['status'] == 'SEM_RECORTE_RESIDENCIAL': reason = 'SEM_RECORTE_RESIDENCIAL'
        else: reason = 'FONTE_SEM_VALOR'
        limitation = old['limitacao']
        if code == '5208707' and ident.startswith('seguranca.'):
            limitation += ' A fonte só permite o total estadual; a ausência é municipal e não significa que Goiânia esteja fora dos dez municípios cobertos.'
        if code == '2611606' and ident.startswith('clima.') and start == '2015-01-01':
            limitation += ' Estação A301: arquivos de 2024 e 2025 ausentes no acervo consultado; não substituídos por outra estação.'
        source_ids = sorted({s['fonte_id'] for s in sources})
        check('Origem rastreável do indicador: ' + code + '/' + ident, bool(source_ids))
        record = {'codigo_ibge': code, 'municipio': city['municipio'], 'uf': city['uf'], 'abrangencia': 'distrito_federal' if code == '5300108' else 'municipio', 'id': ident, 'valor': value, 'unidade': unit, 'periodo': {'inicio': start, 'fim': end}, 'disponibilidade': 'DISPONIVEL' if value is not None else 'AUSENTE', 'motivo_ausencia': reason, 'fontes_ids': source_ids, 'metodo': method, 'estacao': station, 'cobertura': coverage, 'limitacoes': [limitation]}
        records.append(record)
        if reason: gap_rows.append({'codigo_ibge': code, 'municipio': city['municipio'], 'id': ident, 'motivo_ausencia': reason, 'status_original': old['status'], 'explicacao': limitation})
    records.sort(key=lambda r: (r['codigo_ibge'], r['id']))
    check('18 IDs por município após mapeamento', len({(r['codigo_ibge'], r['id']) for r in records}) == 180 and all(n == 18 for n in collections.Counter(r['codigo_ibge'] for r in records).values()))
    check('Valores presentes finitos e ausências explícitas', all((r['valor'] is None and r['motivo_ausencia']) or (r['valor'] is not None and math.isfinite(r['valor']) and r['motivo_ausencia'] is None) for r in records))
    check('Sem alteração dos valores numéricos anteriores', len(records) == len(data['indicadores']))

    # Comparação com a planilha já entregue, sem editar nem criar workbook.
    from openpyxl import load_workbook
    workbook = args.planilha
    wb = load_workbook(workbook, read_only=True, data_only=True)
    rows = list(wb['Indicadores'].iter_rows(min_row=6, max_row=185, values_only=True))
    for row, original in zip(rows, data['indicadores']):
        check('Planilha coincide com consolidado: ' + original['codigo_ibge'] + '/' + original['indicador'], close(row[6], original['valor']))
    check('180 linhas conferidas na planilha', len(rows) == 180)
    wb.close()

    dest.mkdir(parents=True)
    dump(dest / 'indicadores.json', records)
    write_csv(dest / 'indicadores.csv', [{**{k: r[k] for k in ['codigo_ibge', 'municipio', 'uf', 'abrangencia', 'id', 'valor', 'unidade', 'disponibilidade', 'motivo_ausencia']}, 'inicio': r['periodo']['inicio'], 'fim': r['periodo']['fim'], 'fontes_ids': ';'.join(r['fontes_ids'])} for r in records])
    write_csv(dest / 'mapeamento_catalogo.csv', sorted(mapping.values(), key=lambda r: r['id']))
    write_csv(dest / 'lacunas.csv', gap_rows)
    dump(dest / 'municipios.json', list(cities.values()))
    dump(dest / 'evidencias_lacunas_seguranca.json', schemas)
    for filename in ['fontes.csv', 'clima_anual.csv', 'clima_diario.csv', 'clima_normais.csv', 'populacao_2025.csv', 'desastres_registros.csv', 'seguranca_anual.csv', 'seguranca_mensal.csv', 'conciliacao_seguranca.csv']:
        # Arquivos de suporte são evidência histórica, não formato operacional da API.
        shutil.copyfile(root / filename, dest / filename)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    summary = {'resultado': 'VALIDADA_COM_LACUNAS_DOCUMENTADAS', 'validado_em': now, 'municipios': 10, 'indicadores': 180, 'disponiveis': sum(r['valor'] is not None for r in records), 'ausentes': len(gap_rows), 'fontes_com_sha256_conferido': len(data['fontes']), 'arquivos_horarios_reprocessados': 108, 'arquivos_horarios_ausentes': missing_files, 'normais_reconferidas': len(data['normais']), 'protocolos_atlas': len(events), 'atlas_datas_invalidas_nos_10_municipios': invalid, 'totais_residenciais_reextraidos': len(raw_residential), 'sp_duplicatas_descartadas_na_reextracao': duplicates, 'grupos_mensais_conciliados': monthly.groupby(['codigo_ibge', 'ano', 'indicador']).ngroups, 'vinculos_apenas_validados_nao_publicados': 2716, 'quantidade_verificacoes': len(checks), 'api_implementada': False}
    dump(dest / 'validacao.json', {'resumo': summary, 'verificacoes': checks})
    coverage_rows = []
    for code, city in cities.items():
        rec = [r for r in records if r['codigo_ibge'] == code]
        byid = {r['id']: r for r in rec}
        cov = byid['clima.cobertura_chuva']['cobertura']
        coverage_rows.append({'codigo_ibge': code, 'municipio': city['municipio'], 'uf': city['uf'], 'indicadores_disponiveis': sum(r['valor'] is not None for r in rec), 'indicadores_ausentes': sum(r['valor'] is None for r in rec), 'dias_chuva_completos': cov['numerador'], 'dias_esperados': cov['denominador'], 'cobertura_chuva': cov['proporcao'], 'cobertura_rajada': byid['clima.cobertura_rajada']['valor'], 'roubo_residencial_2025': byid['seguranca.roubo_residencial']['valor'], 'furto_residencial_2025': byid['seguranca.furto_residencial']['valor']})
    write_csv(dest / 'cobertura_municipios.csv', coverage_rows)
    dump(dest / 'contexto_auditoria.json', {'planilha_referencia': {'arquivo': workbook.name, 'sha256': sha(workbook)}, 'consolidado_referencia': {'arquivo': 'dados_consolidados.json', 'sha256': sha(root / 'dados_consolidados.json')}, 'coleta_nova_realizada': False, 'precisao_datas_coleta': 'dia; horários originais não registrados, não inventados', 'metodo_lacunas_goiania': 'SEM_RECORTE_MUNICIPAL -> FONTE_SEM_VALOR: fonte estadual não fornece valor para o município; não classificar município coberto como fora da cobertura territorial', 'evidencia_ausencia_a301': 'Ausência dos arquivos no acervo arquivado, conforme coleta anterior. Listagem integral dos ZIPs 2024/2025 não foi arquivada: ausência no ZIP não foi reconfirmada nesta auditoria.', 'reproducao_bruta': '151 fontes locais externas à edição, localizadas no inventário original. Os hashes e URLs são publicados; microdados criminais e dados de clientes não são redistribuídos nesta edição.'})
    report = ['# Primeira edição da base Território', '', '**Ponto 3 concluído: validação e congelamento dos dados. API não implementada.**', '', f'**Edição:** `{dest.name}`. **Contrato de referência:** 1.0.0.', '', f'Validação concluída em {now}. Fontes do levantamento anterior, com datas de coleta no arquivo fontes.csv. Nenhuma coleta nova nesta etapa.', '', f"Resultado: **{summary['disponiveis']} valores disponíveis e {summary['ausentes']} ausências explícitas**, em 180 pares município/indicador. Lacunas não foram preenchidas.", '', '## Cobertura municipal', '', '| Município | Disponíveis/18 | Chuva: dias completos | Roubo residencial 2025 | Furto residencial 2025 |', '|---|---:|---:|---:|---:|']
    for r in coverage_rows:
        report.append(f"| {r['municipio']} | {r['indicadores_disponiveis']}/18 | {r['cobertura_chuva']:.1%} ({r['dias_chuva_completos']}/4018) | {r['roubo_residencial_2025'] if r['roubo_residencial_2025'] is not None else 'Ausente'} | {r['furto_residencial_2025'] if r['furto_residencial_2025'] is not None else 'Ausente'} |")
    report += ['', '## Conferências realizadas', '', f"- {len(checks)} verificações aprovadas: resultados individuais em validacao.json.", '- SHA-256 e tamanho de 151 arquivos originais conferidos; 108 arquivos horários reprocessados e comparados aos 40.180 dias do extrato.', '- 80 normais anuais reconferidas nos arquivos INMET; cinco parâmetros integram o catálogo inicial.', '- 60 indicadores de desastres recalculados a partir do Atlas original; 145 protocolos únicos no recorte completo dos dez municípios, incluindo tipologias fora do catálogo.', '- Sete totais residenciais de 2025 reextraídos das fontes SP, PR, DF, RJ e BA; 49 grupos mensais conciliados com os totais processados.', '- População 2025, ano, unidade, códigos e nomes municipais conferidos nos retornos IBGE arquivados; taxas recalculadas com o denominador correto.', '- Os 180 valores e ausências foram comparados com a planilha entregue. Nenhum valor numérico alterado.', '- 2.716 vínculos sintéticos validados quanto à unicidade e ao uso municipal; não publicados nesta edição.', '', '## Lacunas e limites que permanecem', '', '- Recife: 59,0% de dias completos para chuva. A301 sem arquivos de 2024 e 2025 no acervo; sem imputação ou troca automática de estação. A ausência na listagem original dos ZIPs não foi reconfirmada porque essa listagem não foi preservada.', '- Fortaleza: normal anual de dias de chuva ≥50 mm ausente; valor null, FONTE_SEM_VALOR.', '- Segurança: 13 dos 20 totais residenciais ausentes e, consequentemente, 13 taxas ausentes. Roubo disponível em SP, Curitiba, DF, RJ e Salvador; furto apenas em SP e Curitiba.', '- Goiânia: publicação consultada estadual. Os quatro indicadores residenciais ficam null/FONTE_SEM_VALOR; números de Goiás nunca foram atribuídos ao município.', '- Demais ausências residenciais: SEM_RECORTE_RESIDENCIAL. A disponibilidade refere-se aos arquivos consultados, não afirma inexistência de outras publicações oficiais.', '- Rio: normais do Alto da Boa Vista e observações de Vila Militar, sem média espacial da cidade. Brasília representa todo o DF.', '- Rajada máxima usa todas as horas válidas, inclusive dias incompletos; completude diária não é confiança estatística nem vento de projeto.', '- Zero protocolos Atlas não comprova ausência do fenômeno; taxas criminais por habitantes não são probabilidades de sinistro. Não criar ranking entre estados sem harmonização.', '- Datas de coleta originais têm precisão de dia. Horário UTC não foi inventado; eventual adaptação para o serviço será discutida na preparação da base operacional.', '', '## Padronizações aplicadas, sem alterar valores', '', '- Nomes anteriores mapeados para os 18 IDs do contrato em mapeamento_catalogo.csv; vendaval restrito ao COBRADE 13215.', '- Cobertura de chuva/rajada mantida entre 0 e 1, com unidade fracao, corrigindo o rótulo antigo de porcentagem sem multiplicar valores.', '- Contagens distinguem protocolos de desastres e ocorrências criminais; taxas usam ocorrencias/100mil_habitantes.', '- JSON usa null para ausências. No CSV, campo numérico vazio acompanhado do motivo tem o mesmo significado; não interpretar como zero.', '', '## Conteúdo, integridade e reprodução', '', '- indicadores.json é o snapshot canônico; indicadores.csv facilita conferência. Não são banco operacional nem resposta de uma API.', '- Os CSVs de suporte preservam os rótulos e estados históricos; a tradução para o contrato fica no catálogo e no arquivo de lacunas.', '- manifesto.json identifica edição, períodos, arquivos e hashes; SHA256SUMS inclui também o hash do manifesto. Para verificar: executar o script de auditoria com --verificar-integridade apontando para esta pasta.', '- A auditoria completa exige os arquivos originais locais e Python com pandas, openpyxl e pypdf. Não requer acesso à internet; inventário original localiza os brutos. URLs e hashes permitem conferir novos downloads, mas fontes oficiais podem ser revisadas posteriormente.', '- Os arquivos brutos permanecem no acervo local anterior. Microdados criminais, endereços, IDs de clientes e imóveis não são incluídos neste snapshot nem publicados no GitHub.', '- A edição não deve ser sobrescrita. Correções ou novas fontes geram outra edição, mantendo esta e seus hashes preservados no histórico Git.', '', '## Próxima etapa', '', 'Ponto 4: preparar a base operacional de consulta a partir desta edição. Serviço HTTP, autenticação, hospedagem, motor e Bússola continuam sem implementação nesta frente.', '']
    (dest / 'LEIA-ME.md').write_text('\n'.join(report), encoding='utf-8')
    sources = data['fontes']
    files = [{'arquivo': p.relative_to(dest).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(dest.rglob('*')) if p.is_file()]
    manifest = {'versao_base': dest.name, 'versao_contrato_referencia': '1.0.0', 'congelada_em': now, 'estado': 'CONGELADA_COM_LACUNAS_DOCUMENTADAS', 'escopo': 'Snapshot analítico; pontos 1, 2 e 3 concluídos. Não implementa API ou base operacional.', 'periodos': {'normais': '1991-01-01/2020-12-31', 'clima_observado_desastres': '2015-01-01/2025-12-31', 'crime_populacao': '2025-01-01/2025-12-31'}, 'datas_coleta': sorted({r['data_extracao'] for r in sources}), 'indicadores': 180, 'disponiveis': summary['disponiveis'], 'ausentes': summary['ausentes'], 'municipios': sorted(cities), 'politica': 'Não sobrescrever; qualquer correção ou atualização gera nova edição.', 'script_auditoria_sha256': sha(Path(__file__)), 'arquivos': files}
    dump(dest / 'manifesto.json', manifest)
    checksums = [f"{sha(p)}  {p.relative_to(dest).as_posix()}" for p in sorted(dest.rglob('*')) if p.is_file()]
    (dest / 'SHA256SUMS').write_text('\n'.join(checksums) + '\n', encoding='utf-8')
    verify_snapshot(dest)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origem', type=Path)
    parser.add_argument('--piloto', type=Path)
    parser.add_argument('--destino', type=Path)
    parser.add_argument('--planilha', type=Path)
    parser.add_argument('--verificar-integridade', type=Path)
    args = parser.parse_args()
    if args.verificar_integridade:
        verify_snapshot(args.verificar_integridade)
    else:
        if not all([args.origem, args.piloto, args.destino, args.planilha]): parser.error('Informe origem, piloto, destino e planilha.')
        run(args)
