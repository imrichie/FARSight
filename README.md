# FARSight

> RAG-powered tool for pilots — natural language questions, answers cited directly from the FAR/AIM.

![Status](https://img.shields.io/badge/status-in%20development-yellow)

---

## What It Does

FARSight lets pilots ask questions about FAA regulations and receive answers grounded directly in the source material. It searches across five regulatory documents — the Aeronautical Information Manual and 14 CFR Parts 61, 67, 71, and 91 — and returns a cited answer that identifies the exact section it came from. If a confident answer cannot be found in the source documents, FARSight says so clearly rather than guessing.

---

## Knowledge Base

| Document | Description |
|---|---|
| AIM | Aeronautical Information Manual |
| 14 CFR Part 61 | Certification of Pilots, Flight Instructors, and Ground Instructors |
| 14 CFR Part 67 | Medical Standards and Certification |
| 14 CFR Part 71 | Designation of Class A, B, C, D, and E Airspace Areas |
| 14 CFR Part 91 | General Operating and Flight Rules |

---

## Known Limitations

- **In development** — the application is not yet functional end-to-end.
- **No chat history** — FARSight is single-turn only. Each question is independent; there is no conversation memory.
- **FAR/AIM scope only** — questions outside the five source documents will not be answered. FARSight is not a general aviation assistant.
- **No flight planning or weather** — operational tools are outside scope by design.
- **UI unstyled** — the current interface is a minimal Streamlit shell pending a design handoff.

---

## Project Status

Work is tracked on the [GitHub Projects board](https://github.com/users/imrichie/projects/4). Issues are organized into six milestones covering ingestion, retrieval, generation, frontend, and validation.

---

## License

This project is for educational and portfolio purposes. FAA source documents are public domain.
