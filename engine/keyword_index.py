"""Keyword index with optional Aho-Corasick acceleration."""

from typing import Iterable, List, Set

try:
    import ahocorasick

    _HAS_AC = True
except ImportError:
    ahocorasick = None
    _HAS_AC = False


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
                automaton.add_word(word, word)
            automaton.make_automaton()
            self.automaton = automaton

    def search(self, content: str) -> Set[str]:
        if not content:
            return set()

        if self.automaton is not None:
            return {word for _, word in self.automaton.iter(content)}

        return {word for word in self.words if word in content}


keyword_index = KeywordIndex()
