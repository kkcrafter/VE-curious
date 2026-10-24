# Frontend

Plain HTML / CSS / JS, no build step. The backend serves this folder: `/` is `index.html`, `/static/*` is this folder. Run the backend (`../backend/README.md`) and open http://localhost:3000/.

The backend is the source of truth. API contract: [`docs/design/backend-outline.md`](../docs/design/backend-outline.md) §3. Screens: [`docs/design/UX.md`](../docs/design/UX.md).

| File | Job |
|---|---|
| `app.js` | UI logic and every backend call (`api()`, `act()`) |
| `index.html`, `style.css` | Page skeleton, Ecurious look |
| `i18n/en.json`, `de.json` | All visible text. Backend error codes map to `err.<code>` |
| `sample_chargepoints.json` | Map stations until the GoingElectric key exists [GAP C8] |
| `check_i18n.py` | `python check_i18n.py` before committing text changes |

## How it follows the backend

- Driver: `X-Driver-Id` header from the demo driver picker (`d1`, `d2` seeded by the backend).
- Buttons on the booking screen come from `allowedActions`; mapping to routes is `ACTIONS` in `app.js`. New backend actions (`confirm_arrival`, `deny_arrival`, `report_fault`) show up by themselves once the backend allows them.
- Countdown: `graceDeadline − serverTime`.
- Map pin: the station whose `ge_id` matches a bay's `geId`; while no bay has a `geId`, the sample's `reservable` station.
- Demo panel calls `/api/dev/*` (only with `ADAPTER=mock`).

## Hidden until the backend has it

Deposit and fee box (ledger, B4), booking code (B6), reminder banner, no-show (sweep), fault report, operator clear-fault, KPIs beyond bay status, live GoingElectric data.
