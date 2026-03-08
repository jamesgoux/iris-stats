#!/usr/bin/env python3
"""Fetch artist genres from MusicBrainz — free, no API key."""
import json, os, time, urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if not os.path.exists("data/setlist.json"):
    print("No setlist.json found, skipping artist genre backfill")
    exit(0)

with open("data/setlist.json") as f:
    concerts = json.load(f)

artists = list(set(c["artist"] for c in concerts))

genres_path = "data/artist_genres.json"
existing = {}
if os.path.exists(genres_path):
    with open(genres_path) as f:
        existing = json.load(f)

print(f"=== Artist Genre Backfill ===")
print(f"  Artists: {len(artists)}, Already have: {len(existing)}")

SKIP_TAGS = {"american", "united states", "usa", "uk", "british", "english", "canadian"}
fetched = 0

for artist in artists:
    if artist in existing:
        continue
    try:
        q = urllib.parse.quote(artist)
        url = f"https://musicbrainz.org/ws/2/artist/?query=artist:{q}&fmt=json&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Iris/1.0 (jamesgoux@github)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        tags = []
        if data.get("artists"):
            a = data["artists"][0]
            tags = [t["name"] for t in a.get("tags", [])
                    if t.get("count", 0) >= 1 and t["name"].lower() not in SKIP_TAGS]

        existing[artist] = tags[:8]
        fetched += 1
        print(f"  {artist}: {', '.join(tags[:5]) if tags else '(none)'}")
        time.sleep(1.1)  # MusicBrainz rate limit: 1 req/sec
    except Exception as e:
        print(f"  Error for {artist}: {e}")
        existing[artist] = []
        time.sleep(2)

with open(genres_path, "w") as f:
    json.dump(existing, f, separators=(",", ":"), indent=None)

print(f"  Fetched {fetched} new, total {len(existing)} artists")
print("Done!")
