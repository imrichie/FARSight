# AGENTS.md — FARSight

Instructions for AI coding agents working in this repo.

Everything you need is in **[CLAUDE.md](./CLAUDE.md)** — project overview,
stack, current state, commands, architecture, hard rules, known limitations,
and conventions. Read it before doing anything. It's named for Claude Code
(the primary agent on this project) but every word applies to any tool.

The rules that matter most, repeated here in case you read nothing else:

1. **The chunking spec is locked** — flag proposed changes, don't invent them.
2. **Citations come from chunk metadata, never from a model.** The model only
   points at which chunk answers; code reads the section number off it.
3. **Verbatim excerpts are verified in code** — an unverified quote never
   reaches a user.
4. **Secrets live in `.env` only.** Never hardcode keys or endpoints.
5. **Don't run `az deployment` commands** — write the Bicep, hand Ricardo the
   command, stop.
6. **One issue at a time** — report adjacent problems, don't fix them unprompted.

Also see `docs/product-brief.md` (what we're building and deliberately not
building), `docs/test-queries.md` (the queries that define "working"), and
`DECISIONS.md` (why things are the way they are).
