# GoingElectric API – Findings (A9)

Sources, read 2026-10-23:
- Overview: https://www.goingelectric.de/stromtankstellen/api/
- Docs: https://www.goingelectric.de/stromtankstellen/api/docs/
- Terms: https://www.goingelectric.de/stromtankstellen/api/terms/
- Access request: https://www.goingelectric.de/stromtankstellen/api/new/ (needs a GoingElectric account)

## Access

- **API key required** for every request (`key` GET parameter).
- Free at the moment.
- "Vorerst … auf Apps beschränkt" – currently limited to apps. Unclear if a web app counts. [GAP C8]
- Lead time for approval unknown. Request early, or ask whether Ecurious provides a key for the hackathon. [GAP C8]
- Contact for questions: info@goingelectric.de. Terms say: ask in advance if unsure whether the app complies.

## Endpoints

Base: `https://api.goingelectric.de/chargepoints/`

| Endpoint | Use | Key params |
|---|---|---|
| `/chargepoints/` | Search by position + radius | `lat`, `lng`, `radius` (km, integer) |
| `/chargepoints/` | Search by map box | `sw_lat`, `sw_lng`, `ne_lat`, `ne_lng` |
| `/chargepoints/` | Details | `ge_id` (up to 10; up to 100 with `result_details=minimal`) |
| `/chargepoints/photo/` | Photo | `id`, `size` (max 1000) or `width` + `height` |
| `/chargepoints/pluglist/` | Plug types | – (refresh on app start, list changes) |
| `/chargepoints/networklist/` | Networks | `countries` |
| `/chargepoints/chargecardlist/` | Charge cards / apps | `countries` |

Useful filters: `plugs`, `countries` (ISO alpha-2), `min_power`, `open_now`, `verified`, `exclude_faults`, `orderby=distance|power`, `freeparking`, `freecharging`.

- Max 500 locations per response; `startkey` for next page.
- Server-side clustering: `clustering=true`, `zoom` (0–21), `cluster_distance`.

Response (search), shortened:

```json
{"status":"ok","chargelocations":[{
  "ge_id":3, "name":"Karlsplatz",
  "address":{"street":"…","postcode":"34117","country":"Deutschland","city":"Kassel"},
  "chargepoints":[{"count":4,"power":22,"type":"Typ2"}],
  "coordinates":{"lng":9.494378,"lat":51.312454},
  "fault_report":false, "network":"Ladenetz",
  "url":"//www.goingelectric.de/stromtankstellen/…/3/", "verified":true }]}
```

Details add `operator`, `cost`, `openinghours`, `chargecards`, `fault_report` text, `location_description`.

No live availability (free / occupied). Only static data + fault reports. Availability of our bay comes from Ecurious `status`.

## Terms that affect our design

| Rule (summary of terms) | Consequence for us |
|---|---|
| Data must be fetched **directly from the end device** and stored there **max 24 h** | **Changes the earlier architecture:** no backend cache of GoingElectric data. The client calls GoingElectric. Backend only handles reservations. |
| If stored on device > 1 h, show fetch time | Show "data from HH:MM" or keep cache < 1 h |
| Free for end user, no registration needed | Map/search must work without login. Login only for reserving |
| Show data source readably | "Data: GoingElectric.de" on map and detail |
| Clearly visible, clickable link to the entry | Link from each detail view to `url` |
| Mark which data comes from which source when mixed | Our bay status (Ecurious) visibly separate from GoingElectric data |
| Key secret, only for the registered app | Key in `.env`, never in repo. Note: in a browser app the key is visible in requests – tension with "secret". Ask GoingElectric [GAP C8] |
| Data only in the registered app, not passed to third parties | Do not expose GoingElectric data through our own API (relevant for interoperability: share reservations, not station data) |
| Do not load the API unnecessarily | Use map-box search + clustering; debounce map moves |
| "GoingElectric" not in app name | Pick a neutral app name |
| Breach: €10 per affected record | Take the rules seriously |

## Open questions [GAP C8]

1. Does a web app qualify ("currently limited to apps")?
2. How long does key approval take? Does Ecurious already have a key for teams?
3. Browser app: is a visible key in client requests acceptable? If not, is a thin pass-through proxy (no storage) allowed?
4. Is mapping the Ecurious test bay to a GoingElectric `ge_id` intended, or does the test bay not exist in GoingElectric (venue only)?
5. Favourites: may the app keep only the station ID (`ge_id`) plus a user label on the device beyond 24 h, fetching the station data fresh each time?
