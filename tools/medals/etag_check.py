#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
from pathlib import Path

MEDAL_URL = "https://en.wikipedia.org/w/rest.php/v1/page/2026_Winter_Olympics_medal_table/html"
USER_AGENT = "eddimed-medals-bot/1.0 (https://github.com/Eddimed/eddimed_webpage)"

BASE_DIR = Path(__file__).resolve().parents[2]
META_JSON = BASE_DIR / "data" / "medals_meta.json"


def load_meta():
    if META_JSON.exists():
        return json.loads(META_JSON.read_text(encoding="utf-8"))
    return {}


def fetch_headers():
    req = urllib.request.Request(MEDAL_URL, method="HEAD")
    req.add_header("User-Agent", USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.headers
    except Exception:
        # Fallback to GET if HEAD is not supported
        req = urllib.request.Request(MEDAL_URL, method="GET")
        req.add_header("User-Agent", USER_AGENT)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.headers


def write_output(changed):
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            fh.write(f"changed={str(changed).lower()}\n")


def main():
    meta = load_meta()
    headers = fetch_headers()

    etag = headers.get("ETag")
    last_modified = headers.get("Last-Modified")

    changed = True
    if etag and meta.get("last_etag") == etag:
        changed = False
    elif last_modified and meta.get("last_modified") == last_modified:
        changed = False

    write_output(changed)
    if changed:
        print("changed=true")
        return 0

    print("changed=false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
