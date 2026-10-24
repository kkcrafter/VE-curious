# Backend Services Outline (draft, for frontend review)

Goal: agree on the API contract between backend and frontend **before** writing code, so both sides can build in parallel against the mock adapter. States and transitions: `state-machine.md` (table wins). Screens: `app-outline.md`. Diagrams: `diagrams.md`. Tags as there: [GAP] = waiting on Ecurious / GoingElectric, [TEAM] = team decision open, [PROPOSAL] = not discussed yet.

Assumes stack option A (one Node + TypeScript server, SQLite, serves the built frontend from the same origin) [TEAM B1]. The contract in §3 does not depend on the language.

**Review asks for the frontend:** see §7.

## 1. Services (modules in one process)

One server process, no microservices (`stack-options.md`). Each row is a module / folder, not a separate deploy.

| Module | Job | Phase |
|---|---|---|
| `api` | HTTP routes for driver app, operator view, dev controls (§3). Validates input, maps errors to codes | S1 |
| `reservations` | State machine: `transition(reservation, event) → { next, effects }` as a pure function, plus DB store. Only place that changes `state` | S1 |
| `adapter` | Hardware interface `reserve / release / status / onPlateEvent` (`state-machine.md` "Hardware adapter contract"). Two versions: `mock` and `ecurious`. Chosen by `ADAPTER` env | S1 |
| `hardware-events` | Ecurious SSE consumer (`photo_captured`, `vehicle_presence`, `status_change`, `alarm`) → normalised events into `reservations`. Reconnect with backoff; poll `GET /locks/:id` while the stream is down | S1 |
| `sweep` | Every 5 s: grace deadline passed → `NO_SHOW`; reminder due; mismatch answer timeout → `BLOCKED`; blocked > N min → escalate; camera `lastSeenAt` stale → `UNVERIFIED`. Deadlines live in the DB, so a restart loses nothing | G3 (no-show part S1 if time) |
| `event-log` | Append every adapter call, hardware event and state change (timestamp, reservation ID, bay ID, kind, payload). Read by operator view | S1 |
| `ledger` | Mock money entries `HOLD / RELEASE / CAPTURE / REFUND` per transition (`state-machine.md` "Payment ledger") | Stretch [TEAM B4, B7] |

Not in the backend: GoingElectric data (client fetches it directly, terms in `goingelectric.md`), push notifications, real payments, real identity provider (`stack-options.md` "Out of scope").

Flow of one plate event: `hardware-events` → `reservations.transition` → effects run (`adapter.unlock`, event log, ledger) → new state in DB → frontend sees it on next poll.

## 2. Data model (SQLite)

| Table | Columns (main) | Notes |
|---|---|---|
| `drivers` | `id`, `name`, `plate`, `email`, `password_hash` | Email + password login (prototype, seeded accounts, no sign-up); one plate per driver for now [TEAM B6] |
| `sessions` | `token`, `driver_id`, `created_at` | Opaque bearer token; no expiry in the prototype |
| `bays` | `id`, `lock_id` (`lock-0001`), `ge_id`, `name`, `out_of_service`, `last_seen_at` | One bay for the demo. `ge_id` links to GoingElectric [GAP C8 Q4] |
| `reservations` | `id`, `bay_id`, `driver_id`, `plate`, `state`, `previous_state` (for `UNVERIFIED`), `blocked_reason`, `fault_reason`, `grace_deadline`, `reminder_at`, `mismatch_deadline`, `created_at`, `updated_at` | Partial unique index: one active (non-terminal) reservation per bay |
| `event_log` | `id`, `ts`, `reservation_id`, `bay_id`, `kind`, `payload` (JSON) | Plate stored as match result or masked, not raw [TEAM B6] |
| `ledger` | `id`, `reservation_id`, `type`, `amount_cents`, `ts` | Unique (`reservation_id`, `type`): retries never charge twice. Stretch |

## 3. API contract

Base path `/api`, JSON, times in ISO 8601 UTC. Same origin as the frontend, so no CORS.

