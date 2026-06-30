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

## Host The Demo With Vercel And Azure Container Apps

Problem: The deployed demo needs a public frontend and a FastAPI backend, but a
portfolio project should not pay for an always-on server sitting idle.

Considered:
- Azure App Service B1: simple and reliable, but Always On creates a standing
  monthly cost that is hard to justify for a demo.
- Azure Container Apps: keeps the FastAPI backend on Azure with the AI Search
  and OpenAI resources, while scale-to-zero avoids paying for idle compute.
- Vercel for the frontend: free, simple, and a standard fit for React/Vite.

Picked: host the React frontend on Vercel and the FastAPI backend on Azure
Container Apps. Backend images are stored in Azure Container Registry so the
Azure deployment path stays coherent.

Why: This keeps the cloud architecture easy to explain: Vercel serves the static
React app, Azure runs the AI-backed API, and Container Apps can cold start after
idle instead of billing for an always-on demo backend. Cold starts are acceptable
because demos can be warmed before use.
