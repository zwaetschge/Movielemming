#!/usr/bin/env python3
import csv,gzip,json,math,urllib.request
from collections import defaultdict
from pathlib import Path
from datetime import datetime,timezone
BASE='https://datasets.imdbws.com/'
FILES=['title.ratings.tsv.gz','title.basics.tsv.gz','title.crew.tsv.gz','title.principals.tsv.gz','name.basics.tsv.gz']
ROOT=Path(__file__).resolve().parents[1]; CACHE=ROOT/'.cache/imdb'; OUT=ROOT/'public/data/movies.json'
CACHE.mkdir(parents=True,exist_ok=True); OUT.parent.mkdir(parents=True,exist_ok=True)
for fn in FILES:
 p=CACHE/fn
 if not p.exists(): print('downloading',fn,flush=True); urllib.request.urlretrieve(BASE+fn,p)
def rows(fn):
 with gzip.open(CACHE/fn,'rt',encoding='utf-8',newline='') as f: yield from csv.DictReader(f,delimiter='\t',quoting=csv.QUOTE_NONE)
ratings={r['tconst']:(float(r['averageRating']),int(r['numVotes'])) for r in rows('title.ratings.tsv.gz')}
candidates=[]
for r in rows('title.basics.tsv.gz'):
 if r['titleType']!='movie' or r['isAdult']!='0' or r['startYear']=='\\N': continue
 y=int(r['startYear']); rv=ratings.get(r['tconst'])
 if not 1970<=y<=2026 or not rv or rv[1]<15000: continue
 runtime=None if r['runtimeMinutes']=='\\N' else int(r['runtimeMinutes'])
 if runtime is not None and runtime<55: continue
 rating,votes=rv
 candidates.append({'id':r['tconst'],'title':r['primaryTitle'],'originalTitle':r['originalTitle'],'year':y,'runtime':runtime,'genres':[] if r['genres']=='\\N' else r['genres'].split(','),'rating':rating,'votes':votes,'score':math.log10(votes)*rating})
by_year=defaultdict(list)
for m in candidates: by_year[m['year']].append(m)
selected=[]; seen=set()
for year in sorted(by_year):
 for m in sorted(by_year[year],key=lambda x:(x['score'],x['votes']),reverse=True)[:5]: selected.append(m); seen.add(m['id'])
for m in sorted(candidates,key=lambda x:(x['score'],x['votes']),reverse=True):
 if len(selected)>=380: break
 if m['id'] not in seen: selected.append(m); seen.add(m['id'])
selected=sorted(selected,key=lambda x:(x['year'],-x['score'])); ids={m['id'] for m in selected}; movie_map={m['id']:m for m in selected}
for r in rows('title.crew.tsv.gz'):
 if r['tconst'] in ids: movie_map[r['tconst']]['directorIds']=[] if r['directors']=='\\N' else r['directors'].split(',')[:2]
casts=defaultdict(list)
for r in rows('title.principals.tsv.gz'):
 tid=r['tconst']
 if tid in ids and r['category'] in ('actor','actress') and len(casts[tid])<5: casts[tid].append({'id':r['nconst'],'order':int(r['ordering']),'characters':[] if r['characters']=='\\N' else json.loads(r['characters'])})
for tid,m in movie_map.items(): m['cast']=sorted(casts.get(tid,[]),key=lambda x:x['order'])[:5]
person_ids={x for m in selected for x in m.get('directorIds',[])}|{c['id'] for m in selected for c in m['cast']}
people={}
for r in rows('name.basics.tsv.gz'):
 if r['nconst'] in person_ids: people[r['nconst']]={'id':r['nconst'],'name':r['primaryName'],'birth':None if r['birthYear']=='\\N' else int(r['birthYear']),'death':None if r['deathYear']=='\\N' else int(r['deathYear']),'professions':[] if r['primaryProfession']=='\\N' else r['primaryProfession'].split(',')}
actor_ids={c['id'] for m in selected for c in m['cast']}; director_ids={d for m in selected for d in m.get('directorIds',[])}
for pid,p in people.items(): p['roles']=(['actor'] if pid in actor_ids else [])+(['director'] if pid in director_ids else [])
movies=[]
for m in selected:
 directors=[people[d] for d in m.get('directorIds',[]) if d in people]; cast=[{'id':c['id'],'name':people[c['id']]['name'],'characters':c['characters']} for c in m['cast'] if c['id'] in people]
 if not directors or len(cast)<2: continue
 movies.append({k:m[k] for k in ['id','title','originalTitle','year','runtime','genres','rating','votes']}|{'directors':[{'id':d['id'],'name':d['name']} for d in directors],'cast':cast})
used={d['id'] for m in movies for d in m['directors']}|{c['id'] for m in movies for c in m['cast']}
payload={'meta':{'source':'IMDb Non-Commercial Datasets','sourceUrl':'https://developer.imdb.com/non-commercial-datasets/','generated':datetime.now(timezone.utc).isoformat(),'licenseNote':'For personal and non-commercial use. Verify IMDb terms before redistribution or commercial use.','movieCount':len(movies),'personCount':len(used)},'movies':movies,'people':[people[x] for x in sorted(used)]}
OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(f'wrote {len(movies)} movies and {len(used)} people')
if len(movies)<300: raise SystemExit('dataset too small')
