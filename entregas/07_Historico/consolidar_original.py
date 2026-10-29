"""Consolida Seguro Residencial em uma linha por cliente–imóvel.

Requisitos: Python 3.10 ou superior; somente bibliotecas padrão.
Coloque os dois ZIPs originais em uma pasta e execute, por exemplo:
    python consolidar_seguro_residencial.py --entrada . --saida resultados

As fontes nunca são extraídas nem alteradas. As etapas estão numeradas abaixo.
As validações fazem parte do processo e interrompem uma entrada inconsistente.
"""
from pathlib import Path
from collections import defaultdict, Counter
from decimal import Decimal
from datetime import datetime, timezone
import csv
import io
import json
import hashlib
import re
import argparse

# 1. Definir entradas, saída e versão do contrato de colunas.
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--entrada", type=Path, default=Path("."), help="Pasta com os dois ZIPs originais")
parser.add_argument("--saida", type=Path, default=Path("resultados"), help="Pasta dos CSVs consolidados e do guia")
parser.add_argument("--data-consolidacao", help="Data ISO-8601 opcional, para reprodução da mesma execução")
parser.add_argument("--intermediarios", type=Path, help="Opcional: pasta para JSONs de trabalho e validação")
args = parser.parse_args()
INPUT = args.entrada.resolve()
OUT = args.saida.resolve()
WORK = args.intermediarios.resolve() if args.intermediarios else None
OUT.mkdir(parents=True, exist_ok=True)
if WORK:
    WORK.mkdir(parents=True, exist_ok=True)
SCHEMA_VERSION = "0.1.0"
SCRIPT_VERSION = "0.1.0"
GROUPS = ["Identificação", "Dados observados", "Dados derivados", "Estimativas",
          "Respostas confirmadas", "Controle", "Resultado do motor"]
FILES = ["clientes.csv", "enderecos_imoveis.csv", "sinais_imobiliarios.csv",
         "territorio.csv", "bens_compras.csv"]
DATASETS = [
    ("Seguro_Residencial_Desenvolvimento.zip", "Seguro_Residencial_Desenvolvimento_Consolidado.csv"),
    ("Seguro_Residencial_Teste_Comum.zip", "Seguro_Residencial_Teste_Comum_Consolidado.csv"),
]
NUMERIC_FIELDS = {
    "idade", "renda_mensal", "indice_maturidade_digital", "frequencia_acesso_app_90d",
    "quantidade_dependentes", "qtd_produtos_seguridade", "area_cadastrada_m2",
    "valor_aluguel_recorrente", "valor_medio_credito_recorrente",
    "quantidade_creditos_recorrentes_12m", "parcela_financiamento_imobiliario",
    "pagamento_condominio_mensal", "pagamento_iptu_anual", "energia_media_mensal_6m",
    "agua_media_mensal_6m", "internet_mensal", "compras_moveis_36m",
    "compras_eletrodomesticos_36m", "compras_eletronicos_36m",
    "gastos_material_construcao_24m", "gastos_vidracaria_24m",
    "latitude_aproximada", "longitude_aproximada", "valor_cadastrado",
    "probabilidade_bem_no_imovel_referencia", "valor_bem_ponderado_referencia",
}
import zipfile

def check(condition, message):
    """Registrar uma falha antes de interromper, sem corrigir a fonte silenciosamente."""
    if not condition:
        error = {"status": "ERRO", "versao_script": SCRIPT_VERSION,
                 "mensagem": str(message), "saidas_finais_aprovadas": False}
        OUT.joinpath("Relatorio_Qualidade_ERRO.json").write_text(json.dumps(error, ensure_ascii=False, indent=2), encoding="utf-8")
        raise ValueError(str(message))

