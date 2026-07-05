# -*- coding: utf-8 -*-
"""
封面提示词模块。

职责：
1. 生成封面生图提示词
2. 封面和内页共用风格参数，但各自使用独立排布池
3. 把标题压缩要求写进提示词，不在代码里截断标题
"""

import re

from .template_registry import (
    ACCENT_CARRIERS,
    BACKGROUND_POOLS,
    COMPOSITIONS,
    COVER_TEMPLATES,
    FONTS,
    HUMAN_CHARACTERS,
    MASCOT_CHARACTERS,
    STYLES,
    TEXT_EFFECTS,
    pick_one,
)

_EMOJI_SYMBOL_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\u2600-\u27BF"
    "\u2B00-\u2BFF"
    "\u2190-\u21FF"
    "\u2300-\u23FF"
    "\u200D"
    "\uFE0E-\uFE0F"
    "]",
    re.UNICODE,
)
_KEYCAP_BADGE_PATTERN = re.compile(r"[0-9#*]\uFE0F?\u20E3|[①-⑩]")

# PROMPT_COVER 里的 {xxx} 都是占位符：
# - {raw_title}: 当前文章标题清洗后的内容，供模型理解原始主题
# - {raw_summary}: 当前文章摘要/正文摘要清洗后的内容，供模型理解主题补充信息
# - {style}: 整体画风方向，比如蜡笔手绘、轻水彩、纸感插画
# - {font}: 标题文字本身的字体气质，比如圆手写、黑体、粉笔字
# - {font_effect}: 标题附加字效，比如描边、阴影、托底、擦色、高亮底
# - {accent_carrier}: 重点表达片段的强调方式，比如下划线、笔刷高亮、色块托底
# - {background_pool}: 背景底色与纸感纹理方向
# - {cover_template}: 封面整套模板，里面同时包含主体摆放、标题位置、重点词强调逻辑
# - {character_clause}: 是否出现角色、角色长什么样、是否单人出镜等动态说明
# 其中 {style} / {font} / {font_effect} / {accent_carrier} / {background_pool} / {cover_template}
# 来自 template_registry.py 中的随机池，由 pick_style_options() 抽取后填入。
# {character_clause} 由 _build_character_clause() 根据是否启用角色动态生成。
PROMPT_COVER = (
    "做一张小红书图文封面插画；"
    "图中文字只能出现封面主标题、可选副标题和极少量短标签；"
    "不要把本提示词、风格词、构图词、角色描述、禁令说明直接抄进图中文字；"
    "原始文章标题仅供理解主题参考：\"{raw_title}\"；"
    "文章内容摘要仅供理解主题参考：\"{raw_summary}\"；"
    "请基于原标题自行提炼一个更适合封面的主标题，必须是简体中文，短、顺口、醒目；"
    "主标题必须控制在12个字以内，包括12个字；标题必须语义完整、读起来像一句完整表达，不要为了压字数写成残句、半句或不完整短语；最多两行；"
    "如果原标题太长，必须先压缩成更适合画面的短标题，不要把原标题整句照搬进图片；"
    "副标题不是必须，只有在不拥挤、且确实能增强理解时，才保留一行更短副标题；"
    "如果副标题会让画面拥挤，就直接省略；"
    "整体统一{style}；"
    "封面排版参考：{cover_template}；"
    "{character_clause}"
    "若出现人物或陪伴角色，动作、手势、表情和身体朝向要自然生动，和道具有真实互动，不要僵硬站姿或摆拍感；"
    "若出现单个人物，肢体数量必须正确：只能有两条手臂、两只手，左右对应自然，禁止多手、多臂、第三只手、漂浮手、断手、粘连手、重影手、畸形手指或额外手指；"
    "人物手部只要求清楚、自然、结构稳定，不要刻意增加复杂手势或手部细节；"
    "如果完整展示双手容易导致手部错误，可以自然地让部分手藏在衣袖后、身体侧面、道具后或画面边缘，只要整体看起来合理即可；"
    "优先保证人物整体自然和肢体正确，不要为了展示双手而强行把两只手都完整摊开在画面中央；"
    "标题字感接近{font}，可用{font_effect}轻轻托住文字，但不要夸张字效；"
    "标题承载方式由模型自己决定，让文字自然融入留白和主体之间；"
    "不要小框、不要硬边框、不要对话框、不要横幅底条、不要大色块标题贴片；"
    "关键词可用{accent_carrier}轻轻强调，但强调元素要少；"
    "允许模型自行判断标题里最该先看到的1到3个词，这些词通常是结果词、反差词、提醒词、动作词，或平台语境下会形成阅读停顿的高注意力词；"
    "这些重点词可以用明显放大、加粗、描边、跳色、下划线、彩色笔涂底、贴纸托字等方式强调；"
    "重点词一定要少，整句标题不能每个字都一样重；"
    "封面整体更像精致教程海报：大标题清晰，主体单一明确，周围只点缀少量和主题强相关的小物件或短标签；"
    "配色由模型自行生成，整体低饱和、干净、统一，可带蜡笔、彩铅、粉蜡笔或轻水彩质感；"
    "背景参考\"{background_pool}\"；"
    "背景保持干净浅底、轻微晕染、少量纸感纹理和明确留白，不要复杂拼贴，不要满页碎装饰；"
    "画面要耐看、清楚、主题一眼能懂，不要让提示词内容本身出现在图片文字里；"
    "图内仅出现简体中文，不要英文、emoji、颜文字、表情符号、二维码、水印、编号徽章和无关装饰；"
    "safe_for_xiaohongshu, no_nsfw_elements, flat_illustration"
)


