# Análise inicial — Consolidador de reservas de hotel (Onfly)

Sessão de análise e planejamento. **Nada foi corrigido**: nenhum arquivo do projeto foi alterado além deste.
O `git status` ficou limpo durante toda a sessão. O pytest rodou em um venv fora do repositório
(com `PYTHONDONTWRITEBYTECODE=1` e `-p no:cacheprovider`). As saídas do CLI foram gravadas em `/tmp`.

## 1. Resumo executivo

- Encontrei **5 defeitos independentes** no CLI, em 5 arquivos diferentes. Os 5 testes fornecidos falham, e cada um
  cai em um defeito, com sobreposição entre eles.
- Um dos defeitos (**D1**, truncamento em 200 linhas) **não é detectado por nenhum teste**. Os testes usam no máximo 4
  linhas. Ele só aparece ao rodar o CSV real, que tem 300 reservas e sai com `total_reservations = 200`.
- Dados e regras de negócio **não precisam mudar**. Um script independente, escrito do zero a partir das regras do
  README, reproduziu **exatamente** a amostra de validação (12/9/2/1, 28 noites, 7566.00, 270.21, `by_month` e
  `top_hotels`). Nenhum dos 5 testes contradiz o README.
- O código está bem separado em camadas (repositório → parser → serviços → builder), e cada defeito mora em uma função
  pequena. Cada correção é de 1 a 3 linhas e o risco é baixo.
- **Trecho já correto** (não mexer): `format_money` (quantize half-up), o fluxo da ordem de processamento, o parser
  de linha, `by_month` (mês do check-in, ordenado por `month`), `generated_at` com offset `-03:00`, argparse e códigos de saída.

## 2. Diagnóstico dos testes (`pytest -q`: 5 falhas, 0 passes)

| Teste | Falha observada | Causa provável |
|---|---|---|
| `test_nights_across_month_boundary` | `-28 == 3` | **D3** — `checkout.day - checkin.day` |
| `test_currency_conversion_to_brl` | total ≠ `642.00` | **D4** — divide pela taxa em vez de multiplicar, e usa `float` |
| `test_status_rules_exclude_cancelled_and_no_show` | `120.00 != 100.00` (o NO_SHOW de 20 entrou) | **D2** — `is_billable` só exclui `CANCELLED` |
| `test_top_hotels_are_ranked_descending` | `['H04','H03','H02']` em vez de `['H01','H02','H03']` | **D5** — ordem crescente |
| `test_regression_report_on_sample` | total `1018.45` ≠ `1542.00`; média `203.69` ≠ `308.40` | **D4** (câmbio). A conta de noites dá certo neste teste porque as datas ficam no mesmo mês, então não é D3. |

Nenhum teste cobre D1. Os testes não contradizem o README. Conferi cada valor esperado à mão: `1000 + 100×5.42 = 1542.00`;
`1542 / 5 = 308.40`; `100 + 100×5.42 = 642.00`.

## 3. CLI na amostra de validação vs. README

Comando: `python -m onfly_report --input data/exemplo-validacao.csv --rates data/taxas_cambio.csv --output /tmp/exemplo.json` (exit 0).

| Campo | Esperado | Obtido | OK? | Defeito |
|---|---|---|---|---|
| `total_reservations` | 12 | 12 | ✅ | |
| `confirmed_reservations` | 9 | 9 | ✅ | |
| `cancelled_reservations` | 2 | 2 | ✅ | |
| `no_show_reservations` | 1 | 1 | ✅ | |
| `total_room_nights` | 28 | **-33** | ❌ | D3 e D2 |
| `total_amount_brl` | 7566.00 | **5962.41** | ❌ | D4 e D2 |
| `average_nightly_rate_brl` | 270.21 | **0.00** | ❌ | D3. O total de noites ficou negativo, então a média cai no ramo "sem noites". |
| `by_month` 2025-01 | 8 / 25 / 6684.00 | 9 / **-36** / **5936.90** | ❌ | D2 (9 reservas em vez de 8), D3 e D4 |
| `by_month` 2025-02 | 1 / 3 / 882.00 | 1 / 3 / **25.51** | ❌ | D4. As noites ficam certas só porque a conta ainda cai no mesmo mês de calendário. |
| `top_hotels` | H01, H02, H12, H10, H09 | H09, H02, H05, H08, H07 | ❌ | D5 (ordem), D4 (valores), D2 (H05 é NO_SHOW e entrou) |

**Contagens de status batem** porque são calculadas antes do filtro. Todo o resto diverge.

