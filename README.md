# Banco de Dados e API Território - Time Vector

Datathon Proteção Inteligente - Ibmec / BB Seguros / Brasilseg. Desafio escolhido: Seguro Residencial.

Este repositório reúne a preparação da base residencial e uma API de contexto territorial. São componentes independentes: o pacote residencial v2 permanece preservado, enquanto a API é um extra funcional validado localmente. O motor de recomendação e a jornada Bússola estão no [repositório do MVP](https://github.com/tmzhenrique/BBDW-X-IBMEC).

## 1. Base residencial vigente

A referência ativa dos dados é a **v2**, com schema **0.2.0**. Cada linha representa um par cliente + imóvel; clientes com mais de um imóvel possuem linhas distintas.

| Base | Clientes na origem | Pares cliente + imóvel | Colunas |
| --- | ---: | ---: | ---: |
| Desenvolvimento | 2.200 | 2.578 | 200 |
| Teste Comum | 120 | 138 | 200 |

Os identificadores originais foram preservados. Os bens foram resumidos antes das junções, evitando multiplicação dos imóveis. Dados observados, derivados, estimados, declarados e controles mantêm suas naturezas e fontes identificadas.

Não foi estimada nova área na consolidação v2. Área ausente permanece desconhecida. Métodos de estimação implementados posteriormente no MVP devem ser avaliados por suas próprias versões e evidências. O experimento v3 descartado não integra a base ativa.

## 2. Organização dos arquivos

O pacote extraído está em [entregas/](https://github.com/fg9646/datathonBBseg/tree/main/entregas):

| Pasta | Conteúdo |
| --- | --- |
| 01_Tabelas_Finais | CSVs consolidados de Desenvolvimento e Teste Comum |
| 02_Scripts | Consolidação, verificações e organização do pacote |
| 03_Documentacao | Guia, dicionário, mapeamento, política e alinhamento de integração |
| 04_Qualidade | Relatórios e evidências da preparação dos dados |
| 05_Detalhes_e_Proveniencia | Bens detalhados e rastreabilidade dos valores |
| 06_Referencias | Orientações recebidas da equipe |
| 07_Historico | Código anterior preservado para rastreabilidade |

Comece pelo [LEIA-ME da v2](https://github.com/fg9646/datathonBBseg/blob/main/entregas/LEIA-ME.md) e pelo [guia de consolidação](https://github.com/fg9646/datathonBBseg/blob/main/entregas/03_Documentacao/Guia_Consolidacao_Seguro_Residencial.md).

## 3. Reprodução da consolidação

Requer **Python 3.10 ou superior**. Este componente utiliza somente a biblioteca padrão; suas dependências estão documentadas separadamente das da API.

Na raiz do repositório, coloque os dois ZIPs originais recebidos da organização na pasta `originais/`, sem modificar seus arquivos:

- Seguro_Residencial_Desenvolvimento.zip
- Seguro_Residencial_Teste_Comum.zip

Execute:

```bash
python entregas/02_Scripts/consolidar_seguro_residencial.py --entrada originais --saida resultados_reproduzidos
```

Para conferir os casos de regressão:

```bash
python entregas/02_Scripts/verificar_ajustes.py --script entregas/02_Scripts/consolidar_seguro_residencial.py --originais originais --trabalho testes_consolidacao
```

Para comparação byte a byte, use a mesma data de consolidação indicada no relatório de qualidade. As verificações do pacote demonstram integridade da preparação dos dados; não certificam as decisões do motor de seguros.

## 4. API de contexto territorial

A [API Território](https://github.com/fg9646/datathonBBseg/blob/main/api_territorio/README.md) permite consultar contexto municipal de clima, desastres e criminalidade, com fonte, período, método e limitações junto dos valores.

- Contrato JSON 1.0.0, por `POST /v1/enriquecimento/consulta`.
- Edição `territorio-2026-10-28-r1`: 10 municípios, 18 indicadores e 180 registros, com 153 valores e 27 ausências explícitas.
- SQLite local preparado a partir dos dados versionados. A consulta não acessa planilhas nem fontes externas em tempo real.
- Fontes documentadas: INMET, Atlas Digital de Desastres, IBGE e órgãos estaduais de segurança.
- Autenticação por consumidor e HTTPS fora do modo de desenvolvimento em loopback. Nenhuma chave real acompanha a entrega.

Os testes foram locais. Publicação, capacidade, latência de rede e integração com o motor são evoluções futuras. A API não participa das decisões do motor/Bússola nesta versão, e não há benefício de score comprovado por seu uso.

## 5. Executar e testar a API

A API tem ambiente próprio e dependências fixadas. **Python 3.12.14 foi testado**; as dependências atuais exigem no mínimo Python 3.11. Consulte a [execução local em PowerShell](https://github.com/fg9646/datathonBBseg/blob/main/api_territorio/docs/EXECUCAO_LOCAL.md) para a sequência completa, incluindo credencial temporária e inicialização do servidor.

Preparação básica no Windows:

```powershell
py -3.12 -m venv .venv
$python = Join-Path $PWD '.venv\Scripts\python.exe'
& $python -m pip install -r api_territorio/requirements-dev.txt
& $python -m pip check
& $python -m api_territorio.preparar_base
```

Conferências locais:

```powershell
& $python -m unittest discover -s tests -v
& $python -X utf8 auditoria/validar_congelar_base.py --verificar-integridade dados/edicoes/territorio-2026-10-28-r1
```

O teste HTTPS utiliza OpenSSL CLI para um certificado temporário; sem esse recurso, o teste é ignorado e a limitação deve ser registrada. Segredos gerados para demonstração não devem ser gravados em commits, PDFs ou logs.

## 6. Limitações, segurança e integração

Município, UF e código IBGE são referências reais do desafio. CEP, endereço e coordenadas são fictícios ou perturbados. A API usa o município e não identifica domicílios, comunidades ou elegibilidade individual.

Ausências são explícitas e não equivalem a zero ou baixo risco. Indicadores territoriais não são probabilidades de sinistro. Os períodos e métodos das fontes variam, e não há atualização automática.

O cadastro de seguro no nível do cliente não comprova seguro para cada imóvel. Declarações do cliente não são laudos nem confiança estatística de 100%. Regras e saídas de negócio devem permanecer explicáveis e associadas à versão dos dados utilizada.

Os CSVs consolidados são entradas de trabalho. Os templates oficiais de resultado e coberturas são saídas do motor, disponibilizadas e avaliadas no contexto do MVP e da pasta de entrega.

## 7. Documentação de referência

- [Contrato da API](https://github.com/fg9646/datathonBBseg/blob/main/api_territorio/docs/CONTRATO.md)
- [Fontes, indicadores e métodos](https://github.com/fg9646/datathonBBseg/blob/main/api_territorio/docs/DADOS.md)
- [Validação técnica e limites dos testes](https://github.com/fg9646/datathonBBseg/blob/main/api_territorio/docs/VALIDACAO.md)
- [Implantação opcional](https://github.com/fg9646/datathonBBseg/blob/main/api_territorio/docs/IMPLANTACAO.md)
- [Documentos e arquivos da entrega](https://drive.google.com/drive/folders/1JlDkNCBysBYXLBWHecneTqgFvjT-70qe)

Documentos de histórico e propostas anteriores são preservados como referência e não substituem automaticamente os contratos vigentes. Condições contratuais e orientações oficiais da Brasilseg/BB Seguros prevalecem em conflitos de produto.

## 8. Uso de IA e registro de alterações

ChatGPT apoiou a estruturação da base, elaboração e revisão de scripts, documentação, verificações e conversão documental. A equipe deve compreender, revisar, executar e defender a solução. Novas mudanças devem registrar fonte, método, versão e evidências.

Este README foi atualizado para a entrega documental de **29/10/2026**, esclarecendo as frentes de dados e API e os caminhos atuais do repositório. Não houve alteração dos CSVs da v2, dos indicadores territoriais, dos cálculos ou das regras do motor nesta atualização.
