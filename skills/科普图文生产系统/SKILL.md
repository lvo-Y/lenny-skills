---
name: 科普图文生产系统
description: 小红书科普图文生产系统。用于把结构式干货文章拆解成内容生产蓝图，生成封面、内页、文案改写和质检提示词，适合减脂饮食、生活方式、干货科普类图文批量生产。
---

# 科普图文生产系统

这是一个面向小红书科普图文的生产型技能包。它把一篇结构式干货文章转成可执行的生产蓝图，并围绕同一套视觉风格生成封面图、内页图、文案改写和质检提示词。

## 适用场景

当用户需要把一篇干货文章加工成小红书图文内容时使用本技能，包括：

- 从文章中拆出 3 到 5 个内页知识点
- 生成封面文生图提示词
- 生成系列内页文生图提示词
- 改写标题、正文和 5 个候选话题
- 对图片提示词做平台合规质检
- 对改写后的标题、内容、话题做质量检查

## 文件结构

核心代码放在 `scripts/ALL_prompt/` 包内：

- `central_control.py`：总控蓝图解析提示词，将文章拆成内容生产蓝图 JSON
- `template_registry.py`：字体、字效、风格、封面模板、内页构图、背景、人设等随机池
- `prompt_base_write.py`：标题、正文、话题一次性改写提示词
- `prompt_cover.py`：封面生图提示词构建
- `prompt_content_image.py`：内页生图提示词构建
- `prompt_expand_content.py`：原文扩写成 4 到 8 个内容块
- `prompt_quality_check.py`：图片提示词与文章改写质检
- `__init__.py`：包说明

## 使用流程

1. 调用 `central_control.build_blueprint_prompt()`，把文章标题、正文和话题转成蓝图解析提示词。
2. 使用大模型输出蓝图 JSON，得到知识点、是否有人物、人设建议和敏感度。
3. 调用 `prompt_cover.pick_style_options()` 选出全组共享视觉风格。
4. 调用 `prompt_cover.build_cover_prompt()` 生成封面图提示词。
5. 对每个知识点调用 `prompt_content_image.build_content_prompt()` 生成内页图提示词。
6. 调用 `prompt_quality_check.build_image_quality_prompt()` 对封面和内页提示词做合规质检。
7. 如需文案改写，调用 `prompt_base_write.PROMPT_REWRITE_ARTICLE_WITH_TOPICS` 或 `prompt_quality_check.build_article_quality_prompt()`。

## 关键原则

- 原文拆解必须保持原文边界，`original_text` 要从正文逐字摘抄。
- 封面和内页共用同一套风格参数，但使用各自独立的版式模板。
- 图内文字只出现中文标题、短句、标签和说明，不出现提示词本身。
- 图片提示词必须避免解剖、内脏、血管、半透明人体、多手多臂、二维码、水印等风险元素。
- 标题、正文、话题不应出现互动引导、平台名、私域引流或候选话题池之外的话题。

## 快速示例

```python
from ALL_prompt.central_control import build_blueprint_prompt
from ALL_prompt.prompt_cover import pick_style_options, build_cover_prompt
from ALL_prompt.prompt_content_image import build_content_prompt

article_title = "减脂期怎么吃更稳"
article_content = "这里放文章正文"

blueprint_prompt = build_blueprint_prompt(article_title, article_content)
style_opts = pick_style_options(use_character=True)
cover_prompt = build_cover_prompt(article_title, article_content, style_opts)
content_prompt = build_content_prompt(article_title, article_content, style_opts, page_index=1, total_pages=4)
```

## 注意

当前代码保留了原始业务约束和候选话题池，偏向减脂、饮食、生活方式、小红书图文生产。如果迁移到其他赛道，应先调整 `prompt_base_write.py` 中的候选话题池和违禁词。