# 2. Ler os CSVs diretamente dos ZIPs, respeitando vírgulas e aspas.
def read_zip(filename):
    path = INPUT / filename
    with zipfile.ZipFile(path) as archive:
        raw = {}
        headers = {}
        for name in archive.namelist():
            if name.endswith(".csv"):
                reader = csv.DictReader(io.StringIO(archive.read(name).decode("utf-8-sig")))
                headers[name] = reader.fieldnames
                raw[name] = list(reader)
                check(all(None not in r and all(v is not None for v in r.values()) for r in raw[name]), name)
                for line, row in enumerate(raw[name], 2):
                    for field in NUMERIC_FIELDS.intersection(headers[name]):
                        value = row[field]
                        check(value == "" or re.fullmatch(r"-?\d+(?:\.\d+)?", value) is not None,
                              (filename, name, line, field, "Formato numérico inesperado; usar ponto decimal"))
                        if value != "":
                            check(Decimal(value).is_finite(), (filename, name, line, field, "Número não finito"))
        return {
            "input": filename, "raw": raw, "headers": headers,
            "zip_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

def unique_index(rows, fields, name):
    result = {}
    for row in rows:
        key = tuple(row[f] for f in fields)
        check(key not in result, ("Chave duplicada", name, key))
        check(all(key), ("Chave vazia", name, key))
        result[key] = row
    return result

# 3. Validar cardinalidade e integridade antes de fazer qualquer junção.
# Nunca unir sinais ou bens apenas por cliente_id: um cliente pode ter dois imóveis.
sources = [read_zip(filename) for filename, _ in DATASETS]
max_bens = 0
types = set()
for source in sources:
    raw = source["raw"]
    clients = unique_index(raw["clientes.csv"], ["cliente_id"], "clientes")
    props = unique_index(raw["enderecos_imoveis.csv"], ["cliente_id", "imovel_id"], "imóveis")
    unique_index(raw["enderecos_imoveis.csv"], ["imovel_id"], "ID imóvel")
    signals = unique_index(raw["sinais_imobiliarios.csv"], ["cliente_id", "imovel_id"], "sinais")
    territories = unique_index(raw["territorio.csv"], ["territorio_id"], "territórios")
    template = unique_index(raw["template_resultado_times.csv"], ["cliente_id", "imovel_id"], "template")
    unique_index(raw["bens_compras.csv"], ["bem_id"], "bens")
    # A base de imóveis sempre é preservada. Vínculos ausentes viram pendências.
    source["association_counts"] = {
        "imoveis_sem_cliente": sum((p["cliente_id"],) not in clients for p in props.values()),
        "imoveis_sem_sinais": len(set(props) - set(signals)),
        "imoveis_sem_territorio": sum((p["territorio_id"],) not in territories for p in props.values()),
        "clientes_sem_imovel": len(set(clients) - {(p["cliente_id"],) for p in props.values()}),
        "sinais_sem_imovel": len(set(signals) - set(props)),
    }
    goods = defaultdict(list)
    orphan_goods = []
    for good in raw["bens_compras.csv"]:
        key = good["cliente_id"], good["imovel_id_referencia"]
        if key not in props:
            orphan_goods.append(good)
            continue  # Preservado no detalhe e no relatório; nunca distribuído entre imóveis.
        goods[key].append(good)
        types.add(good["tipo_bem"])
    for key in goods:
        goods[key].sort(key=lambda r: r["bem_id"])
        max_bens = max(max_bens, len(goods[key]))
    source["territory_conflicts"] = []
    for key, p in props.items():
        t = territories.get((p["territorio_id"],), {})
        for field in ["codigo_ibge_municipio", "municipio_real", "uf_real", "cep_agregado"]:
            if t and p[field] != t[field]:
                source["territory_conflicts"].append({"cliente_id": key[0], "imovel_id": key[1],
                    "campo": field, "imovel": p[field], "territorio": t[field],
                    "politica": "PRESERVAR_VALOR_ENDERECOS_IMOVEIS_E_REGISTRAR_DIVERGENCIA"})
    source["association_counts"]["bens_sem_vinculo_valido"] = len(orphan_goods)
    source.update(clients=clients, props=props, signals=signals,
                  territories=territories, goods=goods, orphan_goods=orphan_goods)

for name in sources[0]["headers"]:
    check(sources[0]["headers"][name] == sources[1]["headers"][name], name)

# 4. Construir um schema único para as duas bases.
# Dados observados, cálculos, estimativas, respostas e resultados ficam separados.
columns = []
def column(name, group, origin="", rule="", numeric=False):
    check(name not in {c["name"] for c in columns}, name)
    columns.append({"name": name, "group": group, "origin": origin, "rule": rule,
                    "numeric": numeric})
    return name

for name in ["ID", "cliente_id", "imovel_id", "territorio_id"]:
    column(name, "Identificação",
           "enderecos_imoveis.csv",
           "cliente_id + '__' + imovel_id" if name == "ID" else "Identificador original, preservado como texto")

mappings = {}
for table in FILES[:-1]:
    for field in sources[0]["headers"][table]:
        if field in ["cliente_id", "imovel_id", "territorio_id"]:
            continue
        if table == "territorio.csv" and field in ["codigo_ibge_municipio", "municipio_real", "uf_real", "cep_agregado"]:
            continue  # Mesmo valor cadastral, validado nas duas fontes.
        if table == "clientes.csv" and field == "renda_mensal":
            column("obs_renda_mensal_informada", "Dados observados",
                   "clientes.csv.renda_mensal", "Somente quando origem_renda = INFORMADA", True)
            column("est_renda_mensal_presumida", "Estimativas",
                   "clientes.csv.renda_mensal", "Somente quando origem_renda = PRESUMIDA_COM_BASE_EM_MOVIMENTACAO", True)
            continue
        group, prefix = "Dados observados", "obs_"
        if field in ["origem_renda", "confianca_renda", "origem_area", "confianca_area",
                     "chave_enriquecimento_publico", "observacao_privacidade", "orientacao_enriquecimento"]:
            group, prefix = "Controle", "ctl_"
        elif field == "indice_maturidade_digital":
            group, prefix = "Dados derivados", "der_"
        elif field in ["latitude_aproximada", "longitude_aproximada"]:
            group, prefix = "Estimativas", "est_"
        name = column(prefix + field, group, table + "." + field,
                      "Valor original; sem recálculo", field in NUMERIC_FIELDS)
        mappings[(table, field)] = name

good_mappings = {}
for slot in range(1, max_bens + 1):
    for field in sources[0]["headers"]["bens_compras.csv"]:
        if field in ["cliente_id", "imovel_id_referencia"]:
            continue
        group, prefix = "Dados observados", "obs_"
        if field in ["probabilidade_bem_no_imovel_referencia", "valor_bem_ponderado_referencia"]:
            group, prefix = "Estimativas", "est_"
        elif field == "nivel_confianca_vinculo":
            group, prefix = "Controle", "ctl_"
        suffix = "id" if field == "bem_id" else field
        name = column(f"{prefix}bem_{slot}_{suffix}", group, "bens_compras.csv." + field,
                      f"{slot}º bem do par, em ordem de bem_id; vazio quando não existe esse bem",
                      field in NUMERIC_FIELDS)
        good_mappings[(slot, field)] = name

column("der_quantidade_bens_referencia", "Dados derivados", "bens_compras.csv",
       "Contagem por cliente_id + imovel_id_referencia", True)
column("der_valor_bens_cadastrado_total_referencia", "Dados derivados", "bens_compras.csv.valor_cadastrado",
       "Soma por cliente_id + imovel_id_referencia; não comprova presença física", True)
column("est_valor_bens_ponderado_total_referencia", "Estimativas", "bens_compras.csv.valor_bem_ponderado_referencia",
       "Soma dos valores ponderados já fornecidos; não é limite inferior nem faixa de valor", True)
for kind in sorted(types):
    slug = kind.lower()
    column(f"der_quantidade_bens_{slug}_referencia", "Dados derivados", "bens_compras.csv",
           "Contagem do tipo por cliente–imóvel", True)
    column(f"der_valor_bens_{slug}_cadastrado_referencia", "Dados derivados", "bens_compras.csv",
           "Soma de valor_cadastrado do tipo por cliente–imóvel", True)
    column(f"est_valor_bens_{slug}_ponderado_referencia", "Estimativas", "bens_compras.csv.valor_bem_ponderado_referencia",
           "Soma dos valores ponderados já fornecidos, do tipo e do par; sem ponderar novamente", True)
for confidence in ["ALTA", "MEDIA", "BAIXA"]:
    column("der_quantidade_bens_confianca_" + confidence.lower(), "Dados derivados", "bens_compras.csv.nivel_confianca_vinculo",
           "Contagem por nível de confiança do vínculo no par cliente–imóvel", True)
column("der_area_cadastral_utilizavel_m2", "Dados derivados", "enderecos_imoveis.csv.area_cadastrada_m2 + origem_area",
       "Cópia da área cadastral positiva com origem disponível; nulo quando indisponível; não é estimativa", True)
for name in ["tipo_imovel_sugerido", "uso_imovel_sugerido", "tipo_vinculo_sugerido"]:
    column("der_" + name, "Dados derivados", "",
           "Reservado para inferência posterior; status em ctl_status_inferencias")
for name in ["valor_bens_min", "valor_bens_max"]:
    column("est_" + name, "Estimativas", "",
           "Reservado para estimativa de faixa; não calculado nesta consolidação", True)
for name in ["area_m2", "area_min_m2", "area_max_m2"]:
    column("est_" + name, "Estimativas", "",
           "Reservado; nenhuma área é estimada nesta consolidação. Exige método e proveniência por perfil", True)

CONF_FIELDS = {
    "tipo_imovel": False, "uso_imovel": False, "tipo_vinculo": False,
    "material_parede_externa": False, "area_m2": True,
    "valor_bens": True, "imovel_possui_seguro_residencial": False,
}
for field, numeric in CONF_FIELDS.items():
    column("conf_" + field, "Respostas confirmadas", "",
           "Resposta futura da Bússola, sem sobrescrever o cadastro; status individual em ctl_status_conf_" + field, numeric)
    column("ctl_status_conf_" + field, "Controle", "",
           "NAO_COLETADO inicialmente; INFORMADO ou DESCONHECIDO após coleta")

CONTROL_RULES = {
    "versao_schema": "Versão do contrato de colunas",
    "revisao_base": "SHA-256 dos bytes do ZIP original",
    "revisao_perfil": "SHA-256 canônico de schema, base e todos os registros originais do par",
    "fonte_base": "Nome do ZIP original",
    "fontes_dados": "Tabelas que alimentaram o perfil, separadas por |",
    "consolidado_em": "Instante de processamento UTC; não é a data de atualização dos dados",
    "dados_atualizados_em": "Não fornecido nas fontes; vazio",
    "status_data_atualizacao": "NAO_INFORMADO_NA_FONTE",
    "status_revisao": "NAO_REVISADO; validação mecânica não equivale à revisão de negócio",
    "status_inferencias": "NAO_CALCULADO",
    "status_faixa_bens": "NAO_CALCULADO",
    "status_area_cadastrada": "DESCONHECIDO quando origem_area = NAO_DISPONIVEL; DISPONIVEL nos demais",
    "status_material_cadastrado": "DESCONHECIDO quando a fonte contém NAO_DISPONIVEL",
    "status_padrao_cadastrado": "DESCONHECIDO quando a fonte contém NAO_DISPONIVEL",
    "status_bussola": "NAO_EXECUTADA",
    "revisao_perfil_usada_bussola": "Vazio até execução da Bússola; registrar revisão exata consumida",
    "status_integridade_juncoes": "VALIDADA após verificações de chaves, vínculos e duplicações",
    "estimativa_area_status": "NAO_CALCULADO quando falta área; NAO_NECESSARIO quando há área cadastral utilizável",
    "estimativa_area_metodo": "Vazio; preencher somente quando houver estimativa calculada",
    "estimativa_area_formula": "Vazio; fórmula exata ou identificação do modelo utilizado",
    "estimativa_area_versao_metodo": "Vazio; versão do método ou modelo",
    "estimativa_area_dados_utilizados_json": "Vazio; valores e identificadores exatos dos dados usados na estimativa",
    "estimativa_area_parametros_json": "Vazio; coeficientes ou parâmetros do método",
    "estimativa_area_fonte_referencia": "Vazio; arquivo/documento/URL e versão da referência",
    "estimativa_area_data_referencia": "Vazio; data dos dados/referências usados",
    "estimativa_area_confianca": "Vazio; não foi inventado um nível de confiança",
    "estimativa_area_limitacoes": "Vazio; hipóteses e limitações do método quando existir",
}
for field, rule in CONTROL_RULES.items():
    column("ctl_" + field, "Controle", "", rule)

MOTOR_FIELDS = [
    "elegivel", "motivo_inelegibilidade", "plano_recomendado", "coberturas_recomendadas",
    "confianca_geral", "justificativa_recomendacao", "perguntas_confirmacao",
    "fontes_publicas_adicionais", "scores_json", "pendencias_json",
    "versao_regras", "revisao_perfil_avaliada", "avaliado_em", "status",
]
for field in MOTOR_FIELDS:
    column("motor_" + field, "Resultado do motor", "",
           "NAO_EXECUTADO" if field == "status" else "Reservado para execução posterior; vazio")

columns.sort(key=lambda c: GROUPS.index(c["group"]))  # Mantém a ordem original dentro de cada grupo.
header = [c["name"] for c in columns]
numeric_names = {c["name"] for c in columns if c["numeric"]}
generated_at = (datetime.fromisoformat(args.data_consolidacao).astimezone(timezone.utc).isoformat(timespec="seconds")
                if args.data_consolidacao else "")
payload = {"columns": columns, "max_bens": max_bens, "types": sorted(types),
           "generated_at": generated_at, "schema_version": SCHEMA_VERSION, "datasets": []}

def total(rows, field):
    return str(sum((Decimal(r[field]) for r in rows), Decimal(0)))

# 5. Consolidar cada par cliente–imóvel e calcular somente contagens e somas.
# O hash representa a revisão inicial. Confirmações futuras exigem nova revisão.
for source, (_, output) in zip(sources, DATASETS):
    records = []
    for prop in source["raw"]["enderecos_imoveis.csv"]:
        key = prop["cliente_id"], prop["imovel_id"]
        client = source["clients"].get((key[0],), {})
        signal = source["signals"].get(key, {})
        territory = source["territories"].get((prop["territorio_id"],), {})
        goods = source["goods"][key]
        row = {name: "" for name in header}
        row.update(ID=key[0] + "__" + key[1], cliente_id=key[0],
                   imovel_id=key[1], territorio_id=prop["territorio_id"])
        for table, original in [
            ("clientes.csv", client), ("enderecos_imoveis.csv", prop),
            ("sinais_imobiliarios.csv", signal), ("territorio.csv", territory)
        ]:
            for field, value in original.items():
                target = mappings.get((table, field))
                if target:
                    row[target] = value
        origin = client.get("origem_renda", "")
        check(not client or origin in ["INFORMADA", "PRESUMIDA_COM_BASE_EM_MOVIMENTACAO"], 'Falha de validação: not client or origin in ["INFORMADA", "PRESUMIDA_COM_BASE_EM_MOVIMENTACAO"]')
        if client:
            row["obs_renda_mensal_informada" if origin == "INFORMADA" else "est_renda_mensal_presumida"] = client["renda_mensal"]
        for slot, good in enumerate(goods, 1):
            for field, value in good.items():
                target = good_mappings.get((slot, field))
                if target:
                    row[target] = value
        row["der_quantidade_bens_referencia"] = str(len(goods))
        row["der_valor_bens_cadastrado_total_referencia"] = total(goods, "valor_cadastrado")
        row["est_valor_bens_ponderado_total_referencia"] = total(goods, "valor_bem_ponderado_referencia")
        for kind in sorted(types):
            subset = [g for g in goods if g["tipo_bem"] == kind]
            row[f"der_quantidade_bens_{kind.lower()}_referencia"] = str(len(subset))
            row[f"der_valor_bens_{kind.lower()}_cadastrado_referencia"] = total(subset, "valor_cadastrado")
            row[f"est_valor_bens_{kind.lower()}_ponderado_referencia"] = total(subset, "valor_bem_ponderado_referencia")
        for confidence in ["ALTA", "MEDIA", "BAIXA"]:
            row["der_quantidade_bens_confianca_" + confidence.lower()] = str(sum(g["nivel_confianca_vinculo"] == confidence for g in goods))
        area_available = (prop["origem_area"] not in ["", "NAO_DISPONIVEL", "DESCONHECIDO", "NAO_COLETADO"]
                          and prop["area_cadastrada_m2"] != "" and Decimal(prop["area_cadastrada_m2"]) > 0)
        row["der_area_cadastral_utilizavel_m2"] = prop["area_cadastrada_m2"] if area_available else ""
        for field in CONF_FIELDS:
            row["ctl_status_conf_" + field] = "NAO_COLETADO"
        profile_source = {
            "schema": SCHEMA_VERSION, "base": source["input"], "cliente": client,
            "imovel": prop, "sinais": signal, "territorio": territory, "bens": goods,
        }
        canonical = json.dumps(profile_source, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        row.update({
            "ctl_versao_schema": SCHEMA_VERSION,
            "ctl_revisao_base": source["zip_sha256"],
            "ctl_revisao_perfil": hashlib.sha256(canonical).hexdigest(),
            "ctl_fonte_base": source["input"], "ctl_fontes_dados": "|".join(FILES),
            "ctl_consolidado_em": generated_at,
            "ctl_status_data_atualizacao": "NAO_INFORMADO_NA_FONTE",
            "ctl_status_revisao": "NAO_REVISADO",
            "ctl_status_inferencias": "NAO_CALCULADO",
            "ctl_status_faixa_bens": "NAO_CALCULADO",
            "ctl_status_area_cadastrada": "DISPONIVEL" if area_available else "DESCONHECIDO",
            "ctl_status_material_cadastrado": "DESCONHECIDO" if prop["material_parede_externa_cadastrado"] == "NAO_DISPONIVEL" else "DISPONIVEL",
            "ctl_status_padrao_cadastrado": "DESCONHECIDO" if prop["padrao_construtivo_cadastrado"] == "NAO_DISPONIVEL" else "DISPONIVEL",
            "ctl_status_bussola": "NAO_EXECUTADA",
            "ctl_status_integridade_juncoes": "VALIDADA",
            "ctl_estimativa_area_status": "NAO_NECESSARIO" if area_available else "NAO_CALCULADO",
            "motor_status": "NAO_EXECUTADO",
        })
        missing_links = []
        if not client:
            missing_links.append("SEM_CLIENTE")
        if not signal:
            missing_links.append("SEM_SINAIS")
        if not territory:
            missing_links.append("SEM_TERRITORIO")
        if any((c["cliente_id"], c["imovel_id"]) == key for c in source["territory_conflicts"]):
            missing_links.append("DIVERGENCIA_TERRITORIAL")
        if missing_links:
            row["ctl_status_integridade_juncoes"] = "|".join(missing_links)
        check(set(row) == set(header), 'Falha de validação: set(row) == set(header)')
        records.append(row)
    check(len({r["ID"] for r in records}) == len(records), 'Falha de validação: len({r["ID"] for r in records}) == len(records)')
    payload["datasets"].append({
        "input": source["input"], "output": output, "records": records,
        "zip_sha256": source["zip_sha256"], "source_rows": {n: len(source["raw"][n]) for n in FILES},
    })

# 6. Exportar os CSVs. Campos vazios continuam vazios, sem fillna(0).
# UTF-8 com BOM ajuda a reconhecer os acentos no Excel; CRLF funciona no Windows.
for dataset in payload["datasets"]:
    with OUT.joinpath(dataset["output"]).open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=header, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(dataset["records"])

# 7. Reler os CSVs exportados e verificar todos os registros e atributos.
# Esta verificação confere o arquivo realmente gravado, não só o objeto em memória.
audit = []
for source, dataset in zip(sources, payload["datasets"]):
    with OUT.joinpath(dataset["output"]).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        check(reader.fieldnames == header, "Cabeçalho diferente do schema")
        exported = list(reader)
    check(exported == dataset["records"], "Conteúdo alterado durante a exportação")
    by_pair = unique_index(exported, ["cliente_id", "imovel_id"], "CSV exportado")
    check(set(by_pair) == set(source["props"]), "Perda ou multiplicação de pares")
    check(len({r["ID"] for r in exported}) == len(exported), "ID repetido")
    goods_recovered = []
    for key, row in by_pair.items():
        for table, original in [
            ("clientes.csv", source["clients"].get((key[0],), {})),
            ("enderecos_imoveis.csv", source["props"][key]),
            ("sinais_imobiliarios.csv", source["signals"].get(key, {})),
            ("territorio.csv", source["territories"].get((row["territorio_id"],), {})),
        ]:
            for field, value in original.items():
                target = mappings.get((table, field))
                if target:
                    check(row[target] == value, (key, table, field))
        client = source["clients"].get((key[0],), {})
        if client:
            income_column = "obs_renda_mensal_informada" if client["origem_renda"] == "INFORMADA" else "est_renda_mensal_presumida"
            check(row[income_column] == client["renda_mensal"], 'Falha de validação: row[income_column] == client["renda_mensal"]')
        original_goods = source["goods"][key]
        check(int(row["der_quantidade_bens_referencia"]) == len(original_goods), 'Falha de validação: int(row["der_quantidade_bens_referencia"]) == len(original_goods)')
        for slot in range(1, max_bens + 1):
            if slot <= len(original_goods):
                recovered = {"cliente_id": key[0], "imovel_id_referencia": key[1]}
                for field in source["headers"]["bens_compras.csv"]:
                    if field not in recovered:
                        recovered[field] = row[good_mappings[(slot, field)]]
                check(recovered == original_goods[slot - 1], (key, slot))
                goods_recovered.append(recovered)
            else:
                check(all(row[target] == "" for (number, _), target in good_mappings.items() if number == slot), 'Falha de validação: all(row[target] == "" for (number, _), target in good_mappings.items() if number == slot)')
    check(len(goods_recovered) + len(source["orphan_goods"]) == len(source["raw"]["bens_compras.csv"]), 'Falha de validação: len(goods_recovered) + len(source["orphan_goods"]) == len(source["raw"]["bens_compras.csv"])')
    check(sum(Decimal(r["der_valor_bens_cadastrado_total_referencia"]) for r in exported) == sum(Decimal(r["valor_cadastrado"]) for r in goods_recovered), 'Falha de validação: sum(Decimal(r["der_valor_bens_cadastrado_total_referencia"]) for r in exported) == sum(Decimal(r["valor_cadastrado"]) for r in goods_recovered)')
    check(sum(Decimal(r["est_valor_bens_ponderado_total_referencia"]) for r in exported) == sum(Decimal(r["valor_bem_ponderado_referencia"]) for r in goods_recovered), 'Falha de validação: sum(Decimal(r["est_valor_bens_ponderado_total_referencia"]) for r in exported) == sum(Decimal(r["valor_bem_ponderado_referencia"]) for r in goods_recovered)')
    check(hashlib.sha256(INPUT.joinpath(source["input"]).read_bytes()).hexdigest() == source["zip_sha256"], 'Falha de validação: hashlib.sha256(INPUT.joinpath(source["input"]).read_bytes()).hexdigest() == source["zip_sha256"]')
    audit.append({"arquivo": dataset["output"], "linhas": len(exported), "colunas": len(header),
                  "bens_preservados": len(goods_recovered), "ids_duplicados": 0,
                  "pares_perdidos": 0, "fontes_preservadas": True, "status": "VALIDADO"})

if WORK:
    WORK.joinpath("dados_consolidados.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    WORK.joinpath("mapeamentos.json").write_text(json.dumps({
        "mappings": [[table, field, target] for (table, field), target in mappings.items()],
        "good_mappings": [[slot, field, target] for (slot, field), target in good_mappings.items()],
    }, ensure_ascii=False), encoding="utf-8")
    WORK.joinpath("validacao_consolidacao.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

# 8. Documentar o contrato, as regras e cada coluna utilizada.
group_counts = Counter(c["group"] for c in columns)
group_table = "\n".join(f"| {g} | {group_counts[g]} |" for g in GROUPS)
dictionary = "\n".join(
    "| " + " | ".join(str(c[k]).replace("|", "/").replace("\n", " ") for k in ["name", "group", "origin", "rule"]) + " |"
    for c in columns
)
summary = "\n".join(
    f"- {d['output']}: {len(d['records']):,} linhas, {len(columns)} colunas; {d['source_rows']['bens_compras.csv']:,} bens preservados."
    for d in payload["datasets"]
)
guide = f"""# Consolidação do Seguro Residencial

Foram geradas duas visões de trabalho, a partir dos ZIPs originais, sem modificar as fontes.
O arquivo recebido chama-se Desenvolvimento. Ele corresponde à primeira base mencionada como Demonstração na solicitação.
A consolidação foi feita com auxílio de IA (ChatGPT/Codex).

{summary}

## Unidade de registro e chaves

Uma linha representa exatamente um par cliente–imóvel. ID = cliente_id + '__' + imovel_id.
Exemplo: CLI_00001__IMO_CLI_00001_01. Os códigos originais e territorio_id continuam disponíveis.
Clientes com mais de um imóvel têm uma linha para cada imóvel.
Clientes são unidos por cliente_id; sinais são unidos por cliente_id + imovel_id; território por territorio_id.
Bens são associados exclusivamente por cliente_id + imovel_id_referencia, antes de qualquer resumo.
O cadastro de imóveis determina o universo e a ordem das linhas.
Os dois CSVs têm exatamente as mesmas colunas, na mesma ordem.

## Grupos de colunas

| Grupo | Colunas |
| --- | ---: |
{group_table}

Os prefixos obs_, der_, est_, conf_, ctl_ e motor_ identificam a natureza do campo.
A classificação considera o dicionário da base e, no caso da renda, a origem informada em cada registro.
Renda INFORMADA fica em obs_renda_mensal_informada.
Renda PRESUMIDA_COM_BASE_EM_MOVIMENTACAO fica em est_renda_mensal_presumida.
A outra coluna de renda permanece vazia. Isso não representa renda zero.
Índice de maturidade digital é derivado. Coordenadas aproximadas, probabilidades e valores ponderados são estimativas existentes na fonte.

## Bens

Os {max_bens} blocos numerados preservam todos os atributos dos bens, em ordem crescente de bem_id dentro do par.
O número do bloco é apenas uma posição. O tipo do bem está na própria coluna tipo_bem.
Quando um imóvel tem menos bens, os blocos restantes ficam vazios, sem inventar bens ou valores.
A confiança de cada vínculo fica em ctl_bem_N_nivel_confianca_vinculo.
Contagens e somas por imóvel e por tipo são campos derivados.
Somente valores_cadastrados da mesma tabela são somados: compras de 36 meses e gastos de outras tabelas não entram nessa soma.
O total cadastrado de bens associados não comprova que todos estejam fisicamente no imóvel.
O total ponderado é a soma exata de valor_bem_ponderado_referencia da fonte, sem recalcular nem arredondar.
Esse total não é um limite inferior de faixa, nem o preço de reposição.
est_valor_bens_min e est_valor_bens_max ficam vazios, com status NAO_CALCULADO, até existir um método de estimação definido.

## Ausência e estados

- NAO: resposta negativa explícita existente na fonte; não equivale a falta de informação.
- DESCONHECIDO: informação indisponível ou dúvida explícita. Para material, padrão e área, há um status cadastral próprio.
- NAO_COLETADO: respostas de confirmação ainda não coletadas pela Bússola.
- NAO_CALCULADO: inferência ou faixa ainda não produzida.
- NAO_EXECUTADO / NAO_EXECUTADA: motor / Bússola ainda não executados.
- DISPONIVEL: valor cadastral está disponível conforme sua origem.

Os marcadores originais NAO_DISPONIVEL e os zeros das fontes foram preservados.
Em particular, area_cadastrada_m2 = 0 com origem_area = NAO_DISPONIVEL significa área desconhecida.
Um campo numérico vazio deve ser lido como nulo, nunca convertido automaticamente em zero.
Para os blocos de bens inexistentes, vazio significa que não existe aquele registro, não um bem desconhecido.
obs_complemento = SEM_COMPLEMENTO, quando presente, continua sendo o valor original.

## Confirmação, avaliação e motor

Campos conf_ estão vazios, com ctl_status_conf_CAMPO = NAO_COLETADO. Não há entrevistas nos ZIPs.
Campos sugeridos e resultados do motor também ficam vazios. Não foram inferidos tipo, uso, vínculo, elegibilidade, plano ou scores.
O grupo deve definir no motor a política de escolha entre cadastro, estimativa e confirmação.
A consolidação preserva as alternativas; não cria silenciosamente uma regra de negócio ou escolhe um valor efetivo.
Uma resposta coletada com conteúdo desconhecido deve usar status DESCONHECIDO.
Uma resposta negativa explícita usa valor NAO e status INFORMADO.
Valores confirmados devem ser adicionados em conf_ sem apagar obs_ ou est_.
Os campos scores_json e pendencias_json, quando preenchidos, devem conter JSON válido; inicialmente ficam vazios, sem simular uma lista vazia de pendências.
Catálogo de produtos e regras continuam separados e não são repetidos por perfil.
Dicionário original, catálogo e templates são arquivos de apoio, não fontes de observações a juntar como novas linhas.

## Revisões e datas

ctl_versao_schema = {SCHEMA_VERSION}.
ctl_revisao_base identifica os bytes exatos do ZIP por SHA-256.
ctl_revisao_perfil identifica o conteúdo original de cada perfil e a versão do schema por SHA-256 canônico.
ctl_consolidado_em registra o processamento em UTC. Não é a data de atualização dos dados originais.
A atualização na origem não foi informada: ctl_dados_atualizados_em fica vazio.
Bússola e motor devem registrar a revisão consumida nos campos próprios.
Estes CSVs são snapshots estáticos. O hash inicial não muda sozinho ao editar o arquivo.
Ao incorporar confirmações ou alterar um perfil, a aplicação deve gerar uma nova revisão do conteúdo completo, incluindo confirmações e estados, e invalidar ou recalcular resultados antigos.
A validação mecânica das junções não equivale a revisão de negócio: ctl_status_revisao começa em NAO_REVISADO.
Não foi criada uma confiança geral artificial; permanecem as confianças específicas da fonte.

## Formato

CSV separado por vírgula, UTF-8 com BOM e quebras de linha CRLF.
Decimais usam ponto. Aspas e vírgulas em texto seguem o padrão CSV.
Não foi gerado XLSX. Para abrir no Excel, importar como UTF-8 e selecionar o separador vírgula.
Código IBGE, número do endereço e todos os IDs devem ser tratados como texto.
As fontes são fictícias conforme o LEIA-ME dos pacotes. Não houve enriquecimento externo.

## Dicionário das colunas finais

| Coluna | Grupo | Origem | Regra ou significado |
| --- | --- | --- | --- |
{dictionary}
"""
OUT.joinpath("Guia_Consolidacao_Seguro_Residencial.md").write_text(guide, encoding="utf-8")
print(json.dumps({
    "schema_version": SCHEMA_VERSION, "columns": len(columns), "max_bens": max_bens,
    "groups": dict(group_counts), "datasets": [{"output": d["output"], "rows": len(d["records"]), "sources": d["source_rows"]} for d in payload["datasets"]]
}, ensure_ascii=False))

# 9. Produzir documentação e trilhas de proveniência utilizáveis pela equipe.
# As fórmulas geradoras das estimativas fornecidas no ZIP não são presumidas.

def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)

