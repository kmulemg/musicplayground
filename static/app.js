const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

let currentSid = null;       // 当前结果列表 sid（搜索或歌单）
let currentKind = null;      // 'search' | 'playlist'
let config = null;
let logTimer = null;

function setStatus(sel, msg, isError) {
  const el = $(sel);
  el.textContent = msg || "";
  el.className = "status" + (isError ? " error" : "") + (msg && !isError ? " loading" : "");
  if (!msg) el.className = "status";
}

async function api(url, opts) {
  const res = await fetch(url, opts);
  return res.json();
}

async function restartServer() {
  if (!confirm("确定要重启服务吗？重启过程中页面会短暂不可用，完成后自动刷新。")) return;
  const btn = $("#restart-btn");
  const status = $("#restart-status");
  btn.disabled = true;
  btn.textContent = "重启中…";
  status.textContent = "";
  try {
    await fetch("/api/restart", { method: "POST" });
  } catch (e) {
    // 请求发出后服务可能立刻重启，忽略连接中断
  }
  // 轮询等待服务恢复，然后刷新页面
  const deadline = Date.now() + 30000;
  const poll = setInterval(async () => {
    if (Date.now() > deadline) {
      clearInterval(poll);
      btn.disabled = false;
      btn.textContent = "重启服务";
      status.textContent = "重启超时，请手动刷新页面。";
      return;
    }
    try {
      const res = await fetch("/api/config");
      if (res.ok) {
        clearInterval(poll);
        location.reload();
      }
    } catch (e) {
      // 服务尚未恢复，继续轮询
    }
  }, 1500);
}

async function shutdownServer() {
  if (!confirm("确定要终止服务吗？终止后服务将停止运行，请手动刷新页面。")) return;
  const btn = $("#shutdown-btn");
  const status = $("#restart-status");
  btn.disabled = true;
  btn.textContent = "终止中…";
  status.textContent = "";
  try {
    await fetch("/api/shutdown", { method: "POST" });
    status.textContent = "服务已终止，请关闭页面或手动刷新。";
  } catch (e) {
    // 请求发出后服务可能立刻关闭，忽略连接中断
    status.textContent = "服务已终止，请关闭页面或手动刷新。";
  }
}

