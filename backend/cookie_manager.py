import json
import os


DEFAULT_SOURCES = [
    "AppleMusicClient",
    "NeteaseMusicClient",
    "QQMusicClient",
    "KuwoMusicClient",
    "MiguMusicClient",
    "KugouMusicClient",
    "QianqianMusicClient",
]

DEFAULT_WORK_DIR = "downloads"


class CookieManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.data = self._default()
        self.load()

    def _default(self):
        return {"sources": list(DEFAULT_SOURCES), "work_dir": DEFAULT_WORK_DIR, "cookies": {}}

    def load(self):
        if not os.path.exists(self.config_path):
            self.save()
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            default = self._default()
            default.update(data if isinstance(data, dict) else {})
            self.data = default
        except Exception:
            self.data = self._default()

    def save(self):
        with open(self.config_path, "w", encoding="utf-8") as fp:
            json.dump(self.data, fp, indent=2, ensure_ascii=False)

    def all_cookies(self):
        return dict(self.data.get("cookies", {}) or {})

    def get(self, source):
        return dict(self.data.get("cookies", {}).get(source, {}) or {})

    def set(self, source, cookies):
        self.data.setdefault("cookies", {})[source] = dict(cookies or {})
        self.save()

    def delete(self, source):
        self.data.setdefault("cookies", {}).pop(source, None)
        self.save()

    @property
    def sources(self):
        return list(self.data.get("sources", DEFAULT_SOURCES))

    def set_sources(self, sources):
        self.data["sources"] = list(sources or [])
        self.save()

    @property
    def work_dir(self):
        return self.data.get("work_dir", DEFAULT_WORK_DIR)

    def set_work_dir(self, work_dir):
        self.data["work_dir"] = str(work_dir or DEFAULT_WORK_DIR)
        self.save()
