#!/usr/bin/env python3
"""推送含 IMG_xx 占位符的文章到微信公众号草稿箱。

用法:
  python3 push_draft.py --html article_raw.html --cover cover.jpg \
      --digest "最想被转发的那句，<=120字" --author "作者名" \
      [--images-dir images] [--env wechat-mp.env]

流程: 注入 base64 -> 取 token -> 上传正文图(media/uploadimg)
      -> 传封面拿 thumb_media_id(material/add_material) -> draft/add -> 打印 MEDIA_ID

凭证: 优先读环境变量 WECHAT_APPID / WECHAT_SECRET；
      缺失时回退到 --env 指定的 .env 文件（默认 ~/.workbuddy/secrets/wechat-mp.env）。
      切勿把密钥写进仓库。
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid


def load_env(path):
    d = {}
    if not path or not os.path.exists(path):
        return d
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip()
    return d


def http_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        sys.exit(f"HTTP {e.code} from WeChat API: {body}")


def multipart(name, filename, data, ctype="image/jpeg"):
    b = uuid.uuid4().hex
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + data + f"\r\n--{b}--\r\n".encode()
    return body, f"multipart/form-data; boundary={b}"


def main():
    ap = argparse.ArgumentParser(description="Push an article to WeChat MP draft box.")
    ap.add_argument("--html", required=True, help="article_raw.html，含 IMG_01..IMG_04 占位符与 <h1> 标题")
    ap.add_argument("--cover", required=True, help="封面图路径 (jpg)")
    ap.add_argument("--digest", required=True, help="文章摘要/转发语 (<=120 字)")
    ap.add_argument("--author", required=True, help="公众号文章作者名")
    ap.add_argument("--images-dir", default="images",
                    help="存放 01.jpg..04.jpg 的目录 (默认: 与 html 同级的 images/)")
    ap.add_argument("--env", default=os.path.expanduser("~/.workbuddy/secrets/wechat-mp.env"),
                    help="含 WECHAT_APPID/WECHAT_SECRET 的 .env 文件路径")
    args = ap.parse_args()

    env = load_env(args.env)
    appid = os.environ.get("WECHAT_APPID") or env.get("WECHAT_APPID")
    secret = os.environ.get("WECHAT_SECRET") or env.get("WECHAT_SECRET")
    if not appid or not secret:
        sys.exit("缺少凭证：请设置环境变量 WECHAT_APPID/WECHAT_SECRET，或用 --env 指定含密钥的文件")

    img_dir = args.images_dir
    if not os.path.isabs(img_dir):
        img_dir = os.path.join(os.path.dirname(os.path.abspath(args.html)), img_dir)
    images = {f"IMG_{i:02d}": os.path.join(img_dir, f"{i:02d}.jpg") for i in range(1, 5)}

    # 1) 注入 base64
    html = open(args.html, encoding="utf-8").read()
    for key, path in images.items():
        if not os.path.exists(path):
            sys.exit(f"找不到图片 {path}（对应占位符 {key}）")
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        html = html.replace(key, "data:image/jpeg;base64," + b64)
    n_b64 = html.count("data:image/jpeg;base64")
    print(f"[inject] base64 图 {n_b64} 张, 大小 {len(html) // 1024} KB")

    # 2) token + 抽标题
    m = re.search(r"<h1>(.*?)</h1>", html, re.S)
    if not m:
        sys.exit("article_raw.html 必须含 <h1> 标题（推送脚本会抽 <h1> 作标题）")
    title = m.group(1).strip()
    content = re.sub(r"<h1>.*?</h1>", "", html, flags=re.S).strip()
    print(f"[title] {title} ({len(title)} 字)")

    token = http_json(
        f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
    ).get("access_token")
    if not token:
        sys.exit("获取 access_token 失败（检查 AppID/Secret 与 API IP 白名单）")
    print("[token] OK")

    # 3) 上传正文图
    for key, path in images.items():
        data = open(path, "rb").read()
        body, ctype = multipart("media", os.path.basename(path), data)
        r = http_json(f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}",
                      body, {"Content-Type": ctype})
        if "url" not in r:
            sys.exit(f"uploadimg 失败: {r}")
        mm = re.search(r"data:image/jpeg;base64,[A-Za-z0-9+/=]+", html)
        if not mm:
            sys.exit("找不到可替换的 base64 图")
        html = html.replace(mm.group(0), r["url"], 1)
        print(f"[img] {key} -> {r['url'][:60]}...")
    if "base64" in html:
        sys.exit("还有残留 base64 未上传，请检查图片数量")

    # 4) 封面永久素材
    cdata = open(args.cover, "rb").read()
    body, ctype = multipart("media", "cover.jpg", cdata)
    r = http_json(f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
                  body, {"Content-Type": ctype})
    thumb = r.get("media_id")
    if not thumb:
        sys.exit(f"封面上传失败: {r}")
    print(f"[cover] media_id {thumb[:30]}...")

    # 5) draft/add
    payload = {"articles": [{
        "title": title,
        "author": args.author,
        "digest": args.digest,
        "content": html,
        "thumb_media_id": thumb,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }]}
    r = http_json(f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}",
                  json.dumps(payload, ensure_ascii=False).encode(),
                  {"Content-Type": "application/json; charset=utf-8"})
    print("[draft/add]", json.dumps(r, ensure_ascii=False))
    if "media_id" not in r:
        sys.exit("推送失败")
    media_id = r["media_id"]
    print("MEDIA_ID=" + media_id)
    print("\n回读核验: 用 draft/get 取 media_id=%s 的标题/摘要/封面，确认与预期一致。" % media_id)


if __name__ == "__main__":
    main()
