"""
得物掘金工具 - URL 解析工具
"""
import re
from typing import Optional


# 得物商品页 URL 正则：匹配 dw4.co 短链或 dewu.com 商品链接
# 只匹配 URL 合法字符，遇到中文或其他非法字符立即停止
_DEWU_URL_PATTERN = re.compile(
    r'(https?://(?:dw4\.co|(?:www\.)?dewu\.com)[A-Za-z0-9/\-_.?=&#%+~:]*)'
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
        url = match.group(0)
        # 仅当括号不平衡时才去掉末尾的 )，避免误截合法 URL
        if url.endswith(")") and url.count("(") < url.count(")"):
            url = url[:-1]
        return url
    return None
