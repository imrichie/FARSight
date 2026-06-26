# FARSight Frontend

React + TypeScript + Vite shell for the FARSight demo experience.

This is the mock-only UI for Issue #14. It implements the design-system tokens,
core screens, loading state, cited-answer state, and out-of-scope refusal state
without calling the backend yet. API wiring belongs to Issue #15.

## Commands

```bash
npm install
npm run dev
npm run build
npm run lint
```

Run `npm run dev -- --host 127.0.0.1 --port 5173` to match the local review
URL used during visual QA.