Auth (prototype): `POST /api/login` `{email, password}` returns `{token, driver}`; driver routes need `Authorization: Bearer <token>`. `POST /api/logout`, `GET /api/me`. Wrong login: `401 bad_credentials`; missing or unknown token: `401 unauthorized`. Operator routes use `X-Operator-Token` when `OPERATOR_TOKEN` is set; dev routes are unprotected (mock only).

### Reservation object

```json
{
  "id": "r_8f2c",
  "bayId": "bay-1",
  "plate": "M-AB 1234",
  "state": "RESERVED",
  "blockedReason": null,
  "faultReason": null,
  "graceDeadline": "2026-11-07T10:15:00Z",
  "serverTime": "2026-11-07T10:02:13Z",
  "allowedActions": ["cancel", "report_fault"],
  "createdAt": "2026-11-07T10:00:00Z",
  "updatedAt": "2026-11-07T10:00:02Z"
}
```

- `state`: one of the 12 states in `state-machine.md`.
- `allowedActions`: backend tells the frontend which buttons to show, so the state machine lives in one place (§4). Frontend owns all wording.
- `serverTime`: compute the countdown as `graceDeadline − serverTime` to avoid phone clock drift.

### Bay object

```json
{
  "id": "bay-1",
  "geId": 12345,
  "name": "Test bay",
  "status": "reserved",
  "lastSeenAt": "2026-11-07T10:02:10Z"
}
```

`status`: `free` | `reserved` | `occupied` | `unverified` | `out_of_service`. Rule: stale camera → `unverified`, **never** `free`. Frontend shows this next to GoingElectric data, visibly separate (terms).

### Driver routes

| Method + path | Body | Returns | Errors |
|---|---|---|---|
| `GET /api/bays` | – | `Bay[]` | – |
| `GET /api/bays/:id` | – | `Bay` | `not_found` |
| `POST /api/reservations` | `{ bayId, plate }`; header `Idempotency-Key` | `201 Reservation` (state `REQUESTED` or already `RESERVED`) | `bay_taken`, `out_of_service`, `driver_has_active`, `hardware_error` |
| `GET /api/reservations/:id` | – | `Reservation` | `not_found` |
| `GET /api/me/reservations?active=true` | – | `Reservation[]` (newest first) | – |
| `POST /api/reservations/:id/cancel` | – | `Reservation` | `invalid_action` |
| `POST /api/reservations/:id/confirm-arrival` | `{ code? }` | `Reservation` (`ARRIVED`) | `invalid_action`, `wrong_code` |
| `POST /api/reservations/:id/deny-arrival` | – | `Reservation` (`BLOCKED`) | `invalid_action` |
| `POST /api/reservations/:id/fault` | `{ reason: "no_power" \| "cable_damaged" \| "obstacle" \| "other", note? }` | `Reservation` (`FAULT_REPORTED`) | `invalid_action` |
| `POST /api/reservations/:id/charging` | `{ action: "start" \| "stop" }` | `Reservation` | `invalid_action` |

`/charging` is a stand-in: we do not know yet how charging is started or observed [GAP C3]. If Ecurious gives us a signal, the route stays as a manual fallback.

Live updates: frontend polls `GET /api/reservations/:id` every 2 s while a reservation is active. SSE push to the client is Stretch.

### Error format

```json
{ "error": { "code": "bay_taken", "message": "Bay already reserved" } }
```

HTTP status: `400` bad input, `404 not_found`, `409` for `bay_taken` / `out_of_service` / `driver_has_active` / `invalid_action`, `502 hardware_error` (Ecurious down or rejected). Frontend switches on `code`, not on `message`.

### Operator routes (G3)

| Method + path | Returns |
|---|---|
| `GET /api/operator/overview` | Bays with live status, active reservations, alerts (blocked > N min, `UNVERIFIED`, fault reports) |
| `GET /api/operator/events?limit=100` | Event log, newest first |
| `POST /api/operator/bays/:id/clear-fault` | Clears `out_of_service` |
| `POST /api/operator/reservations/:id/refund` | Stretch, needs ledger |

### Dev controls (mock adapter only)

Enabled when `ADAPTER=mock`. Lets the frontend and the demo play every scenario in `test-scenarios.md` without hardware.

