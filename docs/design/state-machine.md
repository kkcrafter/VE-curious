# Reservation State Machine (draft, A1 + A2)

Proposal for the team. Stack-neutral. Names are ours, not from Ecurious. Items tagged [TEAM] or [GAP] are not settled.

## States

| State | Meaning | Bay held by hardware? |
|---|---|---|
| `REQUESTED` | Driver asked; waiting for Ecurious confirm | No |
| `RESERVED` | Hardware holds bay; grace timer running | Yes |
| `BLOCKED` | Another vehicle stands in the reserved bay | – (bay occupied) |
| `PLATE_MISMATCH` | A vehicle arrived but plate ≠ booked plate; waiting for driver confirm | Yes |
| `UNVERIFIED` | Camera health unknown (no heartbeat, or signals disagree); bay status cannot be trusted | Unknown |
| `ARRIVED` | Booked vehicle checked in (plate match or manual fallback) | Released for parking |
| `CHARGING` | Charging session running | – |
| `COMPLETED` | Session ended, bay released | No |
| `CANCELLED` | Driver or system cancelled before arrival | No |
| `NO_SHOW` | Grace period ended without check-in | No |
| `FAILED` | Ecurious rejected or errored on reserve | No |
| `FAULT_REPORTED` | Driver on site reported the bay as not working | No |

Terminal states: `COMPLETED`, `CANCELLED`, `NO_SHOW`, `FAILED`, `FAULT_REPORTED`.

## Transitions

| From | Trigger | To | Side effects |
|---|---|---|---|
| `REQUESTED` | Ecurious `reserve` OK | `RESERVED` | Start grace timer, schedule reminder |
| `REQUESTED` | Ecurious `reserve` error / timeout | `FAILED` | Show reason, offer other bay |
| `REQUESTED` | Status shows bay occupied | `BLOCKED` | See blocked handling |
| `RESERVED` | Driver cancels | `CANCELLED` | `release` |
| `RESERVED` | Reminder time reached | `RESERVED` | Notify driver ("still coming?") |
| `RESERVED` | Grace timer expires | `NO_SHOW` | `release`, apply no-show rule [TEAM B4] |
| `RESERVED` | Plate event, plate = booked | `ARRIVED` | Stop timer, lower barrier (`unlock`) |
| `RESERVED` | Plate event, plate ≠ booked | `PLATE_MISMATCH` | Ask driver in app: "Is this you?" |
| `PLATE_MISMATCH` | Driver confirms (code / QR / button) | `ARRIVED` | Log manual check-in |
| `PLATE_MISMATCH` | Driver denies or no answer in N min | `BLOCKED` | |
| `BLOCKED` | Vehicle leaves (`vehicle_presence: vacant`) | `RESERVED` | Notify driver, timer continues or restarts [TEAM B5] |
| `BLOCKED` | Driver accepts reroute / cancels | `CANCELLED` | `release`, no fee, offer nearby free point (GoingElectric) |
| `BLOCKED` | Unresolved after N min | `BLOCKED` | Escalate to operator [TEAM B5] |
| `REQUESTED` / `RESERVED` / `PLATE_MISMATCH` / `BLOCKED` | No camera/bay update for X min, or signals disagree (e.g. charger `Charging` but camera "free") [GAP C12] | `UNVERIFIED` | App shows "status unverified", never "free"; alert operator; remember previous state |
| `UNVERIFIED` | Camera reports again and signals agree | previous state | Notify driver only if state changed |
| `UNVERIFIED` | Driver cancels or accepts reroute | `CANCELLED` | `release`, no fee |
| `ARRIVED` | Charging started [GAP C3] | `CHARGING` | |
| `ARRIVED` | No charging start after N min | `COMPLETED` | Idle rule [TEAM] |
| `CHARGING` | Charging stopped / vehicle leaves | `COMPLETED` | `release` |
| `RESERVED` / `ARRIVED` | Driver taps "Bay not working" + reason | `FAULT_REPORTED` | `release`, no fee (ledger: see Payment ledger), mark bay `out_of_service`, offer nearby free point (GoingElectric) with one-tap rebook, open CPO ticket |

