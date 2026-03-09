#!/usr/bin/env python3
"""
One-time Trakt OAuth authorization script.
Run locally to get an access token for write operations.

Usage:
  Set TRAKT_CLIENT_ID and TRAKT_CLIENT_SECRET as env vars, then run:
  python scripts/trakt_auth.py

  It will give you a URL and code to enter on trakt.tv.
  After approval, it prints the access token to add as a GitHub secret.
"""

import os, json, time, requests

CLIENT_ID = os.environ.get("TRAKT_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("TRAKT_CLIENT_SECRET", "")

if not CLIENT_ID or not CLIENT_SECRET:
    print("Set TRAKT_CLIENT_ID and TRAKT_CLIENT_SECRET environment variables")
    print("You can find these at https://trakt.tv/oauth/applications")
    exit(1)

BASE = "https://api.trakt.tv"

# Step 1: Request device code
print("Requesting device code from Trakt...")
r = requests.post(f"{BASE}/oauth/device/code", json={"client_id": CLIENT_ID})
if r.status_code != 200:
    print(f"Error: {r.status_code} {r.text}")
    exit(1)

data = r.json()
user_code = data["user_code"]
verify_url = data["verification_url"]
device_code = data["device_code"]
interval = data.get("interval", 5)
expires_in = data.get("expires_in", 600)

print(f"\n{'='*50}")
print(f"Go to: {verify_url}")
print(f"Enter code: {user_code}")
print(f"{'='*50}")
print(f"\nWaiting for authorization (expires in {expires_in}s)...")

# Step 2: Poll for token
start = time.time()
while time.time() - start < expires_in:
    time.sleep(interval)
    r = requests.post(f"{BASE}/oauth/device/token", json={
        "code": device_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    })
    if r.status_code == 200:
        token_data = r.json()
        print(f"\nAuthorized!")
        print(f"\n{'='*50}")
        print(f"Add these as GitHub secrets:")
        print(f"  TRAKT_ACCESS_TOKEN = {token_data['access_token']}")
        print(f"  TRAKT_REFRESH_TOKEN = {token_data['refresh_token']}")
        print(f"{'='*50}")
        print(f"\nToken expires: {token_data.get('created_at', 0) + token_data.get('expires_in', 0)}")
        exit(0)
    elif r.status_code == 400:
        print(".", end="", flush=True)  # pending
    elif r.status_code == 409:
        print("\nAlready approved, fetching token...")
    elif r.status_code == 410:
        print("\nCode expired. Run again.")
        exit(1)
    elif r.status_code == 418:
        print("\nDenied by user.")
        exit(1)
    elif r.status_code == 429:
        time.sleep(interval)

print("\nTimed out. Run again.")
