import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

from flask import Flask, jsonify, request, send_from_directory

from backend import ALL_SOURCES, CookieManager, MusicService, parse_cookies_input, BROWSERS, COOKIE_SUPPORTED_SOURCES, SOURCE_DOMAINS, extract_cookies

app = Flask(__name__, static_folder="static", static_url_path="/static")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

cookie_manager = CookieManager(config_path=CONFIG_PATH)
service = MusicService(cookie_manager=cookie_manager)

# pip 更新任务状态（单任务，避免并发冲突）
_UPDATE_STATE = {
    "running": False,
    "kind": None,
    "done": False,
    "ok": None,
    "output": [],
}


def _pip_version(name):
    try:
        return __import__("importlib.metadata", fromlist=["version"]).version(name)
    except Exception:
        return None


# ---- 依赖状态检测 ----
_DEPS_CACHE = {"ts": 0, "latest": {}}
_DEPS_CACHE_TTL = 600  # 10 分钟


def _parse_requirements():
    req_path = os.path.join(BASE_DIR, "requirements.txt")
    reqs = []
    if not os.path.exists(req_path):
        return reqs
    with open(req_path, "r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for sep in ("==", ">=", "<=", "~=", "!=", ">", "<"):
                if sep in line:
                    name, _, spec = line.partition(sep)
                    reqs.append({"name": name.strip(), "spec": sep + spec})
                    break
            else:
                reqs.append({"name": line.split()[0], "spec": ""})
    return reqs


def _installed_version(name):
    return _pip_version(name)


def _pypi_latest(name, refresh=False):
    now = time.time()
    if not refresh and _DEPS_CACHE["latest"].get(name) is not None:
        return _DEPS_CACHE["latest"][name]
    try:
        url = f"https://pypi.org/pypi/{name}/json"
        req = urllib.request.Request(url, headers={"User-Agent": "MusicPlayground/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        latest = data.get("info", {}).get("version")
    except Exception:
        latest = None
    _DEPS_CACHE["latest"][name] = latest
    _DEPS_CACHE["ts"] = now
    return latest


def _parse_ver(v):
    out = []
    for part in str(v or "").replace("-", ".").split("."):
        if part.isdigit():
            out.append(int(part))
        else:
            out.append(sum(ord(c) for c in part) if part else 0)
    return tuple(out)


def _spec_satisfied(installed, spec):
    if not installed or not spec:
        return bool(installed)
    try:
        op = spec[:2].strip()
        if op not in (">=", "<=", "==", "~=", "!=", ">", "<"):
            return True
        ver = _parse_ver(spec[2:].strip())
        cur = _parse_ver(installed)
        if op == ">=":
            return cur >= ver
        if op == "<=":
            return cur <= ver
        if op == "==":
            return cur == ver
        if op == "!=":
            return cur != ver
        if op == ">":
            return cur > ver
        if op == "<":
            return cur < ver
        if op == "~=":
            return cur >= ver and cur[0] == ver[0]
    except Exception:
        pass
    return True


def _check_tool(name, ver_args, ver_index):
    path = subprocess.run(["which", name], capture_output=True, text=True).stdout.strip()
    if not path:
        return {"name": name, "found": False, "version": None}
    version = None
    try:
        out = subprocess.run([name] + ver_args, capture_output=True, text=True, timeout=8).stdout
        first = next((l for l in out.splitlines() if l.strip()), "")
        parts = first.split()
        version = parts[ver_index] if len(parts) > ver_index else first[:80]
    except Exception:
        pass
    return {"name": name, "found": True, "version": version}


def _update_worker(kind):
    req_path = os.path.join(BASE_DIR, "requirements.txt")
    if kind == "musicdl":
        cmd = [sys.executable, "-m", "pip", "install", "-U", "musicdl"]
        label = "更新 musicdl"
    elif kind == "deps":
        cmd = [sys.executable, "-m", "pip", "install", "-r", req_path]
        label = "安装/更新依赖"
    elif kind == "all":
        cmd = [sys.executable, "-m", "pip", "install", "-U", "musicdl", "-r", req_path]
        label = "更新 musicdl + 依赖"
    else:
        _UPDATE_STATE.update(running=False, done=True, ok=False, output=["未知的更新类型"])
        return
    _UPDATE_STATE["output"].append(f"$ {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                _UPDATE_STATE["output"].append(line)
                if len(_UPDATE_STATE["output"]) > 800:
                    _UPDATE_STATE["output"] = _UPDATE_STATE["output"][-800:]
        proc.wait()
        ok = proc.returncode == 0
        _UPDATE_STATE["output"].append(("成功：" if ok else "失败：") + label)
    except Exception as err:
        ok = False
        _UPDATE_STATE["output"].append(f"错误：{err}")
    finally:
        _UPDATE_STATE.update(running=False, done=True, ok=ok)


@app.route("/")
def index():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "index.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    cookies = cookie_manager.all_cookies()
    return jsonify(
        {
            "sources": cookie_manager.sources,
            "work_dir": cookie_manager.work_dir,
            "all_sources": ALL_SOURCES,
            "cookie_supported_sources": sorted(COOKIE_SUPPORTED_SOURCES),
            "cookies": cookies,
        }
    )


@app.route("/api/config", methods=["POST"])
def update_config():
    data = request.get_json(force=True) or {}
    if "sources" in data:
        sources = [s for s in data["sources"] if s in ALL_SOURCES]
        cookie_manager.set_sources(sources)
    if "work_dir" in data:
        cookie_manager.set_work_dir(data["work_dir"])
    return jsonify({"ok": True})


@app.route("/api/cookies", methods=["POST"])
def set_cookies():
    data = request.get_json(force=True) or {}
    source = data.get("source")
    if source not in ALL_SOURCES:
        return jsonify({"ok": False, "error": f"invalid source: {source}"}), 400
    cookies = parse_cookies_input(data.get("cookies"))
    cookie_manager.set(source, cookies)
    service._client = None
    return jsonify({"ok": True, "cookies": cookies})


@app.route("/api/cookies", methods=["DELETE"])
def delete_cookies():
    data = request.get_json(force=True) or {}
    source = data.get("source")
    if source:
        cookie_manager.delete(source)
        service._client = None
    return jsonify({"ok": True})


@app.route("/api/cookies/from-browser", methods=["POST"])
def cookies_from_browser():
    data = request.get_json(force=True) or {}
    source = data.get("source")
    browser = data.get("browser") or "chrome"
    if source not in ALL_SOURCES:
        return jsonify({"ok": False, "error": f"invalid source: {source}"}), 400
    if browser not in BROWSERS:
        return jsonify({"ok": False, "error": f"unsupported browser: {browser}"}), 400
    try:
        cookies = extract_cookies(source, browser)
        return jsonify({"ok": True, "cookies": cookies, "domains": SOURCE_DOMAINS.get(source, [])})
    except Exception as err:
        return jsonify({"ok": False, "error": str(err)}), 500


@app.route("/api/cookies/import-all", methods=["POST"])
def import_all_cookies():
    data = request.get_json(force=True) or {}
    browser = data.get("browser") or "chrome"
    if browser not in BROWSERS:
        return jsonify({"ok": False, "error": f"unsupported browser: {browser}"}), 400
    results = {}
    total = 0
    for source in cookie_manager.sources:
        if source not in COOKIE_SUPPORTED_SOURCES:
            continue
        try:
            cookies = extract_cookies(source, browser)
            if cookies:
                cookie_manager.set(source, cookies)
                total += len(cookies)
                results[source] = len(cookies)
            else:
                results[source] = 0
        except Exception as err:
            results[source] = "error: " + str(err)
    service._client = None
    return jsonify({"ok": True, "total": total, "results": results})


@app.route("/api/browsers")
def list_browsers():
    return jsonify({"ok": True, "browsers": BROWSERS})


@app.route("/api/domains")
def list_domains():
    return jsonify({"ok": True, "domains": SOURCE_DOMAINS})


@app.route("/api/update", methods=["POST"])
def start_update():
    data = request.get_json(force=True) or {}
    kind = data.get("kind") or "all"
    if kind not in ("musicdl", "deps", "all"):
        return jsonify({"ok": False, "error": f"invalid kind: {kind}"}), 400
    if _UPDATE_STATE["running"]:
        return jsonify({"ok": False, "error": "已有更新任务在进行中，请稍候"}), 409
    _UPDATE_STATE.update(running=True, kind=kind, done=False, ok=None, output=[])
    threading.Thread(target=_update_worker, args=(kind,), daemon=True).start()
    return jsonify({"ok": True, "kind": kind})


@app.route("/api/update/status")
def update_status():
    out = _UPDATE_STATE["output"]
    return jsonify(
        {
            "ok": True,
            "running": _UPDATE_STATE["running"],
            "done": _UPDATE_STATE["done"],
            "result_ok": _UPDATE_STATE["ok"],
            "kind": _UPDATE_STATE["kind"],
            "output": out,
            "versions": {
                "musicdl": _pip_version("musicdl"),
                "flask": _pip_version("flask"),
                "rookiepy": _pip_version("rookiepy"),
            },
        }
    )


@app.route("/api/deps/status")
def deps_status():
    refresh = request.args.get("refresh") == "1"
    packages = []
    for r in _parse_requirements():
        installed = _installed_version(r["name"])
        latest = _pypi_latest(r["name"], refresh=refresh)
        packages.append(
            {
                "name": r["name"],
                "spec": r["spec"],
                "installed": installed,
                "latest": latest,
                "satisfied": _spec_satisfied(installed, r["spec"]),
            }
        )
    tools = [
        _check_tool("ffmpeg", ["-version"], 2),
        _check_tool("N_m3u8DL-RE", ["--version"], 2),
        _check_tool("MP4Box", ["-version"], 2),
    ]
    return jsonify(
        {
            "ok": True,
            "python": sys.version.split()[0],
            "pip": _pip_version("pip"),
            "refresh": refresh,
            "packages": packages,
            "tools": tools,
        }
    )


@app.route("/api/search")
def search():
    keyword = (request.args.get("keyword") or "").strip()
    if not keyword:
        return jsonify({"ok": False, "error": "keyword required"}), 400
    try:
        sid, songs = service.search(keyword=keyword)
        return jsonify(
            {
                "ok": True,
                "sid": sid,
                "songs": [service.song_to_dict(s) for s in songs],
            }
        )
    except Exception as err:
        return jsonify({"ok": False, "error": str(err)}), 500


@app.route("/api/playlist", methods=["POST"])
def parse_playlist():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"ok": False, "error": "url required"}), 400
    try:
        sid, songs, detected = service.parse_playlist(url)
        return jsonify(
            {
                "ok": True,
                "sid": sid,
                "source": detected,
                "songs": [service.song_to_dict(s) for s in songs],
            }
        )
    except Exception as err:
        return jsonify({"ok": False, "error": str(err)}), 500


@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json(force=True) or {}
    sid = data.get("sid")
    ids = data.get("ids")
    mode = data.get("mode") or "best"
    if mode not in ("best", "aac"):
        mode = "best"
    try:
        job_id = service.start_download(sid, ids, mode=mode)
        return jsonify({"ok": True, "job_id": job_id})
    except Exception as err:
        return jsonify({"ok": False, "error": str(err)}), 400


@app.route("/api/jobs")
def list_jobs():
    return jsonify({"ok": True, "jobs": service.jobs()})


@app.route("/api/jobs/<job_id>")
def get_job(job_id):
    job = service.job(job_id)
    if job is None:
        return jsonify({"ok": False, "error": "job not found"}), 404
    return jsonify({"ok": True, "job": job})


@app.route("/api/files")
def list_files():
    return jsonify({"ok": True, "files": service.list_files()})


@app.route("/api/logs")
def get_logs():
    from musicdl.modules.utils.logger import LoggerHandle

    num_lines = request.args.get("lines", default=300, type=int)
    log_path = LoggerHandle.log_file_path
    if not os.path.exists(log_path):
        return jsonify({"ok": True, "file": log_path, "lines": []})
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as fp:
            content = fp.read()
        log_lines = content.splitlines()[-max(1, min(num_lines, 2000)):]
        return jsonify({"ok": True, "file": log_path, "lines": log_lines})
    except Exception as err:
        return jsonify({"ok": False, "error": str(err)}), 500


@app.route("/api/download-file/<path:relpath>")
def download_file(relpath):
    from backend.service import _ALREADY_LOSSY_EXT, _LOSSLESS_EXT, _is_lossless_m4a, convert_to_aac

    root = os.path.abspath(cookie_manager.work_dir)
    full = os.path.abspath(os.path.join(root, relpath))
    if os.path.commonpath([root, full]) != root or not os.path.isfile(full):
        return jsonify({"ok": False, "error": "invalid path"}), 400
    kind = request.args.get("kind", "raw")
    stem = os.path.splitext(full)[0]
    # 下载歌词
    if kind == "lrc":
        for cand in (stem + ".lrc", stem + ".txt"):
            if os.path.exists(cand):
                return send_from_directory(root, os.path.relpath(cand, root), as_attachment=True)
        return jsonify({"ok": False, "error": "no lyric file"}), 404
    # 下载压缩版（m4a / mp3）
    if kind == "compressed":
        ext = os.path.splitext(full)[1].lower()
        lossless = ext in _LOSSLESS_EXT or (ext == ".m4a" and _is_lossless_m4a(full))
        if not lossless:
            # 本身已是有损压缩，直接返回
            return send_from_directory(root, relpath, as_attachment=True)
        for cand in (stem + ".m4a", stem + ".mp3"):
            if os.path.exists(cand):
                return send_from_directory(root, os.path.relpath(cand, root), as_attachment=True)
        # 没有压缩版：现场转换并保留，然后返回
        result = convert_to_aac(full)
        if result and os.path.exists(result) and result != full:
            return send_from_directory(root, os.path.relpath(result, root), as_attachment=True)
        return send_from_directory(root, relpath, as_attachment=True)
    # 默认：下载原始文件
    return send_from_directory(root, relpath, as_attachment=True)


if __name__ == "__main__":
    print("MusicPlayground running at http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False, threaded=True)