Key insight: to the camera, "driver came in another car" and "stranger blocks bay" look the same (unknown plate). Only the app can tell them apart, by asking the driver. Hence the `PLATE_MISMATCH` state before `BLOCKED`.

Blocked sub-cases from the brief (combustion car / EV not charging / EV charging): the camera alone may not tell these apart. Possible signals: charger status via GoingElectric or Ecurious [GAP C3/C4], operator input. Store as `blocked_reason`.

Camera failure: a false "free" (blind camera, car actually there) is worse than a false "blocked", because the driver drives over trusting it. Rule: unknown camera health never shows as "free". Detection, cheapest first: (1) heartbeat: stale `lastSeenAt`, non-empty `activeErrors` or an SSE `alarm`, (2) cross-check `carPresence` with plate events, charger status and manual check-ins (e.g. `occupied` but no `photo_captured` = camera may be blind), (3) image-quality checks (brightness, blur, glare): not possible, the API gives plate events only, no raw frames. A trained model is out of scope for the hackathon; pitch 2–3 as the production version.

Driver fault report: covers what the hardware cannot see (damaged cable or plug, no power, obstacle such as snow or a cone). Reasons: `no_power`, `cable_damaged`, `obstacle`, `other`; store as `fault_reason`. From `RESERVED` because a broken barrier or charger can stop check-in. Not from `CHARGING` for now: a session that stops early ends in `COMPLETED` [TEAM].

Bay out of service: a flag on the bay, not a reservation state. While set, our backend rejects new reservations for that bay before calling Ecurious, and the map shows the bay as unavailable. Cleared only by the operator [TEAM]. If the charger reports OCPP `Faulted` [GAP C3], set the same flag without a driver report.

Fake reports (to dodge a no-show fee): cross-check with `status` and the latest plate event. If signals disagree, refund anyway but flag the report for operator review; count reports per user. Pitch only, not built.

## Payment ledger

Append-only list of money events per reservation, written by transitions. Mock in our backend for the demo; Stripe test mode (`capture_method=manual`) is a stretch. Amounts, late-cancel rule and whether the deposit is credited against charging cost: [TEAM B4, B7].

| Transition | Ledger entry | Note |
|---|---|---|
| `REQUESTED` (before Ecurious `reserve`) | `HOLD` deposit | Hold first; if the hold fails, do not call `reserve`, go to `FAILED` |
| `REQUESTED` → `FAILED` | `RELEASE` | Reserve error / timeout after a successful hold |
| `RESERVED` → `CANCELLED` (driver) | `RELEASE` | Or partial `CAPTURE` for a late cancel [TEAM B4] |
| `RESERVED` → `NO_SHOW` | `CAPTURE` | The only path where the driver loses the deposit |
| `RESERVED` / `PLATE_MISMATCH` → `ARRIVED` | `RELEASE` | Or credit against charging cost [TEAM B4] |
| `BLOCKED` / `UNVERIFIED` → `CANCELLED` | `RELEASE` | Not the driver's fault, no fee |
| `RESERVED` → `FAULT_REPORTED` | `RELEASE` | From `ARRIVED` the hold is already released; nothing to do |
| Operator decides after dispute | `REFUND` | Only for an earlier `CAPTURE` |

Rules:
- One entry per (reservation ID, entry type): a retried transition never holds or captures twice.
- Every entry also goes to the event log (timestamp, reservation ID, amount, reason), so a no-show fee can be explained.
- Show the reservation fee separately from the kWh price (AFIR); charging itself is billed outside this ledger.

## Hardware adapter contract (A2)

One interface. Mock version first, real version against the Ecurious parking-lock service (docs received 2026-10-24).

```
reserve(bayId, reservationId, plate, until) -> { ok, error? }
release(bayId, reservationId)               -> { ok, error? }
status(bayId)                               -> { occupied, plate?, reservedBy?, lastSeen, raw }
onPlateEvent(callback(bayId, plate|null, confidence?, timestamp))
```

### Ecurious parking-lock API (as probed 2026-10-24)

