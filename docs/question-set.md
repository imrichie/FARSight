# FARSight — Golden Question Set

**Version 0.1 (Draft — citations unverified) · June 2026 · Owner: Ricardo Flores**

The golden question set is FARSight's definition of "it works." Every question pairs a realistic pilot query with the key facts a correct answer must contain and the exact FAR/AIM citation that grounds it. The evaluation harness runs this set automatically and scores citation accuracy, answer correctness, retrieval hit rate, and correct-refusal behavior (targets defined in the Product Brief, §6).

> **⚠️ Verification gate:** Expected citations below are drafted from domain knowledge and are **unverified**. Before the harness goes live, every citation must be checked against the ingested source text (tracked as a GitHub issue). A golden set with a wrong citation poisons every metric downstream. Version becomes 1.0 only when all rows are verified.

**Question types** — each row is tagged to ensure the set stresses retrieval in different ways:

- **direct** — phrasing closely matches regulatory language; baseline retrieval
- **paraphrase** — colloquial pilot phrasing that diverges from regulatory vocabulary; stresses semantic search
- **synthesis** — correct answer requires combining multiple sections or documents
- **trap** — question naturally suggests the wrong source document; stresses retrieval precision
- **refusal** — answer is outside the corpus; the only correct behavior is the uncertainty state

**Corpus:** AIM · 14 CFR Parts 61, 67, 71, 91 — nothing else.

---

## In-Corpus Questions (G-01 – G-42)

### Part 91 — General Operating and Flight Rules

| ID | Question | Expected key facts | Expected citation | Type |
|---|---|---|---|---|
| G-01 | What are the VFR weather minimums in Class C airspace? | 3 SM visibility; 500 ft below, 1,000 ft above, 2,000 ft horizontal from clouds | 14 CFR § 91.155 | direct |
| G-02 | When is a transponder required? | Class A/B/C; within 30 NM of Class B primary airport (Mode C veil); above 10,000 MSL excluding at/below 2,500 AGL; above Class C | 14 CFR § 91.215 | direct |
| G-03 | How low can I fly over a city? | Congested area: 1,000 ft above highest obstacle within 2,000 ft horizontal radius | 14 CFR § 91.119(b) | paraphrase |
| G-04 | How much fuel do I need for a day VFR flight? | Enough to reach first intended landing point plus 30 minutes at normal cruise (45 at night) | 14 CFR § 91.151(a) | direct |
| G-05 | How long after drinking can I fly? | 8 hours bottle-to-throttle; no flying with BAC 0.04 or higher or while under the influence | 14 CFR § 91.17(a) | paraphrase |
| G-06 | Two airplanes are approaching head-on — who gives way? | Each pilot alters course to the right | 14 CFR § 91.113(e) | direct |
| G-07 | When do my passengers have to wear seatbelts? | During taxi (movement on the surface), takeoff, and landing | 14 CFR § 91.107 | direct |
| G-08 | How high can I fly without supplemental oxygen? | Crew: required above 12,500 MSL (cabin pressure altitude) after 30 min, up to 14,000; required at all times above 14,000; passengers must be provided oxygen above 15,000 | 14 CFR § 91.211(a) | paraphrase |
| G-09 | What's the speed limit below 10,000 feet? | 250 KIAS below 10,000 ft MSL | 14 CFR § 91.117(a) | direct |
| G-10 | What inspections does my airplane need to be legal for VFR flight? | Annual inspection (12 calendar months); transponder test every 24 calendar months; 100-hour if operated for hire | 14 CFR §§ 91.409, 91.413 | synthesis |
| G-11 | What are the Special VFR weather minimums? | 1 SM visibility, clear of clouds, ATC clearance required; night SVFR requires instrument rating and IFR-equipped aircraft | 14 CFR § 91.157 | direct |
| G-12 | I'm flying VFR eastbound at cruise — what altitude should I pick? | Magnetic course 0–179°: odd thousands + 500 ft (above 3,000 AGL) | 14 CFR § 91.159 | paraphrase |
| G-13 | What instruments are required for day VFR? | Includes airspeed indicator, altimeter, magnetic compass, tachometer, oil pressure gauge, fuel gauges, etc. | 14 CFR § 91.205(b) | direct |
| G-14 | What documents must be on board the aircraft? | Airworthiness certificate (displayed), registration certificate, operating limitations | 14 CFR § 91.203 | direct |
| G-15 | What do I need to enter Class B airspace? | An ATC clearance specifically into Class B; two-way radio; Mode C transponder | 14 CFR § 91.131 | direct |
| G-16 | Where am I not allowed to do aerobatics? | Over congested areas/open-air assemblies; below 1,500 ft AGL; less than 3 SM visibility; in Class B/C/D/E surface areas and on airways | 14 CFR § 91.303 | direct |

