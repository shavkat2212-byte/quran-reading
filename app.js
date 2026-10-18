"use strict";
// Самоучитель чтения Корана — статическое приложение, прогресс хранится в localStorage телефона.
const VERSION = "5";
const KEY = "qr.progress.v1";
const $app = document.getElementById("app");
const LEVELS = {1: "Очень легко", 2: "Легко", 3: "Средне", 4: "Сложнее", 5: "Аяты"};
let INDEX = null;
const cache = {};

// ---------- прогресс ----------
function load() {
  try { return Object.assign({done: {}, runs: {}, days: [], translit: false}, JSON.parse(localStorage.getItem(KEY) || "{}")); }
  catch (e) { return {done: {}, runs: {}, days: [], translit: false}; }
}
function save(p) { localStorage.setItem(KEY, JSON.stringify(p)); }
function today(d = new Date()) {
  const z = n => String(n).padStart(2, "0");
  return d.getFullYear() + "-" + z(d.getMonth() + 1) + "-" + z(d.getDate());
}
function markDay(p) { const t = today(); if (!p.days.includes(t)) p.days.push(t); }
function streak(p) {
  const set = new Set(p.days); let n = 0; const d = new Date();
  if (!set.has(today(d))) d.setDate(d.getDate() - 1); // серия не сгорает до конца сегодняшнего дня
  while (set.has(today(d))) { n++; d.setDate(d.getDate() - 1); }
  return n;
}
function best(p, id) { const r = p.runs[id] || []; return r.length ? Math.min(...r.map(x => x.ms)) : null; }
function fmt(ms) { return (ms / 1000).toFixed(1).replace(".", ",") + " с"; }
function plural(n, a, b, c) { const m = n % 10, h = n % 100; return m == 1 && h != 11 ? a : (m >= 2 && m <= 4 && (h < 10 || h >= 20) ? b : c); }
function esc(s) { return String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c])); }
// арабские фрагменты в русском тексте показываем Коранским шрифтом
function rich(s) { return esc(s).replace(/([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF](?:[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s]*[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF])?)/g, '<span class="ar">$1</span>'); }

function renderStreak() {
  const s = streak(load());
  document.getElementById("streak").textContent = s ? "🔥 " + s + " " + plural(s, "день", "дня", "дней") : "";
}

// ---------- данные ----------
async function getJSON(url) {
  if (!cache[url]) cache[url] = fetch(url + (url.includes("?") ? "&" : "?") + "v=" + VERSION, {cache: "no-cache"}).then(r => { if (!r.ok) throw new Error(url + " " + r.status); return r.json(); });
  return cache[url];
}

// ---------- аудио ----------
const audio = new Audio(); audio.preload = "none";
let playingEl = null;
function play(url, el) {
  if (!url) return;
  if (playingEl) playingEl.classList.remove("playing");
  playingEl = el || null; if (el) el.classList.add("playing");
  audio.src = url; audio.currentTime = 0;
  audio.play().catch(() => {});
}
audio.addEventListener("ended", () => { if (playingEl) playingEl.classList.remove("playing"); playingEl = null; });