**Execução no CSV real** (`data/reservas_hoteis.csv`, 300 linhas): o CLI reporta 200 reservas e 153 confirmadas, com
noites negativas (-1393). **Expectativa calculada de forma independente** com as regras do README: 300 reservas, 235 CONFIRMED,
1347 noites, `total_amount_brl = 396170.00`, média `294.11`, top 1 = H06 (45165.46). Esses valores servem como
**oráculo de validação** pós-correção; não há `expected` oficial para o CSV real.

## 4. Tabela de defeitos

| # | Arquivo:linha | Regra violada | Causa raiz (1 frase) | Como confirmar sem alterar nada |
|---|---|---|---|---|
| **D1** | `repositories/csv_reservation_repository.py:47-48` | "`total_reservations` = número de reservas no arquivo" | O leitor interrompe a leitura ao atingir 200 linhas (`if len(rows) == 200: break`), descartando as 100 restantes. | `python -m onfly_report` no CSV real: `total_reservations: 200`, e o arquivo tem 300 linhas de dados (`wc -l` = 301 com cabeçalho). |
| **D2** | `services/status_policy.py:8` | "Só `CONFIRMED` é faturável" | `is_billable` usa `status != "CANCELLED"`, deixando passar `NO_SHOW` (e qualquer status desconhecido). | `is_billable("NO_SHOW")` → `True` e `is_billable("XYZ")` → `True`; teste de status com `120.00` em vez de `100.00`. |
| **D3** | `services/stay_calculator.py:10` | `room_nights = (checkout - checkin).days * rooms` | Subtrai o *dia do mês* (`.day`) em vez de subtrair as datas, então vira o mês e gera número negativo. | `calculate_room_nights(2025-01-30, 2025-02-02, 1)` → `-28` (esperado 3); `(2024-12-30, 2025-01-02, 2)` → `-56` (esperado 6). |
| **D4** | `services/currency_converter.py:11` | `amount * rate_to_brl`, `Decimal` e nunca `float` | Divide pela taxa (operação invertida) e passa por `float`, perdendo exatidão (`Decimal(str(float(...)))`). | `convert_to_brl(100.00, USD, 5.42)` → `18.4501…` (esperado `542.00`); `0.10 / 3` → `0.03333333333333333`. |
| **D5** | `services/report_builder.py:91` | `top_hotels`: `total_brl` decrescente, empate por `hotel_id` crescente | A ordenação usa a chave `(amount, hotel_id)` em ordem crescente, quando o valor deveria ser decrescente e só o desempate crescente. | Teste do top: `['H04','H03','H02']`; na amostra, o primeiro é o hotel de menor valor. |

**Efeito em cascata** (não são defeitos próprios): `by_month`, `summary` e `average_nightly_rate_brl` saem errados por causa de D2/D3/D4.
Os testes e a amostra **não detectam** D1; só o CSV real revela.

**Observações de robustez** (fora do escopo dos 5 defeitos; precisam de decisão sua — ver seção 9):
- `report_builder.py:63` / `currency_converter.py:10`: `rates[currency]` levanta `KeyError` se a moeda não tiver taxa, e o CLI
  devolve **exit 1** (erro inesperado). O README diz "todas as moedas do dataset têm taxa", então não ocorre nos dados.
  Mas, se a moeda não tiver taxa, é "entrada inválida", o que sugeriria **exit 2**.
- `row_parser.py:34`: a moeda da reserva não passa por `.upper()`, mas o repositório de taxas usa `.upper()`. É inofensivo
  nos dados atuais (todas maiúsculas).
- Não há validação de `rooms < 1` nem de `checkout <= checkin`. Os dados são consistentes, e o README diz que
  falhas de formato são erro de arquivo; hoje só falhas de *parse* viram exit 2.

## 5. Dados e regras de negócio — confirmação

- `data/reservas_hoteis.csv`: 300 linhas; status CONFIRMED 235, NO_SHOW 34, CANCELLED 31; moedas BRL/USD/EUR (todas com taxa);
  `rooms` 1–3; nenhum `checkout <= checkin`; sem IDs duplicados; sem espaços sobrando; `hotel_name` consistente por `hotel_id`;
  check-ins de 2024-12 a 2025-06 (cobre virada de ano).
- `data/taxas_cambio.csv`: BRL 1.000000, USD 5.420000, EUR 5.880000.
- O script independente (Decimal, multiplicação, half-up) reproduz a amostra do README **campo a campo**. Isso valida
  dados, regras e amostra entre si. **Não há motivo para alterar dados nem regras.**
