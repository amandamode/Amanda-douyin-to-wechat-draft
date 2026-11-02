# API 规范与关键配置项填写位置

本文件说明本技能调用哪些外部接口、每个关键配置项写在哪里、以及出错时怎么查。

## 一、关键配置项一览（**配置项填写位置**）

| 配置项 | 是否必填 | 写在哪里 | 说明 |
|---|---|---|---|
| `WECHAT_APPID` | ✅ 必填 | ① 环境变量 ② `--env` 指向的文件 ③ `config.example.env` 模板 | 公众号 AppID，形如 `wx` + 16 位十六进制 |
| `WECHAT_SECRET` | ✅ 必填 | 同上 | 公众号 AppSecret，后台只显示一次 |
| `WECHAT_API_BASE` | ⭕ 可选 | ① `--api-base` 参数 ② 环境变量 ③ `--env` 文件 | API 基地址，默认 `https://api.weixin.qq.com`；走代理/网关时才改 |
| `WECHAT_ACCOUNT` | ⭕ 可选 | `--env` 文件 | 公众号名称，仅日志标注，不参与接口调用 |
| `WECHAT_API_BASE` 同上 | — | — | 生效优先级：**命令行 > 环境变量 > `--env` 文件 > 默认值** |

**凭证读取顺序**（`scripts/push_draft.py` 实测逻辑）：

```
appid/secret :  环境变量 WECHAT_APPID/WECHAT_SECRET  →  --env 文件  →  都没有则报错退出
api_base     :  --api-base 参数  →  环境变量  →  --env 文件  →  默认 https://api.weixin.qq.com
```

**推荐做法**：把真实凭证放在技能包**之外**（如 `~/.workbuddy/secrets/wechat-mp.env`），
脚本默认就读这个路径；CI / Docker 里直接注入环境变量，**不要把密钥写进仓库**。

```bash
mkdir -p ~/.workbuddy/secrets
cp config.example.env ~/.workbuddy/secrets/wechat-mp.env
$EDITOR ~/.workbuddy/secrets/wechat-mp.env     # 填入 AppID / AppSecret
```

## 二、调用的接口

| 顺序 | 接口 | 方法 | 用途 | 关键参数 |
|---|---|---|---|---|
| 1 | `{api_base}/cgi-bin/token` | GET | 换取 access_token | `grant_type=client_credential`、`appid`、`secret` |
| 2 | `{api_base}/cgi-bin/media/uploadimg` | POST multipart | 上传**正文图** | `media`（二进制）、返回 `url`（mmbiz 外链） |
| 3 | `{api_base}/cgi-bin/material/add_material` | POST multipart | 上传**封面**永久素材 | `media`、`type=image`，返回 `media_id` |
| 4 | `{api_base}/cgi-bin/draft/add` | POST JSON | 写入草稿箱 | 见下方 payload |
| 5 | `{api_base}/cgi-bin/draft/get` | POST JSON | 回读核验 | `media_id` |

### draft/add 请求体

```json
{
  "articles": [{
    "title":        "≤64 字的标题",
    "author":       "作者名",
    "digest":       "≤120 字的摘要/转发语",
    "content":      "<正文 HTML，图片已是 mmbiz 外链>",
    "thumb_media_id": "<步骤 3 返回的 media_id>",
    "need_open_comment": 0,
    "only_fans_can_comment": 0
  }]
}
```

### 字段约束

| 字段 | 约束 |
|---|---|
| `title` | ≤ 64 字 |
| `digest` | ≤ 120 字 |
| `content` | 整体 ≤ 900 KB（超出 `draft/add` 有失败风险）；正文图必须先上传拿 `url`，不能留 base64 |
| `thumb_media_id` | 必须是**永久素材**的 `media_id`（`material/add_material`），不能用临时素材 |
| 正文图 | 单张 ≤ 300 KB；建议 900×506 |

## 三、返回与错误码

### 正常返回

```json
{ "errcode": 0, "errmsg": "ok", "media_id": "..." }          // draft/add
{ "errcode": 0, "errmsg": "ok", "url": "http://mmbiz..." }   // media/uploadimg
{ "access_token": "...", "expires_in": 7200 }                // token
```

### 常见错误码与处理

| errcode | 含义 | 处理 |
|---|---|---|
| `40164` | 调用 IP 不在白名单 | 公众号后台「开发信息 → API IP 白名单」加入当前出口 IP；**本技能没有免白名单通道**，只能加白名单 |
| `40001` / `40013` | AppSecret / AppID 不正确 | 核对凭证；AppSecret 重置后要同步更新本地配置 |
| `48001` | api unauthorized（未授权该接口） | 确认该公众号类型有草稿箱接口权限 |
| `45009` | 接口调用超过限制 | 稍后重试 |
| `41001` | 缺少 access_token | 检查 token 获取步骤 |

## 四、脚本调用示例

```bash
python3 scripts/push_draft.py \
  --html article_raw.html \
  --cover cover.jpg \
  --images-dir images \
  --author "你的作者名" \
  --digest "最想被转发的那句，≤120字" \
  --env ~/.workbuddy/secrets/wechat-mp.env \
  --api-base https://api.weixin.qq.com
```

- `--env` 不填则默认读 `~/.workbuddy/secrets/wechat-mp.env`
- `--api-base` 不填则按上文优先级回落
- 脚本成功后会打印 `MEDIA_ID=`，用它调 `draft/get` 回读核验

## 五、非微信的外部依赖

| 依赖 | 形态 | 说明 |
|---|---|---|
| 抖音网页 | 浏览器内 JS（`scripts/grab_stream.py`） | 取流地址 + 作者信息；**不调用抖音开放接口**（已全部封死） |
| Pexels | 图片 CDN 直链 | 只下载公开图库照片，**不调用需要 key 的 API** |
| faster-whisper | 本地模型 | 模型首次下载走 HuggingFace 镜像，**推理完全本地**，不上传音频 |
