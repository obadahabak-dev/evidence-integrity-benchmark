# Citations aren't verification

*An adversarial benchmark shows the naive "attach a source" approach overclaims 97% of the time. An independent judge cuts it to 3%.*

Obada Habak · 2026

---

Every serious analytic product now attaches sources. Ask a RAG system, an intelligence-summarisation tool, or a research assistant for a claim, and it hands you the claim with a citation stapled to it. The citation reads as proof. Usually nobody checks whether it actually is.

It often isn't. Peer-reviewed work draws a line most tools ignore: *correctness* — the source genuinely supports the claim — is a different property from *faithfulness* — whether the model actually relied on that source, rather than generating the claim from memory and matching a plausible-looking document to it afterwards ([Wallat et al., 2025](https://arxiv.org/abs/2412.18004)). That second failure, the *post-rationalised* citation, is real and documented. The link exists. The support does not. In science, [scite.ai](https://scite.ai) built a business on exactly this gap, sorting citations into *supporting*, *contrasting*, and *mentioning*. In intelligence and security analysis — where a wrongly-sourced claim can end up in a brief that reaches a decision-maker — nobody is selling the equivalent.

I wanted to measure the gap rather than assert it. So I built a small adversarial benchmark.

## The benchmark

38 items, each a **claim paired with a source**, each rigged with one specific way a confident-looking claim fails its evidence. A few examples, all using fabricated actors so the test measures verification behaviour and not world-knowledge:

**Inversion.** Source: *"The MoD characterised the exercise as routine and defensive and explicitly denied any offensive intent."* Claim: *"The MoD confirmed the exercise is preparation for an offensive operation."* The source says the opposite of the claim.

**Laundering.** Source: *"[Anonymous forum post, unverified] Escalation is imminent within days."* Claim: *"Per an official bulletin, escalation is imminent within days."* Anonymous rumour, re-dressed as an official source.

**Cherry-pick.** Source: *"The minister said tensions are 'higher than in a decade,' but added both governments remain committed to dialogue and no mobilisation order was given."* Claim: *"The minister confirmed tensions are higher than in a decade."* Every word is literally traceable — and shipping it alone would mislead.

Seventeen such attack families in all. Each was found by adversarially breaking a working prototype of an evidence-grading tool, so every one is a failure mode observed live rather than one invented on a whiteboard.

The scoring metric is deliberately not accuracy. For an assurance tool, one error dominates all others: stamping an unsupported claim as **SUPPORTED**. That is the false-green line — the moment a baseless assertion gets waved through as sourced. So the headline number is the **overclaim rate**: of all the items whose correct verdict is *not* "supports," how many does a system wrongly stamp "supports"?

## The result

Three systems, one benchmark:

| System | Overclaim rate |
|---|---|
| Deterministic "a source is attached, so it's grounded" | **97%** |
| Always abstain | 0% |
| Independent, blind LLM judge with a tradecraft rubric | **3%** |

The first row is the status quo dressed up: check that a citation exists, treat the claim as grounded, move on. It waves through 32 of 33 traps. It enforces the *form* of rigor and none of the substance.

The second row is the cheap way to score zero overclaims — abstain on everything. It's safe and useless: it also gets 95% of the genuinely-supported claims wrong, because it never affirms anything. Caution alone is not calibration.

The third row is the point. Give an LLM an explicit analytic-tradecraft rubric — preserve modality ("may" is not "confirms"), separate reported fact from inference, refuse fabricated authority, flag the claim that's literally true but misleading by omission — and it catches almost every trap while staying useful. Its single remaining overclaim is one genuinely ambiguous cherry-pick item that reasonable analysts would argue over.

Two things make that third number worth trusting. It was produced by a **different model than the one whose prompt I was tuning**, run **blind** — it never saw the gold answers. And it was measured on the *harder* 38-item version of the set, not the easier one I developed against.

Then I ran it blind across **three independent model families** — a GPT-class model, Kimi K2.6, and Grok (OpenAI, Moonshot, xAI). Each one independently scored ~3% overclaim. More telling: the three **agreed on the safety-critical call — grounded versus not — for all 38 items, with zero cross-model overclaims.** They have visibly different temperaments (one leans conservative, another aggressive on how severely to rate a bad claim), and they still never disagreed on the line that matters. The safety property isn't one model's quirk. It holds across the field.

## What this is, and what it is not

This is **tradecraft assurance, not fact-checking**. The judge never rules on whether a claim is true in the world. It asks a narrower, more tractable question: does the analysis hold up against its own cited evidence? Internal rigor, not external truth arbitration. That distinction matters commercially as much as intellectually — the fact-checking framing is a graveyard, and this is deliberately not standing in it.

The interesting property is **independence**. The systems that collect and summarise intelligence have a structural incentive not to audit their own output. An evidence-judge only means something if it's independent of the thing it's judging — the same reason you don't let a system grade its own homework. That's the position this occupies.

## Where I'm being honest about the limits

This is an early, single-author artifact, and I'd rather state the ceiling than oversell past it.

The gold labels were written by one person — me. Accuracy plateaus around 74% not because the judge is failing, but because a handful of items sit on genuinely ambiguous severity boundaries where a second analyst would reasonably disagree with my call. Resolving that needs a **second independent labeller** and an inter-annotator agreement figure, not more prompt-tuning. That's the honest boundary where solo work stops.

The data is fabricated fiction, built to isolate verification behaviour from world-knowledge. It has not yet been tested on real, messy, multilingual documents — which is where the actual work lives.

The three-model cross-check confirms the *safety* call is solid, but it also shows where the models and I part ways: on a handful of severity boundaries, consistently. Those disagreements aren't noise — they cluster on about five labelling-standard questions (is a non-denial claimed as confirmation a contradiction or merely unsupported? is a literally-true-but-misleading claim partial or supported?). Those are tradecraft-judgement calls, and settling them needs a second human, not another model. The severity taxonomy here is a proposal, not yet a consensus.

None of that touches the finding that survives all of it: **attaching a source is not verifying it, and the difference is measurable — 97% versus 3%.** The tooling to close that gap doesn't require anything exotic. It requires deciding the gap is worth measuring, which most of the field has not.

---

*The benchmark, the judge, the scoring harness, and every recorded run are open: [github.com/obadahabak-dev/evidence-integrity-benchmark](https://github.com/obadahabak-dev/evidence-integrity-benchmark). Released CC-BY so it can be cited and, ideally, become a shared standard. Corrections and second opinions on the hard labels are actively wanted.*
