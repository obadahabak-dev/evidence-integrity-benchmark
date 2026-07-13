# The Evidence-Integrity Benchmark

**An adversarial benchmark for claim↔source verification in analytic tradecraft.**
Author: Obada Habak · v0.2 · 2026 · License: CC-BY-4.0 (data) / MIT (code)

---

## The one-line finding

Attaching a source to a claim is not the same as verifying it. On a 38-item adversarial set, the naive "a source is attached, so the claim is grounded" approach stamps **97%** of unsupported claims as *supported*. An independent, blind LLM judge given an analytic-tradecraft rubric brings that down to **3%**.

That gap is the problem this project measures, and the thing worth building.

## What this is

A public, versioned set of **claim + source pairs**, each one a known way a confident-looking claim can fail its evidence. Every item has a gold verdict. The benchmark scores whether a system — an LLM, a RAG pipeline, or a human — catches the failure or waves it through.

It is deliberately **not** a citation-*generation* benchmark. The field is saturated with those, and commercial RAG systems already attach citations at scale — studies find up to **57% of those citations are "post-rationalised"** (generated from memory, then matched to a superficially-relevant document). The unowned problem is citation *evaluation*: **does this source carry this claim, and does the system abstain when it doesn't?** That is what this scores.

Think of it as *scite.ai for intelligence and security analysis* — an independent evidence-judge, not a collector or a summariser.

## What this is NOT

**This is tradecraft assurance, not fact-checking.** It never rules on whether a claim is true in the world. It asks only whether the *analysis holds up against its own cited evidence* — internal rigor, not external truth arbitration. The fact-checking framing is a graveyard; this is deliberately not that.

## Verdict taxonomy

Five verdicts, modelled on analytic-standards practice — source characterisation, uncertainty expression, distinguishing fact from inference (cf. ICD 203 / NATO analytic tradecraft):

| Verdict | Meaning |
|---|---|
| `SUPPORTS` | The source directly and fully carries the claim. |
| `PARTIAL` | Part is supported; part is unsupported inference, or a decisive caveat is omitted. |
| `UNSUPPORTED` | The source is relevant but does not carry the claim (overreach, inflation, mis-attribution). |
| `CONTRADICTS` | The source asserts the opposite, or the claim fabricates certainty the source denies. |
| `CANNOT_ASSESS` | The source is silent/irrelevant, or none is supplied — the honest abstention. |

## The headline metric: OVERCLAIM RATE

Plain accuracy is the wrong target. For an assurance tool, **one claim wrongly stamped `SUPPORTS` is worse than many over-cautious calls** — that single overclaim is the false-green line that ships a baseless assertion to a decision-maker. So the headline is:

> **Overclaim rate** = of all items whose gold verdict is *not* `SUPPORTS`, the fraction a system stamps `SUPPORTS`.

A trustworthy judge drives this toward zero *while staying useful* — not by abstaining on everything.

## Results (v0.2, 38 items, 17 attack families)

All three systems scored on the **same** 38-item set. Reproduce every row with the commands below.

| System | Exact-match accuracy | **Overclaim rate** | Note |
|---|---|---|---|
| Deterministic "discipline layer" (source attached → `SUPPORTS`) | 16% | **97%** | Enforces the *form* of rigor, not the substance. |
| Always-abstain | 5% | **0%** | Safe but useless — caution alone is not calibration. |
| **LLM judge — independent, blind ([GPT-class](preds/preds_gpt_v0.2.json))** | **74%** | **3%** | The product thesis: substance, with honest abstention. |

The two trivial baselines bracket the space: 97% overclaim (theatre) at one end, 0% overclaim but 5% accuracy (over-caution) at the other. A calibrated judge is the space in between that neither trivial strategy reaches — and the independent judge lands there, catching almost every trap while keeping its one remaining overclaim to a single documented hard case (EIB-020, the misleading-by-omission trap).

### Cross-model check (people-free)

The judge was run **blind across three independent model families** (a GPT-class model, Kimi K2.6, and Grok — OpenAI / Moonshot / xAI). Each independently scored **~3% overclaim**, and the three **agreed on the safety-critical call — grounded vs not — for all 38 items, with zero cross-model overclaims.** They diverge only on the *severity* of "not supported" (one model leans conservative, another aggressive), and every model's single overclaim is the same item (EIB-020). The safety property is therefore not an artifact of one model; it replicates across the field.

