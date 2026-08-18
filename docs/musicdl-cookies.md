# musicdl Cookie 字段速查表

来源：[musicdl Clients 官方文档](https://musicdl.readthedocs.io/en/latest/Clients.html)

> 通用传参方式（CLI）：
> `musicdl -m <ClientName> -i "{'<ClientName>': {'default_search_cookies': 'COOKIES'}}"`
>
> cookie 支持字典 `{"k": "v", ...}` 或字符串 `k=v; k2=v2` 两种格式。

---

## 明确指定必需字段的客户端

### AppleMusicClient

- **必需字段**：`media-user-token`
- 示例：`{"media-user-token": "xxx"}`
- 说明：
  - 不配置 cookie 时只能下载 30–90 秒预览片段，不能下完整曲目
  - 仅用 subscriber cookie 时，最高音质为 `aac-legacy`
  - 想下更高音质（如 `alac`）需要搭建 [wrapper server](https://github.com/WorldObservationLog/wrapper)
  - 依赖工具：FFmpeg、N_m3u8DL-RE（wrapper 模式还需 Bento4、amdecrypt）

### DeezerMusicClient

- **必需字段**：`arl`
- 示例：`{"arl": "xxx"}` 或 `arl=xxx; ...`
- 说明：
  - 若不配置，只能下载约 30 秒预览片段
  - 非 Deezer Premium 订阅账号的 cookie 只能下载 128 kbps

### QobuzMusicClient

- **必需字段**：`x-user-auth-token`
- 示例：`{"x-user-auth-token": "xxx", ...}` 或 `x-user-auth-token=xxx; ...`
- 说明：其他字段可选；可用官方脚本 [build_cookies_for_qobuz.py](https://github.com/CharlesPikachu/musicdl/blob/master/scripts/build_cookies_for_qobuz.py) 一键生成

### SoundCloudMusicClient

- **必需字段**：`oauth_token`、`client_id`
- 示例：`{"oauth_token": "OAuth xxx", "client_id": "xxx"}`
- 说明：`oauth_token` 若从自己账号的 Web 客户端抓取，则必须同时提供对应的 `client_id`
- 依赖工具：FFmpeg、N_m3u8DL-RE、Bento4

### TIDALMusicClient

- **必需字段**：`access_token`、`refresh_token`、`expires`、`user_id`、`country_code`、`client_id`、`client_secret`
- 示例：
  ```json
  {
    "access_token": "xxx",
    "refresh_token": "xxx",
    "expires": "2026-02-10T07:32:18.102233",
    "user_id": 12345,
    "country_code": "SG",
    "client_id": "7m7Ap0JC9j1cOM3n",
    "client_secret": "xxx"
  }
  ```
- 说明：免费注册账号的 cookie 即可（内置会员账号）；推荐用官方脚本 [build_cookies_for_tidal.py](https://github.com/CharlesPikachu/musicdl/blob/master/scripts/build_cookies_for_tidal.py) 生成
- 依赖工具：FFmpeg、N_m3u8DL-RE、Bento4

### SodaMusicClient

- **必需字段**：`cookies`（字符串）、`device_id`、`x_helios`、`x_medusa`
- 示例：
  ```python
  SODA_MUSIC_REQUIRED_COOKIES = {
    'cookies': 'ttwid=1|fqVX...; passport_csrf_token=...; sessionid=...; ...',
    'device_id': 'xxx',
    'x_helios': 'xxx',
    'x_medusa': 'xxx',
  }
  ```
- 说明：cookie 必须从 **Soda Music 桌面版** 的网络请求中抓取；作者推荐用 [Reqable](https://reqable.com/zh-CN/) 抓包

### MOOVMusicClient

- **必需字段**：`MOOVUUID`、`MTGSESSIONID`
- 示例：`MOOVUUID=7A1DA713-6CC7-461F-91BD-595DF18C159F; MTGSESSIONID=xxx`

### BodianMusicClient

- **必需字段**：`uid`、`token`、`dev_id`
- 示例：`{"uid": "xxx", "token": "xxx", "dev_id": "xxx-xxx-xxx-xxx-xxx"}`
- 说明：仅接受此 VIP 会员 cookie 格式，可从 Bodian 音乐桌面客户端或手机 App 抓包获取

### KugouMusicClient

- **必需字段**：`KUGOU_API_GUID`、`KUGOU_API_MID`、`KUGOU_API_MAC`、`KUGOU_API_DEV`、`token`、`userid`、`dfid`
- 示例：
  ```python
  {
    'KUGOU_API_GUID': 'xxx',
    'KUGOU_API_MID': 'xxx',
    'KUGOU_API_MAC': 'xxx',
    'KUGOU_API_DEV': 'xxx',
    'token': 'xxx',
    'userid': 'xxx',
    'dfid': 'xxx',
  }
  ```
- 说明：直接从网页复制的酷狗会员 cookie 容易出问题，官方推荐用脚本 [build_cookies_for_kugou.py](https://github.com/CharlesPikachu/musicdl/blob/master/scripts/build_cookies_for_kugou.py) 生成有效 cookie

### JooxMusicClient

- **未在文档中列出具体字段**
- 说明：官方提供脚本 [build_cookies_for_joox.py](https://github.com/CharlesPikachu/musicdl/blob/master/scripts/build_cookies_for_joox.py)，填入自己的 premium 账号凭据即可生成 musicdl 所需格式的 cookie

---

## 文档仅用 "YOUR_COOKIES" 占位（无明确字段限制）

以下客户端在文档中只写了 `default_search_cookies: 'YOUR_COOKIES'`，未指定具体字段。通常直接传入浏览器登录后的完整 cookie 即可（登录态 cookie 一般足够）：

| 客户端 | 备注 |
| --- | --- |
| NeteaseMusicClient | 登录后浏览器 cookie（含 `MUSIC_U` 等） |
| QQMusicClient | 登录后 cookie；需含登录凭据字段才能下高音质 |
| KuwoMusicClient | 内置会员账号，可不用 cookie |
| MiguMusicClient | 登录后 cookie |
| QianqianMusicClient | 登录后 cookie |
| BilibiliMusicClient | 登录后 cookie |
| FiveSingMusicClient | 登录后 cookie |
| SpotifyMusicClient | 内置会员账号 |

---

## 夸克网盘 Cookie（quark_parser_config）

聚合/小众下载站（MyFreeMP3、Buguyy、Fangpi、FiveSong、Gequbao、Gequhai、KKWS、LivePOO、LiziYY、MGMP3、Mitu、Sgogo、Xiageba、XMFWAV、Yinyuedao 等）的部分搜索结果会落到夸克网盘分享链接。**不配置夸克网盘 Cookie 时，这类源只能下载 MP3，无法下载更高清（如 FLAC）文件**；配置后即可解析网盘链接下载更高音质。

- **传参方式**：在客户端配置中加入 `quark_parser_config: {"cookies": "..."}`：
  ```
  musicdl -m MyFreeMP3MusicClient -i "{'MyFreeMP3MusicClient': {'quark_parser_config': {'cookies': 'Your Quark Drive Login Cookies'}}}"
  ```
- **Cookie 内容**：登录 https://pan.quark.cn 后的完整浏览器 Cookie，支持 `{"k": "v", ...}` 或 `k=v; k2=v2` 两种格式
- **说明**：
  - 夸克网盘登录 Cookie 为各聚合站共用，本工具在「Cookie 管理」中提供统一的「夸克网盘」条目，保存后自动应用到上述所有聚合站源
  - 可在浏览器登录 https://pan.quark.cn 后，用「一键导入全部 Cookie」或单源「导入」自动读取
  - 参考官方 Clients 文档：MyFreeMP3MusicClient / BuguyyMusicClient / FangpiMusicClient / FiveSongMusicClient / GequbaoMusicClient / GequhaiMusicClient / KKWSMusicClient / LivePOOMusicClient / LiziYYMusicClient / MGMP3MusicClient / MituMusicClient / SgogoMusicClient / XiagebaMusicClient / XMFWAVMusicClient / YinyuedaoMusicClient

---

## 相关官方脚本汇总

| 脚本 | 用途 |
| --- | --- |
| [build_cookies_for_kugou.py](https://github.com/CharlesPikachu/musicdl/blob/master/scripts/build_cookies_for_kugou.py) | 生成酷狗会员 cookie |
| [build_cookies_for_qobuz.py](https://github.com/CharlesPikachu/musicdl/blob/master/scripts/build_cookies_for_qobuz.py) | 生成 Qobuz 订阅 cookie |
| [build_cookies_for_tidal.py](https://github.com/CharlesPikachu/musicdl/blob/master/scripts/build_cookies_for_tidal.py) | 生成 TIDAL 账号 cookie |
| [build_cookies_for_joox.py](https://github.com/CharlesPikachu/musicdl/blob/master/scripts/build_cookies_for_joox.py) | 生成 JOOX 账号 cookie |
