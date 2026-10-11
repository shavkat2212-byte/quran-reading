#!/bin/sh
# Скачивает 604 страницы мусхафа и список сур из api.quran.com в raw/
mkdir -p raw/pages
curl -s "https://api.quran.com/api/v4/chapters?language=ru" -o raw/chapters_ru.json
seq 1 604 | xargs -P 8 -I{} sh -c 'curl -s --retry 3 "https://api.quran.com/api/v4/verses/by_page/{}?words=true&word_fields=text_uthmani,line_number&per_page=50" -o raw/pages/{}.json'
