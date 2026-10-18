"use strict";
// Зикры (азкары) по «Крепости мусульманина» со счётчиками: утро, вечер, после намаза.
// Утро и вечер сбрасываются каждый новый день; «после намаза» — через час без нажатий (следующий намаз).
const DK_SETS = {
  morning: {key: "qr.adhkar.v1", url: "adhkar/morning.json", hash: "#/adhkar", icon: "🌅", title: "Утренние зикры", word: "утренних",
    intro: "Читаются после утреннего намаза (фаджр); лучшее время — до восхода солнца."},
  evening: {key: "qr.adhkar.evening.v1", url: "adhkar/evening.json", hash: "#/adhkar/evening", icon: "🌇", title: "Вечерние зикры", word: "вечерних",
    intro: "Читаются после послеполуденного намаза (аср) до заката, а также после заката."},
  salah: {key: "qr.adhkar.salah.v1", url: "adhkar/salah.json", hash: "#/adhkar/salah", icon: "🕌", title: "Зикры после намаза", word: "",
    intro: "После каждого обязательного намаза, сразу после саляма. Счётчик сам обнуляется через час — к следующему намазу.", idle: 60 * 60 * 1000}
};
let DKN = "morning", DK = null, DKS = null; const DKC = {}; const dkOpen = new Set();
const dkSet = () => DK_SETS[DKN];

function dkLoad(name) {
  const S = DK_SETS[name || DKN];
  let s; try { s = JSON.parse(localStorage.getItem(S.key) || "{}"); } catch (e) { s = {}; }
  s = Object.assign({date: today(), c: {}, big: {}, tr: true, ru: true, days: [], t: 0}, s);
  if (s.date !== today()) { s.date = today(); s.c = {}; } // новый день — всё заново
  if (S.idle && s.t && Date.now() - s.t > S.idle) { s.c = {}; s.t = 0; } // следующий намаз
  return s;
}
function dkSave() { localStorage.setItem(dkSet().key, JSON.stringify(DKS)); }
async function dkUse(name) { DKN = name; DK = DKC[name] = DKC[name] || await getJSON(DK_SETS[name].url); DKS = dkLoad(); }
function dkTarget(it) { return it.alt && DKS.big[it.id] ? it.alt : it.count; }
function dkLeft(it) { return Math.max(0, dkTarget(it) - (DKS.c[it.id] || 0)); }
function dkDone(it) { return dkLeft(it) === 0; }
function dkStats() { const n = DK.items.filter(dkDone).length; return {n, all: DK.items.length}; }
function dkCur() { return DK.items.find(it => !dkDone(it)) || null; }
function dkStreak(s) {
  const set = new Set(s.days); let n = 0; const d = new Date();
  if (!set.has(today(d))) d.setDate(d.getDate() - 1);
  while (set.has(today(d))) { n++; d.setDate(d.getDate() - 1); }
  return n;
}
function buzz(p) { try { if (navigator.vibrate) navigator.vibrate(p); } catch (e) {} }
function times(n) { return n + " " + plural(n, "раз", "раза", "раз"); }

// ---------- карточка на главной: утром — утренние, после 14:00 — вечерние ----------
async function adhkarCard() {
  const name = new Date().getHours() < 14 ? "morning" : "evening";
  await dkUse(name); const S = dkSet();
  const {n, all} = dkStats(); const s = dkStreak(DKS);
  const btn = n >= all
    ? `<div class="okday">✓ Сегодня ${S.word} зикры прочитаны. Барака-Ллаху фик!</div>`
    : `<a class="btn big gold" href="${S.hash}">🤲 ${n ? "Продолжить: " + n + " из " + all : "Читать " + S.title.toLowerCase()}</a>`;
  return `<section class="card mcard dkcard">
    <h3 class="sec" style="margin:0 0 6px"><span>${S.icon} ${S.title}</span><small>${s ? "🔥 " + s + " " + plural(s, "день", "дня", "дней") : ""}</small></h3>
    <div class="muted" style="font-size:14px">${name === "morning" ? "После утреннего намаза" : "После асра и вечером"} · ${all} зикров из «Крепости мусульманина» со счётчиком</div>
    <div class="pbar" style="margin:8px 0 12px"><i style="width:${Math.round(n / all * 100)}%"></i></div>
    ${btn}
    <div class="row dksets" style="margin-top:10px">${["morning", "evening", "salah"].map(k => `<a class="btn light2" href="${DK_SETS[k].hash}">${DK_SETS[k].icon} ${{morning: "Утро", evening: "Вечер", salah: "После намаза"}[k]}</a>`).join("")}</div>
  </section>`;
}

