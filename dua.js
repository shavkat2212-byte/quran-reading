"use strict";
// Раздел «🤲 Дуа»: достоверные мольбы по темам (Коран + «Крепость мусульманина»), поиск и избранное.
const DUA_URL = "dua/duas.json", FAV_KEY = "qr.dua.fav.v1", DUA_OPT = "qr.dua.opt.v1";
let DUA = null, duaQ = "", duaFavOnly = false;

function favs() { try { return new Set(JSON.parse(localStorage.getItem(FAV_KEY) || "[]")); } catch (e) { return new Set(); } }
function setFavs(s) { localStorage.setItem(FAV_KEY, JSON.stringify([...s])); }
function duaOpt() { try { return Object.assign({tr: true, ru: true}, JSON.parse(localStorage.getItem(DUA_OPT) || "{}")); } catch (e) { return {tr: true, ru: true}; } }
function duaAll() { return DUA.cats.flatMap(c => c.items.map(it => Object.assign(it, {cat: c}))); }
function normAr(t) { return t.replace(/[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/g, "").replace(/[أإآٱ]/g, "ا").replace(/ى/g, "ي").replace(/ة/g, "ه").replace(/[^\u0621-\u064A ]/g, " ").replace(/\s+/g, " "); }
function normRu(t) { return t.toLowerCase().replace(/ё/g, "е").replace(/['’ʼ`«»"-]/g, "").replace(/\s+/g, " "); }
function duaAr(it) { return it.ar || (it.parts ? it.parts.map(p => p.ar).join(" ") : it.ayat.map(a => a.ar).join(" ")); }
function duaHay(it) {
  if (!it._hay) it._hay = {ru: normRu([it.title, it.translit, it.ru, it.when, it.src, it.cat.title].join(" ")), ar: normAr(duaAr(it))};
  return it._hay;
}
function duaMatch(it, q) {
  if (!q) return true;
  const h = duaHay(it);
  if (/[\u0600-\u06FF]/.test(q)) { const a = normAr(q).trim(); return !!a && h.ar.replace(/ /g, "").includes(a.replace(/ /g, "")); }
  return normRu(q).trim().split(" ").every(w => h.ru.includes(w));
}

async function duaCard() {
  DUA = DUA || await getJSON(DUA_URL);
  const n = DUA.cats.reduce((a, c) => a + c.items.length, 0), f = favs().size;
  return `<section class="card mcard duacard">
    <h3 class="sec" style="margin:0 0 6px"><span>🤲 Дуа</span><small>${f ? "⭐ " + f : ""}</small></h3>
    <div class="muted" style="font-size:14px">${n} достоверных мольб по темам: из Корана, на сон, дом, еду, поездку, трудности, болезнь, истихара…</div>
    <div class="row" style="margin-top:10px"><a class="btn" href="#/dua">🤲 Открыть дуа</a>${f ? `<a class="btn light2" href="#/dua/fav" style="flex:0 0 40%">⭐ Избранное</a>` : ""}</div>
  </section>`;
}

async function duaView(cat) {
  DUA = DUA || await getJSON(DUA_URL);
  if (cat === "fav") { duaFavOnly = true; cat = null; }
  else if (!cat) duaFavOnly = false;
  const c = cat && DUA.cats.find(x => x.id === cat);
  const opt = duaOpt();
  let h;
  if (c) {
    h = `<a class="back" href="#/dua">‹ Все темы</a>
      <h1 class="lt">${c.icon} ${esc(c.title)}</h1>
      ${duaToggles(opt)}
      <div id="dualist">${c.items.map(it => duaCardHTML(it, opt)).join("")}</div>`;
  } else {
    h = `<a class="back" href="#/">‹ На главную</a>
      <h1 class="lt">🤲 Дуа</h1>
      <div class="muted" style="font-size:14px">Мольбы из Корана и Сунны по книге «Крепость мусульманина». Арабский текст сверен по двум источникам.</div>
      <div class="dsearch"><input id="dq" type="search" placeholder="Поиск: сон, дорога, долг, رَبَّنَا…" value="${esc(duaQ)}" autocomplete="off"><button class="sbtn ${duaFavOnly ? "" : "light"}" id="dfav">⭐ ${favs().size}</button></div>
      <div id="duares"></div>
      <div id="duacats">
        <div class="dgrid">${DUA.cats.map(c => `<a class="card dcat" href="#/dua/${c.id}"><span class="di">${c.icon}</span><b>${esc(c.title)}</b><small>${c.items.length} ${plural(c.items.length, "дуа", "дуа", "дуа")}</small></a>`).join("")}</div>
        <h3 class="sec"><span>📿 Зикры со счётчиком</span></h3>
        <div class="dgrid">${Object.entries(DK_SETS).map(([k, S]) => `<a class="card dcat" href="${S.hash}"><span class="di">${S.icon}</span><b>${S.title}</b><small>со счётчиком</small></a>`).join("")}</div>
      </div>`;
  }
  h += `<p class="foot">Арабский текст: «Хисн аль-муслим» (github.com/asellam/HisnElMuslim), сверено по буквам с официальным hisnmuslim.com и другими наборами; аяты — api.quran.com (усмани), сверено с api.alquran.cloud; перевод аятов — Э. Кулиев. Звук: hisnmuslim.com, аяты — Мишари аль-Афаси (everyayah.com).</p>`;
  $app.innerHTML = h; window.scrollTo(0, 0);
  const list = document.getElementById("dualist") || document.getElementById("duares");
  document.getElementById("app").onclick = duaClick;
  for (const k of ["tr", "ru"]) { const e = document.getElementById("dopt" + k); if (e) e.onchange = () => { const o = duaOpt(); o[k] = e.checked; localStorage.setItem(DUA_OPT, JSON.stringify(o)); duaView(cat); }; }
  if (!c) {
    const q = document.getElementById("dq");
    q.oninput = () => { duaQ = q.value; duaResults(); };
    document.getElementById("dfav").onclick = () => { duaFavOnly = !duaFavOnly; history.replaceState(null, "", duaFavOnly ? "#/dua/fav" : "#/dua"); duaResults(); };
    duaResults();
  }
}
function duaToggles(opt) {
  return `<div class="ctrls"><label class="toggle"><input type="checkbox" id="doptr" ${opt.tr ? "checked" : ""}> Транскрипция</label><label class="toggle"><input type="checkbox" id="doptru" ${opt.ru ? "checked" : ""}> Перевод</label></div>`;
}
function duaResults() {
  const box = document.getElementById("duares"), cats = document.getElementById("duacats"), fb = document.getElementById("dfav");
  const F = favs(); fb.className = "sbtn " + (duaFavOnly ? "" : "light"); fb.textContent = "⭐ " + F.size;
  if (!duaQ.trim() && !duaFavOnly) { box.innerHTML = ""; cats.style.display = ""; return; }
  const res = duaAll().filter(it => (!duaFavOnly || F.has(it.id)) && duaMatch(it, duaQ));
  cats.style.display = "none";
  const opt = duaOpt();
  box.innerHTML = `<div class="muted dcount">${duaFavOnly ? "⭐ Избранное" : "Найдено"}: ${res.length}${duaFavOnly && !res.length ? " — нажмите ☆ на любой дуа, чтобы сохранить её здесь" : ""}</div>` +
    res.map(it => duaCardHTML(it, opt, true)).join("");
}
function duaArabic(it) {
  if (it.ayat) return quranHTML(it);
  if (it.parts) return it.parts.map(p => `${p.label ? `<div class="dlab">${esc(p.label)}</div>` : ""}<div class="dkar ar">${esc(p.ar)}${p.count > 1 ? ` <span class="dcnt">×${p.count}</span>` : ""}</div>`).join("");
  return `<div class="dkar ar">${esc(it.ar)}</div>`;
}
function duaCardHTML(it, opt, showCat) {
  const fav = favs().has(it.id);
  return `<section class="card dua" id="du-${it.id}" data-id="${it.id}">
    <div class="dkh"><span class="dkt">${esc(it.title)}</span><button class="fav ${fav ? "on" : ""}" data-act="fav" title="В избранное">${fav ? "⭐" : "☆"}</button></div>
    ${showCat ? `<div class="dcatl muted">${it.cat.icon} ${esc(it.cat.title)}</div>` : ""}
    ${duaArabic(it)}
    ${opt.tr ? `<div class="dktr">${esc(it.translit)}</div>` : ""}
    ${opt.ru ? `<div class="dkru">${esc(it.ru)}${it.ruSrc ? ` <small>(${esc(it.ruSrc)})</small>` : ""}</div>` : ""}
    <div class="tip dkv">🕰 ${esc(it.when)}</div>
    ${it.grade ? `<div class="dgrade">⚠️ ${esc(it.grade)}</div>` : ""}
    <div class="dksrc">📚 ${esc(it.src)}</div>
    <div class="dkctl">${it.audio && it.audio.length ? `<button class="sbtn" data-act="play">▶ Слушать</button>` : ""}<button class="sbtn light" data-act="copy">📋 Копировать</button></div>
  </section>`;
}
let duaSeq = null;
function duaPlay(it, el) {
  if (playingEl === el && !audio.paused) { audio.pause(); el.classList.remove("playing"); playingEl = null; duaSeq = null; return; }
  duaSeq = {list: it.audio, i: 0, el}; play(it.audio[0], el);
}
audio.addEventListener("ended", () => {
  if (!duaSeq) return;
  if (++duaSeq.i < duaSeq.list.length) play(duaSeq.list[duaSeq.i], duaSeq.el); else duaSeq = null;
});
function duaClick(ev) {
  const b = ev.target.closest("[data-act]"); if (!b) return;
  const card = b.closest(".dua"); if (!card) return;
  const it = duaAll().find(x => x.id === card.dataset.id); if (!it) return;
  if (b.dataset.act === "fav") {
    const F = favs(); F.has(it.id) ? F.delete(it.id) : F.add(it.id); setFavs(F);
    b.classList.toggle("on", F.has(it.id)); b.textContent = F.has(it.id) ? "⭐" : "☆"; buzz(10);
    const fb = document.getElementById("dfav"); if (fb) fb.textContent = "⭐ " + F.size;
  }
  if (b.dataset.act === "play") duaPlay(it, b);
  if (b.dataset.act === "copy") {
    const t = [duaAr(it), it.translit, it.ru, it.src].join("\n\n");
    (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(() => { b.textContent = "✓ Скопировано"; }, () => { b.textContent = "не удалось"; });
  }
}
