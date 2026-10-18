#!/usr/bin/env python3
"""Собирает dua/duas.json (раздел «🤲 Дуа»), adhkar/evening.json и adhkar/salah.json.

Арабский текст НЕ набирается вручную — только берётся из наборов данных и сверяется:
  * дуа из «Крепости мусульманина» — основной текст github.com/asellam/HisnElMuslim (hisn.json);
    второй источник — официальный API книги www.hisnmuslim.com/api/ar/*.json (+ github.com/rn0x/Adhkar-json,
    github.com/rn0x/hisn_almuslim_json, github.com/Seen-Arabic/Morning-And-Evening-Adhkar-DB).
    Буквы показываемого текста ОБЯЗАНЫ найтись во втором источнике, иначе сборка падает (assert).
    Огласовки сравниваются по словам; явные опечатки исправлены в FIX (каждая правка тоже проверяется).
  * кораническое дуа — api.quran.com v4 (усмани, перевод Э. Кулиева id 45), сверено по буквам с api.alquran.cloud (quran-uthmani).
Звук: www.hisnmuslim.com/audio/ar/<№>.mp3 (номер зикра в книге) и everyayah.com (Мишари Алафаси) для аятов.
Транскрипция и перевод дуа — tools/duas_spec.py.
Запуск: python3 tools/build_duas.py  (кеш исходников — raw/duasrc, raw/dua; raw/ не публикуется)
"""
import json, os, re, sys, difflib, unicodedata, urllib.request, ast
sys.path.insert(0, os.path.dirname(__file__))
from duas_spec import QURAN, CATS, SALAH

C = "raw/duasrc"
SRC = {"hisn.json": "https://raw.githubusercontent.com/asellam/HisnElMuslim/main/hisn.json",
       "adhkar.json": "https://raw.githubusercontent.com/rn0x/Adhkar-json/main/adhkar.json",
       "hisn_almuslim.json": "https://raw.githubusercontent.com/rn0x/hisn_almuslim_json/main/hisn_almuslim.json",
       "ar.json": "https://raw.githubusercontent.com/Seen-Arabic/Morning-And-Evening-Adhkar-DB/main/ar.json"}
UA = {"User-Agent": "Mozilla/5.0"}

