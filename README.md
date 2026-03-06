# Trakt Watch Dashboard

Auto-refreshing personal Trakt.tv watch history dashboard.

- **Data refreshes every 20 minutes** via GitHub Actions
- **Actor headshots refresh daily** (incremental — only fetches new people)
- **View on any device** at `https://YOUR_USERNAME.github.io/trakt-dashboard/`

## Setup

1. **Create this repo on GitHub** (public)

2. **Add secrets** in Settings → Secrets → Actions:
   - `TRAKT_CLIENT_ID` — your Trakt API client ID
   - `TRAKT_USERNAME` — your Trakt username

3. **Enable GitHub Pages** in Settings → Pages:
   - Source: "Deploy from a branch"
   - Branch: `main`, folder: `/ (root)`

4. **Run the first refresh** manually:
   - Go to Actions → "Refresh Trakt Data" → "Run workflow"
   - Then Actions → "Refresh Headshots" → "Run workflow"

5. **Bookmark** `https://YOUR_USERNAME.github.io/trakt-dashboard/` on your phone

## Files

```
index.html                    ← The dashboard (auto-generated, don't edit)
templates/dashboard.html      ← HTML template
scripts/refresh_data.py       ← Pulls Trakt data + rebuilds index.html
scripts/refresh_headshots.py  ← Fetches actor photos from TMDB
data/headshots.json           ← Cached headshot URLs (grows over time)
data/people.json              ← Cast data (rebuilt each refresh)
.github/workflows/            ← Scheduled refresh jobs
```
