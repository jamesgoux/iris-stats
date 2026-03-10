import json
with open('data/pocketcasts_history.json') as f:
    h = json.load(f)
march10 = [(k,v) for k,v in h.items() if v.get('d')=='2026-03-10']
print(f'Entries on 3/10: {len(march10)}')
for k,v in march10[:10]:
    print(f'  src={v.get("src","")} | {v.get("p","")} - {v.get("t","")[:50]}')
march9 = [(k,v) for k,v in h.items() if v.get('d')=='2026-03-09']
print(f'\nEntries on 3/9: {len(march9)}')
for k,v in march9[:10]:
    print(f'  src={v.get("src","")} | {v.get("p","")} - {v.get("t","")[:50]}')