def fetch(url, path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "wb").write(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
    return json.loads(open(path, encoding="utf-8-sig").read())

def N(t): return unicodedata.normalize("NFC", t)

def rel(t):  # только буквы, без огласовок и вариантов написания хамзы/алифа
    t = t.replace("ﷺ", "صلى الله عليه وسلم")
    t = "".join(c for c in t if not unicodedata.category(c).startswith("M")).replace("ٱ", "ا").replace("ـ", "")
    t = re.sub(r"[أإآ]", "ا", t).replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي").replace("ء", "")
    return re.sub(r"[^\u0621-\u064A]", "", t).replace("سماوات", "سموات")  # السماوات/السموات — два написания

hisn = fetch(SRC["hisn.json"], f"{C}/hisn.json"); HK = list(hisn)
def AS(i, j): return hisn[HK[i]]["Adhkar"][j]
HM = {}
idx = fetch("https://www.hisnmuslim.com/api/ar/husn_ar.json", f"{C}/hm/index.json")["العربية"]
for c in idx:
    for v in fetch(f"https://www.hisnmuslim.com/api/ar/{c['ID']}.json", f"{C}/hm/{c['ID']}.json").values():
        for x in v: HM[x["ID"]] = x
POOL = [("hisnmuslim.com №%d" % k, x["ARABIC_TEXT"]) for k, x in HM.items()]
for c in fetch(SRC["adhkar.json"], f"{C}/adhkar.json"):
    POOL += [("rn0x/Adhkar-json", x["text"]) for x in c["array"]]
for v in fetch(SRC["hisn_almuslim.json"], f"{C}/hisn_almuslim.json").values():
    POOL += [("rn0x/hisn_almuslim_json", t) for t in v["text"]]
SEEN = fetch(SRC["ar.json"], f"{C}/ar.json")
POOL += [("Seen-Arabic", x["content"]) for x in SEEN]
POOLR = [(n, rel(t), t) for n, t in POOL]

# явные опечатки огласовок в hisn.json (сверено с hisnmuslim.com / sunnah.com)
FIX = {(0, 0): [("النُّشُّورُ", "النُّشُورُ")], (10, 0): [("اللًّهِ", "اللَّهِ")], (14, 3): [("وَأبْعَثْهُ", "وَابْعَثْهُ")],
       (104, 0): [("التَّامَاتِ", "التَّامَّاتِ")], (35, 1): [("لَاإِلَهَ", "لَا إِلَهَ")],
       (27, 3): [("وَشَرَّ مَا بَعْدَهَا", "وَشَرِّ مَا بَعْدَهَا"), ("رَبَّ أَعُوذُ", "رَبِّ أَعُوذُ")]}
GFIX = [("الذِي", "الَّذِي"), ("التِي", "الَّتِي")]
EXTRA = {(29, 0): [("لَا إِلَهِ", "لَا إِلَهَ")], (28, 10): [("وَرَبَّ كُلَّ", "وَرَبَّ كُلِّ")],
         (95, 0): [("فَاِغْفِرْ", "فَاغْفِرْ")], (46, 0): [("اللَّهِ. وَمَا", "اللَّهِ، وَمَا"), ("فَعَلْ", "فَعَلَ")],
         (3, 0): [("إِلْبَسْ", "الْبَسْ")], (9, 0): [("أو أُزَلَّ", "أَوْ أُزَلَّ"), ("أَظْلِم ", "أَظْلِمَ ")],
         (24, 7): [("وعَمَلًا", "وَعَمَلًا")], (11, 0): [("نُورا،", "نُورًا،")], (7, 0): [("اللَّه", "اللَّهِ")],
         (5, 0): [("[بِسْمِ اللَّه]", "[بِسْمِ اللَّهِ]")], (1, 0): [("( الثَّوْبَ )", "(الثَّوْبَ)"), ("وَرَزَقَنِيه ", "وَرَزَقَنِيهِ ")]}  # найдено сравнением огласовок со вторым источником

def marks(word):
    """слово -> [(буква, огласовки)], огласовки на алифе относим к предыдущей букве, сукун не учитываем"""
    out = []
    for ch in unicodedata.normalize("NFC", word):
        if unicodedata.category(ch).startswith("M"):
            if ch in "\u0652\u06e1" or not out: continue
            out[-1][1].add(ch)
        elif rel(ch):
            b = rel(ch)
            out.append([b if ch not in "اٰ" else "", set()])
    for b in out:  # хамза под/над алифом подразумевает кясру/фатху
        b[1] = frozenset(b[1])
    return [(b, m) for b, m in out]

VOW = set("\u064b\u064c\u064d\u064e\u064f\u0650")
def differ(p, q):
    if not p[0] or not q[0]: return False  # огласовки на алифе (рабба̄н/раббан) не сравниваем
    f = lambda m: {"\u064e" if c == "\u064b" else c for c in m & VOW}  # «раббан»: танвин на букве или на алифе
    vx, vy = f(p[1]), f(q[1])
    return bool(vx and vy and (vx != vy or (("\u0651" in p[1]) != ("\u0651" in q[1]))))

def dia_report(tag, shown, other):
    a, b = shown.split(), re.sub(r"[()\[\]{}*«»]", " ", other).split()
    ra, rb = [rel(x) for x in a], [rel(x) for x in b]
    sm = difflib.SequenceMatcher(None, ra, rb, autojunk=False)
    bad = []
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            x, y = a[blk.a + k], b[blk.b + k]
            if not rel(x): continue
            mx, my = marks(x), marks(y)
            if len(mx) == len(my) and any(differ(p, q) for p, q in zip(mx, my)):
                bad.append(f"{x} ≠ {y}")
    if bad: print(f"  ! огласовки {tag}: " + "; ".join(bad))
    return bad

def clean(t, notes=False, rm=()):
    t = t.replace("\r", "")
    for s in rm: assert s in t, s; t = t.replace(s, "")
    t = t.replace("{", "﴿").replace("}", "﴾").replace("*", "")
    if notes: t = re.sub(r"[()\[\]]", "", t)
    return re.sub(r"[ \t]+", " ", t).strip(" ،:.\n")

def take(i, j, w=None, notes=False, rm=(), paren=False, primary=None):
    if primary == "hm":
        t = N(HM[primary_id]["ARABIC_TEXT"]); notes = True
    else:
        t = AS(i, j)["Text"]
        t = N(t)
        for a, b in FIX.get((i, j), []) + EXTRA.get((i, j), []):
            a, b = N(a), N(b); assert a in t, ((i, j), a); t = t.replace(a, b)
        for a, b in GFIX: t = t.replace(N(a), N(b))
    if paren: t = t[t.index("(") + 1:t.rindex(")")]
    if w: t = " ".join(t.replace("\r\n", " ").split()[w[0]:w[1]])
    return clean(t, notes or bool(w), rm)

def verify(tag, ar, hm=None):
    r = rel(ar)
    assert len(r) >= 4 or hm, tag
    if hm:
        assert r in rel(HM[hm]["ARABIC_TEXT"]), f"{tag}: нет совпадения с hisnmuslim.com №{hm}"
        return "hisnmuslim.com №%d" % hm, HM[hm]["ARABIC_TEXT"]
    m = [(n, t) for n, rr, t in POOLR if r in rr]
    if m: return max(m, key=lambda x: sum(unicodedata.category(c).startswith("M") for c in x[1]) / (len(x[1]) or 1))
    raise AssertionError(f"{tag}: текст не найден во втором источнике")

AUDIO = "https://www.hisnmuslim.com/audio/ar/{}.mp3"
EA = "https://everyayah.com/data/Alafasy_128kbps/{:03d}{:03d}.mp3"
conflicts = []

def hisn_item(it):
    global primary_id
    rec = {k: it[k] for k in ("id", "title", "translit", "ru", "when", "src", "grade") if k in it}
    hm = it.get("hm"); primary_id = hm
    specs = it.get("parts") or [(it["h"][0], it["h"][1], it.get("w"), "", it.get("count", 0))]
    parts = []
    for (i, j, w, label, cnt) in specs:
        ar = take(i, j, w, it.get("notes"), it.get("rm", ()), it.get("paren"), it.get("primary"))
        who, other = verify(it["id"], ar, hm)
        conflicts.extend(dia_report(f"{it['id']} ({who})", ar, other))
        parts.append({"ar": ar, **({"label": label} if label else {}), **({"count": cnt} if cnt and len(specs) > 1 else {})})
    if len(parts) == 1: rec["ar"] = parts[0]["ar"]
    else: rec["parts"] = parts
    rec["check"] = who
    if hm: rec["audio"] = [AUDIO.format(hm)]
    return rec

def quran_item(q):
    qid, keys, start, title, translit, when = q
    ayat, ru = [], []
    for n, k in enumerate(keys):
        d = json.load(open(f"raw/dua/{k.replace(':', '_')}.json"))
        v, ac = d["qc"].get("verse", d["qc"]), d["ac"]["data"]["text"]
        words = [w["text_uthmani"] for w in v["words"] if w["char_type_name"] == "word"]
        full = " ".join(words)
        assert rel(full) == rel(ac).replace("بسماللهالرحمنالرحيم", "", 1) or rel(full) == rel(ac), f"{k}: quran.com ≠ alquran.cloud"
        ar = " ".join(words[start:] if n == 0 else words)
        ayat.append({"k": k, "ar": ar, **({"part": True} if n == 0 and start else {})})
        ru.append(re.sub(r"<[^>]+>", "", v["translations"][0]["text"]).strip())
    s0, a0 = map(int, keys[0].split(":")); s1, a1 = map(int, keys[-1].split(":"))
    return {"id": qid, "title": title, "ayat": ayat, "translit": translit, "ru": " ".join(ru),
            "ruSrc": "перевод аята целиком — Э. Кулиев", "when": when,
            "src": f"Коран, {s0}:{a0}" + (f"–{a1}" if keys[-1] != keys[0] else ""), "check": "api.quran.com = api.alquran.cloud",
            "audio": [EA.format(*map(int, k.split(":"))) for k in keys]}

cats = [{"id": "quran", "icon": "📖", "title": "Из Корана: «Раббана…»", "items": [quran_item(q) for q in QURAN]}]
for cid, icon, title, items in CATS:
    cats.append({"id": cid, "icon": icon, "title": title, "items": [hisn_item(it) for it in items]})
ids = [x["id"] for c in cats for x in c["items"]]
assert len(ids) == len(set(ids)), "повтор id"
os.makedirs("dua", exist_ok=True)
json.dump({"title": "Дуа", "cats": cats}, open("dua/duas.json", "w"), ensure_ascii=False, indent=1)
for c in cats: print(f"{c['icon']} {c['title']}: {len(c['items'])}")
print("всего дуа:", len(ids))

# ---------- счётчики: вечер и после намаза ----------
morning = {x["id"]: x for x in json.load(open("adhkar/morning.json"))["items"]}
def seen_check(tag, ar):
    r = rel(ar)
    m = [x for x in SEEN if rel(x["content"]) == r]
    assert m, f"{tag}: нет точного совпадения в Seen-Arabic"
    conflicts.extend(dia_report(f"{tag} (Seen-Arabic)", ar, m[0]["content"]))
    return m[0]

EV = {3: ("asbahna", dict(title="Амсайна ва амса-ль-мульку ли-Ллях",
         translit="Амсайна ва амса-ль-мульку ли-Лляхи ва-ль-хамду ли-Лляхи, ля иляха илля-Ллаху вахдаху ля шарикя лях, ляху-ль-мульку ва ляху-ль-хамду ва хуа 'аля кулли шай'ин кадир. Рабби, ас'алюкя хайра ма фи хазихи-ль-лейляти ва хайра ма ба'даха, ва а'узу бикя мин шарри ма фи хазихи-ль-лейляти ва шарри ма ба'даха. Рабби, а'узу бикя мина-ль-кясали ва су'и-ль-кибар. Рабби, а'узу бикя мин 'азабин фи-н-нари ва 'азабин фи-ль-кабр.",
         ru="Мы дожили до вечера, и этим вечером владычество принадлежит Аллаху, и хвала Аллаху. Нет божества, кроме одного лишь Аллаха, у которого нет сотоварища. Ему принадлежит владычество, Ему хвала, Он всё может. Господь мой, прошу Тебя о благе того, что будет этой ночью, и благе того, что за ней последует, и прибегаю к Тебе от зла того, что будет этой ночью, и зла того, что за ней последует. Господь мой, прибегаю к Тебе от лени и старческой дряхлости. Господь мой, прибегаю к Тебе от мучений в огне и мучений в могиле!", noaudio=1)),
      4: ("bika", dict(title="Аллахумма бика амсайна",
         translit="Аллахумма бика амсайна, ва бика асбахна, ва бика нахйа, ва бика намуту ва иляйка-ль-масыр.",
         ru="О Аллах, благодаря Тебе мы дожили до вечера и благодаря Тебе мы дожили до утра, Ты даёшь нам жизнь, и Ты лишаешь нас её, и к Тебе — возвращение.",
         virtue="Пророк ﷺ велел говорить это, когда наступает вечер.", src="ат-Тирмизи 3391, Абу Дауд 5068", noaudio=1)),
      5: ("sayyid", dict(virtue="Кто скажет это ночью, твёрдо веря, и умрёт до утра — попадёт в Рай.")),
      6: ("ushhiduka", dict(title="Аллахумма инни амсайту ушхидука",
         translit="Аллахумма, инни амсайту ушхидукя ва ушхиду хамаляты 'аршикя, ва маля'икятакя ва джами'а халькикя, аннякя Анта-Ллаху ля иляха илля Анта вахдакя ля шарикя лякя, ва анна Мухаммадан 'абдукя ва расулюк.",
         ru="О Аллах, поистине, этим вечером я призываю Тебя, и тех, кто несёт Твой Трон, и Твоих ангелов, и всех, кого Ты создал, засвидетельствовать, что Ты — Аллах, нет божества, кроме одного лишь Тебя, у Тебя нет сотоварища, и что Мухаммад — Твой раб и Твой посланник.", noaudio=1)),
      7: ("ni3ma", dict(title="Аллахумма ма амса бий мин ни'матин",
         translit="Аллахумма, ма амса би мин ни'матин ау би-ахадин мин халькикя фа-минкя вахдакя ля шарикя лякя, фа-лякя-ль-хамду ва лякя-ш-шукр.",
         ru="О Аллах, всякая милость, оказанная этим вечером мне или кому-либо из Твоих созданий, — только от Тебя одного, нет у Тебя сотоварища! Тебе хвала и Тебе благодарность!",
         virtue="Кто скажет это вечером — выполнил долг благодарности за эту ночь.", noaudio=1)),
      8: ("afini", {}), 9: ("hasbiya", {}), 10: ("afw", {}), 11: ("alim", {}),
      12: ("bismi", dict(virtue="Кто скажет это трижды вечером, того не постигнет внезапная беда до утра.")),
      13: ("radiytu", {}), 14: ("hayy", {}),
      15: ("asbahna2", dict(title="Амсайна ва амса-ль-мульку ли-Лляхи Рабби-ль-'алямин",
         translit="Амсайна ва амса-ль-мульку ли-Лляхи Рабби-ль-'алямин. Аллахумма, инни ас'алюкя хайра хазихи-ль-лейля: фатхаха ва насраха ва нураха ва баракятаха ва худаха, ва а'узу бикя мин шарри ма фиха ва шарри ма ба'даха.",
         ru="Мы дожили до вечера, и этим вечером владычество принадлежит Аллаху, Господу миров. О Аллах, я прошу Тебя о благе этой ночи: о её открытиях и помощи, о её свете, благословении и верном руководстве, и прибегаю к Тебе от зла того, что в ней, и зла того, что после неё.",
         virtue="Сказав утром «асбахна…», вечером говорят «амсайна…».", noaudio=1)),
      16: ("fitra", dict(title="Амсайна 'аля фитрати-ль-ислам",
         translit="Амсайна 'аля фитрати-ль-ислами, ва 'аля кялимати-ль-ихляс, ва 'аля дини набиййина Мухаммадин, салля-Ллаху 'аляйхи ва салляма, ва 'аля мил-ляти абина Ибрахима ханифан муслиман ва ма кяна мина-ль-мушрикин.",
         ru="Мы встретили вечер в лоне ислама, со словом искренности, исповедуя религию нашего пророка Мухаммада ﷺ и религию нашего отца Ибрахима, который был единобожником, мусульманином и не был из многобожников.", noaudio=1)),
      17: ("subhan100", {}),
      18: ("tahlil", dict(virtue="10 раз вечером (ан-Насаи). А кто скажет это 100 раз за день — словно освободил десять рабов, ему запишут сто добрых дел и сотрут сто грехов.", src="ан-Насаи («Амаль аль-йаум» 24), «Сахих ат-Таргиб» 1/272")),
      19: ("istighfar", {}),
      20: (None, dict(id="kalimat", n=97, title="А'узу би-кялимати-Лляхи-т-таммат",
         translit="А'узу би-кялимати-Лляхи-т-таммати мин шарри ма халяк.",
         ru="Прибегаю к совершенным словам Аллаха от зла того, что Он сотворил.",
         virtue="Кто скажет это трижды вечером, тому этой ночью не повредит жало (ядовитого существа).",
         src="Ахмад 2/290, ан-Насаи («Амаль аль-йаум» 590); «Сахих ат-Тирмизи» 3/187")),
      21: ("salawat", {})}

def set_build(name, title, rows):
    json.dump({"title": title, "items": rows}, open(f"adhkar/{name}.json", "w"), ensure_ascii=False, indent=1)
    print(f"adhkar/{name}.json: {len(rows)}")

ev = []
ch = hisn[HK[27]]["Adhkar"]
for j in (1, 2):
    m = dict(morning["kursi" if j == 1 else "quls"]); m["virtue"] = m["virtue"].replace("утром", "вечером").replace("до вечера", "до утра") if j == 1 else m["virtue"]; ev.append(m)
for j in range(3, 22):
    mid, ov = EV[j]
    ar = N(ch[j]["Text"].replace("\r", ""))
    if j == 5: FIX[(27, 5)] = [("عَبْدُك،", "عَبْدُكَ،")]
    for a, b in FIX.get((27, j), []) + EXTRA.get((27, j), []): a, b = N(a), N(b); assert a in ar, (j, a); ar = ar.replace(a, b)
    for a, b in GFIX: ar = ar.replace(N(a), N(b))
    ar = ar.strip()
    seen_check(f"вечер {j}", ar)
    base = dict(morning[mid]) if mid else {}
    for k in ("alt", "altAudio"): base.pop(k, None)
    base.update({k: v for k, v in ov.items() if k != "noaudio"})
    base["id"] = "e_" + base["id"]; base["ar"] = ar; base["count"] = ch[j]["Count"]
    if ov.get("noaudio"): base.pop("audio", None)
    else: base["audio"] = AUDIO.format(base["n"])
    ev.append(base)
for x in ev:
    if x["id"] in ("kursi", "quls"): x["id"] = "e_" + x["id"]
set_build("evening", "Вечерние зикры", ev)

sl = []
for it in SALAH:
    if "quran" in it:
        m = dict(morning["kursi" if it["id"] == "s_kursi" else "quls"])
        m.update(id=it["id"], title=it["title"], translit=it["translit"], virtue=it["virtue"], src=it["src"], count=1)
        if it["id"] == "s_kursi": m["pre"] = ""
        m["n"] = it["n"]; m["audio"] = AUDIO.format(it["n"])
        sl.append(m); continue
    i, j = it["h"]; primary_id = it.get("hm")
    ar = take(i, j, it.get("w"), it.get("notes"), it.get("rm", ()))
    who, other = verify(it["id"], ar, it.get("hm"))
    conflicts.extend(dia_report(f"{it['id']} ({who})", ar, other))
    rec = {k: it[k] for k in ("id", "title", "translit", "ru", "virtue", "src")}
    rec["ar"] = ar; rec["count"] = it.get("count") or (10 if it["id"] == "s_10" else 1)
    if it.get("hm"): rec["n"] = it["hm"]; rec["audio"] = AUDIO.format(it["hm"])
    sl.append(rec)
set_build("salah", "Зикры после намаза", sl)
print("расхождений огласовок для проверки:", len(conflicts))