- Não achei empates de arredondamento (terceira casa = 5) nos totais, então half-up vs. half-even não distingue nada
  nos dados atuais. O teste de arredondamento precisa ser sintético.

## 6. Plano de correção

**Ordem proposta** (cada passo = 1 teste novo vermelho → correção mínima → verde; um commit por defeito):

1. **D3 (noites)**: `(checkout - checkin).days * rooms`. Zero dependências, e já deixa a amostra com 28 noites.
2. **D4 (câmbio)**: `amount * rates[currency]`, tudo em `Decimal`, sem `float`.
3. **D2 (status)**: `status == "CONFIRMED"`. Considerar um nome mais fiel (`is_billable` já serve) e comparar com o valor exato do CSV.
4. **D5 (ordenação)**: `key=lambda i: (-i[1]["amount"], i[0])`.
5. **D1 (truncamento)**: remover o `break` e o limite de 200. Fica por último porque o efeito só se vê com o CSV real.
6. Opcional, só após sua decisão: robustez da seção 4 (moeda sem taxa → exit 2).

**Riscos**
- D3 e D4 se mascaram mutuamente nos totais. Por isso o passo 1 vem sozinho, com o teste de noites isolado.
- D1 muda o conjunto de dados, então os números do CSV real só são comparáveis com o oráculo da seção 3 depois do passo 5.
- D5: lembrar que ordenar por `-Decimal` funciona, e **não** usar `reverse=True` (inverteria também o desempate por `hotel_id`).
- D4: manter `Decimal` do começo ao fim; arredondar **só** em `format_money`. Não quantizar por reserva (a soma de valores
  arredondados diverge da soma exata).

**Validação final**: `pytest -q` (5 originais + novos); CLI na amostra comparado campo a campo com o README;
CLI no CSV real comparado com o oráculo (300 / 235 / 1347 / 396170.00 / 294.11); `ruff check .`.

### Casos de borda e testes novos (arquivos novos `tests/test_*.py`, sem tocar nos fornecidos)

| Caso | Teste novo | Protege |
|---|---|---|
| Virada de mês e de ano | `2024-12-30 → 2025-01-02` = 3 noites | D3 |
| `rooms > 1` | 3 noites × 2 quartos = 6; o valor `amount` **não** é multiplicado por quartos | D3 |
| Moeda não-BRL | USD e EUR (`100 × 5.88 = 588.00`) | D4 |
| Precisão decimal | valor tipo `0.10` e taxa que gere resíduo de `float`; total exato em `Decimal` | D4 |
| Arredondamento half-up | valor que dê terceira casa 5 (ex.: `0.005` → `0.01`; `1.005` → `1.01`) e média com meio-centavo | `format_money` e média |
| Arredondamento só no final | duas reservas de `0.004` somam `0.008` → `"0.01"` (por reserva daria `"0.00"`) | D4 |
| Status | CANCELLED e NO_SHOW contam em `total_reservations` e nas contagens, mas não entram em noites, valor, `by_month` nem `top_hotels` | D2 |
| Empate no `top_hotels` | dois hotéis com o mesmo total: `hotel_id` crescente | D5 |
| `--top` maior que o nº de hotéis | `--top 10` com 3 hotéis devolve 3 itens | contrato |
| `--top 1` | devolve só o maior | D5 |
| Período sem noites | todas CANCELLED: `total_room_nights = 0`, `total_amount_brl = "0.00"`, `average = "0.00"`, `by_month = []`, `top_hotels = []` | contrato |
| `by_month` | ordenação ascendente e mês do **check-in** (estadia que vira o mês fica no mês de entrada) | contrato |
| Mais de 200 linhas | CSV sintético de 250 linhas; `total_reservations == 250` | D1 |
| Entradas inválidas (exit 2) | arquivo inexistente; coluna obrigatória ausente; data inválida; `rooms` não numérico; `--top 0`; `--top abc`; argumento obrigatório ausente | CLI |
| Formato do JSON | chaves exatas, `report_version == "1.0"`, dinheiro com 2 casas sem separador de milhar, `generated_at` com `-03:00` | contrato |
| Regressão no CSV real | totais do oráculo (300 / 235 / 1347 / 396170.00 / 294.11), só leitura dos dados | D1 e tudo mais |
| Regressão na amostra | teste que roda o CLI em `data/exemplo-validacao.csv` e compara com a tabela do README | todos |

Observação: esses testes novos ficam em arquivos próprios, ex.: `tests/test_nights_extra.py`, `tests/test_cli_exit_codes.py`.
O helper `tests/helpers.py` fornecido só serve para casos com exit 0 (ele faz `assert returncode == 0`), então os testes
de exit code chamam `subprocess` ou `main()` diretamente, sem alterar o helper.

