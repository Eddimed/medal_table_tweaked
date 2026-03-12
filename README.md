# Medal Tables (Milano–Cortina 2026)

This folder contains a standalone, auto-updating medal-table site that adds a computed **EU27** row to the official standings for both the Olympics and Paralympics.

## What it does
- Fetches the Milano–Cortina 2026 Olympic and Paralympic medal tables from Wikipedia (MediaWiki REST API).
- Maps countries to IOC-style three-letter codes using a shared `ioc_codes.csv`.
- Sums medals for the 27 EU member states and inserts a computed **EU27** row for each event.
- Outputs CSV and JSON for both events.
- Provides a static HTML page that can switch between Olympic and Paralympic standings.
- Includes a GitHub Actions workflow to refresh both datasets on a schedule.

## Structure
```
medal_table_tweaked/
├── index.html
├── data/
│   ├── medals_eu.csv
│   ├── medals_eu.json
│   ├── medals_meta.json
│   ├── medals_eu_paralympics.csv
│   ├── medals_eu_paralympics.json
│   ├── medals_meta_paralympics.json
│   ├── ioc_codes.csv
│   └── eu_members.json
├── tools/
│   └── medals/
│       ├── fetch_medals.py
│       ├── etag_check.py
│       └── requirements.txt
└── .github/
    └── workflows/
        └── medals_eu_update.yml
```

## Run locally
```bash
cd (local Path)/medal_table_tweaked
python3 tools/medals/fetch_medals.py --event olympics --force
python3 tools/medals/fetch_medals.py --event paralympics --force
```

Serve the page locally (so `fetch()` works):
```bash
python3 -m http.server 8000
```
Open: `http://localhost:8000/index.html`

## GitHub Actions
The workflow runs every 30 minutes and performs a **fast ETag check** to skip full work when nothing changed.


## Data Access
Once published to GitHub Pages, the data files are publicly accessible and can be used as a lightweight API.

Example URLs (adjust to your repo/site):
- `https://<your-domain-or-user>.github.io/<repo>/data/medals_eu.json`
- `https://<your-domain-or-user>.github.io/<repo>/data/medals_eu.csv`
- `https://<your-domain-or-user>.github.io/<repo>/data/medals_eu_paralympics.json`
- `https://<your-domain-or-user>.github.io/<repo>/data/medals_eu_paralympics.csv`

Example (fetch JSON in the browser):
```js
fetch('https://<your-domain-or-user>.github.io/<repo>/data/medals_eu.json')
  .then(r => r.json())
  .then(console.log);
```
## Notes
- The EU27 row is computed from `data/eu_members.json` and uses the code `EU27`.
- `data/medals_eu.json` and `data/medals_eu.csv` remain the Olympic outputs for backward compatibility.
- `data/medals_eu_paralympics.json` and `data/medals_eu_paralympics.csv` hold the Paralympic outputs.
- `ioc_codes.csv` is shared by both event pipelines for now and is auto-populated from Wikipedia if empty.


## GitHub Pages Deployment
This repository is set up to be served from the **master** branch using GitHub Pages.

Required files:
- `index.html`
- `CNAME` containing `olympia.diabsurance.de`
- `.nojekyll`

DNS setup (at your domain provider):
- **Type:** CNAME
- **Host/Name:** `olympia`
- **Value/Target:** `eddimed.github.io`

After the DNS change propagates and the repo is pushed, the site will be reachable at:
- `https://olympia.diabsurance.de`

For the Paralympics entry point, use a domain redirect instead of a second GitHub Pages custom domain:
- `https://paralympics.diabsurance.de` should be configured at the DNS/domain provider as an HTTP 301/302 redirect to `https://olympia.diabsurance.de/paralympics/`
- Keep this repository `CNAME` file set to `olympia.diabsurance.de` only
- A plain DNS `CNAME` for `paralympics` is not sufficient, because it cannot append the `/paralympics/` path


## Commercial Use
Commercial use requires prior permission. Please contact us via:
- https://diabsurance.de/impressum.html
