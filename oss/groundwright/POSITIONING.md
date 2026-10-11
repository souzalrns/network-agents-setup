# groundwright — positioning & competitive analysis

> Evidence-based, per the repo playbook (`docs/initiatives/REPO-EVAL-PLAYBOOK.md`).
> The honest question: *what do the others have that we don't, and what would make
> groundwright the recommended choice in its lane?*

## Background: this reverses RE1 (honestly)

The repo's earlier decision **RE1 = B** was *no-go as a product* for a **generic**
`rag-eval`: that market (ragas / deepeval / promptfoo) is saturated and the name
`rag-eval` is taken, and a generic answer-quality evaluator carries no differentiation.
That reasoning still holds — and is exactly why groundwright is **not** a generic RAG
evaluator. The maestro reopened the extraction ("avance com todos") and the honest way
to do it is to ship the **narrow thing we actually have an edge on**: a deterministic
**retrieval-provenance / grounding gate**, not an LLM-as-judge answer scorer.

## The lane

groundwright answers one question: **did retrieval return the expected source (and the
anchor chunk), and does the run still pass the regression threshold?** It is a
*retrieval-provenance gate*. It is **not** an answer-quality evaluator, **not** an
LLM-as-judge, **not** a benchmark harness.

## The competitors (and what each actually does)

### ragas
- **What it is:** RAG metrics (faithfulness, answer/context relevancy, context
  precision/recall) — mostly **LLM-as-judge**.
- **What it has that we don't:** answer-level semantic metrics, a big metric catalogue.
- **Why it is a different lane:** it scores whether the *answer* is faithful/relevant,
  usually by calling an LLM (cost, nondeterminism). groundwright asks the prior,
  deterministic question — *was the right source retrieved and attributable?* — with no
  LLM and a hard pass/fail gate.

### deepeval
- **What it is:** an LLM-eval test framework (pytest-style), many metrics incl. RAG.
- **What it has that we don't:** a test-runner UX, large metric set, integrations.
- **Why it is different:** again answer/metric-centric and largely LLM-judged.
  groundwright is a tiny deterministic gate you can run every commit without an LLM key.

### promptfoo
- **What it is:** prompt/eval harness with assertions and matrices.
- **What it has that we don't:** prompt matrices, providers, a UI.
- **Why it is different:** general prompt testing, not a retrieval-provenance contract
  with source-hit / anchor-chunk / provenance metrics and a regression threshold.

### "hit@k / MRR" on your own
- Rolling your own retrieval metrics is common — but you then also hand-roll provenance
  (does every hit carry a source? a uri?), the anchor-in-chunk check, the golden-set
  validation and the gate thresholds. groundwright is that, packaged, deterministic and
  retriever-agnostic.

## Where groundwright wins (and the evidence)

| Property | groundwright | ragas | deepeval | promptfoo |
|----------|--------------|-------|----------|-----------|
| Deterministic, **no LLM** in the loop | ✅ | ❌ (judge) | ❌ (judge) | ⚠️ |
| **Provenance** metrics (`provenance_ok`, v2 uri+metadata) | ✅ | ❌ | ❌ | ❌ |
| **source_hit@k** + **anchor-chunk** ranking | ✅ | ⚠️ context recall | ⚠️ | ❌ |
| **Regression gate** with explicit thresholds | ✅ | ⚠️ | ⚠️ | ⚠️ |
| Retriever-agnostic (a callable you pass) | ✅ | ⚠️ | ⚠️ | ⚠️ |
| Offline golden↔chunking anchor check | ✅ `anchor_errors` | ❌ | ❌ | ❌ |
| Zero dependency / zero cost per run | ✅ | ❌ | ❌ | ❌ |

The distinctive combination is **deterministic provenance + source/anchor ranking as a
regression gate, retriever-agnostic, no LLM, no cost**. The others judge the *answer*;
groundwright gates the *retrieval*.

## Honest limits (what groundwright does NOT do)

- **Not answer quality.** It does not tell you if the generated answer is correct or
  faithful — pair it with ragas/deepeval for that. It tells you if the *right source was
  retrieved*.
- **Needs a golden set.** You must author questions with an expected source and an anchor
  string. (That authoring cost is the price of determinism.)
- **Lexical anchor match.** The anchor is matched by normalized substring, not semantics;
  a paraphrased anchor won't match. (Deliberate: deterministic and cheap.)
- **Not a benchmark leaderboard.** It gates *your* retriever against *your* golden set.

## What would make it "more the choice" (roadmap, not claims)

- Loaders for golden sets in JSON/YAML (YAML optional, no hard dep).
- A `pytest` plugin so the gate is one assertion in a test suite.
- More ranking metrics (nDCG) behind the same gate contract.
