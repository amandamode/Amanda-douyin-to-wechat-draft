# 使用示例

本文件给出可直接照做的调用场景，以及一次真实跑通的完整记录。

## 场景一：自己的口播 → 公众号草稿箱（主场景）

**用户视角**：在对话里甩一条链接 + 说一句「推到草稿箱」。

```
把这个抖音链接推到公众号草稿箱：https://v.douyin.com/XXXXXX/
```

**技能会依次完成**：

1. 解析短链拿到 `video_id`，在浏览器里取作者昵称/点赞/发布时间 → 确认是**用户自己的号**（否则停下提醒版权）
2. 页面内取流地址 → 立刻下载（带 Referer）→ ffmpeg 转 16k 单声道 wav
3. faster-whisper 本地转写 → 同音错字修正（拿不准的切片对照复听）
4. 口语转书面润色（**保留原意与第一人称，不扩写**）
5. Pexels 真实摄影配图 4 张（成一条视觉暗线）+ 封面（压到 ≤100KB）
6. 生成移动端版式 HTML（内联样式、base64 内嵌、0 外链）
7. `push_draft.py` 推入草稿箱 → `draft/get` 回读核验
8. 交付：标题、字数、配图逻辑、草稿 media_id，并提醒**手动点发布**

## 场景二：只要逐字稿，不要推草稿箱

```
这个视频讲了什么？给我逐字稿
```

只走到步骤 1–3（取流 + 转写 + 错字修正），**不配图、不推草稿箱**。

## 场景三：别人的视频

```
把这个链接整理成公众号文章：https://v.douyin.com/XXXXXX/
```

技能在步骤 1 会停下来：说明这是他人内容、涉及版权，**不搬运**。
若用户确认拥有授权，请用户明确说明，再继续。

## 手动调用脚本（不走对话触发）

```bash
# 1) 取流 + 拿 meta
python3 scripts/grab_stream.py <VIDEO_ID>
#    输出 {video_id, url, method, meta, video_duration}

# 2) 下载（URL 分钟级过期，拿到立刻下）
curl -s -L -m 180 -o video.mp4 \
  -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36" \
  -e "https://www.douyin.com/" "<上一步的 url>"

# 3) 转码
ffmpeg -y -loglevel error -i video.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le audio.wav

# 4) 转写（模型已缓存时可全离线）
#    转写脚本已独立为 douyin-to-transcript 技能（去该技能 scripts 目录下取转写脚本），
#    或按 references/transcribe.md 在本包内手动跑 faster-whisper

# 5) 推送
python3 scripts/push_draft.py \
  --html article_raw.html --cover cover.jpg --images-dir images \
  --author "你的作者名" --digest "≤120 字的转发语"
```

## 一次真实跑通记录（2026-11-02，已去敏）

| 环节 | 实测 |
|---|---|
| 视频 | 70.4 秒 / 720×1280 / 11.79 MB |
| 取流 | `video.currentSrc` 命中（performance 未命中音频流） |
| 转写 | faster-whisper small 离线，27 段 / 328 字 / 21 秒 |
| 错字修正 | 「我爸我哥」经 4 组提示词对照复听，确认原词是「我哥」；另修 5 处（深讨→声讨、心疯作浪→兴风作浪、送容→容忍、自念供养→自恋供养、作者→做着） |
| 成稿 | 标题 24 字 / 正文 477 汉字 / 摘要 54 字 |
| 配图 | 4 张 900×506，共 199 KB；封面 900×383 → 68.7 KB |
| 推送 | 正文图 4 张全上传，残留 base64 = 0，草稿 media_id 已回读核验 |

**得到的经验**：抖音页面结构与开放接口都会变，脚本必须保留多条取流路径；
封面压缩与图片命名是最容易翻车的两处，务必先读 `references/image-selection.md`。