// ---------- экран зикров ----------
async function adhkarView(name) {
  await dkUse(name || "morning"); dkOpen.clear();
  drawAdhkar(); window.scrollTo(0, 0);
}
function dkArabic(it) {
  if (!it.ayat) return `<div class="dkar ar">${esc(it.ar).replace(/\n+/g, "<br>")}</div>`;
  return quranHTML(it);
}
function quranHTML(it) {
  let h = it.pre ? `<div class="dkpre ar">${esc(it.pre)}</div>` : "";
  let run = [];
  const flush = () => { if (run.length) h += `<div class="dkar ar">${run.join(" ")}</div>`; run = []; };
  for (const a of it.ayat) {
    if (a.k === "1:1") { flush(); h += `<div class="dkbasm ar">${esc(a.ar)}</div>`; continue; }
    run.push(`${esc(a.ar)} <span class="dkay">﴿${(+a.k.split(":")[1]).toLocaleString("ar-EG")}﴾</span>`);
  }
  flush(); return h;
}
function dkCardHTML(it, i) {
  const left = dkLeft(it), tgt = dkTarget(it), done = left === 0, cur = DKS && dkCur() === it;
  const open = !done || dkOpen.has(it.id);
  const pct = Math.round((tgt - left) / tgt * 100);
  return `<section class="card dk ${done ? "done" : ""} ${cur ? "cur" : ""}" id="dk-${it.id}" data-id="${it.id}">
    <div class="dkh" data-act="head"><span class="num">${done ? "✓" : i + 1}</span><span class="dkt">${rich(it.title)}</span><span class="dkx">${done ? (open ? "▴" : "▾") : "×" + tgt}</span></div>
    ${open ? `<div class="dkbody">
      ${dkArabic(it)}
      ${DKS.tr ? `<div class="dktr">${esc(it.translit).replace(/\n/g, "<br>")}</div>` : ""}
      ${DKS.ru ? `<div class="dkru">${esc(it.ru).replace(/\n/g, "<br>")}${it.ruSrc ? ` <small>(${esc(it.ruSrc)})</small>` : ""}</div>` : ""}
      <div class="tip dkv">✨ ${esc(it.virtue)}</div>
      <div class="dksrc">📚 ${esc(it.src)}${it.n ? ` · «Крепость мусульманина» № ${it.n}` : ""}</div>
      <div class="dkctl">
        ${it.audio ? `<button class="sbtn" data-act="play">▶ Слушать</button>` : `<span class="muted" style="font-size:13px">без аудиозаписи</span>`}
        ${it.alt ? `<span class="seg"><button data-act="cnt" data-v="0" class="${DKS.big[it.id] ? "" : "on"}">${it.count}</button><button data-act="cnt" data-v="1" class="${DKS.big[it.id] ? "on" : ""}">${it.alt}</button></span>` : ""}
        ${(DKS.c[it.id] || 0) > 0 ? `<button class="undo" data-act="undo" title="Отменить последнее нажатие">↶ −1</button>` : ""}
      </div>
    </div>` : ""}
    ${done ? "" : `<button class="dkbtn" data-act="tap"><i style="width:${pct}%"></i><span><b>${left}</b> ${tgt > 1 ? "осталось из " + tgt + " · нажмите после каждого раза" : "Прочитал(а) ✓"}</span></button>`}
  </section>`;
}
function drawAdhkar() {
  const {n, all} = dkStats();
  let h = `<a class="back" href="#/">‹ На главную</a>
    <div class="seg dkseg">${Object.entries(DK_SETS).map(([k, S]) => `<a href="${S.hash}" class="${k === DKN ? "on" : ""}">${S.icon} ${{morning: "Утро", evening: "Вечер", salah: "После намаза"}[k]}</a>`).join("")}</div>
    <h1 class="lt">${dkSet().icon} ${dkSet().title}</h1>
    <div class="muted" style="font-size:14px">${dkSet().intro} По книге «Крепость мусульманина» (Хисн аль-муслим).</div>
    <section class="card dkprog" id="dkprog">${dkProgHTML(n, all)}</section>
    <div class="ctrls">
      <label class="toggle"><input type="checkbox" id="dktr" ${DKS.tr ? "checked" : ""}> Транскрипция</label>
      <label class="toggle"><input type="checkbox" id="dkru" ${DKS.ru ? "checked" : ""}> Перевод</label>
      <button class="sbtn light" id="dkreset">↺ Сбросить</button>
    </div>
    <div id="dklist">${DK.items.map(dkCardHTML).join("")}</div>
    <p class="foot">Арабский текст: «Хисн аль-муслим» (github.com/asellam/HisnElMuslim, сверено с Seen-Arabic/Morning-And-Evening-Adhkar-DB и hisnmuslim.com); аяты — api.quran.com (письмо усмани), перевод аятов — Э. Кулиев.<br>Перевод и транскрипция дуа — русское издание «Крепости мусульманина». Звук: hisnmuslim.com.<br>${dkSet().idle ? "Счётчик обнуляется через час без нажатий — к следующему намазу." : "Счётчики обнуляются каждый новый день."}</p>`;
  $app.innerHTML = h;
  document.documentElement.style.setProperty("--toph", document.querySelector(".top").offsetHeight + "px");
  dkDock();
  const chk = (id, key) => { document.getElementById(id).onchange = e => { DKS[key] = e.target.checked; dkSave(); drawAdhkar(); }; };
  chk("dktr", "tr"); chk("dkru", "ru");
  document.getElementById("dkreset").onclick = () => {
    if (!confirm("Сбросить все счётчики?")) return;
    DKS.c = {}; DKS.days = DKS.days.filter(d => d !== today()); dkSave(); dkOpen.clear(); drawAdhkar(); window.scrollTo(0, 0);
  };
  document.getElementById("dklist").onclick = dkClick;
}
function dkProgHTML(n, all) {
  return n >= all
    ? `<div class="okday" style="margin:0">✓ Все ${all} ${dkSet().word ? dkSet().word + " " : ""}зикров прочитаны. Да примет Аллах!</div>`
    : `<div class="phead"><b>Прочитано ${n} из ${all}</b><span class="muted">${Math.round(n / all * 100)}%</span></div><div class="pbar" style="margin:8px 0 0"><i style="width:${Math.round(n / all * 100)}%"></i></div>`;
}
function dkDock() {
  let dock = document.querySelector(".dock"); if (!dock) { dock = document.createElement("div"); dock.className = "dock"; document.body.appendChild(dock); }
  const it = dkCur();
  if (!it) dock.innerHTML = `<div class="in"><a class="btn" href="#/">✓ Готово — на главную</a></div>`;
  else {
    const i = DK.items.indexOf(it), left = dkLeft(it), tgt = dkTarget(it);
    dock.innerHTML = `<div class="in"><div class="dkdk muted"><span>№${i + 1} · ${esc(it.title)}</span><b>${tgt > 1 ? left + " / " + tgt : ""}</b></div>
      <div class="row"><button class="btn outline" id="dkgo" style="flex:0 0 30%">К тексту</button><button class="btn" id="dktap">${tgt > 1 ? "＋1 · осталось " + left : "Прочитал(а) ✓"}</button></div></div>`;
    document.getElementById("dktap").onclick = () => dkTap(it);
    document.getElementById("dkgo").onclick = () => dkScrollTo(it);
  }
  fitDock();
}
function dkScrollTo(it) {
  const el = document.getElementById("dk-" + it.id); if (!el) return;
  const top = el.getBoundingClientRect().top + window.scrollY - document.querySelector(".top").offsetHeight - 8;
  window.scrollTo({top, behavior: "smooth"});
}
function dkRefresh(ids) {
  for (const id of ids) {
    const it = DK.items.find(x => x.id === id), el = document.getElementById("dk-" + id);
    if (it && el) el.outerHTML = dkCardHTML(it, DK.items.indexOf(it));
  }
  const {n, all} = dkStats(); document.getElementById("dkprog").innerHTML = dkProgHTML(n, all);
  dkDock();
}
function dkTap(it) {
  const fresh = dkLoad(); if (fresh.date !== DKS.date || Object.keys(fresh.c).length < Object.keys(DKS.c).length) { DKS = fresh; drawAdhkar(); return; }
  if (dkDone(it)) return;
  const prevCur = dkCur();
  DKS.c[it.id] = (DKS.c[it.id] || 0) + 1; DKS.t = Date.now();
  const fin = dkDone(it);
  let all = false;
  if (fin && DK.items.every(dkDone) && !DKS.days.includes(today())) { DKS.days.push(today()); all = true; }
  dkSave(); buzz(fin ? [35, 50, 35] : 12);
  const next = dkCur();
  dkRefresh([...new Set([it.id, prevCur && prevCur.id, next && next.id].filter(Boolean))]);
  if (fin && next) setTimeout(() => dkScrollTo(next), 250);
  if (all) setTimeout(() => window.scrollTo({top: 0, behavior: "smooth"}), 250);
}
function dkClick(ev) {
  const b = ev.target.closest("[data-act]"); if (!b) return;
  const card = b.closest(".dk"); const it = DK.items.find(x => x.id === card.dataset.id);
  const act = b.dataset.act;
  if (act === "tap") return dkTap(it);
  if (act === "play") { const u = it.alt && DKS.big[it.id] ? it.altAudio : it.audio; if (audio.src === u && !audio.paused) { audio.pause(); b.classList.remove("playing"); return; } return play(u, b); }
  if (act === "undo") { const prevCur = dkCur(); DKS.c[it.id] = Math.max(0, (DKS.c[it.id] || 0) - 1); DKS.days = DKS.days.filter(d => d !== today()) ; dkSave(); dkOpen.add(it.id); return dkRefresh([...new Set([it.id, prevCur && prevCur.id].filter(Boolean))]); }
  if (act === "cnt") { DKS.big[it.id] = b.dataset.v === "1"; dkSave(); return dkRefresh([it.id]); }
  if (act === "head" && dkDone(it)) { dkOpen.has(it.id) ? dkOpen.delete(it.id) : dkOpen.add(it.id); dkRefresh([it.id]); }
}
// если приложение было открыто через полночь — при возвращении начинаем новый день
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState !== "visible" || !DKS) return;
  const fresh = dkLoad();
  if (fresh.date !== DKS.date || Object.keys(fresh.c).length < Object.keys(DKS.c).length) { DKS = fresh; if (location.hash.startsWith("#/adhkar")) drawAdhkar(); else if (!location.hash || location.hash === "#/") route(); }
});
