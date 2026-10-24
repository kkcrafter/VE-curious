# VE-curious – Ecurious Hackathon (Watt the Hack)

Challenge: integrate a smart reservation system for public EV charging into a charging app.

## Run

```bash
cd backend
cp .env.example .env   # ADAPTER=mock needs no key; ADAPTER=ecurious needs ECURIOUS_API_KEY
uv run --env-file .env uvicorn app.main:app --reload --port 3000
```

- App: http://localhost:3000/ (demo drivers `driver1@demo.test` / `driver2@demo.test`, password `demo1234`)
- API docs: http://localhost:3000/docs
- Hardware test page: http://localhost:3000/test
- Tests: `cd backend && uv run pytest -q`

## Repo layout

- `backend/` – FastAPI + SQLite, one process; serves the frontend. See [backend/README.md](backend/README.md)
- `frontend/` – plain HTML / CSS / JS, no build step. See [frontend/README.md](frontend/README.md)
- `docs/` – brief, plans, design drafts

## Docs map

- [To-do: technical features still missing](docs/todo.md)
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
  - [UX specification](docs/design/UX.md) – screens per state, navigation, operator tab
  - [Backend services outline](docs/design/backend-outline.md) – modules, data model, API contract for the frontend
  - [State machine](docs/design/state-machine.md), [stack options](docs/design/stack-options.md), [test scenarios](docs/design/test-scenarios.md), [GoingElectric API](docs/design/goingelectric.md)
- `docs/templates/` – documentation, decision log, declaration log, pitch outline
