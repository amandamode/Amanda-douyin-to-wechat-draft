# 常见问题（FAQ）

更底层的排错见 `troubleshooting.md`。

## 安装与环境

**Q：装完提示找不到 `agent-browser`？**
A：旧版文档里的 `agent-browser` 命令在多数机器上并不存在。v1.1.0 起改用自带的
`scripts/grab_stream.py`（Playwright 驱动系统 Chrome），**不需要额外装任何命令行工具**。

**Q：`playwright install` 要不要执行？**
A：**不要**。脚本用 `channel="chrome"` 驱动你系统里已装的 Google Chrome，
不需要下载浏览器内核（省几百 MB，也避开下载失败）。只需 `pip install playwright`。

**Q：抓流脚本报 `Executable doesn't exist`？**
A：说明它退化成了下载内核模式。确认 `pip install playwright` 装成功、
且系统装有 Google Chrome，然后重跑。

**Q：faster-whisper 报 onnxruntime 符号错误 / `built for macOS 13.4 which is newer than running OS`？**
A：这是 VAD 依赖 `onnxruntime` 装不上。**转写时务必 `vad_filter=False`** 绕过，
不影响转写主体（VAD 只负责静音切分）。

**Q：模型下载卡住？**
A：挂镜像 `HF_ENDPOINT=https://hf-mirror.com`；模型已缓存后可用
`HF_HUB_OFFLINE=1` + 本地 snapshot 路径完全离线跑。

## 抓流

**Q：取不到流地址？**
A：按 `performance` 音频流 → `video.currentSrc` → 页面 HTML 搜 `douyinvod` 三条依次试
（脚本已内置这个顺序）。若 `currentSrc` 返回 `blob:`，说明走 MSE，三条都可能失效——
换 headed 重试（**别用 headless，抖音风控更严**），或请用户直接提供视频文件。

**Q：抖音接口还能直接调吗？**
A：不能了。分享页 `_ROUTER_DATA` 已不含播放地址、`iteminfo` 返回 0 字节、
`detail` 被 `ArgusSecurityPlugin` 拦。只能在真实浏览器里执行 JS 取流。

**Q：下载返回 403？**
A：两个原因——① URL 签名分钟级过期，拿到**立刻**下载；② 少了 Referer，
必须带 `-e "https://www.douyin.com/"`。

## 转写与成稿

**Q：逐字稿里有些词明显不对？**
A：Whisper 中文错字有固定套路（同音不同调、近音词、专有名词），
错字规律表见 `transcribe.md`。**单个存疑处**用切片 + 多提示词对照复听判定；
实在还原不出来的，按原意改写整句绕开它，并在交付时列明存疑处——**不要瞎猜硬填**。

**Q：文章多长合适？**
A：口播 70 秒 ≈ 330 字口语，润色后约 450–550 字；2–3 分钟 ≈ 800 字口语，润色后 550–650 字。
**「润色」是口语转书面，不是扩写**，不要擅自加段落或加内容。

**Q：配图能自己生成吗？**
A：**不能**。配图与封面必须是真实摄影（Pexels 等免费图库），**禁用 AI 生图**——这是内容铁律。

**Q：封面要多大？**
A：微信侧 ≤64 KB 较稳，脚本不压缩，**自己先压**。做法见 `image-selection.md`
（900×383、quality 自适应到 ≤100KB）。

## 推送与草稿箱

**Q：报「找不到图片 xxx（对应占位符 IMG_xx）」？**
A：文件名必须是 `images/01.jpg` ~ `images/04.jpg`（**不是** `IMG_01.jpg`）。

**Q：报 40164？**
A：调用出口 IP 不在公众号后台白名单。**只能加白名单**，本技能没有免白名单通道。
代理/重连会让出口 IP 漂移，加之前先查当前 IP。

**Q：推完了怎么确认真的进去了？**
A：用 `draft/get` 回读 `MEDIA_ID`，核对标题、摘要、`thumb_media_id`、正文图数量、
残留 base64 必须为 0。**别只信脚本自检**。可运行代码见 `troubleshooting.md`。

**Q：能直接发布吗？**
A：不能。本技能只推到**草稿箱**。个人主体订阅号没有群发 API 权限，
最终发布必须用户在公众号后台手动点。

## 内容与合规

**Q：视频不是我的，能用吗？**
A：不搬运。技能在第一步就会识别作者，不是你的号会停下提醒版权风险。

**Q：图文里的字要避讳什么？**
A：标题避免医学惊悚词；正文不使用「赋能 / 重塑 / 杠杆 / 底层 / 维度」这类黑名单词；
破折号少用（AI 味指标之一）；不同公众号还有各自的篇数标注、品牌词规范，
按自己账号规则适配——本技能不内置特定账号规范。

## GitHub 与安装

**Q：怎么装到 WorkBuddy？**
A：把整个技能目录复制或软链到 `~/.workbuddy/skills/` 下，刷新后在对话中即可触发。
注意：**不要**与自有的同名流水线 skill 同时激活（触发词重叠会导致行为不确定、产生重复草稿）。

**Q：平台 `name` 能改吗？**
A：不能。`name`（slug）全平台唯一、**发布后不可改**。GitHub 仓库名不受此限制。
