# 配图：真实摄影，禁用 AI 生图

本文件是 SKILL.md 步骤 5–7 的详细实现。**铁律：配图与封面一律真实摄影，禁用 AI 生图。**
用 Pexels 等免费图库取真实照片，下载后**逐张肉眼确认内容**，再决定采用。

## 流程

1. 从 Pexels 搜索页（WebFetch）取 `https://images.pexels.com/photos/<ID>/` 形式的直链数字 ID：

```bash
WebFetch "https://www.pexels.com/search/<关键词>/"
# 在返回里抠 /photos/<ID>/ 的数字 ID
```

2. 批量下载 6 张候选（一次要成品尺寸，别二次压）：

```bash
curl -s -o img_1.jpg "https://images.pexels.com/photos/<ID>/pexels-photo-<ID>.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop"
```

3. **用 Read 逐张看内容再定**（尺寸对了不代表内容对）。注意图上文字、人物年龄/性别、场景是否符合叙述。

4. 选 4 张，让它们形成一条**视觉暗线**（不是随机配图）。例如：
   - 城市黄昏（时代背景）→ 键盘手部（拼执行力）→ 窗前侧影（停下来想）→ 林中分岔小径（找到自己的路）

5. 正文图建议 900×506（移动端 667px 容器足够）；封面见 `html-template.md`。

## 文件命名与压缩（推送脚本的硬约定）

`scripts/push_draft.py` 按**固定文件名**找图，不认占位符名：

| 占位符 | 实际文件 | 建议尺寸 |
|---|---|---|
| `IMG_01` | `images/01.jpg` | 900×506（16:9） |
| `IMG_02` | `images/02.jpg` | 900×506 |
| `IMG_03` | `images/03.jpg` | 900×506 |
| `IMG_04` | `images/04.jpg` | 900×506 |

命名错了脚本会直接报「找不到图片 …（对应占位符 IMG_xx）」。

**脚本不做任何压缩**，封面必须自己先压：

```bash
# 封面：向图库要 2.35:1 成品，再压到 ≤100KB
curl -s -m 90 -o cover_src.jpg "https://images.pexels.com/photos/<ID>/pexels-photo-<ID>.jpeg?auto=compress&cs=tinysrgb&w=2350&h=1000&fit=crop"

python3 - <<'PY'
from PIL import Image
import os
im = Image.open("cover_src.jpg").convert("RGB").resize((900, 383), Image.LANCZOS)
q = 92
while q >= 40:
    im.save("cover.jpg", "JPEG", quality=q, optimize=True, progressive=True)
    if os.path.getsize("cover.jpg") <= 100*1024: break
    q -= 6
print(os.path.getsize("cover.jpg")//1024, "KB")
PY
```

2026-11-02 实测：2350×1000 原图 257 KB → quality=92 压到 **68.7 KB**，微信接受。

## 避坑

- **屏幕/键盘特写常有外文界面**，甚至是非英文键盘布局（曾选中一张俯拍笔记本，放大才发现是俄文西里尔字母键盘）——中文文章务必看清图上文字再定。
- **人物图注意年龄/性别与叙述者是否对得上**（「我带我妈」不能用「年轻妈妈+幼女」）。
- **不要用 `sips -s formatOptions 60` 二次压**——对已压缩 JPEG 无效，经常越压越大。直接跟图库要成品尺寸。
- 单张正文图控制在 ≤300 KB，避免 HTML 整体超过 900 KB（微信 `draft/add` 有体积风险）。
- **候选图超过 6 张时，先拼成蒙太奇再看**（PIL 拼图 + `Read` 看一张），比逐张 `Read` 省一个数量级的 token：

```python
from PIL import Image, ImageDraw
import glob, os
files = sorted(glob.glob("cand/*.jpg"))
cols, tw, th = 4, 420, 236
rows = (len(files)+cols-1)//cols
sheet = Image.new("RGB", (cols*tw, rows*(th+26)), (255,255,255))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    sheet.paste(Image.open(f).convert("RGB").resize((tw, th)),
                ((i % cols)*tw, (i//cols)*(th+26)))
    d.text(((i % cols)*tw+8, (i//cols)*(th+26)+th+6),
           os.path.basename(f).replace(".jpg", ""), fill=(0,0,0))
sheet.save("cand_sheet.jpg", quality=85)
```

- **同主题相邻两张不要都用人像群像**，视觉会重复；也不要用明显带医疗/疫情联想的道具（如医用口罩），会被误读成别的主题。