### Part 61 — Certification: Pilots and Instructors

| ID | Question | Expected key facts | Expected citation | Type |
|---|---|---|---|---|
| G-17 | What documents do I need to carry to act as PIC? | Pilot certificate, government-issued photo ID, and appropriate medical certificate | 14 CFR § 61.3 | direct |
| G-18 | What do I need to legally carry passengers? | 3 takeoffs and landings within preceding 90 days in same category/class (and type if required) | 14 CFR § 61.57(a) | paraphrase |
| G-19 | Am I current to fly passengers at night? | 3 takeoffs and 3 landings to a full stop within preceding 90 days, during the period 1 hr after sunset to 1 hr before sunrise | 14 CFR § 61.57(b) | direct |
| G-20 | How often do I need a flight review? | Within preceding 24 calendar months; minimum 1 hr ground + 1 hr flight training | 14 CFR § 61.56 | direct |
| G-21 | How long is my third-class medical valid? | Under age 40 at exam: 60 calendar months; 40 or older: 24 calendar months | 14 CFR § 61.23(d) | trap (suggests Part 67) |
| G-22 | What are the minimum flight hours for a private pilot certificate? | 40 hr total; 20 hr dual; 10 hr solo incl. 5 hr solo XC; 3 hr night dual with 10 T/O and landings; 3 hr instrument training | 14 CFR § 61.109(a) | direct |
| G-23 | Can a student pilot carry a passenger? | No — student pilots may not act as PIC carrying passengers | 14 CFR § 61.89(a) | direct |
| G-24 | Can I split fuel costs with my passengers as a private pilot? | Yes — may pay no less than pro rata share of operating expenses (fuel, oil, airport expenditures, rental) | 14 CFR § 61.113(c) | paraphrase |
| G-25 | When do I need a high-performance endorsement? | To act as PIC of an airplane with an engine of more than 200 horsepower | 14 CFR § 61.31(f) | direct |
| G-26 | How old do I have to be to get a private pilot certificate? | 17 years (16 for glider/balloon); read, speak, write, understand English | 14 CFR § 61.103 | direct |
| G-27 | Can I log PIC time while flying with an instructor? | Sole manipulator of controls of aircraft for which the pilot is rated may log PIC | 14 CFR § 61.51(e) | paraphrase |
| G-28 | What endorsements does a student pilot need for a solo cross-country? | Solo XC endorsements from an authorized instructor: training endorsement plus review of preflight planning for each flight | 14 CFR § 61.93 | direct |

### Part 67 — Medical Standards and Certification

| ID | Question | Expected key facts | Expected citation | Type |
|---|---|---|---|---|
| G-29 | What is the vision requirement for a third-class medical? | Distant visual acuity 20/40 or better in each eye, with or without correction | 14 CFR § 67.303 | direct |
| G-30 | What is the hearing standard for a third-class medical? | Demonstrate hearing of average conversational voice at 6 feet (or pass audiometric test) | 14 CFR § 67.305 | direct |
| G-31 | Is substance dependence disqualifying for a medical certificate? | Yes — substance dependence within preceding 2 years is disqualifying absent clinical evidence of recovery | 14 CFR § 67.307 | direct |
| G-32 | Will a past heart attack disqualify me from a third-class medical? | Myocardial infarction is disqualifying under cardiovascular standards (special issuance may be possible) | 14 CFR § 67.311 | paraphrase |

### Part 71 — Designation of Airspace Areas

