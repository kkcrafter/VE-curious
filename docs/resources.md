# Resources

## Generic hackathon toolkits

| Resource | Worth it for us? | Read |
|---|---|---|
| [Hackathon Starter Pack](https://github.com/udaysharmadev/Hackathon-Starter-Pack-Complete-Guide-Roadmap) | Yes, selectively. Distilled into `hackathon-playbook.md` | 10 Deployment, 11 Presentation, 28 Testing, 08 Build Fast, 07 Vibe Coding |
| [ShiftKey Labs hackathon-101](https://github.com/shiftkey-labs/hackathon-101) | Low. Beginner guide for students, last update Jan 2025 | Skim only |
| [MLH + GitHub hackathon starters](https://github.blog/developer-skills/career-growth/make-your-next-hackathon-a-success-with-mlh-and-github) | Low. Old Flask / Node starter templates | Only if B1 picks Flask or Node and the team wants a skeleton |
| [awesome-hackathon](https://github.com/ArikRahman/awesome-hackathon) | No. Aimed at organisers | – |

Generic toolkits mostly help with idea finding and polish. Our challenge is fixed, and the jury rewards integration, edge cases and documentation. Domain material below is more valuable.

## Domain material (higher value)

| Resource | Why | Link |
|---|---|---|
| GoingElectric API docs + terms | Map data, design constraints | `design/goingelectric.md` |
| OCPP (Open Charge Alliance) | `ReserveNow`, `CancelReservation` message shapes for our API naming (A8) | https://openchargealliance.org/ |
| OCPI (EVRoaming Foundation) | Reservation commands for app A ↔ app B interop (A8) | https://github.com/ocpi/ocpi |

TODO (A8): read the reservation parts of OCPP 1.6 / 2.0.1 and the OCPI commands module; note exact field names in `design/state-machine.md`.
