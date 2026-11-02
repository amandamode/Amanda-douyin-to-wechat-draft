# 抖音口播转公众号草稿箱（douyin-to-wechat-draft）

把一条抖音口播视频，端到端转成微信公众号图文草稿：**提取逐字稿 → 润色 → 配真实摄影图 → 推送草稿箱**。

一个**自包含** skill：装上即用，不依赖任何私有 skill、也不依赖 `agent-browser` 这类外部命令行工具。

> 本 skill 推到的是**草稿箱**，最终**发布需你在公众号后台手动点**（个人主体订阅号无群发 API 权限）。

| 元信息 | 值 |
|---|---|
| 技能标识（平台 slug） | `douyin-to-wechat-draft`（全平台唯一，发布后不可改） |
| 版本 | 1.2.0 |
| 作者 | Amanda |
| 许可证 | MIT |
| 仓库 | https://github.com/amandamode/Amanda-douyin-to-wechat-draft |
| 适用平台 | WorkBuddy（macOS / Linux / Windows）· 抖音网页版 · 微信公众号公众平台 |
| 依赖运行时 | Python 3.9+ · ffmpeg · Google Chrome · faster-whisper 模型 |

## 功能特性

- **逐字稿提取**：浏览器内取流 → ffmpeg 转码 → faster-whisper **本地**转写（音频不出本机）
- **同音错字修正**：内置中文错字规律表；拿不准的词用**切片 + 多提示词对照复听**判定，不瞎猜
- **口语转书面润色**：保留原意与第一人称，**不扩写**（70 秒口播 ≈ 450–550 字成稿）
- **真实摄影配图**：4 张 Pexels 照片构成一条视觉暗线（**禁用 AI 生图**，内容铁律）
- **移动端版式**：内联样式、图片 base64 内嵌、**0 外链**（微信屏蔽外链）
- **一键推草稿箱**：`push_draft.py` 走官方 API，末尾打印 `MEDIA_ID` 并给出回读核验代码
- **配置外置**：密钥只在你本地，仓库里只有占位符模板

## 安装

### 方式一：WorkBuddy 客户端（推荐）

