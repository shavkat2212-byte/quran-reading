import json, sys
sys.path.insert(0, 'tools')
from analyze import words
WBW = "https://audio.qurancdn.com/"
AYAH = "https://everyayah.com/data/Alafasy_128kbps/{s:03d}{a:03d}.mp3"
byloc = {w['loc']: w for w in words}
# preferred surah order when the same word appears in several places
PRIO = [1, 112, 113, 114] + list(range(111, 77, -1))
def best(loc):
    t = byloc[loc]['t']
    occ = [w for w in words if w['t'] == t]
    occ.sort(key=lambda w: (PRIO.index(int(w['loc'].split(':')[0])), [int(x) for x in w['loc'].split(':')]))
    return occ[0]
# Звук слова: файл wbw/SSS_AAA_WWW.mp3 по номеру слова. Поле audio_url в API после знаков
# остановки (ۖ ۚ ۜ ۞) сдвигается на 1–2 и указывает на чужое/несуществующее слово, поэтому строим путь сами.
def wbw(loc):
    s, a, p = map(int, loc.split(':'))
    return WBW + f"wbw/{s:03d}_{a:03d}_{p:03d}.mp3"
def item(loc):
    w = best(loc)
    d = {"type": "word", "ar": w['t'], "loc": w['loc'], "audio": wbw(w['loc'])}
    if w['tr']: d["translit"] = w['tr']
    return d
verses = {}
for n in [1] + list(range(78, 115)):
    for v in json.load(open(f'raw/ch{n}.json'))['verses']:
        verses[v['verse_key']] = v
def ayah(key):
    v = verses[key]; s, a = map(int, key.split(':'))
    ws = [w for w in v['words'] if w['char_type_name'] == 'word']
    return {"type": "ayah", "key": key, "ar": " ".join(w['text_uthmani'] for w in ws),
            "audio": AYAH.format(s=s, a=a),
            "words": [{"ar": w['text_uthmani'], "loc": f"{key}:{w['position']}", "audio": wbw(f"{key}:{w['position']}"),
                       **({"translit": w['transliteration']['text']} if (w.get('transliteration') or {}).get('text') else {})} for w in ws]}

