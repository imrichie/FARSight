# FARSight — Product Brief

## The problem

Pilots are legally responsible for knowing regulations that were never written to be read. The rules behind a single question — *"Can I carry a passenger at night?"* — are scattered across 14 CFR Parts 61 and 91 and the AIM, written in legal language, and organized the way lawyers organize things, not the way pilots ask questions.

Right now a student pilot has three options, and they're all bad:

1. **Ask your CFI.** Authoritative, but not available at 10 PM the night before a stage check.
2. **Search the FAR/AIM yourself.** Keyword search falls apart because pilots ask in plain English ("cloud clearance") while the regulation says something else ("distance from clouds").
3. **Ask ChatGPT.** You'll get a fluent answer with a citation that may or may not exist. In aviation, an answer you can't verify is an answer you can't use.

The gap isn't access — every pilot owns the FAR/AIM. The gap is getting from a plain-English question to the exact regulatory text that answers it, reliably enough to bet a checkride on.

## Who it's for

**Maya — the student pilot.** 24, about 35 hours into her Private Pilot License. She's studying for the written and the oral checkride. She doesn't have the mental map of where rules live yet, so she can't tell when an answer is incomplete. She needs answers she can check against the source, because her examiner is going to ask her to point to the regulation.

**Dan — the rusty-but-rated private pilot.** 41, flies about 50 hours a year. His questions are occasional and specific: currency, equipment, airspace. "Am I current to take passengers at night?" He knows the rules exist — he just needs the exact section, fast.

What they have in common: **the citation isn't a nice-to-have, it's the answer.** A response without a verifiable source is worth nothing to either of them.

## The one rule

> **Every answer is verifiable, or it doesn't ship.**

FARSight never asks to be trusted. Every answer shows the exact FAR/AIM section it came from, with the source text right there to check. And when the system can't ground an answer in the documents with confidence, it says so — plainly — instead of guessing. A correct "I couldn't find that" is a win. A confident made-up answer is the worst thing this product can do.

## What v1 does

- **Single-turn Q&A.** One question in, one cited answer out.
- **Knowledge base:** the AIM plus 14 CFR Parts 61, 91, 71, and 67. Versioned, with a "current as of" date shown to the user.
- **Grounded citations.** Every answer cites the exact section (e.g., *14 CFR § 91.215*). The citation comes from the retrieved document's metadata — the model never writes a section number itself.
- **An honest uncertainty state.** When retrieval confidence is too low, FARSight shows the "couldn't find a confident answer" state. It never guesses.
- **A responsive web app**, built to the FARSight Design System coming out of Figma.
- **Evaluation.** A ~50-question test query set with expected answers and citations, run automatically as a quality gate.

## What I'm not building (on purpose)

| Cut | Why |
|---|---|
| Chat history / multi-turn conversation | Doubles the retrieval and state complexity for marginal value. The core job is one question, one verifiable answer. |
| Accounts and personalization | Nothing in v1 needs to know who you are. Pure overhead. |
| Parts 121 / 135 / 141 | Commercial and flight-school ops are a different user with different stakes. Scope creep. |
| Weather, NOTAMs, flight planning | ForeFlight already does that job well. FARSight does regulations. |
| Multi-model selection | Which model to use is a product decision, not a user preference. One model, evaluated properly. |
| Native mobile apps | Responsive web covers how people actually study. |
| Legal advice | FARSight is a study aid. It shows you what the regulation says — it doesn't rule on whether your specific flight was legal. |

## How I'll know it works

All of this gets measured against the test query set, automatically, in CI.

| Metric | Target |
|---|---|
| **Citation accuracy** — the cited section actually contains the text behind the answer | ≥ 95% |
| **Answer correctness** — judged against the test query reference answers | ≥ 90% |
| **Correct refusal** — out-of-corpus questions hit the uncertainty state, zero made-up citations | 100% |
| **Retrieval hit rate** — the right source chunk shows up in the top results | ≥ 95% |
| **Latency** — question to full answer, p95 | < 10 s |

## What could go wrong (and what I'm doing about it)

- **The model makes up a citation.** It structurally can't — section numbers come from retrieval metadata, never from the model. Evaluation verifies this on every run.
- **Chunking breaks the legal structure.** A regulation separated from its exceptions changes meaning. We chunk along section boundaries — there's a dedicated decision note on this.
- **The regulations change.** The corpus is versioned, and every answer shows its "current as of" date.
- **People trust it too much.** The source excerpt is always right there to check, the study-aid disclaimer is persistent, and the system prefers saying "I'm not sure" over a shaky answer.

## Maybe later (parked, not promised)

Follow-up questions · ACS task cross-referencing for checkride prep · more Parts if people actually ask for them.
