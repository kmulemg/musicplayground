import json
import os
import re
import shutil
import subprocess
import threading
import time
import uuid

from musicdl import musicdl as musicdl_module
from musicdl.modules import MusicClientBuilder
from musicdl.modules.utils import cookies2dict, safeextractfromdict
from musicdl.modules.utils import hosts as _musicdl_hosts

from .cookie_manager import CookieManager

ALL_SOURCES = sorted(MusicClientBuilder.REGISTERED_MODULES.keys())

# 域名 → 音乐源（基于 musicdl 官方 hosts 常量构建）
_HOST_CONST_TO_SOURCE = {
    "APPLE_MUSIC_HOSTS": "AppleMusicClient",
    "AUDIUS_MUSIC_HOSTS": "AudiusMusicClient",
    "BODIAN_MUSIC_HOST": "BodianMusicClient",
    "CCMIXTER_MUSIC_HOSTS": "CCMixterMusicClient",
    "DEEZER_MUSIC_HOSTS": "DeezerMusicClient",
    "FIVESING_MUSIC_HOSTS": "FiveSingMusicClient",
    "JOOX_MUSIC_HOSTS": "JooxMusicClient",
    "JAMENDO_MUSIC_HOSTS": "JamendoMusicClient",
    "KUWO_MUSIC_HOSTS": "KuwoMusicClient",
    "KUGOU_MUSIC_HOSTS": "KugouMusicClient",
    "MIGU_MUSIC_HOSTS": "MiguMusicClient",
    "NETEASE_MUSIC_HOSTS": "NeteaseMusicClient",
    "QQ_MUSIC_HOSTS": "QQMusicClient",
    "QIANQIAN_MUSIC_HOSTS": "QianqianMusicClient",
    "QOBUZ_MUSIC_HOSTS": "QobuzMusicClient",
    "STREETVOICE_MUSIC_HOSTS": "StreetVoiceMusicClient",
    "SOUNDCLOUD_MUSIC_HOSTS": "SoundCloudMusicClient",
    "SODA_MUSIC_HOSTS": "SodaMusicClient",
    "SPOTIFY_MUSIC_HOSTS": "SpotifyMusicClient",
    "SUNO_MUSIC_HOSTS": "SunoMusicClient",
    "TIDAL_MUSIC_HOSTS": "TIDALMusicClient",
    "FMA_MUSIC_HOSTS": "FMAMusicClient",
    "JIOSAAVN_MUSIC_HOSTS": "JioSaavnMusicClient",
    "MOOV_MUSIC_HOSTS": "MOOVMusicClient",
}

HOST_TO_SOURCE = {}
for _const_name, _source in _HOST_CONST_TO_SOURCE.items():
    _hosts = getattr(_musicdl_hosts, _const_name, None)
    if not _hosts:
        continue
    for _host in _hosts:
        HOST_TO_SOURCE.setdefault(str(_host).lower().lstrip("."), _source)


def detect_source(url):
    hostname = _musicdl_hosts.obtainhostname(url)
    if not hostname:
        return None
    for host, source in HOST_TO_SOURCE.items():
        if hostname == host or hostname.endswith("." + host):
            return source
    return None

VALID_AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".aac", ".wav", ".ape", ".ogg", ".opus", ".alac", ".webm", ".m4b"}

AAC_BITRATE = "256k"

_LOSSLESS_EXT = {".flac", ".ape", ".wav", ".wv", ".tta", ".dsf", ".dff"}
_ALREADY_LOSSY_EXT = {".mp3", ".aac", ".ogg", ".opus", ".wma", ".webm"}

# musicdl 默认目录格式： "<yyyy-mm-dd-hh-mm-ss> <名称>"，整理时去掉时间戳前缀
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}\s+")


def _strip_timestamp(name):
    return _TIMESTAMP_RE.sub("", name, count=1) or name


