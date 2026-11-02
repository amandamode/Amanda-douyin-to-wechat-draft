# 抖音视频 → 逐字稿（转写链路）

本文件是 SKILL.md 步骤 2–3 的详细实现。用户发来抖音分享链接要「逐字稿」时，用这条链路把口播转成文字。**不需要用户提供任何额外东西**，全程约 2–4 分钟（首次要下模型）。

## 不要走的路（已验证失败）

| 方案 | 结果 |
|---|---|
| `yt-dlp <抖音链接>` | ❌ `Fresh cookies (not necessarily logged in) are needed` |
| curl 抓分享页 HTML | ❌ JS 渲染，拿不到内容 |
| 页面 `<video>` 标签的 src | ❌ 是 `blob:` MSE 流，无法下载 |

## 正确链路

### 1. 拿到视频 ID 和作者

```bash
curl -s -o /dev/null -w "%{url_effective}\n" -L -m 20 \
  -A "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15" \
  "https://v.douyin.com/XXXXXX/"
# → https://www.iesdouyin.com/share/video/<VIDEO_ID>/?...
```

作者昵称、点赞数、发布时间都在 **meta description** 里，用 agent-browser 取：

```bash
agent-browser open "https://www.iesdouyin.com/share/video/<VIDEO_ID>/"
agent-browser eval "Array.from(document.querySelectorAll('meta')).map(m=>(m.getAttribute('name')||m.getAttribute('property')||'')+' = '+(m.getAttribute('content')||'')).filter(x=>/description/i.test(x)).join('\n')"
```

> ⚠️ **首次打开常是 `chrome-error://chromewebdata/` + `ERR_PROXY_CONNECTION_FAILED`**。
> 别急着换方法，先 `agent-browser close` 再重开一次就好。开完 `agent-browser eval "location.href"`
> 确认已跳到 `www.douyin.com/video/<ID>`，**没跳转时取 meta 会得到空字符串**。

meta description 里含「`<标题>` - `<作者昵称>`于`YYYYMMDD`发布在抖音，已经收获了`N`个喜欢」。
**这一步很关键**：用它判断这是不是用户自己的号（涉及版权，是别人视频的话不要直接搬）。

### 2. 抓流地址（核心技巧）

**首选：从 performance 里挖纯音频流 `media-audio-und-mp4a`**

```bash
# 先静音播一下，资源才会进 performance
agent-browser eval "var v=document.querySelector('video'); v?(v.muted=true, v.play(), 'playing dur='+v.duration):'no-video'"
sleep 8
agent-browser eval "performance.getEntriesByType('resource').map(e=>e.name).filter(n=>/media-audio-und-mp4a/.test(n)).pop()"
```

拿到的是**纯音频**，265 秒视频只有 **2.1 MB**（对比完整视频流十几 MB），下载和转码都快一大截。
同一次播放里还会有 `media-video-avc1`（视频）——**别选它**。

**回退一：`<video>.currentSrc`**（完整视频流）

```bash
agent-browser eval "document.querySelector('video').currentSrc"
```

**回退二：直接在页面 HTML 里正则搜**

```bash
agent-browser eval "var s=new Set(); (document.documentElement.innerHTML.match(/https:[^\"'\\s]*douyinvod[^\"'\\s]*/g)||[]).forEach(function(u){s.add(u.replace(/&amp;/g,'&'))}); Array.from(s).join('\n')"
```

> ⚠️ 三条路都要试，别只认一条：
> - performance 抓不到 douyinvod（走 MSE）时 → 回退 currentSrc
> - currentSrc 返回 `blob:`（MSE）时 → 回退搜 HTML
>
> 顺序建议：**performance 找 audio 流 > currentSrc > 搜 HTML**。

### 2b. 取 URL 的引号坑（不处理必 404）

`agent-browser eval` 的返回值外面包着 JSON 引号，直接拼进 curl 会 404。先剥掉：

```bash
PY=python3
URL=$(agent-browser eval "document.querySelector('video').currentSrc" 2>/dev/null | $PY -c "import sys,json;raw=sys.stdin.read().strip();
try: print(json.loads(raw))
except Exception: print(raw.strip('\"'))")
```

