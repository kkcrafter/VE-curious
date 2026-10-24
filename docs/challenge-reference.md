# Challenge Reference

Source: `challenge-brief.pdf` (Ecurious). Summary only; the PDF wins if anything differs.

## Setup

- **Reservation hardware** at a test bay: keeps the bay free for the driver who booked.
- **Built-in camera**: license plate recognition (which vehicle stands in the bay).
- **Ecurious server**: our access point to the hardware – reserve, release, status, plate events. Credentials and API docs only on site.
- **GoingElectric**: public charge point data (locations, connectors, power) for map and search. https://www.goingelectric.de/stromtankstellen/

## Mandatory

Core integration: app ↔ Ecurious server ↔ reservation hardware.

## Deliverables

1. Charging app prototype (mobile or web) that shows public charge points from GoingElectric.
2. Full live reservation cycle on the hardware: reserve → arrive (check-in via plate recognition) → charge → release.
3. Documentation: architecture, API calls, data flows, design decisions, tools used, what did not work.
4. Answers to at least two mission areas.
5. Limitations and ideas for scaling to other apps, operators and locations.

"A polished app is a bonus – not a requirement."

## Mission areas (pick ≥ 2)

| Area | Core question |
|---|---|
| No-Shows | Driver reserves but never arrives: grace period, detection (GPS, ETA, check-in), fair pricing |
| Blocked Bays | Car already in bay: combustion car / EV not charging / EV still charging. Detection, informing or rerouting, escalation |
| License Plate Recognition | Link plate to reservation, different car, auto actions, recognition errors, GDPR |
| Interoperability | Access for other apps (open API, OCPI, OCPP), deep links, roaming, app A ↔ app B |
| New Use Cases | Events, retail, hotels, workplaces, fleets, loyalty perk |
| Utilisation | Reservations increase use instead of idle bays. KPIs for CPOs |
| Business Case | Who pays, pricing model, value of a guaranteed spot |

## Scoring (1–5 per criterion, weighted to 100)

| Criterion | Weight | Jury looks for |
|---|---|---|
| Technical Implementation | 30% | Working integration, full live cycle, edge cases (no-show, blocked bay, plate errors), code quality |
| Solution Concept & Innovation | 20% | Smart answers to mission areas, creative plate recognition use, new use cases |
| Interoperability & Scalability | 15% | Open API, OCPI/OCPP, transfer to other locations and hardware |
| Business Case & CPO Value | 20% | Plausible pricing, value for drivers and CPOs, effect on utilisation |
| Documentation & Pitch | 15% | Complete process docs incl. what did not work; convincing live demo |

- Full cycle on hardware = prerequisite for top ranks.
- Tie-breaker: Technical Implementation score.
- GDPR violations can cost points.

## Rules (Fair Play & Safety, plus event conduct rules)

- Use only the hardware and server access provided. Do not touch public or production infrastructure.
- Respect GoingElectric terms of use.
- Treat user, location and plate data per GDPR.
- AI tools allowed, but declare them. Declare external sources. (Event conduct rules, from earlier discussion.)
- Work fairly and collaboratively within the team.

## Standards for inspiration

- OCPP: `ReserveNow`, `CancelReservation`
- OCPI: reservation commands (check exact names in the spec before use)

Prize: €1,000.