L = [
 ("Короткие слова из 2 букв", "Фатха, касра, дамма",
  "Читайте букву вместе с огласовкой как один слог: не по отдельным буквам, а сразу «ху-ва». Смотрите на слово целиком.",
  ["81:24:2","94:1:3","94:5:2","78:14:2","78:38:11","80:42:2"]),
 ("Слова из 3 букв", "Только короткие гласные",
  "Многие из этих слов — глаголы прошедшего времени (خَلَقَ «создал»). Ритм у них одинаковый: та-та-та. Поймайте ритм — и скорость придёт сама.",
  ["87:2:2","104:2:2","111:2:6","90:3:3","96:12:2","113:5:5","114:2:1"]),
 ("Слова с приставками وَ и فَ", "4–5 букв, короткие гласные",
  "وَ («и») и فَ («и вот / тогда») пишутся слитно со словом. Сначала узнайте приставку глазом, потом читайте остаток слова как знакомое слово.",
  ["80:9:1","87:19:1","92:8:3","113:3:5","82:7:2","87:15:1","88:23:4","79:23:1"]),
 ("Сукун: короткие слова", "Буква без гласной ( ْ )",
  "Буква с сукуном читается без гласной и «закрывает» слог: قُلْ — «куль», одним коротким толчком.",
  ["109:1:1","79:46:4","80:18:1","79:15:1","1:1:1","1:4:2","109:6:1","112:3:2"]),
 ("Сукун: слова подлиннее", "Слоги с сукуном внутри слова",
  "Делите слово на слоги по сукуну: نَعْ-بُدُ, أَنْ-عَمْ-تَ. Через пару повторов глаз начнёт видеть эти слоги сразу.",
  ["1:5:2","1:7:3","1:7:4","109:2:2","94:1:2","94:1:4","97:1:4","99:7:2","104:3:1","114:5:2"]),
 ("Шадда", "Удвоенная буква ( ّ )",
  "Шадда — это та же буква дважды: первая с сукуном, вторая с гласной. إِنَّ = إِنْ + نَ. Задержитесь на удвоенной букве чуть дольше.",
  ["78:17:1","78:5:1","1:2:3","113:2:2","79:19:3","96:4:2","1:2:2","111:1:1","108:2:1","113:1:3"]),
 ("Артикль ال: лунные и солнечные буквы", "Слова с ٱلْ / ٱل",
  "Если после ل стоит сукун (ٱلْحَمْدُ) — ل читается («аль-хамду», лунная буква). Если на следующей букве шадда (ٱلصَّمَدُ) — ل не читается («ас-самаду», солнечная буква). Значок ٱ (васла) произносится как «а» только в начале чтения.",
  ["1:2:1","1:1:2","113:1:4","112:2:2","97:1:5","108:1:3","97:5:5","94:5:3","106:3:4","114:6:2"]),
 ("Танвин и долгие гласные (мадд)", "ـٌ ـٍ ـً и ا و ي",
  "Танвин — двойная огласовка в конце слова, читается «-ун / -ин / -ан» (أَحَدٌ — «ахадун»). Долгие гласные: ا после фатхи, و после даммы, ي после касры, а также маленькая алиф над буквой (مَـٰلِكِ) тянутся на два счёта.",
  ["112:1:4","112:4:4","101:11:1","97:5:1","96:10:1","94:5:4","83:13:5","78:17:4","109:6:4","113:1:2","1:4:1","1:7:1"]),
 ("Длинные слова из Фатихи и коротких сур", "Всё вместе",
  "Эти слова вы, скорее всего, знаете на слух. Сейчас задача — узнать их глазом. Читайте по слогам один раз, затем сразу целиком.",
  ["1:1:3","1:2:4","1:5:1","1:5:4","1:6:3","1:7:6","1:7:9","103:3:5","108:1:2","109:1:3","114:4:3","114:4:4"]),
]
index = []
LEVEL  = [1,1,2,2,3,3,3,4,4,5]
TARGET = [30,30,32,30,35,32,32,36,40,60]  # секунд на весь урок (3-й круг)
for i, (title, sub, tip, locs) in enumerate(L, 1):
    lid = f"{i:03d}"
    items = [item(l) for l in locs]
    assert len({x['ar'] for x in items}) == len(items), (lid, [x['ar'] for x in items])
    les = {"id": lid, "title": title, "subtitle": sub, "level": LEVEL[i-1], "targetSeconds": TARGET[i-1], "tip": tip, "items": items}
    json.dump(les, open(f"lessons/{lid}.json", "w"), ensure_ascii=False, indent=1)
    index.append({"id": lid, "title": title, "subtitle": sub, "level": LEVEL[i-1], "count": len(items), "targetSeconds": TARGET[i-1]})
lid = "010"
les = {"id": lid, "title": "Целые аяты: сура аль-Ихлас и аль-Каусар", "subtitle": "Сначала по словам, потом аят целиком", "level": LEVEL[9], "targetSeconds": TARGET[9],
       "tip": "Прочитайте аят по словам (нажимайте на слово, чтобы сверить), затем весь аят на одном дыхании. Послушайте чтеца (Мишари аль-Афаси) и прочитайте ещё раз.",
       "items": [ayah(k) for k in ["112:1","112:2","112:3","112:4","108:1","108:2","108:3"]]}
json.dump(les, open(f"lessons/{lid}.json", "w"), ensure_ascii=False, indent=1)
index.append({"id": lid, "title": les['title'], "subtitle": les['subtitle'], "level": LEVEL[9], "count": len(les['items']), "targetSeconds": TARGET[9]})

# ---- уроки 11–15 ----
def words_target(items, per_word):
    n = sum(len(it["words"]) if it["type"] == "ayah" else 1 for it in items)
    return int(round(n * per_word / 5.0) * 5)
