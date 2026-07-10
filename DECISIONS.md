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

## Break The ACR Pull Identity/Role-Assignment Circular Dependency

Problem: `hosting.bicep` originally granted the Container App's system-assigned
identity the `AcrPull` role by referencing `containerApp.identity.principalId`.
That made the role assignment implicitly depend on the Container App resource
reaching a terminal state. But the Container App listed the same ACR under
`registries`, so it couldn't reach a healthy terminal state without already
having that role. Neither side could go first — every deployment failed with
`Operation expired`, and `az role assignment list` on the ACR scope stayed
empty across multiple retries over several days. This was not an Azure AD
propagation delay; it was a genuine deadlock in the template.

Considered:
- Wait-and-retry: the first hypothesis, based on "Operation expired" often
  being a propagation timeout. Ruled out once the Container Apps system log's
  cumulative warning counter showed the same 401 climbing continuously for
  three days with no gap, and the role assignment never existed at all.
- Grant the role manually via CLI outside Bicep: works once, but leaves
  infrastructure-as-code incomplete and the same deadlock waiting for the
  next fresh deployment (e.g., a new environment).

Picked: a user-assigned managed identity (`acrPullIdentity`), created with no
dependency on the Container App. The `AcrPull` role assignment targets that
identity's principal ID instead, so it depends only on the identity and the
registry — both available immediately. The Container App then references the
already-permissioned identity via `identity.userAssignedIdentities` and
`registries[].identity`, with an explicit `dependsOn: [acrPullRoleAssignment]`
since nothing in its properties otherwise references that resource.

Why: this breaks the deadlock structurally instead of papering over it with
a retry — permissions now exist before anything tries to use them, on every
fresh deployment, not just this one.

## Trust `containerapp revision list`, Not The Deployment CLI Exit Code, For Scale-To-Zero Apps

Problem: after the fix above, `az deployment group create` still reported
`Operation expired`, which looked like the same failure recurring. Fresh logs
showed otherwise: no auth errors, a revision that had briefly failed its
readiness probe on cold start and then converged to `Healthy` / `Provisioned`
about 16 minutes later — after the CLI's own synchronous polling window had
already given up and reported failure.

Why this matters going forward: for a Container App with `minReplicas: 0`,
the deployment CLI's synchronous wait and the app's actual convergence to a
healthy revision are not guaranteed to stay in sync — a cold start can outlast
the CLI's patience even when the deployment is otherwise fine. Treat the CLI's
top-level exit code as a hint, not a verdict. Confirm real state with
`az containerapp revision list` (and, if needed, `containerapp logs show`)
before deciding a deployment actually failed.
