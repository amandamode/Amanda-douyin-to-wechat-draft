# 排错清单（已知限制）

本文件是 SKILL.md「已知限制」的详细排错。按现象自查。

## 1. 微信 API 报 40164（IP 不在白名单）

现象：调 `token` 或 `draft/add` 返回 `40164 invalid ip ... not in whitelist`。
原因：公众号后台「开发信息 → API IP 白名单」未包含当前出口 IP。
处理：**唯一解法是把出口 IP 加入白名单**（公众号后台，管理员扫码），等生效后重跑。
本包的 `push_draft.py` 走的是官方 API（`cgi-bin/draft/add`），**没有免白名单的浏览器侧通道**，
不要指望换个调用方式绕开。出口 IP 可能漂移（代理/重连会变），可先查当前 IP 再加白名单。

## 2. 抓流 URL 失效（403 / 404）

现象：下载返回 403，或取到的 URL 拼进 curl 报 404。
原因：
- **签名时效**：抖音流地址分钟级过期，拿到要**立刻下载**。
- **引号坑**：脚本输出是 JSON，取 `url` 字段时剥掉引号（见 `transcribe.md` 2c）。
- **Referer**：下载必须带 `-e "https://www.douyin.com/"`，否则 403。

## 3. 抓不到流地址

现象：performance / currentSrc / 搜 HTML 三条路轮流失败。
原因：
- 抖音页面结构变动（走 MSE 时流是 `blob:`）。
- **headless 被风控**：脚本默认 headed，加 `--headless` 更容易失败。
- **`agent-browser` 不存在**：本包已改用 `scripts/grab_stream.py`（Playwright + 系统 Chrome）。

处理：按 `transcribe.md` 的三条路径依次试（performance 音频流 / currentSrc / 搜 HTML），
`currentSrc` 返回 `blob:` 时跳到搜 HTML；三条都失败就换 headed 重试，或请用户直接提供视频文件。

## 4. 凭证缺失 / 格式错误

现象：`push_draft.py` 报 `WECHAT_APPID` 未设置或 token 获取失败。
处理：
- 确认环境变量 `WECHAT_APPID` / `WECHAT_SECRET` 已设置，或用 `--env` 指向含 `WECHAT_APPID=...` / `WECHAT_SECRET=...` 的文件。
- 凭证来自公众号后台「开发信息」，**切勿提交到仓库**。

## 5. 找不到图片 / 封面不对

现象：报「找不到图片 xxx（对应占位符 IMG_xx）」，或草稿箱里封面缺失。
原因与处理：
- **文件名必须是 `images/01.jpg` ~ `images/04.jpg`**（不是 `IMG_01.jpg`）。
- 封面必须**预先压到 ≤100KB**（脚本不压缩），建议 900×383；压法见 `image-selection.md`。
- 草稿箱封面显示异常时，确认封面用的是 `material/add_material` 拿到的 `thumb_media_id`。

## 6. 推送后摘要/封面不对

现象：脚本自检显示 ✅，但草稿箱里摘要是乱码或封面缺失。
处理：**推完自己回读一次**，跟预期值比（别只信脚本自检）：

```python
import json, re, urllib.request
env = {}
for line in open("<你的 .env>", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k.strip()] = v.strip()
tok = json.load(urllib.request.urlopen(
    f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential"
    f"&appid={env['WECHAT_APPID']}&secret={env['WECHAT_SECRET']}", timeout=30))["access_token"]
req = urllib.request.Request(
    f"https://api.weixin.qq.com/cgi-bin/draft/get?access_token={tok}",
    data=json.dumps({"media_id": "<MEDIA_ID>"}).encode(),
    headers={"Content-Type": "application/json"})
a = json.load(urllib.request.urlopen(req, timeout=30))["news_item"][0]
c = a["content"]
print("标题:", a["title"], "| 字数:", len(a["title"]), "(上限 64)")
print("摘要:", a["digest"], "| 字数:", len(a["digest"]), "(上限 120)")
print("正文图:", c.count("mmbiz.qpic.cn"), "张 | 残留 base64:", c.count("base64"), "(必须 0)")
print("正文字数:", len(re.findall(r"[\u4e00-\u9fff]", c)))
```

> 注意 `urllib.request.urlopen` 传 `headers` 必须用 `Request` 对象，直接传会报
> `unexpected keyword argument 'headers'`。

## 7. 体积超限

现象：`draft/add` 失败或图片不显示。
处理：HTML 整体控制在 ≤900 KB；单张正文图 ≤300 KB（直接跟图库要成品尺寸，别二次压）。

## 8. 脚本不压缩，微信自己会压

正文图走 `media/uploadimg` 拿到的是 `mmbiz.qpic.cn` 外链，微信侧会自行压缩；
但**封面**走 `material/add_material`，上传多大就存多大，务必自己先压。

## 9. 2026-11-02 完整实跑基线（可作为对照）

| 环节 | 实测值 |
|---|---|
| 视频 | 70.4 秒 / 720×1280 / 11.79 MB |
| 取流 | `video.currentSrc` 命中（performance 未命中音频流） |
| 转写 | faster-whisper small 离线，27 段 / 328 字 / 21 秒完成 |
| 配图 | 4 张 900×506，共 199 KB |
| 封面 | 2350×1000 → 900×383，68.7 KB |
| 推送 | 标题 24 字、摘要 54 字、正文 477 汉字、正文图 4 张、残留 base64 = 0 |
