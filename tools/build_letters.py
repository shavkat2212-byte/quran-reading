# Собирает уроки раздела «Буквы» (lessons/letters/L*.json).
# Каждая буква проверяется по официальному имени Unicode, чтобы не перепутать символы.
import json, os, random, unicodedata
os.makedirs("lessons/letters", exist_ok=True)
FATHA, KASRA, DAMMA, TATWEEL = "\u064E", "\u0650", "\u064F", "\u0640"
# символ, имя Unicode, название по-русски, звук (русская транскрипция для слогов), соединяется ли с последующей буквой
L = [
 ("\u0627","ARABIC LETTER ALEF","Алиф","",False),
 ("\u0628","ARABIC LETTER BEH","Ба","б",True),
 ("\u062A","ARABIC LETTER TEH","Та","т",True),
 ("\u062B","ARABIC LETTER THEH","Са (межзубная)","с̱",True),
 ("\u062C","ARABIC LETTER JEEM","Джим","дж",True),
 ("\u062D","ARABIC LETTER HAH","Ха (гортанная)","х̣",True),
 ("\u062E","ARABIC LETTER KHAH","Хо","х",True),
 ("\u062F","ARABIC LETTER DAL","Даль","д",False),
 ("\u0630","ARABIC LETTER THAL","Заль (межзубная)","з̱",False),
 ("\u0631","ARABIC LETTER REH","Ра","р",False),
 ("\u0632","ARABIC LETTER ZAIN","Зай","з",False),
 ("\u0633","ARABIC LETTER SEEN","Син","с",True),
 ("\u0634","ARABIC LETTER SHEEN","Шин","ш",True),
 ("\u0635","ARABIC LETTER SAD","Сод","с̣",True),
 ("\u0636","ARABIC LETTER DAD","Дод","д̣",True),
 ("\u0637","ARABIC LETTER TAH","То","т̣",True),
 ("\u0638","ARABIC LETTER ZAH","Зо","з̣",True),
 ("\u0639","ARABIC LETTER AIN","Айн","ʿ",True),
 ("\u063A","ARABIC LETTER GHAIN","Гойн","ғ",True),
 ("\u0641","ARABIC LETTER FEH","Фа","ф",True),
 ("\u0642","ARABIC LETTER QAF","Коф","қ",True),
 ("\u0643","ARABIC LETTER KAF","Каф","к",True),
 ("\u0644","ARABIC LETTER LAM","Лям","л",True),
 ("\u0645","ARABIC LETTER MEEM","Мим","м",True),
 ("\u0646","ARABIC LETTER NOON","Нун","н",True),
 ("\u0647","ARABIC LETTER HEH","Ха (лёгкая)","һ",True),
 ("\u0648","ARABIC LETTER WAW","Вав","в",False),
 ("\u064A","ARABIC LETTER YEH","Йа","й",True),
]
assert len(L) == 28 and len({c for c, *_ in L}) == 28
for c, name, *_ in L:
    assert unicodedata.name(c) == name, (c, unicodedata.name(c), name)
for ch, nm in [(FATHA,"ARABIC FATHA"),(KASRA,"ARABIC KASRA"),(DAMMA,"ARABIC DAMMA"),(TATWEEL,"ARABIC TATWEEL")]:
    assert unicodedata.name(ch) == nm
EXTRA = [
 ("\u0621","ARABIC LETTER HAMZA","Хамза"),
 ("\u0623","ARABIC LETTER ALEF WITH HAMZA ABOVE","Хамза на алифе (сверху)"),
 ("\u0625","ARABIC LETTER ALEF WITH HAMZA BELOW","Хамза под алифом"),
 ("\u0624","ARABIC LETTER WAW WITH HAMZA ABOVE","Хамза на вав"),
 ("\u0626","ARABIC LETTER YEH WITH HAMZA ABOVE","Хамза на «зубце» (йа без точек)"),
 ("\u0629","ARABIC LETTER TEH MARBUTA","Та марбута (круглая та)"),
 ("\u0649","ARABIC LETTER ALEF MAKSURA","Алиф максура (йа без точек = «а»)"),
]
for c, name, _ in EXTRA: assert unicodedata.name(c) == name, (c, name)
by = {c: (c, ru, snd, conn) for c, _, ru, snd, conn in L}
def letter(c): ch, ru, snd, conn = by[c]; return {"type": "letter", "ar": ch, "name": ru}
def forms(c):
    ch, ru, snd, conn = by[c]
    f = [ch, ch + TATWEEL, TATWEEL + ch + TATWEEL, TATWEEL + ch] if conn else [ch, TATWEEL + ch]
    return {"type": "forms", "ar": " ".join(f), "forms": f, "name": ru,
            "hint": "отдельно · начало · середина · конец" if conn else "отдельно · конец (с буквой слева не соединяется)"}
HAMZA_ALEF = {FATHA: "\u0623", KASRA: "\u0625", DAMMA: "\u0623"}
VOW = {FATHA: "а", KASRA: "и", DAMMA: "у"}
def syl(c, v):
    ch, ru, snd, conn = by[c]
    if ch == "\u0627":  # гласная ставится на хамзу: أَ إِ أُ
        return {"type": "letter", "ar": HAMZA_ALEF[v] + v, "name": VOW[v]}
    s = snd + VOW[v]
    if snd == "й" and v == FATHA: s = "йа"
    return {"type": "letter", "ar": ch + v, "name": s}
