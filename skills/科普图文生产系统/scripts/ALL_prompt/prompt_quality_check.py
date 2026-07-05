# -*- coding: utf-8 -*-
"""
质检模块

职责：
1. 图片提示词质检
2. 文章改写质检

所有规则都在提示词里，让LLM判断
"""

import re
from datetime import datetime

from ALL_prompt.prompt_base_write import PROMPT_EDITABLE_PARAMS

# =============================================================================
# 图片提示词质检
# =============================================================================

PROMPT_IMAGE_QUALITY_CHECK = """
你是图片提示词质检工程师。

【禁止内容】
- 人体解剖图、解剖结构、生理结构、医学示意图
- 内脏器官、心脏、肺、胃、肠、肝、肾、大脑等
- 血液、血管网络、动脉静脉、循环系统图
- 肌肉纤维、肌肉切面、剖面图、骨骼系统、半透明人体
- 二维码、水印
- 多手、多臂、第三只手、漂浮手、断手、粘连手、畸形手指、额外手指、错误肢体数量

【违禁词】
解剖、解剖图、解剖结构、生理结构、人体内部、半透明人体、透明人体、透视人体
内脏、器官、心脏、肺、肝、胃、肠、肾、大脑、骨骼、骨架
肌肉纤维、肌纤维、肌肉切面、剖面图、横切面
血液、血管、动脉、静脉、毛细血管、循环系统、血流
多手、多臂、第三只手、漂浮手、断手、粘连手、重影手、畸形手指、额外手指

【替代方案】
- 解剖图/人体结构 → 抽象信息图标
- 内脏/器官 → 抽象功能图标
- 心脏/肺/肝等 → 功能图标
- 血管 → 流向箭头
- 血液循环 → 能量流动箭头
- 肌肉纤维/切面 → 恢复进度示意
- 骨骼 → 支撑结构图标
- 半透明人体 → 衣着完整的卡通人物剪影
- 多手/多臂/畸形手 → 改为单人物、双臂双手数量正确、手部结构自然稳定；若手部难以稳定，可允许部分手自然藏在衣袖后、身体侧面、道具后或画面边缘

【季节处理】
当前日期：{current_date}
如果提示词中涉及季节词（春夏秋冬、季节穿搭、当季食材等），请根据当前日期判断正确的季节：
- 3-5月：春季
- 6-8月：夏季
- 9-11月：秋季
- 12-2月：冬季

【改写要求】
1. 发现违禁词就用对应方案替换
2. 去除所有 emoji 和编号符号（1️⃣2️⃣3️⃣、①②③）
3. 图内文字仅限简体中文
4. 季节词根据当前日期修正
5. 若出现人物，优先保证肢体数量正确和手部结构自然稳定；必要时允许部分手自然遮挡，不强求双手完整展示
6. 结尾添加：safe_for_xiaohongshu, no_nsfw_elements, flat_illustration

请质检并改写以下图片提示词：

{prompts}
"""


# =============================================================================
# 文章改写质检
# =============================================================================

PROMPT_ARTICLE_QUALITY_CHECK = """
你是小红书内容质检工程师。

【违禁词】
{banned_words}

【内容规范】
1. 标题：必须高度概括正文核心观点，有信息量，避免空洞（如"干货分享""必看"）
2. 正文：要有具体生活场景、动作或道具，不要只有抽象判断
3. 话题：恰好5个，从候选池原样选择，不能自造、不能改写、不能重复

【候选话题池】
{candidate_topics_pool}

【禁止行为】
- 复制原句、照搬案例
- 互动引导（点赞、评论、私信、关注等）
- 编造原文没有的数据、案例、结论
- 使用模糊词（大量、尽量、大概）描述定量内容

【输出要求】
质检以下文章，如发现问题请改写；如果没有问题，也输出整理后的最终版本：

标题：{title}
内容：{content}
话题：{topics}

只允许输出一个可被 json.loads 直接解析的 JSON 对象，不要 markdown 代码块，不要解释，不要输出“通过”。
JSON 结构固定如下：
{{"title":"...","content":"...","topic":"#话题1 #话题2 #话题3 #话题4 #话题5"}}
"""


# =============================================================================
# 工具函数
# =============================================================================

def get_current_date() -> str:
    """获取当前日期字符串"""
    return datetime.now().strftime("%Y-%m-%d")


def build_image_quality_prompt(prompts: list) -> str:
    """构建图片质检提示词"""
    content = "\n---\n".join(
        f"【{'封面' if i == 0 else f'内页{i}'}】\n{p or ''}"
        for i, p in enumerate(prompts)
    )
    return PROMPT_IMAGE_QUALITY_CHECK.format(
        current_date=get_current_date(),
        prompts=content,
    )


def build_article_quality_prompt(
    title: str,
    content: str,
    topics: str = "",
) -> str:
    """构建文章质检提示词"""
    return PROMPT_ARTICLE_QUALITY_CHECK.format(
        banned_words=PROMPT_EDITABLE_PARAMS["banned_words"],
        candidate_topics_pool=PROMPT_EDITABLE_PARAMS["candidate_topics_pool"],
        title=title or "",
        content=content or "",
        topics=topics or "",
    )


# 安全后缀
SAFE_SUFFIX = "safe_for_xiaohongshu, no_nsfw_elements, flat_illustration"
NO_EMOJI_SYMBOLS_CLAUSE = "禁止出现任何emoji、颜文字、表情符号、表情贴纸、表情包元素"
_EMOTICON_PATTERN = re.compile(
    r"(:-?\)|:-?\(|;-\)|:\]|:\[|:D|:P|xD|XD|T_T|QAQ|>_<|\^_\^|=\)|=\(|=\]|=\[)"
)


def ensure_safe_suffix(text: str) -> str:
    """确保提示词有安全后缀"""
    text = (text or "").strip().rstrip("，,；;。 ")
    if _EMOTICON_PATTERN.search(text):
        text = _EMOTICON_PATTERN.sub("", text)
        text = re.sub(r"\s+", " ", text).strip().rstrip("，,；;。 ")
    if text and NO_EMOJI_SYMBOLS_CLAUSE not in text:
        text = f"{text}；{NO_EMOJI_SYMBOLS_CLAUSE}"
    if SAFE_SUFFIX in text:
        return text
    return f"{text}, {SAFE_SUFFIX}" if text else f"{NO_EMOJI_SYMBOLS_CLAUSE}, {SAFE_SUFFIX}"


# 季节检测关键词
SEASON_KEYWORDS = ["春季", "夏天", "夏季", "秋天", "秋季", "冬天", "冬季", "春夏秋冬"]


def has_season_keyword(text: str) -> bool:
    """检测文本是否有季节关键词"""
    return any(kw in text for kw in SEASON_KEYWORDS)
