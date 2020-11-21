import re
from dataclasses import dataclass
from typing import Dict, Set

from lexem import ExtendedLexem, Separator

token_pattern = r'(<[A-Za-z_]+>)'


@dataclass
class TransitionFunc:
    state: int
    input_term: str
    write_symbol: str
    transition_state: int
    output_sequence: str
    read_input: bool = True


class Analyzer:
    def __init__(self, rules: Dict, terms: Set):
        self.terms = terms
        self.rules = self.normalize_rules(rules)
        # self.transition_funcs: List[TransitionFunc] = self.init_transition_funcs()
        self.transition_table = self.init_transition_table()

    def normalize_rules(self, rules: Dict) -> Dict:
        for left, right in rules.items():
            rules[left] = [self.normalize_rules_right(rules_right) for rules_right in right]
        return rules

    def normalize_rules_right(self, right):
        symbols = self.split_rules_right(right)
        alt = []
        for symbol in symbols:
            if not re.match(token_pattern, symbol):
                alt.extend(list(symbol))
            else:
                alt.append(symbol)
        return alt

    def split_rules_right(self, right):
        slashed_terms = []
        for term in self.terms:
            if term in ('+',):
                term = f'\\{term}'
            slashed_terms.append(term)
        term_groups = [f'({term})' for term in slashed_terms]
        regex = '|'.join([token_pattern, *term_groups])
        return [s for s in re.split(regex, right) if s]

    def get_first(self, symbol):
        if not re.match(token_pattern, symbol):
            return [symbol]
        rule = self.rules[symbol]
        first = []
        for alt in rule:
            first.extend(self.get_first(alt[0]))
        return first

    def get_follow(self, symbol):
        follow = set()
        for _, rules in self.rules.items():
            for rule in rules:
                try:
                    idx = rule.index(symbol)
                except ValueError:
                    continue
                try:
                    follow.update(self.get_first(rule[idx + 1]))
                except IndexError:
                    pass

        return follow

    def init_transition_funcs(self):
        funcs = []
        for not_term, rules in self.rules.items():
            for rule in rules:
                if rule:
                    for x in self.get_follow(not_term):
                        funcs.append(
                            TransitionFunc(
                                state=0, input_term=x, write_symbol=not_term, transition_state=0, output_sequence=''
                            )
                        )
                    continue
                if re.match(token_pattern, rule[0]):
                    funcs.append(
                        TransitionFunc(0, rule[0], not_term, 0, ''.join(rule[1::-1]))
                    )
                else:
                    for x in self.get_first(rule[0]):
                        funcs.append(
                            TransitionFunc(
                                state=0, input_term=x, write_symbol=not_term, transition_state=0,
                                output_sequence=''.join(rule[1::-1] + [rule[0]])
                            )
                        )
        for term in self.terms - self.term_on_first_place:
            funcs.append(
                TransitionFunc(
                    state=0, input_term=term, write_symbol=term, transition_state=0, output_sequence=''
                )
            )
        return funcs

    def init_transition_table(self):
        table = {}
        for not_term, rules in self.rules.items():
            for rule in rules:
                if rule:
                    rules_first = rule[0]
                else:
                    rules_first = ''
                for first in self.get_first(rules_first):
                    table[(not_term, first)] = rule
        return table

    @property
    def term_on_first_place(self):
        terms = set()
        for _, rules in self.rules.items():
            for rule in rules:
                if rule and re.match(token_pattern, rule[0]):
                    terms.add(rule[0])
        return terms

    def analyze(self, code, start_symbol):
        stack = ['$', start_symbol]
        read_idx = 0
        code_len = len(code)
        lexers = []

        while read_idx < code_len:
            symbol = code[read_idx]

            if stack[-1] == '$':
                raise ValueError(f'Unexpected symbols: "{code[read_idx:]}"')

            if re.match(token_pattern, stack[-1]):
                not_term = stack.pop()
                lexers.append(not_term)
                try:
                    right = self.transition_table[(not_term, symbol)]
                    stack.extend(right[::-1])
                except KeyError:
                    raise ValueError(f'Unexpected symbol "{symbol}"')
            elif symbol == stack[-1]:
                stack.pop()
                read_idx += 1
            else:
                raise ValueError(f'Unexpected symbol "{symbol}", expected "{stack[-1]}"')
        return lexers


class LexerAnalyzer:
    def __init__(self, regex_terms: Dict[str, str], reserved_words, include_separators=None, ignore_separators=None):
        self.regex_terms = regex_terms
        self.reserved_words = reserved_words
        self.separators = self.get_separators(include_separators, ignore_separators)

    def analyze(self, code):
        lexers = []
        buffer = ''
        code += ' '
        for letter in code:
            buffer += letter
            sep = self.test_sep_ending(buffer)
            if not sep:
                continue

            buffer = buffer[:-len(sep)]
            if buffer:
                if buffer in self.reserved_words:
                    lexers.append(buffer)
                else:
                    lex, value = self.test_regex_lex(buffer)
                    if lex and value:
                        lexers.append(ExtendedLexem(name=lex, value=value))
                    else:
                        raise ValueError
                buffer = ''
            if not self.separators[sep].ignore:
                lexers.append(sep)

        if buffer:
            raise ValueError
        return lexers

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
    def get_separators(include_separators, ignore_separators) -> Dict[str, Separator]:
        separators = {}
        for name, val in include_separators.items():
            separators[val] = Separator(name, val, ignore=False)
        for name, val in ignore_separators.items():
            separators[val] = Separator(name, val, ignore=True)
        return separators