def unit_for(name, numeric):
    if not numeric:
        return "texto"
    if "area" in name:
        return "m²"
    if "latitude" in name or "longitude" in name:
        return "graus"
    if "probabilidade" in name:
        return "proporção de 0 a 1"
    if "maturidade" in name:
        return "pontos; escala definida pela fonte"
    if name == "obs_idade":
        return "anos"
    if any(word in name for word in ["quantidade", "qtd_", "frequencia_acesso"]):
        return "quantidade"
    return "BRL"

def level_for(col):
    if re.search(r"_bem_\d+_", col["name"]):
        return "bem associado ao par"
    if col["origin"].startswith("clientes.csv."):
        return "cliente; repetido nos imóveis"
    if col["origin"].startswith("territorio.csv."):
        return "território do imóvel"
    return "cliente–imóvel"

def absence_for(col):
    name = col["name"]
    if name == "obs_area_cadastrada_m2":
        return "0 + origem NAO_DISPONIVEL = área desconhecida; valor original preservado"
    if name == "der_area_cadastral_utilizavel_m2":
        return "vazio = sem área cadastral positiva utilizável; não é zero m²"
    if re.search(r"_bem_\d+_", name):
        return "vazio no bloco = inexistência daquele registro de bem; não substituir por zero"
    if name.startswith("conf_"):
        return "vazio + status NAO_COLETADO; NAO explícito é resposta negativa; DESCONHECIDO é dúvida"
    if name.startswith("motor_"):
        return "vazio = não executado; somente motor_status possui NAO_EXECUTADO"
    if col["numeric"]:
        return "vazio = nulo; zero válido preservado; interpretar com origem e status"
    return "vazio, NAO, NAO_DISPONIVEL e NAO_SE_APLICA conservam significados distintos por campo"

