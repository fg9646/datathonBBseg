"""Regressões da consolidação. Usa apenas cópias mínimas dos ZIPs originais."""
from pathlib import Path
import argparse
import csv
import io
import json
import shutil
import subprocess
import sys
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--script", type=Path, required=True)
parser.add_argument("--originais", type=Path, required=True)
parser.add_argument("--trabalho", type=Path, required=True)
parser.add_argument("--fase", choices=["essencial", "completa"], default="completa")
args = parser.parse_args()
args.trabalho.mkdir(parents=True, exist_ok=True)
NAMES = ["Seguro_Residencial_Desenvolvimento.zip", "Seguro_Residencial_Teste_Comum.zip"]
OUTPUTS = ["Seguro_Residencial_Desenvolvimento_Consolidado.csv", "Seguro_Residencial_Teste_Comum_Consolidado.csv"]

def load_fixture(filename):
    with zipfile.ZipFile(args.originais / filename) as z:
        members = {n: z.read(n) for n in z.namelist()}
    def read(name):
        reader = csv.DictReader(io.StringIO(members[name].decode("utf-8-sig")))
        return reader.fieldnames, list(reader)
    headers = {}
    data = {}
    for name in members:
        if name.endswith(".csv"):
            headers[name], data[name] = read(name)
    prop = data["enderecos_imoveis.csv"][0].copy()
    cli, imo, ter = prop["cliente_id"], prop["imovel_id"], prop["territorio_id"]
    data["enderecos_imoveis.csv"] = [prop]
    data["clientes.csv"] = [next(r for r in data["clientes.csv"] if r["cliente_id"] == cli)]
    data["sinais_imobiliarios.csv"] = [next(r for r in data["sinais_imobiliarios.csv"] if (r["cliente_id"], r["imovel_id"]) == (cli, imo))]
    data["territorio.csv"] = [next(r for r in data["territorio.csv"] if r["territorio_id"] == ter)]
    data["template_resultado_times.csv"] = [next(r for r in data["template_resultado_times.csv"] if (r["cliente_id"], r["imovel_id"]) == (cli, imo))]
    prototype = data["bens_compras.csv"][0].copy()
    goods = []
    kinds = ["ELETRODOMESTICO", "ELETRONICO", "MOVEL", "ITEM_LAZER", "MOVEL", "ELETRONICO"]
    for index, kind in enumerate(kinds, 1):
        goods.append({**prototype, "bem_id": f"BEM_FIXTURE_{index:02d}", "cliente_id": cli,
                      "imovel_id_referencia": imo, "tipo_bem": kind, "nivel_confianca_vinculo": "ALTA",
                      "probabilidade_bem_no_imovel_referencia": "0.5"})
    data["bens_compras.csv"] = goods
    return members, headers, data

def write_fixture(path, fixture):
    members, headers, data = fixture
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, original in members.items():
            if name not in data:
                z.writestr(name, original)
                continue
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=headers[name], lineterminator="\r\n")
            writer.writeheader()
            writer.writerows(data[name])
            z.writestr(name, stream.getvalue().encode("utf-8-sig"))

def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def run_case(name, mutate, inspect, expect_failure=False):
    folder = args.trabalho / name
    inputs, outputs = folder / "entrada", folder / "saida"
    inputs.mkdir(parents=True, exist_ok=True)
    fixtures = [load_fixture(filename) for filename in NAMES]
    mutate(fixtures[1][2])
    for filename, fixture in zip(NAMES, fixtures):
        write_fixture(inputs / filename, fixture)
    result = subprocess.run([sys.executable, str(args.script), "--entrada", str(inputs), "--saida", str(outputs),
                             "--data-consolidacao", "2026-10-28T18:00:00+00:00"],
                            capture_output=True, text=True)
    if expect_failure:
        error_file = outputs / "Relatorio_Qualidade_ERRO.json"
        error = json.loads(error_file.read_text()) if error_file.exists() else {}
        verdict, detail = inspect(result, error, outputs)
    elif result.returncode:
        verdict, detail = False, result.stderr[-1000:]
    else:
        quality = json.loads((outputs / "Relatorio_Qualidade.json").read_text())["relatorios"][1]
        verdict, detail = inspect(rows(outputs / OUTPUTS[1]), quality, outputs)
    return {"caso": name, "passou": verdict, "detalhe": detail}

def absence_change(data):
    row = data["enderecos_imoveis.csv"][0]
    row["material_parede_externa_cadastrado"] = ""
    row["padrao_construtivo_cadastrado"] = "   "
def absence_check(rs, report, out):
    row = rs[0]
    ok = (row["obs_material_parede_externa_cadastrado"] == "" and row["obs_padrao_construtivo_cadastrado"] == "   "
          and row["ctl_status_material_cadastrado"] == "DESCONHECIDO"
          and row["ctl_status_padrao_cadastrado"] == "DESCONHECIDO")
    return ok, {"material": row["ctl_status_material_cadastrado"], "padrao": row["ctl_status_padrao_cadastrado"],
                "status_relatorio": report["status"]}

def probability_change(data):
    data["bens_compras.csv"][0]["probabilidade_bem_no_imovel_referencia"] = "1.25"
def probability_check(rs, report, out):
    row = rs[0]
    events = report.get("ocorrencias_qualidade", [])
    ok = (row["est_bem_1_probabilidade_bem_no_imovel_referencia"] == "1.25"
          and row.get("der_quantidade_bens_probabilidade_invalida") == "1"
          and report["status"] != "VALIDADO"
          and any(e.get("codigo") == "PROBABILIDADE_FORA_INTERVALO" and e.get("valor_original") == "1.25" for e in events))
    return ok, {"valor": row["est_bem_1_probabilidade_bem_no_imovel_referencia"],
                "contagem_invalida": row.get("der_quantidade_bens_probabilidade_invalida"),
                "status_relatorio": report["status"]}