// ---------- главная ----------
const OWNER = "Приложение Шавката Ташходжаева для улучшения чтения Корана";
function sections() { return INDEX.sections || [{id: "reading", title: "Уроки", dir: "", lessons: INDEX.lessons}]; }
function findLesson(id) {
  for (const s of sections()) { const l = s.lessons.find(x => x.id === id); if (l) return {sec: s, l}; }
  return null;
}
function lessonUrl(sec, id) { return "lessons/" + (sec.dir ? sec.dir + "/" : "") + id + ".json"; }
function href(sec, id) { return sec.id === "letters" ? "#/letters/" + id : "#/lesson/" + id; }
function nextOf(sec, p) { return sec.lessons.find(l => !p.done[l.id]) || sec.lessons[sec.lessons.length - 1]; }
async function home() {
  INDEX = INDEX || await getJSON("lessons/index.json");
  const p = load(); const S = sections();
  const all = S.flatMap(s => s.lessons);
  const doneN = all.filter(l => p.done[l.id]).length;
  const s = streak(p);
  let h = `<section class="card hero">
    <h2>Ассаляму алейкум, Шавкат!</h2>
    <div>Самоучитель беглого чтения. 15 минут в день — и чтение пойдёт без остановок.</div>
    <div class="stats"><div><b>${doneN}/${all.length}</b>уроков</div><div><b>${s}</b>${plural(s, "день", "дня", "дней")} подряд</div><div><b>${p.days.length}</b>${plural(p.days.length, "день", "дня", "дней")} занятий</div></div>
    <div class="row">${S.map(sec => { const n = nextOf(sec, p); const d = sec.lessons.filter(l => p.done[l.id]).length;
      return `<a class="btn ${sec.id === "letters" ? "light" : "gold"}" href="${href(sec, n.id)}">${sec.id === "letters" ? "🔤 Буквы" : "📝 Уроки"} ▸</a>`; }).join("")}</div>
  </section>`;
  try { h += await adhkarCard(); } catch (e) { console.error(e); }
  try { h += await duaCard(); } catch (e) { console.error(e); }
  try { h += await mushafCard(); } catch (e) { console.error(e); }
  for (const sec of S) {
    const d = sec.lessons.filter(l => p.done[l.id]).length, n = sec.lessons.length;
    h += `<h3 class="sec"><span>${sec.id === "letters" ? "🔤" : "📝"} ${esc(sec.title)}</span><small>${d} из ${n}</small></h3>
      <div class="pbar"><i style="width:${Math.round(d / n * 100)}%"></i></div>`;
    for (const l of sec.lessons) {
      const b = best(p, l.id); const t = l.targetSeconds;
      const hit = b != null && t && b <= t * 1000;
      const num = sec.id === "letters" ? +l.id.slice(1) : +l.id;
      h += `<a class="card lesson ${p.done[l.id] ? "done" : ""}" href="${href(sec, l.id)}">
        <div class="num">${p.done[l.id] ? "✓" : num}</div>
        <div><div class="t">${rich(l.title)}</div><div class="s">${sec.id === "letters" ? rich(l.subtitle || "") + " · " : ""}${LEVELS[l.level] || ""}${l.count ? " · " + l.count : ""}${t ? " · цель " + t + " с" : ""}</div></div>
        <div class="best">${b != null ? (hit ? "🎯 " : "⏱ ") + fmt(b) : ""}</div></a>`;
    }
  }
  h += `<p class="foot"><b>${OWNER}</b><br>Текст: мусхаф (усмани) через api.quran.com · Звук слов: quran.com · Аяты: Мишари аль-Афаси (everyayah.com) · Зикры и дуа: «Крепость мусульманина», звук hisnmuslim.com<br>Произношение и таджвид — с устазом. Здесь тренируем беглость.</p>`;
  $app.innerHTML = h; renderStreak(); window.scrollTo(0, 0);
}

// ---------- урок ----------
let state = null, timerId = null;
async function lesson(id) {
  INDEX = INDEX || await getJSON("lessons/index.json");
  const f = findLesson(id); if (!f) throw new Error("Урок " + id + " не найден");
  const les = await getJSON(lessonUrl(f.sec, id));
  les._sec = f.sec;
  state = {les, step: 1, order: les.items.map((_, i) => i), t0: 0, result: null};
  drawLesson(); window.scrollTo(0, 0);
}
function shuffle(a) { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }

