#!/usr/bin/env python3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

EVENTS = {
    "olympics": {
        "key": "olympics",
        "page_slug": "2026_Winter_Olympics_medal_table",
        "page_title": "Milano-Cortina 2026 Olympics",
        "games_label": "Milano-Cortina 2026",
        "event_label": "Olympics",
        "hero_title": "Olympic Medal Table",
        "source_label": "Wikipedia (Olympic Medal Table)",
        "json_path": DATA_DIR / "medals_eu.json",
        "csv_path": DATA_DIR / "medals_eu.csv",
        "meta_path": DATA_DIR / "medals_meta.json",
        "featured": False,
    },
    "paralympics": {
        "key": "paralympics",
        "page_slug": "2026_Winter_Paralympics_medal_table",
        "page_title": "Milano-Cortina 2026 Paralympics",
        "games_label": "Milano-Cortina 2026",
        "event_label": "Paralympics",
        "hero_title": "Paralympic Medal Table",
        "source_label": "Wikipedia (Paralympic Medal Table)",
        "json_path": DATA_DIR / "medals_eu_paralympics.json",
        "csv_path": DATA_DIR / "medals_eu_paralympics.csv",
        "meta_path": DATA_DIR / "medals_meta_paralympics.json",
        "featured": True,
    },
}


def event_names():
    return ", ".join(sorted(EVENTS))


def get_event_config(event_key):
    try:
        event = EVENTS[event_key]
    except KeyError as exc:
        raise SystemExit(f"Unknown event '{event_key}'. Expected one of: {event_names()}") from exc

    return {
        **event,
        "medal_url": f"https://en.wikipedia.org/w/rest.php/v1/page/{event['page_slug']}/html",
    }


def default_event_key():
    for key, event in EVENTS.items():
        if event.get("featured"):
            return key
    return "olympics"
