# UX specification

What each screen shows in each situation. The code that implements this is `renderRes()` and `showDetail()` in `frontend/app.js`; the texts are in `frontend/i18n/`. Wireframes (earlier low-fi sketches from the team's design canvas): `wireframes/`. The built UI follows them loosely; **this document and the running app are the reference.**

Parts that need backend features not built yet (deposit, booking code, reminder banner, ledger, clear flag, fault report) are hidden in the app; see `frontend/README.md`.

## Principles

1. **One screen per question.** Map: "where?". Booking: "what is happening with my spot right now?". Operator: "what needs attention?".
2. **The Booking screen is one screen whose content follows the state.** The driver is standing at a charger with a phone: one big headline, at most one primary action, secondary actions small.
3. **Never show "free" when we are not sure.** `UNVERIFIED` is its own state with its own text. The map card disables the reserve button unless the bay is verified free.
4. **No-fee guarantee is visible.** Cancelling because of a blocked bay, an unverified bay or a fault never costs money, and the screen says so.
5. **Deposit rules are shown before reserving** (purple box on the booking form), not after.
6. **Our bay status is visually separate from GoingElectric data** (dark "Smart bay" block vs. white station card). Required by the GoingElectric terms.

## Navigation

```
Map ──tap pin──> station card ──"Reserve this bay"──> Booking (form)
                                                         │ Reserve
                                                         v
                                                  Booking (status, polled every 1.5 s)
Operator: separate tab, no login in the prototype
```

Bottom tab bar: Map · Booking · Operator. A small orange dot on "Booking" means the driver has to act (plate mismatch, blocked, unverified).

## Map screen

| Element | Behaviour |
|---|---|
| Map (Leaflet, light basemap) | Reloads stations 0.6 s after the map stops moving (debounced, GoingElectric terms: do not load the API unnecessarily) |
| Lime pin with glow | The one reservable smart bay. Always on top |
| Dark dot / purple dot | Fast charger (>= 50 kW) / AC charger |
| Legend (bottom left) | Reservable, Fast, AC |
| Hint block under the map | Shown until the first pin is tapped |
| Station card | Network label, name, address, plug chips, fault chip, **Smart bay block** (only for the reservable bay), GoingElectric link |
| Footer line | "Data: GoingElectric.de" (+ "sample data" when no API key) |

Smart bay block status text: `Free now` (green, button enabled) / `Reserved` / `Occupied` / `Unverified` / `Out of service` (orange, button disabled).

## Booking: form (no active reservation)

Name, licence plate (plate-style input), arrival in N minutes, deposit/no-show rule box, one primary button "Reserve bay". Error text appears under the button.

## Booking: status screen, per state

Dark card. Eyebrow = technical state name, headline = `state.<STATE>.title`, sub-line = `state.<STATE>.sub`. Progress bar (Reserved · Arrived · Charging · Done) for the happy path only.

| State | Headline (EN) | Extra content | Buttons (first = primary) |
|---|---|---|---|
| `RESERVED` | Bay held for you | Big countdown to end of grace period; reminder banner (orange) shortly before the end | Navigate · Cancel (no fee) · Bay not working |
| `PLATE_MISMATCH` | Is this you? | Booking code shown (demo; production: driver types it or scans a QR) | Yes, it's me · No |
| `BLOCKED` | Bay occupied | – | Cancel (no fee) · See alternatives (goes to map) |
| `UNVERIFIED` | Status unverified | – | Cancel (no fee) · See alternatives |
| `ARRIVED` | You're in | – | Plug in · start charging (simulated) · Bay not working |
| `CHARGING` | Charging | Count-up timer | Stop charging (simulated) |
| `COMPLETED` | Session finished | – | Reserve again |
| `CANCELLED` | Cancelled | – | Reserve again |
| `NO_SHOW` | No-show (red) | Says the deposit was kept | Reserve again |
| `FAILED` | Couldn't reserve (red) | – | Reserve again |
| `FAULT_REPORTED` | Bay reported | Says no fee | Reserve again |

Headline colour: lime = going well, soft orange = needs attention, red-orange = bad outcome. Defined in `STATE_CLS` (`app.js`).

Below the headline, always: a 2x2 info grid (Bay, Plate, Booking code, Deposit).

## Operator tab

KPI tiles (reservation state, camera vacant/occupied, barrier raised/lowered, bookings, no-shows, out of service), "Clear flag" button when the bay is out of service, event log (newest first), payment ledger (mock). No login in the prototype.

## Language

DE / EN button, top right. Every visible text goes through the dictionaries (see README).

## Not designed yet (ideas, if time)

- Login / profile screen (wireframes `03`, `04` exist), several plates per driver
- Session summary with receipt (`08`)
- Fault report with reason picker (currently one tap = "no power"; reasons exist in the i18n files)
- Alternatives list with one-tap rebook when blocked (currently: goes back to the map)
- Push notifications (currently in-app banner only)
