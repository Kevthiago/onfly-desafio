# Declaração de uso de IA

## Ferramenta e modelo

- Ferramenta: Claude Code (extensão do VS Code), usada na análise e na correção.
- Modelo: Sonnet 5.5, no nível médio.
- Ambiente: meu Claude Code pessoal tem o plugin "superpowers" instalado e habilitado, e ele vale para todos os meus projetos. Nesta sessão, o Claude Code carregou por conta própria a skill `systematic-debugging` desse plugin no início da análise. O plugin não faz parte do repositório: ele não está no CLAUDE.md nem no .claude/settings.json, e eu não o configurei para este desafio.
- Também usei o Claude em um chat separado, na preparação (abaixo).

## Preparação (chat separado, não exportado)

Antes de abrir o Claude Code, usei o Claude em um chat separado para planejar a abordagem). Nesse chat, o Claude
redigiu o prompt inicial e os prompts de cada etapa seguinte, revisou os relatórios e as saídas do Claude Code que
colei, recomendou respostas para as decisões em aberto e sugeriu as mensagens de commit. Eu li o material, decidi
o que aproveitar e enviei os prompts. Esse chat não está exportado nesta pasta.

Esse chat não está exportado porque a mesma conversa continuou depois com assuntos de outros projetos, sem relação com este desafio. O papel dele está descrito acima; tudo o que foi feito no repositório está na `sessao-01.md`.

## O que a IA fez

- Leu o README, o código, os testes e os dados (somente leitura) e rodou o pytest e o CLI.
- Agrupou as falhas por causa, comparou a saída do CLI com a amostra do README e auditou o código contra as regras.
- Achou os defeitos D1 a D5 e calculou, de forma independente, os valores esperados (amostra e CSV real).
- Escreveu o ANALISE_INICIAL.md, o CLAUDE.md e o .claude/settings.json.
- Para cada defeito (D3, D4, D2, D5, D1 e a moeda sem taxa), escreveu o teste novo, viu falhar, aplicou a correção
  mínima, rodou pytest, ruff e a amostra e sugeriu a mensagem de commit.
- Escreveu o rascunho do README-ENTREGA.md e desta declaração.

## O que eu fiz

- Defini os limites do trabalho (não alterar testes fornecidos, CSVs, comando e schema; análise antes de qualquer
  correção; nada de validações ou logs que o README não peça).
- Criei o ambiente Python, rodei os testes e a amostra por conta própria e conferi o git status e o git diff
  antes de cada commit.
- Revisei cada diff e aprovei cada etapa antes de seguir para a próxima.
- Aprovei as decisões da seção 9 da análise (moeda sem taxa, validações extras, local dos testes novos, hook de
  pytest, commits, localização da análise, uso do .venv), várias delas recomendadas pelo Claude no chat.
- Fiz todos os commits e o push (a IA foi configurada para não commitar).
- Reescrevi com minhas palavras o que achei necessário no README-ENTREGA.md e nesta declaração.
- Executei o /export da sessão.

## Sessões

- `entrega/uso-de-ia/sessao-01.md`: sessão única do Claude Code, do início ao fim do trabalho no repositório. Cobre:
  1. a análise inicial, somente leitura: leitura do repositório, pytest, comparação com a amostra do README, auditoria do código e geração do ANALISE_INICIAL.md;
  2. a criação do CLAUDE.md e do .claude/settings.json;
  3. as correções, uma por vez e cada uma com teste novo: D3 (noites), D4 (câmbio), D2 (status), D5 (ordenação do top_hotels), D1 (truncamento em 200 linhas) e a moeda sem taxa (exit 2);
  4. o rascunho dos documentos de entrega (README-ENTREGA.md, esta declaração e as notas no ANALISE_INICIAL.md).
     Os commits foram feitos por mim entre as etapas, fora da sessão.
- O chat de preparação descrito acima não está exportado.
