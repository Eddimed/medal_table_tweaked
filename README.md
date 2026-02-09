# EU27 Medal Table (Milano–Cortina 2026)

This folder contains a standalone, auto-updating medal table that adds a computed **EU27** row to the official medal standings.

## What it does
- Fetches the Milano–Cortina 2026 medal table from Wikipedia (MediaWiki REST API).
- Maps countries to IOC NOC codes.
- Sums medals for the 27 EU member states and inserts a computed **EU27** row.
- Outputs both CSV and JSON for reuse.
- Provides a static HTML page that displays the enhanced table.
- Includes a GitHub Actions workflow to refresh the data on a schedule.

## Structure
```
medal_table_tweaked/
├── medal-table.html
├── data/
│   ├── medals_eu.csv
│   ├── medals_eu.json
│   ├── medals_meta.json
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
cd /home/bernd/Software/medal_table_tweaked
python3 tools/medals/fetch_medals.py --force
```

Serve the page locally (so `fetch()` works):
```bash
python3 -m http.server 8000
```
Open: `http://localhost:8000/olympics-eu.html`

## GitHub Actions
The workflow runs every 30 minutes and performs a **fast ETag check** to skip full work when nothing changed.


## Data Access
Once published to GitHub Pages, the data files are publicly accessible and can be used as a lightweight API.

Example URLs (adjust to your repo/site):
- `https://<your-domain-or-user>.github.io/<repo>/data/medals_eu.json`
- `https://<your-domain-or-user>.github.io/<repo>/data/medals_eu.csv`

Example (fetch JSON in the browser):
```js
fetch('https://<your-domain-or-user>.github.io/<repo>/data/medals_eu.json')
  .then(r => r.json())
  .then(console.log);
```
## Notes
- The EU27 row is computed from `data/eu_members.json` and uses the code `EU27`.
- `ioc_codes.csv` is auto-populated from Wikipedia if empty; you can replace it with a curated list if desired.
