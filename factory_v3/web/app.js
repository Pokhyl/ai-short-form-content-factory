"use strict";
const base = "/factory-v3";
const $ = id => document.getElementById(id);
let selected = null, detail = null, pending = null, pollTimer = null;
const labels = {preparing:"Подготовка: факты и фотографии",prepared:"Подготовка завершена",voice_running:"Создание озвучки",voice_ready:"Озвучка готова",align_running:"Синхронизация сцен",align_ready:"Сцены синхронизированы",render_running:"Сборка видео",render_ready:"Видео собрано, проверка качества",qa_running:"Проверка качества",qa_pass:"Видео прошло проверку качества",failed:"Задание остановлено",unknown:"Результат внешнего запроса не подтверждён; повтор заблокирован"};
async function api(path, options = {}) {
  const response = await fetch(base + path, {credentials:"same-origin",...options});
  const body = await response.json();
  if (!response.ok) {
    if (response.status === 401) { $("login").hidden = false; $("workspace").hidden = true; }
    throw new Error(body.error || "Ошибка запроса");
  }
  return body;
}
const post = (path, data) => api(path, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
const report = error => { $("message").textContent = error.message; };
function link(url, text) {
  const a = document.createElement("a");
  try { const u = new URL(url); if (!["http:","https:"].includes(u.protocol) || u.username || u.password) throw new Error(); a.href = u.href; }
  catch { a.textContent = text; return a; }
  a.textContent = text; a.target = "_blank"; a.rel = "noopener noreferrer"; return a;
}
async function history() {
  const rows = await api("/api/requests");
  $("history").replaceChildren();
  for (const row of rows) {
    const button = document.createElement("button");
    button.textContent = row.request.topic + " · " + row.request.language.toUpperCase() + " · " + row.request.seconds + " с · " + (labels[row.status] || row.status);
    button.onclick = () => show(row.id).catch(report);
    $("history").append(button);
  }
  return rows;
}
async function show(id) {
  clearTimeout(pollTimer); pollTimer = null;
  selected = id; localStorage.setItem("factoryV3Last", id);
  const response = await api("/api/requests/" + id);
  if (selected !== id) return;
  detail = response;
  $("result").hidden = false; $("result-title").textContent = detail.request.topic;
  $("status").textContent = (labels[detail.status] || detail.status) + " · " + (detail.request.visual_validation_mode === "metadata" ? "Стандартный режим" : "Gemini Vision") + (detail.error_code ? " · " + detail.error_code : "") + (detail.photo_count ? " · " + detail.photo_count + " фото" : "") + (detail.actual_duration_ms ? " · " + (detail.actual_duration_ms / 1000) + " с" : "");
  $("script").textContent = detail.script || "Текст появится после проверки фактов и фотографий.";
  const ready = detail.machine_pass === true;
  $("video").hidden = !ready; $("download").hidden = !ready; $("review").hidden = !ready || !!detail.review;
  if (ready) {
    const url = base + "/video/" + id;
    if ($("video").getAttribute("src") !== url) $("video").src = url;
    $("download").href = url;
  } else { $("video").removeAttribute("src"); $("video").load(); }
  $("decision").textContent = detail.review ? (detail.review.decision === "accepted" ? "Вы приняли это видео." : "Вы отклонили это видео.") + (detail.review.comment ? " " + detail.review.comment : "") : (ready ? "Ожидает вашего просмотра и решения." : "");
  $("identity").textContent = "ID: " + id + " · версия: " + detail.source_revision + (detail.video_sha256 ? " · SHA-256: " + detail.video_sha256 : "");
  $("scenes").replaceChildren();
  for (const scene of detail.scenes || []) {
    const item = document.createElement("div"); item.className = "scene";
    const photo = document.createElement("img"); photo.src = base + "/photo/" + id + "/" + encodeURIComponent(scene.id); photo.alt = scene.narration || "Фотография " + scene.id; photo.loading = "lazy";
    const text = document.createElement("div"), caption = document.createElement("p");
    caption.textContent = scene.narration; text.append(caption);
    const author = document.createElement("p"); author.className = "note"; author.textContent = "Автор: " + scene.asset.author + (scene.asset.attribution ? " · " + scene.asset.attribution : ""); text.append(author);
    text.append(link(scene.asset.source_url,"Фото"),document.createTextNode(" · "),link(scene.asset.license_url,scene.asset.license + (scene.asset.license_version ? " " + scene.asset.license_version : "")));
    item.append(photo,text); $("scenes").append(item);
  }
  if (!["qa_pass", "failed", "unknown"].includes(detail.status)) {
    pollTimer = setTimeout(() => { if (selected === id) Promise.all([history(), show(id)]).catch(report); }, 5000);
  }
  $("sources").replaceChildren();
  for (const source of detail.sources || []) { const item = document.createElement("div"); item.className = "source"; item.append(link(source.url,source.title || source.url)); $("sources").append(item); }
}
async function open() {
  await api("/api/session"); $("login").hidden = true; $("workspace").hidden = false;
  const rows = await history(); const requested = new URLSearchParams(location.search).get("request");
  const last = requested && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(requested) ? requested : localStorage.getItem("factoryV3Last") || (rows[0] && rows[0].id); if (last) await show(last);
}
$("login-form").onsubmit = async event => {
  event.preventDefault(); $("message").textContent = "";
  try { await post("/api/session",{token:$("access").value}); $("access").value = ""; await open(); } catch(error) { report(error); }
};
$("request-form").onsubmit = async event => {
  event.preventDefault(); $("message").textContent = ""; $("create").disabled = true;
  const fields = {topic:$("topic").value.trim(),language:$("language").value,seconds:Number($("seconds").value),visual_validation_mode:$("visualValidationMode").value};
  if (!pending || JSON.stringify(pending.fields) !== JSON.stringify(fields)) pending = {id:crypto.randomUUID(),fields};
  try {
    const result = await post("/api/requests",{request_id:pending.id,...fields});
    pending = null; await history(); await show(result.id);
  } catch(error) { report(error); }
  finally { $("create").disabled = false; }
};
$("refresh").onclick = () => Promise.all([history(),show(selected)]).catch(report);
async function decide(decision) {
  if (!detail || !detail.video_sha256) return;
  $("accept").disabled = $("reject").disabled = true;
  try { await post("/api/requests/" + selected + "/review",{decision,video_sha256:detail.video_sha256,comment:$("comment").value}); await show(selected); }
  catch(error) { report(error); }
  finally { $("accept").disabled = $("reject").disabled = false; }
}
$("accept").onclick = () => decide("accepted");
$("reject").onclick = () => decide("rejected");
open().catch(error => { if (error.message !== "authentication_required") report(error); });
