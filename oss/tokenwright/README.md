# tokenwright

**A token-cost ledger and a budget cap that refuses BEFORE you spend.**

Most cost tools tell you what a run cost *after* it ran. tokenwright does the two
things those tools don't:

1. **Fail closed on an unknown price.** If a model has no confirmed price, its cost is
   **not** silently treated as zero — `CostUnknown` is raised. You never under-count
   spend because a price was missing.
2. **A projective cap.** Before the next call, estimate its cost and **refuse it** when
   `spent + next > cap` (`BudgetExceeded`). The overrun is *prevented*, not reported.

```python
from tokenwright import prices_from_mapping, ledger_cost_usd, guard_next_call

prices = prices_from_mapping({
    "gemini-2.5-flash": {"usd_per_1m_input": 0.30, "usd_per_1m_output": 2.50},
})

spent = ledger_cost_usd("runs/42/token_usage.jsonl", prices)   # USD so far

guard_next_call(spent, projected_in=1200, projected_out=800,
                model="gemini-2.5-flash", prices=prices, cap_usd=0.05)
# returns the projected USD, or raises:
#   BudgetExceeded  if spent + projected would cross the cap
#   CostUnknown     if the model has no confirmed price (fail-closed)
```

Or from the shell:

```console
$ tokenwright cost runs/42/token_usage.jsonl --prices prices.json
0.013400
$ tokenwright check --spent 0.04 --in 1200 --out 800 --model gemini-2.5-flash \
      --prices prices.json --cap 0.05   # exit 1 if it would exceed
```

## The model

A ledger row is `{"model", "tokens_in", "tokens_out"?, "tokens_total"?}`. When
`tokens_total` is present, output is `tokens_total - tokens_in` — so **reasoning
tokens** (billed as output but not reported in `tokens_out`) are counted. Rows with no
tokens cost `0`. Prices are a plain mapping; load them from JSON, YAML or a database —
tokenwright stays zero-dependency.

| | tokenwright |
|---|---|
| Unknown price | **`CostUnknown`** (never silently 0) |
| Reasoning tokens | counted via `tokens_total - tokens_in` |
| Cap | **projective** — refuses the next call before it runs |
| Dependencies | none (pure stdlib) |

## API

- `prices_from_mapping(data) -> Prices` — keep only models with both prices confirmed
- `estimate_cost_usd(tokens_in, tokens_out, model, prices) -> float`
- `row_cost_usd(row, prices) -> float` · `ledger_cost_usd(path_or_rows, prices) -> float`
- `would_exceed(spent, next, cap) -> bool`
- `guard_next_call(spent, *, projected_in, projected_out, model, prices, cap_usd) -> float`
- `CostUnknown`, `BudgetExceeded`

## How it compares

See `POSITIONING.md` for the evidence-based comparison with `tokencost`, LiteLLM cost
tracking, Langfuse and Helicone — and why "measure after" is not the same as "refuse
before".

## Install

```console
pip install tokenwright
```

MIT licensed. Part of the [network-agents-setup](https://github.com/souzalrns/network-agents-setup)
ecosystem; extracted from its governed runner so any project can cap token spend by evidence.
