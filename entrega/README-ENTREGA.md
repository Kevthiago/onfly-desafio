# Entrega — Consolidador de reservas de hotel (Onfly)

## Defeitos corrigidos

Cada defeito tem um commit próprio e um teste novo que falhava antes da correção.

| #  | Arquivo                                                         | Causa raiz                                                                                                                              |
| -- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| D1 | `src/onfly_report/repositories/csv_reservation_repository.py` | O leitor parava na 200ª linha (`if len(rows) == 200: break`), descartando as 100 reservas restantes do CSV real (300).               |
| D2 | `src/onfly_report/services/status_policy.py`                  | `is_billable` usava `status != "CANCELLED"`, deixando `NO_SHOW` (e qualquer status desconhecido) entrar nos totais.               |
| D3 | `src/onfly_report/services/stay_calculator.py`                | A conta subtraía `checkout.day - checkin.day` em vez das datas, e dava número negativo na virada de mês.                           |
| D4 | `src/onfly_report/services/currency_converter.py`             | A conversão dividia pela taxa em vez de multiplicar e passava por `float`.                                                           |
| D5 | `src/onfly_report/services/report_builder.py`                 | O ranking ordenava por `(amount, hotel_id)` em ordem crescente, em vez de valor decrescente com desempate por `hotel_id` crescente. |
| — | `src/onfly_report/services/currency_converter.py`             | Moeda sem taxa na tabela levantava `KeyError` (exit 1); agora vira `InputFileError` (exit 2, "moeda XXX sem taxa de câmbio").      |

A última linha não é um defeito do README, e sim uma decisão do autor: o README diz que todas as moedas do dataset
têm taxa, e o CLI devia tratar o caso como entrada inválida (exit 2). Ela só vale para reservas CONFIRMED, as únicas
que são convertidas; o autor decidiu não validar a moeda antes do filtro de status.

D1 não é detectado pelos 5 testes fornecidos (usam no máximo 4 linhas). Só apareceu rodando o CLI no CSV real.

## Como investiguei

1. Li o README, o código de `src/`, os testes e os dados. O README foi a fonte da verdade das regras.
2. Rodei o `pytest` (5 falhas) e agrupei as falhas por causa provável: noites, câmbio, status, ordenação.
3. Rodei o CLI na amostra `data/exemplo-validacao.csv` e comparei com a tabela do README campo a campo. Só as
   contagens de status batiam.
4. Auditei o código regra por regra. Cada suspeita foi confirmada **antes de mexer em código**, chamando a função
   isolada (por exemplo, `calculate_room_nights(2025-01-30, 2025-02-02, 1)` devolvia `-28`).
5. Escrevi um script independente em `Decimal` com as regras do README. Ele reproduziu a amostra exatamente e deu o
   valor esperado para o CSV real (300 / 235 / 1347 / 396170.00 / 294.11), usado como oráculo. Isso mostra
   que dados, regras e amostra do README são coerentes entre si, e que o defeito está no CLI.
6. Corrigi um defeito por vez, na ordem D3, D4, D2, D5, D1, depois a moeda sem taxa: teste novo falhando, correção
   mínima, `pytest`, amostra. A amostra só bate inteira depois de D2 a D5; cada passo foi validado pelo teste
   fornecido e pelo novo.
7. Dados, regras e testes fornecidos não precisaram mudar. Nenhum teste fornecido contradiz o README.

A análise completa feita antes das correções está em [ANALISE_INICIAL.md](ANALISE_INICIAL.md).

## Como validar

Pré-requisito: Python 3.11+.

**Linux/macOS**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

pytest -q
ruff check .

PYTHONPATH=src python -m onfly_report --input data/exemplo-validacao.csv --rates data/taxas_cambio.csv --output output/exemplo.json
PYTHONPATH=src python -m onfly_report --input data/reservas_hoteis.csv --rates data/taxas_cambio.csv --output output/report.json
```

**Windows (PowerShell)**

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

pytest -q
ruff check .

$env:PYTHONPATH = "src"
python -m onfly_report --input data/exemplo-validacao.csv --rates data/taxas_cambio.csv --output output/exemplo.json
python -m onfly_report --input data/reservas_hoteis.csv --rates data/taxas_cambio.csv --output output/report.json
```

### Valores esperados — amostra (`output/exemplo.json`)

Resumo impresso: `Reservas: 12 | Confirmadas: 9 | Noites: 28 | Total BRL: 7566.00`

