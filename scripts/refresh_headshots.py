#!/usr/bin/env python3
"""
Incrementally fetch headshot images for people in data/people.json.
Only fetches people not already in data/headshots.json.
Saves progress every 200 people so partial runs aren't lost.
"""

import os, json, time, re, requests

CLIENT_ID = os.environ.get("TRAKT_CLIENT_ID")
BASE_URL = "https://api.trakt.tv"
HEADERS = {"Content-Type": "application/json", "trakt-api-version": "2", "trakt-api-key": CLIENT_ID}
MAX_PER_RUN = 800  # Cap per run to stay within GitHub Actions timeout

if not CLIENT_ID:
    print("ERROR: Set TRAKT_CLIENT_ID"); exit(1)

# Load existing
hs = {}
if os.path.exists("data/headshots.json"):
    with open("data/headshots.json") as f:
        hs = json.load(f)

if not os.path.exists("data/people.json"):
    print("No data/people.json found. Run refresh_data.py first."); exit(0)

with open("data/people.json") as f:
    people = json.load(f)

# Find who needs headshots
need = [slug for slug, info in people.items() if info["name"] not in hs]
need = need[:MAX_PER_RUN]

print(f"=== Headshot Refresh ===")
print(f"  Cached: {len(hs)}, Need: {len(need)} (capped at {MAX_PER_RUN})")

if not need:
    print("  All headshots up to date!"); exit(0)

count = 0
for i, slug in enumerate(need):
    name = people[slug]["name"]
    try:
        r1 = requests.get(f"{BASE_URL}/people/{slug}?extended=full", headers=HEADERS, timeout=5)
        if r1.status_code == 200:
            tmdb_id = r1.json().get("ids", {}).get("tmdb")
            if tmdb_id:
                r2 = requests.get(f"https://www.themoviedb.org/person/{tmdb_id}",
                                 timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                if r2.status_code == 200:
                    imgs = re.findall(r'https://image\.tmdb\.org/t/p/w500/([^"\']+\.jpg)', r2.text)
                    if imgs:
                        hs[name] = f"https://image.tmdb.org/t/p/w185/{imgs[0]}"
                        count += 1
    except:
        pass

    if (i + 1) % 200 == 0:
        print(f"  {i+1}/{len(need)} processed, {count} found")
        with open("data/headshots.json", "w") as f:
            json.dump(hs, f, separators=(',', ':'))

    time.sleep(0.1)

with open("data/headshots.json", "w") as f:
    json.dump(hs, f, separators=(',', ':'))

print(f"  Done! +{count} new headshots, {len(hs)} total")
