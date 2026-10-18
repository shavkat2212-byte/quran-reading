# Уроки 016–030 (продолжение раздела «Чтение»). Запускается после build_lessons.py:
#   python3 tools/build_lessons.py && python3 tools/build_lessons2.py
# Слова и аяты НЕ набираются вручную: всё берётся из raw/ch*.json (api.quran.com v4, письмо усмани).
# Слова для уроков 016–023 отбираются автоматически по правилу урока (танвин, мадд, хамза…),
# самые частые в 30-м джузе, без повторов с уроками 001–015 и между собой.
import json, glob, re, sys, unicodedata, collections
sys.path.insert(0, "tools")
from analyze import words, units

WBW = "https://audio.qurancdn.com/wbw/{:03d}_{:03d}_{:03d}.mp3"
AYAH = "https://everyayah.com/data/Alafasy_128kbps/{:03d}{:03d}.mp3"
PRIO = [1, 112, 113, 114] + list(range(111, 77, -1))
TAN = "\u064b\u064c\u064d\u08f0\u08f1\u08f2"; SH = "\u0651"; MADDAH = "\u0653"; WASLA = "\u0671"
WAQF = re.compile(r"[\u06D6-\u06DC\u06DE\u06E9\s]")

def norm(t):  # для сравнения «то же слово»: без малых знаков 06E2/06ED и т.п.
    return re.sub(r"[\u06E1-\u06ED\u0640]", "", t)
def wbw(loc):
    s, a, p = map(int, loc.split(":")); return WBW.format(s, a, p)
def L(t): return len(units(t))

used = set()
for f in sorted(glob.glob("lessons/0*.json")):
    if f >= "lessons/016": continue
    for it in json.load(open(f))["items"]:
        used |= {norm(it["ar"])} if it["type"] != "ayah" else {norm(w["ar"]) for w in it["words"]}

occ = collections.defaultdict(list)
for w in words:
    if WAQF.search(w["t"]): continue
    occ[norm(w["t"])].append(w)
def first(k):
    o = sorted(occ[k], key=lambda w: (PRIO.index(int(w["loc"].split(":")[0])), [int(x) for x in w["loc"].split(":")]))
    return o[0]

RULES = {
 "tanwin": lambda t: any(c in t for c in TAN) and SH not in t and WASLA not in t and MADDAH not in t,
 "madd":   lambda t: not any(c in t for c in TAN + SH + MADDAH) and WASLA not in t and not any(c in t for c in "ءأإؤئ")
                     and any(x in t for x in ["\u064e\u0627", "\u064f\u0648", "\u0650\u064a", "\u0670"]),
 "maddah": lambda t: MADDAH in t,
 "hamza":  lambda t: MADDAH not in t and (any(c in t for c in "ءؤئإ") or "أ" in t[1:]),
 "tam":    lambda t: "ة" in t,
 "shams":  lambda t: t.startswith(WASLA + "ل") and "".join(u[0] for u in units(t))[:4] != WASLA + "لله" and L(t) > 2 and SH in units(t)[2][1],
 "qamar":  lambda t: t.startswith(WASLA + "ل\u0652"),
 "long":   lambda t: True,
}
taken = set()
def pick(rule, n, lo, hi):
    c = [k for k in occ if RULES[rule](k) and k not in used and k not in taken and lo <= L(k) <= hi]
    c.sort(key=lambda k: (-len(occ[k]), L(k), first(k)["loc"]))
    sel, skel = [], set()
    for k in c:  # одно и то же слово с другой огласовкой в конце не повторяем
        s = "".join(ch for ch in k if not unicodedata.category(ch).startswith("M"))
        if s in skel: continue
        skel.add(s); sel.append(k)
        if len(sel) == n: break
    taken.update(sel)
    sel.sort(key=lambda k: (L(k), -len(occ[k])))
    out = []
    for k in sel:
        w = first(k); d = {"type": "word", "ar": w["t"], "loc": w["loc"], "audio": wbw(w["loc"])}
        if w["tr"]: d["translit"] = w["tr"]
        out.append(d)
    assert len(out) == n, (rule, len(out))
    return out