function fmtSize(bytes) {
  if (!bytes) return "";
  if (bytes > 1024 * 1024 * 1024) return (bytes / 1024 / 1024 / 1024).toFixed(2) + "GB";
  if (bytes > 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + "MB";
  return (bytes / 1024).toFixed(1) + "KB";
}

function fmtTime(ts) {
  if (!ts) return "";
  const d = new Date(ts * 1000);
  return d.toLocaleString();
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

const SOURCE_NAMES = {
  "AppleMusicClient": "Apple Music",
  "NeteaseMusicClient": "网易云音乐",
  "QQMusicClient": "QQ音乐",
  "KugouMusicClient": "酷狗音乐",
  "KuwoMusicClient": "酷我音乐",
  "MiguMusicClient": "咪咕音乐",
  "QianqianMusicClient": "千千音乐",
  "BilibiliMusicClient": "哔哩哔哩",
  "FiveSingMusicClient": "5sing原创音乐",
  "SodaMusicClient": "Soda Music",
  "StreetVoiceMusicClient": "街声",
  "BodianMusicClient": "波点音乐",
  "MOOVMusicClient": "MOOV",
  "JooxMusicClient": "JOOX",
  "YouTubeMusicClient": "YouTube Music",
  "SpotifyMusicClient": "Spotify",
  "DeezerMusicClient": "Deezer",
  "QobuzMusicClient": "Qobuz",
  "TIDALMusicClient": "TIDAL",
  "SoundCloudMusicClient": "SoundCloud",
  "SunoMusicClient": "Suno",
  "AudiusMusicClient": "Audius",
  "JamendoMusicClient": "Jamendo",
  "FMAMusicClient": "Free Music Archive",
  "JioSaavnMusicClient": "JioSaavn",
  "OpenGameArtMusicClient": "OpenGameArt",
  "WikimediaCommonsMusicClient": "Wikimedia Commons",
  "CCMixterMusicClient": "ccMixter",
  "XimalayaMusicClient": "喜马拉雅",
  "LizhiMusicClient": "荔枝FM",
  "QingtingMusicClient": "蜻蜓FM",
  "LRTSMusicClient": "懒人听书",
  "ITunesMusicClient": "iTunes",
  "MP3JuiceMusicClient": "MP3Juice",
  "TuneHubMusicClient": "TuneHub",
  "GDStudioMusicClient": "GD Studio",
  "MyFreeMP3MusicClient": "MyFreeMP3",
  "JBSouMusicClient": "巨星搜",
  "XiaoBaiMusicClient": "小白音乐",
  "MituMusicClient": "咪兔音乐",
  "BuguyyMusicClient": "布谷YY",
  "GequbaoMusicClient": "歌曲宝",
  "YinyuedaoMusicClient": "音乐岛",
  "XiagebaMusicClient": "下歌吧",
  "FangpiMusicClient": "放屁网",
  "FiveSongMusicClient": "五首歌",
  "KKWSMusicClient": "KK音乐网",
  "GequhaiMusicClient": "歌曲海",
  "LivePOOMusicClient": "LivePOO",
  "HTQYYMusicClient": "好听音乐网",
  "TwoT58MusicClient": "58音乐",
  "ZhuolinMusicClient": "卓林音乐",
  "LiziYYMusicClient": "荔枝音乐",
  "MGMP3MusicClient": "MGMP3",
  "ITingWaMusicClient": "爱听哇",
  "SgogoMusicClient": "SGOGO",
  "XMFWAVMusicClient": "笑模音乐",
  "QuarkMusicClient": "夸克网盘",
};

function sourceName(source) {
  return SOURCE_NAMES[source] || (source || "").replace(/MusicClient$/, "").toUpperCase();
}

const COOKIE_CLASS_INFO = {
  none: { cls: "src-ok", label: "无需 Cookie，开箱即用" },
  needed: { cls: "src-cookie", label: "需平台登录/会员 Cookie，可下载高清 / 无损 / 已购买" },
  quark: { cls: "src-quark", label: "需夸克网盘 Cookie，可下载更高清文件" },
  preview: { cls: "src-preview", label: "不配 Cookie 仅可下载预览或无法下载" },
};

function sourceCookieInfo(source) {
  const cc = config.cookie_classes && config.cookie_classes[source];
  return COOKIE_CLASS_INFO[cc] || COOKIE_CLASS_INFO.none;
}

function sourceBadge(source) {
  return `<span class="badge">${escapeHtml(sourceName(source))}</span>`;
}

function disabledSourcesNote(disabled) {
  if (!disabled || !disabled.length) return "";
  const names = disabled.map(sourceName).join("、");
  return `提示：${names} 需配置「夸克网盘」Cookie 才能使用，当前已跳过（可在「设置 → Cookie 管理」底部录入后自动恢复）。`;
}

function renderSongs(bodySel, songs) {
  const tbody = $(bodySel);
  tbody.innerHTML = "";
  songs.forEach((s, i) => {
    const tr = document.createElement("tr");
    const previewCell = s.preview_url
      ? `<button class="preview-btn" data-preview="${escapeHtml(s.preview_url)}" data-name="${escapeHtml(s.song_name)}">▶ 试听</button>`
      : `<span class="muted">—</span>`;
    tr.innerHTML = `
      <td><input type="checkbox" class="row-check" data-idx="${i}"></td>
      <td>${i + 1}</td>
      <td class="song-title">${escapeHtml(s.song_name)}</td>
      <td>${escapeHtml(s.singers)}</td>
      <td>${escapeHtml(s.album)}</td>
      <td>${escapeHtml(s.duration)}</td>
      <td>${escapeHtml(s.file_size)}</td>
      <td>${sourceBadge(s.source)}</td>
      <td>${previewCell}</td>
    `;
    tbody.appendChild(tr);
  });
}

function refreshSelectionState() {
  const rows = $$(".row-check");
  const checked = Array.from(rows).filter((r) => r.checked);
  const prefix = currentKind === "playlist" ? "playlist" : "search";
  const disabled = checked.length === 0;
  $(`#${prefix}-download-best-btn`).disabled = disabled;
  $(`#${prefix}-download-aac-btn`).disabled = disabled;
  const countEl = currentKind === "playlist" ? "#playlist-count" : "#search-count";
  $(countEl).textContent = rows.length ? `共 ${rows.length} 首，已选 ${checked.length} 首` : "";
}

function bindCheckAll(checkSel, bodySel) {
  $(checkSel).addEventListener("change", (e) => {
    $$(`${bodySel} .row-check`).forEach((r) => { r.checked = e.target.checked; });
    refreshSelectionState();
  });
  $(bodySel).addEventListener("change", (e) => {
    if (e.target.classList.contains("row-check")) refreshSelectionState();
  });
}

async function doSearch() {
  const kw = $("#search-input").value.trim();
  if (!kw) return;
  setStatus("#search-status", "正在搜索…");
  $("#search-body").innerHTML = "";
  try {
    const data = await api("/api/search?keyword=" + encodeURIComponent(kw));
    if (!data.ok) throw new Error(data.error || "搜索失败");
    currentSid = data.sid;
    currentKind = "search";
    renderSongs("#search-body", data.songs);
    const note = disabledSourcesNote(data.disabled_sources);
    setStatus("#search-status", note);
    refreshSelectionState();
  } catch (err) {
    setStatus("#search-status", "搜索出错：" + err.message, true);
  }
}

async function doPlaylist() {
  const url = $("#playlist-input").value.trim();
  if (!url) return;
  setStatus("#playlist-status", "正在解析歌单…");
  $("#playlist-body").innerHTML = "";
  try {
    const data = await api("/api/playlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    if (!data.ok) throw new Error(data.error || "解析失败");
    currentSid = data.sid;
    currentKind = "playlist";
    renderSongs("#playlist-body", data.songs);
    if (!data.songs.length) {
      setStatus("#playlist-status", "歌单解析成功，但未获取到可下载的歌曲。请检查 Cookie 是否有效（media-user-token 可能已过期）。", true);
    } else {
      setStatus("#playlist-status", disabledSourcesNote(data.disabled_sources));
    }
    refreshSelectionState();
  } catch (err) {
    setStatus("#playlist-status", "解析出错：" + err.message, true);
  }
}

function getCheckedIds() {
  return Array.from($$(".row-check"))
    .filter((r) => r.checked)
    .map((r) => Number(r.dataset.idx));
}

async function doDownload(kind, mode) {
  if (!currentSid) return;
  const ids = getCheckedIds();
  if (!ids.length) return;
  const prefix = kind === "playlist" ? "playlist" : "search";
  const btn = $(`#${prefix}-download-${mode === "aac" ? "aac" : "best"}-btn`);
  const old = btn.innerHTML;
  btn.disabled = true;
  btn.textContent = "已提交…";
  try {
    const data = await api("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sid: currentSid, ids, mode }),
    });
    if (!data.ok) throw new Error(data.error);
    switchTab("downloads");
    loadJobs();
    loadFiles();
  } catch (err) {
    alert("提交下载失败：" + err.message);
  } finally {
    btn.innerHTML = old;
    refreshSelectionState();
  }
}

function switchTab(name) {
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  $$(".panel").forEach((p) => p.classList.toggle("active", p.id === "tab-" + name));
  localStorage.setItem("musicplayground_tab", name);
  if (name === "settings") loadDepsStatus();
}

async function loadConfig() {
  config = await api("/api/config");
  const br = await api("/api/browsers");
  config.browsers = br.browsers;
  const dom = await api("/api/domains");
  config.domains = dom.domains;
  const sel = $("#import-all-browser");
  sel.innerHTML = "";
  config.browsers.forEach((b) => {
    const opt = document.createElement("option");
    opt.value = b;
    opt.textContent = b;
    sel.appendChild(opt);
  });
  renderSources();
  renderCookieRows();
}

async function importAllCookies() {
  const browser = $("#import-all-browser").value;
  const btn = $("#import-all-btn");
  const status = $("#import-all-status");
  btn.disabled = true;
  btn.textContent = "导入中…";
  status.textContent = "";
  try {
    const res = await api("/api/cookies/import-all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ browser }),
    });
    if (!res.ok) throw new Error(res.error || "导入失败");
    const failed = [];
    let got = 0;
    for (const [src, val] of Object.entries(res.results)) {
      if (typeof val === "number") got += val;
      else failed.push(`${src}：${val}`);
    }
    const failedTip = failed.length ? `；失败：${failed.join("；")}` : "";
    status.textContent = `已从 ${browser} 导入并保存 ${got} 个 Cookie（来源 ${Object.keys(res.results).length} 个）${failedTip}`;
    await loadConfig();
  } catch (err) {
    status.textContent = "导入失败：" + err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "一键导入并保存全部";
  }
}

let updatePollTimer = null;

async function startUpdate(kind) {
  const label = kind === "musicdl" ? "更新 musicdl" : "安装/更新依赖";
  const res = await api("/api/update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kind }),
  });
  if (!res.ok) {
    $("#update-status").textContent = "启动失败：" + (res.error || "");
    return;
  }
  const box = $("#update-output");
  box.classList.remove("hidden");
  box.textContent = "正在执行 " + label + " …";
  $("#update-status").textContent = "正在执行" + label + "，请稍候…";
  $("#update-musicdl-btn").disabled = true;
  $("#update-deps-btn").disabled = true;
  updatePollTimer = setInterval(pollUpdate, 1500);
}