original_descriptions = {(r["tabela"].lower() + ".csv", r["campo"]): r["descricao"]
                         for r in sources[0]["raw"]["dicionario_dados.csv"]}
dictionary_rows = []
for col in columns:
    name = col["name"]
    values = sorted({r[name] for d in payload["datasets"] for r in d["records"] if r[name] != ""})
    is_count = col["numeric"] and any(word in name for word in ["quantidade", "qtd_", "frequencia_acesso", "obs_idade"])
    table_part, separator, field_part = col["origin"].partition(".csv.")
    description = original_descriptions.get((table_part + ".csv", field_part), "") if separator else ""
    dictionary_rows.append({
        "nome_final": name, "grupo": col["group"], "significado": description or col["rule"] or name,
        "nivel": level_for(col),
        "tipo": "inteiro" if is_count else ("decimal" if col["numeric"] else "texto"),
        "unidade": unit_for(name, col["numeric"]), "origem": col["origin"],
        "transformacao": col["rule"], "versao_transformacao": SCRIPT_VERSION,
        "natureza": col["group"], "ausencias": absence_for(col),
        "categorias_encontradas": "|".join(values) if not col["numeric"] and len(values) <= 24 else "",
        "consumidor": "RESULTADO; não usar como entrada de treinamento" if name.startswith("motor_") else "Bússola e motor; controles também servem à auditoria",
    })