### 3. 立刻下载（URL 有签名时效）

```bash
curl -s -L -m 180 -o audio.mp4 \
  -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -e "https://www.douyin.com/" "<上一步的 URL>"
```

**必须带 Referer**，否则 403。

### 4. 转码

```bash
ffmpeg -y -loglevel error -i audio.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le audio.wav
```

### 5. 转写（faster-whisper）

首次安装：

```bash
python3 -m venv "$HOME/.venvs/whisper" && "$HOME/.venvs/whisper/bin/pip" install -q -U faster-whisper
```

跑：

```bash
HF_ENDPOINT=https://hf-mirror.com "$HOME/.venvs/whisper/bin/python" - <<'PY'
from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8")
segments, info = model.transcribe(
    "audio.wav", language="zh", beam_size=5,
    vad_filter=False,                        # ← 必须 False，见下方坑
    initial_prompt="以下是普通话口播视频的逐字稿。",
)
out = []
for s in segments:
    out.append(s.text.strip())
print("".join(out))
PY
```

## 两个必须记住的坑

### 1. `vad_filter=True` 会直接崩

报错：`ImportError: ... onnxruntime_pybind11_state.so ... built for macOS 13.4 which is newer than running OS`。
`onnxruntime`（VAD 依赖）编译目标比本机 macOS 新，装不上也修不了。**`vad_filter=False` 即可绕过**——VAD 只影响静音切分，转写主体不依赖它。代价：静音段可能产生少量幻觉文本，看一遍删掉即可。

### 2. 模型下载要挂镜像

`HF_ENDPOINT=https://hf-mirror.com`，否则 huggingface.co 大概率超时。`small` 模型约 460 MB，CPU 转写速度约为音频时长的 0.5–1 倍（150 秒音频约 1.5 分钟）。

> **模型下载超时**：`small` 走镜像实测可能要 5–8 分钟，直接前台跑「下载+转写」易撞 Bash 9 分钟超时被 SIGTERM。正确姿势：先用 `huggingface_hub.snapshot_download("Systran/faster-whisper-small")`（挂镜像、前台 10 分钟超时）把模型单独下完，再跑转写；转写本身 167s 音频只要 1–2 分钟。
>
> **snapshot_download 抽风修复**：镜像 API 间歇性返回空会报 `LocalEntryNotFoundError`，但 model.bin 往往已完整落盘。修复：把缺的小文件直接下进 snapshot 目录，再改成传本地路径 `WhisperModel(<snapshot_dir>, ...)` 并设 `HF_HUB_OFFLINE=1` 彻底避开网络。

## 转写完必做：同音错字修正

Whisper 的中文错字有固定套路，**逐字稿不能直接用**，至少过一遍：

| 常见错写 | 正确 |
|---|---|
| 牛城 / 行程（视语境） | 行程 |
| 垫赋 | 垫付 |
| 十成大海 | 石沉大海 |
| 高兴兼职 | 高薪兼职 |
| 体验室 | 体验师 |
| 食品（在招聘语境） | 直聘 |
| 何都而不为 | 何乐而不为 |
| 出门站外 | 出门在外 |
| 人事安全 | 人身安全 |
| 经济分享出来 | 经历分享出来 |
| 我的我妈 | 我和我妈 |
| 外摊大会 | 外滩大会 |
| 真正「之前」 | 真正「值钱」 |
| 特别「内」 | 特别「累」 |
| 祖先家庭 | 组建家庭 |
| 按部就班的路 | 按部就班的路 |
| 被树立为榜样 | 被树立为榜样 |
| 天专家瓦 | 添砖加瓦 |
| 长暗 | 惨案 |
| 热终于制造 | 热衷于制造 |

规律：**同音不同调、近音词、专有名词**最容易错。带 `initial_prompt` 提示主题能减少一部分。

### 语音彻底还原不出来的怎么办

有些错字听不出原词，**不要瞎猜硬填**：

1. 优先按上下文**改写整句**绕开那个词（保住意思，放弃原词）
2. 在交付时**明确列出存疑处**，让用户自己回忆原话
3. 绝不假装听清了
