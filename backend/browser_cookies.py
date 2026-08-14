import rookiepy

# 官方文档（https://musicdl.readthedocs.io/en/latest/Clients.html）明确提供
# "with login cookies" 用法示例、支持 cookie 录入的音乐源
COOKIE_SUPPORTED_SOURCES = {
    "AppleMusicClient",
    "AudiusMusicClient",
    "BilibiliMusicClient",
    "BodianMusicClient",
    "CCMixterMusicClient",
    "DeezerMusicClient",
    "FiveSingMusicClient",
    "FMAMusicClient",
    "JamendoMusicClient",
    "JioSaavnMusicClient",
    "JooxMusicClient",
    "KugouMusicClient",
    "KuwoMusicClient",
    "MiguMusicClient",
    "MOOVMusicClient",
    "NeteaseMusicClient",
    "QianqianMusicClient",
    "QQMusicClient",
    "QobuzMusicClient",
    "SodaMusicClient",
    "SoundCloudMusicClient",
    "StreetVoiceMusicClient",
    "SunoMusicClient",
    "TIDALMusicClient",
}


SOURCE_DOMAINS = {
    "AppleMusicClient": [".apple.com"],
    "NeteaseMusicClient": ["music.163.com", ".163.com"],
    "QQMusicClient": ["y.qq.com", ".qq.com"],
    "KuwoMusicClient": [".kuwo.cn"],
    "KugouMusicClient": [".kugou.com"],
    "MiguMusicClient": ["music.migu.cn", ".migu.cn"],
    "QianqianMusicClient": ["music.91q.com", ".91q.com"],
    "DeezerMusicClient": [".deezer.com"],
    "SoundCloudMusicClient": [".soundcloud.com"],
    "BilibiliMusicClient": [".bilibili.com"],
    "SodaMusicClient": [".douyin.com"],
    "JooxMusicClient": [".joox.com"],
    "QobuzMusicClient": [".qobuz.com"],
    "TIDALMusicClient": [".tidal.com"],
    "MOOVMusicClient": [".moov.hk"],
    "BodianMusicClient": ["bodian.kuwo.cn", ".kuwo.cn"],
    "FiveSingMusicClient": ["5sing.kugou.com", ".kugou.com"],
    "StreetVoiceMusicClient": [".streetvoice.cn"],
    "SunoMusicClient": ["suno.com", ".suno.com"],
    "JioSaavnMusicClient": [".jiosaavn.com"],
}

BROWSERS = ["chrome", "firefox", "edge", "safari", "brave", "opera", "vivaldi"]


def domains_for(source):
    return SOURCE_DOMAINS.get(source, [])


def extract_cookies(source, browser):
    domains = domains_for(source)
    fn = getattr(rookiepy, browser, None)
    if fn is None:
        raise ValueError(f"unsupported browser: {browser}")

    raw = None
    if domains:
        try:
            raw = fn(domains=domains)
        except Exception:
            raw = None
    if raw is None:
        raw = fn()

    cookies = {}
    for c in raw or []:
        name, value, domain = c.get("name"), c.get("value"), (c.get("domain") or "").lstrip(".")
        if not name or value is None:
            continue
        if domains and domain and not any(
            d.lstrip(".") == domain or domain.endswith("." + d.lstrip(".")) or d.lstrip(".").endswith("." + domain)
            for d in domains
        ):
            continue
        cookies[name] = value
    return cookies
