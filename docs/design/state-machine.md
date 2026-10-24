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
| `RESERVED` | Plate event, plate = booked | `ARRIVED` | Stop timer, lower barrier [GAP C2] |
| `RESERVED` | Plate event, plate ≠ booked | `PLATE_MISMATCH` | Ask driver in app: "Is this you?" |
| `PLATE_MISMATCH` | Driver confirms (code / QR / button) | `ARRIVED` | Log manual check-in |
| `PLATE_MISMATCH` | Driver denies or no answer in N min | `BLOCKED` | |
| `BLOCKED` | Vehicle leaves (plate gone event) [GAP C4] | `RESERVED` | Notify driver, timer continues or restarts [TEAM B5] |
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

Camera failure: a false "free" (blind camera, car actually there) is worse than a false "blocked", because the driver drives over trusting it. Rule: unknown camera health never shows as "free". Detection, cheapest first: (1) heartbeat / last seen, (2) cross-check with charger status and manual check-ins, (3) image-quality checks (brightness, blur, glare) if raw frames are available [GAP C12]. A trained model is out of scope for the hackathon; pitch 2–3 as the production version.

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

One interface. Mock version first, real version on site once docs arrive [GAP C2].

```
reserve(bayId, reservationId, plate, until) -> { ok, error? }
release(bayId, reservationId)               -> { ok, error? }
status(bayId)                               -> { occupied, plate?, reservedBy?, lastSeen, raw }
onPlateEvent(callback(bayId, plate|null, confidence?, timestamp))
```

Open points:
- Push (webhook / websocket) or poll for plate events? [GAP C2] Poll fallback works for demo.
- Does the server or we hold the reservation timer? Proposal: our backend holds it, so logic stays ours.
- Error cases to handle: timeout, auth error, bay already reserved, hardware offline.

## Event log

Log every adapter call, response and state change with timestamp and reservation ID. Used for debugging, documentation ("API calls, data flows") and demo.
