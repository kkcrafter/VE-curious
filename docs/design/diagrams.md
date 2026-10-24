# Architecture and Data Flow Diagrams (draft)

Rough first version, before Ecurious API docs and team decisions. Mermaid, renders on GitHub. Sources: `state-machine.md`, `goingelectric.md`, `test-scenarios.md`, `../prep-plan.md`.

Legend, used in every diagram:

- **Red dashed** = [GAP] – unknown until Ecurious / GoingElectric / organiser answers (C-items in `prep-plan.md`)
- **Orange** = [TEAM] – team has not decided yet (B-items)
- **Green dashed** = [PROPOSAL] – extra design idea, not yet discussed with the team (see "Proposed additions" below)
- Plain = draft from the shared design docs, no open question

Replace each tag when the item is answered; update the gap table at the end.

## 1. Components (who talks to whom)

```mermaid
flowchart LR
    classDef gap stroke:#d33,stroke-width:2px,stroke-dasharray:5 4
    classDef team fill:#ffe3bf,stroke:#e8890c
    classDef prop stroke:#2a9d4b,stroke-width:2px,stroke-dasharray:3 3

    driver(["Driver"])
    operator(["Operator / CPO staff"])

    subgraph us["Our system – eMSP side"]
        app["Driver app<br/>web or mobile [TEAM B1]"]:::team
        api["Backend API<br/>reservations, check-in, cancel"]
        core["Reservation core<br/>state machine + timers"]
        db[("DB<br/>reservations, bays (out_of_service),<br/>event log")]
        adapter["Hardware adapter<br/>reserve / release / status / onPlateEvent"]
        mock["Mock adapter<br/>dev + demo fallback"]
        opview["Operator view<br/>alerts, escalations [TEAM B5]"]:::team
        sweep["Timer sweep<br/>periodic check of deadlines in DB<br/>[PROPOSAL]"]:::prop
        recon["Reconciliation loop<br/>our state vs status(bayId)<br/>[PROPOSAL]"]:::prop
        hooks["Partner webhooks<br/>reservation / bay events out<br/>[PROPOSAL]"]:::prop
        kpi["KPI read model<br/>aggregates from event log<br/>[PROPOSAL]"]:::prop
    end

    appB["App B / partner<br/>[TEAM B8]"]:::team

    subgraph ecu["Ecurious – CPO side"]
        server["Ecurious server<br/>protocol, auth, endpoints [GAP C2]"]:::gap
        hw["Reservation hardware<br/>test bay (shared? [GAP C6])"]:::gap
        cam["Camera<br/>plate recognition, health [GAP C12]"]:::gap
        charger["Charger<br/>start / observe charging [GAP C3]"]:::gap
    end

    ge["GoingElectric API<br/>static charge point data<br/>key + web app OK? [GAP C8]"]:::gap

    driver --> app
    app -- "map search, direct from device<br/>(terms: no backend cache)" --> ge
    app -- "HTTPS" --> api
    appB -. "our open API [TEAM B8]" .-> api
    api --> core
    core <--> db
    core --> adapter
    core -. "switch" .-> mock
    adapter -- "venue network reachable? [GAP C9]" --> server
    server -. "plate events: push or poll? [GAP C2]" .-> adapter
    server --> hw
    hw --- cam
    server -. "?" .-> charger
    core --> opview
    operator --> opview
    sweep -. "expired grace_deadline: NO_SHOW" .-> core
    recon -. "status(bayId)" .-> adapter
    recon -. "mismatch: log + alert" .-> opview
    core -. "state change events" .-> hooks
    hooks -. "HTTPS POST [TEAM B8]" .-> appB
    db -. "event log" .-> kpi
    kpi -. "utilisation, no-show rate,<br/>blocked minutes" .-> opview
```

Notes:

- Map data never passes our backend (GoingElectric terms). Our bay status (Ecurious) is shown separately from GoingElectric data.
- Core does not know Ecurious directly; only the adapter does. Real adapter is built on site once C2 is answered; mock first.
- Timers live in our backend, not on the Ecurious server (proposal in `state-machine.md`).
- Green dashed boxes: see "Proposed additions" below.
- Only what the demo needs is drawn. Full-system parts we leave out (real payments, push, identity provider, CRM, store release …): `stack-options.md` "Out of scope".

## 2. Data flows (what data goes where)

