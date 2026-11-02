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

## 避坑

- **屏幕/键盘特写常有外文界面**，甚至是非英文键盘布局（曾选中一张俯拍笔记本，放大才发现是俄文西里尔字母键盘）——中文文章务必看清图上文字再定。
- **人物图注意年龄/性别与叙述者是否对得上**（「我带我妈」不能用「年轻妈妈+幼女」）。
- **不要用 `sips -s formatOptions 60` 二次压**——对已压缩 JPEG 无效，经常越压越大。直接跟图库要成品尺寸。
- 单张正文图控制在 ≤300 KB，避免 HTML 整体超过 900 KB（微信 `draft/add` 有体积风险）。
