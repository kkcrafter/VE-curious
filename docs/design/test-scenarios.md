# Test and Demo Scenarios (draft, A4)

Same list serves as test cases and demo script. States refer to `state-machine.md`. Mark each one with what hardware supports [GAP C5, C11].

| # | Scenario | Steps | Expected | Mission area | Live demo? |
|---|---|---|---|---|---|
| S1 | Happy path | Find bay on map → reserve → car arrives, plate matches → charge → leave | `REQUESTED → RESERVED → ARRIVED → CHARGING → COMPLETED`, bay released | Core | Must |
| S2 | Driver cancels | Reserve → cancel in app | `CANCELLED`, bay released, fee rule applied | No-Shows | Optional |
| S3 | No-show | Reserve → do nothing until grace ends (shorten timer for demo) | Reminder sent, then `NO_SHOW`, bay released, fee rule applied | No-Shows | Should |
| S4 | Blocked by combustion car | Unknown plate stands in bay at reservation or arrival | `BLOCKED`, driver informed, reroute offered, operator escalated | Blocked Bays | Should |
| S5 | Blocked by EV still charging | As S4, other EV charging | `BLOCKED` with reason, ETA of free bay or reroute | Blocked Bays | Pitch only? |
| S6 | Blocked by EV not charging | As S4, EV idle | `BLOCKED`, escalation, idle-fee idea | Blocked Bays | Pitch only? |
| S7 | Driver in different car | Reserve with plate A → arrive with plate B → confirm in app | `PLATE_MISMATCH → ARRIVED` | Plate Recognition | Should |
| S8 | Plate unreadable | Dirty / dark / foreign plate (cover plate, low light) | No match → manual fallback (code / QR) → `ARRIVED` | Plate Recognition | If testable |
| S9 | Server or hardware error | Kill network / wrong credentials / bay offline | `FAILED` or retry, clear message, nothing stuck | Technical | Show in log |
| S10 | App B uses reservation | Second client reserves via our API → arrive | Recognised on site by plate / reservation ID | Interoperability | If B8 = demo |
| S11 | Camera blind | Reserve → cover the lens or cut the camera/server connection | After X min `UNVERIFIED`, app shows "status unverified" (never "free"), operator alerted; uncover → previous state | Plate Recognition / Technical | Should [GAP C12] |
| S12 | Driver reports bay fault | Reserve → arrive → tap "Bay not working", pick reason → try to reserve same bay again | `FAULT_REPORTED`, bay released, no fee, reroute offered, CPO ticket logged; second reserve rejected (bay `out_of_service`) | Blocked Bays / Utilisation | Should |

Per scenario during the event, note: date/time run, result (pass / fail), what did not work. Copy failures into the documentation.