```mermaid
flowchart LR
    classDef gap stroke:#d33,stroke-width:2px,stroke-dasharray:5 4
    classDef team fill:#ffe3bf,stroke:#e8890c
    classDef store fill:#eef,stroke:#669
    classDef prop stroke:#2a9d4b,stroke-width:2px,stroke-dasharray:3 3

    app["Driver app"]
    partner["Partner app / webhook receiver<br/>[PROPOSAL]"]:::prop
    kpi[("KPI aggregates<br/>no personal data<br/>[PROPOSAL]")]:::prop
    ge["GoingElectric"]
    be["Our backend"]
    ecu["Ecurious server + hardware"]:::gap
    resv[("Reservations<br/>user, bay, plate, state, deadlines")]:::store
    log[("Event log<br/>adapter calls, state changes<br/>plate stored how? [TEAM B6]")]:::team
    cache[("Device cache<br/>GoingElectric data ≤ 24 h,<br/>show fetch time if > 1 h")]:::store

    app -- "bbox, filters (no personal data)" --> ge
    ge -- "locations, plugs, power, fault_report" --> app
    app --- cache

    app -- "account, bay ID, plate, until" --> be
    be -- "reservation state, bay status,<br/>'Is this you?' prompts" --> app
    be --- resv
    be --- log

    be -- "reserve(bayId, reservationId, plate?, until)<br/>does Ecurious need the plate? [GAP C2]" --> ecu
    ecu -- "plate events: plate or null, confidence?<br/>which events exist? [GAP C4]" --> be
    ecu -- "status: occupied, plate?, lastSeen [GAP C12]" --> be
    ecu -. "charging started / stopped [GAP C3]" .-> be

    be -. "webhook: reservation ID, bay, state, time<br/>no plate, no GoingElectric data" .-> partner
    log -. "counts per bay / hour" .-> kpi
```

GDPR points on this flow (values = decision B6, see `../templates/documentation.md` §8):

- Plates of non-customers arrive in plate events. Decide what we keep: nothing, match result only, or hashed plate (hash = pseudonymised, not anonymous).
- Plate leaves our system only if Ecurious needs it for `reserve` [GAP C2].
- No personal data goes to GoingElectric; no GoingElectric data goes out through our API (terms).
- Location / GPS: only if we build ETA-based no-show detection [TEAM B4].
- Webhooks [PROPOSAL] carry reservation ID and state only; KPI aggregates hold counts, no personal data.

## 3. Reservation states

Visual of the transition table in `state-machine.md`. Table wins if they differ.

```mermaid
stateDiagram-v2
    [*] --> REQUESTED: driver reserves
    REQUESTED --> RESERVED: Ecurious reserve OK
    REQUESTED --> FAILED: error / timeout
    REQUESTED --> BLOCKED: bay occupied

    RESERVED --> ARRIVED: plate = booked [GAP C4]
    RESERVED --> PLATE_MISMATCH: plate ≠ booked
    RESERVED --> NO_SHOW: grace timer expires [TEAM B4]
    RESERVED --> CANCELLED: driver cancels
    RESERVED --> FAULT_REPORTED: "bay not working"

    PLATE_MISMATCH --> ARRIVED: driver confirms (code / QR / button) [TEAM B6]
    PLATE_MISMATCH --> BLOCKED: denies / no answer

    BLOCKED --> RESERVED: vehicle leaves [GAP C4] [TEAM B5]
    BLOCKED --> CANCELLED: reroute / cancel
    BLOCKED --> BLOCKED: escalate after N min [TEAM B5]

    REQUESTED --> UNVERIFIED: no camera update / signals disagree [GAP C12]
    RESERVED --> UNVERIFIED
    PLATE_MISMATCH --> UNVERIFIED
    BLOCKED --> UNVERIFIED
    UNVERIFIED --> REQUESTED: signals agree again (previous state)
    UNVERIFIED --> CANCELLED: cancel / reroute

    ARRIVED --> CHARGING: charging started [GAP C3]
    ARRIVED --> COMPLETED: no charge after N min [TEAM]
    ARRIVED --> FAULT_REPORTED: "bay not working"
    CHARGING --> COMPLETED: stop / vehicle leaves

    COMPLETED --> [*]
    CANCELLED --> [*]
    NO_SHOW --> [*]
    FAILED --> [*]
    FAULT_REPORTED --> [*]
```

`UNVERIFIED` returns to whichever state it came from; the diagram shows only one return arrow to stay readable.

## 4. Full cycle sequence (S1 happy path)

The mandatory live cycle: reserve → arrive → charge → release.