const INSTR = {
  1: "Круг 1 — с подсказкой. Читайте вслух каждое слово. Не уверены — нажмите на слово и послушайте.",
  2: "Круг 2 — сами. Прочитайте всё вслух ещё раз, не слушая. Старайтесь не останавливаться внутри слова.",
  3: "Круг 3 — на время. Слова перемешаются. Нажмите «Старт», прочитайте всё вслух и сразу нажмите «Готово».",
  a1: "Круг 1 — с подсказкой. Читайте каждый аят по словам (нажмите на слово — услышите его), затем целиком. Можно послушать весь аят.",
  a3: "Круг 3 — на время. Нажмите «Старт», прочитайте все аяты вслух подряд и сразу нажмите «Готово».",
  l1: "Круг 1 — с подсказкой. Называйте вслух каждую букву (или слог), справа налево. Под каждой — подсказка.",
  l2: "Круг 2 — сами. Подсказки те же, но старайтесь не смотреть на них — называйте сразу.",
  l3: "Круг 3 — на время. Порядок перемешается, подсказки исчезнут. «Старт» — назовите всё вслух — «Готово».",
};
function itemHTML(it, i, tr) {
  if (it.type === "ayah") {
    const n = it.key.split(":")[1];
    return `<div class="w ayah" data-i="${i}">
      <div class="full ar">${esc(it.ar)} <span class="muted">﴿${(+n).toLocaleString("ar-EG")}﴾</span></div>
      <div class="chips">${it.words.map((w, j) => `<span class="chip ar" data-w="${j}">${esc(w.ar)}</span>`).join("")}</div>
      <div class="bar"><span>Сура ${it.key}${tr ? " · " + esc(it.words.map(w => w.translit || "").join(" ")) : ""}</span><button data-full="1">▶ Аят целиком</button></div></div>`;
  }
  if (it.type === "forms") {
    return `<div class="w forms" data-i="${i}"><div class="fr">${it.forms.map(f => `<span class="ar">${esc(f)}</span>`).join("")}</div><div class="tr">${tr ? esc(it.name) + (it.hint ? ` <small>(${esc(it.hint)})</small>` : "") : ""}</div></div>`;
  }
  if (it.type === "letter") return `<div class="w lt1" data-i="${i}"><div class="ar">${esc(it.ar)}</div><div class="tr">${tr ? esc(it.name) : ""}</div></div>`;
  return `<div class="w" data-i="${i}"><div class="ar">${esc(it.ar)}</div><div class="tr">${tr && it.translit ? esc(it.translit) : ""}</div></div>`;
}
function drawLesson() {
  const {les, step} = state; const p = load();
  const b = best(p, les.id); const tgt = les.targetSeconds;
  const timing = step === 3 && state.t0 && !state.result;
  let h = `<a class="back" href="#/">‹ Все уроки</a>
    <div class="muted" style="font-size:14px">${les._sec.id === "letters" ? "Буквы · урок " + (+les.id.slice(1)) : "Урок " + (+les.id)}${les.level ? " · " + (LEVELS[les.level] || "") : ""}${tgt ? " · цель " + tgt + " с" : ""}</div>
    <h1 class="lt">${rich(les.title)}</h1><div class="muted">${rich(les.subtitle || "")}</div>
    ${les.tip ? `<div class="tip">💡 ${rich(les.tip)}</div>` : ""}
    <div class="steps">${[1, 2, 3].map(s => `<div class="${s === step ? "on" : s < step ? "ok" : ""}">${s < step ? "✓ " : ""}${["", "С подсказкой", "Сам", "На время"][s]}</div>`).join("")}</div>`;
  if (state.result) {
    const ms = state.result, ok = tgt && ms <= tgt * 1000;
    const runs = (p.runs[les.id] || []).slice(-12);
    const mx = Math.max(...runs.map(r => r.ms));
    h += `<section class="card result">
      <div class="muted">Ваше время</div><div class="big">${fmt(ms)}</div>
      ${tgt ? `<div class="cmp">${ok ? "🎯 Цель " + tgt + " с выполнена!" : "Цель: " + tgt + " с — осталось ускориться на " + fmt(ms - tgt * 1000)}</div>` : ""}
      <div class="cmp">Лучшее: ${fmt(b)} · первая попытка: ${fmt(p.runs[les.id][0].ms)} · попыток: ${p.runs[les.id].length}</div>
      ${runs.length > 1 ? `<div class="hist" title="последние попытки">${runs.map(r => `<span style="height:${Math.max(8, Math.round(r.ms / mx * 60))}px"></span>`).join("")}</div>` : ""}
      <div class="row"><button class="btn outline" id="again">↻ Ещё раз</button>
      <button class="btn" id="done">${p.done[les.id] ? "✓ Пройден" : "✓ Урок пройден"}</button></div></section>`;
  } else {
    h += `<p class="instr">${(les._sec.id === "letters" && INSTR["l" + step]) || (les.items.some(x => x.type === "ayah") && INSTR["a" + step]) || INSTR[step]}</p>
      ${les.showHints ? "" : `<label class="toggle"><input type="checkbox" id="tr" ${p.translit ? "checked" : ""} ${step === 3 ? "disabled" : ""}> Показывать транскрипцию (латиницей)</label>`}`;
  }
  const tr = (les.showHints || p.translit) && step !== 3;
  const isLetters = les.items.every(x => x.type === "letter");
  h += `<div class="grid ${isLetters ? "g3" : ""} ${step === 3 ? "timing" : ""}">${state.order.map(i => itemHTML(les.items[i], i, tr)).join("")}</div>`;
  $app.innerHTML = h;

  // нижняя панель
  let dock = document.querySelector(".dock"); if (!dock) { dock = document.createElement("div"); dock.className = "dock"; document.body.appendChild(dock); }
  if (state.result) dock.innerHTML = `<div class="in"><a class="btn light" href="#/">На главную</a></div>`;
  else if (step < 3) dock.innerHTML = `<div class="in"><button class="btn" id="next">Прочитал(а) ✓ — дальше</button></div>`;
  else if (!timing) dock.innerHTML = `<div class="in">${b != null ? `<div class="muted center" style="font-size:14px;margin-bottom:6px">Лучшее время: ${fmt(b)}${tgt ? " · цель " + tgt + " с" : ""}</div>` : (tgt ? `<div class="muted center" style="font-size:14px;margin-bottom:6px">Цель: успеть за ${tgt} с</div>` : "")}<button class="btn gold" id="start">▶ Старт</button></div>`;
  else dock.innerHTML = `<div class="in"><div class="timer" id="tm">0,0 с</div><button class="btn" id="stop">⏹ Готово</button></div>`;

  fitDock();
  // события
  $app.querySelectorAll(".w").forEach(el => el.addEventListener("click", ev => {
    if (state.step === 3 && state.t0 && !state.result) return; // во время замера без подсказок
    const it = les.items[+el.dataset.i];
    if (it.type === "ayah") {
      const chip = ev.target.closest(".chip");
      if (chip) return play(it.words[+chip.dataset.w].audio, chip);
      if (ev.target.closest("[data-full]")) return play(it.audio, el);
      return;
    }
    play(it.audio, el);
  }));
  const on = (id, f) => { const e = document.getElementById(id); if (e) e.onclick = f; };
  on("tr", () => { const q = load(); q.translit = document.getElementById("tr").checked; save(q); drawLesson(); });
  on("next", () => { state.step++; if (state.step === 3) { const words = state.order.filter(i => les.items[i].type !== "ayah"); if (words.length === state.order.length) shuffle(state.order); } drawLesson(); window.scrollTo(0, 0); });
  on("start", () => { audio.pause(); state.t0 = performance.now(); drawLesson(); window.scrollTo(0, 0); tick(); });
  on("stop", () => {
    const ms = Math.round(performance.now() - state.t0); clearInterval(timerId);
    const q = load(); (q.runs[les.id] = q.runs[les.id] || []).push({ms, date: today()}); markDay(q); save(q);
    state.result = ms; drawLesson(); renderStreak(); window.scrollTo(0, 0);
  });
  on("again", () => { state.result = null; state.t0 = 0; shuffle(state.order); drawLesson(); window.scrollTo(0, 0); });
  on("done", () => { const q = load(); q.done[les.id] = q.done[les.id] || today(); markDay(q); save(q); location.hash = "#/"; });
}
// нижняя панель не должна закрывать последние слова: отступ снизу = высота панели
const dockObs = window.ResizeObserver ? new ResizeObserver(() => fitDock()) : null;
function fitDock() {
  const d = document.querySelector(".dock");
  const h = d ? Math.ceil(d.getBoundingClientRect().height) : 0;
  document.documentElement.style.setProperty("--dock", h + "px");
  if (d && dockObs && !d._obs) { dockObs.observe(d); d._obs = true; }
}
function tick() {
  clearInterval(timerId);
  timerId = setInterval(() => { const e = document.getElementById("tm"); if (!e) return clearInterval(timerId); e.textContent = fmt(performance.now() - state.t0); }, 100);
}

// ---------- маршруты ----------
function route() {
  clearInterval(timerId); audio.pause(); $app.onclick = null;
  const d = document.querySelector(".dock"); if (d) d.remove(); fitDock();
  const m = location.hash.match(/^#\/(?:lesson|letters)\/(\w+)/);
  const pm = location.hash.match(/^#\/page\/(\d+)/);
  const am = location.hash.match(/^#\/adhkar(?:\/(evening|salah))?$/), du = location.hash.match(/^#\/dua(?:\/(\w+))?$/);
  (pm ? pageView(+pm[1]) : am ? adhkarView(am[1] || "morning") : du ? duaView(du[1]) : location.hash === "#/pages" ? pagePicker() : m ? lesson(m[1]) : home()).catch(e => { $app.innerHTML = `<p class="card">Не удалось загрузить урок. Проверьте интернет.<br><small class="muted">${esc(e.message)}</small></p>`; });
}
window.addEventListener("hashchange", route);
renderStreak();
window.addEventListener("DOMContentLoaded", route);
