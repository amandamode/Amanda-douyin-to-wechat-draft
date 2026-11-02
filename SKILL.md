---
name: douyin-to-wechat-draft
display_name: 抖音口播转公众号草稿箱
display_name_en: Douyin Short-Video to WeChat MP Draft
description: 从抖音/短视频分享链接提取口播逐字稿，润色排版并配真实图片，推送至微信公众号草稿箱。当用户发来 v.douyin.com 链接并要求「推到草稿箱」「润色后发公众号」「一鱼两吃」时使用。
description_zh: 把抖音口播视频一键转成公众号图文草稿：提取逐字稿、润色、配真实摄影图、推送草稿箱。
description_en: Turn a Douyin short-video into a WeChat Official Account draft — transcribe, polish, add real photos, and push to the draft box.
examples_zh:
- "把这个抖音链接推到公众号草稿箱：https://v.douyin.com/XXXXXX/"
- "润色后发公众号：https://v.douyin.com/YYYYYY/"
- "一鱼两吃，把我这条口播转成公众号文章"
examples_en:
- "Push this Douyin link to my WeChat draft: https://v.douyin.com/XXXXXX/"
- "Polish and send to Official Account: https://v.douyin.com/YYYYYY/"
- "Repurpose my short-video into a WeChat article"
version: 1.0.0
author: Amanda
allowed-tools: Bash, Read
---

# 抖音口播 → 微信公众号草稿箱（一鱼两吃流水线）

用户甩一条自己的抖音口播链接，要求「推到草稿箱 / 润色后发公众号 / 一鱼两吃」时，走这条端到端链路。
全程无需用户提供脚本外的任何东西；最终**发布需用户手动点**（个人主体订阅号无 API 发布权限，绕不过）。

## 何时使用

满足以下全部条件时触发：

- 用户发来抖音/短视频分享链接（形如 `v.douyin.com/...` 或 `douyin.com/video/...`）
- 用户明确要求把内容搬到微信公众号（「推到草稿箱」「润色后发公众号」「一鱼两吃」「转成公众号文章」）
- 内容是**用户自己的**口播视频（他人视频涉及版权，不得搬运，见步骤 1）

不适用：纯本地逐字稿需求（不要推草稿箱）请只走到步骤 2–3；非抖音平台请先确认抓取方式。

## 步骤

### 1. 解析链接 + 作者身份确认（版权红线）

短链 `v.douyin.com/XXXX` 先解析出真实 `video_id` 与作者页：

```bash
curl -s -o /dev/null -w "%{url_effective}\n" -L -m 20 \
  -A "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15" \
  "https://v.douyin.com/XXXXXX/"
```

用 agent-browser 打开分享页，从 `meta description` 取作者昵称、点赞数、发布时间（含「`<标题>` - `<作者>`于`YYYYMMDD`发布在抖音，已经收获了`N`个喜欢」）。

- **是用户自己的号** → 继续。
- **是别人的视频** → 停下来，提醒版权风险，**不搬运**。

### 2. 抓流 + 转写 → 逐字稿

完整链路（performance 抓纯音频流 → ffmpeg → faster-whisper → 同音错字修正）见 `@references/transcribe.md`。
这一步产出原始逐字稿文本，是后续所有环节的输入。

### 3. 同音错字修正

Whisper 中文错字有固定套路（同音不同调、近音词、专有名词）。先通读逐字稿，按 `@references/transcribe.md` 的错字规律表过一遍，把存疑处列给用户确认，**绝不瞎猜硬填**。

### 4. 润色成文（关键：不扩写）

「润色」= 保留原意和第一人称、把口语改成书面语，**不是重写、不是扩写**。
口播 2–3 分钟 ≈ 800 字口语 → 润色后约 550–650 字。不要擅自加段落或加内容；想加先问。

> 各公众号有自己的标题/正文规范（如是否标篇数、敏感词规避、品牌词），**使用者按自己账号规则适配**，本 skill 不内置特定账号规范。

### 5. 配图（真实摄影，禁用 AI 生图）

流程与避坑见 `@references/image-selection.md`。铁律：**配图与封面一律真实摄影，禁用 AI 生图**。
选 4 张形成一条视觉暗线（不是随机配图），用 Read 逐张看内容再定。

### 6. 写 HTML + 注入 base64

版式规范与注入方式见 `@references/html-template.md`，套用 `templates/article_raw.html`（含 `IMG_01`..`IMG_04` 占位符与 `<h1>` 标题）。
要求：**内联样式、图片 base64 内嵌、0 外链**（微信屏蔽外链）。

### 7. 生成封面

按 `@references/html-template.md` 的尺寸要求生成 2350×1000 与 1080×1080 两张封面（真实摄影，禁用 AI 生图）。

### 8. AI 味自检（可选）

若已安装 humanizer skill → 调用它报分（如重启号硬门槛 <30）。
未安装 → 用手工检查清单：黑名单词（赋能/重塑/杠杆/底层/维度）、破折号数量、冒号「：」/双引号在正文里的使用、三段以上排比、加粗密度。

### 9. 推送草稿箱

```bash
python3 scripts/push_draft.py \
  --html "可粘贴版.html" \
  --cover "cover-2350x1000.jpg" \
  --digest "最想被转发的那句，≤120字" \
  --author "你的作者名" \
  --images-dir "images"
```

脚本会：注入 base64 → 取 token → 上传正文图 → 传封面拿 `thumb_media_id` → `draft/add`，末尾打印 `MEDIA_ID` 与回读核验命令。
凭证从环境变量 `WECHAT_APPID` / `WECHAT_SECRET` 读取，缺失时回退到 `--env` 指定的 `.env` 文件（默认 `~/.workbuddy/secrets/wechat-mp.env`）。**切勿把密钥写进 skill 或提交到仓库。**

### 10. 回读核验摘要

推完自己回读一次，确认标题/摘要/封面/图片数量符合预期（详见 `@references/troubleshooting.md` 的核验命令）。**不要只信脚本的自检输出。**

### 11. 交付与归档

- 归档：原始 ASR 逐字稿、`audio.wav`、成稿 HTML 留在工作目录（原始素材可追溯）。
- 删除未采用的候选图。
- 回复中给出：标题、正文字数、AI 味分（如有）、配图逻辑、草稿箱状态。
- **提醒用户：发布需手动在公众号后台点**。

## 前置依赖

| 依赖 | 说明 |
|---|---|
| ffmpeg | 音频转码（`-vn -ac 1 -ar 16000 -c:a pcm_s16le`） |
| faster-whisper | 本地转写（`vad_filter=False`，模型下载挂 `HF_ENDPOINT=https://hf-mirror.com` 镜像） |
| agent-browser | 抓抖音视频流地址（见 `@references/transcribe.md`） |
| 微信凭证 | `WECHAT_APPID` / `WECHAT_SECRET`，来自公众号后台「开发信息」；个人主体订阅号无群发 API 权限 |
| Python 3 | 运行 `scripts/push_draft.py`（仅用标准库） |

## 已知限制

- 抓流 URL 有签名时效（分钟级），拿到立刻下载。
- 抖音页面结构会变，抓流失效时回退 `currentSrc`（见 `@references/transcribe.md`）。
- 微信 API 有 IP 白名单，`40164` 表示出口 IP 不在白名单；处理见 `@references/troubleshooting.md`。
- 发布必须用户手动操作，本 skill 只负责推到草稿箱。

详细排错见 `@references/troubleshooting.md`。