async function pollUpdate() {
  const res = await api("/api/update/status");
  if (!res.ok) return;
  const box = $("#update-output");
  if (res.output && res.output.length) {
    box.textContent = res.output.join("\n");
    box.scrollTop = box.scrollHeight;
  }
  if (res.running) return;
  if (updatePollTimer) {
    clearInterval(updatePollTimer);
    updatePollTimer = null;
  }
  $("#update-musicdl-btn").disabled = false;
  $("#update-deps-btn").disabled = false;
  const v = res.versions || {};
  const verText = `当前版本 musicdl ${v.musicdl || "?"} · flask ${v.flask || "?"} · rookiepy ${v.rookiepy || "?"}`;
  $("#update-status").textContent = res.result_ok ? `已完成。${verText}` : `执行失败，详见输出。${verText}`;
  await loadDepsStatus();
}

function depsStatusBadge(pkg) {
  if (!pkg.installed) return `<span class="deps-missing">未安装</span>`;
  if (pkg.latest && pkg.latest !== pkg.installed) return `<span class="deps-warn">可更新 → ${escapeHtml(pkg.latest)}</span>`;
  if (pkg.satisfied) return `<span class="deps-ok">已满足</span>`;
  return `<span class="deps-warn">版本不符</span>`;
}

async function loadDepsStatus(refresh) {
  const box = $("#deps-status");
  try {
    const res = await api("/api/deps/status" + (refresh ? "?refresh=1" : ""));
    if (!res.ok) throw new Error(res.error || "获取依赖状态失败");
    const pkgRows = (res.packages || [])
      .map(
        (p) => `
      <tr>
        <td><strong>${escapeHtml(p.name)}</strong></td>
        <td class="muted">${escapeHtml(p.spec || "—")}</td>
        <td>${p.installed ? escapeHtml(p.installed) : `<span class="deps-missing">—</span>`}</td>
        <td class="muted">${p.latest ? escapeHtml(p.latest) : "未知"}</td>
        <td>${depsStatusBadge(p)}</td>
      </tr>`
      )
      .join("");
    const toolRows = (res.tools || [])
      .map(
        (t) => `
      <tr>
        <td><strong>${escapeHtml(t.name)}</strong></td>
        <td class="muted">${t.found ? (t.version ? escapeHtml(t.version) : "已安装") : `<span class="deps-missing">未安装</span>`}</td>
        <td class="muted">${t.required_by ? escapeHtml(t.required_by) : "—"}</td>
        <td>${t.found ? `<span class="deps-ok">可用</span>` : `<span class="deps-missing">缺失</span>`}</td>
      </tr>`
      )
      .join("");
    box.innerHTML = `
      <div class="deps-block">
        <div class="deps-block-title">运行环境</div>
        <div class="muted" style="font-size:12px">Python ${escapeHtml(res.python || "?")} · pip ${escapeHtml(res.pip || "?")}${refresh ? " · 已检查 PyPI 最新版本" : "（未联网检查，可点「检查更新」）"}</div>
      </div>
      <div class="deps-block">
        <div class="deps-block-title">Python 依赖（requirements.txt）</div>
        <table class="deps-table">
          <thead><tr><th>包名</th><th>要求</th><th>已安装</th><th>最新</th><th>状态</th></tr></thead>
          <tbody>${pkgRows || `<tr><td colspan="5" class="muted">未找到 requirements.txt</td></tr>`}</tbody>
        </table>
      </div>
      <div class="deps-block">
        <div class="deps-block-title">外部 CLI 工具</div>
        <table class="deps-table">
          <thead><tr><th>工具</th><th>版本</th><th>Required By</th><th>状态</th></tr></thead>
          <tbody>${toolRows || `<tr><td colspan="4" class="muted">无</td></tr>`}</tbody>
        </table>
      </div>
    `;
  } catch (err) {
    box.innerHTML = `<div class="deps-block"><span class="deps-missing">加载依赖状态失败：${escapeHtml(err.message)}</span></div>`;
  }
}

