# Preparation Plan

Three groups. Each item has a status tag.

- **[READY]** – can be prepared now by anyone. No team agreement needed. Treat as a proposal.
- **[TEAM]** – the team must decide before or during implementation.
- **[GAP]** – nobody in the team knows. Only Ecurious, the organiser or GoingElectric can answer.

First check gap **C1**: if code made before the event is not allowed, all A items stay documents.

---

## A. Prepare now [READY]

| # | Item | Content | Status | File |
|---|---|---|---|---|
| A1 | Reservation state machine | States, transitions, triggers | Draft done | `design/state-machine.md` |
| A2 | Hardware adapter contract | `reserve`, `release`, `status`, `onPlateEvent`: inputs, outputs, errors | In state machine draft; refine on site | `design/state-machine.md` |
| A3 | Mock hardware behaviour | Simulated delays, plate events, errors so the frontend can start before credentials. Also the demo fallback (switchable, labelled) | Not started | `hackathon-playbook.md` §1 |
| A4 | Demo and test scenarios | Happy path + edge cases, each with steps and expected result | Draft done | `design/test-scenarios.md` |
| A5 | Documentation template | Deliverables 3 and 5 sections | Done | `templates/documentation.md` |
| A6 | GDPR data inventory | Data item, purpose, retention, legal basis | Structure in doc template; values = B6 | `templates/documentation.md` |
| A7 | KPI and pricing parameters | Names only, no values | In doc template | `templates/documentation.md` |
| A8 | Standards mapping | Endpoints ↔ OCPP `ReserveNow` / `CancelReservation`; check OCPI command names | Not started | – |
| A9 | GoingElectric check | Terms of use, API key needed?, lead time. Request key now if needed | Done. Key required; terms forbid backend cache (client fetches, max 24 h). Key not yet requested | `design/goingelectric.md` |
| A10 | Pitch outline | One section per scoring criterion | Done | `templates/pitch-outline.md` |
| A11 | Mentor questions | Group C below | Done | this file |
| A12 | Declaration log | AI tools, libraries, data sources, pre-event material | Done | `templates/declaration-log.md` |

## B. Team decides [TEAM]

Record each decision in `templates/decision-log.md`.

| # | Decision | Options | Blocks |
|---|---|---|---|
| B1 | Tech stack and app type | Web or mobile; language, framework, hosting. Options A/B/C + out-of-scope list: `design/stack-options.md` | All code |
| B2 | Roles | Integration/backend, frontend, business/docs/pitch. Combine with 2 people | Work split |
| B3 | Mission areas: deep / light / pitch-only | Proposal: deep = No-Shows, Blocked Bays, Plate Recognition; light = Business Case, Interoperability | Scope |
| B4 | No-show rules | Grace period, reminder time, auto release, fee amount and cap, who pays | Timers, pricing |
| B5 | Blocked-bay policy | Action per case (combustion / EV not charging / EV charging), rerouting, operator escalation | Transitions |
| B6 | Plate policy | Different car allowed? Manual fallback (code, QR)? Retention period, consent text | Check-in, GDPR |
| B7 | Business model | Who pays; fee type (reservation, no-show, subscription, revenue share) | Business section |
| B8 | Interoperability depth | API naming per OCPP/OCPI only, or a second "app" that uses our API in the demo | Interop section |
| B9 | Demo story and presenter | Which scenarios live, who presents, fallback video yes/no | Pitch |
| B10 | Way of working | Repo, branch rules, check-in points, feature freeze time | Coordination |
| B11 | Collaboration tools | See `collaboration-tools.md` | Coordination – **decide before event** |
| B12 | Use of pre-event material | Which of A1–A12 the team adopts; how we declare it | Fairness, declaration |

## C. Open gaps [GAP]

Ask at the mentor slots (10:15 or 11:00) or the organiser before the event.

| # | Gap | Who answers | Effect if unanswered |
|---|---|---|---|
| C1 | May we bring code or designs made before the event? | Organiser – **ask before event** | A2/A3 stay documents, not code |
| C2 | Ecurious API: protocol, auth, endpoints, push or poll for events, response times | Ecurious | Real adapter cannot be built |
| C3 | How is the "charge" step started or observed? Server or charger? | Ecurious | Cycle cannot complete |
| C4 | Which plate events exist: unknown plate, blocked bay, vehicle leaves? | Ecurious | Blocked-bay and mismatch logic unconfirmed |
| C5 | How to test plate recognition: real car, printed test plate? | Ecurious | Check-in demo at risk |
| C6 | Is the test bay shared between teams? Time slots? | Ecurious / organiser | More work against the mock; book hardware time |
| C7 | Does plate recognition count as a separate mission area? | Ecurious mentor | Changes B3 |
| C8 | GoingElectric: does a web app qualify ("currently limited to apps")? Approval time? Key visible in browser OK? Does Ecurious provide a key? May we keep only station IDs (favourites) on the device beyond 24 h? | GoingElectric (info@goingelectric.de) / Ecurious – **ask before event** | Map feature at risk; may force mobile app (B1) |
| C9 | Is the Ecurious server reachable from venue network? Do we need a public URL (webhooks)? | Ecurious / organiser | Hosting choice (B1), tunnel needed |
| C10 | What exactly to submit at 18:00, and format | Organiser | Docs and slides planning |
| C11 | Can we test a blocked bay on the test bay? How? | Ecurious | Blocked-bay demo at risk |
| C12 | Camera health: does the hardware report a heartbeat / last-seen or its own health? Do we get raw frames or only plate events? May we cover the lens to test? | Ecurious | Camera-failure detection limited to our own timeout; S11 demo at risk |
| C13 | Does Ecurious have a back office / CRM with an API for operator tickets (escalations, faults, disputes)? In scope and accessible for us? | Ecurious | Operator events stay in our own outbox + generic webhook; CRM link pitch only |

---

## Event-day gates

Ordered by priority. Times are the latest acceptable.

| Gate | Result | Latest |
|---|---|---|
| G0 | Team registered. Roles, stack and state machine agreed | 12:00 |
| G1 | First real call to Ecurious server works (reserve, then release) | ~13:30 |
| G2 | Full cycle works once end to end, even if ugly | ~15:00 |
| G3 | No-show, blocked bay and plate mismatch handled | ~16:30 |
| G4 | Docs complete, demo rehearsed, feature freeze | 17:15 |
| Submit | Submission | 18:00 |

Team rules:

- G2 not done at 15:00 → stop new features, fix the cycle.
- Write docs while building. Keep the "what did not work" list from the first hour.
- Record a short video of the working cycle as fallback for the live demo.
- Fill the declaration log as you go.
