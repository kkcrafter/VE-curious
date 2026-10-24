# Ve-curious – Ecurious Hackathon (Watt the Hack)

Challenge: integrate a smart reservation system for public EV charging into a charging app.

A driver finds a charger on the map, books the bay now or for a time slot, and a barrier keeps the bay free until they arrive. A camera reads the plate, the barrier goes down, the car charges, and the bay is released when charging ends or the car leaves. The backend keeps one reservation state that the app, the hardware and the operator all read; it talks to the Ecurious lock and camera through an adapter, with a mock adapter so the whole cycle runs on a laptop.

<img src="docs/design/happy-flow/01-map.jpg" width="160" alt="Map with the reservable smart bay"> <img src="docs/design/happy-flow/09-bay-held.jpg" width="160" alt="Bay held, grace countdown"> <img src="docs/design/happy-flow/11-charging.jpg" width="160" alt="Charging: battery %, kWh, cost"> <img src="docs/design/happy-flow/13-session-summary.jpg" width="160" alt="Session summary with fee and energy cost">

All screens step by step: [happy flow](docs/design/happy-flow.md).

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
