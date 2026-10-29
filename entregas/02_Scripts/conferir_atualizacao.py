"""Conferência independente: compara o pacote recebido com a revisão corrigida."""
from pathlib import Path
from decimal import Decimal
import argparse,csv,io,json,zipfile,hashlib

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--pacote-anterior",type=Path,required=True)
parser.add_argument("--atualizado",type=Path,required=True)
parser.add_argument("--originais",type=Path,required=True)
parser.add_argument("--relatorio",type=Path,required=True)
args=parser.parse_args()
def read_rows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        return reader.fieldnames,list(reader)
expected_new={
    "der_quantidade_bens_confianca_desconhecida","der_quantidade_bens_confianca_invalida",
    "der_quantidade_bens_probabilidade_valida","der_quantidade_bens_probabilidade_ausente",
    "der_quantidade_bens_probabilidade_invalida","ctl_status_qualidade_dados",
    "ctl_quantidade_ocorrencias_qualidade","ctl_ocorrencias_qualidade_json",
}
allowed_updates={"ctl_versao_schema","ctl_revisao_perfil","ctl_consolidado_em"}
summaries=[]
with zipfile.ZipFile(args.pacote_anterior) as z:
    assert z.testzip() is None
    for base,amount,goods in [("Desenvolvimento",2578,8988),("Teste_Comum",138,494)]:
        name="Seguro_Residencial_"+base+"_Consolidado.csv"
        old_reader=csv.DictReader(io.StringIO(z.read(name).decode("utf-8-sig")))
        old_header,old_rows=old_reader.fieldnames,list(old_reader)
        new_header,new_rows=read_rows(args.atualizado/name)
        assert len(new_header)==200 and len(new_rows)==amount
        assert set(new_header)-set(old_header)==expected_new and set(old_header)<=set(new_header)
        assert [(r["cliente_id"],r["imovel_id"]) for r in old_rows]==[(r["cliente_id"],r["imovel_id"]) for r in new_rows]
        checked=0
        for previous,current in zip(old_rows,new_rows):
            for field in old_header:
                if field not in allowed_updates:
                    assert previous[field]==current[field],(base,current["ID"],field)
                    checked+=1
            assert current["ctl_versao_schema"]=="0.2.0"
            occurrences=json.loads(current["ctl_ocorrencias_qualidade_json"])
            assert len(occurrences)==int(current["ctl_quantidade_ocorrencias_qualidade"])
            assert all("prioridade_pergunta" not in event and "elegivel" not in event for event in occurrences)
            assert current["motor_status"]=="NAO_EXECUTADO"
            assert all(v=="" for k,v in current.items() if k.startswith("conf_") or (k.startswith("motor_") and k!="motor_status"))
            assert sum(int(current["der_quantidade_bens_confianca_"+key]) for key in ["alta","media","baixa","desconhecida","invalida"])==int(current["der_quantidade_bens_referencia"])
            assert sum(int(current["der_quantidade_bens_probabilidade_"+key]) for key in ["valida","ausente","invalida"])==int(current["der_quantidade_bens_referencia"])
            assert current["est_area_m2"]==current["est_area_min_m2"]==current["est_area_max_m2"]==""
        detail_name="Bens_Detalhados_"+base+".csv"
        old_detail=list(csv.DictReader(io.StringIO(z.read(detail_name).decode("utf-8-sig"))))
        new_detail_header,new_detail=read_rows(args.atualizado/detail_name)
        assert len(new_detail)==len(old_detail)==goods
        for previous,current in zip(old_detail,new_detail):
            assert all(previous[k]==current[k] for k in previous)
            assert current["status_probabilidade_vinculo"]=="VALIDA"
            assert current["status_confianca_vinculo"]=="VALIDA"
        summaries.append({"base":base,"linhas":amount,"bens":goods,"colunas":len(new_header),
                          "celulas_preexistentes_preservadas":checked,"ids_e_ordem_preservados":True})

quality=json.loads((args.atualizado/"Relatorio_Qualidade.json").read_text(encoding="utf-8"))
for report in quality["relatorios"]:
    assert report["status"]=="VALIDADO_COM_AUSENCIAS"
    assert report["resumo_ocorrencias"]["pendencias"]==0
    assert report["bens"]["diferenca_cadastrado"]==report["bens"]["diferenca_ponderado"]=="0"
    assert report["rotulagem_ausencias_conferida"]
    assert report["bens"]["confiancas_explicam_todos_os_bens"]
    assert report["bens"]["probabilidades_explicam_todos_os_bens"]
    assert report["bens"]["por_validade_probabilidade"]["INVALIDA"]==0
    assert report["bens"]["por_confianca_vinculo"]["INVALIDA"]==0
    assert hashlib.sha256((args.atualizado/report["saida"]).read_bytes()).hexdigest()==report["sha256_csv"]
    assert hashlib.sha256((args.originais/report["pacote"]).read_bytes()).hexdigest()==report["sha256_pacote"]
dictionary_header,dictionary=read_rows(args.atualizado/"Dicionario_Colunas.csv")
assert len(dictionary)==200
lookup={r["nome_final"]:r for r in dictionary}
for name in expected_new:
    if name.startswith("der_quantidade") or name=="ctl_quantidade_ocorrencias_qualidade":
        assert lookup[name]["tipo"]=="inteiro" and lookup[name]["unidade"]=="quantidade",name
assert lookup["conf_area_m2"]["natureza"]=="DECLARADO"
_,events=read_rows(args.atualizado/"Ocorrencias_Qualidade_Dados.csv")
assert len(events)==sum(len(r["ocorrencias_qualidade"]) for r in quality["relatorios"])
result={"status":"APROVADO","versao":"0.2.0","bases":summaries,
        "oito_colunas_novas_exatas":True,"contagens_confianca_e_probabilidade_completas":True,
        "probabilidades_e_confiancas_invalidas_nos_originais":0,
        "ocorrencias_ausencia_documentadas":len(events),
        "estimativas_area_novas":0,"fontes_originais_preservadas":True,
        "pacote_anterior_sha256":hashlib.sha256(args.pacote_anterior.read_bytes()).hexdigest()}
args.relatorio.parent.mkdir(parents=True,exist_ok=True)
args.relatorio.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(result,ensure_ascii=False,indent=2))