function syncGroupCheck(group) {
  const checks = Array.from(group.querySelectorAll(".src-check"));
  const on = checks.filter((c) => c.checked).length;
  const gc = group.querySelector(".group-check");
  if (gc) {
    gc.checked = on > 0 && on === checks.length;
    gc.indeterminate = on > 0 && on < checks.length;
  }
}

function renderSources() {
  const box = $("#source-list");
  box.innerHTML = "";
  const groups = config.source_groups && config.source_groups.length
    ? config.source_groups
    : [{ name: "全部音乐源", sources: config.all_sources }];
  groups.forEach((g, gi) => {
    const group = document.createElement("div");
    group.className = "source-group";
    group.dataset.group = gi;
    const head = document.createElement("div");
    head.className = "source-group-head";
    head.innerHTML = `
      <span class="source-group-name">${escapeHtml(g.name)}</span>
      <span class="muted">${g.sources.length} 个源</span>
      <label class="group-toggle"><input type="checkbox" class="group-check" data-group="${gi}"> 全选本组</label>
    `;
    const chips = document.createElement("div");
    chips.className = "source-group-chips";
    g.sources.forEach((s) => {
      const on = config.sources.includes(s);
      const disabled = (config.disabled_sources || []).includes(s);
      const info = sourceCookieInfo(s);
      const chip = document.createElement("label");
      chip.className = "source-chip " + info.cls + (on ? "" : " off") + (disabled ? " disabled" : "");
      chip.title = (disabled ? "已启用但因未配置夸克网盘 Cookie 被跳过（搜索不返回结果）\n" : "") + info.label;
      chip.innerHTML = `<span class="src-dot"></span><input type="checkbox" class="src-check" data-src="${escapeHtml(s)}" ${on ? "checked" : ""}> ${escapeHtml(sourceName(s))}${disabled ? " <span class='src-disabled-tag'>待配夸克</span>" : ""}`;
      chip.querySelector("input").addEventListener("change", (e) => {
        chip.classList.toggle("off", !e.target.checked);
        syncGroupCheck(group);
      });
      chips.appendChild(chip);
    });
    head.querySelector(".group-check").addEventListener("change", (e) => {
      toggleGroupSources(gi, e.target.checked);
    });
    group.appendChild(head);
    group.appendChild(chips);
    box.appendChild(group);
  });
  $$(".source-group").forEach(syncGroupCheck);
}

