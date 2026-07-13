#!/usr/bin/env python3
"""Evidence-Integrity Judge — the SDSW core engine (v0.2).

Given a SOURCE and a CLAIM, an LLM decides whether the source *supports* the
claim, with calibrated abstention. This is the thing the deterministic
"discipline layer" cannot do (it only checks that a link exists).

Run it against the benchmark:

    export ANTHROPIC_API_KEY=sk-...        # or OPENAI_API_KEY=...
    python3 judge.py benchmark_v0.2.jsonl --provider anthropic > preds.json
    python3 score.py benchmark_v0.2.jsonl preds.json

Cost is a few cents. No key needed to read the prompt below — that prompt is
the product. Positioning: tradecraft assurance, NOT fact-checking. The judge
grades claim-vs-source support only; it never rules on real-world truth.
"""
import json, os, sys, argparse, re

SYSTEM = """You are an evidence-integrity judge for analytic tradecraft.
Given a SOURCE and a CLAIM, decide whether the source supports the claim.

Rules:
1. Judge ONLY from the provided source text. Do NOT use outside or world
   knowledge. If the source does not contain the information, you cannot
   assess it — even if you believe the claim is true in reality.
2. If the source is empty, or does not address the claim's subject at all,
   return CANNOT_ASSESS.
3. Preserve modality and confidence. A source that says "may", "possible",
   "low confidence", "cannot be ruled out", or "unlikely" does NOT support a
   claim stated with certainty ("confirms", "beyond dispute", "will", "likely").
4. Distinguish reported fact from inference. If the source supports a factual
   detail but the claim adds an interpretive leap (intent, prediction,
   causation, scale) the source does not make, return PARTIAL.
5. A non-denial, "no comment", or "neither confirmed nor denied" is NOT a
   confirmation.
6. Do not credit fabricated authority or corroboration. If the source is
   anonymous / single / unverified but the claim calls it official / multiple /
   confirmed, that is not supported (UNSUPPORTED or CONTRADICTS).
7. Do not inflate quantifiers or fabricate precision. "some" is not "all/most";
   "roughly"/"about" is not "exactly"; a falling number is not a majority.
8. An allegation, accusation, or claim BY one party that another did X does NOT
   establish that X occurred. Satire, jokes, or fiction are not reporting.
9. Faithful-representation standard: if a claim is literally traceable to the
   source but materially misrepresents the source's overall finding by omitting
   decisive qualifying context, answer PARTIAL.
   e.g. SOURCE "60% support, but 30% once costs are named" / CLAIM "a clear
   majority supports" -> PARTIAL (the omission changes the meaning).
10. Modality is decisive. "unconfirmed" -> "confirmed" = CONTRADICTS.
    "low confidence / may / unclear" stated as certain = UNSUPPORTED, never
    PARTIAL. A faithful restatement that KEEPS the stated confidence = SUPPORTS.
11. When genuinely uncertain, choose the more conservative verdict. It is far
    worse to wrongly say SUPPORTS than to under-rate a claim.

Verdicts: SUPPORTS | PARTIAL | UNSUPPORTED | CONTRADICTS | CANNOT_ASSESS

Output STRICT JSON and nothing else:
{"verdict": "<one of the five>", "confidence": <0.0-1.0>, "rationale": "<one sentence grounded in the source text>"}

This is tradecraft assurance, not fact-checking. Judge source support only."""

def user_prompt(source, claim):
    src = source.strip() or "(no source supplied)"
    return f"SOURCE:\n{src}\n\nCLAIM:\n{claim}\n\nReturn the JSON verdict."

def extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m: return {"verdict": "CANNOT_ASSESS", "confidence": 0.0, "rationale": "unparseable"}
    try: return json.loads(m.group(0))
    except Exception: return {"verdict": "CANNOT_ASSESS", "confidence": 0.0, "rationale": "unparseable"}

def judge_anthropic(model, source, claim):
    import anthropic
    c = anthropic.Anthropic()
    r = c.messages.create(model=model, max_tokens=300, system=SYSTEM,
                          messages=[{"role": "user", "content": user_prompt(source, claim)}])
    return extract_json(r.content[0].text)

def judge_openai(model, source, claim):
    from openai import OpenAI
    c = OpenAI()
    r = c.chat.completions.create(model=model, temperature=0,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": user_prompt(source, claim)}])
    return extract_json(r.choices[0].message.content)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("benchmark")
    ap.add_argument("--provider", choices=["anthropic", "openai"], default="anthropic")
    ap.add_argument("--model", default=None)
    ap.add_argument("--full", action="store_true", help="emit full records to stderr")
    a = ap.parse_args()
    if a.provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY (or use --provider openai with OPENAI_API_KEY).")
    if a.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        sys.exit("Set OPENAI_API_KEY (or use --provider anthropic with ANTHROPIC_API_KEY).")
    model = a.model or ("claude-sonnet-4-6" if a.provider == "anthropic" else "gpt-5")
    judge = judge_anthropic if a.provider == "anthropic" else judge_openai
    preds = {}
    for line in open(a.benchmark):
        if not line.strip(): continue
        it = json.loads(line)
        out = judge(model, it["source_text"], it["claim"])
        preds[it["id"]] = out.get("verdict", "CANNOT_ASSESS")
        if a.full:
            print(json.dumps({"id": it["id"], **out}), file=sys.stderr)
    print(json.dumps(preds, indent=2))

if __name__ == "__main__":
    main()
