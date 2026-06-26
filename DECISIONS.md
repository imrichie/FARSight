# Decisions

## Use React/Tailwind For The Frontend Demo

Problem: The original frontend issues named Streamlit, but the design system
already defines a React/Tailwind product shell with tokens, component anatomy,
lucide-react icons, and motion/react loading states.

Considered:
- Streamlit: fastest way to expose a Python UI, but it would orphan the design
  system and read like a technical prototype.
- React + TypeScript + Vite + Tailwind: more setup, but it directly implements
  the existing design system and presents FARSight as a polished product demo.

Picked: React + TypeScript + Vite + Tailwind for the frontend, with FastAPI
wrapping the existing Python retrieval/generation code in the next issue.

Why: This is still a portfolio demo, not SaaS. The app does not need accounts,
history, settings, analytics, or a database. It does need to feel like a real
product experience when a hiring manager opens it and tests the RAG system.