verses = {}
for f in glob.glob("raw/ch[0-9]*.json"):
    for v in json.load(open(f))["verses"]: verses[v["verse_key"]] = v
def ayah(key):
    v = verses[key]; s, a = map(int, key.split(":"))
    ws = [w for w in v["words"] if w["char_type_name"] == "word"]
    return {"type": "ayah", "key": key, "ar": " ".join(w["text_uthmani"] for w in ws), "audio": AYAH.format(s, a),
            "words": [{"ar": w["text_uthmani"], "loc": f"{key}:{w['position']}", "audio": wbw(f"{key}:{w['position']}"),
                       **({"translit": w["transliteration"]["text"]} if (w.get("transliteration") or {}).get("text") else {})} for w in ws]}
def sura(n, a=None, b=None):
    ks = sorted((k for k in verses if k.startswith(f"{n}:")), key=lambda k: int(k.split(":")[1]))
    return [k for k in ks if (a is None or int(k.split(":")[1]) >= a) and (b is None or int(k.split(":")[1]) <= b)]

# (заголовок, подзаголовок, уровень, цель в секундах, совет; {0},{1} — примеры из самого урока)
W = [
 ("tanwin", 12, 3, 6, "Танвин", "Двойная огласовка: -ун, -ин, -ан", 3, 32,
  "Танвин — двойной значок в конце слова: ـٌ «-ун», ـٍ «-ин», ـً «-ан» (после него часто пишется немая алиф). Пример: {0} и {1}. В конце аята при остановке танвин -ун/-ин не читается, а -ан превращается в долгое «а»."),
 ("madd", 12, 3, 6, "Долгие гласные (мадд табии)", "ا و ي и маленькая алиф", 3, 30,
  "Буква ا после фатхи, و после даммы, ي после касры — это не новые звуки, а удлинение гласной на два счёта. Маленькая алиф над буквой ( ـٰ ) — тоже долгое «а». Пример: {0}, {1}. Тяните ровно, не дольше и не короче."),
 ("maddah", 12, 4, 7, "Длинный мадд ( ـٓ )", "Волнистый значок — тянем 4–5 счётов", 4, 30,
  "Волнистая черта ـٓ над долгой гласной означает, что её тянут дольше обычного — 4–5 счётов. Чаще всего это перед хамзой: {0}, {1}. На время читайте быстро, но мадд не обрезайте."),
 ("hamza", 12, 3, 7, "Хамза: ء أ إ ؤ ئ", "Короткая «запинка» голоса", 4, 28,
  "Хамза — короткий смычок в горле, как пауза в «а-а». Она пишется отдельно (ء) или на подставке: أ إ (алиф), ؤ (вав), ئ (йа без точек). Подставка не читается — читается только хамза со своей огласовкой: {0}, {1}."),
 ("tam", 12, 4, 7, "Та марбута ( ة )", "Окончание -ат / -а", 4, 28,
  "ة (та марбута) — женское окончание. При чтении подряд это «т» со своей огласовкой ({0}), а при остановке читается как лёгкое «х» / «а». Глаз должен узнавать ة сразу — она похожа на ه с двумя точками."),
 ("shams", 12, 4, 7, "Солнечные буквы", "ٱل + шадда: «ль» не читается", 4, 26,
  "Если после ٱل на следующей букве стоит шадда — лям не читается, звук сразу удваивается: {0}, {1}, {2}. Солнечных букв 14: ت ث د ذ ر ز س ش ص ض ط ظ ل ن."),
 ("qamar", 12, 4, 7, "Лунные буквы", "ٱلْ с сукуном: «аль» читается", 4, 25,
  "Если на ل стоит сукун ( ٱلْ ) — лям читается: «аль-». Пример: {0}, {1}. Сравните с прошлым уроком: глаз сразу смотрит на вторую букву — шадда или нет."),
 ("long", 14, 8, 12, "Длинные слова: 8–12 букв", "Всё вместе на скорость", 5, 32,
  "Самые длинные слова 30-го джуза. Ищите знакомые части: приставку, ٱل, корень, окончание ـُونَ / ـِينَ / ـَـٰتِ. Пример: {0}. Сначала по слогам, потом целиком и быстро."),
]
WAQF_TIP = "В конце аята останавливаемся: последнюю огласовку не произносим (ٱلْعَصْرِ → «аль-'аср»), танвин -ан читаем как долгое «а», а ة — как «х»."
A = [
 ("Сура ан-Наср и сура Курайш", "Остановка в конце аята (вакф)", 5, 1.6, sura(110) + sura(106),
  WAQF_TIP + " Прочитайте аят по словам, потом целиком, затем обе суры подряд."),
 ("Сура аль-Филь и сура аль-Ма'ун", "Короткие суры в хорошем темпе", 5, 1.5, sura(105) + sura(107),
  "Следите за танвином и маддом в середине аята, а в конце аята — останавливайтесь, как в прошлом уроке."),
 ("Сура аль-Масад и сура аль-Кадр", "Быстрее: цель строже", 5, 1.45, sura(111) + sura(97),
  "В суре аль-Кадр много раз повторяется слово «ночь» — когда слово уже знакомо, читайте его сразу, не по слогам."),
 ("Сура ат-Такасур и сура аль-Кари'а", "Длинные аяты подряд", 5, 1.4, sura(102) + sura(101),
  "Повторяющиеся слова ( كَلَّا ، سَوْفَ تَعْلَمُونَ ) читайте сразу целиком. Длинный мадд ـٓ не обрезайте даже на скорость."),
 ("Сура аш-Шарх и сура ад-Духа", "Две суры подряд без остановок внутри слов", 5, 1.3, sura(94) + sura(93),
  "Цель — ровное чтение без пауз внутри слов. Если споткнулись, не начинайте аят заново — читайте дальше."),
 ("Сура ат-Тин и сура аз-Зальзаля", "Почти без подсказок", 5, 1.25, sura(95) + sura(99),
  "Попробуйте уже на первом круге читать целые аяты и нажимать на слова только в крайнем случае."),
 ("Сура аль-Мульк, аяты 1–5", "Длинные аяты за пределами 30-го джуза", 5, 1.2, sura(67, 1, 5),
  "Аяты аль-Мульк длиннее, чем в коротких сурах. В аятах 2, 3 и 5 над строкой стоят маленькие знаки остановки (ج — «джим», ص-ل-ي — «сали»): там можно перевести дух. Читайте каждую часть аята на одном дыхании."),
]

