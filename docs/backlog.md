# Starter Backlog

The to-do list for the task board (`collaboration-tools.md`). One row = one card on the board. Edit freely once the team has picked the stack, roles and focus topics (decisions B1–B3).

## How to read this

- **Checkpoint**: the event day has fixed checkpoints. Each one must be reached by a certain time; if we are late, we cut features, not the checkpoint.

  | Checkpoint | Meaning | Latest |
  |---|---|---|
  | Prep | Before the event day | – |
  | G0 | Team, roles and plan agreed | 12:00 |
  | G1 | Our app talks to the Ecurious system for the first time | ≈ 13:30 |
  | G2 | One full charging visit works on the real hardware: book → arrive → charge → leave | ≈ 15:00 |
  | G3 | Problem cases handled (no-show, someone else in the bay, wrong car) | ≈ 16:30 |
  | G4 | Building stops; documents and presentation finished and rehearsed | 17:15 |

- **Priority**: P0 = must have, or we fail the challenge · P1 = should have · P2 = nice to have · P3 = only if time is left.
- **Area**: Core (the basic booking flow) · Plate (number-plate camera) · No-Shows · Blocked (bay occupied by someone else) · Interop (other apps using our system) · Business (pricing, value for operators) · Docs · Pitch.
- **Ref**: codes for people who want the detail. B = team decision, C = open question for Ecurious or the organiser (`prep-plan.md`), A = preparation item, S = test scenario (`design/test-scenarios.md`). Non-technical readers can ignore this column.

## Prep (before the event)

| Checkpoint | Priority | Area | Card | Ref |
|---|---|---|---|---|
| Prep | P0 | Core | Ask the organiser: may we bring work prepared before the event? What exactly do we hand in, and in which format? | C1, C10 |
| Prep | P0 | Core | Get access to the public charging-station data (GoingElectric needs an access key), or check whether Ecurious gives us one | C8 |
| Prep | P1 | Core | Team decides: which technology we build with, who does what, which challenge topics we focus on | B1, B2, B3 |
| Prep | P1 | Core | Plan a "simulated hardware" mode, so we can build and demo even when the real bay or server is not available | A3 |
| Prep | P1 | Interop | Read how the industry standards (OCPP, OCPI) name "reserve" and "cancel", so our names match | A8 |
| Prep | P2 | Docs | Set up the shared code folder and the task board; copy our prepared documents into it | – |
| Prep | P2 | Pitch | Turn the pitch outline into first slides | A10 |
| Prep | P2 | Core | Everyone: make sure the tools are installed and a test project runs on your laptop | – |

## G0 – team and plan (by 12:00)

| Checkpoint | Priority | Area | Card | Ref |
|---|---|---|---|---|
| G0 | P0 | Core | Collect login details and technical documentation for the Ecurious system | C2 |
| G0 | P0 | Core | Ask the Ecurious mentors our open questions; write the answers down | C2–C7, C11, C12 |
| G0 | P0 | Core | Agree the booking steps and statuses (booked, arrived, charging, …) against what the real system offers | A1, A2 |
| G0 | P1 | Docs | Write the team's decisions into the decision log | B1–B10 |

## G1 – first contact with the hardware (≈ 13:30)

| Checkpoint | Priority | Area | Card | Ref |
|---|---|---|---|---|
| G1 | P0 | Core | Our system can tell the bay "hold this spot" (reserve) | A2 |
| G1 | P0 | Core | Our system can tell the bay "spot is free again" (release) | A2 |
| G1 | P0 | Core | Keep a time-stamped log of every message to and from the hardware (for debugging, documentation and proof in the demo) | – |
| G1 | P1 | Core | Map in the app showing public charging stations, with the data source named and linked | C8 |
| G1 | P1 | Core | Simulated hardware mode works the same way as the real one | A3 |

## G2 – one full visit works (≈ 15:00)

| Checkpoint | Priority | Area | Card | Ref |
|---|---|---|---|---|
| G2 | P0 | Core | Driver can pick a bay in the app, book it and see its status | S1 |
| G2 | P0 | Plate | When the camera reads the booked car's number plate, the driver is checked in automatically | S1 |
| G2 | P0 | Core | Charging start and end are recognised (how depends on the Ecurious answer) | C3 |
| G2 | P0 | Core | When the visit ends, the bay is freed for the next driver | S1 |
| G2 | P0 | Pitch | Film a video of the full visit on the real hardware (backup if the live demo fails) | – |

## G3 – problem cases (≈ 16:30)

| Checkpoint | Priority | Area | Card | Ref |
|---|---|---|---|---|
| G3 | P1 | No-Shows | Driver books but never comes: reminder, then the booking expires and the bay is freed after a waiting time | S3, B4 |
| G3 | P1 | Plate | A different car arrives (e.g. driver came in a second car): app asks "Is this you?" | S7 |
| G3 | P1 | Blocked | Someone else is parked in the booked bay: inform the driver, suggest another station, alert the operator | S4, B5 |
| G3 | P2 | Plate | Number plate cannot be read (dirty, dark): driver checks in with a code instead | S8, B6 |
| G3 | P2 | Core | Server or hardware fails: clear message for the driver, nothing gets stuck | S9 |
| G3 | P2 | Business | Pricing ideas and example figures for operators (clearly marked as assumptions) | B7 |
| G3 | P3 | Interop | A second app books through our system, to show other apps can use it | S10, B8 |

## G4 – finish (by 17:15)

| Checkpoint | Priority | Area | Card | Ref |
|---|---|---|---|---|
| G4 | P0 | Docs | Documentation complete, including what did not work | – |
| G4 | P0 | Docs | List of AI tools, libraries and outside sources we used (required by the rules) | A12 |
| G4 | P0 | Pitch | Rehearse the pitch twice, including switching to the backup (simulated mode or video) | – |
| G4 | P1 | Docs | Short guide: how to run the app, overview picture, link to the video | – |
| G4 | P1 | Core | Final checks before handing in (`hackathon-playbook.md` §3) | – |
