"""
得物掘金工具 - URL 解析工具
"""
import re
from typing import Optional


# 得物商品页 URL 正则：匹配 m.dewu.com 或 dewu.com 商品链接
_DEWU_URL_PATTERN = re.compile(
    r"https?://(?:m\.)?dewu\.com/[^\s\"'<>]+"
)


def extract_dewu_url(text: str) -> Optional[str]:
    """从分享文本中提取得物商品页 URL。

    Args:
        text: 用户粘贴的分享文本，可能包含多余文字。

    Returns:
        第一个匹配的得物 URL，未找到则返回 None。
    """
    match = _DEWU_URL_PATTERN.search(text)
    if match:
        return match.group(0).rstrip(")")
    return None
