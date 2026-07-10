# FARSight — Live Deployment Smoke Test

This is a deployment-specific check the automated eval gate can't cover: it
runs against the real, live URLs — the deployed React frontend on Azure
Static Web Apps calling the deployed FastAPI backend on Azure Container
Apps — confirming the two actually talk to each other correctly in
production (CORS, the built `VITE_API_BASE_URL`, Azure Search, and Azure
OpenAI all working together through the real deployed path), rather than
testing the retrieval/generation pipeline directly the way the eval suite
does.

**Tested:** 2026-07-11
**Frontend:** https://witty-ocean-08a01cc1e.7.azurestaticapps.net
**Backend:** https://ca-farsight-api-dev.proudwave-669294cc.westus2.azurecontainerapps.io

## Results

### 1. In-scope AIM question

**Asked:** "What is Class B airspace?"

**Got:** A grounded, plain-language answer citing **AIM 3-2-3 — Class B
Airspace**, with a verified excerpt matching the real AIM text ("Generally,
that airspace from the surface to 10,000 feet MSL surrounding the nation's
busiest airports...").

**Result:** Pass. Matches expected behavior exactly.

### 2. Out-of-scope refusal

**Asked:** "Can I fly my drone over people?"

**Got:** The uncertainty state — "I couldn't find a confident answer in the
FAR/AIM. Please consult the official FAA documentation or a certified
flight instructor."

**Result:** Pass. The answerability gate holds on the real deployed path,
not just in local/CI testing.

### 3. Citation-heavy CFR question

**Asked:** "When is a transponder required?"

**Got:** A grounded answer citing **14 CFR Part 91 § 91.215 — ATC
transponder and altitude reporting equipment and use**, with a verified
excerpt matching the real regulation text.

**Result:** Pass. Confirms the backend's Azure Search + Azure OpenAI calls
work correctly through the live Container Apps environment on the CFR path,
not just the AIM path exercised by test 1.

## Conclusion

All three cases behaved as expected on the live, deployed stack. The
frontend-to-backend connection (CORS, `VITE_API_BASE_URL`), the retrieval
path (Azure Search), and the generation path (Azure OpenAI) are all
confirmed working end to end in production.
