"""
匹配器 —— 每种条件 type 对应一个匹配器，负责判断「这个条件命中没有」。
新增一种判断能力 = 加一个匹配器函数 + 在 MATCHERS 里注册，规则结构不用动。

本期实现 keyword / regex / length；model 预留。
"""
import re
from typing import List


def match_keyword(content: str, value: List[str], match: str = "any") -> bool:
    """
    词库匹配。本骨架先用最朴素的 in 判断，跑通流程用。
    TODO(A->性能优化阶段): 换成 AC 自动机(pyahocorasick)，词库大时速度才够。
    """
    if not isinstance(value, list):
        value = [value]
    hits = [w for w in value if w in content]
    if match == "all":
        return len(hits) == len(value)
    return len(hits) > 0  # any


def match_regex(content: str, value: str, **_) -> bool:
    """正则匹配。"""
    try:
        return re.search(value, content) is not None
    except re.error:
        return False


def match_length(content: str, value: int, **_) -> bool:
    """长度特征：内容长度 >= value 时命中。可按需扩展。"""
    return len(content) >= int(value)


def match_model(content: str, value=None, **_) -> bool:
    """模型匹配器（预留）。本期不实现，恒返回 False。"""
    # TODO(扩展): 调用文本分类模型，分数超阈值则命中
    return False


# 匹配器注册表：type -> 函数
MATCHERS = {
    "keyword": match_keyword,
    "regex": match_regex,
    "length": match_length,
    "model": match_model,
}


def run_condition(content: str, condition) -> bool:
    """根据 condition.type 找到对应匹配器并执行。"""
    matcher = MATCHERS.get(condition.type)
    if matcher is None:
        return False  # 未知类型，安全起见判为不命中
    kwargs = {}
    if condition.type == "keyword":
        kwargs["match"] = condition.match
    return matcher(content, condition.value, **kwargs)
