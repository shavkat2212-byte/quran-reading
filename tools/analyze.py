import json,unicodedata,collections
SHORT={'\u064e','\u064f','\u0650'}; SUK='\u0652'; SH='\u0651'; TAN={'\u064b','\u064c','\u064d','\u08f0','\u08f1','\u08f2'}
words=[]
for n in [1]+list(range(78,115)):
  for v in json.load(open(f'raw/ch{n}.json'))['verses']:
    for w in v['words']:
      if w['char_type_name']!='word': continue
      words.append(dict(loc=f"{v['verse_key']}:{w['position']}",t=w['text_uthmani'],tr=(w.get('transliteration') or {}).get('text'),en=(w.get('translation') or {}).get('text'),audio=w['audio_url']))
def units(t):
  # split into (letter, marks)
  u=[]
  for c in t:
    if unicodedata.category(c)=='Lo' and c!='\u0640': u.append([c,''])
    elif c=='\u0640': continue
    else:
      if u: u[-1][1]+=c
      else: u.append(['',c])
  return u
def cat(t):
  u=units(t); ms=[m for _,m in u]; letters=len(u)
  allm=set(''.join(ms))
  if all(m in SHORT for m in ms): return 'short',letters
  if all(m in SHORT or m==SUK for m in ms) and SUK in allm: return 'sukun',letters
  if '\u0671' not in t and all(m in SHORT or m==SUK or (len(m)==2 and m[0]==SH and m[1] in SHORT) for m in ms) and SH in allm: return 'shadda',letters
  return 'other',letters
if __name__=='__main__':
  c=collections.defaultdict(list)
  seen={}
  for w in words:
    k,l=cat(w['t']); 
    if w['t'] in seen: seen[w['t']]['n']+=1; continue
    w['n']=1; w['k']=k; w['l']=l; seen[w['t']]=w
  for k in ['short','sukun','shadda']:
    print('==',k)
    for w in sorted([w for w in seen.values() if w['k']==k], key=lambda w:(w['l'],-w['n'])):
      print(w['l'],w['n'],w['loc'],w['t'],w['tr'],'|',w['en'])
