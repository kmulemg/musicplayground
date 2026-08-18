# MusicPlayground

基于 [musicdl](https://github.com/CharlesPikachu/musicdl) 的网页版音乐搜索 / 下载 / 歌单工具，参考 [musicsquare](https://github.com/CharlesPikachu/musicsquare) 的交互方式构建，并针对本地使用做了增强。

## 功能特性
- **网页搜索**：在浏览器中搜索音乐，支持多平台（Apple Music、网易云、QQ 音乐、酷我、酷狗、咪咕等，取决于 musicdl 已安装的 source）
- **歌单下载**：粘贴歌单链接，自动识别平台并直接调用对应源解析，批量下载所有曲目
- **双下载模式**：
- **最高音质**：用当前 cookie 下载最高可用音质（网易云 VIP 出 FLAC，Apple 出 AAC-Legacy）
- **FLAC→AAC**：下载无损后用 ffmpeg 转 AAC-LC 256kbps（`.m4a`），**同时保留无损原件**
- **智能去重**：下载前检查本地是否已有相同歌曲 ID 的文件，有则跳过不重复下载；已有无损时若存在 AAC 版则直接复用，不重复转换
- **自动整理**：下载后的文件按 `downloads/<来源>/<歌单名或搜索词>/` 结构归位，歌词（.lrc）等附属文件一并移动，重复下载自动合并
- **文件页分格式下载**：无损文件可分别下载 FLAC 原版 / 压缩版（M4A/MP3，无则现场转换）/ 歌词
- **任务明细**：每个下载任务可展开，显示每首歌状态（下载中 / 转换中 / 已有文件 / 已有无损已转 / 失败等）
- **运行日志**：内置日志查看页，实时展示 musicdl 运行日志
- **Cookie 管理**：手动录入 + 从浏览器自动导入（含一键导入全部）；Cookie 录入区只显示官方文档支持 Cookie 的源
- **在线试听**：对支持的音乐源直接试听（Apple Music 提供预览片段）
- **本地运行**：基于本地 Python 与 musicdl，不依赖第三方 bridge API

## 官方文档（参考）

| 文档 | 链接 |
| --- | --- |
| 文档首页 | https://musicdl.readthedocs.io/en/latest/ |
| 快速上手 | https://musicdl.readthedocs.io/en/latest/Quickstart.html |
| 音乐源（Clients） | https://musicdl.readthedocs.io/en/latest/Clients.html |
| API 参考 | https://musicdl.readthedocs.io/en/latest/API.html |
| 安装说明 | https://musicdl.readthedocs.io/en/latest/Install.html |
| 更新日志 | https://musicdl.readthedocs.io/en/latest/Changelog.html |
| 源码仓库 | https://github.com/CharlesPikachu/musicdl |

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python + Flask，封装 [musicdl](https://github.com/CharlesPikachu/musicdl) |
| 前端 | 原生 HTML / CSS / JavaScript（单页，参考 musicsquare） |
| 浏览器 Cookie | [rookiepy](https://pypi.org/project/rookiepy/) |
| 转码 / 下载工具 | ffmpeg、N_m3u8DL-RE（Apple Music 需要） |

## 安装

```bash
# 1. 安装 Python 依赖（musicdl / flask / rookiepy）
pip install -r requirements.txt

# 2. Apple Music 下载依赖（macOS）
brew install ffmpeg
# N_m3u8DL-RE 手动下载安装，并保证在 PATH 中：
# https://github.com/nilaoda/N_m3u8DL-RE/releases
```

## 启动

```bash
# 使用 Homebrew Python（已装 musicdl 并打了补丁）
/opt/homebrew/bin/python3.11 app.py

# 或先安装依赖再启动
pip install -r requirements.txt
python app.py

# 打开 http://127.0.0.1:5001
```

## Cookie 配置

在网页的「Cookie 设置」面板中，为每个音乐源录入 Cookie，支持三种方式。Cookie 录入区只显示**官方文档明确支持 Cookie 的源**（Apple、网易云、QQ、酷我、酷狗、咪咕、千千、Deezer、Qobuz、SoundCloud、TIDAL、Soda、MOOV、Bodian、JOOX、B站、5sing 等，另含「夸克网盘」用于聚合站更高清下载）；Spotify / YouTube / 喜马拉雅等官方不支持 Cookie 录入的源不在此列。各源所需字段见 [docs/musicdl-cookies.md](docs/musicdl-cookies.md)。

**方式一：一键导入全部（推荐）**
在「一键导入全部 Cookie」栏选择浏览器后点击按钮，会自动遍历所有**启用中**的音乐源，从浏览器读取各网站已登录的 Cookie 并**直接保存生效**（无需逐个操作），结束后显示各源导入数量汇总。
- 需先在该浏览器中登录对应网站（如 Apple Music 的 https://music.apple.com）
- 常见音乐源的域名已内置映射（Apple → `.apple.com`、网易云 → `.163.com`、TIDAL → `.tidal.com` 等），未映射的源会导入该浏览器**全部** Cookie 后自动筛选
- 如果使用 **Safari**，需要先在「系统设置 → 隐私与安全性 → 完全磁盘访问权限」中给终端授权

**方式二：单个源导入**
每个音乐源旁有「导入」按钮，选择浏览器（Chrome / Firefox / Edge / Safari / Brave / Opera / Vivaldi），即可自动读取该源在浏览器中已登录的 Cookie 并填入文本框，点击「保存」后生效。

**方式三：手动粘贴**
- **AppleMusicClient**：`{"media-user-token": "xxx"}`，获取方式：
 1. 打开 https://music.apple.com 并登录
 2. 开发者工具 → Application → Cookies → `https://music.apple.com`
 3. 复制 `media-user-token` 的值
- **NeteaseMusicClient**：网页登录后复制 Cookie
- **QQMusicClient / KuwoMusicClient / KugouMusicClient** 等：同理，均支持手动录入

**夸克网盘 Cookie（聚合下载站更高清）**
列表底部还有「夸克网盘」条目：登录 https://pan.quark.cn 后复制浏览器 Cookie 填入保存（或直接「导入」/「一键导入全部」自动读取）。保存后会自动应用到 MyFreeMP3、Buguyy、Fangpi、FiveSong、Gequbao、Gequhai、KKWS、LivePOO、LiziYY、MGMP3、Mitu、Sgogo、Xiageba、XMFWAV、Yinyuedao 等聚合下载站源的 `quark_parser_config`，不配置时这些源只能下载 MP3。字段要求见 [docs/musicdl-cookies.md](docs/musicdl-cookies.md)。

### 当前配置的 Apple Music Cookie

```
media-user-token: xxx（真实值见 config.json，勿提交到公开仓库）
```

即：

```json
{
  "AppleMusicClient": {
    "media-user-token": "xxx"
  }
}
```

> `media-user-token` 会过期，过期后需重新从浏览器获取并在网页中更新。

## 下载与格式

在搜索结果或歌单中勾选歌曲后，可点击两个按钮之一：

| 按钮 | 行为 |
| --- | --- |
| 下载选中（最高音质） | musicdl 用当前 cookie 下最高可用音质 |
| 下载选中（FLAC→AAC） | 下载最高音质后，用 ffmpeg 转为 AAC-LC 256kbps（`.m4a`），保留无损原件 |

**下载去重**：提交任务时会先检查目标目录是否已有相同歌曲 ID 的文件：
- 最高音质模式：已有即跳过
- FLAC→AAC 模式：已有无损则直接转 AAC（若已有 AAC 则完全跳过），不重复下载

## 文件整理

下载完成后文件自动归入 `downloads/<来源>/<歌单名或搜索词>/` 目录（方案：歌单优先）：

```
downloads/
├── AppleMusicClient/
│   └── KTV/                                  ← 歌单名
│       ├── 给自己的歌 (Live) - 1173734841.m4a
│       └── 给自己的歌 (Live) - 1173734841.lrc  ← 歌词跟随音频
└── NeteaseMusicClient/
    └── 押忍!闘え!応援団/
        ├── サムライブルー - 22819802.flac
        └── サムライブルー - 22819802.m4a      ← 转 AAC 后无损与压缩版并存
```

同名歌曲自动去重合并。

## 文件页下载

「任务 / 文件」页每个文件根据格式显示不同按钮：

| 文件类型 | 可用按钮 |
| --- | --- |
| FLAC / ALAC 等无损 | `下载FLAC` `压缩版` `歌词` |
| M4A / MP3 等有损 | `下载` `歌词` |
- **压缩版**：已有同曲 M4A/MP3 直接下载；没有则现场转换并保留
- **歌词**：下载同名 `.lrc` 文件

## 下载任务

「任务 / 文件」页的每个任务**默认展开**，显示每首歌的状态明细：
`下载中` → `转换中` → `完成` / `完成（FLAC + AAC）` / `已有文件` / `已有无损已转 AAC` / `已有压缩版` / `失败`

## 运行日志

顶部「日志」标签页实时展示 `~/Library/Logs/musicdl/musicdl.log` 最近内容，支持自动刷新与手动刷新，错误/警告自动高亮。

## 使用歌单下载

在网页「歌单解析」中输入 Apple Music 歌单链接，例如：

```
https://music.apple.com/cn/playlist/cello/pl.u-KVXBkAPIzEpA5P
```

点击解析即可列出全部曲目，选择后一键批量下载。

## 项目结构

```
musicplayground/
├── app.py                  # Flask 后端入口（API 路由）
├── backend/
│   ├── cookie_manager.py   # Cookie 与音乐源配置管理（config.json）
│   ├── browser_cookies.py  # 自动从浏览器读取 Cookie（基于 rookiepy）+ 官方 Cookie 支持源清单
│   └── service.py          # musicdl 封装（搜索/歌单/下载任务/去重/转码/整理/文件列表）
├── static/
│   ├── index.html          # 前端页面
│   ├── style.css           # 样式
│   └── app.js              # 前端逻辑
├── docs/
│   └── musicdl-cookies.md  # 官方文档各音乐源 Cookie 字段速查
├── downloads/              # 下载文件（运行时生成，按 来源/歌单名 整理）
├── config.json             # Cookie 与下载配置（运行时生成）
├── requirements.txt
└── README.md
```

> 本机已对 `musicdl` 打补丁修复无歌词歌曲解析崩溃的问题（`modules/sources/apple.py` 第119行），
> 需使用 Homebrew 的 Python 3.11（`/opt/homebrew/bin/python3.11`）运行，以复用已安装的 musicdl 与已打补丁的代码。

## GitHub 发布

本目录是**本地开发/使用副本**（非 git 仓库）；对外发布走独立的发布副本，仓库地址：

> **https://github.com/kmulemg/musicplayground**

### 发布流程

1. **更新发布副本**：把修改过的文件从本目录同步到发布副本 `musicplayground-release`：
   ```bash
   cp -R app.py backend static docs requirements.txt LICENSE README.md /path/to/musicplayground-release/
   rm -rf /path/to/musicplayground-release/backend/__pycache__
 ```
2. **提交并推送**：
   ```bash
   cd /path/to/musicplayground-release
   git add -A
   git commit -m "your message"
   git push
 ```

### 发布注意
- **敏感文件不发布**：`config.json`（含真实 Cookie / media-user-token）、`downloads/`、`__pycache__/` 等已在 `.gitignore` 中忽略，**切勿手动加回**
- **README 脱敏**：发布副本的 README 不含本地真实的 `media-user-token`，仅保留获取方法示例
- **License**：与上游 [musicdl](https://github.com/CharlesPikachu/musicdl) 一致，采用 [PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0)（仅限非商业用途），详见发布仓库的 `LICENSE` 与「License」章节

## 免责声明

本工具仅供个人学习与合法使用。请遵守所在国家/地区的法律法规，仅下载拥有合法权限的音乐内容。Cookie 属于敏感凭据，请勿将 `config.json` 提交到公开仓库。

## 更新日志

### 2026-08-18 · 终止服务功能

** 新增：终止服务按钮**
- 设置页「服务」区域新增「终止服务」按钮，与「重启服务」并列
- 点击后弹出确认对话框，确认后优雅关闭服务进程
- 终止后提示用户手动刷新页面或关闭页面

### 2026-08-18 · Bug 修复与健壮性改进

** 修复：任务页文件下载链接损坏**
- 下载任务完成后，任务卡片中的文件下载链接只保留了文件名（`.pop()`），丢失了目录结构（如 `AppleMusicClient/歌名/song.flac`），导致下载接口返回 400
- 后端 `job["files"]` 改为存储相对于 `work_dir` 的路径，前端用完整相对路径构造下载 URL，显示名仍为纯文件名

** 修复：Python 依赖版本比较 `~=`（compatible release）逻辑错误**
- 原实现 `cur >= ver and cur[0] == ver[0]` 不符合 PEP 440，例如 `~=1.4.2` 会错误放行 `1.5.0`
- 改为 `cur >= ver and cur < upper`，其中 `upper` 为版本号截断末位后末位 +1（如 `~=1.4.2` → `<1.5`，`~=1.4` → `<2`，`~=1` → `<2`）

** 修复：依赖版本缓存永不过期**
- `_pypi_latest` 中 `_DEPS_CACHE_TTL`（10 分钟）从未被检查，已缓存的版本直到进程重启才会刷新
- 加入 TTL 判断，过期后自动重新请求 PyPI

** 修复：Cookie / 源变更时绕过锁直接置空客户端**
- `set_cookies`、`delete_cookies`、`import_all_cookies` 三个端点直接赋值 `service._client = None`，绕过了 `MusicService._lock`，下载线程可能读到半构建的客户端实例
- 新增 `MusicService.reset_client()` 方法，在锁内原子清空 `_client` 和 `_client_cfg_hash`

** 修复：内存持续增长无上限**
- `_library`（搜索/歌单结果缓存）和 `_jobs`（下载任务记录）无清理机制，长时间运行后内存持续增长
- 新增 `_trim_library(max_entries=200)` 和 `_trim_jobs(max_entries=50)`，每次写入后自动淘汰最旧条目

### 2026-08-18 · 夸克网盘 Cookie 支持 + 聚合下载站修复

** 新增：夸克网盘 Cookie 配置**
- 「设置 → Cookie 管理」新增「夸克网盘」条目（虚拟源 `QuarkMusicClient`，域名映射 `pan.quark.cn` / `.quark.cn`，支持手动粘贴、单源导入、一键导入全部）
- 保存后自动注入到 15 个聚合下载站源的 `quark_parser_config`（MyFreeMP3 / Buguyy / Fangpi / FiveSong / Gequbao / Gequhai / KKWS / LivePOO / LiziYY / MGMP3 / Mitu / Sgogo / Xiageba / XMFWAV / Yinyuedao），不配置时这些源只能下载 MP3
- 对应字段说明已同步至 [docs/musicdl-cookies.md](docs/musicdl-cookies.md)

** 修复：未配置夸克 Cookie 时搜索整体崩溃**
- FiveSong / KKWS / LiziYY / Xiageba 这 4 个源在 musicdl 中以 `assert` 硬性要求 `quark_parser_config`，未配置时连客户端构造都会抛异常，导致所有源的搜索 / 歌单解析整体失败
- 现在未配置夸克 Cookie 时自动跳过这 4 个源（搜索恢复正常，其余聚合站降级为仅 MP3）；配置夸克 Cookie 后自动重建并启用，无需重启
- 前端在搜索结果上方提示被跳过的源，设置页源列表对这些源显示「待配夸克」虚线标签

** 修复：全局 request_overrides 导致部分源搜索失败**
- 移除对所有源全局注入的 `headers` / `timeout` 覆盖
- musicdl 会将 `request_overrides` 以 `**kwargs` 展开到 `get/post`，而 TwoT58 / ITingWa / GDStudio / TuneHub / JBSou 等源自身又显式传 `headers=` / `timeout=`，触发 `got multiple values for keyword argument 'timeout'/'headers'`，整批源搜索失败

** 已知站点侧限制（非本工具问题）**
- **403 Forbidden**：TwoT58 / Gequbao / Fangpi（站点反爬拦截）
- **DNS 解析失败**：Zhuolin（`music.zhuolin.wang` 域名已失效）
- **404**：LivePOO（播放页 URL 返回 404）
- **429 限流**：LiziYY（并发搜索触发频控）
- **2026-08-17**：搜索结果 / 歌单结果支持按 **歌曲、歌手、专辑、时长、大小** 客户端排序。点击表头切换升序 / 降序 / 恢复原始顺序，当前排序列高亮并显示方向箭头。
