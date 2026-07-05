# -*- coding: utf-8 -*-
"""
内页内容扩写模块

职责：
1. 将原文扩写成 4-8 个内容块
2. 根据原文字数动态决定块数（字数多→4块，字数少→8块）
3. 扩写时不改变原意，只是拆分和丰富细节
"""

# -----------------------------------------------------------------------------
# 扩写提示词
# -----------------------------------------------------------------------------
PROMPT_EXPAND_CONTENT = """
# 角色设定
你是一名小红书内容策划专家，擅长将干货内容拆分成多个独立、易懂的知识点块。

# 任务目标
我将提供一篇干货文章的标题和内容，请你将其扩写成 {block_count} 个独立的内容块。
每个内容块应该：
- 独立成段，能单独作为一页内页的内容
- 保留原文的核心信息和专业判断
- 丰富细节，补充生活化场景、动作、道具等
- 保持原文的口吻和风格
- 不改变原意，只是拆分和丰富

【原标题】
{title}

【原内容】
{content}

# 扩写规则
1. **数量精确**：必须恰好输出 {block_count} 个内容块
2. **保持原意**：不改变原文的核心观点和结论
3. **丰富细节**：
   - 补充具体的生活场景、动作描述
   - 添加使用顺序、对应道具、前后变化
   - 可适当举例说明，但要贴近生活
4. **独立完整**：每个块应该能独立理解，不要前后依赖太强
5. **字数适中**：每个块 50-150 字左右
6. **口吻一致**：保持原文的口语感和生活化表达

# 输出格式
严格按以下格式输出，每个块单独占一段，用【块N】标记：

【块1】
xxx（第一个内容块的内容）

【块2】
xxx（第二个内容块的内容）

...

【块{block_count}】
xxx（最后一个内容块的内容）

注意：必须恰好输出 {block_count} 个块，不要多也不要少。
"""


def calculate_block_count(content: str, min_blocks: int = 4, max_blocks: int = 8) -> int:
    """
    根据内容字数计算块数

    规则：
    - 字数少（<100字）→ 8块
    - 字数中等（100-200字）→ 6块
    - 字数多（200-300字）→ 5块
    - 字数很多（>300字）→ 4块
    """
    if not content:
        return min_blocks

    char_count = len(content.strip())

    if char_count < 100:
        return max_blocks  # 8块
    elif char_count < 200:
        return 6
    elif char_count < 300:
        return 5
    else:
        return min_blocks  # 4块


def build_expand_prompt(title: str, content: str, block_count: int = None) -> str:
    """
    构建扩写提示词

    Args:
        title: 文章标题
        content: 文章内容
        block_count: 指定块数，为None时自动计算

    Returns:
        扩写提示词
    """
    if block_count is None:
        block_count = calculate_block_count(content)

    return PROMPT_EXPAND_CONTENT.format(
        title=title or "（无标题）",
        content=content or "（无内容）",
        block_count=block_count,
    )


def parse_expanded_blocks(llm_output: str, expected_count: int = None) -> list:
    """
    解析LLM输出的扩写块

    Args:
        llm_output: LLM返回的文本
        expected_count: 期望的块数（用于校验）

    Returns:
        内容块列表
    """
    import re

    if not llm_output:
        return []

    blocks = []
    # 匹配【块N】xxx 格式
    pattern = r"【块\d+】\s*([\s\S]*?)(?=【块\d+】|$)"
    matches = re.findall(pattern, llm_output)

    for match in matches:
        block_text = match.strip()
        if block_text:
            blocks.append(block_text)

    # 如果解析失败，尝试按段落分割
    if not blocks:
        paragraphs = [p.strip() for p in llm_output.split("\n\n") if p.strip()]
        for p in paragraphs:
            # 去掉可能的编号前缀
            cleaned = re.sub(r"^\d+[\.、）]\s*", "", p)
            if cleaned:
                blocks.append(cleaned)

    # 校验数量
    if expected_count and len(blocks) != expected_count:
        # 如果块数不对，尝试简单分割
        if len(blocks) < expected_count:
            # 块数不够，尝试进一步分割
            new_blocks = []
            for block in blocks:
                sentences = re.split(r"(?<=[。！？!?；;])\s*", block)
                sentences = [s.strip() for s in sentences if s.strip()]
                if len(sentences) >= 2 and len(new_blocks) + len(sentences) <= expected_count:
                    new_blocks.extend(sentences)
                else:
                    new_blocks.append(block)
            blocks = new_blocks[:expected_count]

            # 如果还是不够，用最后一个块补齐
            while len(blocks) < expected_count:
                blocks.append(blocks[-1] if blocks else "重点内容")
        else:
            # 块数太多，合并
            while len(blocks) > expected_count:
                # 找到最短的两个相邻块合并
                min_idx = 0
                min_total = float('inf')
                for i in range(len(blocks) - 1):
                    total = len(blocks[i]) + len(blocks[i + 1])
                    if total < min_total:
                        min_total = total
                        min_idx = i
                blocks[min_idx] = blocks[min_idx] + "\n" + blocks[min_idx + 1]
                blocks.pop(min_idx + 1)

    return blocks
