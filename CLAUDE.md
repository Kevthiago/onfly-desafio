# Consolidador de reservas de hotel (Onfly) — Python 3.11, só stdlib

## Comandos
Use o Python do `.venv` da raiz (no Windows: `.venv\Scripts\python`; em Git Bash: `.venv/Scripts/python`).
O Python global não tem pytest. Em Linux/macOS, troque por `.venv/bin/python` (os demais argumentos são iguais).

- Testes: `.venv/Scripts/python -m pytest -q`
- CLI: `PYTHONPATH=src .venv/Scripts/python -m onfly_report --input data/reservas_hoteis.csv --rates data/taxas_cambio.csv --output output/report.json --top 5`
- Amostra: mesmo comando com `data/exemplo-validacao.csv` e `--output output/exemplo.json`; comparar com a tabela do README
- Lint: `.venv/Scripts/python -m ruff check .`

## Estrutura
`src/onfly_report/`: `cli.py` → `services/report_builder.py` (orquestra) → `repositories/` (leitura CSV) e
`services/` (`row_parser`, `status_policy`, `stay_calculator`, `currency_converter`).
`tests/` = testes fornecidos. `entrega/` = documentos da entrega (ANALISE_INICIAL.md, README-ENTREGA.md, uso-de-ia/).

## Regras (a fonte da verdade é o README)
- Só CONFIRMED é faturável. Noites = `(checkout - checkin).days * rooms`. Valor BRL = `amount * rate_to_brl`.
- `Decimal` sempre, nunca `float`. Arredondar só na serialização, 2 casas, half-up.
- `top_hotels`: `total_brl` decrescente, empate por `hotel_id` crescente. `by_month`: mês do check-in, ascendente.
- Saída: 0 ok, 2 entrada/argumento inválido, 1 erro inesperado.

## Nunca alterar
- Os testes fornecidos em `tests/` (5 arquivos `test_*.py` + `helpers.py`). Testes novos vão em `tests/test_*_extra.py`.
- `data/reservas_hoteis.csv`, `data/taxas_cambio.csv` e `data/exemplo-validacao.csv`.
- O comando e os argumentos do CLI, o schema e a semântica do relatório.
- Não fazer `git commit` nem `git push`: o autor faz todos os commits.

## Convenções
- Uma correção por vez: teste novo falhando → correção mínima → verde. Um commit por defeito.
- Não criar validações que o README não pede e não adicionar log novo.
- Defeito novo que viole o README: avisar (arquivo, linha, regra, causa em uma frase) antes de corrigir.
- Mensagens, docstrings e comentários em português.