idx = json.load(open("lessons/index.json"))
sec = next(s for s in idx["sections"] if s["id"] == "reading")
sec["lessons"] = [l for l in sec["lessons"] if l["id"] < "016"]
assert [l["id"] for l in sec["lessons"]] == [f"{i:03d}" for i in range(1, 16)]
def add(les):
    json.dump(les, open(f"lessons/{les['id']}.json", "w"), ensure_ascii=False, indent=1)
    sec["lessons"].append({k: les[k] for k in ("id", "title", "subtitle", "level", "targetSeconds")} | {"count": len(les["items"])})
for rule, n, lo, hi, title, sub, level, target, tip in W:
    items = pick(rule, n, lo, hi)
    lid = f"{len(sec['lessons']) + 1:03d}"
    add({"id": lid, "title": title, "subtitle": sub, "level": level, "targetSeconds": target,
         "tip": tip.format(*[it["ar"] for it in items]), "items": items})
for title, sub, level, per_word, keys, tip in A:
    items = [ayah(k) for k in keys]
    nw = sum(len(it["words"]) for it in items)
    lid = f"{len(sec['lessons']) + 1:03d}"
    add({"id": lid, "title": title, "subtitle": sub, "level": level, "targetSeconds": int(round(nw * per_word / 5) * 5), "tip": tip, "items": items})
json.dump(idx, open("lessons/index.json", "w"), ensure_ascii=False, indent=1)
for l in sec["lessons"][15:]: print(l["id"], l["count"], l["targetSeconds"], l["title"])