| Campo                                                                | Valor                                                                                                 |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `total_reservations` / `confirmed` / `cancelled` / `no_show` | 12 / 9 / 2 / 1                                                                                        |
| `total_room_nights`                                                | 28                                                                                                    |
| `total_amount_brl`                                                 | `"7566.00"`                                                                                         |
| `average_nightly_rate_brl`                                         | `"270.21"`                                                                                          |
| `by_month`                                                         | 2025-01: 8 / 25 / `"6684.00"`; 2025-02: 1 / 3 / `"882.00"`                                        |
| `top_hotels`                                                       | H01 3 `"1200.00"`; H02 2 `"1084.00"`; H12 1 `"1000.00"`; H10 4 `"900.00"`; H09 3 `"882.00"` |

### Valores esperados — CSV real (`output/report.json`)

Resumo impresso: `Reservas: 300 | Confirmadas: 235 | Noites: 1347 | Total BRL: 396170.00`

| Campo                                                                | Valor                                                                                                                                                                                                                                                      |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `total_reservations` / `confirmed` / `cancelled` / `no_show` | 300 / 235 / 31 / 34                                                                                                                                                                                                                                        |
| `total_room_nights`                                                | 1347                                                                                                                                                                                                                                                       |
| `total_amount_brl`                                                 | `"396170.00"`                                                                                                                                                                                                                                            |
| `average_nightly_rate_brl`                                         | `"294.11"`                                                                                                                                                                                                                                               |
| `by_month` (reservas / noites / total)                             | 2024-12: 35 / 174 / `"61335.80"`; 2025-01: 37 / 235 / `"64662.89"`; 2025-02: 26 / 138 / `"45991.09"`; 2025-03: 39 / 215 / `"65984.99"`; 2025-04: 21 / 146 / `"31335.97"`; 2025-05: 39 / 196 / `"63507.98"`; 2025-06: 38 / 243 / `"63351.29"` |
| `top_hotels` (5)                                                   | H06 160 `"45165.46"`; H10 120 `"45041.69"`; H12 106 `"41647.69"`; H07 148 `"39920.52"`; H11 102 `"37455.69"`                                                                                                                                     |

Os valores do CSV real vêm do cálculo independente descrito acima e foram conferidos contra a saída do CLI; o README
não traz uma amostra oficial para esse arquivo.

Moeda sem taxa: troque `USD` por uma moeda ausente de `data/taxas_cambio.csv` numa **cópia** do CSV; o CLI sai com
código 2 e escreve em stderr `moeda GBP sem taxa de câmbio`.

## Resultado do `pytest` e do `ruff`

Saída real, em 2026-11-11, no `.venv` da raiz (Windows, Python 3.11.9, pytest 8.3.4, ruff 0.8.4):

```
$ pytest -q
.......................................                                  [100%]
39 passed in 4.42s

$ ruff check .
All checks passed!
```

39 testes: os 5 fornecidos e 34 novos, em `tests/test_*_extra.py`:

| Arquivo                        | Protege                                                                                         |
| ------------------------------ | ----------------------------------------------------------------------------------------------- |
| `test_nights_extra.py`       | D3: virada de mês e de ano, fevereiro, `rooms > 1`                                           |
| `test_currency_extra.py`     | D4: USD/EUR, exatidão decimal, BRL com taxa 1, arredondamento só no final                     |
| `test_status_extra.py`       | D2: CANCELLED/NO_SHOW só nas contagens, status desconhecido, período sem noites               |
| `test_top_hotels_extra.py`   | D5: empate por `hotel_id`, `--top 1`, `--top` maior que o nº de hotéis, ordem numérica |
| `test_truncation_extra.py`   | D1: 199, 200, 201, 250 e 300 linhas; linhas após a 200ª nos agregados                         |
| `test_missing_rate_extra.py` | moeda sem taxa: exit 2 e mensagem com a moeda; moeda com taxa: exit 0                           |

## O que não foi alterado

- Os testes fornecidos em `tests/` (`test_currency.py`, `test_nights.py`, `test_regression_report.py`,
  `test_status_rules.py`, `test_top_hotels.py` e `helpers.py`). Só foram adicionados arquivos novos.
- `data/reservas_hoteis.csv`, `data/taxas_cambio.csv` e `data/exemplo-validacao.csv`.
- O comando e os argumentos do CLI (`cli.py` não foi modificado) e o schema e a semântica do relatório.

Conferível com `git diff <commit inicial> --name-status -- tests data src/onfly_report/cli.py`: só aparecem
arquivos novos em `tests/` e nenhuma modificação nos demais.

Também foram adicionados `CLAUDE.md` e `.claude/settings.json` (configuração de assistente de IA) e a pasta `entrega/`.
Não foi adicionado log novo, nem validação que o README não peça.

## Uso de IA

Foi usado assistente de IA. Ver [uso-de-ia/declaracao.md](uso-de-ia/declaracao.md) e as sessões exportadas em
`uso-de-ia/`.
