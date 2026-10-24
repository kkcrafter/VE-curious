# Hackathon Playbook (event-day practices)

Distilled from the [Hackathon Starter Pack](https://github.com/udaysharmadev/Hackathon-Starter-Pack-Complete-Guide-Roadmap) (MIT), sections 07, 08, 10, 11, 20, 28. Adapted to our setup: one day, real hardware at the venue, a jury that rewards documentation and honesty over polish. Generic parts (finding hackathons, idea selection, resume, monetization) skipped – our challenge is fixed.

Declare this source in `templates/declaration-log.md`.

## 1. Demo fallback ladder

Most important idea. Our demo depends on venue Wi-Fi, the Ecurious server and the test bay. Any of them can fail.

| Level | What runs | When |
|---|---|---|
| 1 | Live: app → backend → Ecurious → hardware | Default |
| 2 | Same app with **mock adapter** (`?demo=1` or env flag), visibly labelled "simulated hardware" | Ecurious server or bay down |
| 3 | Recorded video of S1 (and one edge case) on real hardware | Laptop or network down |
| 4 | Screenshots in slides + event log excerpt | Everything down |

Consequence: the mock hardware (A3) is not only for development – it is our demo kill-switch. Build it switchable from day one. Always label mock mode; the jury will ask "what is real and what is mocked?".

## 2. Demo rules

- Golden path only, under 2 minutes: S1, then one edge case (S3, S4 or S7).
- Seed everything: driver logged in, plate stored, bay already on the map. No sign-up on stage, no live typing.
- Narrate before clicking: "I reserve this bay – watch the hardware."
- Show the event log on a second screen or tab: proves real API calls.
- One speaker; another person drives the laptop.

## 3. Pre-demo checks

**30 min before**
- [ ] Full cycle from clean state on the demo laptop and venue network
- [ ] Bay reset to free; test plate / test car ready (C5)
- [ ] Mock mode tested as fallback
- [ ] Video and screenshots exported, opened once

**15 min before**
- [ ] Close other tabs and apps, notifications off
- [ ] Phone hotspot ready as network backup
- [ ] Tabs open: app, event log, slides

**Pre-submit (≥ 30 min before 18:00)** – deliverables and deployment: `submission-deliverables.md`
- [ ] Repo builds from a clean clone; `.env.example` complete; no secrets committed
- [ ] README: how to run, architecture link, live demo link or video
- [ ] Documentation sections filled, incl. "what did not work"
- [ ] Declaration log complete

## 4. AI coding guardrails

- One agent, one task. Small, reviewable diffs.
- Ask the agent to run the code or tests and show output. Do not trust "done".
- Human review for: Ecurious adapter, plate/GDPR handling, `.env`, anything that touches credentials.
- Commit after each working step, so a bad agent run is one `git revert`.
- Everyone must be able to explain any line to the jury. Rotate who drives the AI.
- Log AI use as you go (declaration log).

Quick review of AI-generated code: does it run; hardcoded URLs, plates or keys; happy-path-only error handling; wrong imports; secrets in client code.

## 5. Progress checks and scope cuts

Our gates G0–G4 are in `prep-plan.md`. Add a quick colour check every hour: green (on track), yellow (focus on next gate), red (cut scope now).

Scope reduction ladder for our project – cut from the top, never the bottom:

1. Map polish, filters, photos
2. Interoperability demo (keep as API naming + pitch slide)
3. Blocked-bay sub-cases S5/S6 (pitch only)
4. Push notifications (in-app status only)
5. No-show fee logic (keep timer + release)
6. **Never cut:** S1 full cycle on hardware

New feature test: under 30 min? Strengthens the demo? Cannot demo without it? Otherwise defer.

## 6. Team split (adapt to B2)

| Size | Split |
|---|---|
| 2 | A: backend + Ecurious adapter + state machine. B: frontend + GoingElectric map + docs/pitch |
| 3 | + C: business case, KPIs, docs, pitch, demo recording, testing scenarios |
| 4 | + D: mock hardware, interoperability API, deployment, fallback |

Rules: agree data shapes early (reservation object, adapter contract); separate folders per person; commit often; never break `main`.

## 7. Bug triage

| Priority | Examples | Action |
|---|---|---|
| P0 | Cycle broken, data lost, credentials exposed | Fix now |
| P1 | Jury will see it in the demo | Fix before G4 |
| P2 | Edge case outside demo path | Fix if time; else document |
| P3 | Cosmetic | Ignore; maybe document |

Rule: 5-minute fix → fix. Long fix and avoidable in demo → work around and write it in "what did not work". Our jury rewards that list.

## 8. Pitch

3-minute structure mapped to our scoring (adjust once time limit known, C10):

| Time | Content | Criterion |
|---|---|---|
| 0:00–0:20 | Problem: driver arrives, bay taken | – |
| 0:20–1:40 | Live demo: S1 + one edge case | Technical 30% |
| 1:40–2:10 | Mission-area answers, plate recognition idea | Concept 20% |
| 2:10–2:35 | Who pays, KPIs (assumptions labelled) | Business 20% |
| 2:35–2:50 | Open API, OCPP/OCPI, other sites | Interop 15% |
| 2:50–3:00 | Close: one sentence + repo link / QR | Docs 15% |

Start with the problem, not team introductions. End 10 s early.

## 9. Likely jury questions (prepare answers)

1. What is real and what is mocked?
2. What happens when the Ecurious server or camera fails?
3. Where is plate data stored, for how long, who sees it?
4. How does a driver using another app (app B) get recognised on site?
5. Who pays, and why would a CPO adopt this?
6. How do you know reservations increase utilisation and not idle time?
7. What breaks with 100 bays or 10 operators?
8. What did each teammate own?
9. What was the hardest problem, and what did not work?
10. How did you use AI tools?

Answer pattern: direct answer → evidence (log, demo, number) → honest limit. Never bluff a live capability.