write_csv(OUT / "Dicionario_Colunas.csv", list(dictionary_rows[0]), dictionary_rows)

source_mappings = []
for table in FILES:
    for field in sources[0]["headers"][table]:
        condition = "cópia do valor original"
        if field in ["cliente_id", "imovel_id", "territorio_id"]:
            targets = [field]
        elif field == "imovel_id_referencia":
            targets = ["imovel_id"]
            condition = "associar somente pelo par cliente_id + imovel_id_referencia"
        elif table == "clientes.csv" and field == "renda_mensal":
            targets = ["obs_renda_mensal_informada", "est_renda_mensal_presumida"]
            condition = "INFORMADA -> obs_; PRESUMIDA_COM_BASE_EM_MOVIMENTACAO -> est_; sem duplicar a renda"
        elif table == "territorio.csv" and field in ["codigo_ibge_municipio", "municipio_real", "uf_real", "cep_agregado"]:
            targets = ["obs_" + field]
            condition = "comparar com enderecos_imoveis.csv; cadastro do imóvel é canônico, divergência é registrada"
        elif table == "bens_compras.csv":
            targets = [good_mappings[(slot, field)] for slot in range(1, max_bens + 1)]
            condition = "posição em ordem crescente de bem_id dentro do par; detalhe original também é exportado"
        else:
            targets = [mappings[(table, field)]]
        source_mappings.append({"arquivo_origem": table, "coluna_origem": field,
                                "colunas_destino": "|".join(targets), "condicao": condition})
write_csv(OUT / "Mapeamento_Origem_Destino.csv", list(source_mappings[0]), source_mappings)