def clean_text(text: str) -> str:
    """清理文本。"""
    if not text:
        return ""
    text = _EMOJI_SYMBOL_PATTERN.sub("", text)
    text = _KEYCAP_BADGE_PATTERN.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def pick_style_options(use_character: bool = True) -> dict:
    """随机选择一组共享风格选项，并分别给封面/内页挑选独立排布。"""
    use_mascot = bool(use_character and pick_one([False, False, True]))
    style_opts = {
        "font": pick_one(FONTS),
        "font_effect": pick_one(TEXT_EFFECTS),
        "composition": pick_one(COMPOSITIONS),
        "cover_template": pick_one(COVER_TEMPLATES),
        "background_pool": pick_one(BACKGROUND_POOLS),
        "style": pick_one(STYLES),
        "accent_carrier": pick_one(ACCENT_CARRIERS),
        "use_character": use_character,
        "character": "",
        "character_mode": "mascot" if use_mascot else "human",
    }
    if use_character:
        style_opts["character"] = (
            pick_one(MASCOT_CHARACTERS) if use_mascot else pick_one(HUMAN_CHARACTERS)
        )
    return style_opts


def _build_character_clause(style_opts: dict) -> str:
    if style_opts.get("use_character") and style_opts.get("character"):
        return (
            f"若出现角色，固定为\"{style_opts['character']}\"，作为整组统一讲解IP；"
            "封面优先一个人物或一个陪伴角色，不要多人同屏；"
        )
    return "不强制人物，也可用单个主体物、主道具或大信息板做视觉焦点；"


def build_cover_prompt(
    title: str,
    summary: str,
    style_opts: dict = None,
) -> str:
    """构建封面提示词。"""
    if style_opts is None:
        style_opts = pick_style_options()

    raw_title = clean_text(title) or "重点总结"
    raw_summary = clean_text(summary)[:220] or raw_title

    return PROMPT_COVER.format(
        raw_title=raw_title,
        raw_summary=raw_summary,
        style=style_opts.get("style", "蜡笔手绘教程海报"),
        cover_template=style_opts.get(
            "cover_template",
            "单一大主体居中或略偏下，全身或半身人物占画面主要面积；标题做成2到3行超大字压在主体前方或身体周围；只选1到3个重点表达片段做明显放大、加粗、跳色或描边，其余字保持克制",
        ),
        character_clause=_build_character_clause(style_opts),
        font=style_opts.get("font", "蜡笔圆手写字"),
        font_effect=style_opts.get("font_effect", "蜡笔轻涂底"),
        accent_carrier=style_opts.get("accent_carrier", "淡色笔刷高亮"),
        background_pool=style_opts.get("background_pool", "暖米白纸感浅底，带轻微蜡笔颗粒和淡淡边缘晕染，留白干净"),
    ).strip()


SAFE_SUFFIX = "safe_for_xiaohongshu, no_nsfw_elements, flat_illustration"


def ensure_safe_suffix(text: str) -> str:
    """确保提示词有安全后缀。"""
    text = (text or "").strip().rstrip("，,。")
    if SAFE_SUFFIX in text:
        return text
    return f"{text}, {SAFE_SUFFIX}" if text else SAFE_SUFFIX
