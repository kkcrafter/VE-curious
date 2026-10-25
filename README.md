# VE-curious – Ecurious Hackathon (Watt the Hack)

A reservation app for public EV charging bays: a smart parking lock holds the bay until the driver's car arrives.

Made for the Ecurious challenge at the Watt the Hack hackathon on 24 October 2026, part of Munich Climate Week.

**How it works:** find a charger on the map → book the bay → a barrier holds it → the camera reads your plate and lowers the barrier → charge → the bay is released.

<img src="docs/design/happy-flow/01-map.jpg" width="160" alt="Map with the reservable smart bay"> <img src="docs/design/happy-flow/09-bay-held.jpg" width="160" alt="Bay held, grace countdown"> <img src="docs/design/happy-flow/11-charging.jpg" width="160" alt="Charging: battery %, kWh, cost"> <img src="docs/design/happy-flow/13-session-summary.jpg" width="160" alt="Session summary with fee and energy cost">

All screens step by step: [happy flow](docs/design/happy-flow.md).

## Run it

Needs Python and [uv](https://docs.astral.sh/uv/). Runs fully on a laptop with simulated hardware; no keys needed.

```bash
cd backend
cp .env.example .env
uv run --env-file .env uvicorn app.main:app --port 3000
```

Open http://localhost:3000/ and log in with `driver1@demo.test` / `demo1234`. The demo panel simulates the camera reading the plate and the car leaving. Details and tests: [backend/README.md](backend/README.md).

## Status

A working prototype, not a product. Real: the Ecurious lock and camera through their API, GoingElectric map data (needs a key). Simulated: the charger (kWh, battery %, cost) and all prices.

## Key features

- **Map of real chargers** – stations from GoingElectric; our smart bay is the lime pin with its live status.
- **Book now or a time slot** – slots with a price each; a slot holds the bay only from its start time. Cancel anytime before arrival.
- **Plate check-in** – the camera's plate read moves the booking to `ARRIVED` and lowers the barrier; no app tap at the bay.
- **Charging and summary** – start / stop in the app, live battery %, kWh and cost, then a summary with energy cost and reservation fee apart.
- **Never "free" when unsure** – if the camera stops reporting, the bay shows `unverified`, not free, and cannot be booked.
- **One source of truth** – a pure state machine; only one module changes state or calls hardware; every step goes to an event log. Bookings are idempotent per driver, so a retry never books twice.
- **Mock or real hardware** – `ADAPTER=mock` with dev controls to simulate plate reads and car departure; `ADAPTER=ecurious` for the real lock (SSE with polling fallback), plus a hardware test page.
- **Operator view** – bay status and the event list.
- **Driver login** – email + password; the map stays public.
- **English and German** – all text in `frontend/i18n/`.

Not built yet (no-show, blocked bay, plate mismatch, fees charged, hosting): [to-do](docs/todo.md).

## Repo structure

One backend process serves both the API and the frontend files. No build step.

```
backend/                  FastAPI + SQLite (details: backend/README.md)
  app/
    main.py               HTTP routes: driver, operator, dev controls; serves frontend/
    core.py               the only place that changes reservation state or calls hardware
    machine.py            state machine: (state, event) -> next state, pure
    adapters.py           hardware adapters: MockAdapter and EcuriousAdapter, one interface
    hardware_events.py    Ecurious event stream (SSE) -> core; reconnects, polling fallback
    db.py                 SQLite schema, seed bays and demo drivers, password hashing, event log
    config.py             settings from env (.env.example lists them)
    test.html             hardware test page at /test
  tests/                  pytest: full cycle, slots, dev controls, Ecurious adapter
frontend/                 plain HTML / CSS / JS (details: frontend/README.md)
  index.html, style.css   page skeleton: Map, Booking, Operator tabs
  app.js                  UI logic and every backend call
  i18n/en.json, de.json   all visible text; check_i18n.py checks keys match and none are missing
  sample_chargepoints.json  our test bay pin, and map data when no GoingElectric key is set
docs/                     brief, plans, design (see Docs map below)
  design/                 state machine, API contract, UX, diagrams, happy-flow screens
  templates/              decision log, declaration log, pitch outline
```

How a booking moves through the code: `app.js` calls a route in `main.py` → `core.py` asks `machine.py` for the next state, saves it in SQLite, writes the event log and calls the adapter → the adapter talks to the lock (or the mock). Plate reads and car departures come back the other way, through `hardware_events.py` (or `/api/dev/*` on mock) into `core.py`. The frontend only shows the buttons the backend lists in `allowedActions`.

## Docs map

- `docs/challenge-brief.pdf` – original brief from Ecurious
- `docs/challenge-reference.md` – brief summary, scoring, rules
- `docs/prep-plan.md` – what we can do now, what the team must decide, open gaps
- `docs/collaboration-tools.md` – tool proposal for the team
- `docs/hackathon-playbook.md` – event-day practices: demo fallback, checks, AI guardrails, scope cuts, pitch, jury questions
- `docs/submission-deliverables.md` – what to submit in the form, ranked; minimum deployment
- `docs/backlog.md` – starter cards for the task board, grouped by gate
- `docs/resources.md` – external toolkits and standards worth reading
- `docs/design/` – design drafts (proposals):
  - [Architecture + data flow diagrams](docs/design/diagrams.md) – components, data flows, reservation states, full-cycle sequence, plate event handling
  - [App outline + wireframes](docs/design/app-outline.md) – domains, screen flow, wireframe images
  - [Backend services outline](docs/design/backend-outline.md) – modules, data model, API contract for the frontend (draft for review)
  - [State machine](docs/design/state-machine.md), [stack options](docs/design/stack-options.md), [test scenarios](docs/design/test-scenarios.md), [GoingElectric API](docs/design/goingelectric.md)
- `docs/templates/` – documentation, decision log, declaration log, pitch outline