def confidence_change(data):
    data["bens_compras.csv"][0]["nivel_confianca_vinculo"] = "ALTISSIMA"
def confidence_check(rs, report, out):
    row = rs[0]
    counts = report["bens"]["por_confianca_vinculo"]
    quantity = int(row["der_quantidade_bens_referencia"])
    ok = (row["ctl_bem_1_nivel_confianca_vinculo"] == "ALTISSIMA"
          and counts.get("INVALIDA") == 1 and sum(counts.values()) == quantity
          and report["status"] != "VALIDADO")
    return ok, {"contagens": counts, "bens": quantity, "status_relatorio": report["status"]}

results = [
    run_case("material_e_padrao_vazios", absence_change, absence_check),
    run_case("probabilidade_fora_intervalo", probability_change, probability_check),
    run_case("confianca_nao_reconhecida", confidence_change, confidence_check),
]
if args.fase == "completa":
    def probability_limits(data):
        values = ["0", "1", "", "-0.01", "NAO_DISPONIVEL", "0.5"]
        for good, value in zip(data["bens_compras.csv"], values):
            good["probabilidade_bem_no_imovel_referencia"] = value
    def probability_limits_check(rs, report, out):
        row = rs[0]
        detail = rows(out / "Bens_Detalhados_Teste_Comum.csv")
        counts = report["bens"].get("por_validade_probabilidade", {})
        ok = (counts == {"VALIDA": 3, "AUSENTE": 2, "INVALIDA": 1}
              and [r["probabilidade_bem_no_imovel_referencia"] for r in detail] == ["0", "1", "", "-0.01", "NAO_DISPONIVEL", "0.5"])
        return ok, counts
    results.append(run_case("probabilidade_limites_ausencia_e_negativa", probability_limits, probability_limits_check))

    def missing_confidence(data):
        values = ["ALTA", "MEDIA", "BAIXA", "", "DESCONHECIDO", "ALTA "]
        for good, value in zip(data["bens_compras.csv"], values):
            good["nivel_confianca_vinculo"] = value
    def missing_confidence_check(rs, report, out):
        counts = report["bens"]["por_confianca_vinculo"]
        ok = counts == {"ALTA": 1, "MEDIA": 1, "BAIXA": 1, "DESCONHECIDA": 2, "INVALIDA": 1}
        return ok, counts
    results.append(run_case("confianca_ausente_e_invalida", missing_confidence, missing_confidence_check))

    def marker_change(data):
        p = data["enderecos_imoveis.csv"][0]
        p["material_parede_externa_cadastrado"] = "DESCONHECIDO"
        p["padrao_construtivo_cadastrado"] = "NAO_COLETADO"
    results.append(run_case("outros_marcadores_ausencia", marker_change,
        lambda rs, report, out: (rs[0]["ctl_status_material_cadastrado"] == rs[0]["ctl_status_padrao_cadastrado"] == "DESCONHECIDO",
                                {"material":rs[0]["ctl_status_material_cadastrado"],"padrao":rs[0]["ctl_status_padrao_cadastrado"]})))

    def orphan_change(data):
        data["bens_compras.csv"][0]["imovel_id_referencia"] = "IMOVEL_INEXISTENTE"
        data["bens_compras.csv"][0]["nivel_confianca_vinculo"] = "ALTISSIMA"
    def orphan_check(rs, report, out):
        detail = rows(out / "Bens_Detalhados_Teste_Comum.csv")
        counts = report["bens"]["por_confianca_vinculo"]
        ok = (len(detail) == 6 and int(rs[0]["der_quantidade_bens_referencia"]) == 5
              and report["bens"]["registros_sem_vinculo"] == 1 and sum(counts.values()) == 5
              and counts.get("INVALIDA") == 0 and detail[0]["status_associacao"] == "SEM_VINCULO_VALIDO")
        return ok, {"bens_detalhe":len(detail), "bens_resumo":rs[0]["der_quantidade_bens_referencia"],"confiancas":counts}
    results.append(run_case("bem_orfao_preservado_separadamente", orphan_change, orphan_check))

    def extra_good(data):
        good = data["bens_compras.csv"][0].copy()
        good["bem_id"] = "BEM_FIXTURE_07"
        data["bens_compras.csv"].append(good)
    def schema_failure(result, error, outputs):
        ok = result.returncode != 0 and "SCHEMA" in error.get("mensagem", "") and not list(outputs.glob("*Consolidado.csv"))
        return ok, error.get("mensagem", result.stderr[-300:])
    results.append(run_case("mais_bens_nao_altera_schema_silenciosamente", extra_good, schema_failure, expect_failure=True))
    results.append(run_case("nova_categoria_nao_altera_schema_silenciosamente",
        lambda data: data["bens_compras.csv"][0].update(tipo_bem="NOVA_CATEGORIA"),
        schema_failure, expect_failure=True))
    results.append(run_case("chave_duplicada_bloqueia_saida",
        lambda data: data["clientes.csv"].append(data["clientes.csv"][0].copy()),
        lambda result, error, outputs: (result.returncode != 0 and bool(error) and not list(outputs.glob("*Consolidado.csv")), error.get("mensagem","")),
        expect_failure=True))

summary = {"script_testado": args.script.name, "fase": args.fase,
           "total": len(results), "aprovados": sum(r["passou"] for r in results),
           "resultados": results}
(args.trabalho / "Resultados_Testes_Regressao.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
sys.exit(0 if all(r["passou"] for r in results) else 1)