def _is_lossless_m4a(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return False
    try:
        res = subprocess.run(
            [
                ffprobe, "-v", "error", "-select_streams", "a:0",
                "-show_entries", "stream=codec_name",
                "-of", "default=noprint_wrappers=1:nokey=1", path,
            ],
            capture_output=True, text=True, timeout=60,
        )
        codec = (res.stdout or "").strip().lower()
        return codec in {"alac", "flac", "pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le", "truehd"}
    except Exception:
        return False


def convert_to_aac(path, bitrate=AAC_BITRATE):
    """将无损音频转为 AAC-LC(m4a)；已是压缩格式则跳过；转换成功则返回新 m4a 路径（保留原文件）。"""
    ext = os.path.splitext(path)[1].lower()
    if ext in _ALREADY_LOSSY_EXT:
        return path
    need = ext in _LOSSLESS_EXT
    if ext == ".m4a":
        need = _is_lossless_m4a(path)
    if not need:
        return path
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return path
    out = os.path.splitext(path)[0] + ".m4a"
    cmd = [ffmpeg, "-y", "-i", path, "-vn", "-c:a", "aac", "-b:a", bitrate, "-movflags", "+faststart", out]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if res.returncode == 0 and os.path.exists(out):
            return out
    except Exception:
        pass
    if os.path.exists(out):
        try:
            os.remove(out)
        except Exception:
            pass
    return path


def parse_cookies_input(raw):
    if isinstance(raw, dict):
        return dict(raw)
    if not isinstance(raw, str):
        return {}
    raw = raw.strip()
    if not raw:
        return {}
    try:
        return dict(json.loads(raw))
    except Exception:
        pass
    return dict(cookies2dict(raw))


class MusicService:
    def __init__(self, cookie_manager: CookieManager):
        self.cm = cookie_manager
        self._client = None
        self._client_cfg_hash = None
        self._lock = threading.Lock()
        self._library = {}
        self._jobs = {}
        self._seq = 0

    def _cfg_hash(self):
        return json.dumps(
            {
                "sources": self.cm.sources,
                "work_dir": self.cm.work_dir,
                "cookies": self.cm.all_cookies(),
            },
            sort_keys=True,
        )

    def _build_init_cfg(self):
        init_cfg = {}
        for source in self.cm.sources:
            cookies = self.cm.get(source)
            cfg = {
                "work_dir": self.cm.work_dir,
                "disable_print": True,
                "search_size_per_source": 10,
                "max_retries": 2,
            }
            if cookies:
                cfg["default_search_cookies"] = cookies
                cfg["default_download_cookies"] = cookies
                cfg["default_parse_cookies"] = cookies
            init_cfg[source] = cfg
        return init_cfg

    def _build_client(self):
        request_overrides = {
            source: {"timeout": (8, 20), "headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"}}
            for source in self.cm.sources
        }
        return musicdl_module.MusicClient(
            music_sources=self.cm.sources,
            init_music_clients_cfg=self._build_init_cfg(),
            requests_overrides=request_overrides,
        )

    def _get_client(self):
        cfg_hash = self._cfg_hash()
        with self._lock:
            if self._client is None or self._client_cfg_hash != cfg_hash:
                self._client = self._build_client()
                self._client_cfg_hash = cfg_hash
            return self._client

    def _store(self, kind, songs, source=None, name=None):
        self._seq += 1
        sid = str(self._seq)
        self._library[sid] = {
            "kind": kind,
            "source": source,
            "name": name,
            "songs": list(songs),
            "created": time.time(),
        }
        return sid

    def get_songs(self, sid, ids=None):
        entry = self._library.get(sid)
        if not entry:
            raise KeyError(f"unknown sid: {sid}")
        songs = entry["songs"]
        if ids is None:
            return list(songs)
        return [songs[int(i)] for i in ids if 0 <= int(i) < len(songs)]

    def song_to_dict(self, song_info):
        preview_url = None
        download_url = song_info.download_url
        if isinstance(download_url, str) and str(download_url).startswith("http"):
            preview_url = download_url
        else:
            try:
                previews = safeextractfromdict(song_info.raw_data, ["search", "attributes", "previews"], []) or []
                if previews and previews[0].get("url"):
                    preview_url = previews[0]["url"]
            except Exception:
                pass
        return {
            "song_name": song_info.song_name,
            "singers": song_info.singers,
            "album": song_info.album,
            "duration": song_info.duration,
            "file_size": song_info.file_size,
            "ext": song_info.ext,
            "source": song_info.source,
            "cover_url": song_info.cover_url,
            "preview_url": preview_url,
        }

    def search(self, keyword):
        client = self._get_client()
        results = client.search(keyword=keyword)
        songs = []
        for source, source_songs in results.items():
            for song_info in source_songs:
                if song_info.with_valid_download_url:
                    songs.append(song_info)
        sid = self._store("search", songs, name=keyword or "搜索")
        return sid, songs

    def parse_playlist(self, url):
        client = self._get_client()
        detected = detect_source(url)
        if detected and detected in client.music_clients:
            # 根据链接域名识别平台后，直接调用对应源，避免逐源空试
            source_client = client.music_clients[detected]
            songs = source_client.parseplaylist(
                url, request_overrides=dict(client.requests_overrides.get(detected, {}) or {})
            ) or []
        else:
            songs = client.parseplaylist(url) or []
        # 歌单名取自 musicdl 生成的目录名（"<时间戳> <歌单名>"），去掉时间戳前缀
        name = None
        if songs:
            try:
                name = _strip_timestamp(os.path.basename(songs[0].work_dir or "")) or None
            except Exception:
                name = None
        sid = self._store("playlist", songs, name=name or "歌单")
        return sid, songs, detected

    def start_download(self, sid, ids, mode="best"):
        songs = self.get_songs(sid, ids)
        job_id = uuid.uuid4().hex[:10]
        job = {
            "id": job_id,
            "sid": sid,
            "mode": mode,
            "status": "running",
            "total": len(songs),
            "done": 0,
            "files": [],
            "error": None,
            "created": time.time(),
            "finished": None,
            "items": [
                {
                    "song_name": s.song_name,
                    "singers": s.singers,
                    "status": "pending",
                    "detail": "等待中",
                    "file": None,
                }
                for s in songs
            ],
        }
        self._jobs[job_id] = job
        threading.Thread(target=self._run_download, args=(job, songs, mode), daemon=True).start()
        return job_id

    def _find_existing(self, source, folder, identifier):
        """在 downloads/<来源>/<名称>/ 中查找相同歌曲 ID 的已有文件。"""
        dest_dir = os.path.join(self.cm.work_dir, source, folder)
        if not os.path.isdir(dest_dir):
            return None
        marker = f" - {identifier}."
        try:
            for name in os.listdir(dest_dir):
                if name.endswith((".lrc", ".jpg", ".png", ".pkl", ".DS_Store")):
                    continue
                if marker in name:
                    full = os.path.join(dest_dir, name)
                    if os.path.isfile(full):
                        return full
        except Exception:
            return None
        return None

    def _run_download(self, job, songs, mode):
        try:
            client = self._get_client()
            folder = (self._library.get(job["sid"]) or {}).get("name") or "未分类"
            items = job["items"]
            # 本地查重：相同 ID 的文件已存在则跳过下载
            to_download, available = [], []
            for idx, song_info in enumerate(songs):
                item = items[idx]
                existing = self._find_existing(song_info.source, folder, song_info.identifier)
                if existing:
                    if mode == "aac":
                        ext = os.path.splitext(existing)[1].lower()
                        if (ext in _LOSSLESS_EXT) or (ext == ".m4a" and _is_lossless_m4a(existing)):
                            # 已有无损版本
                            available.append(existing)
                            stem = os.path.splitext(existing)[0]
                            sibling = None
                            for cand in (stem + ".m4a", stem + ".mp3"):
                                if os.path.exists(cand) and cand != existing:
                                    sibling = cand
                                    break
                            if sibling:
                                # 已有无损 + 已有压缩版，无需再转
                                available.append(sibling)
                                item["status"], item["detail"], item["file"] = "done", "已有无损 + 已有 AAC", sibling
                            else:
                                # 无压缩版，需直接转 AAC（保留无损）
                                item["status"], item["detail"] = "converting", "已有无损，正在转 AAC"
                                converted = convert_to_aac(existing)
                                if converted != existing:
                                    available.append(converted)
                                    item["status"], item["detail"], item["file"] = "done", "已有无损已转 AAC", converted
                                else:
                                    item["status"], item["detail"], item["file"] = "done", "已有无损", existing
                        else:
                            item["status"], item["detail"], item["file"] = "done", "已有压缩版", existing
                            available.append(existing)
                    else:
                        item["status"], item["detail"], item["file"] = "done", "已有文件", existing
                        available.append(existing)
                    continue
                item["status"], item["detail"] = "downloading", "下载中"
                to_download.append((idx, song_info))
            downloaded = client.download(song_infos=[s for _, s in to_download]) if to_download else []
            # 按 (来源, ID) 对应已下载结果
            downloaded_map = {}
            for dl in downloaded:
                downloaded_map[(dl.source, dl.identifier)] = dl
            files = list(available)
            for idx, song_info in to_download:
                item = items[idx]
                dl = downloaded_map.get((song_info.source, song_info.identifier))
                if dl is None:
                    item["status"], item["detail"] = "error", "下载失败"
                    continue
                path = dl.save_path
                if not path or not os.path.exists(path):
                    item["status"], item["detail"] = "error", "下载失败"
                    continue
                if mode == "aac":
                    item["status"], item["detail"] = "converting", "转换 AAC 中"
                    converted = convert_to_aac(path)
                    org_flac = self._organize(job["sid"], song_info.source, path)
                    files.append(org_flac)
                    item["file"] = org_flac
                    if converted != path:
                        org_m4a = self._organize(job["sid"], song_info.source, converted)
                        files.append(org_m4a)
                        item["file"] = org_m4a
                        item["status"], item["detail"] = "done", "完成（FLAC + AAC）"
                    else:
                        item["status"], item["detail"] = "done", "完成"
                else:
                    org = self._organize(job["sid"], song_info.source, path)
                    files.append(org)
                    item["status"], item["detail"], item["file"] = "done", "完成", org
            # 去重文件列表
            seen, deduped = set(), []
            for f in files:
                if f not in seen:
                    seen.add(f)
                    deduped.append(f)
            job["files"] = deduped
            job["done"] = sum(1 for it in items if it["status"] in {"done", "error"})
            job["status"] = "done"
        except Exception as err:
            job["status"] = "error"
            job["error"] = str(err)
        finally:
            job["finished"] = time.time()

    def _organize(self, sid, source, path):
        """把下载好的文件移动到 downloads/<来源>/<歌单或搜索词>/ 目录，同名去重，并携带歌词等附属文件。"""
        entry = self._library.get(sid) or {}
        folder = entry.get("name") or "未分类"
        dest_dir = os.path.join(self.cm.work_dir, source, folder)
        try:
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, os.path.basename(path))
            if os.path.abspath(dest) == os.path.abspath(path):
                return path
            if os.path.exists(dest):
                if os.path.getsize(dest) == os.path.getsize(path):
                    os.remove(path)  # 已存在同名同大小文件，视为重复
                    return dest
                stem, ext = os.path.splitext(dest)
                i = 1
                while os.path.exists(f"{stem} ({i}){ext}"):
                    i += 1
                dest = f"{stem} ({i}){ext}"
            src_dir = os.path.dirname(path)
            shutil.move(path, dest)
            # 移动同名附属文件（.lrc / .jpg / .png 等）
            stem = os.path.splitext(os.path.basename(path))[0]
            try:
                for side in os.listdir(src_dir):
                    side_full = os.path.join(src_dir, side)
                    if os.path.isfile(side_full) and os.path.splitext(side)[0] == stem:
                        shutil.move(side_full, os.path.join(dest_dir, side))
            except Exception:
                pass
            self._prune_empty_parents(path)
            return dest
        except Exception:
            return path

    def _prune_empty_parents(self, path):
        root = os.path.abspath(self.cm.work_dir)
        d = os.path.dirname(path)
        while d and os.path.abspath(d) != root and os.path.abspath(d).startswith(root):
            try:
                if not os.listdir(d):
                    os.rmdir(d)
                else:
                    break
            except Exception:
                break
            d = os.path.dirname(d)

    def organize_existing(self):
        """扫描现有文件，按 downloads/<来源>/<名称> 结构整理；返回移动数量。"""
        root = os.path.abspath(self.cm.work_dir)
        if not os.path.isdir(root):
            return 0
        moved = 0
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                full = os.path.join(dirpath, name)
                rel_dir = os.path.relpath(dirpath, root).split(os.sep)
                if len(rel_dir) < 2:
                    continue  # 直接位于来源目录下，无法分类
                source, folder = rel_dir[0], rel_dir[1]
                clean = _strip_timestamp(folder)
                if clean == folder:
                    continue  # 已在整理后的目录
                dest_dir = os.path.join(root, source, clean)
                dest = os.path.join(dest_dir, name)
                if os.path.abspath(dest) == os.path.abspath(full):
                    continue
                os.makedirs(dest_dir, exist_ok=True)
                if os.path.exists(dest):
                    if os.path.getsize(dest) == os.path.getsize(full):
                        os.remove(full)
                        moved += 1
                        continue
                    stem, ext = os.path.splitext(dest)
                    i = 1
                    while os.path.exists(f"{stem} ({i}){ext}"):
                        i += 1
                    dest = f"{stem} ({i}){ext}"
                shutil.move(full, dest)
                moved += 1
        # 清理 .pkl 缓存与空的旧目录
        for dirpath, _dirnames, filenames in os.walk(root, topdown=False):
            for name in filenames:
                if name.endswith(".pkl"):
                    try:
                        os.remove(os.path.join(dirpath, name))
                    except Exception:
                        pass
            if dirpath != root and not os.listdir(dirpath):
                try:
                    os.rmdir(dirpath)
                except Exception:
                    pass
        return moved

    def job(self, job_id):
        return self._jobs.get(job_id)

    def jobs(self):
        return sorted(self._jobs.values(), key=lambda x: x["created"], reverse=True)

    def list_files(self):
        root = self.cm.work_dir
        if not os.path.isdir(root):
            return []
        out = []
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                ext = os.path.splitext(name)[1].lower()
                if ext not in VALID_AUDIO_EXTS:
                    continue
                full = os.path.join(dirpath, name)
                lossless = ext in _LOSSLESS_EXT or (ext == ".m4a" and _is_lossless_m4a(full))
                stem = os.path.splitext(full)[0]
                # 同名的压缩版本（m4a / mp3）
                compressed_path = None
                if lossless:
                    for cand in (stem + ".m4a", stem + ".mp3"):
                        if os.path.exists(cand):
                            compressed_path = os.path.relpath(cand, root)
                            break
                # 同名的歌词文件
                lrc_path = None
                for cand in (stem + ".lrc", stem + ".txt"):
                    if os.path.exists(cand):
                        lrc_path = os.path.relpath(cand, root)
                        break
                out.append(
                    {
                        "path": os.path.relpath(full, root),
                        "name": name,
                        "size": os.path.getsize(full),
                        "mtime": os.path.getmtime(full),
                        "format": "lossless" if lossless else "lossy",
                        "compressed_path": compressed_path,
                        "lrc_path": lrc_path,
                    }
                )
        return sorted(out, key=lambda x: x["mtime"], reverse=True)