1. 从 [开放平台](https://open.workbuddy.cn) 技能市场搜索 `douyin-to-wechat-draft` 安装
2. 或把本目录软链到 skills 目录：

```bash
ln -s "$(pwd)/douyin-to-wechat-draft" ~/.workbuddy/skills/douyin-to-wechat-draft
```

> ⚠️ **不要**与自有的 `douyin-to-wechat-pipeline` 同时激活：两者触发词重叠，
> 会导致 Agent 行为不确定，并可能向同一草稿箱推重复内容。二选一，或让触发词互斥。

### 方式二：源码使用

```bash
git clone https://github.com/amandamode/Amanda-douyin-to-wechat-draft.git
cd Amanda-douyin-to-wechat-draft
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**系统依赖**：`ffmpeg`（音频转码）、`Google Chrome`（抓流所需）。
脚本用 `channel="chrome"` 驱动系统 Chrome，**不需要** `playwright install` 下载内核。

## 配置

### 唯一必配项：微信开发凭证

获取路径：**公众号后台 → 设置与开发 → 开发管理 → 开发接口管理 → 基本配置**
（AppSecret 点「重置」后可见，**只显示一次**）。

```bash
mkdir -p ~/.workbuddy/secrets
cp config.example.env ~/.workbuddy/secrets/wechat-mp.env
$EDITOR ~/.workbuddy/secrets/wechat-mp.env
```

```ini
WECHAT_APPID=wx0000000000000000
WECHAT_SECRET=your-app-secret-here
WECHAT_API_BASE=https://api.weixin.qq.com   # 可选，一般不改
WECHAT_ACCOUNT=你的公众号名称                # 可选，仅日志标注
```

**填写位置与优先级**

| 配置项 | 必填 | 填写位置 | 优先级 |
|---|---|---|---|
| `WECHAT_APPID` / `WECHAT_SECRET` | ✅ | 环境变量 → `--env` 文件 → `config.example.env` 模板 | 环境变量最高 |
| `WECHAT_API_BASE`（**API 地址**） | ⭕ | `--api-base` 参数 → 环境变量 → `--env` 文件 | 命令行最高 |
| `WECHAT_ACCOUNT` | ⭕ | `--env` 文件 | — |

**切勿把真实凭证提交到仓库或上传到技能市场**；`config.example.env` 只含占位符，可以公开。
详细字段与接口说明见 [`references/api-spec.md`](references/api-spec.md)。

## 调用示例

**对话触发**（安装后在 WorkBuddy 里直接说）：

```
把这个抖音链接推到公众号草稿箱：https://v.douyin.com/XXXXXX/
润色后发公众号：https://v.douyin.com/YYYYYY/
一鱼两吃，把我这条口播转成公众号文章
这个视频讲了什么？给我逐字稿          ← 只走到逐字稿，不推草稿箱
```

**手动调脚本**：

```bash
# 取流 + 拿作者信息
python3 scripts/grab_stream.py <VIDEO_ID>

# 推送
python3 scripts/push_draft.py \
  --html article_raw.html \
  --cover cover.jpg \
  --images-dir images \
  --author "你的作者名" \
  --digest "最想被转发的那句，≤120字" \
  --env ~/.workbuddy/secrets/wechat-mp.env
```

完整场景与一次真实跑通记录见 [`references/examples.md`](references/examples.md)。

## 目录结构

```
douyin-to-wechat-draft/
├── SKILL.md                      # ★ 技能定义（frontmatter + 步骤 + 元信息）
├── README.md                     # 本文件
├── LICENSE                       # MIT
├── CONTRIBUTING.md               # 贡献指南（本地开发 / 提交规范 / 敏感信息红线）
├── CHANGELOG.md                  # 变更记录
├── requirements.txt              # 依赖声明（Playwright / faster-whisper）
├── config.example.env            # 配置模板（含 API 地址占位符，无密钥）
├── .gitignore
├── references/                   # 详细实现（SKILL.md 用 @references/ 引用各 .md）
│   ├── transcribe.md             # 抓流 + 转写 + 错字修正
│   ├── image-selection.md        # 配图与封面（命名与压缩硬约定）
│   ├── html-template.md          # 公众号版式 + base64 注入
│   ├── troubleshooting.md        # 排错清单 + 回读核验代码 + 实跑基线
│   ├── api-spec.md               # 微信 API 规范 + 关键配置项填写位置
│   ├── examples.md               # 使用示例 + 实跑记录
│   └── faq.md                    # 常见问题
├── scripts/                      # 可执行脚本
│   ├── grab_stream.py            # 浏览器内取流（Playwright + 系统 Chrome）
│   └── push_draft.py             # 推送草稿箱（仅标准库）
└── templates/
    └── article_raw.html          # 正文模板（IMG_01..IMG_04 占位符 + <h1>）
```

## 发布

### WorkBuddy 开放平台

1. 将 `douyin-to-wechat-draft/` 目录压缩为 zip，**确保 `SKILL.md` 位于压缩包第一层**
   （即 zip 内第一层是 `douyin-to-wechat-draft/` 且该目录内含 `SKILL.md`）
2. 打开 [open.workbuddy.cn](https://open.workbuddy.cn) → 添加技能 → 创建技能 → 上传 zip
3. 填写市场展示名称、能力介绍、分类与服务类目 → 提交审核（通常 1–3 个工作日）

**规范注意**
- `name`（slug）为 `douyin-to-wechat-draft`，**全平台唯一、发布后不可改**，上传前先确认未被占用
- `description` 必须写**确定性触发场景**，不得含「可能 / 也许 / 万能」等模糊词（会驳回）
- 脚本不得含「下载后执行」、不得读取系统敏感目录；`push_draft.py` 仅用标准库调微信 API
- 密钥不上传，仅由使用者本地配置

### GitHub

仓库：https://github.com/amandamode/Amanda-douyin-to-wechat-draft
（命名遵循作者约定：所有开源 skill 仓库统一加 `Amanda-` 前缀；平台 slug 不加前缀，两套命名互不影响）

```bash
# 1. 初始化
git init -b main
git remote add origin https://github.com/amandamode/Amanda-douyin-to-wechat-draft.git

# 2. 提交
git add -A
git commit -m "feat: v1.2.0 — 补齐依赖声明、配置模板、API 规范、示例与 FAQ"

# 3. 打标签
git tag -a v1.2.0 -m "v1.2.0"

# 4. 推送
git push -u origin main
git push origin v1.2.0
```

## 许可证

MIT —— 见 [LICENSE](./LICENSE)。贡献流程见 [CONTRIBUTING.md](./CONTRIBUTING.md)。
