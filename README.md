# 抖音口播转公众号草稿箱（douyin-to-wechat-draft）

把一条抖音口播视频，端到端转成微信公众号图文草稿：提取逐字稿 → 润色 → 配真实摄影图 → 推送草稿箱。
一个自包含 skill，装上即用，不依赖其他私有 skill。

> 本 skill 推到的是**草稿箱**，最终**发布需你在公众号后台手动点**（个人主体订阅号无群发 API 权限）。

## 功能

- 从抖音分享链接（`v.douyin.com`）提取口播逐字稿（本地 faster-whisper，纯本地、不联网转写）
- 同音错字修正、口语转书面润色（不扩写）
- Pexels 真实摄影配图（**禁用 AI 生图**）
- 移动端版式 HTML + base64 内嵌、0 外链
- `scripts/push_draft.py` 一键推送至微信公众号草稿箱

## 目录结构

```
douyin-to-wechat-draft/
├── SKILL.md                  # 技能定义（官方 frontmatter + 步骤）
├── references/               # 详细实现：转写 / 配图 / HTML模板 / 排错
├── scripts/push_draft.py     # 推送脚本（仅标准库）
├── templates/article_raw.html
├── README.md
└── LICENSE
```

## 前置依赖

| 依赖 | 用途 |
|---|---|
| ffmpeg | 音频转码 |
| faster-whisper | 本地转写（`vad_filter=False`，模型下载挂 `HF_ENDPOINT=https://hf-mirror.com` 镜像） |
| agent-browser | 抓取抖音视频流地址 |
| Python 3 | 运行 `scripts/push_draft.py`（仅标准库，无第三方依赖） |
| 微信凭证 | `WECHAT_APPID` / `WECHAT_SECRET`，来自公众号后台「开发信息」 |

## 凭证配置

推送脚本从以下位置读取凭证（**不内嵌任何密钥**）：

1. 环境变量 `WECHAT_APPID` / `WECHAT_SECRET`
2. 或 `--env` 指定的 `.env` 文件，内容形如：
   ```
   WECHAT_APPID=wxXXXXXXXX
   WECHAT_SECRET=xxxxxxxx
   ```

## 用法

对话中发抖音链接并说「推到草稿箱 / 润色后发公众号 / 一鱼两吃」即可触发 SKILL.md 的步骤。
最后一步调用推送脚本：

```bash
python3 scripts/push_draft.py \
  --html "可粘贴版.html" \
  --cover "cover-2350x1000.jpg" \
  --digest "最想被转发的那句，≤120字" \
  --author "你的作者名" \
  --images-dir "images"
```

查看参数说明：`python3 scripts/push_draft.py --help`

## 本地测试（WorkBuddy）

把整个 `douyin-to-wechat-draft/` 目录复制或软链到 `~/.workbuddy/skills/` 下，重启/刷新后在对话中即可触发：

```bash
ln -s "$(pwd)/douyin-to-wechat-draft" ~/.workbuddy/skills/douyin-to-wechat-draft
```

## 本地安装须知（与自用流水线共存警告）

本技能定位为**发布给他人使用的成品**。若你本机已在用私有的 `douyin-to-wechat-pipeline`（抖音→公众号流水线），**请勿把本目录 symlink / 复制进 `~/.workbuddy/skills/` 与之一同激活**，原因：

- 两者 `description` 在「推到草稿箱」「润色后发公众号」上**触发词高度重叠**，同时安装会导致 Agent 随机选其一，行为不确定。
- 两者都向**同一公众号草稿箱**推送，可能因此产生**重复草稿**。

如需在本地自用本技能，请**二选一**：保留 `douyin-to-wechat-pipeline` 或保留本技能，禁用另一个；或让两者 `description` 触发词互斥。仅发布到市场（见下）不会写入本机 skills 目录，日常流水线不受影响。

## 发布到 WorkBuddy 开放平台

1. 将 `douyin-to-wechat-draft/` 目录压缩为 zip，**确保 `SKILL.md` 位于压缩包根目录**（即 zip 内第一层是 `douyin-to-wechat-draft/` 且该目录内含 `SKILL.md`）。
2. 打开 [open.workbuddy.cn](https://open.workbuddy.cn) → 添加技能 → 创建技能 → 上传 zip。
3. 审核通常 1–3 个工作日。

**平台规范注意：**
- `name`（slug）为 `douyin-to-wechat-draft`，**全平台唯一、发布后不可改**，请确认未占用。
- `description` 必须写确定性触发场景，不得含「可能/也许/万能」等模糊词。
- 脚本不得含「下载后执行」、不得读取系统敏感目录；本 skill 的 `push_draft.py` 仅用标准库调用微信 API，符合审核要求。
- 密钥不上传，仅由使用者本地配置。

## GitHub 开源命名约定

按作者统一规范，**所有开源 skill/插件在 GitHub 仓库名前加 `Amanda-` 前缀**。
因此本项目的 GitHub 仓库名为：

```
Amanda-douyin-to-wechat-draft
```

注意区分两套命名：
- **平台 `name`（slug）**：`douyin-to-wechat-draft`（平台规则，小写连字符，发布后不可改）
- **GitHub 仓库名**：`Amanda-douyin-to-wechat-draft`（作者开源命名约定，可自由设定）

本地目录名可用任意其一；上传平台时 `name` 字段以 SKILL.md 中的 `douyin-to-wechat-draft` 为准。

## 许可证

MIT —— 见 [LICENSE](./LICENSE)。