for it in [syl(c, v) for c in by for v in (FATHA, KASRA, DAMMA)]:
    for x in it["ar"]: unicodedata.name(x)

lessons = []
def add(title, sub, level, target, tip, items, kind="letter"):
    lid = f"L{len(lessons)+1:02d}"
    les = {"id": lid, "section": "letters", "title": title, "subtitle": sub, "level": level, "targetSeconds": target, "showHints": True, "tip": tip, "items": items}
    json.dump(les, open(f"lessons/letters/{lid}.json", "w"), ensure_ascii=False, indent=1)
    lessons.append({"id": lid, "title": title, "subtitle": sub, "level": level, "count": len(items), "targetSeconds": target})
G = lambda s: [letter(c) for c in s]
add("Алиф, Ба, Та, Са", "ا ب ت ث", 1, 15, "Ба, Та, Са — одна и та же форма, разница только в точках: одна снизу, две сверху, три сверху. Смотрите сначала на точки.", G("ابتث"))
add("Джим, Ха, Хо", "ج ح خ", 1, 15, "Одна форма: точка внутри (ج), без точки (ح), точка сверху (خ).", G("جحخ"))
add("Даль, Заль, Ра, Зай", "د ذ ر ز", 1, 15, "Пары: د и ذ (точка сверху), ر и ز (точка сверху). Ра и Зай опускаются ниже строки. Эти буквы не соединяются с буквой после себя.", G("دذرز"))
add("Син, Шин, Сод, Дод", "س ش ص ض", 1, 18, "Син и Шин — «зубцы» (у Шин три точки). Сод и Дод — «петля» (у Дод точка сверху).", G("سشصض"))
add("То, Зо, Айн, Гойн", "ط ظ ع غ", 1, 18, "То и Зо — петля с палочкой (у Зо точка). Айн и Гойн — «крючок» (у Гойн точка сверху).", G("طظعغ"))
add("Фа, Коф, Каф, Лям", "ف ق ك ل", 1, 18, "Фа — одна точка, Коф — две точки и хвост ниже строки. Каф — с «загогулиной» внутри, Лям — высокий крючок.", G("فقكل"))
add("Мим, Нун, Ха, Вав, Йа", "م ن ه و ي", 1, 20, "Нун — чаша с точкой. Ха (лёгкая) ه отличается от ح. Вав и Йа бывают и согласными, и долгими гласными.", G("منهوي"))
add("Хамза, та марбута, алиф максура", "ء أ إ ؤ ئ ة ى", 2, 25, "Хамза — это звук «гортанной смычки», она может сидеть на алифе, вав или на зубце. ة читается как «т» (или «х» при остановке). ى в конце слова — это долгое «а».", [{"type": "letter", "ar": c, "name": ru} for c, _, ru in EXTRA])
add("Все 28 букв по порядку", "Повторение алфавита", 2, 60, "Назовите каждую букву вслух. В круге «на время» порядок перемешается — так проверяется, что вы узнаёте букву, а не помните порядок.", G([c for c, *_ in L]))
add("Формы букв: Ба, Та, Са, Нун, Йа", "Начало · середина · конец слова", 2, 30, "В начале и середине слова эти пять букв выглядят одинаково — маленький зубец. Различаются только точками: ب 1 снизу, ت 2 сверху, ث 3 сверху, ن 1 сверху, ي 2 снизу.", [forms(c) for c in "بتثني"])
add("Формы букв: Джим…Коф", "ج ح خ ع غ ه ف ق", 2, 40, "Обратите внимание на Айн/Гойн в середине слова (ـعـ ـغـ) и на Ха (лёгкую), которая сильно меняется: هـ ـهـ ـه.", [forms(c) for c in "جحخعغهفق"])
add("Формы букв: Син…Мим", "س ش ص ض ط ظ ك ل م", 3, 40, "Каф в начале и середине слова пишется без «загогулины»: كـ ـكـ. Мим в середине — маленькая петля.", [forms(c) for c in "سشصضطظكلم"])
add("Буквы, которые не соединяются слева", "ا د ذ ر ز و", 3, 20, "После этих шести букв слово «разрывается» — следующая буква пишется в начальной форме. Поэтому в слове бывают промежутки.", [forms(c) for c in "ادذرزو"])
add("Фатха: ба, та, са…", "Все буквы с фатхой ( َ )", 3, 60, "Фатха — чёрточка над буквой, звук «а». Читайте ровно, в одном темпе, не растягивая.", [syl(c, FATHA) for c in by])
add("Касра: би, ти, си…", "Все буквы с касрой ( ِ )", 3, 55, "Касра — чёрточка под буквой, звук «и».", [syl(c, KASRA) for c in by])
add("Дамма: бу, ту, су…", "Все буквы с даммой ( ُ )", 3, 50, "Дамма — маленькая вав над буквой, звук «у».", [syl(c, DAMMA) for c in by])
rnd = random.Random(2026)
mix = [syl(c, v) for c in by for v in (FATHA, KASRA, DAMMA)]
rnd.shuffle(mix)
add("Огласовки вперемешку", "а · и · у в случайном порядке", 4, 40, "Здесь буквы и огласовки идут вразнобой — смотрите и на букву, и на огласовку.", mix[:24])
json.dump(lessons, open("lessons/letters/_list.json", "w"), ensure_ascii=False, indent=1)
for l in lessons: print(l["id"], l["count"], l["targetSeconds"], l["title"])
