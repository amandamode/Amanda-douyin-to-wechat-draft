# 贡献指南

感谢你愿意让这个技能变得更好。这份文档说明怎么改、怎么提、怎么发。

## 目录

- [环境准备](#环境准备)
- [本地开发](#本地开发)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [红线：绝对不能提交的东西](#红线绝对不能提交的东西)
- [版本与发布](#版本与发布)
- [报告问题](#报告问题)

## 环境准备

```bash
git clone https://github.com/amandamode/Amanda-douyin-to-wechat-draft.git
cd Amanda-douyin-to-wechat-draft

# Python 依赖
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 系统依赖
#   ffmpeg        brew install ffmpeg / apt install ffmpeg
#   Google Chrome 用于抓流（脚本用 channel="chrome" 驱动系统 Chrome）

# 微信凭证（复制模板并填真实值，勿提交）
mkdir -p ~/.workbuddy/secrets
cp config.example.env ~/.workbuddy/secrets/wechat-mp.env
```

## 本地开发

改完必跑这三条自检，再提 PR：

```bash
# 1. 脚本语法
python3 -m py_compile scripts/push_draft.py scripts/grab_stream.py

# 2. 包结构与元信息合规
grep -E "^(name|display_name|description|version|author):" SKILL.md
grep -rn "/Users/" . --exclude-dir=.git     # 必须无输出：不能有本机绝对路径

# 3. 脚本帮助可跑
python3 scripts/push_draft.py --help
python3 scripts/grab_stream.py --help
```

修改 `SKILL.md` 正文时注意：

- `@references/xxx.md` 引用的文件必须真实存在
- `description` 要写**确定性触发场景**（含触发词），不要写「可能/也许/万能」这类模糊词——平台审核会据此驳回
- `version` 用语义化版本（见下）

## 提交规范

用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat: 新增能力
fix: 修 bug
docs: 只改文档
refactor: 不改行为的重构
chore: 构建/配置/杂项
```

正文写清「改了什么 + 为什么」，尤其是抖音/微信接口变动这类外部依赖变化。

## Pull Request 流程

1. 从 `main` 切分支：`git checkout -b feat/xxx`
2. 改动 + 自检 + `git commit`
3. 推送：`git push -u origin feat/xxx`
4. 开 PR，描述里写：**改了什么 / 为什么 / 怎么验证的 / 是否影响用户**
5. 维护者 review 后合并到 `main`

改动涉及抓流、微信接口、版式这三块时，PR 里**必须附一次真实跑通的证据**（视频 ID、字数、图片数、草稿 media_id），否则不予合并。

## 红线：绝对不能提交的东西

| 红线 | 说明 |
|---|---|
| **微信凭证** | AppID/AppSecret 一律不进仓库。仓库里有 `config.example.env` 模板，真实值放本地或 CI secret |
| **本机绝对路径** | 不能出现用户目录绝对路径（macOS 的 `~/Users/…`、Linux 的 `~/home/…` 这类写法）。配置一律走环境变量或 `--env` |
| **他人视频内容** | 不要把别人的口播逐字稿、他人账号信息写进仓库或示例 |
| **AI 生成配图** | 配图与封面必须真实摄影，禁用 AI 生图（这是内容铁律） |
| **生成产物** | `*.zip`、`__pycache__/`、模型缓存、音频与视频中间件都不提交（已写进 `.gitignore`） |

## 版本与发布

语义化版本：

| 变更 | 版本位 |
|---|---|
| 修 bug、改文案 | PATCH `1.2.1` |
| 新增功能、扩依赖 | MINOR `1.3.0` |
| 破坏性变更（参数改名、目录结构变化） | MAJOR `2.0.0` |

发布流程：

1. 更新 `SKILL.md` 的 `version` 与 `CHANGELOG.md`
2. `git commit -am "release: v1.3.0"` + `git tag -a v1.3.0 -m "v1.3.0"` + `git push --tags`
3. 重新打包 zip（首层为技能目录且含 `SKILL.md`），上传开放平台更新

## 报告问题

请开 issue，并附上：

- 操作系统与 Python 版本
- 你执行的完整命令
- 完整报错（不要只贴最后一行）
- 若涉及抓流失败：贴 `scripts/grab_stream.py` 输出的 `method` 字段（是 `performance` / `currentSrc` / `html-scan` / `blob`）
- **不要贴任何密钥**，贴前先打码
