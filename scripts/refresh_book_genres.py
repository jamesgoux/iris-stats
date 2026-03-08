#!/usr/bin/env python3
"""Scrape community genres from Goodreads book pages — daily backfill."""
import json, os, re, time
import urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if not os.path.exists("data/goodreads.json"):
    print("No goodreads.json found, skipping genre backfill")
    exit(0)

with open("data/goodreads.json") as f:
    books = json.load(f)

# Load existing genres
genres_path = "data/book_genres.json"
existing = {}
if os.path.exists(genres_path):
    with open(genres_path) as f:
        existing = json.load(f)

print(f"=== Book Genre Backfill ===")
print(f"  Books: {len(books)}, Already have genres: {len(existing)}")

# Prioritize books without genres, recent first
to_fetch = [b for b in books if b["book_id"] not in existing]
already = [b for b in books if b["book_id"] in existing]
print(f"  Need genres: {len(to_fetch)}")

BUDGET = 100  # max requests per run
fetched = 0

for b in to_fetch[:BUDGET]:
    book_id = b["book_id"]
    url = f"https://www.goodreads.com/book/show/{book_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Extract genres from genresList section
        m = re.search(r'genresList.*?</div>', html, re.DOTALL)
        if m:
            genres = list(dict.fromkeys(re.findall(r'/genres/([a-z-]+)', m.group())))
        else:
            genres = []

        existing[book_id] = genres
        fetched += 1
        if fetched % 10 == 0:
            print(f"  Fetched {fetched}... ({b['title'][:30]})")
        time.sleep(1)
    except Exception as e:
        print(f"  Error for {book_id} ({b['title'][:30]}): {e}")
        existing[book_id] = []
        time.sleep(2)

with open(genres_path, "w") as f:
    json.dump(existing, f, separators=(",", ":"))

print(f"  Fetched {fetched} new, total {len(existing)} books with genres")
print("Done!")
