#!/usr/bin/env python3
import csv
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
import pycountry

MEDAL_URL = "https://en.wikipedia.org/w/rest.php/v1/page/2026_Winter_Olympics_medal_table/html"
IOC_CODES_URL = "https://en.wikipedia.org/wiki/List_of_IOC_country_codes"
USER_AGENT = "eddimed-medals-bot/1.0 (https://github.com/Eddimed/eddimed_webpage)"

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

IOC_CODES_CSV = DATA_DIR / "ioc_codes.csv"
EU_MEMBERS_JSON = DATA_DIR / "eu_members.json"
MEDALS_CSV = DATA_DIR / "medals_eu.csv"
MEDALS_JSON = DATA_DIR / "medals_eu.json"
META_JSON = DATA_DIR / "medals_meta.json"

NAME_OVERRIDES = {
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
    "United States": "United States of America",
    "United States of America": "United States of America",
    "Great Britain": "Great Britain",
    "Russia": "Russian Federation",
    "Korea": "South Korea",
    "Korea, South": "South Korea",
    "Korea, North": "North Korea",
    "People's Republic of China": "China",
    "Hong Kong": "Hong Kong, China",
    "Côte d'Ivoire": "Cote d'Ivoire",
    "Curaçao": "Curacao",
}

ISO2_OVERRIDES = {
    "EU27": "EU",
    "EU": "EU",
    "Great Britain": "GB",
    "United States of America": "US",
    "United States": "US",
    "Russia": "RU",
    "Russian Federation": "RU",
    "Czech Republic": "CZ",
    "Czechia": "CZ",
    "Türkiye": "TR",
    "Turkey": "TR",
    "South Korea": "KR",
    "North Korea": "KP",
    "Korea": "KR",
    "China": "CN",
    "People's Republic of China": "CN",
    "Hong Kong, China": "HK",
    "Hong Kong": "HK",
    "Cote d'Ivoire": "CI",
    "Côte d'Ivoire": "CI",
    "Viet Nam": "VN",
    "Vietnam": "VN",
    "Iran": "IR",
    "Iran, Islamic Republic of": "IR",
    "Moldova": "MD",
    "Bolivia": "BO",
    "Venezuela": "VE",
    "Syria": "SY",
}