# O detalhe auxiliar mantém cada bem, inclusive um eventual vínculo órfão.
detail_files = []
for source, dataset in zip(sources, payload["datasets"]):
    base_name = "Desenvolvimento" if "Desenvolvimento" in source["input"] else "Teste_Comum"
    filename = "Bens_Detalhados_" + base_name + ".csv"
    detail = []
    for good in source["raw"]["bens_compras.csv"]:
        pair = good["cliente_id"], good["imovel_id_referencia"]
        detail.append({
            "base": base_name, "ID": pair[0] + "__" + pair[1], **good,
            "status_associacao": "VINCULO_VALIDO" if pair in source["props"] else "SEM_VINCULO_VALIDO",
        })
    write_csv(OUT / filename, list(detail[0]) if detail else ["base", "ID"] + source["headers"]["bens_compras.csv"] + ["status_associacao"], detail)
    detail_files.append(filename)

TRACE_FIELDS = [
    "base", "ID", "campo_final", "valor", "unidade", "status", "arquivo_origem", "coluna_origem",
    "chave_origem_json", "linha_csv_origem", "metodo", "formula", "versao_metodo",
    "dados_utilizados_json", "parametros_json", "confianca_fonte", "data_referencia",
    "limitacoes", "sha256_zip_origem",
]
trace_path = OUT / "Registro_Proveniencia_Estimativas_e_Area.csv"
trace_counts = Counter()
with trace_path.open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=TRACE_FIELDS, lineterminator="\r\n")
    writer.writeheader()
    for source, dataset in zip(sources, payload["datasets"]):
        base_name = "Desenvolvimento" if "Desenvolvimento" in source["input"] else "Teste_Comum"
        client_lines = {r["cliente_id"]: i for i, r in enumerate(source["raw"]["clientes.csv"], 2)}
        property_lines = {(r["cliente_id"], r["imovel_id"]): i for i, r in enumerate(source["raw"]["enderecos_imoveis.csv"], 2)}
        territory_lines = {r["territorio_id"]: i for i, r in enumerate(source["raw"]["territorio.csv"], 2)}
        good_lines = {r["bem_id"]: i for i, r in enumerate(source["raw"]["bens_compras.csv"], 2)}
        for row in dataset["records"]:
            pair = row["cliente_id"], row["imovel_id"]
            prop = source["props"][pair]
            client = source["clients"].get((pair[0],), {})
            goods = source["goods"][pair]
            for col in columns:
                name = col["name"]
                if not name.startswith("est_") and name != "obs_area_cadastrada_m2":
                    continue
                slot_match = re.search(r"^est_bem_(\d+)_", name)
                if slot_match and int(slot_match.group(1)) > len(goods):
                    continue
                trace = {field: "" for field in TRACE_FIELDS}
                trace.update({
                    "base": base_name, "ID": row["ID"], "campo_final": name, "valor": row[name],
                    "unidade": unit_for(name, col["numeric"]), "sha256_zip_origem": source["zip_sha256"],
                    "status": "FORNECIDO_NA_BASE" if row[name] != "" else "NAO_CALCULADO",
                    "metodo": "COPIA_DE_ESTIMATIVA_FORNECIDA" if row[name] != "" else "NAO_CALCULADO",
                    "formula": "NAO_DOCUMENTADA_NA_FONTE" if row[name] != "" else "",
                    "versao_metodo": "NAO_INFORMADA_NA_FONTE" if row[name] != "" else "",
                    "limitacoes": "Fórmula geradora e data de referência não disponibilizadas no pacote; valor não recalculado.",
                })
                if name == "est_renda_mensal_presumida":
                    trace.update(arquivo_origem="clientes.csv", coluna_origem="renda_mensal",
                        chave_origem_json=json.dumps({"cliente_id": pair[0]}, ensure_ascii=False),
                        linha_csv_origem=client_lines.get(pair[0], ""),
                        dados_utilizados_json=json.dumps({k: client.get(k, "") for k in ["renda_mensal", "origem_renda", "confianca_renda"]}, ensure_ascii=False),
                        confianca_fonte=client.get("confianca_renda", ""))
                    if client.get("origem_renda") == "INFORMADA":
                        trace.update(status="NAO_SE_APLICA_RENDA_INFORMADA", metodo="NAO_SE_APLICA", formula="", versao_metodo="",
                                     limitacoes="Renda fornecida como INFORMADA, preservada no grupo observado.")
                elif name in ["est_latitude_aproximada", "est_longitude_aproximada"]:
                    territory = source["territories"].get((prop["territorio_id"],), {})
                    trace.update(arquivo_origem="territorio.csv", coluna_origem=name.removeprefix("est_"),
                        chave_origem_json=json.dumps({"territorio_id": prop["territorio_id"]}, ensure_ascii=False),
                        linha_csv_origem=territory_lines.get(prop["territorio_id"], ""),
                        dados_utilizados_json=json.dumps(territory, ensure_ascii=False),
                        confianca_fonte="NAO_INFORMADA_NA_FONTE",
                        limitacoes="Coordenada aproximada e perturbada; não representa o domicílio real. Método de perturbação e data não fornecidos.")
                elif slot_match:
                    good = goods[int(slot_match.group(1)) - 1]
                    original_field = name.split("_", 3)[3]
                    trace.update(arquivo_origem="bens_compras.csv", coluna_origem=original_field,
                        chave_origem_json=json.dumps({"cliente_id": pair[0], "imovel_id_referencia": pair[1], "bem_id": good["bem_id"]}, ensure_ascii=False),
                        linha_csv_origem=good_lines[good["bem_id"]],
                        dados_utilizados_json=json.dumps(good, ensure_ascii=False),
                        confianca_fonte=good["nivel_confianca_vinculo"])
                    trace["limitacoes"] += " A confiança fornecida se refere ao vínculo do bem com o imóvel, não à calibração do erro da estimativa."
                elif name.startswith("est_valor_bens_") and name.endswith("_referencia"):
                    subset = goods
                    if name != "est_valor_bens_ponderado_total_referencia":
                        type_slug = name.removeprefix("est_valor_bens_").removesuffix("_ponderado_referencia")
                        subset = [g for g in goods if g["tipo_bem"].lower() == type_slug]
                    entries = [{"bem_id": g["bem_id"], "linha_csv": good_lines[g["bem_id"]],
                                "valor_bem_ponderado_referencia": g["valor_bem_ponderado_referencia"]} for g in subset]
                    trace.update(status="CALCULADO_POR_AGREGACAO", arquivo_origem="bens_compras.csv",
                        coluna_origem="valor_bem_ponderado_referencia",
                        chave_origem_json=json.dumps({"cliente_id": pair[0], "imovel_id_referencia": pair[1]}, ensure_ascii=False),
                        metodo="SOMA_DOS_VALORES_PONDERADOS_FORNECIDOS", versao_metodo=SCRIPT_VERSION,
                        formula="sum(valor_bem_ponderado_referencia dos bens do par e, quando aplicável, do tipo); soma de conjunto vazio = 0",
                        dados_utilizados_json=json.dumps(entries, ensure_ascii=False),
                        confianca_fonte="NAO_AGREGADA",
                        limitacoes="Soma auditável; fórmulas geradoras dos valores originais não fornecidas. Não é limite inferior nem inventário completo.")
                elif name in ["est_area_m2", "est_area_min_m2", "est_area_max_m2", "obs_area_cadastrada_m2"]:
                    trace.update(arquivo_origem="enderecos_imoveis.csv", coluna_origem="area_cadastrada_m2",
                        chave_origem_json=json.dumps({"cliente_id": pair[0], "imovel_id": pair[1]}, ensure_ascii=False),
                        linha_csv_origem=property_lines[pair],
                        dados_utilizados_json=json.dumps({k: prop[k] for k in ["area_cadastrada_m2", "origem_area", "confianca_area"]}, ensure_ascii=False),
                        confianca_fonte=prop["confianca_area"])
                    if name == "obs_area_cadastrada_m2":
                        trace.update(status=row["ctl_status_area_cadastrada"], metodo="COPIA_DO_CADASTRO", versao_metodo=SCRIPT_VERSION,
                            formula="valor original; indisponível para consumo quando origem_area=NAO_DISPONIVEL ou área<=0",
                            limitacoes="Origem conceitual declarada pela base: " + prop["origem_area"] +
                                       ". O pacote não inclui o laudo/cadastro original, seu identificador ou data.")
                    else:
                        trace.update(status=row["ctl_estimativa_area_status"], metodo="NAO_CALCULADO", formula="", versao_metodo="",
                            limitacoes="Nenhuma área estimada. Antes de estimar: definir e versionar método, dados, parâmetros, referências e validação.")
                else:
                    trace.update(limitacoes="Campo reservado; não foi produzida estimativa nem método nesta consolidação.")
                writer.writerow(trace)
                trace_counts[base_name] += 1

