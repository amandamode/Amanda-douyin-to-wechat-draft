# 公众号 HTML 版式规范 + base64 注入

本文件是 SKILL.md 步骤 6–7 的详细实现。公众号图文要**内联样式、图片 base64 内嵌、0 外链**（微信屏蔽外链）。

## 版式（移动端优先）

- 容器 `max-width:667px`、`line-height:1.8`、字号 16px、段落 `margin:0 0 18px`
- 主色 `#2f5c8a`；小标题 `h2` 用左边框样式
- 强调卡片：`background:#f7f9fb;border-left:4px solid #2f5c8a`
- 核心金句可用居中大字块
- 破折号少用（AI 味指标之一）

## 写法

先写 `article_raw.html`（图片位置放占位符 `IMG_01`…`IMG_04`），`scripts/push_draft.py` 再把占位符替换成 base64，生成「可粘贴版.html」。

`templates/article_raw.html` 是最小可套用模板：

```html
<h1>这里是公众号标题</h1>
<p>开头段落……</p>
<p>IMG_01</p>
<h2>小节标题</h2>
<p>正文……</p>
<p>IMG_02</p>
<p>……</p>
<p>IMG_03</p>
<p>……</p>
<p>IMG_04</p>
<p>结尾段落。</p>
```

## 两个必踩的坑

1. **`article_raw.html` 最前面必须有 `<h1>`** —— `push_draft.py` 第 1 步是「从 HTML 抽 `<h1>` 作标题，并从正文移除」。raw 里没有 h1 → **草稿标题是空的**（接口不报错）。h1 内容就是公众号标题，正文不会重复显示。

2. **正文图不要下 1280 宽再压** —— 直接跟图库要成品尺寸一次到位：
   ```bash
   curl -s -o img_1.jpg "https://images.pexels.com/photos/<ID>/pexels-photo-<ID>.jpeg?auto=compress&cs=tinysrgb&w=900&h=506&fit=crop"
   ```
   4 张合计 250–400 KB，900 宽在移动端 667px 容器下观感完全够。

## 注入后自检（必须）

```python
print("汉字:", len(re.findall(r"[\u4e00-\u9fff]", body)))
print("http:", h.count("http"), "（必须 0）")
print("base64:", h.count("data:image/jpeg;base64"), "张")
```

> 注意：HTML 超过约 900 KB 时 `draft/add` 有失败风险，优先压缩大图。

## 封面尺寸

```bash
curl -s -m 90 -o cover-2350x1000.jpg "https://images.pexels.com/photos/<ID>/pexels-photo-<ID>.jpeg?auto=compress&cs=tinysrgb&w=2350&h=1000&fit=crop"
curl -s -m 90 -o cover-1080x1080.jpg "https://images.pexels.com/photos/<ID>/pexels-photo-<ID>.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1080&fit=crop"
```
用 `sips -g pixelWidth -g pixelHeight` 确认尺寸。
