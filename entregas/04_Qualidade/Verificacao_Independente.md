# Verificação independente — versão 0.2.0

- Antes: 0/3 casos essenciais aprovados no script recebido.
- Depois: 10/10 cenários artificiais aprovados no script corrigido.
- Testes usam cópias mínimas das fontes. Nenhum ZIP original foi alterado.
- Desenvolvimento: 2.578 linhas e 8.988 bens. Teste comum: 138 linhas e 494 bens.
- As duas bases têm as mesmas 200 colunas; são oito colunas novas e nenhuma coluna original removida.
- Chaves, ordem, atributos preexistentes e detalhe dos bens foram comparados com o pacote anterior.
- Mudanças esperadas nos metadados: versão do schema, hash do perfil e data parametrizada da consolidação.
- Reconciliação exata de valores cadastrados e ponderados; nenhuma diferença nas somas.
- As cinco contagens de confiança e as três contagens de probabilidade explicam todos os bens vinculados.
- 56988 registros de proveniência conferidos: 28450 cópias, 13580 somas e 14958 campos reservados vazios.
- Reexecução do script com mesmos ZIPs e parâmetros: todos os arquivos gerados comparados byte a byte.
- Os originais não contêm probabilidades ou confianças inválidas; as falhas anteriores foram reproduzidas somente em cópias artificiais.
- As lacunas cadastrais existentes foram registradas como ausências, sem aprovação/rejeição comercial ou P0 automático.
- Nenhuma área nova, prioridade de pergunta, score, plano ou cobertura foi calculada.

## Casos artificiais

| Caso | Resultado |
| --- | --- |
| material_e_padrao_vazios | APROVADO |
| probabilidade_fora_intervalo | APROVADO |
| confianca_nao_reconhecida | APROVADO |
| probabilidade_limites_ausencia_e_negativa | APROVADO |
| confianca_ausente_e_invalida | APROVADO |
| outros_marcadores_ausencia | APROVADO |
| bem_orfao_preservado_separadamente | APROVADO |
| mais_bens_nao_altera_schema_silenciosamente | APROVADO |
| nova_categoria_nao_altera_schema_silenciosamente | APROVADO |
| chave_duplicada_bloqueia_saida | APROVADO |

## Reproduzir os testes

Com os dois ZIPs originais na pasta originais, executar:

```bash
python verificar_ajustes.py --script consolidar_seguro_residencial.py --originais originais --trabalho testes
```

A reprodução dos três defeitos anteriores pode usar --script historico/consolidar_original.py e --fase essencial.
Nesse caso, os três testes devem falhar, demonstrando os problemas anteriores.
conferir_atualizacao.py compara a revisão com o ZIP anterior e verifica os dados preservados.
Os casos comerciais da proposta de integração ainda dependem do contrato e do motor. Estes testes não os implementam.
