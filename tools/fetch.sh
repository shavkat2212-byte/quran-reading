#!/bin/sh
# Скачивает слова Фатихи и 30-го джуза из api.quran.com в папку raw/
mkdir -p raw
for n in 1 $(seq 78 114); do
  curl -s "https://api.quran.com/api/v4/verses/by_chapter/$n?words=true&word_fields=text_uthmani,text_imlaei&per_page=50" -o raw/ch$n.json
done