| Method + path | Body | Simulates |
|---|---|---|
| `POST /api/dev/plate` | `{ bayId, plate }` | `photo_captured` (S1, S7, S8) |
| `POST /api/dev/presence` | `{ bayId, occupied }` | `vehicle_presence` (S4, leave) |
| `POST /api/dev/camera` | `{ bayId, online }` | Heartbeat stops / resumes (S11) |
| `POST /api/dev/fail-next` | `{ call: "reserve" \| "release" }` | Next adapter call errors (S9) |
| `POST /api/dev/reset` | – | Empty DB, reseed |

## 4. Allowed actions per state

Derived from `app-outline.md` §4. Backend enforces it; frontend reads `allowedActions`.

| State | `allowedActions` |
|---|---|
| `REQUESTED` | – |
| `RESERVED` | `cancel`, `report_fault` |
| `PLATE_MISMATCH` | `confirm_arrival`, `deny_arrival` |
| `BLOCKED` | `cancel` |
| `UNVERIFIED` | `cancel` |
| `ARRIVED` | `report_fault`, `start_charging` [GAP C3] |
| `CHARGING` | `stop_charging` [GAP C3] |
| `COMPLETED`, `CANCELLED`, `NO_SHOW`, `FAILED`, `FAULT_REPORTED` | – (terminal) |

## 5. Config (`.env`, git-ignored)

| Key | Example | Note |
|---|---|---|
| `ADAPTER` | `mock` | `mock` or `ecurious` |
| `ECURIOUS_BASE_URL` | `https://parking-lock-service-production.up.railway.app` | |
| `ECURIOUS_API_KEY` | – | Team key, never in the repo |
| `LOCK_ID` | `lock-0001` | Our only lock |
| `GRACE_MINUTES` | `15` | Short (e.g. 1) for the demo [TEAM B4] |
| `REMINDER_MINUTES_BEFORE` | `5` | [TEAM B4] |
| `MISMATCH_TIMEOUT_MINUTES` | `3` | "Is this you?" answer window |
| `CAMERA_STALE_SECONDS` | `60` | Heartbeat older than this → `UNVERIFIED` [GAP C12] |
| `PORT`, `DB_PATH` | `3000`, `./data.db` | |

## 6. Build order

Full hardware cycle before any extra feature.

1. Server skeleton, DB, mock adapter, `GET /bays`, `POST /reservations`, `GET /reservations/:id`, `cancel`, dev controls. **Frontend can start here.**
2. Plate event → `ARRIVED` → `/charging` → `COMPLETED` on the mock (S1 on mock).
3. Ecurious adapter: `lock` / `unlock`, SSE consumer, polling fallback, event log. **S1 on real hardware.**
4. `sweep`: `NO_SHOW` and reminder (S3), `UNVERIFIED` (S11).
5. `PLATE_MISMATCH`, `BLOCKED`, fault report, operator routes (S4, S7, S12).
6. Stretch: ledger, SSE to the client, partner webhooks [PROPOSAL, TEAM B8].

## 7. Questions for the frontend reviewer

1. Polling every 2 s OK for the demo, or do you need SSE from the start?
2. Is `allowedActions` enough to drive the buttons on the status screen, or do you need more fields?
3. ~~Auth placeholder~~ Answered: email + password login with bearer token (seeded accounts, no sign-up).
4. Bay ↔ GoingElectric: backend returns `geId` for our bay; you match it to the GoingElectric result on the map. Works for you? [GAP C8 Q4]
5. Anything on the screens in `app-outline.md` that needs data not listed here (e.g. history, address)?
6. One deploy (backend serves the built frontend) OK, or do you want a separate frontend host?

## Open items that change the backend

| Tag | Changes |
|---|---|
| B1 Stack | Language and framework of every module |
| B4 No-show rules | Grace, reminder, fee values |
| B5 Blocked policy | Escalation time, `BLOCKED → RESERVED` timer rule |
| B6 Plate policy | `confirm-arrival` code / QR, plate storage in event log |
| B8 Interop | Whether partner routes or webhooks exist |
| C3 Charging | Replaces or keeps `/charging` |
| C5, C11 | How plate and blocked scenarios are tested on site |
| C9 Venue network | Whether the server reaches Ecurious from the venue; hosting |
| C12 Camera health | `CAMERA_STALE_SECONDS`, blind-camera detection |
