#!/usr/bin/env python3
"""
Backfill song data for concerts missing setlists.

Strategy:
  1. Concerts with setlist.fm ID but no songs → re-fetch by ID
  2. Concerts without ID → search setlist.fm by artist + date
  3. Extract songs, update setlist.json

Rate limit: setlist.fm allows ~2 req/sec. Budget controls how many to process per run.

Usage: python scripts/backfill_setlist_songs.py
Env: SETLIST_FM_API_KEY (required)
     SETLIST_SONG_BUDGET (optional, default 50)
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from utils import retry_request

API_KEY = os.environ.get("SETLIST_FM_API_KEY")
BASE = "https://api.setlist.fm/rest/1.0"
BUDGET = int(os.environ.get("SETLIST_SONG_BUDGET", "50"))
REQUEST_DELAY = 0.6  # seconds between API calls

if not API_KEY:
    print("No SETLIST_FM_API_KEY set, skipping setlist song backfill")
    exit(0)

HEADERS = {"Accept": "application/json", "x-api-key": API_KEY}


def api_get(url, params=None):
    """Rate-limited API request."""
    time.sleep(REQUEST_DELAY)
    resp = retry_request("get", url, headers=HEADERS, params=params, timeout=15)
    if resp and resp.status_code == 200:
        return resp.json()
    if resp and resp.status_code == 429:
        print("  Rate limited, waiting 10s...")
        time.sleep(10)
        resp = retry_request("get", url, headers=HEADERS, params=params, timeout=15)
        if resp and resp.status_code == 200:
            return resp.json()
    return None


def extract_songs(setlist_data):
    """Extract song list from setlist.fm API response."""
    songs = []
    for s in setlist_data.get("sets", {}).get("set", []):
        for song in s.get("song", []):
            name = song.get("name", "")
            if name:
                songs.append(name)
    return songs


def fetch_by_id(setlist_id):
    """Fetch a setlist directly by ID."""
    data = api_get(f"{BASE}/setlist/{setlist_id}")
    if data:
        return extract_songs(data), data.get("id", setlist_id)
    return [], setlist_id


def search_by_artist_date(artist, date_iso):
    """Search for a setlist by artist name + date. Returns (songs, setlist_id)."""
    # setlist.fm date format: dd-MM-yyyy
    if len(date_iso) == 10 and date_iso[4] == "-":
        date_sfm = f"{date_iso[8:10]}-{date_iso[5:7]}-{date_iso[0:4]}"
    else:
        return [], ""

    data = api_get(f"{BASE}/search/setlists", {
        "artistName": artist,
        "date": date_sfm,
    })

    if not data:
        return [], ""

    setlists = data.get("setlist", [])
    if not setlists:
        return [], ""

    # Find best match — prefer one with songs
    best = None
    best_songs = []
    for sl in setlists:
        songs = extract_songs(sl)
        sl_artist = sl.get("artist", {}).get("name", "").lower()
        # Match artist name (case-insensitive, partial match for "feat." etc.)
        if artist.lower() in sl_artist or sl_artist in artist.lower():
            if songs:
                return songs, sl.get("id", "")
            if not best:
                best = sl

    # Return best match even without songs (gets us the ID for future lookups)
    if best:
        return [], best.get("id", "")

    return [], ""


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    setlist_file = os.path.join(data_dir, "setlist.json")

    with open(setlist_file) as f:
        concerts = json.load(f)

    # Categorize
    with_songs = []
    need_refetch = []  # has ID, no songs
    need_search = []   # no ID, no songs

    for c in concerts:
        if c.get("songs") and len(c["songs"]) > 0:
            with_songs.append(c)
        elif c.get("id"):
            need_refetch.append(c)
        else:
            need_search.append(c)

    print(f"=== Setlist Song Backfill ===")
    print(f"  Already have songs: {len(with_songs)}")
    print(f"  Re-fetch by ID: {len(need_refetch)}")
    print(f"  Search by artist+date: {len(need_search)}")
    print(f"  Budget: {BUDGET} lookups")

    # Build lookup map for updating
    concert_map = {}
    for i, c in enumerate(concerts):
        key = f"{c['artist']}||{c['date']}"
        concert_map[key] = i

    enriched = 0
    ids_found = 0
    api_calls = 0

    # Phase 1: Re-fetch by ID (cheap, reliable)
    for c in need_refetch:
        if api_calls >= BUDGET:
            break
        songs, sid = fetch_by_id(c["id"])
        api_calls += 1
        if songs:
            idx = concert_map.get(f"{c['artist']}||{c['date']}")
            if idx is not None:
                concerts[idx]["songs"] = songs
                concerts[idx]["song_count"] = len(songs)
                enriched += 1
                print(f"  ✅ ID {c['id']}: {c['artist']} — {len(songs)} songs")
        else:
            print(f"  ⬜ ID {c['id']}: {c['artist']} — no setlist yet")

    # Phase 2: Search by artist + date (slower, may not match)
    # Sort by date descending — recent concerts more likely to have setlists
    need_search.sort(key=lambda c: c.get("date", ""), reverse=True)

    # Skip cache: track which artist+date combos we've already tried
    skip_file = os.path.join(data_dir, "setlist_search_skip.json")
    skip_cache = {}
    if os.path.exists(skip_file):
        with open(skip_file) as f:
            skip_cache = json.load(f)

    for c in need_search:
        if api_calls >= BUDGET:
            break
        key = f"{c['artist']}||{c['date']}"
        if key in skip_cache:
            continue

        songs, sid = search_by_artist_date(c["artist"], c["date"])
        api_calls += 1

        idx = concert_map.get(key)
        if idx is None:
            continue

        if songs:
            concerts[idx]["songs"] = songs
            concerts[idx]["song_count"] = len(songs)
            if sid:
                concerts[idx]["id"] = sid
            enriched += 1
            print(f"  ✅ {c['date']} {c['artist']}: {len(songs)} songs")
        else:
            if sid:
                concerts[idx]["id"] = sid
                ids_found += 1
                print(f"  🔑 {c['date']} {c['artist']}: got ID {sid} (no songs yet)")
            else:
                # Mark as searched so we don't retry next run
                skip_cache[key] = True
                print(f"  ⬜ {c['date']} {c['artist']}: not found")

    # Save updated setlist.json
    with open(setlist_file, "w") as f:
        json.dump(concerts, f, indent=2, ensure_ascii=False)

    # Save skip cache
    with open(skip_file, "w") as f:
        json.dump(skip_cache, f)

    total_with_songs = sum(1 for c in concerts if c.get("songs") and len(c["songs"]) > 0)
    print(f"\n=== Results ===")
    print(f"  API calls: {api_calls}/{BUDGET}")
    print(f"  Songs enriched: {enriched}")
    print(f"  IDs found: {ids_found}")
    print(f"  Total with songs: {total_with_songs}/{len(concerts)}")
    print(f"  Skip cache: {len(skip_cache)} entries")


if __name__ == "__main__":
    main()