```mermaid
sequenceDiagram
    autonumber
    actor D as Driver
    participant A as Driver app
    participant G as GoingElectric
    participant B as Our backend
    participant E as Ecurious server [GAP C2]
    participant H as Bay hardware + camera

    D->>A: open map
    A->>G: search by map box (key in client [GAP C8])
    G-->>A: charge points (static, no live availability)
    D->>A: pick test bay, reserve
    Note over A,B: How is the test bay linked to a GoingElectric ge_id? [GAP C8 Q4]
    A->>B: POST reservation (bay, plate)
    B->>B: check bay not out_of_service, state REQUESTED, log
    B->>E: reserve(bayId, reservationId, plate, until)
    E->>H: hold bay
    E-->>B: ok
    B->>B: RESERVED, store grace deadline [TEAM B4]
    B-->>A: reserved, countdown

    Note over D,H: driver drives to site (reminder before grace ends [TEAM B4])

    H->>E: plate read
    E-->>B: plate event (push or poll? [GAP C2], event types [GAP C4])
    B->>B: plate = booked: ARRIVED, stop timer, log
    B->>E: open barrier / release hold? [GAP C2]
    B-->>A: "checked in"

    D->>H: plug in
    Note over B,H: How do we learn charging started? Server, charger, or driver tap [GAP C3]
    E-->>B: charging started
    B->>B: CHARGING

    D->>H: unplug, leave
    E-->>B: charging stopped / plate gone [GAP C3, C4]
    B->>E: release(bayId, reservationId)
    E-->>B: ok
    B->>B: COMPLETED, log
    B-->>A: session summary
```

## 5. Plate event handling (S4, S7, S8)

What the backend does with any plate event while a reservation is `RESERVED`.

```mermaid
flowchart TD
    classDef gap stroke:#d33,stroke-width:2px,stroke-dasharray:5 4
    classDef team fill:#ffe3bf,stroke:#e8890c

    ev["Plate event (bayId, plate or null, confidence?)<br/>[GAP C4]"]:::gap
    ev --> read{"Plate read?"}
    read -- "no / low confidence [GAP C5]" --> mis
    read -- "yes" --> match{"= booked plate?"}
    match -- "yes" --> arr["ARRIVED"]
    match -- "no" --> mis["PLATE_MISMATCH<br/>app asks driver: 'Is this you?'"]
    mis --> ans{"Driver answer within N min"}
    ans -- "yes + code / QR [TEAM B6]" --> arr
    ans -- "no / timeout" --> blk["BLOCKED<br/>blocked_reason: combustion / EV idle / EV charging"]
    blk --> why{"Can we tell the case?<br/>charger status [GAP C3/C4], operator"}:::gap
    why --> act["Inform driver, offer reroute (GoingElectric),<br/>escalate after N min [TEAM B5]"]:::team
    ev -. "non-customer plate: keep what? [TEAM B6]" .-> gdpr["GDPR rule"]:::team
```

Key point for the pitch: the camera cannot tell "driver came in another car" from "stranger in my bay". Only the app can, by asking. Hence `PLATE_MISMATCH` before `BLOCKED`.

## Proposed additions [PROPOSAL]

Not yet discussed with the team. Each is small and fits the backend we already plan; drop any that do not fit the stack (B1).

| Proposal | What it does | Why | Diagram |
|---|---|---|---|
| Timer sweep | Store `grace_deadline` in the DB; a periodic job moves expired reservations to `NO_SHOW` | In-memory timers vanish on restart and leave bays held forever | 1 |
| Reconciliation loop | Every N s, compare our state with `status(bayId)`; log mismatches, alert operator | Hardware is source of truth; catches missed plate events [GAP C2 push/poll] | 1 |
| Partner webhooks | Push `reservation.reserved`, `reservation.no_show`, `bay.blocked` to a partner URL (or webhook.site in the demo) | Live interoperability proof for B8 without building a second app | 1, 2 |
| KPI read model | Build utilisation, no-show rate, blocked minutes from the event log | Utilisation and Business Case answers with real numbers from the demo | 1, 2 |

## Open items shown above

| Tag | Where it appears | What changes when answered |
|---|---|---|
| C2 Ecurious API | 1, 2, 4 | Real adapter, push vs poll, barrier call, whether plate is sent on `reserve` |
| C3 Charge step | 1, 2, 3, 4, 5 | `ARRIVED → CHARGING` trigger; blocked sub-case detection |
| C4 Plate events | 2, 3, 4, 5 | Mismatch, blocked, "vehicle leaves" transitions |
| C5 Plate testing | 5 | Low-confidence branch, S8 demo |
| C6 Shared test bay | 1 | Hardware time slots, more work on mock |
| C8 GoingElectric | 1, 4 | Web vs mobile (B1), key in client, bay ↔ `ge_id` mapping |
| C9 Venue network | 1 | Hosting, tunnel for webhooks |
| C12 Camera health | 1, 2, 3 | `UNVERIFIED` trigger beyond our own timeout |
| B1 Stack | 1 | App type, component technology column in docs |
| B4 No-show rules | 2, 3, 4 | Grace deadline, reminder, fee |
| B5 Blocked policy | 1, 3, 5 | Escalation, operator view |
| B6 Plate policy | 2, 3, 5 | Fallback check-in, what plate data is stored |
| B8 Interop depth | 1 | App B arrow: build or pitch only |
