"""Organiza um pacote existente sem recalcular ou alterar os CSVs."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--entrada", type=Path, required=True, help="ZIP já gerado e validado")
parser.add_argument("--saida", type=Path, required=True, help="ZIP final, com v2, v3 etc. no nome")
parser.add_argument("--versao", default="v2", help="Versão da entrega, como v2 ou v3")
args = parser.parse_args()
if re.fullmatch(r"v[1-9][0-9]*", args.versao) is None:
    raise ValueError("Usar uma versão como v2, v3 ou v4.")
if args.entrada.resolve() == args.saida.resolve():
    raise ValueError("Entrada e saída devem ter caminhos diferentes.")
if not args.saida.stem.endswith("_" + args.versao):
    raise ValueError("O nome do ZIP de saída deve terminar em _" + args.versao + ".zip.")

FOLDERS = {
    "01_Tabelas_Finais": "Os dois CSVs consolidados",
    "02_Scripts": "Geração, conferência, testes e empacotamento",
    "03_Documentacao": "Guias, dicionário, mapeamento, política e schema",
    "04_Qualidade": "Relatórios, ocorrências, alertas e resultados dos testes",
    "05_Detalhes_e_Proveniencia": "Bens detalhados e rastreabilidade dos valores",
    "06_Referencias": "Markdown recebidos da equipe",
    "07_Historico": "Script antigo para reproduzir as falhas já corrigidas",
}

def destination(name):
    p = Path(name)
    leaf = p.name
    if any(part.lower() in ["historico", "07_historico"] for part in p.parts):
        return "07_Historico/" + leaf
    if any(part.lower() in ["referencias", "06_referencias"] for part in p.parts):
        return "06_Referencias/" + leaf
    if leaf.endswith("_Consolidado.csv"):
        return "01_Tabelas_Finais/" + leaf
    if leaf.endswith(".py"):
        return "02_Scripts/" + leaf
    if leaf.startswith("Bens_Detalhados_") or leaf == "Registro_Proveniencia_Estimativas_e_Area.csv":
        return "05_Detalhes_e_Proveniencia/" + leaf
    if leaf.startswith(("Relatorio_", "Resultados_Testes_", "Verificacao_")) or leaf in [
        "Alertas_Valores_Extremos.csv", "Ocorrencias_Qualidade_Dados.csv"
    ]:
        return "04_Qualidade/" + leaf
    if leaf in [
        "Dicionario_Colunas.csv", "Mapeamento_Origem_Destino.csv", "Alinhamento_Integracao.md",
        "Alteracoes_por_Markdown.md", "Guia_Consolidacao_Seguro_Residencial.md",
        "LEIA-ME_Pacote.md", "Politica_Validacao_Dados.json", "Schema_Base_Consolidada.json"
    ]:
        return "03_Documentacao/" + leaf
    raise ValueError("Arquivo sem pasta definida; revisar o mapeamento: " + name)

with zipfile.ZipFile(args.entrada) as original:
    if original.testzip() is not None:
        raise ValueError("ZIP de entrada com falha de integridade.")
    source_files = {n: original.read(n) for n in original.namelist() if not n.endswith("/")}
    manifest = json.loads(source_files["Manifesto_SHA256.json"])
    for name, info in manifest.items():
        if hashlib.sha256(source_files[name]).hexdigest() != info["sha256"]:
            raise ValueError("Hash de origem divergente: " + name)

result = {}
mapping = {}
for name, data in source_files.items():
    if name in ["Manifesto_SHA256.json", "LEIA-ME.md"]:
        continue
    target = destination(name)
    if target in result:
        raise ValueError("Dois arquivos teriam o mesmo destino: " + target)
    result[target] = data
    mapping[name] = target

# Os scripts anteriores continuam preservados; este script reproduz a organização.
organizer_name = "02_Scripts/organizar_pacote.py"
result[organizer_name] = Path(__file__).read_bytes()
quality_name = "04_Qualidade/Relatorio_Qualidade.json"
quality = json.loads(result[quality_name])
schema = quality["versao_schema"]
stamp = quality["relatorios"][0]["parametros"].get("data_consolidacao", "")
version = args.versao
readme = [
    "# Seguro Residencial — " + version, "",
    "Comece pelas tabelas finais. As demais pastas servem para documentação e conferência.",
    "Esta entrega reorganiza os arquivos da v2. O script e o schema de dados continuam em " + schema + ".",
    "Os CSVs, seus valores e as evidências anteriores foram preservados byte a byte; não houve novo cálculo.", "",
    "## Tabelas para uso", "",
    "- [Desenvolvimento: 2.578 linhas](01_Tabelas_Finais/Seguro_Residencial_Desenvolvimento_Consolidado.csv)",
    "- [Teste comum: 138 linhas](01_Tabelas_Finais/Seguro_Residencial_Teste_Comum_Consolidado.csv)",
    "- Ambas têm 200 colunas e uma linha por cliente + imóvel.", "",
    "## Onde encontrar cada coisa", "",
    "| Pasta | Conteúdo |", "| --- | --- |",
] + ["| " + folder + "/ | " + purpose + " |" for folder, purpose in FOLDERS.items()]
readme += [
    "", "## Documentos principais", "",
    "- [Alterações por Markdown](03_Documentacao/Alteracoes_por_Markdown.md)",
    "- [Guia da consolidação](03_Documentacao/Guia_Consolidacao_Seguro_Residencial.md)",
    "- [Dicionário das colunas](03_Documentacao/Dicionario_Colunas.csv)",
    "- [Alinhamento de integração](03_Documentacao/Alinhamento_Integracao.md)",
    "- [Relatório de qualidade](04_Qualidade/Relatorio_Qualidade.md)",
    "- [Verificação independente](04_Qualidade/Verificacao_Independente.md)", "",
    "## Executar os scripts", "",
    "Os comandos abaixo partem da raiz do ZIP extraído. Coloque os dois ZIPs originais numa pasta chamada originais.",
    "A geração produz uma pasta de trabalho plana; a organização do ZIP é uma etapa posterior.",
    "Nos documentos técnicos preservados, comandos com nomes curtos de scripts usam a pasta 02_Scripts como ponto de partida; ajuste os caminhos de entrada e saída.", "",
    chr(96)*3 + "bash",
    "python 02_Scripts/consolidar_seguro_residencial.py --entrada originais --saida resultados_reproduzidos" + (" --data-consolidacao " + stamp if stamp else ""),
    "python 02_Scripts/verificar_ajustes.py --script 02_Scripts/consolidar_seguro_residencial.py --originais originais --trabalho testes",
    chr(96)*3, "",
    "Para conferir um pacote recebido, conferir_atualizacao.py compara a pasta plana de resultados reproduzidos com o ZIP anterior.",
    "montar_pacote.py reúne resultados, referências e evidências num pacote intermediário.",
    "organizar_pacote.py separa esse pacote nas pastas e gera o manifesto com os caminhos finais:", "",
    chr(96)*3 + "bash",
    "python 02_Scripts/organizar_pacote.py --entrada pacote_intermediario.zip --saida Pacote_Completo_Seguro_Residencial_" + version + ".zip --versao " + version,
    chr(96)*3, "",
    "## Conferência e histórico", "",
    "Manifesto_SHA256.json está na raiz e contém o tamanho e o hash de cada arquivo, usando o novo caminho.",
    "O script ativo de consolidação está em 02_Scripts. O script antigo está em 07_Historico e serve somente para reproduzir os defeitos anteriores.",
    "A organização não executa o motor, não estima áreas e não altera os resultados de validação.",
]
result["LEIA-ME.md"] = ("\n".join(readme) + "\n").encode("utf-8")
new_manifest = {
    name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    for name, data in sorted(result.items())
}
result["Manifesto_SHA256.json"] = json.dumps(new_manifest, ensure_ascii=False, indent=2).encode("utf-8")

args.saida.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(args.saida, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name in sorted(result):
        info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, result[name], compresslevel=9)

with zipfile.ZipFile(args.saida) as archive:
    assert archive.testzip() is None
    for name, info in new_manifest.items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == info["sha256"], name
    for old_name, target in mapping.items():
        assert archive.read(target) == source_files[old_name], old_name
    assert {n.split("/")[0] for n in archive.namelist() if "/" in n} == set(FOLDERS)
    assert {n for n in archive.namelist() if "/" not in n} == {"LEIA-ME.md", "Manifesto_SHA256.json"}
    final_tables = [n for n in archive.namelist() if n.startswith("01_Tabelas_Finais/")]
    assert len(final_tables) == 2
print(json.dumps({"arquivo": str(args.saida), "versao_entrega": version, "versao_schema": schema,
                  "pastas": list(FOLDERS), "arquivos": len(result),
                  "arquivos_originais_preservados": len(mapping), "tabelas_finais_inalteradas": True,
                  "manifesto_verificado": True, "bytes": args.saida.stat().st_size}, ensure_ascii=False))