function toggleGroupSources(groupIdx, on) {
  const group = document.querySelector(`.source-group[data-group="${groupIdx}"]`);
  if (!group) return;
  group.querySelectorAll(".src-check").forEach((c) => {
    c.checked = on;
    c.closest(".source-chip").classList.toggle("off", !on);
  });
  const gc = group.querySelector(".group-check");
  gc.checked = on;
  gc.indeterminate = false;
}

function toggleAllSources(on) {
  $$(".src-check").forEach((c) => {
    c.checked = on;
    c.closest(".source-chip").classList.toggle("off", !on);
  });
  $$(".source-group").forEach(syncGroupCheck);
}

function cookieClassOf(src) {
  const cc = config.cookie_classes && config.cookie_classes[src];
  return cc || "none";
}

function toggleClassSources(cls) {
  const checks = Array.from($$(".src-check")).filter((c) => cookieClassOf(c.dataset.src) === cls);
  if (!checks.length) return;
  const target = !checks.every((c) => c.checked);
  checks.forEach((c) => {
    c.checked = target;
    c.closest(".source-chip").classList.toggle("off", !target);
  });
  $$(".source-group").forEach(syncGroupCheck);
}

async function saveSources() {
  const checked = Array.from($$(".src-check")).filter((c) => c.checked).map((c) => c.dataset.src);
  const res = await api("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sources: checked }),
  });
  if (res.ok) {
    await loadConfig();
    $("#cookie-status").textContent = "音乐源已保存，客户端已重建。";
  }
}