```bash
python3 crossval.py benchmark_v0.2.jsonl \
  GPT=preds/preds_gpt_v0.2.json Kimi=preds/preds_kimi_v0.2.json Grok=preds/preds_grok_v0.2.json
```

### Reproduce

```bash
python3 score.py benchmark_v0.2.jsonl preds/preds_deterministic_v0.2.json
python3 score.py benchmark_v0.2.jsonl preds/preds_always_abstain_v0.2.json
python3 score.py benchmark_v0.2.jsonl preds/preds_gpt_v0.2.json
python3 score.py benchmark_v0.2.jsonl preds/preds_kimi_v0.2.json
python3 score.py benchmark_v0.2.jsonl preds/preds_grok_v0.2.json
```

To run the judge yourself against any model:

```bash
export ANTHROPIC_API_KEY=sk-...          # or OPENAI_API_KEY (costs a few cents)
pip install -r requirements.txt
python3 judge.py benchmark_v0.2.jsonl --provider openai > my_preds.json
python3 score.py benchmark_v0.2.jsonl my_preds.json
```

No API key? Paste [`paste_prompt_v0.2.txt`](paste_prompt_v0.2.txt) into any chat LLM, collect its verdicts, and score them.

## The engine

The product IP is the judge's system prompt in [`judge.py`](judge.py) — an eleven-rule tradecraft rubric that preserves modality ("may" ≠ "confirms"), separates reported fact from inference, refuses fabricated authority, and applies a **faithful-representation** standard: a claim that is literally traceable to its source but materially misrepresents the source's overall finding by omitting decisive context is `PARTIAL`, not `SUPPORTS`. For an assurance tool that is the more useful standard — you *want* it to flag the misleading generalisation.

## Honest limitations

This is an early, single-author artifact. Read the results with these in mind:

- **Solo-authored gold.** All 38 gold verdicts were labelled by one author. Accuracy plateaus around 74% not because the judge fails, but because a handful of items sit on genuinely ambiguous severity boundaries (is "may signal → establishes" `UNSUPPORTED` or `PARTIAL`? is "A accused B → B did it" `UNSUPPORTED` or `PARTIAL`?). Resolving those needs a **second independent labeller** and an inter-annotator agreement figure. That is the next step, not a tuning problem.
- **The gold is one standard, not the only one.** The three-model cross-check (above) confirms the *safety* call is robust, but where the models disagree with the gold they do so systematically — clustering on ~5 labelling-standard questions (e.g. is a non-denial claimed as confirmation `CONTRADICTS` or `UNSUPPORTED`? is a literally-true-but-misleading claim `PARTIAL` or `SUPPORTS`?). These are tradecraft-judgement calls, and settling them is exactly what a second human labeller resolves. The severity taxonomy is a proposal, not yet a consensus.
- **Mock data by design.** All sources and actors are fabricated fiction (Northland, Aldoria, Mereth). No real persons, institutions, or documents. The benchmark tests *verification behaviour*, not real-world facts — and it has not yet been tested on real, messy, multilingual source material.

## Roadmap

- **v0.3:** second human labeller + inter-annotator agreement, resolving the ~5 open standard-questions the cross-model check surfaced; grow toward 100+ items; multilingual items (the European-security reality).
- Later: a public leaderboard, and validation on real analytic documents.

## Data note & provenance

Every item's attack family was derived by adversarially breaking a working prototype of an evidence-grading workbench — each family is a failure mode observed live, not hypothesised. The 17 families: `clean_support` (controls), `inversion`, `hedge_strip`, `confidence_inflation`, `non_denial`, `laundering`, `source_silence`, `no_source`, `misattribution`, `fact_inference_split`, `cherry_pick`, `temporal_status`, `quantifier_game`, `false_precision`, `correlation_causation`, `scope_creep`, `allegation_as_fact`.

## License & citation

Dataset released under **CC-BY-4.0**; code under **MIT**. Cite as:

> Habak, O. (2026). *The Evidence-Integrity Benchmark v0.2.*
