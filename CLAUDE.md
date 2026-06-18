# CLAUDE.md — FARSight

FARSight answers natural-language questions about FAA regulations with answers
cited directly from the source documents. It's a RAG system: Azure AI Search
finds the relevant regulation text, an LLM writes the answer from that text
only, and the citation comes from chunk metadata — never from the model.

This is a portfolio project. Quality and clarity beat feature count. The repo
itself is a deliverable — a hiring manager will read it.

## Stack

- Python 3.13, plain Python — **no orchestration frameworks** (no LangChain,
  no Semantic Kernel). Every step stays inspectable and explainable.
- Azure: AI Search (`srch-farsight`, free tier, westus2) and Azure OpenAI
  (`oai-farsight`, S0, westus — westus2 has no OpenAI models; that's
  deliberate). Resource group: `rg-farsight-dev`.
- Models: `text-embedding-3-small` (vectors) and `gpt-5.4-mini` (answers).
  Both declared in Bicep, pinned versions. Note: gpt-4o-mini was the original
  pick but Azure retired it 3/31/26 — hence gpt-5.4-mini.
- Bicep for all infrastructure (`infrastructure/`). GitHub Issues + Project
  board for all work tracking.
- Frontend: **undecided, parked.** Don't touch frontend issues or app.py.

## Where the project is

- **Milestone 1 (Foundation): done.** AI Search + Azure OpenAI provisioned via
  Bicep, both models deployed. #19 (CI auto-deploy) deferred until app deploy
  + eval gate land together.
- **Milestone 2 (Data Pipeline): done.** All five PDFs parsed, chunked,
  enriched, embedded, and persisted — 1,754 chunks in the index. Validated.
- **Milestone 3 (Query Path): done.** Hybrid retrieval + grounded answer
  generation with verbatim verification. Working end to end.
- **Next:** re-ingestion (fix title hyphenation + resolve storage ceiling,
  rebuild index clean), then Milestone 5 (Evaluation), then frontend + deploy.

## Commands

```bash
# Chunk the source PDFs (writes data/processed/chunks.json)
python3 -m src.data_pipeline.chunk_source_documents

# Embed + persist chunks to the index (live, costs ~2 cents, use caffeinate)
caffeinate -i python3 -m src.data_pipeline.chunk_persister

# Validate the index against chunks.json
python3 -m src.data_pipeline.validate_index

# Retrieve chunks for a question (CLI)
python3 -m src.regulation_retriever "when is a transponder required?"

# Full query -> cited answer (CLI)
python3 -m src.answer_generator "how long after drinking can I fly?"

# Tests — fast suite (mocked, no network)
python3 -m pytest tests/ -m "not integration"
# Tests — integration suite (hits live Azure)
python3 -m pytest tests/ -m integration

# Validate a Bicep file (always before deploying)
az bicep build --file infrastructure/<file>.bicep

# Deploy infra — RICHIE RUNS THIS, not you. Provide the command, stop.
az deployment group create --resource-group rg-farsight-dev --template-file infrastructure/<file>.bicep
```

## Architecture, short version

Two pipelines that meet at the search index:

- **Data pipeline** (offline, on demand): `src/data_pipeline/` — parse PDFs ->
  structure-aware chunking -> enrichment (metadata) -> embed -> persist to the
  `farsight-regulations` index. Each step writes its output to a file so it
  can be inspected before the next step runs.
- **Query path** (runtime): question -> embed -> hybrid search (vector + BM25,
  fused by RRF) -> generation grounded in retrieved chunks only -> answer with
  verbatim excerpt + citation assembled from chunk metadata.
  `regulation_retriever.py`, `answer_generator.py`.

Vocabulary follows Microsoft's RAG reference architecture: data pipeline,
chunking, enrichment, embedding, persistence, evaluation, test query set.
Don't reintroduce "ingestion", "harness", or "golden".

## Hard rules

- **The chunking spec is locked.** One CFR section per chunk; one AIM
  paragraph per chunk; oversized pieces split along the document's own
  structure (lettered paragraphs, then AIM numbered sub-items), parent
  header prepended. Any change needs Richie's explicit approval — flag,
  don't invent.
- **Citations never come from the model.** The model only points at which
  chunk answers the question; the section number is read off that chunk's
  metadata in code. The model never emits a section number.
- **Verbatim excerpts are verified in code.** The model's quote is checked
  against the source chunk; an unverified quote gets one corrective retry,
  then falls back to the uncertainty state. An unverified quote never
  reaches a user.
- **Secrets live in `.env` only** (gitignored). `.env.example` carries the
  variable names with blank values and must stay in sync. Never hardcode
  endpoints or keys. Current variables: AZURE_SEARCH_ENDPOINT,
  AZURE_SEARCH_SERVICE_NAME, AZURE_SEARCH_ADMIN_KEY, AZURE_OPENAI_ENDPOINT,
  AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT,
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT.
- **Failures visible, never silent.** Pipeline runs print summary stats and
  list anything skipped, dropped, or oversized.
- **Don't deploy infrastructure and don't run az deployment commands** —
  write the Bicep, give Richie the command, stop there.
- **One issue at a time.** Work the issue given; if you find adjacent
  problems, report them, don't fix them unprompted.
- **data/processed/ is gitignored** — generated output stays out of the repo;
  the scripts are the source of truth.

## Known limitations (documented, parked deliberately)

- **Refusal is too permissive.** The system can answer from surface-keyword
  matches that don't actually address the question (e.g. answering an
  airline-pilot rest question from section 91.1059, which is
  fractional-ownership rules). To be measured and tuned against the
  Milestone 5 evaluation, not guessed at now.
- **Storage ceiling.** The index is at the free tier's 50 MB limit; the next
  re-ingestion must resolve this (rebuild clean, shrink vectors, or move to
  Basic) before re-persisting.
- **Title hyphenation.** Section titles still carry print hyphenation
  ("Gen- eral"). Cosmetic, fixed in the upcoming re-ingestion.

## Conventions

- Descriptive naming, Apple style: files and functions read like sentences.
  No abbreviations.
- Docs and comments in a human voice — plain, direct, like explaining to a
  teammate. No enterprise jargon, no ceremony. Comments explain *why*, not
  what.
- PRs close their issue with "Closes #N" and describe what changed in plain
  language, including anything that went wrong and how it was handled.
- Big or risky work gets verified incrementally: do a slice, show stats and
  samples, wait for approval before extending.
- Decisions with alternatives get a short entry in DECISIONS.md
  (problem -> considered -> picked -> why).
- Tests split: mocked unit tests (fast, no network, CI-safe) vs.
  `@pytest.mark.integration` tests that hit live Azure.

## Pointers

- Product scope and the "not doing" list: `docs/product-brief.md`
- The test queries that define correctness: `docs/test-queries.md`
- Why things are the way they are: `DECISIONS.md`
- Design system for the eventual frontend: `docs/design-system.pdf`