function renderCookieRows() {
  const tbody = $("#cookie-body");
  tbody.innerHTML = "";
  const supported = config.cookie_supported_sources || [];
  const cookieSources = supported.filter((s) => config.all_sources.includes(s));
  if (config.quark_source && supported.includes(config.quark_source) && !cookieSources.includes(config.quark_source)) {
    cookieSources.push(config.quark_source);
  }
  cookieSources.forEach((s) => {
    const val = config.cookies[s] ? JSON.stringify(config.cookies[s], null, 2) : "";
    const tr = document.createElement("tr");
    const hasDomains = config.domains && config.domains[s] && config.domains[s].length;
    const hint = s === "AppleMusicClient"
      ? `需 media-user-token`
      : s === config.quark_source
        ? `需登录 https://pan.quark.cn 后的完整 Cookie`
        : "";
    tr.innerHTML = `
      <td><strong>${escapeHtml(sourceName(s))}</strong>${hint ? `<br><span class="muted">${escapeHtml(hint)}</span>` : ""}</td>
      <td><textarea data-cookie-src="${escapeHtml(s)}" placeholder="留空则清除；支持 JSON 或 k=v; k2=v2">${escapeHtml(val)}</textarea></td>
      <td style="display:flex;flex-direction:column;gap:6px;min-width:140px;">
        ${hasDomains ? `
          <div class="import-row">
            <select class="browser-sel" data-src="${escapeHtml(s)}"></select>
            <button class="btn small browser-import" data-src="${escapeHtml(s)}" title="从浏览器自动读取 Cookie（需先在该浏览器登录该网站）">导入</button>
          </div>` : ""}
        <button class="btn small cookie-save" data-src="${escapeHtml(s)}">保存</button>
        <button class="btn small cookie-clear" data-src="${escapeHtml(s)}">清除</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  $$(".browser-sel").forEach((sel) => {
    (config.browsers || ["chrome"]).forEach((b) => {
      const opt = document.createElement("option");
      opt.value = b;
      opt.textContent = b;
      sel.appendChild(opt);
    });
  });
}

function bindCookieActions() {
  $("#cookie-body").addEventListener("click", async (e) => {
    const importBtn = e.target.closest(".browser-import");
    if (importBtn) {
      const src = importBtn.dataset.src;
      const browser = importBtn.parentElement.querySelector(".browser-sel").value;
      importBtn.disabled = true;
      importBtn.textContent = "读取中…";
      try {
        const res = await api("/api/cookies/from-browser", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ source: src, browser }),
        });
        if (!res.ok) throw new Error(res.error || "读取失败");
        if (!Object.keys(res.cookies).length) {
          $("#cookie-status").textContent = `在 ${browser} 中未找到 ${src} 相关域名（${(res.domains || []).join(", ")}）的 Cookie。请先在浏览器登录，若用 Safari 需给终端开启「完全磁盘访问权限」。`;
          return;
        }
        const ta = document.querySelector(`textarea[data-cookie-src="${CSS.escape(src)}"]`);
        ta.value = JSON.stringify(res.cookies, null, 2);
        $("#cookie-status").textContent = `已从 ${browser} 读取 ${Object.keys(res.cookies).length} 个 Cookie（含 ${res.cookies["media-user-token"] ? "media-user-token" : "提示：未含 media-user-token"}）。点击「保存」生效。`;
      } catch (err) {
        $("#cookie-status").textContent = "导入失败：" + err.message;
      } finally {
        importBtn.disabled = false;
        importBtn.textContent = "导入";
      }
      return;
    }
    const btn = e.target.closest(".cookie-save, .cookie-clear");
    if (!btn) return;
    const src = btn.dataset.src;
    if (btn.classList.contains("cookie-clear")) {
      await api("/api/cookies", { method: "DELETE", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ source: src }) });
      $("#cookie-status").textContent = `已清除 ${src} 的 Cookie。`;
      await loadConfig();
      return;
    }
    const ta = document.querySelector(`textarea[data-cookie-src="${CSS.escape(src)}"]`);
    const raw = ta.value.trim();
    let payload = {};
    if (raw) {
      try { payload = JSON.parse(raw); }
      catch { payload = raw; }
    }
    const res = await api("/api/cookies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: src, cookies: payload }),
    });
    if (res.ok) {
      $("#cookie-status").textContent = `已保存 ${src} 的 Cookie。`;
      await loadConfig();
    } else {
      $("#cookie-status").textContent = "保存失败：" + (res.error || "");
    }
  });
}

const ITEM_STATUS = {
  pending: "等待中",
  downloading: "下载中",
  converting: "转换中",
  done: "完成",
  error: "失败",
};

function itemStatusBadge(item) {
  let cls = "tag";
  if (item.status === "downloading" || item.status === "converting") cls += " running";
  else if (item.status === "error") cls += " error";
  else cls += " done";
  return `<span class="${cls}">${ITEM_STATUS[item.status] || item.status}</span>`;
}

async function loadJobs() {
  const data = await api("/api/jobs");
  const box = $("#jobs-list");
  box.innerHTML = "";
  if (!data.jobs.length) {
    box.innerHTML = `<div class="empty-tip">暂无下载任务</div>`;
    return;
  }
  data.jobs.forEach((j) => {
    const card = document.createElement("div");
    card.className = "job-card";
    const files = (j.files || []).map((f) => {
      const name = f.split(/[\\/]/).pop();
      return `<a href="/api/download-file/${encodeURIComponent(f)}" download>${escapeHtml(name)}</a>`;
    }).join("，");
    const items = (j.items || []).map((it, i) => `
      <div class="job-item">
        <span class="item-name">${i + 1}. ${escapeHtml(it.song_name)} <span class="muted">${escapeHtml(it.singers || "")}</span></span>
        <span class="item-status">${itemStatusBadge(it)}<span class="muted">${escapeHtml(it.detail || "")}</span></span>
      </div>
    `).join("");
    const running = j.status === "running";
    card.innerHTML = `
      <div class="job-head">
        <div class="job-info">
          <span class="job-title">任务 ${j.id} ${j.mode === "aac" ? "· FLAC→AAC" : "· 最高音质"} · ${j.done}/${j.total} 首</span>
          <span class="muted">${running ? "进行中" : fmtTime(j.finished)}</span>
          ${j.error ? `<span class="muted" style="color:var(--red)">错误：${escapeHtml(j.error)}</span>` : ""}
          ${files ? `<span class="muted">文件：${files}</span>` : ""}
        </div>
        <div class="job-right">
          <span class="tag ${j.status}">${j.status === "running" ? "下载中" : j.status === "done" ? "完成" : "失败"}</span>
          <button class="btn small job-toggle" aria-expanded="true">收起</button>
        </div>
      </div>
      <div class="job-items">${items || `<div class="empty-tip">无明细</div>`}</div>
    `;
    card.querySelector(".job-toggle").addEventListener("click", (e) => {
      const itemsEl = card.querySelector(".job-items");
      const expanded = itemsEl.classList.toggle("hidden") === false;
      e.target.textContent = expanded ? "收起" : "展开";
      e.target.setAttribute("aria-expanded", expanded);
    });
    box.appendChild(card);
  });
}

async function loadFiles() {
  const data = await api("/api/files");
  const box = $("#files-list");
  box.innerHTML = "";
  if (!data.files.length) {
    box.innerHTML = `<div class="empty-tip">暂无已下载文件</div>`;
    return;
  }
  data.files.forEach((f) => {
    const card = document.createElement("div");
    card.className = "file-card";
    const dl = (path, label, extra = "") =>
      `<a class="btn small" href="/api/download-file/${encodeURIComponent(path)}${extra}" download>${label}</a>`;
    let actions = "";
    if (f.format === "lossless") {
      actions += dl(f.path, "下载FLAC");
      actions += dl(f.path, "压缩版", "?kind=compressed");
    } else {
      actions += dl(f.path, "下载");
    }
    if (f.lrc_path) actions += dl(f.lrc_path, "歌词");
    card.innerHTML = `
      <div class="file-meta">
        <span class="file-name">${escapeHtml(f.name)}</span>
        <span class="muted">${fmtSize(f.size)} · ${f.format === "lossless" ? "无损" : "压缩"} · ${fmtTime(f.mtime)}</span>
      </div>
      <div class="file-actions">${actions}</div>
    `;
    box.appendChild(card);
  });
}

function playPreview(url, name) {
  const bar = $("#player-bar");
  bar.classList.remove("hidden");
  $("#audio").src = url;
  $("#player-label").textContent = "正在试听：" + name;
  $("#audio").play().catch(() => {});
}

const ANSI_RE = /\u001b\[[0-9;]*[a-zA-Z]/g;

let logFilterLevel = "all";
let logSearchQuery = "";

function classifyLogLine(line) {
  const cleaned = line.replace(ANSI_RE, "");
  if (/\b(ERROR|Error|Traceback|Exception)\b/.test(cleaned)) return "error";
  if (/\b(WARNING|WARN)\b/.test(cleaned)) return "warn";
  return "info";
}

function escapeLogLine(line) {
  const cleaned = line.replace(ANSI_RE, "");
  const level = classifyLogLine(line);
  const cls = level === "error" ? "log-err" : level === "warn" ? "log-warn" : "log-line";
  return `<div class="${cls}" data-level="${level}">${escapeHtml(cleaned)}</div>`;
}

function filterLogLines() {
  const box = $("#log-box");
  const divs = box.querySelectorAll("div[data-level]");
  divs.forEach((d) => {
    const level = d.dataset.level;
    const text = d.textContent;
    const matchLevel = logFilterLevel === "all" || level === logFilterLevel;
    const matchSearch = !logSearchQuery || text.toLowerCase().includes(logSearchQuery);
    d.style.display = matchLevel && matchSearch ? "" : "none";
  });
}

async function loadLogs() {
  try {
    const data = await api("/api/logs?lines=400");
    if (!data.ok) throw new Error(data.error || "读取日志失败");
    const box = $("#log-box");
    const atBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 40;
    box.innerHTML = data.lines.map(escapeLogLine).join("");
    $("#log-file").textContent = "文件：" + data.file;
    filterLogLines();
    if (atBottom) box.scrollTop = box.scrollHeight;
  } catch (err) {
    $("#log-file").textContent = "读取日志失败：" + err.message;
  }
}

async function clearLogs() {
  if (!confirm("确定要清空日志文件吗？")) return;
  try {
    const res = await api("/api/logs/clear", { method: "POST" });
    if (!res.ok) throw new Error(res.error || "清空失败");
    $("#log-box").innerHTML = "";
    $("#log-file").textContent = "日志已清空";
  } catch (err) {
    $("#log-file").textContent = "清空失败：" + err.message;
  }
}

function init() {
  $$(".tab").forEach((t) => t.addEventListener("click", () => switchTab(t.dataset.tab)));
  $("#search-btn").addEventListener("click", doSearch);
  $("#search-input").addEventListener("keydown", (e) => { if (e.key === "Enter") doSearch(); });
  $("#playlist-btn").addEventListener("click", doPlaylist);
  $("#playlist-input").addEventListener("keydown", (e) => { if (e.key === "Enter") doPlaylist(); });
  $("#search-download-best-btn").addEventListener("click", () => doDownload("search", "best"));
  $("#search-download-aac-btn").addEventListener("click", () => doDownload("search", "aac"));
  $("#playlist-download-best-btn").addEventListener("click", () => doDownload("playlist", "best"));
  $("#playlist-download-aac-btn").addEventListener("click", () => doDownload("playlist", "aac"));
  $("#save-sources-btn").addEventListener("click", saveSources);
  $("#select-all-sources-btn").addEventListener("click", () => toggleAllSources(true));
  $("#clear-sources-btn").addEventListener("click", () => toggleAllSources(false));
  $$(".legend-toggle").forEach((li) => li.addEventListener("click", () => toggleClassSources(li.dataset.class)));
  $("#import-all-btn").addEventListener("click", importAllCookies);
  $("#update-musicdl-btn").addEventListener("click", () => startUpdate("musicdl"));
  $("#update-deps-btn").addEventListener("click", () => startUpdate("deps"));
  $("#deps-refresh-btn").addEventListener("click", () => loadDepsStatus(false));
  $("#deps-check-btn").addEventListener("click", () => loadDepsStatus(true));
  $("#refresh-files-btn").addEventListener("click", loadFiles);
  $("#log-refresh-btn").addEventListener("click", loadLogs);
  $("#log-clear-btn").addEventListener("click", clearLogs);
  $$(".log-filter").forEach((btn) => {
    btn.addEventListener("click", () => {
      $$(".log-filter").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      logFilterLevel = btn.dataset.level;
      filterLogLines();
    });
  });
  $("#log-search").addEventListener("input", (e) => {
    logSearchQuery = e.target.value.trim().toLowerCase();
    filterLogLines();
  });
  $("#restart-btn").addEventListener("click", () => restartServer());
  $("#shutdown-btn").addEventListener("click", () => shutdownServer());
  $("#log-auto").addEventListener("change", (e) => {
    if (e.target.checked) { logTimer = setInterval(loadLogs, 4000); loadLogs(); }
    else clearInterval(logTimer);
  });
  $("#player-close").addEventListener("click", () => { $("#player-bar").classList.add("hidden"); $("#audio").pause(); });
  bindCheckAll("#search-check-all", "#search-body");
  bindCheckAll("#playlist-check-all", "#playlist-body");
  bindCookieActions();

  document.body.addEventListener("click", (e) => {
    const btn = e.target.closest(".preview-btn");
    if (btn) playPreview(btn.dataset.preview, btn.dataset.name);
  });

  const savedTab = localStorage.getItem("musicplayground_tab");
  if (savedTab) switchTab(savedTab);

  loadConfig();
  loadJobs();
  loadFiles();
  loadLogs();
  logTimer = setInterval(loadJobs, 4000);
  setInterval(() => {
    if ($("#log-auto").checked && $("#tab-logs").classList.contains("active")) loadLogs();
  }, 4000);
}

init();