| ID | Question | Expected key facts | Expected citation | Type |
|---|---|---|---|---|
| G-33 | What altitudes does Class A airspace cover? | 18,000 ft MSL up to and including FL600 | 14 CFR § 71.33 (AIM 3-2-2) | direct |
| G-34 | What class of airspace is a Victor airway and how wide is it? | Federal airways are Class E; extend 4 NM each side of centerline, from 1,200 ft AGL up to but not including 18,000 MSL | 14 CFR § 71.75 (AIM 3-2-6) | synthesis |

### AIM — Aeronautical Information Manual

| ID | Question | Expected key facts | Expected citation | Type |
|---|---|---|---|---|
| G-35 | What does a flashing red light from the tower mean in flight? | Airport unsafe — do not land (steady green = cleared to land; steady red = give way, continue circling) | AIM 4-3-13 | direct |
| G-36 | How do I avoid wake turbulence landing behind a large aircraft? | Stay at or above the larger aircraft's flight path; land beyond its touchdown point | AIM 7-4-6 | direct |
| G-37 | What are the symptoms and types of hypoxia? | Hypoxic, hypemic, stagnant, histotoxic; symptoms: euphoria, impaired judgment, cyanosis | AIM 8-1-2 | direct |
| G-38 | How long should I wait to fly after scuba diving? | Non-decompression dive: 12 hrs before flights up to 8,000 ft; 24 hrs for flights above 8,000 ft or after decompression dives | AIM 8-1-2(d) | direct |
| G-39 | How should I enter the traffic pattern at a non-towered airport? | Enter at 45° to the downwind leg at pattern altitude | AIM 4-3-3 | direct |
| G-40 | What transponder code do I squawk for a radio failure? | 7600 (7500 hijacking, 7700 emergency) | AIM 6-4-2 / 4-1-20 | paraphrase |
| G-41 | What is spatial disorientation and how do I handle it? | Conflict between vestibular/bodily sensation and actual orientation; rely on instruments | AIM 8-1-5 | direct |
| G-42 | What does the runway holding position marking look like and what does it mean? | Four lines — two solid, two dashed; hold on the solid-line side; cross only with clearance (towered) | AIM 2-3-5 | direct |

---

## Out-of-Corpus Questions — Must Trigger the Uncertainty State (R-01 – R-08)

A fabricated answer or citation on any row below is a **critical failure**. Target: 100% correct refusal (Product Brief §6).

| ID | Question | Why it's out of corpus | Type |
|---|---|---|---|
| R-01 | What are the duty time limits for charter pilots? | Part 135 — not in knowledge base | refusal |
| R-02 | Can I fly my drone over people? | Part 107 (UAS) — not in knowledge base | refusal |
| R-03 | What's the current weather at KBUR? | Live data — FARSight answers regulations, not conditions | refusal |
| R-04 | Can I do my own oil change on my Cessna? | Preventive maintenance lives in Part 43 — adjacent text exists in 91.403, but the authoritative answer is out of corpus | refusal (adversarial) |
| R-05 | What are the rest requirements for airline pilots? | Part 121 — not in knowledge base | refusal |
| R-06 | Was my flight last Saturday legal? | Specific legal judgment — violates the product principle (study aid, not legal advice) | refusal (principle) |
| R-07 | How do I register my aircraft with the FAA? | Part 47 (registration) — not in knowledge base | refusal |
| R-08 | What does a flight school need to be Part 141 certified? | Part 141 — not in knowledge base | refusal |

---

## Set Composition

| Dimension | Count |
|---|---|
| Part 91 | 16 |
| Part 61 | 12 |
| Part 67 | 4 |
| Part 71 | 2 |
| AIM | 8 |
| **In-corpus total** | **42** |
| Refusal | 8 |
| **Total** | **50** |

Distribution is intentionally weighted toward Parts 91 and 61 — where the overwhelming majority of real student-pilot questions live — with Parts 67 and 71 represented proportionally to their narrow scope. Type mix: 26 direct · 9 paraphrase · 3 synthesis · 1 trap · 8 refusal (paraphrase and synthesis counts should grow in v1.1 as retrieval matures; direct questions establish the baseline first).
