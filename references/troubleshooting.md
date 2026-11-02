# 排错清单（已知限制）

本文件是 SKILL.md「已知限制」的详细排错。按现象自查。

## 1. 微信 API 报 40164（IP 不在白名单）

现象：调 `token` 或 `draft/add` 返回 `40164`。
原因：公众号后台「开发信息 → API IP 白名单」未包含当前出口 IP。
处理：
- 把报错里的出口 IP 加入白名单（管理员扫码），等待生效后再跑。
- **或走路线 B（免白名单）**：用 agent-browser 打开 `mp.weixin.qq.com` → 点 iframe 中的「微信快捷登录」（可用 snapshot ref 直接 `click`，如 `agent-browser click e18`）→ 登录态记住后，改用 `scripts/push_draft.py` 的浏览器侧推送路径（路线 B 不依赖 IP 白名单）。

> 出口 IP 可能漂移（每次重连变），若白名单段兜底仍触发 40164，优先试路线 B。

## 2. 抓流 URL 失效（403 / 404）

现象：下载返回 403，或 `agent-browser eval` 取到的 URL 拼进 curl 报 404。
原因：
- **签名时效**：抖音流地址分钟级过期，拿到要**立刻下载**。
- **引号坑**：`agent-browser eval` 返回包着 JSON 引号，必须剥离再拼（见 `transcribe.md` 2b）。
- **Referer**：下载必须带 `-e "https://www.douyin.com/"`，否则 403。

## 3. 抓不到流地址

现象：performance / currentSrc / 搜 HTML 三条路轮流失败。
原因：抖音页面结构变动（MSE 流、广告素材干扰）。
处理：按 `transcribe.md` 优先级 **performance 找 audio 流 > currentSrc > 搜 HTML** 依次试；`currentSrc` 返回 `blob:` 时直接跳到搜 HTML。

## 4. 凭证缺失 / 格式错误

现象：`push_draft.py` 报 `WECHAT_APPID` 未设置或 token 获取失败。
处理：
- 确认环境变量 `WECHAT_APPID` / `WECHAT_SECRET` 已设置，或用 `--env` 指向含 `WECHAT_APPID=...` / `WECHAT_SECRET=...` 的文件。
- 凭证来自公众号后台「开发信息」，**切勿提交到仓库**。

## 5. 推送后摘要/封面不对

现象：脚本自检显示 ✅，但草稿箱里摘要是乱码或封面缺失。
处理：**推完自己回读一次**，跟预期值比（别只信脚本自检）：

```bash
python3 - <<'PY'
import sys,re
sys.path.insert(0, "scripts")
# 用 urllib 直接调 draft/get；此处示意，实际请按 push_draft.py 的 token 获取方式
PY
```

`push_draft.py` 末尾会打印具体的回读核验命令，照着跑即可。核验项：标题、摘要原文是否一致、封面 `thumb_media_id` 是否存在、正文图片数量。

## 6. 体积超限

现象：`draft/add` 失败或图片不显示。
处理：HTML 整体控制在 ≤900 KB；单张正文图 ≤300 KB（直接跟图库要成品尺寸，别二次压）。
