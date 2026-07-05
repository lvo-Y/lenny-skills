# -*- coding: utf-8 -*-
"""
内页图片提示词模块。

职责：
1. 构建内页文生图提示词
2. 封面与内页共用风格参数，内页继续使用当前信息页模板池
3. 页标题由提示词自行提炼，不在代码里截断或硬算
"""

import re

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

PROMPT_CONTENT_IMAGE = (
    "做一张小红书图文内页插画，第{page_index}页，共{total_pages}页；"
    "图中文字只能出现本页主标题、少量说明短句、步骤短句、对比短句或结果短句；"
    "不要把本提示词、风格词、构图词、角色描述、禁令说明直接抄进图中文字；"
    "整篇文章总标题仅供理解主题参考：\"{article_title}\"；"
    "以下原文只是本页内容依据，不是要整段照搬进图片：\"{content}\"；"
    "请根据整页内容自行提炼一个简短主标题，必须概括整页核心意思；"
    "这个标题必须是整页描述，不要只摘局部一句话、单个数字、零散词、某个小步骤名或某个小食物名；"
    "本页主标题建议控制在6到12个字，最多不超过14个中文或等效字符，最多两行；"
    "如果本页原文里没有天然适合直接上图的标题，就先重写成更像海报标题的整页总结，再放进图里；"
    "整体统一{style}，版式采用{composition}；"
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
    "整体分布尽量接近教程海报或手账信息页：一个明确主场景或主人物，周围自然分布多个信息区、标签区、对比区或小结论；"
    "如果本页内容更适合做合集、替代项、分类清单、推荐列表，也可以不用单一主场景，改为2到4个圆角小场景卡片拼页；"
    "这类卡片拼页里，每个卡片最好都有独立小标题、对应小插画和2到4条短要点，整体像清单合集页；"
    "按本页内容密度，优先组织成{block_plan}个信息块，每块尽量是短标题加短说明的结构；"
    "信息块可以比原文写得更完整，但必须拆成清楚可读的短句块，不要整段堆字；"
    "如果本页内容天然适合清单、tips、步骤、对比、前后变化，可以自然扩成更多短句信息区；"
    "若原文偏短，可在不改变原意和结论的前提下，补充少量生活化细节、动作、场景、对比说明、结果说明或读者更容易理解的小提示；"
    "扩写只是为了把这页讲清楚，不要改变主题，不要编造新结论，不要偏离原文；"
    "图中文字数量由画面需要决定，不固定写死；但优先保证可读性和结构感，不要为了凑字数堆满整页；"
    "配色由模型自行生成，整体低饱和、干净、统一，可带蜡笔、彩铅、粉蜡笔或轻水彩质感；"
    "背景参考\"{background_pool}\"；"
    "背景保持干净浅底、轻微晕染、少量纸感纹理和明确留白，不要复杂拼贴，不要满页碎装饰；"
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


def infer_block_plan(content: str) -> str:
    """根据内容长度给出信息块数量建议。"""
    text = clean_text(content)
    length = len(text)
    sentence_count = len([
        part for part in re.split(r"[。！？；，\n]", text)
        if part.strip()
    ])
    if length >= 60 or sentence_count >= 6:
        return "4到5"
    if length >= 24 or sentence_count >= 3:
        return "5到6"
    return "6到8"


def _build_character_clause(style_opts: dict) -> str:
    if style_opts.get("use_character") and style_opts.get("character"):
        return (
            f"若出现角色，固定为\"{style_opts['character']}\"，与封面保持同一人设；"
            "优先一个主人物或一个陪伴角色，不要多人同屏；"
        )
    return "不强制人物，也可用单个主体物、大信息板或主道具做视觉焦点；"


def build_content_prompt(
    article_title: str,
    content: str,
    style_opts: dict,
    page_index: int = 1,
    total_pages: int = 1,
) -> str:
    """构建内容页提示词。"""
    cleaned_article_title = clean_text(article_title) or "重点提醒"
    cleaned_content = clean_text(content)[:320] or "重点内容"

    return PROMPT_CONTENT_IMAGE.format(
        article_title=cleaned_article_title,
        content=cleaned_content,
        style=style_opts.get("style", "蜡笔手绘教程海报"),
        composition=style_opts.get("composition", "上方大标题，中间主体，四周环绕4到8个信息块或小标签"),
        character_clause=_build_character_clause(style_opts),
        font=style_opts.get("font", "蜡笔圆手写字"),
        font_effect=style_opts.get("font_effect", "蜡笔轻涂底"),
        accent_carrier=style_opts.get("accent_carrier", "淡色笔刷高亮"),
        block_plan=infer_block_plan(cleaned_content),
        background_pool=style_opts.get("background_pool", "暖米白纸感浅底，带轻微蜡笔颗粒和淡淡边缘晕染，留白干净"),
        page_index=page_index,
        total_pages=total_pages,
    ).strip()


SAFE_SUFFIX = "safe_for_xiaohongshu, no_nsfw_elements, flat_illustration"


def ensure_safe_suffix(text: str) -> str:
    """确保提示词有安全后缀。"""
    text = (text or "").strip().rstrip("，,。")
    if SAFE_SUFFIX in text:
        return text
    return f"{text}, {SAFE_SUFFIX}" if text else SAFE_SUFFIX