NEW = [
 ("Длинные слова: 7–9 букв", "Быстрое узнавание длинных слов", 4, 36,
  "Длинное слово собирается из знакомых кусков: приставка (وَ، فَ، بِ، لِ), артикль ٱل, корень и окончание (ـُونَ، ـِينَ، ـَـٰتِ). Найдите глазом эти куски — и слово прочитается сразу.",
  ["101:1:1","102:1:2","107:7:2","99:1:4","99:2:3","100:1:1","101:4:5","95:1:2","78:4:2","85:10:4","98:1:8","83:26:6"]),
 ("Сукун и шадда в одном слове", "ٱلشَّمْسُ، فَسَبِّحْ، ٱلْمُطْمَئِنَّةُ", 4, 32,
  "В этих словах есть и сукун, и шадда. Не останавливайтесь на сукуне и не «проглатывайте» шадду: удвоенная буква — чуть дольше, буква с сукуном — коротко и сразу дальше.",
  ["81:1:2","89:27:3","78:31:2","84:1:3","84:19:1","84:24:1","87:9:1","90:17:7","98:1:12","102:8:2","110:3:1","81:18:1"]),
]
for title, sub, level, target, tip, locs in NEW:
    i = len(index) + 1; lid = f"{i:03d}"
    items = [item(l) for l in locs]
    assert len({x['ar'] for x in items}) == len(items)
    les = {"id": lid, "title": title, "subtitle": sub, "level": level, "targetSeconds": target, "tip": tip, "items": items}
    json.dump(les, open(f"lessons/{lid}.json", "w"), ensure_ascii=False, indent=1)
    index.append({"id": lid, "title": title, "subtitle": sub, "level": level, "count": len(items), "targetSeconds": target})
AY = [
 ("Знаки остановки (вакф)", "Значки ـۖ ـۚ ـۜ внутри аята", 5, 2.0,
  "Маленькие значки над строкой подсказывают, где можно остановиться. ـۖ («сала») — можно остановиться, но лучше продолжить. ـۚ («джим») — можно и остановиться, и продолжить. ـۜ (сакта) — короткая пауза без нового вдоха. Кружок с номером в конце аята — обычное место остановки. Если остановились на слове — последнюю огласовку обычно не произносим.",
  ["89:17","104:4","79:27","83:26","110:3","87:7","83:14","78:39"]),
 ("Сура аль-Аср и сура аль-Фалак", "Целые суры: по словам, потом целиком", 5, 1.9,
  "Прочитайте каждый аят по словам, затем весь аят. В конце прочитайте всю суру подряд, не глядя на подсказки.",
  [f"103:{a}" for a in range(1, 4)] + [f"113:{a}" for a in range(1, 6)]),
 ("Сура ан-Нас и сура аль-Кафирун", "Целые суры в хорошем темпе", 5, 1.7,
  "Цель — ровный темп без остановок внутри слов. Сравните своё время с прошлыми попытками.",
  [f"114:{a}" for a in range(1, 7)] + [f"109:{a}" for a in range(1, 7)]),
]
for title, sub, level, per_word, tip, keys in AY:
    i = len(index) + 1; lid = f"{i:03d}"
    items = [ayah(k) for k in keys]
    target = words_target(items, per_word)
    les = {"id": lid, "title": title, "subtitle": sub, "level": level, "targetSeconds": target, "tip": tip, "items": items}
    json.dump(les, open(f"lessons/{lid}.json", "w"), ensure_ascii=False, indent=1)
    index.append({"id": lid, "title": title, "subtitle": sub, "level": level, "count": len(items), "targetSeconds": target})
letters = json.load(open("lessons/letters/_list.json"))
json.dump({"title": "Самоучитель чтения Корана", "owner": "Шавкат Ташходжаев",
           "sections": [
             {"id": "letters", "title": "Буквы", "dir": "letters", "lessons": letters},
             {"id": "reading", "title": "Чтение: слова и аяты", "dir": "", "lessons": index}]},
          open("lessons/index.json", "w"), ensure_ascii=False, indent=1)
for x in index: print(x['id'], x['count'], x['targetSeconds'], x['title'])

# уроки 016–030
exec(open("tools/build_lessons2.py").read())
