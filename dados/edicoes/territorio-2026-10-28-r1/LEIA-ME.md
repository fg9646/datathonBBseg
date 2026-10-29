# Primeira edição da base Território

**Ponto 3 concluído: validação e congelamento dos dados. API não implementada.**

**Edição:** `territorio-2026-10-28-r1`. **Contrato de referência:** 1.0.0.

Validação concluída em 2026-10-28T23:40:33.295367+00:00. Fontes do levantamento anterior, com datas de coleta no arquivo fontes.csv. Nenhuma coleta nova nesta etapa.

Resultado: **153 valores disponíveis e 27 ausências explícitas**, em 180 pares município/indicador. Lacunas não foram preenchidas.

## Cobertura municipal

| Município | Disponíveis/18 | Chuva: dias completos | Roubo residencial 2025 | Furto residencial 2025 |
|---|---:|---:|---:|---:|
| Belo Horizonte | 14/18 | 99.4% (3993/4018) | Ausente | Ausente |
| Brasília | 16/18 | 98.4% (3955/4018) | 155 | Ausente |
| Curitiba | 18/18 | 89.4% (3591/4018) | 208 | 3222 |
| Fortaleza | 13/18 | 71.6% (2875/4018) | Ausente | Ausente |
| Goiânia | 14/18 | 91.7% (3686/4018) | Ausente | Ausente |
| Porto Alegre | 14/18 | 96.0% (3858/4018) | Ausente | Ausente |
| Recife | 14/18 | 59.0% (2371/4018) | Ausente | Ausente |
| Rio de Janeiro | 16/18 | 92.0% (3695/4018) | 253 | Ausente |
| Salvador | 16/18 | 97.2% (3905/4018) | 344 | Ausente |
| São Paulo | 18/18 | 97.0% (3896/4018) | 657 | 5193 |

## Conferências realizadas

- 1925 verificações aprovadas: resultados individuais em validacao.json.
- SHA-256 e tamanho de 151 arquivos originais conferidos; 108 arquivos horários reprocessados e comparados aos 40.180 dias do extrato.
- 80 normais anuais reconferidas nos arquivos INMET; cinco parâmetros integram o catálogo inicial.
- 60 indicadores de desastres recalculados a partir do Atlas original; 145 protocolos únicos no recorte completo dos dez municípios, incluindo tipologias fora do catálogo.
- Sete totais residenciais de 2025 reextraídos das fontes SP, PR, DF, RJ e BA; 49 grupos mensais conciliados com os totais processados.
- População 2025, ano, unidade, códigos e nomes municipais conferidos nos retornos IBGE arquivados; taxas recalculadas com o denominador correto.
- Os 180 valores e ausências foram comparados com a planilha entregue. Nenhum valor numérico alterado.
- 2.716 vínculos sintéticos validados quanto à unicidade e ao uso municipal; não publicados nesta edição.

## Lacunas e limites que permanecem

- Recife: 59,0% de dias completos para chuva. A301 sem arquivos de 2024 e 2025 no acervo; sem imputação ou troca automática de estação. A ausência na listagem original dos ZIPs não foi reconfirmada porque essa listagem não foi preservada.
- Fortaleza: normal anual de dias de chuva ≥50 mm ausente; valor null, FONTE_SEM_VALOR.
- Segurança: 13 dos 20 totais residenciais ausentes e, consequentemente, 13 taxas ausentes. Roubo disponível em SP, Curitiba, DF, RJ e Salvador; furto apenas em SP e Curitiba.
- Goiânia: publicação consultada estadual. Os quatro indicadores residenciais ficam null/FONTE_SEM_VALOR; números de Goiás nunca foram atribuídos ao município.
- Demais ausências residenciais: SEM_RECORTE_RESIDENCIAL. A disponibilidade refere-se aos arquivos consultados, não afirma inexistência de outras publicações oficiais.
- Rio: normais do Alto da Boa Vista e observações de Vila Militar, sem média espacial da cidade. Brasília representa todo o DF.
- Rajada máxima usa todas as horas válidas, inclusive dias incompletos; completude diária não é confiança estatística nem vento de projeto.
- Zero protocolos Atlas não comprova ausência do fenômeno; taxas criminais por habitantes não são probabilidades de sinistro. Não criar ranking entre estados sem harmonização.
- Datas de coleta originais têm precisão de dia. Horário UTC não foi inventado; eventual adaptação para o serviço será discutida na preparação da base operacional.

## Padronizações aplicadas, sem alterar valores

- Nomes anteriores mapeados para os 18 IDs do contrato em mapeamento_catalogo.csv; vendaval restrito ao COBRADE 13215.
- Cobertura de chuva/rajada mantida entre 0 e 1, com unidade fracao, corrigindo o rótulo antigo de porcentagem sem multiplicar valores.
- Contagens distinguem protocolos de desastres e ocorrências criminais; taxas usam ocorrencias/100mil_habitantes.
- JSON usa null para ausências. No CSV, campo numérico vazio acompanhado do motivo tem o mesmo significado; não interpretar como zero.

## Conteúdo, integridade e reprodução

- indicadores.json é o snapshot canônico; indicadores.csv facilita conferência. Não são banco operacional nem resposta de uma API.
- Os CSVs de suporte preservam os rótulos e estados históricos; a tradução para o contrato fica no catálogo e no arquivo de lacunas.
- manifesto.json identifica edição, períodos, arquivos e hashes; SHA256SUMS inclui também o hash do manifesto. Para verificar: executar o script de auditoria com --verificar-integridade apontando para esta pasta.
- A auditoria completa exige os arquivos originais locais e Python com pandas, openpyxl e pypdf. Não requer acesso à internet; inventário original localiza os brutos. URLs e hashes permitem conferir novos downloads, mas fontes oficiais podem ser revisadas posteriormente.
- Os arquivos brutos permanecem no acervo local anterior. Microdados criminais, endereços, IDs de clientes e imóveis não são incluídos neste snapshot nem publicados no GitHub.
- A edição não deve ser sobrescrita. Correções ou novas fontes geram outra edição, mantendo esta e seus hashes preservados no histórico Git.

## Próxima etapa

Ponto 4: preparar a base operacional de consulta a partir desta edição. Serviço HTTP, autenticação, hospedagem, motor e Bússola continuam sem implementação nesta frente.
