# FARSight

![Status](https://img.shields.io/badge/status-deployed-green)

An AI that answers aviation regulation questions is only useful if you can
trust it enough to bet a checkride on the answer. This is what it took to
build one you actually can.

![FARSight answering a question about Class B airspace, showing a grounded
answer, an official citation, and a verified excerpt](./docs/hero.png)

## What this is

FARSight is a RAG system that answers plain-English questions about FAA
regulations — the AIM and 14 CFR Parts 61, 67, 71, and 91 — and cites the
exact section it pulled the answer from, every time. Ask it something
outside that scope and it says so, instead of guessing.

It's built for student and rusty pilots who need an answer they can verify,
not just one that sounds right.

👉 [Live Demo](https://witty-ocean-08a01cc1e.7.azurestaticapps.net)

## How it works

Two pipelines meet at a search index:

- **Data pipeline** (offline): five source PDFs → structure-aware chunking
  (one regulation section per chunk, splitting only along the document's
  own internal structure) → metadata enrichment → embeddings → persisted
  to Azure AI Search.
- **Query path** (runtime): question → hybrid retrieval (vector + keyword,
  fused by RRF) → an answerability gate decides if this is even in scope →
  generation grounded only in the retrieved text → citation assembled from
  chunk metadata → the model's quoted excerpt verified against the source
  before it ever reaches a user.

Plain Python throughout — no orchestration framework — so every step stays
inspectable.

## Notable engineering decisions

A few things worth knowing if you're reading the code, not just the demo:

- **The model never writes a citation.** It only points at which retrieved
  chunk answered the question — the section number is read off that
  chunk's metadata in code. A model that's never asked for a citation
  can't fabricate one.
- **Every quoted excerpt is verified before it ships.** The "verbatim"
  quote is checked against the source chunk as a real, continuous span. An
  unverified quote gets one retry, then an honest "I'm not sure" — never a
  guess dressed up as a fact.
- **Chunking respects the regulation's own structure**, not a fixed token
  count. A rule split from its exceptions changes its legal meaning, so
  chunk boundaries follow the document's actual sections and paragraphs.
- **A correct refusal counts as a win.** The system is evaluated on
  refusing out-of-scope questions as rigorously as it's evaluated on
  answering in-scope ones.
- **Every pull request runs the full evaluation suite** — 50 real test
  questions, scored on retrieval accuracy, citation accuracy, answer
  correctness, and refusal behavior — and merges are blocked if any
  question that used to pass starts failing, even if the aggregate score
  looks unchanged.

## Stack

Python · Azure AI Search · Azure OpenAI · React + TypeScript + Vite +
Tailwind · FastAPI · Azure Container Apps · Azure Static Web Apps · Bicep
(infrastructure as code) · GitHub Actions (evaluation gate + CI/CD)

## Running it locally

### Backend

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your own Azure Search / OpenAI values
```

Build the search index (one-time, or after changing source documents):

```bash
python3 -m src.data_pipeline.chunk_source_documents
python3 -m src.data_pipeline.reset_index
python3 -m src.data_pipeline.search_index_manager
python3 -m src.data_pipeline.chunk_persister
python3 -m src.data_pipeline.validate_index
```

Run the API:

```bash
uvicorn src.api:app --reload --port 8000
```

Ask it something directly, no frontend needed:

```bash
python3 -m src.answer_generator "when is a transponder required?"
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
python3 -m pytest tests/ -m "not integration"      # fast, no Azure calls
python3 -m pytest tests/ -m integration             # hits live Azure
python3 -m evaluation.eval_runner                   # full evaluation suite
```

## Deployment

Backend runs on Azure Container Apps (scale-to-zero), built and deployed
via GitHub Actions using OIDC — no stored cloud credentials. Frontend
deploys to Azure Static Web Apps the same way. Infrastructure is Bicep,
applied manually and reviewed by hand; CI is deliberately scoped to ship
application updates only, never to change infrastructure unattended.

Every merge to `main` that touches the pipeline runs the full evaluation
suite against a committed baseline before it's allowed to land.

## The deeper story

👉 [Live Demo](https://witty-ocean-08a01cc1e.7.azurestaticapps.net)

The decisions above are the short version. The full case study — including
the evaluation process, the failures that shaped it, and the tradeoffs
behind them — is here: [Case Study](https://imrichie.github.io/farsight-case-study/)
