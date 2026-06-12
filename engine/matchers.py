"""Condition matchers for keyword, regex, length, and future model checks."""

import re
from typing import List, Optional, Set

from .keyword_index import fuzzy_keyword_hit


def match_keyword(
    content: str,
    value: object,
    match: str = "any",
    hit_words: Optional[Set[str]] = None,
) -> bool:
    if not isinstance(value, list):
        value = [value]

    if hit_words is not None:
        hits = [word for word in value if word in hit_words or fuzzy_keyword_hit(word, content)]
    else:
        hits = [word for word in value if fuzzy_keyword_hit(word, content)]

    if match == "all":
        return len(hits) == len(value)
    return len(hits) > 0


def match_regex(content: str, value: object) -> bool:
    try:
        return re.search(str(value), content) is not None
    except re.error:
        return False


def match_length(content: str, value: object) -> bool:
    return len(content) >= int(value)


def match_model(content: str, value: object) -> bool:
    return False


MATCHERS = {
    "keyword": match_keyword,
    "regex": match_regex,
    "length": match_length,
    "model": match_model,
}


def run_condition(content: str, condition, hit_words: Optional[Set[str]] = None) -> bool:
    matcher = MATCHERS.get(condition.type)
    if matcher is None:
        return False
    if condition.type == "keyword":
        return matcher(content, condition.value, condition.match, hit_words=hit_words)
    return matcher(content, condition.value)