def now_utc_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(value):
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"\[.*?\]", "", text)
    text = text.replace("\xa0", " ")
    text = text.replace("†", "").replace("‡", "").replace("*", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def name_key(value):
    text = normalize_text(value)
    text = NAME_OVERRIDES.get(text, text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    text = re.sub(r"[^a-zA-Z0-9 ]+", "", text).lower().strip()
    return text


def fetch_url(url):
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.text, resp.headers


def maybe_refresh_ioc_codes():
    if IOC_CODES_CSV.exists():
        with IOC_CODES_CSV.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if any(row.get("noc") for row in reader):
                return

    html, _ = fetch_url(IOC_CODES_URL)
    tables = pd.read_html(StringIO(html))
    target = None
    for df in tables:
        cols = [str(c).strip().lower() for c in df.columns]
        if "code" in cols and any("national olympic committee" in c for c in cols):
            target = df
            break
    if target is None:
        raise RuntimeError("Could not find IOC codes table on Wikipedia.")

    col_map = {str(c).strip().lower(): c for c in target.columns}
    code_col = col_map.get("code")
    noc_col = None
    for c in target.columns:
        if "national olympic committee" in str(c).strip().lower():
            noc_col = c
            break
    rows = []
    for _, row in target.iterrows():
        code = normalize_text(row.get(code_col))
        name = normalize_text(row.get(noc_col))
        if not code or len(code) != 3:
            continue
        rows.append((code, name))

    IOC_CODES_CSV.write_text("noc,country_name\n", encoding="utf-8")
    with IOC_CODES_CSV.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        for code, name in sorted(set(rows)):
            writer.writerow([code, name])


def load_ioc_codes():
    maybe_refresh_ioc_codes()
    noc_to_name = {}
    name_to_noc = {}
    with IOC_CODES_CSV.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            noc = normalize_text(row.get("noc"))
            name = normalize_text(row.get("country_name"))
            if not noc or not name:
                continue
            noc_to_name[noc] = name
            name_to_noc[name_key(name)] = noc
    return noc_to_name, name_to_noc


def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for col in df.columns:
            if isinstance(col, tuple):
                parts = [normalize_text(c) for c in col if normalize_text(c)]
                new_cols.append(parts[-1] if parts else "")
            else:
                new_cols.append(normalize_text(col))
        df.columns = new_cols
    else:
        df.columns = [normalize_text(c) for c in df.columns]
    return df



def pick_medal_table(html):
    tables = pd.read_html(StringIO(html))
    for df in tables:
        df = flatten_columns(df.copy())
        cols = [str(c).strip().lower() for c in df.columns]
        if {"gold", "silver", "bronze", "total"}.issubset(set(cols)):
            if any(c in cols for c in ["nation", "noc", "team", "country", "country/region", "country or region"]):
                return df
            return df
    raise RuntimeError("Could not find medal table with required columns.")


def parse_medal_table(html, name_to_noc, noc_to_name):
    df = pick_medal_table(html)
    df = flatten_columns(df)

    colnames = [str(c).strip().lower() for c in df.columns]
    col_map = {str(c).strip().lower(): c for c in df.columns}

    def find_col(*candidates):
        for cand in candidates:
            for col in colnames:
                if cand in col:
                    return col_map.get(col)
        return None

    rank_col = find_col("rank", "rk")
    nation_col = find_col("nation", "team", "country")
    noc_col = find_col("noc")

    medal_cols = {find_col("gold"): "gold", find_col("silver"): "silver", find_col("bronze"): "bronze", find_col("total"): "total"}
    medal_cols = {k: v for k, v in medal_cols.items() if k}

    if nation_col is None:
        for col in df.columns:
            if col in medal_cols or col == rank_col or col == noc_col:
                continue
            nation_col = col
            break

    if nation_col is None and noc_col is not None:
        sample_values = [normalize_text(v) for v in df[noc_col].head(5).tolist()]
        if any(v and len(v) > 3 for v in sample_values):
            nation_col = noc_col
            noc_col = None

    def to_int(value):
        text = normalize_text(value)
        text = re.sub(r"[^0-9]", "", text)
        return int(text) if text else 0

    rows = []
    unmapped = []

    for _, row in df.iterrows():
        country_raw = normalize_text(row.get(nation_col)) if nation_col else ""
        noc_raw = normalize_text(row.get(noc_col)) if noc_col else ""
        country = NAME_OVERRIDES.get(country_raw, country_raw)

        if not country or country.lower().startswith("total"):
            continue

        gold = to_int(row.get(find_col("gold")))
        silver = to_int(row.get(find_col("silver")))
        bronze = to_int(row.get(find_col("bronze")))
        total = to_int(row.get(find_col("total")))
        if total == 0:
            total = gold + silver + bronze

        noc = noc_raw
        if not noc or len(noc) != 3:
            noc = name_to_noc.get(name_key(country))
        if not noc:
            unmapped.append(country)
            continue

        country_name = noc_to_name.get(noc, country)

        iso2 = iso2_from_country(country_name)
        flag_url = f"https://flagcdn.com/w40/{iso2.lower()}.png" if iso2 else None

        rows.append(
            {
                "rank": to_int(row.get(rank_col)) if rank_col else None,
                "country": country_name,
                "noc": noc,
                "iso2": iso2,
                "flag_url": flag_url,
                "gold": gold,
                "silver": silver,
                "bronze": bronze,
                "total": total,
            }
        )

    return rows, sorted(set(unmapped))


def compute_rank(rows):
    rows_sorted = sorted(
        rows,
        key=lambda r: (-r["gold"], -r["silver"], -r["bronze"], -r["total"], r["country"]),
    )
    rank = 0
    prev_key = None
    for idx, row in enumerate(rows_sorted, start=1):
        key = (row["gold"], row["silver"], row["bronze"], row["total"])
        if key != prev_key:
            rank = idx
            prev_key = key
        row["rank"] = rank
    return rows_sorted


def iso2_from_country(country_name):
    if not country_name:
        return None
    if country_name in ISO2_OVERRIDES:
        return ISO2_OVERRIDES[country_name]
    try:
        match = pycountry.countries.search_fuzzy(country_name)[0]
        return match.alpha_2
    except Exception:
        return None


def load_eu_members():
    data = load_json(EU_MEMBERS_JSON, {"members": []})
    return [m for m in data.get("members", []) if m.get("eu_member")]


def add_eu_row(rows, eu_members):
    eu_nocs = {m["noc"] for m in eu_members if m.get("noc")}
    gold = sum(r["gold"] for r in rows if r["noc"] in eu_nocs)
    silver = sum(r["silver"] for r in rows if r["noc"] in eu_nocs)
    bronze = sum(r["bronze"] for r in rows if r["noc"] in eu_nocs)
    total = gold + silver + bronze

    for r in rows:
        r["is_eu"] = r["noc"] in eu_nocs

    rows.append(
        {
            "rank": None,
            "country": "European Union",
            "noc": "EU27",
            "iso2": "EU",
            "flag_url": "https://flagcdn.com/w40/eu.png",
            "gold": gold,
            "silver": silver,
            "bronze": bronze,
            "total": total,
            "is_eu": True,
        }
    )


def write_outputs(rows, meta, unmapped):
    rows = compute_rank(rows)

    with MEDALS_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "rank",
                "country",
                "noc",
                "iso2",
                "flag_url",
                "gold",
                "silver",
                "bronze",
                "total",
                "is_eu",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    medals_payload = {
        "last_updated_utc": now_utc_iso(),
        "source_url": MEDAL_URL,
        "source_revision_id": meta.get("last_revision_id"),
        "source_retrieved_at_utc": meta.get("last_update_utc"),
        "rows": rows,
    }
    save_json(MEDALS_JSON, medals_payload)

    meta["unmapped_countries"] = unmapped
    save_json(META_JSON, meta)


def main():
    force = "--force" in sys.argv

    meta = load_json(
        META_JSON,
        {
            "last_etag": None,
            "last_modified": None,
            "last_revision_id": None,
            "last_update_utc": None,
            "source_url": MEDAL_URL,
            "unmapped_countries": [],
        },
    )

    html, headers = fetch_url(MEDAL_URL)
    etag = headers.get("ETag")
    last_modified = headers.get("Last-Modified")

    if not force:
        if etag and meta.get("last_etag") == etag:
            print("No changes detected (ETag).")
            return 0
        if last_modified and meta.get("last_modified") == last_modified:
            print("No changes detected (Last-Modified).")
            return 0

    meta["last_etag"] = etag
    meta["last_modified"] = last_modified
    meta["last_revision_id"] = etag or meta.get("last_revision_id")
    meta["last_update_utc"] = now_utc_iso()
    meta["source_url"] = MEDAL_URL

    noc_to_name, name_to_noc = load_ioc_codes()
    rows, unmapped = parse_medal_table(html, name_to_noc, noc_to_name)

    if unmapped:
        meta["unmapped_countries"] = unmapped
        save_json(META_JSON, meta)
        raise RuntimeError(f"Unmapped countries: {', '.join(unmapped)}")

    eu_members = load_eu_members()
    add_eu_row(rows, eu_members)
    write_outputs(rows, meta, unmapped)

    print("Medal table updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
