import json
with open('data/pocketcasts_history.json') as f:
    h = json.load(f)
to_remove = []
for k, v in h.items():
    if v.get('d') == '2026-03-10' and v.get('src') == 'poll':
        played = v.get('played', 0)
        print(f"  {v.get('p','')} played={played}s {'REMOVE' if played < 300 else 'KEEP'}")
        if played < 300:
            to_remove.append(k)
for k in to_remove:
    del h[k]
with open('data/pocketcasts_history.json', 'w') as f:
    json.dump(h, f, separators=(',',':'))
print(f'Removed {len(to_remove)} entries')
