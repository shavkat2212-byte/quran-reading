# Собирает страницы мусхафа (pages/NNN.json) из api.quran.com: sh tools/fetch_pages.sh && python3 tools/build_pages.py
# Формат страницы: {"p": номер, "j": джуз, "v": [{"k": "2:1", "w": [[текст, строка, транскрипция], ...], "e": [строка, "١"]}]}
# Номер слова в аяте = его порядок в "w" (1, 2, 3…); звук: audio.qurancdn.com/wbw/SSS_AAA_WWW.mp3
import json, os
os.makedirs("pages", exist_ok=True)
ch = json.load(open("raw/chapters_ru.json"))["chapters"]
p1 = json.load(open("raw/pages/1.json"))["verses"][0]
assert p1["verse_key"] == "1:1"
basmala = [[w["text_uthmani"], (w.get("transliteration") or {}).get("text") or ""] for w in p1["words"] if w["char_type_name"] == "word"]
json.dump({"basmala": basmala, "chapters": [{"id": c["id"], "n": c["name_simple"], "ar": c["name_arabic"], "ru": c["translated_name"]["name"],
            "b": c["bismillah_pre"], "vc": c["verses_count"], "pg": c["pages"]} for c in ch]},
          open("pages/chapters.json", "w"), ensure_ascii=False, separators=(",", ":"))
total = 0
for n in range(1, 605):
    d = json.load(open(f"raw/pages/{n}.json"))
    assert d["pagination"]["total_pages"] == 1
    out = {"p": n, "j": d["verses"][0]["juz_number"], "v": []}
    for v in d["verses"]:
        ws = [w for w in v["words"] if w["char_type_name"] == "word"]
        ends = [w for w in v["words"] if w["char_type_name"] == "end"]
        assert [w["position"] for w in ws] == list(range(1, len(ws) + 1)), v["verse_key"]
        assert len(ends) == 1, v["verse_key"]
        out["v"].append({"k": v["verse_key"],
                         "w": [[w["text_uthmani"], w["line_number"], (w.get("transliteration") or {}).get("text") or ""] for w in ws],
                         "e": [ends[0]["line_number"], ends[0]["text_uthmani"]]})
        total += 1
    json.dump(out, open(f"pages/{n:03d}.json", "w"), ensure_ascii=False, separators=(",", ":"))
assert total == 6236, total
print("pages ok, verses", total)
