# MusicPlayground 🎵

基于 [musicdl](https://github.com/CharlesPikachu/musicdl) 的网页版音乐搜索 / 下载 / 歌单工具，参考 [musicsquare](https://github.com/CharlesPikachu/musicsquare) 的交互方式构建，并针对本地使用做了增强。

## ✨ 功能特性

- 🔍 **网页搜索**：在浏览器中搜索音乐，支持多平台（Apple Music、网易云、QQ 音乐、酷我、酷狗、咪咕等，取决于 musicdl 已安装的 source）
- 📜 **歌单下载**：粘贴歌单链接，自动识别平台并直接调用对应源解析，批量下载所有曲目
- 💾 **双下载模式**：
  - **最高音质**：用当前 cookie 下载最高可用音质（网易云 VIP 出 FLAC，Apple 出 AAC-Legacy）
  - **FLAC→AAC**：下载无损后用 ffmpeg 转 AAC-LC 256kbps（`.m4a`），**同时保留无损原件**
- 🔁 **智能去重**：下载前检查本地是否已有相同歌曲 ID 的文件，有则跳过不重复下载；已有无损时若存在 AAC 版则直接复用，不重复转换
- 🗂️ **自动整理**：下载后的文件按 `downloads/<来源>/<歌单名或搜索词>/` 结构归位，歌词（.lrc）等附属文件一并移动，重复下载自动合并
- 📥 **文件页分格式下载**：无损文件可分别下载 FLAC 原版 / 压缩版（M4A/MP3，无则现场转换）/ 歌词
- 📋 **任务明细**：每个下载任务可展开，显示每首歌状态（下载中 / 转换中 / 已有文件 / 已有无损已转 / 失败等）
- 📜 **运行日志**：内置日志查看页，实时展示 musicdl 运行日志
- 🍪 **Cookie 管理**：手动录入 + 从浏览器自动导入（含一键导入全部）；Cookie 录入区只显示官方文档支持 Cookie 的源
- 🎶 **在线试听**：对支持的音乐源直接试听（Apple Music 提供预览片段）
- 🖥️ **本地运行**：基于本地 Python 与 musicdl，不依赖第三方 bridge API

## 🧱 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python + Flask，封装 [musicdl](https://github.com/CharlesPikachu/musicdl) |
| 前端 | 原生 HTML / CSS / JavaScript（单页，参考 musicsquare） |
| 浏览器 Cookie | [rookiepy](https://pypi.org/project/rookiepy/) |
| 转码 / 下载工具 | ffmpeg、N_m3u8DL-RE（Apple Music 需要） |

## 📦 安装

```bash
# 1. 安装 Python 依赖（musicdl / flask / rookiepy）
pip install -r requirements.txt

# 2. 下载转码 / 流媒体工具（macOS 示例）
brew install ffmpeg
# N_m3u8DL-RE 手动下载安装，并保证在 PATH 中：
#   https://github.com/nilaoda/N_m3u8DL-RE/releases
```

> ⚠️ musicdl 的部分源需要打补丁才能正常工作（例如 Apple 源解析无歌词歌曲时可能崩溃），请根据你的 musicdl 版本按需修复。

## 🚀 启动

```bash
pip install -r requirements.txt
python app.py

# 打开 http://127.0.0.1:5001
```

## 🍪 Cookie 配置

在网页的「Cookie 设置」面板中，为每个音乐源录入 Cookie，支持三种方式。Cookie 录入区只显示**官方文档明确支持 Cookie 的 24 个源**（Apple、网易云、QQ、酷我、酷狗、咪咕、千千、Deezer、Qobuz、SoundCloud、TIDAL、Soda、MOOV、Bodian、JOOX、B站、5sing 等）；Spotify / YouTube / 喜马拉雅等官方不支持 Cookie 录入的源不在此列。各源所需字段见 [docs/musicdl-cookies.md](docs/musicdl-cookies.md)。

**方式一：一键导入全部（推荐）**
在「一键导入全部 Cookie」栏选择浏览器后点击按钮，会自动遍历所有**启用中**的音乐源，从浏览器读取各网站已登录的 Cookie 并**直接保存生效**（无需逐个操作），结束后显示各源导入数量汇总。
- 需先在该浏览器中登录对应网站（如 Apple Music 的 https://music.apple.com）
- 各源对应的域名已内置映射（Apple → `.apple.com`、网易云 → `.163.com` 等）
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

> ⚠️ `media-user-token` 等登录凭据会过期，过期后需重新从浏览器获取并在网页中更新。

## 💾 下载与格式

在搜索结果或歌单中勾选歌曲后，可点击两个按钮之一：

| 按钮 | 行为 |
| --- | --- |
| 下载选中（最高音质） | musicdl 用当前 cookie 下最高可用音质 |
| 下载选中（FLAC→AAC） | 下载最高音质后，用 ffmpeg 转为 AAC-LC 256kbps（`.m4a`），保留无损原件 |

**下载去重**：提交任务时会先检查目标目录是否已有相同歌曲 ID 的文件：
- 最高音质模式：已有即跳过
- FLAC→AAC 模式：已有无损则直接转 AAC（若已有 AAC 则完全跳过），不重复下载

## 🗂️ 文件整理

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

同名歌曲自动去重合并；旧版本（带时间戳前缀的目录）可用「任务 / 文件」页的**整理现有文件**按钮一键迁移。

## 📥 文件页下载

「任务 / 文件」页每个文件根据格式显示不同按钮：

| 文件类型 | 可用按钮 |
| --- | --- |
| FLAC / ALAC 等无损 | `下载FLAC` `压缩版` `歌词` |
| M4A / MP3 等有损 | `下载` `歌词` |

- **压缩版**：已有同曲 M4A/MP3 直接下载；没有则现场转换并保留
- **歌词**：下载同名 `.lrc` 文件

## 📋 下载任务

「任务 / 文件」页的每个任务**默认展开**，显示每首歌的状态明细：
`下载中` → `转换中` → `完成` / `完成（FLAC + AAC）` / `已有文件` / `已有无损已转 AAC` / `已有压缩版` / `失败`

## 📜 运行日志

顶部「日志」标签页实时展示 `~/Library/Logs/musicdl/musicdl.log` 最近内容，支持自动刷新与手动刷新，错误/警告自动高亮。

## 📜 使用歌单下载

在网页「歌单解析」中输入 Apple Music 歌单链接，例如：

```
https://music.apple.com/cn/playlist/cello/pl.u-KVXBkAPIzEpA5P
```

点击解析即可列出全部曲目，选择后一键批量下载。

## 🛠️ 项目结构

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

> `config.json` 与 `downloads/` 为运行时生成，已加入 `.gitignore`。

## 📄 免责声明

本工具仅供个人学习与合法使用。请遵守所在国家/地区的法律法规，仅下载拥有合法权限的音乐内容。Cookie 属于敏感凭据，请勿将 `config.json` 提交到公开仓库。
