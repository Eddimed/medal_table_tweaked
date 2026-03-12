#!/usr/bin/env python3
import json
import os
import sys
import urllib.request

USER_AGENT = "eddimed-medals-bot/1.0 (https://github.com/Eddimed/eddimed_webpage)"

from events import default_event_key, get_event_config


def load_meta(meta_path):
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return {}


def fetch_headers(url):
    req = urllib.request.Request(url, method="HEAD")
    req.add_header("User-Agent", USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.headers
    except Exception:
        # Fallback to GET if HEAD is not supported
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", USER_AGENT)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.headers


def write_output(changed):
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            fh.write(f"changed={str(changed).lower()}\n")


def parse_args(argv):
    event_key = default_event_key()

    idx = 0
    while idx < len(argv):
        arg = argv[idx]
        if arg.startswith("--event="):
            event_key = arg.split("=", 1)[1].strip()
            idx += 1
            continue
        if arg == "--event":
            if idx + 1 >= len(argv):
                raise SystemExit("--event requires a value")
            event_key = argv[idx + 1].strip()
            idx += 2
            continue
        raise SystemExit(f"Unknown argument: {arg}")

    return event_key


def main():
    event = get_event_config(parse_args(sys.argv[1:]))
    meta = load_meta(event["meta_path"])
    headers = fetch_headers(event["medal_url"])

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