# 10. Qualidade: chaves, ausências, categorias e reconciliação.
# Limites de outliers são ajustados somente no desenvolvimento; nenhum valor é alterado.
from statistics import quantiles
thresholds = {}
for table in FILES:
    for field in sources[0]["headers"][table]:
        if field not in NUMERIC_FIELDS:
            continue
        vals = []
        for r in sources[0]["raw"][table]:
            if r[field] == "":
                continue
            if field == "area_cadastrada_m2" and (r["origem_area"] == "NAO_DISPONIVEL" or Decimal(r[field]) <= 0):
                continue
            vals.append(Decimal(r[field]))
        if len(vals) >= 4:
            q1, _, q3 = quantiles(vals, n=4, method="inclusive")
            iqr = q3 - q1
            thresholds[(table, field)] = (q1 - Decimal("1.5") * iqr, q3 + Decimal("1.5") * iqr)
outlier_rows = []
reports = []
for source, dataset, control in zip(sources, payload["datasets"], audit):
    raw = source["raw"]
    missing_report = {}
    type_report = {}
    category_alerts = []
    for table in FILES:
        missing_report[table] = {}
        type_report[table] = {}
        for field in source["headers"][table]:
            values = [r[field] for r in raw[table]]
            blank_count = sum(v == "" for v in values)
            marker_count = sum(v in ["NAO_DISPONIVEL", "DESCONHECIDO", "NAO_COLETADO", "NAO_SE_APLICA"] for v in values)
            if blank_count or marker_count:
                missing_report[table][field] = {"vazios": blank_count, "marcadores_ausencia": marker_count}
            if field in NUMERIC_FIELDS:
                numeric_values = [Decimal(v) for v in values if v != ""]
                check(all(v.is_finite() for v in numeric_values), (table, field, "Número não finito"))
                type_report[table][field] = {"tipo": "decimal", "min": str(min(numeric_values)) if numeric_values else "",
                                            "max": str(max(numeric_values)) if numeric_values else ""}
                bounds = thresholds.get((table, field))
                if bounds:
                    for line, r in enumerate(raw[table], 2):
                        if r[field] == "":
                            continue
                        if field == "area_cadastrada_m2" and (r["origem_area"] == "NAO_DISPONIVEL" or Decimal(r[field]) <= 0):
                            continue
                        value = Decimal(r[field])
                        if value < bounds[0] or value > bounds[1]:
                            keys = {k: r[k] for k in ["cliente_id", "imovel_id", "imovel_id_referencia", "territorio_id", "bem_id"] if k in r}
                            outlier_rows.append({"base": source["input"], "arquivo": table, "linha_csv": line,
                                "chave_json": json.dumps(keys, ensure_ascii=False), "campo": field, "valor": r[field],
                                "limite_inferior": str(bounds[0]), "limite_superior": str(bounds[1]),
                                "metodo": "IQR_1.5_DESENVOLVIMENTO", "acao": "SINALIZAR_SEM_ALTERAR"})
            else:
                type_report[table][field] = {"tipo": "texto"}
            if field in ["usuario_app", "possui_pet_informado", "possui_seguro_residencial",
                         "endereco_principal_compativel", "possui_termo_apartamento", "possui_termo_casa",
                         "possui_termo_bloco", "possui_termo_condominio", "pagamento_aluguel_recorrente",
                         "credito_recorrente_compativel_aluguel", "mesma_uf_imovel", "mesmo_municipio_imovel", "bem_financiado_pelo_banco"]:
                unexpected = sorted(set(values) - {"SIM", "NAO", ""})
                if unexpected:
                    category_alerts.append({"arquivo": table, "campo": field, "valores": unexpected})
    property_rows = dataset["records"]
    valid_goods = [g for g in raw["bens_compras.csv"] if (g["cliente_id"], g["imovel_id_referencia"]) in source["props"]]
    original_total = total(valid_goods, "valor_cadastrado")
    original_weighted = total(valid_goods, "valor_bem_ponderado_referencia")
    sum_total = sum((Decimal(r["der_valor_bens_cadastrado_total_referencia"]) for r in property_rows), Decimal(0))
    sum_weighted = sum((Decimal(r["est_valor_bens_ponderado_total_referencia"]) for r in property_rows), Decimal(0))
    check(Decimal(original_total) == sum_total and Decimal(original_weighted) == sum_weighted, 'Falha de validação: Decimal(original_total) == sum_total and Decimal(original_weighted) == sum_weighted')
    by_type = {}
    for kind in sorted(types):
        subset = [g for g in valid_goods if g["tipo_bem"] == kind]
        qty_after = sum(int(r[f"der_quantidade_bens_{kind.lower()}_referencia"]) for r in property_rows)
        value_after = sum((Decimal(r[f"der_valor_bens_{kind.lower()}_cadastrado_referencia"]) for r in property_rows), Decimal(0))
        weighted_after = sum((Decimal(r[f"est_valor_bens_{kind.lower()}_ponderado_referencia"]) for r in property_rows), Decimal(0))
        check(qty_after == len(subset) and value_after == Decimal(total(subset, "valor_cadastrado")) and weighted_after == Decimal(total(subset, "valor_bem_ponderado_referencia")), 'Falha de validação: qty_after == len(subset) and value_after == Decimal(total(subset, "valor_cadastrado")) and weighted_after == Decimal(total(subset, "valor_bem_ponderado_referencia"))')
        by_type[kind] = {"quantidade": qty_after, "valor_cadastrado": str(value_after), "valor_ponderado": str(weighted_after)}
    confidence_counts = {confidence: sum(g["nivel_confianca_vinculo"] == confidence for g in valid_goods) for confidence in ["ALTA", "MEDIA", "BAIXA"]}
    for confidence, count in confidence_counts.items():
        check(count == sum(int(r["der_quantidade_bens_confianca_" + confidence.lower()]) for r in property_rows), 'Falha de validação: count == sum(int(r["der_quantidade_bens_confianca_" + confidence.lower()]) for r in property_rows)')
    output_path = OUT / dataset["output"]
    report = {
        "pacote": source["input"], "sha256_pacote": source["zip_sha256"],
        "saida": dataset["output"], "sha256_csv": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "versao_script": SCRIPT_VERSION, "versao_schema": SCHEMA_VERSION,
        "parametros": {"data_consolidacao": generated_at, "max_bens_em_colunas": max_bens},
        "contagens_origem": dataset["source_rows"], "contagem_saida": len(property_rows), "colunas": len(columns),
        "chaves_duplicadas": 0, "pares_perdidos": 0, "ids_duplicados": 0,
        "cardinalidade_por_etapa": {stage: len(property_rows) for stage in ["imoveis", "apos_clientes", "apos_sinais", "apos_territorio", "apos_resumo_bens"]},
        "falhas_associacao": source["association_counts"],
        "divergencias_territoriais": source["territory_conflicts"],
        "politica_valor_territorial": "enderecos_imoveis é canônico; divergências são registradas e sinalizadas",
        "ausencias_na_origem": missing_report, "tipos_e_extremos": type_report, "categorias_inesperadas": category_alerts,
        "areas_sem_valor_utilizavel": sum(r["der_area_cadastral_utilizavel_m2"] == "" for r in property_rows),
        "areas_estimadas_nesta_execucao": 0,
        "rendas_presumidas_clientes": sum(r["origem_renda"] == "PRESUMIDA_COM_BASE_EM_MOVIMENTACAO" for r in raw["clientes.csv"]),
        "rendas_presumidas_linhas_perfil": sum(r["est_renda_mensal_presumida"] != "" for r in property_rows),
        "bens": {
            "registros_fonte": len(raw["bens_compras.csv"]), "registros_validos_consolidados": len(valid_goods),
            "registros_sem_vinculo": len(source["orphan_goods"]), "registros_no_detalhe_auxiliar": len(raw["bens_compras.csv"]),
            "imoveis_sem_registros_de_bens": sum(int(r["der_quantidade_bens_referencia"]) == 0 for r in property_rows),
            "soma_valor_cadastrado_antes": original_total, "soma_valor_cadastrado_depois": str(sum_total),
            "soma_valor_ponderado_antes": original_weighted, "soma_valor_ponderado_depois": str(sum_weighted),
            "diferenca_cadastrado": str(sum_total - Decimal(original_total)),
            "diferenca_ponderado": str(sum_weighted - Decimal(original_weighted)),
            "arredondamento_aplicado": "NENHUM; Decimal preserva a soma dos valores de origem",
            "por_tipo": by_type, "por_confianca_vinculo": confidence_counts,
        },
        "alertas_estimativas_fonte": [
            "Fórmula de renda presumida não documentada no pacote.",
            "Fórmula do índice de maturidade digital não documentada no pacote.",
            "Fórmulas das probabilidades e dos valores ponderados de bens não documentadas no pacote.",
            "Coordenadas são perturbadas; método e data de referência não fornecidos.",
            "A origem conceitual de área é fornecida, mas o documento original e sua data não estão no pacote.",
        ],
        "fontes_preservadas": control["fontes_preservadas"],
        "status": "VALIDADO_COM_PENDENCIAS" if any(source["association_counts"].values()) or source["territory_conflicts"] or category_alerts else "VALIDADO",
    }
    reports.append(report)

