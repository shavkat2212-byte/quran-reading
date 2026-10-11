"use strict";
// Чтение Корана по страницам (мединский мусхаф, 604 страницы). Использует общие функции из app.js.
const MUSHAF_PAGES = 604, START_PAGE = 2;
let META = null;
async function meta() { return META = META || await getJSON("pages/chapters.json"); }
function chaptersOn(n) { return META.chapters.filter(c => c.pg[0] <= n && n <= c.pg[1]); }
function chName(c) { return `${c.n} (${c.ru})`; }
function wbwUrl(k, pos) { const [s, a] = k.split(":").map(Number); const z = (x) => String(x).padStart(3, "0"); return `https://audio.qurancdn.com/wbw/${z(s)}_${z(a)}_${z(pos)}.mp3`; }
function ayahUrl(k) { const [s, a] = k.split(":").map(Number); const z = (x) => String(x).padStart(3, "0"); return `https://everyayah.com/data/Alafasy_128kbps/${z(s)}${z(a)}.mp3`; }

// страница: сначала свой файл, если нет — напрямую из api.quran.com (тот же формат)
async function getPage(n) {
  try { return await getJSON(`pages/${String(n).padStart(3, "0")}.json`); }
  catch (e) {
    const r = await fetch(`https://api.quran.com/api/v4/verses/by_page/${n}?words=true&word_fields=text_uthmani,line_number&per_page=50`);
    if (!r.ok) throw e;
    const d = await r.json();
    return {p: n, j: d.verses[0].juz_number, v: d.verses.map(v => {
      const ws = v.words.filter(w => w.char_type_name === "word"), en = v.words.find(w => w.char_type_name === "end");
      return {k: v.verse_key, w: ws.map(w => [w.text_uthmani, w.line_number, (w.transliteration || {}).text || ""]), e: [en.line_number, en.text_uthmani]};
    })};
  }
}

