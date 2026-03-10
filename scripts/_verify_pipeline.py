import os
code = open('scripts/refresh_data.py', encoding='utf-8').read()
lfm = open('scripts/refresh_lastfm.py', encoding='utf-8').read()
pc = open('scripts/refresh_pocketcasts.py', encoding='utf-8').read()

checks = [
    ('2016 dw exclusion', 'y != "2016"' in code),
    ('Pacific timezone lifeline', '_tz_pac' in code),
    ('Podcast 5min filter (data)', 'played < 300' in code),
    ('Podcast 5min filter (poll)', 'min(played, dur) >= 300' in pc),
    ('Podcast export+poll in lifeline', '"poll", "export"' in code),
    ('Undated LB entries added', '"undated": True' in code or 'undated' in code),
    ('Vintage title|year dedup', 'vid = e' in code),
    ('Podcast aliases (data)', 'PODCAST_ALIASES' in code),
    ('Podcast aliases (pocketcasts)', 'PODCAST_ALIASES' in pc),
    ('Per-year top podcasts', 'pc_by_year' in code),
    ('DW per-year data', 'dw_y' in code),
    ('Slug resolution', 'lb_slug_cache' in code),
    ('Season-level TTW', 'season_eps' in code),
    ('TTW <1d filter', 'avg_delay < 1.0' in code),
    ('TTW 4+ eps', 'len(delays) < 4' in code),
    ('LFM no double-count', 'new_periods_y' in lfm),
    ('LFM 30 tracks', 'limit=30' in lfm),
    ('LB backfill no flag gate', '.lb_backfill_done' not in code),
    ('Podcast pc_poll data', 'pc_poll_monthly' in code),
    ('Episodes type fix (mt)', 'etype' in code),
]
all_ok = True
for name, ok in checks:
    status = '✅' if ok else '❌'
    if not ok: all_ok = False
    print(f'{status} {name}')

print(f'\n{"All checks passed!" if all_ok else "SOME CHECKS FAILED"}')
