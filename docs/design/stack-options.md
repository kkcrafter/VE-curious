# Tech Stack Options (decision B1, draft)

Input for the team decision B1. Record the choice in `../templates/decision-log.md`. Diagrams: `diagrams.md`; screens: `app-outline.md`.

## What the stack must handle

Taken from the design so far, independent of language:

| Need | Why | Consequence |
|---|---|---|
| Long-running backend process | Holds Ecurious credentials, grace timers (sweep), polls or receives plate events [GAP C2] | Plain server, not only serverless functions |
| Small relational DB | Reservations, bays, event log; one active reservation per bay (partial unique index) | SQLite is enough; Postgres if hosted DB is needed |
| Driver UI on a phone | Driver uses the app at the bay | Mobile-first layout, or a native app |
| Map in the client | GoingElectric terms: client fetches, no backend cache | Map library in the frontend; key handling depends on C8 |
| Operator view | Escalations, alerts, event log | Simple web page, same frontend or same server |
| Public URL in mock mode | Submission: jury opens the app (`../submission-deliverables.md`) | Easy deploy; webhooks from Ecurious need a public URL [GAP C9] |
| Live status in the app | Reservation state changes from plate events | Poll our backend every few seconds; push (SSE / websocket) only if time |

The biggest factor is not in this table: **what the team already knows**. A one-day hackathon is no time to learn a framework.

## Options

### A. TypeScript web app, one Node server (recommended default)

- **Frontend:** React + Vite, mobile-first web app (installable as PWA if time). Map: Leaflet with OpenStreetMap tiles.
- **Backend:** Node with Express, Fastify or Hono. The same server serves the built frontend and the API → one deploy, one URL.
- **DB:** SQLite (file); hosted Postgres only if the deploy target loses files on restart and that matters.
- **Deploy:** one service on Render, Railway or Fly. Check free-tier limits first (sleep after idle, card required).
- **Good:** one language front and back, shared types for states and API, fastest path to a public URL, operator view is just another route.
- **Risk:** fails only if GoingElectric does not accept a web app [GAP C8], or nobody in the team knows TypeScript / React.

### B. Python backend + web frontend

- **Frontend:** as in A (React + Vite), or server-rendered HTML with HTMX if the team prefers less JavaScript.
- **Backend:** FastAPI. SQLite via the standard library or SQLModel.
- **DB / deploy:** as in A (frontend served by FastAPI as static files, or separate on Vercel / Netlify).
- **Good:** if the backend people are stronger in Python; FastAPI gives an OpenAPI spec for free (helps the interoperability story, B8).
- **Risk:** two languages; with a separate frontend host, two deploys and CORS.

### C. Native-feel mobile app (Expo / React Native) + backend from A or B

- **Driver app:** Expo (React Native). Map: `react-native-maps`. Demo via Expo Go QR; no store release (review takes days).
- **Backend + operator view:** as in A or B (operator view stays a web page).
- **Good:** fits if GoingElectric only accepts real apps [GAP C8]; looks like a real charging app.
- **Risk:** device and Expo setup on the day, harder to give the jury a link (Expo web build or video as fallback), slower iteration.

### Considered and not proposed

| Option | Why not |
|---|---|
| Next.js / serverless-only backend | Timers and event polling need a process that keeps running; serverless functions stop between requests |
| Flutter, native iOS / Android | Same GoingElectric benefit as C, more setup; only if the team already works in it |
| Firebase / Supabase as the whole backend | Fine as a hosted database, but the adapter, timers and state machine still need our own server |
| Microservices, message broker, Kubernetes | One day, one bay; one process is enough |

## How to choose

1. Ask C8 first (does a web app qualify for a GoingElectric key?). If no → **C**.
2. Otherwise → **A**, unless the backend people clearly prefer Python → **B**.
3. Whatever wins: build the mock adapter behind the same interface first (`hackathon-playbook.md` §1), so the frontend can start before Ecurious credentials arrive.

## Out of scope for the hackathon demo

Parts of a full system we will not build. Mention them in the docs (limitations and scaling, deliverable 5) and the pitch roadmap, not in code.

| Component | Full system | Demo instead |
|---|---|---|
| Real login / identity provider | OIDC or eMSP account | Minimal login [TEAM]; map public |
| Real payments | Payment provider, live money | Mock ledger at most (`state-machine.md` "Payment ledger"), Stretch |
| Push notifications, SMS, email | Notification service | In-app status and banner |
| App store release | iOS / Android store | Web URL, Expo Go, or video |
| CPO back office / CRM link | Tickets in the operator's system [GAP C13] | Our own operator view |
| Camera-health model | Image-quality checks or trained model | Heartbeat / last-seen timeout only (`UNVERIFIED`) |
| Fake fault-report detection | Cross-checks, per-user counters | Pitch only |
| Several operators, sites, hardware vendors | Multi-tenant config, more adapters | One bay, one adapter (plus mock) |
| Full OCPI / OCPP implementation | Certified protocol endpoints | Naming that follows `ReserveNow` / `CancelReservation` [TEAM B8] |
| Load handling, monitoring, backups | Production operations | One process, event log |