## 7. Plano de configuração de desenvolvimento assistido por IA

O projeto é pequeno (~10 módulos de ~10–100 linhas, 5 testes, só stdlib). A configuração fica proporcional: **CLAUDE.md +
settings.json**, e nada além disso.

### 7.1 `CLAUDE.md` (enxuto, ~30 linhas)

```markdown
# Consolidador de reservas de hotel (Onfly) — Python 3.11, só stdlib

## Comandos
- Testes: `python -m pytest -q`
- CLI: `PYTHONPATH=src python -m onfly_report --input data/reservas_hoteis.csv --rates data/taxas_cambio.csv --output output/report.json --top 5`
- Amostra: mesma coisa com `data/exemplo-validacao.csv` e `--output output/exemplo.json`; comparar com a tabela do README
- Lint: `ruff check .`

## Estrutura
src/onfly_report/: cli.py → services/report_builder.py (orquestra) → repositories/ (CSV), services/ (row_parser,
status_policy, stay_calculator, currency_converter). tests/ = fornecidos. entrega/ = documentos de entrega.

## Regras (a fonte da verdade é o README)
- Só CONFIRMED é faturável. Noites = (checkout - checkin).days * rooms. Valor BRL = amount * rate_to_brl.
- Decimal sempre, nunca float. Arredondar só na serialização, 2 casas, half-up.
- top_hotels: total_brl decrescente, empate por hotel_id crescente. by_month: mês do check-in, ascendente.
- Saída: 0 ok, 2 entrada/argumento inválido, 1 erro inesperado.

## Nunca alterar
- Os testes fornecidos em tests/ (5 arquivos + helpers.py); testes novos vão em arquivos novos.
- data/reservas_hoteis.csv, data/taxas_cambio.csv (e data/exemplo-validacao.csv).
- O comando/argumentos do CLI e o schema/semântica do relatório.
- Não fazer commit nem push (o autor faz os commits).

## Convenções
- Uma correção por vez: teste novo vermelho → correção mínima → verde. Mensagens e docstrings em português.
```

