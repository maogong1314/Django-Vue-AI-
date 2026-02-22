import re

from rest_framework.exceptions import ValidationError


FORBIDDEN_CHAR_MAP = {
    "<": "＜",
    ">": "＞",
    '"': "＂",
    "'": "＇",
    "`": "｀",
}

FORBIDDEN_CHAR_PATTERN = re.compile(r"[<>\"'`]")
XSS_KEYWORD_PATTERN = re.compile(
    r"(javascript:|data:text/html|vbscript:|onerror\s*=|onload\s*=|onmouseover\s*=|<\s*/?\s*script\b)",
    re.IGNORECASE,
)


def sanitize_user_input(value, field_name="输入内容", required=True):
    """
    对用户输入进行严格特殊字符过滤，拦截常见 XSS 载荷。
    """
    if value is None:
        value = ""

    text = str(value).strip()
    if required and not text:
        raise ValidationError({field_name: "不能为空"})

    if not text:
        return text

    if XSS_KEYWORD_PATTERN.search(text):
        raise ValidationError({field_name: "包含非法脚本特征，已被安全策略拦截"})

    return FORBIDDEN_CHAR_PATTERN.sub(lambda m: FORBIDDEN_CHAR_MAP[m.group(0)], text)


def ensure_positive_int(value, field_name="ID"):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValidationError({field_name: "必须是正整数"})

    if parsed <= 0:
        raise ValidationError({field_name: "必须是正整数"})

    return parsed
