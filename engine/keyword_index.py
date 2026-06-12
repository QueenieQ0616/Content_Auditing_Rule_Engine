"""Keyword index with optional Aho-Corasick acceleration."""

import re
from typing import Iterable, List, Set

try:
    import ahocorasick

    _HAS_AC = True
except ImportError:
    ahocorasick = None
    _HAS_AC = False


def normalize_text(text: object) -> str:
    """归一化文本，去除常见规避分隔符，降低大小写差异影响。"""
    text = str(text).lower()
    return re.sub(r"[\s/\\|_\-·•.。,，、:：;；!！?？()[\]{}<>《》\"'“”‘’]+", "", text)


def _has_cjk(text: str) -> bool:
    """判断文本中是否包含中文字符。"""
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def fuzzy_keyword_hit(keyword: object, content: object, max_gap: int = 2) -> bool:
    """支持符号拆分和少量插字的关键词模糊命中。"""
    normalized_keyword = normalize_text(keyword)
    normalized_content = normalize_text(content)

    if not normalized_keyword or not normalized_content:
        return False
    if normalized_keyword in normalized_content:
        return True
    if len(normalized_keyword) < 2 or not _has_cjk(normalized_keyword):
        return False

    gap_pattern = f".{{0,{max_gap}}}"
    pattern = gap_pattern.join(re.escape(char) for char in normalized_keyword)
    return re.search(pattern, normalized_content) is not None


class KeywordIndex:
    """Global keyword index built once at startup."""

    def __init__(self) -> None:
        self.words: List[str] = []
        self.automaton = None

    def build(self, words: Iterable[str]) -> None:
        self.words = sorted({str(word) for word in words if str(word)})
        self.automaton = None

        if _HAS_AC:
            automaton = ahocorasick.Automaton()
            for word in self.words:
                normalized_word = normalize_text(word)
                if normalized_word:
                    automaton.add_word(normalized_word, word)
            automaton.make_automaton()
            self.automaton = automaton

    def search(self, content: str) -> Set[str]:
        if not content:
            return set()

        normalized_content = normalize_text(content)
        fuzzy_hits = {word for word in self.words if fuzzy_keyword_hit(word, normalized_content)}

        if self.automaton is not None:
            exact_hits = {word for _, word in self.automaton.iter(normalized_content)}
            return exact_hits | fuzzy_hits

        return fuzzy_hits


keyword_index = KeywordIndex()
