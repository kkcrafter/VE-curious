# To-do: technical features still missing

State of `main` at the end of the hackathon (2026-10-24). Priority: P0 must have, P1 should have, P2 nice to have, P3 only if time is left. Full hardware cycle before any extra feature.

**Built:** email + password login, map with GoingElectric stations, booking now or in a time slot (with placeholder price), cancel, plate match → `ARRIVED`, start / stop charging by driver tap, car leaves → `COMPLETED`, charging screen and session summary with simulated charger data (kWh, battery %, cost), bay shows `unverified` when the camera is stale, mock and Ecurious adapters (SSE + polling fallback), event log, dev controls, hardware test page, operator event list, EN / DE text.

## Core cycle

| Priority | Missing | Today |
|---|---|---|
| P0 | Full cycle on the real lock: reserve → plate → unlock → charge → leave → release, then film it | Works on mock and on the real Ecurious lock; not yet filmed |
| P0 | Real charging start / stop signal | Driver taps start / stop; charger data simulated |
| P1 | Link our bays to their GoingElectric station (`geId`) | Bay pin comes from the sample file |
| P1 | Retry or reconcile when `release` / `unlock` fails | State moves on; failure only in the event log |

## Problem cases

| Priority | Missing | Today |
|---|---|---|
| P1 | No-show sweep: reminder before the deadline, then `NO_SHOW` and release the bay | An expired `RESERVED` stays held |
| P1 | Different car arrives: `PLATE_MISMATCH` with "Is this you?" (`confirm_arrival` / `deny_arrival`) and a timeout | No transition; unknown plate is ignored |
| P1 | Someone else in the bay: `BLOCKED`, tell the driver, suggest other bays, alert the operator | No transition; a slot start only waits |
| P1 | Previous driver still charging at the next slot's start: tell the next driver | Hold is delayed silently |
| P2 | Unreadable plate: check in with a booking code or QR | Not built; frontend hides the code |
| P2 | Camera down during a booking: reservation `UNVERIFIED`, driver sees "status unknown" | Only the bay status changes |
| P2 | Fault report: `FAULT_REPORTED`, bay `out_of_service`, operator clears it | Flag exists in the DB; no route sets or clears it |

## Operator

| Priority | Missing | Today |
|---|---|---|
| P1 | `GET /api/operator/overview`: bays, active bookings, alerts (blocked, unverified, faults) | Bay status tiles + event list |
| P2 | `POST /api/operator/bays/:id/clear-fault` | – |
| P2 | KPIs: utilisation, no-show rate, idle time (assumptions labelled) | – |

## Money

| Priority | Missing | Today |
|---|---|---|
| P2 | Ledger per transition: `HOLD` / `RELEASE` / `CAPTURE` / `REFUND`, idempotent | Fee shown per slot; nothing charged or held |
| P2 | Receipt on the session summary: reservation fee apart from the energy price (AFIR) | – |
| P3 | Stripe test mode | – |

## Security, privacy, deploy

| Priority | Missing | Today |
|---|---|---|
| P1 | Hosting reachable from the venue and from Ecurious, HTTPS | Runs on a laptop |
| P1 | Session expiry and login rate limit (before any public deploy) | Tokens never expire |
| P2 | Plate retention rule (hash or delete after the visit) | Event log keeps a plate prefix |
| P3 | Sign-up, several plates per driver, profile screen | Seeded demo accounts only |

## Stretch

| Priority | Missing | Today |
|---|---|---|
| P3 | Push to the app (SSE or push notifications) | App polls |
| P3 | Partner API for a second app (OCPI-style `ReserveNow` / `CancelReservation`) | – |
| P3 | One-tap rebook from an alternatives list when blocked | Goes back to the map |
| P3 | Low battery → one-tap reservation (simulated battery slider) | – |