### 7.2 `.claude/settings.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(python -m pytest:*)",
      "Bash(python -m onfly_report:*)",
      "Bash(PYTHONPATH=src python -m onfly_report:*)",
      "Bash(ruff check:*)",
      "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)"
    ],
    "deny": [
      "Edit(tests/helpers.py)",
      "Edit(tests/test_currency.py)",
      "Edit(tests/test_nights.py)",
      "Edit(tests/test_regression_report.py)",
      "Edit(tests/test_status_rules.py)",
      "Edit(tests/test_top_hotels.py)",
      "Edit(data/reservas_hoteis.csv)",
      "Edit(data/taxas_cambio.csv)",
      "Edit(data/exemplo-validacao.csv)",
      "Bash(git commit:*)",
      "Bash(git push:*)"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "python -m pytest -q -x", "if": "Edit(src/**)" }
        ]
      }
    ]
  }
}
```

Pontos de atenção:
- **Não** usar `Edit(tests/**)` no deny: bloquearia também os testes novos, que o README permite. Por isso os 6 arquivos
  fornecidos entram **um a um**. Se você preferir, a alternativa é mover os testes novos para `tests/extra/`.
- As regras de `Edit` do Claude Code não bloqueiam gravação feita por `Bash` (ex.: `sed -i`, `>`). Para os arquivos
  que não podem mudar, vale também deixar o CLAUDE.md explícito e conferir `git diff -- tests data` antes de cada commit.
- A sintaxe exata de `if` no hook e dos padrões de `Bash(...)` deve ser conferida contra a versão do Claude Code instalada
  (posso validar com o skill `update-config` quando você aprovar). O hook é **opcional**: rodar 5 testes leva ~1 s, então
  compensa; se atrapalhar, remova.
- `.claude/settings.local.json` já está no `.gitignore`. `settings.json` é compartilhável e pode ir no repositório público.

### 7.3 O que descartei (e por quê)

| Item | Decisão | Motivo |
|---|---|---|
| Slash commands (`/validate`, `/fix`) | descartado | Os 3 comandos cabem no CLAUDE.md, e um comando a mais só duplicaria isso. |
| Subagents (revisor, tester) | descartado | O projeto tem ~10 arquivos pequenos; o contexto cabe inteiro numa sessão, e um subagent partiria do zero a cada vez. |
| Plugins / MCP | descartado | Sem dependências externas, sem API, sem banco. |
| Skill própria | descartado | Não há procedimento repetível que justifique. |
| Hook de `ruff` | descartado | Rodar `ruff check .` na validação final já basta, e o ruído por edição não compensa. |
| Hook de bloqueio de `git commit` | descartado | A regra de `deny` já cobre. |

## 8. Plano de entrega (README)

```
entrega/
├── README-ENTREGA.md
└── uso-de-ia/
    ├── sessao-01.md   # /export desta sessão de análise
    ├── sessao-02.md   # /export da sessão de correção (e seguintes)
    └── declaracao.md
```

**`entrega/README-ENTREGA.md`** (escrito **depois** das correções, com os resultados reais):
1. **Defeitos corrigidos**: D1–D5 com a tabela da seção 4 (arquivo, causa raiz em **uma frase** cada).
2. **Como investiguei**: pytest agrupado por causa → CLI na amostra comparado campo a campo → auditoria regra por regra →
   cálculo independente em Decimal como oráculo → confirmação de cada defeito em isolamento, antes de mexer em qualquer código.
   Citar que D1 não era detectado pelos testes fornecidos e só apareceu no CSV real.
3. **Como validar**: comandos exatos (pytest, CLI na amostra, CLI no CSV real) e os valores esperados.
4. **Resultado do pytest**: saída real colada (`N passed`), incluindo os testes novos, mais o `ruff check`.
5. Nota sobre o que **não** foi alterado (testes, CSVs, CLI e schema).

**`entrega/uso-de-ia/`**
- `sessao-NN.md`: exportar com `/export` ao final de **cada** sessão (esta de análise vira `sessao-01`). Conferir o
  conteúdo exportado antes de publicar, pois o repositório será público (ex.: e-mail, caminhos locais, tokens).
- `declaracao.md`: ferramenta e modelo (Claude Code, extensão VS Code, modelo Claude Sonnet 5.5, `claude-sonnet-5-5`);
  **o que a IA fez** (leitura do código, execução de pytest/CLI, análise, proposta de correção, rascunho dos testes e
  documentos) e **o que você fez** (definiu os limites, revisou e aprovou o plano, executou/commitou as correções,
  decisões das seções 9, validação final). Preencher com o que de fato aconteceu, não com o planejado.

**Checklist final**: `PYTHONPATH=src python -m onfly_report ...` gera `output/report.json`; `pytest -q` verde;
`git diff -- tests data` vazio nos arquivos fornecidos; repositório público no GitHub; link enviado pelo formulário.
Observação: `output/*` está no `.gitignore` (exceto `.gitkeep`), então o relatório gerado não vai para o repositório.

## 9. Decisões suas e perguntas em aberto

1. **Moeda sem taxa**: hoje vira `KeyError` → exit 1. Devo tratar como entrada inválida (exit 2, mensagem clara)?
   *Recomendação:* sim, é mudança pequena e fica dentro do contrato; mas é **opcional** e não está nos 5 defeitos.
2. **Validações extras** (`rooms < 1`, `checkout <= checkin`, moeda em minúsculas, status desconhecido): endurecer
   ou manter o parser como está, já que o README garante dados consistentes? *Recomendação:* manter como está e só
   registrar um aviso (log) para status desconhecido.
3. **Status desconhecido** (ex.: `PENDING`): hoje conta em `total_reservations` e não em nenhuma contagem por status;
   com D2 corrigido, não é faturável. Está de acordo com o README?
4. **Testes novos**: ok colocá-los em `tests/test_*_extra.py` (arquivos novos na mesma pasta) ou prefere subpasta?
   Isso define as regras de `deny` da seção 7.2.
5. **Hook de pytest** após editar `src/`: quer ou prefere sem?
6. **Commits**: 1 commit por defeito (5 commits, mais fácil de explicar na entrega) ou um único commit?
   *Recomendação:* 1 por defeito + 1 de testes/documentos + 1 de configuração.
7. **Onde fica este `ANALISE_INICIAL.md`**: mantém na raiz, move para `entrega/`, ou não entra no repositório público?
8. **`data/exemplo-validacao.csv`**: tratar como somente leitura também? (o README só proíbe os dois outros CSVs).
9. **Exportação das sessões**: confirmar que você fará o `/export` de cada sessão, já que isso é feito por comando seu.
10. **Ambiente**: o `pytest` não estava instalado no Python global. Rodei num venv fora do repositório. Para a correção, você prefere
    criar o `.venv` do README na raiz (já está no `.gitignore`)?

---
**Parei aqui, aguardando sua aprovação.** Nenhuma correção foi aplicada e nada foi commitado.
