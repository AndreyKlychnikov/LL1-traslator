import re
from typing import Dict, List, Union

from lexem import ExtendedLexem, Lexem

token_pattern = r"(<[A-Za-z_]+>)"


class Lexers:
    def __init__(self, lexers: List[Union[Lexem, ExtendedLexem]]):
        self.lexers = lexers
        self.idx = 0

    @property
    def cur_lex(self):
        try:
            return self.lexers[self.idx]
        except IndexError:
            return None

    def read_next_lex(self):
        self.idx += 1


class LexerAnalyzer:
    def __init__(
        self,
        regex_terms: Dict[str, str],
        reserved_words,
        include_separators=None,
        ignore_separators=None,
    ):
        self.regex_terms = regex_terms
        self.reserved_words = reserved_words
        self.separators = self.get_separators(include_separators, ignore_separators)

    def analyze(self, code) -> Lexers:
        lexers = []
        buffer = ""
        code += " "
        for letter in code:
            buffer += letter
            sep = self.test_sep_ending(buffer)
            if not sep:
                continue

            buffer = buffer[: -len(sep)]
            if buffer:
                if buffer in self.reserved_words:
                    lexers.append(Lexem(buffer))
                else:
                    lex, value = self.test_regex_lex(buffer)
                    if lex and value:
                        lexers.append(ExtendedLexem(name=lex, value=value))
                    else:
                        raise ValueError(f"Unknown lexer {buffer}")
                buffer = ""
            if not self.separators[sep]:
                lexers.append(Lexem(sep))

        if buffer:
            raise ValueError
        return Lexers(lexers)

    def test_regex_lex(self, buffer):
        for lex_name, regex in self.regex_terms.items():
            match = re.match(regex, buffer)
            if match:
                return lex_name, match.group(1)
        return None, None

    def test_sep_ending(self, buffer):
        for sep in self.separators:
            if buffer.endswith(sep):
                return sep
        return None

    @staticmethod
    def get_separators(include_separators, ignore_separators) -> Dict[str, bool]:
        separators = {}
        for val in include_separators:
            separators[val] = False
        for val in ignore_separators:
            separators[val] = True
        return separators
