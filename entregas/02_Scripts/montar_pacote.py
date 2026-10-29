"""Empacota a revisão, suas referências, evidências e manifesto de integridade."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import shutil
import zipfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--resultado",type=Path,required=True)
parser.add_argument("--pacote-anterior",type=Path,required=True)
parser.add_argument("--referencias",type=Path,required=True)
parser.add_argument("--evidencias",type=Path,required=True)
args=parser.parse_args()
out=args.resultado.resolve()
script_dir=Path(__file__).resolve().parent
out.mkdir(parents=True,exist_ok=True)
for name in ["consolidar_seguro_residencial.py","verificar_ajustes.py","conferir_atualizacao.py","montar_pacote.py"]:
    origin=script_dir/name
    target=out/name
    if origin!=target:
        shutil.copyfile(origin,target)
(out/"referencias").mkdir(exist_ok=True)
for name in ["Checklist_Ajustes_Pacote_Garrido.md","Proposta_Integracao_Base_Bussola_Motor_atualizado.md"]:
    shutil.copyfile(args.referencias/name,out/"referencias"/name)
(out/"historico").mkdir(exist_ok=True)
previous_sha=hashlib.sha256(args.pacote_anterior.read_bytes()).hexdigest()
with zipfile.ZipFile(args.pacote_anterior) as z:
    assert z.testzip() is None
    manifest=json.loads(z.read("Manifesto_SHA256.json"))
    for name,info in manifest.items():
        assert hashlib.sha256(z.read(name)).hexdigest()==info["sha256"],name
    (out/"historico"/"consolidar_original.py").write_bytes(z.read("consolidar_seguro_residencial.py"))
    (out/"referencias"/"Guia_Unificacao_Tabelas_Garrido.md").write_bytes(z.read("referencias/Guia_Unificacao_Tabelas_Garrido.md"))
for name in ["Resultados_Testes_Antes.json","Resultados_Testes_Regressao.json",
             "Verificacao_Independente.json","Verificacao_Reproducibilidade.json"]:
    shutil.copyfile(args.evidencias/name,out/name)
before=json.loads((out/"Resultados_Testes_Antes.json").read_text(encoding="utf-8"))
after=json.loads((out/"Resultados_Testes_Regressao.json").read_text(encoding="utf-8"))
independent=json.loads((out/"Verificacao_Independente.json").read_text(encoding="utf-8"))
repro=json.loads((out/"Verificacao_Reproducibilidade.json").read_text(encoding="utf-8"))
assert after["aprovados"]==after["total"] and independent["status"]=="APROVADO" and repro["reproducao_byte_a_byte"]
quality=json.loads((out/"Relatorio_Qualidade.json").read_text(encoding="utf-8"))
for report in quality["relatorios"]:
    assert hashlib.sha256((out/report["saida"]).read_bytes()).hexdigest()==report["sha256_csv"]
assert hashlib.sha256((out/"consolidar_seguro_residencial.py").read_bytes()).hexdigest()==repro["script_sha256"]

verification=[
    "# Verificação independente — versão 0.2.0","",
    f"- Antes: {before['aprovados']}/{before['total']} casos essenciais aprovados no script recebido.",
    f"- Depois: {after['aprovados']}/{after['total']} cenários artificiais aprovados no script corrigido.",
    "- Testes usam cópias mínimas das fontes. Nenhum ZIP original foi alterado.",
    "- Desenvolvimento: 2.578 linhas e 8.988 bens. Teste comum: 138 linhas e 494 bens.",
    "- As duas bases têm as mesmas 200 colunas; são oito colunas novas e nenhuma coluna original removida.",
    "- Chaves, ordem, atributos preexistentes e detalhe dos bens foram comparados com o pacote anterior.",
    "- Mudanças esperadas nos metadados: versão do schema, hash do perfil e data parametrizada da consolidação.",
    "- Reconciliação exata de valores cadastrados e ponderados; nenhuma diferença nas somas.",
    "- As cinco contagens de confiança e as três contagens de probabilidade explicam todos os bens vinculados.",
    f"- {repro['registros_proveniencia_verificados']} registros de proveniência conferidos: {repro['copias_verificadas']} cópias, {repro['somas_recalculadas']} somas e {repro['reservados_vazios']} campos reservados vazios.",
    "- Reexecução do script com mesmos ZIPs e parâmetros: todos os arquivos gerados comparados byte a byte.",
    "- Os originais não contêm probabilidades ou confianças inválidas; as falhas anteriores foram reproduzidas somente em cópias artificiais.",
    "- As lacunas cadastrais existentes foram registradas como ausências, sem aprovação/rejeição comercial ou P0 automático.",
    "- Nenhuma área nova, prioridade de pergunta, score, plano ou cobertura foi calculada.","",
    "## Casos artificiais","",
    "| Caso | Resultado |","| --- | --- |",
]
for item in after["resultados"]:
    verification.append("| "+item["caso"]+" | "+("APROVADO" if item["passou"] else "FALHOU")+" |")
verification += [
    "", "## Reproduzir os testes", "",
    "Com os dois ZIPs originais na pasta originais, executar:",
    "", chr(96)*3+"bash",
    "python verificar_ajustes.py --script consolidar_seguro_residencial.py --originais originais --trabalho testes",
    chr(96)*3, "",
    "A reprodução dos três defeitos anteriores pode usar --script historico/consolidar_original.py e --fase essencial.",
    "Nesse caso, os três testes devem falhar, demonstrando os problemas anteriores.",
    "conferir_atualizacao.py compara a revisão com o ZIP anterior e verifica os dados preservados.",
    "Os casos comerciais da proposta de integração ainda dependem do contrato e do motor. Estes testes não os implementam.",
]
(out/"Verificacao_Independente.md").write_text("\n".join(verification)+"\n",encoding="utf-8")

# O manifesto exclui apenas ele próprio e os arquivos ZIP, para evitar autorreferência.
manifest={}
for path in sorted(out.rglob("*")):
    if path.is_file() and path.suffix.lower()!=".zip" and path.name!="Manifesto_SHA256.json":
        relative=path.relative_to(out).as_posix()
        manifest[relative]={"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
(out/"Manifesto_SHA256.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
archive=out/"Pacote_Completo_Seguro_Residencial.zip"
with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for relative in sorted([*manifest,"Manifesto_SHA256.json"]):
        z.write(out/relative,relative)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for relative,info in manifest.items():
        assert hashlib.sha256(z.read(relative)).hexdigest()==info["sha256"],relative
assert hashlib.sha256(args.pacote_anterior.read_bytes()).hexdigest()==previous_sha
print(json.dumps({"pacote":str(archive),"bytes":archive.stat().st_size,
                  "arquivos_no_zip":len(manifest)+1,"versao":"0.2.0",
                  "manifesto_verificado":True,"pacote_anterior_preservado":True},ensure_ascii=False))

