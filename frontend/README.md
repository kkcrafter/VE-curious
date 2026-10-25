# Frontend

Plain HTML / CSS / JS, no build step. The backend serves this folder: `/` is `index.html`, `/static/*` is this folder. Run the backend (`../backend/README.md`) and open http://localhost:3000/.

The backend is the source of truth. API contract: [`docs/design/backend-outline.md`](../docs/design/backend-outline.md), section 3. Screens: [`docs/design/UX.md`](../docs/design/UX.md).

| File | Job |
|---|---|
| `app.js` | UI logic and every backend call (`api()`, `act()`) |
| `index.html`, `style.css` | Page skeleton, Ecurious look |
| `i18n/en.json`, `de.json` | All visible text. Backend error codes map to `err.<code>` |
| `sample_chargepoints.json` | Our test bay pin (not in GoingElectric) and all map stations when no key is set |
| `check_i18n.py` | `python check_i18n.py` before committing text changes |

## How it follows the backend

- Driver: email + password login (`POST /api/login`) on the booking tab; token in `localStorage`, sent as `Authorization: Bearer`. A 401 drops back to the login form. Map stays public.
- Buttons on the booking screen come from `allowedActions`; mapping to routes is `ACTIONS` in `app.js`. New backend actions (`confirm_arrival`, `deny_arrival`, `report_fault`) show up by themselves once the backend allows them.
- Countdown: `graceDeadline − serverTime`.
- Map stations: the browser calls GoingElectric directly (terms: device fetches, no backend copy) with the key from `GET /api/config` (`GOINGELECTRIC_API_KEY` in `backend/.env`). Map-box search, debounced, only at zoom ≥ 12. No key: sample data.
- Map pin: the station whose `ge_id` matches a bay's `geId`; while no bay has a `geId`, the sample's `reservable` station.
- Demo panel calls `/api/dev/*` (only with `ADAPTER=mock`).

## Hidden until the backend has it

Deposit and fee box (needs a payment ledger), booking code for unreadable plates, reminder banner, no-show (sweep), fault report, operator clear-fault, KPIs beyond bay status.
