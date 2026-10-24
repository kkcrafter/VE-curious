# To-do: technical features still missing

State of the code on 2026-10-24 (commit `b753ead`, time slots). Priority as in `backlog.md`: P0 must, P1 should, P2 nice, P3 if time is left. Full hardware cycle before any extra feature.

**Built:** email + password login, map with GoingElectric stations, booking now or in a time slot (with placeholder price), cancel, plate match → `ARRIVED`, start / stop charging by driver tap, car leaves → `COMPLETED`, bay shows `unverified` when the camera is stale, mock and Ecurious adapters (SSE + polling fallback), event log, dev controls, hardware test page, operator event list, EN / DE text.

**In progress (not committed):** simulated charging data (kWh, battery %, cost) on the reservation.

## Core cycle (G2)

| Priority | Missing | Today | Ref |
|---|---|---|---|
| P0 | Full cycle on the real lock: reserve → plate → unlock → charge → leave → release, then film it | Works on mock; not yet confirmed on the real lock | S1 |
| P0 | Real charging start / stop signal | Driver taps start / stop; charger data simulated | C3 |
| P1 | Link our bays to their GoingElectric station (`geId`) | Bay pin comes from the sample file | C8 Q4 |
| P1 | Retry or reconcile when `release` / `unlock` fails | State moves on; failure only in the event log | S9 |

## Problem cases (G3)

| Priority | Missing | Today | Ref |
|---|---|---|---|
| P1 | No-show sweep: reminder before the deadline, then `NO_SHOW` and release the bay | An expired `RESERVED` stays held | S3, B4 |
| P1 | Different car arrives: `PLATE_MISMATCH` with "Is this you?" (`confirm_arrival` / `deny_arrival`) and a timeout | No transition; unknown plate is ignored | S7, B6 |
| P1 | Someone else in the bay: `BLOCKED`, tell the driver, suggest other bays, alert the operator | No transition; a slot start only waits | S4–S6, B5, C11 |
| P1 | Previous driver still charging at the next slot's start: tell the next driver | Hold is delayed silently | S5 |
| P2 | Unreadable plate: check in with a booking code or QR | Not built; frontend hides the code | S8, B6 |
| P2 | Camera down during a booking: reservation `UNVERIFIED`, driver sees "status unknown" | Only the bay status changes | S11, C12 |
| P2 | Fault report: `FAULT_REPORTED`, bay `out_of_service`, operator clears it | Flag exists in the DB; no route sets or clears it | S12 |

## Operator

| Priority | Missing | Today | Ref |
|---|---|---|---|
| P1 | `GET /api/operator/overview`: bays, active bookings, alerts (blocked, unverified, faults) | Bay status tiles + event list | backend-outline §3 |
| P2 | `POST /api/operator/bays/:id/clear-fault` | – | S12 |
| P2 | KPIs: utilisation, no-show rate, idle time (assumptions labelled) | – | – |

## Money

| Priority | Missing | Today | Ref |
|---|---|---|---|
| P2 | Ledger per transition: `HOLD` / `RELEASE` / `CAPTURE` / `REFUND`, idempotent | Fee shown per slot; nothing charged or held | B4, B7 |
| P2 | Receipt on the session summary: reservation fee apart from the energy price (AFIR) | – | UX "Not designed yet" |
| P3 | Stripe test mode | – | – |

## Security, privacy, deploy

| Priority | Missing | Today | Ref |
|---|---|---|---|
| P1 | Hosting reachable from the venue and from Ecurious, HTTPS | Runs on a laptop | C9, B1 |
| P1 | Session expiry and login rate limit (before any public deploy) | Tokens never expire | – |
| P2 | Plate retention rule (hash or delete after the visit) | Event log keeps a plate prefix | GDPR, B6 |
| P3 | Sign-up, several plates per driver, profile screen | Seeded demo accounts only | – |

## Stretch

| Priority | Missing | Today | Ref |
|---|---|---|---|
| P3 | Push to the app (SSE or push notifications) | App polls | backend-outline §7 |
| P3 | Partner API for a second app (OCPI-style `ReserveNow` / `CancelReservation`) | – | S10, B8 |
| P3 | One-tap rebook from an alternatives list when blocked | Goes back to the map | UX "Not designed yet" |
| P3 | Low battery → one-tap reservation (simulated battery slider) | – | – |
