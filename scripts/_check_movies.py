import re, json
with open('index.html','r',encoding='utf-8') as f:
    html = f.read()
m = re.search(r'var D=(.+?);\nvar HS=', html, re.DOTALL)
d = json.loads(m.group(1))
tl = d.get('tl',[])
movies = [t for t in tl if t['type']=='movie']
print(f'Movies in title list: {len(movies)}')
s = d.get('c',{}).get('s',{})
print(f'Stats unique_movies: {s.get("unique_movies",0)}')
print(f'Stats movie_watches: {s.get("movie_watches",0)}')

# Check how many undated entries made it
undated = [t for t in tl if t['type']=='movie' and not t.get('eby')]
print(f'Undated movies in TL: {len(undated)}')

# Check letterboxd data
with open('data/letterboxd.json') as f:
    lb = json.load(f)
total_lb = len(lb)
undated_lb = sum(1 for v in lb.values() if v.get('undated'))
print(f'Letterboxd total: {total_lb}, undated: {undated_lb}')
