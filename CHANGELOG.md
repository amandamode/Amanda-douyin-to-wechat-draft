# 变更记录

本文件记录每个版本的改动，便于回溯与审核。

## v1.2.1 — 2026-11-02

开放平台审核驳回修复（评级结论「内置文件缺失」）。

### 修复
- `references/examples.md`：移除对已迁出独立技能 `douyin-to-transcript` 的 `transcribe.py`
  字面引用（平台扫描 examples.md 发现引用文件不存在 → 判定「资产包缺少必需资源」）。
  改为指向本包真实存在的 `references/transcribe.md`，并提示转写脚本已独立为 `douyin-to-transcript` 技能
- `README.md` / `CONTRIBUTING.md`：把说明性占位 `references/xxx.md` 改为不带路径 token 的写法，
  规避字面路径被平台扫描误判为缺失文件
- `SKILL.md` / `README.md`：`version` → 1.2.1

## v1.2.0 — 2026-11-02

### 新增
- `requirements.txt`：依赖声明（Playwright / faster-whisper；说明 push_draft.py 仅用标准库）
- `config.example.env`：配置模板，含 **API 基地址 `WECHAT_API_BASE`** 的填写说明
- `CONTRIBUTING.md`：贡献指南（本地开发、自检命令、提交规范、敏感信息红线、版本与发布流程）
- `CHANGELOG.md`：本文件
- `references/api-spec.md`：微信 API 调用规范 + 关键配置项填写位置 + 错误码对照
- `references/examples.md`：使用示例与一次完整实跑记录
- `references/faq.md`：常见问题

### 变更
- `scripts/push_draft.py`：新增 `--api-base` 参数，API 基地址优先级为
  **命令行 > 环境变量 `WECHAT_API_BASE` > `--env` 文件 > 默认 `https://api.weixin.qq.com`**
- `SKILL.md`：正文新增元信息块（适用平台、仓库地址、许可证、版本、依赖一览）；`version` → 1.2.0
- `README.md`：补全功能特性、安装与配置、调用示例、目录结构、仓库地址、发布说明
- `.gitignore`：补充虚拟环境、模型缓存、音频/视频中间件、编辑器与系统文件

## v1.1.0 — 2026-11-02

一次真实实跑后补齐的链路缺口。

### 新增
- `scripts/grab_stream.py`：用 Playwright 驱动系统 Chrome 在页面内取流，
  **替代本机并不存在的 `agent-browser` 命令**，使技能真正自包含

### 变更
- `references/transcribe.md`：整篇重写——记录抖音三条官方死路
  （`_ROUTER_DATA` 已无 `playAddr`、`iteminfo` 返回 0 字节、`detail` 被 `ArgusSecurityPlugin` 拦）；
  三条取流路径由「performance 优先」改为**并列**；新增切片多提示词对照复听法；新增 5 条同音错字
- `references/image-selection.md`：新增「文件命名与压缩」章节（`01.jpg`~`04.jpg` 硬约定、封面 ≤100KB 压缩代码）、
  蒙太奇批量看图法、避免同主题相邻两张重复的避坑
- `references/troubleshooting.md`：纠正 40164 条（移除并不存在的「免白名单路线 B」）；
  新增「找不到图片 / 封面不对」；补可直接运行的 `draft/get` 回读代码；新增实跑基线对照表
- `SKILL.md` / `README.md`：依赖表与已知限制同步

## v1.0.0 — 2026-11-02

首个发布版。

- 抖音链接 → 视频 ID → 浏览器内取流 → ffmpeg 转码 → faster-whisper 转写 → 同音错字修正
- 口语转书面润色（保留原意与第一人称、不扩写）
- Pexels 真实摄影配图（4 张，视觉暗线成篇）+ 封面
- 移动端版式 HTML（内联样式、base64 内嵌、0 外链）
- `scripts/push_draft.py` 一键推送至微信公众号草稿箱并回读核验