// ---------- прогресс ----------
function pg(p) { p.pages = p.pages || {}; return p.pages; }
function pageStreak(p) {
  const set = new Set(Object.values(pg(p)).map(x => x.d)); let n = 0; const d = new Date();
  if (!set.has(today(d))) d.setDate(d.getDate() - 1);
  while (set.has(today(d))) { n++; d.setDate(d.getDate() - 1); }
  return n;
}
function pageState(p) {
  const P = pg(p); const nums = Object.keys(P).map(Number);
  const readToday = nums.filter(n => P[n].d === today()).sort((a, b) => a - b);
  const main = nums.filter(n => n >= START_PAGE);
  const next = Math.min(MUSHAF_PAGES, main.length ? Math.max(...main) + 1 : START_PAGE);
  return {readToday, next, count: nums.length};
}
function ruDate(s) { const [y, m, d] = s.split("-").map(Number); return d + " " + ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"][m - 1]; }

// ---------- карточка на главной ----------
async function mushafCard() {
  await meta(); const p = load(); const st = pageState(p);
  const cur = st.readToday.length ? st.readToday[st.readToday.length - 1] : st.next;
  const chs = chaptersOn(cur).map(chName).join(", ");
  const s = pageStreak(p);
  const btn = st.readToday.length
    ? `<div class="okday">✓ Сегодня прочитано: стр. ${st.readToday.join(", ")}</div>
       <a class="btn outline" href="#/page/${st.next}">Завтра: страница ${st.next} · можно сейчас ▸</a>`
    : `<a class="btn big" href="#/page/${st.next}">📖 Страница дня: ${st.next}</a>`;
  return `<section class="card mcard">
    <h3 class="sec" style="margin:0 0 6px"><span>📖 Чтение Корана по страницам</span><small>${s ? "🔥 " + s + " " + plural(s, "день", "дня", "дней") : ""}</small></h3>
    <div class="muted" style="font-size:14px">${esc(chs)} · стр. ${cur} из ${MUSHAF_PAGES}</div>
    <div class="pbar" style="margin:8px 0 12px"><i style="width:${Math.max(st.count ? 0.5 : 0, st.count / MUSHAF_PAGES * 100).toFixed(1)}%"></i></div>
    ${btn}
    <div class="row" style="margin-top:10px"><a class="btn light2" href="#/pages">Выбрать страницу</a><a class="btn light2" href="#/page/1">Аль-Фатиха</a></div>
    <div class="muted" style="font-size:13px;margin-top:8px">Прочитано страниц: ${st.count} · одна страница в день — Коран целиком примерно за 1 год 8 месяцев.</div>
  </section>`;
}

// ---------- выбор страницы ----------
async function pagePicker() {
  await meta(); const P = pg(load());
  let h = `<a class="back" href="#/">‹ На главную</a><h1 class="lt">Выбрать страницу</h1>
    <div class="card"><div class="row"><input id="pnum" type="number" min="1" max="604" inputmode="numeric" placeholder="1–604" class="inp"><button class="btn" id="pgo" style="flex:0 0 110px">Открыть</button></div></div>
    <h3 class="sec"><span>Суры</span><small>начальная страница</small></h3>`;
  for (const c of META.chapters) {
    const read = Object.keys(P).filter(n => n >= c.pg[0] && n <= c.pg[1]).length, tot = c.pg[1] - c.pg[0] + 1;
    h += `<a class="card lesson ${read >= tot ? "done" : ""}" href="#/page/${c.pg[0]}"><div class="num">${read >= tot ? "✓" : c.id}</div>
      <div><div class="t">${esc(c.n)} <span class="ar" style="font-size:20px">${esc(c.ar)}</span></div><div class="s">${esc(c.ru)} · ${c.vc} аятов · стр. ${c.pg[0]}${tot > 1 ? "–" + c.pg[1] : ""}</div></div>
      <div class="best">${read ? read + "/" + tot : ""}</div></a>`;
  }
  $app.innerHTML = h; window.scrollTo(0, 0);
  const go = () => { const n = +document.getElementById("pnum").value; if (n >= 1 && n <= 604) location.hash = "#/page/" + n; };
  document.getElementById("pgo").onclick = go;
  document.getElementById("pnum").onkeydown = e => { if (e.key === "Enter") go(); };
}

// ---------- страница ----------
let PS = null;
async function pageView(n) {
  n = Math.max(1, Math.min(MUSHAF_PAGES, n | 0));
  await meta(); const page = await getPage(n);
  PS = {n, page, t0: 0, justDone: false, queue: []};
  drawPage(); window.scrollTo(0, 0);
}
function pageBody(page, tr) {
  // слова по строкам мусхафа; перед первым аятом суры — заголовок и басмала
  const lines = new Map(); const heads = new Map();
  for (const v of page.v) {
    const [s, a] = v.k.split(":").map(Number);
    const first = v.w.length ? v.w[0][1] : v.e[0];
    if (a === 1) heads.set(first, s);
    v.w.forEach((w, i) => { if (!lines.has(w[1])) lines.set(w[1], []); lines.get(w[1]).push({t: "w", k: v.k, pos: i + 1, ar: w[0], tr: w[2]}); });
    if (!lines.has(v.e[0])) lines.set(v.e[0], []);
    lines.get(v.e[0]).push({t: "e", k: v.k, ar: v.e[1]});
  }
  const nums = [...lines.keys()].sort((a, b) => a - b);
  const center = page.p <= 2;
  let h = "";
  nums.forEach((ln, idx) => {
    if (heads.has(ln)) {
      const c = META.chapters[heads.get(ln) - 1];
      h += `<div class="shead"><span class="ar">${esc(c.ar)}</span><small>Сура ${c.id} · ${esc(c.n)} (${esc(c.ru)}) · ${c.vc} аятов</small></div>`;
      if (c.b && c.id !== 1 && c.id !== 9) h += `<div class="basm ar" data-basm="1">${META.basmala.map(b => esc(b[0])).join(" ")}</div>`;
    }
    const items = lines.get(ln);
    const lastOfSurah = items.length && items[items.length - 1].t === "e" && (heads.has(nums[idx + 1]) || isLastAyah(items[items.length - 1].k));
    h += `<div class="ln ${center || lastOfSurah ? "c" : ""}">` + items.map(it => it.t === "w"
      ? `<span class="mw" data-k="${it.k}" data-p="${it.pos}"><span class="ar">${esc(it.ar)}</span>${tr ? `<small>${esc(it.tr)}</small>` : ""}</span>`
      : `<span class="me" data-k="${it.k}" title="Аят ${it.k} — слушать"><span class="ar">﴿${esc(it.ar)}﴾</span></span>`).join(" ") + `</div> `;
  });
  return h;
}
function isLastAyah(k) { const [s, a] = k.split(":").map(Number); return META.chapters[s - 1].vc === a; }
function fitLines() {
  // подбираем размер шрифта так, чтобы самая длинная строка мусхафа влезла в ширину экрана
  const box = document.querySelector(".mushaf.lines"); if (!box) return;
  box.style.fontSize = "40px";
  const W = box.clientWidth - 4; let worst = 1;
  box.querySelectorAll(".ln").forEach(l => { l.classList.add("measure"); const r = W / l.scrollWidth; if (r < worst) worst = r; l.classList.remove("measure"); });
  box.style.fontSize = Math.max(14, Math.floor(40 * worst * 0.98)) + "px";
}
function drawPage() {
  const {n, page} = PS; const p = load(); const P = pg(p); const done = P[n];
  const mode = p.mushafLines ? "lines" : "flow"; const tr = !!p.mushafTr;
  const chs = chaptersOn(n);
  const timing = PS.t0 && !done;
  const st = pageState(p);
  let h = `<div class="phead"><a class="back" href="#/">‹ На главную</a><a class="back" href="#/pages">Страницы ☰</a></div>
    <div class="muted" style="font-size:14px">Джуз ${page.j} · страница ${n} из ${MUSHAF_PAGES}</div>
    <h1 class="lt">${chs.map(c => esc(c.n) + ` <span class="ar" style="font-size:.9em">${esc(c.ar)}</span>`).join(" · ")}</h1>
    ${PS.justDone ? `<div class="tip">✓ Страница ${n} прочитана${done && done.ms ? " за " + mmss(done.ms) : ""}. <b>Завтра: страница ${st.next}.</b> Можно читать дальше и сейчас.</div>` : ""}
    <div class="ctrls">
      <label class="toggle"><input type="checkbox" id="mtr" ${tr ? "checked" : ""}> Транскрипция</label>
      <label class="toggle"><input type="checkbox" id="mbig" ${mode === "lines" ? "checked" : ""}> Строки как в мусхафе</label>
      <button class="sbtn" id="mplay">▶ Слушать страницу</button>
    </div>
    <div class="muted" style="font-size:13px;margin:0 2px 8px">Нажмите на слово — услышите его; на зелёный номер аята — весь аят (Мишари аль-Афаси).</div>
    <div class="mushaf ${tr || mode === "flow" ? "flow" : "lines"} ${tr ? "tr" : ""}">${pageBody(page, tr)}</div>
    <div class="pnav"><a class="btn light2 ${n >= MUSHAF_PAGES ? "dis" : ""}" href="#/page/${n + 1}">◀ Стр. ${Math.min(n + 1, MUSHAF_PAGES)}</a><a class="btn light2 ${n <= 1 ? "dis" : ""}" href="#/page/${n - 1}">Стр. ${Math.max(n - 1, 1)} ▶</a></div>
    <p class="foot">Текст и звук слов: quran.com · Аяты: Мишари аль-Афаси (everyayah.com)</p>`;
  $app.innerHTML = h;
  let dock = document.querySelector(".dock"); if (!dock) { dock = document.createElement("div"); dock.className = "dock"; document.body.appendChild(dock); }
  if (done) dock.innerHTML = `<div class="in"><div class="muted center" style="font-size:14px;margin-bottom:6px">✓ Прочитано ${ruDate(done.d)}${done.ms ? " · " + mmss(done.ms) : ""}</div><a class="btn ${n === st.next ? "" : "outline"}" href="#/page/${st.next}">${st.next > n ? "Следующая непрочитанная: стр. " + st.next : "К странице дня: " + st.next}</a></div>`;
  else if (timing) dock.innerHTML = `<div class="in"><div class="timer" id="tm">0:00</div><button class="btn" id="mdone">Прочитал страницу ✓</button></div>`;
  else dock.innerHTML = `<div class="in row"><button class="btn outline" id="mtime" style="flex:0 0 38%">⏱ Засечь</button><button class="btn" id="mdone">Прочитал страницу ✓</button></div>`;
  fitDock();
  if (!tr && mode === "lines") { fitLines(); if (document.fonts) document.fonts.ready.then(fitLines); }
  if (timing) tickPage();

  $app.querySelectorAll(".mw").forEach(el => el.onclick = () => { if (PS.t0 && !load().pages?.[n]) return; PS.queue = []; play(wbwUrl(el.dataset.k, +el.dataset.p), el); });
  $app.querySelectorAll(".me").forEach(el => el.onclick = () => { PS.queue = []; playAyah(el.dataset.k); });
  const bm = $app.querySelector("[data-basm]"); if (bm) bm.onclick = () => { PS.queue = []; play(ayahUrl("1:1"), bm); };
  const on = (id, f) => { const e = document.getElementById(id); if (e) e.onclick = f; };
  on("mtr", () => { const q = load(); q.mushafTr = document.getElementById("mtr").checked; save(q); drawPage(); });
  on("mbig", () => { const q = load(); q.mushafLines = document.getElementById("mbig").checked; save(q); drawPage(); });
  on("mplay", () => { PS.queue = page.v.map(v => v.k); nextInQueue(); });
  on("mtime", () => { PS.t0 = performance.now(); drawPage(); });
  on("mdone", () => {
    const q = load(); pg(q)[n] = {d: today()}; if (PS.t0) pg(q)[n].ms = Math.round(performance.now() - PS.t0);
    markDay(q); save(q); clearInterval(timerId); PS.t0 = 0; PS.justDone = true; renderStreak(); drawPage(); window.scrollTo(0, 0);
  });
}
function mmss(ms) { const s = Math.round(ms / 1000); return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); }
function tickPage() { clearInterval(timerId); timerId = setInterval(() => { const e = document.getElementById("tm"); if (!e) return clearInterval(timerId); e.textContent = mmss(performance.now() - PS.t0); }, 250); }
function playAyah(k) {
  document.querySelectorAll(".mw.hl").forEach(e => e.classList.remove("hl"));
  document.querySelectorAll(`.mw[data-k="${k}"]`).forEach(e => e.classList.add("hl"));
  play(ayahUrl(k), document.querySelector(`.me[data-k="${k}"]`));
}
function nextInQueue() {
  if (!PS || !PS.queue.length) { document.querySelectorAll(".mw.hl").forEach(e => e.classList.remove("hl")); return; }
  const k = PS.queue.shift(); playAyah(k);
  const el = document.querySelector(`.me[data-k="${k}"]`); if (el) el.scrollIntoView({block: "center", behavior: "smooth"});
}
audio.addEventListener("ended", () => { if (location.hash.startsWith("#/page/")) nextInQueue(); });