Hardware: Chang Cheng CC5S ground lock (barrier arm) with camera column (plate recognition) and presence sensor. Base URL `https://parking-lock-service-production.up.railway.app`. Auth: team API key as `X-API-Key` header (preferred) or `?apiKey=`. Key is per team and scopes access to our assigned locks; other lock IDs return 403. **Key lives in a git-ignored `.env`, never in this repo.** Our team has one lock: `lock-0001` (camera). The docs' examples use `bay-1`, which is not ours.

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/locks` | Our locks with `status` (`raised` / `lowered`), `carPresence` (`vacant` / `occupied`), batteries, 4G signal, `waterIngress`, `activeErrors`, `lastSeenAt`, `whitelist` |
| `GET /api/v1/locks/:id` | Same for one lock |
| `POST /api/v1/locks/:id/unlock` | Lower arm. Body `{ cancelAutoLift? }`; by default the arm re-raises if no car arrives within a timeout (length undocumented) |
| `POST /api/v1/locks/:id/lock` | Raise arm |
| `POST /api/v1/locks/:id/keep-state` | `{ state: "normal" \| "keep_open" \| "keep_closed" }` |
| `POST /api/v1/locks/:id/whitelist` | Up to 10 plates in camera EEPROM: `{ plates: [...] }`, `{ wildcard: true }`, or `{ plates: [] }` to disable. Matching plate lowers the arm in hardware, without our call |
| `GET /api/v1/locks/:id/plate/latest` | `{ lockId, timestamp, licensePlate, plateType }`; error if none yet |
| `GET /events` (SSE, also `/api/v1/events`) | Push stream filtered to our locks: `status_change`, `vehicle_presence`, `photo_captured` (with `licensePlate`), `alarm` (`water_ingress`, tamper, motor stall) |
| `POST /mcp` | Remote MCP server with the same actions as tools (`list_my_locks`, `get_lock_status`, `unlock_parking_lock`, `lock_parking_lock`, `set_lock_whitelist`, `get_latest_recognized_plate`) |

State at first probe: arm `raised`, `vacant`, whitelist `["*"]` (any plate auto-lowers), no plate recognised yet. `battery3_7V: 0` and `signalStrength4G: 0` look like placeholders; ask Ecurious.

Mapping to our interface:

| Ours | Ecurious calls |
|---|---|
| `reserve` | `whitelist { plates: [] }` (see decision below), then `lock` (arm up) |
| `release` | `whitelist { plates: [] }`, `unlock`; arm then re-raises by auto-lift after the car leaves [check on site] |
| `status` | `GET /locks/:id` → `occupied = carPresence == "occupied"`, `lastSeen = lastSeenAt`, `raw` = full body; `reservedBy` is ours, not from hardware |
| `onPlateEvent` | SSE `photo_captured` → `(lockId, licensePlate, timestamp)`; no confidence field. `vehicle_presence: vacant` → `plate = null` (vehicle left) |
| check-in (`RESERVED` → `ARRIVED`) | our backend calls `unlock` after the plate matches |

Decision proposal [TEAM]: keep the hardware whitelist **empty** and unlock from our backend after the plate check. Reason: with the plate whitelisted, the arm lowers before our state machine sees the event, which skips `PLATE_MISMATCH` and the event log. Hardware whitelist stays a fallback if our backend or venue network is down. Never leave `wildcard` on.

Open points:
- Push or poll? Answered: SSE push. Fall back to polling `GET /locks/:id` if the stream drops; reconnect with backoff.
- Does the server or we hold the reservation timer? Proposal: our backend holds it, so logic stays ours. The API has no reservation concept, only arm up / down.
- Auto-lift timeout length, and whether arm re-raises on its own after a car leaves [check on site].
- Error cases to handle: timeout, 403 (wrong lock / key), lock offline (`lastSeenAt` stale), `activeErrors` non-empty, arm command sent but no `status_change` follows.
- Charging is not in this API [GAP C3].

## Event log

Log every adapter call, response and state change with timestamp and reservation ID. Used for debugging, documentation ("API calls, data flows") and demo.