write_csv(OUT / "Alertas_Valores_Extremos.csv",
          ["base", "arquivo", "linha_csv", "chave_json", "campo", "valor", "limite_inferior", "limite_superior", "metodo", "acao"],
          outlier_rows)
quality = {
    "versao_script": SCRIPT_VERSION, "versao_schema": SCHEMA_VERSION,
    "relatorios": reports,
    "politica_extremos": "Regra 1,5 IQR com quartis inclusivos aprendidos somente no desenvolvimento; alerta de revisão, sem alteração dos dados.",
    "avisos_consumo": [
        "Renda de cliente se repete nos imóveis; não somar como se fossem clientes diferentes.",
        "Seguro residencial informado no cadastro do cliente não identifica qual imóvel está segurado.",
        "Campos motor_ são resultados reservados; não usar como atributos de treinamento.",
        "Registro de estimativas distingue cópia de estimativa existente de um cálculo produzido nesta execução.",
    ],
}
OUT.joinpath("Relatorio_Qualidade.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
quality_lines = [
    "# Relatório de qualidade da consolidação", "",
    f"Script e schema: {SCRIPT_VERSION}. Data de consolidação parametrizada: {generated_at or 'não fornecida'}.", "",
    "| Base | Clientes | Imóveis / linhas finais | Bens preservados | Áreas ausentes | Áreas estimadas |",
    "| --- | ---: | ---: | ---: | ---: | ---: |",
]
for report in reports:
    quality_lines.append(f"| {report['pacote']} | {report['contagens_origem']['clientes.csv']} | {report['contagem_saida']} | {report['bens']['registros_no_detalhe_auxiliar']} | {report['areas_sem_valor_utilizavel']} | 0 |")
quality_lines += [
    "", "As verificações não encontraram IDs duplicados, pares perdidos ou multiplicação de registros nos pacotes fornecidos.",
    "Os totais cadastrado e ponderado dos bens foram reconciliados exatamente, por base e por categoria, sem arredondamento.",
    "As confianças ALTA, MEDIA e BAIXA também foram contadas e reconciliadas.",
    "", "## Limitações registradas", "",
    "Não foram estimadas áreas, faixas de bens, tipos, vínculos ou resultados do motor.",
    "As estimativas existentes foram copiadas com referência ao ZIP, arquivo, chave e linha de dados.",
    "Os pacotes não documentam suas fórmulas geradoras, parâmetros ou datas; essa limitação está registrada, sem atribuir uma fórmula presumida.",
    "Para área conhecida, a origem conceitual é preservada. Não é possível conferir um laudo ou cadastro original que não veio no pacote.",
    "O arquivo Alertas_Valores_Extremos.csv apenas sinaliza observações fora da regra de 1,5 IQR calibrada no desenvolvimento.",
    "Outlier não significa erro, inelegibilidade ou categoria de risco. Nenhum valor foi cortado, substituído ou removido.",
    "", "## Reprodutibilidade", "",
    "As linhas seguem o cadastro de imóveis e os bens são ordenados por bem_id no par.",
    "Com os mesmos ZIPs e parâmetros, os CSVs são determinísticos. Para reproduzir os arquivos desta execução, use:",
    "", chr(96) * 3 + "bash",
    f"python consolidar_seguro_residencial.py --entrada . --saida resultados --data-consolidacao {generated_at}" if generated_at else "python consolidar_seguro_residencial.py --entrada . --saida resultados",
    chr(96) * 3, "",
    "Sem --data-consolidacao, o campo de processamento fica vazio, para não inserir um relógio variável nos CSVs.",
    "Hashes SHA-256 dos ZIPs e das saídas estão em Relatorio_Qualidade.json.",
]
OUT.joinpath("Relatorio_Qualidade.md").write_text("\n".join(quality_lines) + "\n", encoding="utf-8")

guide_path = OUT / "Guia_Consolidacao_Seguro_Residencial.md"
guide_text = guide_path.read_text(encoding="utf-8")
guide_text += """
## Área e proveniência

Não foi estimada nenhuma área. est_area_m2, est_area_min_m2 e est_area_max_m2 estão vazios.
der_area_cadastral_utilizavel_m2 copia a área positiva quando sua origem está disponível; nos demais casos fica nulo.
Os campos ctl_estimativa_area_* reservam método, fórmula, versão, dados utilizados, parâmetros, referência, data, confiança e limitações.
O registro de proveniência inclui cada área original e cada campo estimado ou reservado, com ZIP, arquivo, chave e linha.
Quando a fórmula geradora de uma estimativa da fonte não foi fornecida, o registro informa NAO_DOCUMENTADA_NA_FONTE.
Uma área estimada futura exige definir o método, registrar seus dados e validar o erro nos imóveis com área conhecida.
Se houver treinamento ou calibração, usar somente Desenvolvimento para ajustar parâmetros; aplicar o método fixo no Teste Comum.
Não foi criada uma imputação por mediana, uma regressão nem uma relação presumida entre IPTU e área.

## Uso e arquivos de apoio

O script usa somente a biblioteca padrão do Python 3.10 ou superior, sem dependências externas.
As verificações são explícitas e permanecem ativas em todas as execuções do script.
Exemplo: python consolidar_seguro_residencial.py --entrada . --saida resultados
Para repetir a mesma data de processamento, informar o parâmetro mostrado no relatório de qualidade.
Nomes de novas colunas e schema 0.1.0 são a proposta de contrato para alinhamento com a equipe.
conf_ significa resposta confirmada; confiança estatística usa nomes explícitos em ctl_.
O seguro no cadastro do cliente não é convertido em confirmação de seguro para cada imóvel.

- Dicionario_Colunas.csv: tipo, unidade, nível, origem, transformação, ausência, natureza e consumidor.
- Mapeamento_Origem_Destino.csv: mapeamento de todas as colunas das cinco fontes.
- Relatorio_Qualidade.json e .md: conferências e limitações.
- Registro_Proveniencia_Estimativas_e_Area.csv: linhagem das estimativas e da área, incluindo as que não foram calculadas.
- Alertas_Valores_Extremos.csv: alertas estatísticos para revisão, sem modificar valores.
- Bens_Detalhados_Desenvolvimento.csv e Bens_Detalhados_Teste_Comum.csv: todos os bens originais, com o par e o status do vínculo.

Os blocos numerados na base principal atendem à opção escolhida nesta conversa.
O detalhe auxiliar também atende ao guia e permite consultar um bem pelo identificador.
Os CSVs não implementam atualizações automáticas: a aplicação deve gerar nova revisão ao incorporar respostas.
"""
guide_path.write_text(guide_text, encoding="utf-8")
print(json.dumps({"relatorios_qualidade": [r["status"] for r in reports],
                  "registros_proveniencia": dict(trace_counts),
                  "alertas_estatisticos": len(outlier_rows),
                  "areas_estimadas": 0, "arquivo_dicionario": "Dicionario_Colunas.csv"}, ensure_ascii=False))


