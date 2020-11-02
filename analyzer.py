import re
import string
from dataclasses import dataclass
from typing import List, Dict, Set

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
        self.transition_funcs: List[TransitionFunc] = self.init_transition_funcs()
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
        slashed_terms = [f'\\{term}' for term in self.terms if term in ('+')]
        term_groups = [f'({term})' for term in slashed_terms]
        regex = '|'.join([token_pattern, *term_groups])
        print(regex)
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
                for first in self.get_first(rule[0]):
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


def analyze(code, rules):
    stack = ['$']
    while code:
        let = code[0]
        for left, right in rules.items():
            first = {}


if __name__ == '__main__':
    with open('test_program.txt', 'r') as file:
        code = ''.join(file.readlines())

    terms = {
        'VAR', 'BEGIN', 'END', 'INTEGER', 'CASE', 'OF', 'END_CASE', '=', '+',
        '-', '/', 'WRITE', 'READ', ':', ';', ' '
    }
    terms.update(*string.ascii_lowercase.split())
    rules = {
        '<PROGRAM>': ('<VAR_DEFINITION><COMPUTATIONS>',),
        '<VAR_DEFINITION>': ('VAR<VAR_LIST>:INTEGER;',),
        '<COMPUTATIONS>': ('BEGIN<VAR_LIST>END',),
        '<ASSIGN_LIST>': ('<ASSIGN><ASSIGN_LIST_>',),
        '<ASSIGN_LIST_>': ('<ASSIGN_LIST>', ''),
        '<VAR_LIST>': ('<IDENTIFIER><VAR_LIST_>',),
        '<VAR_LIST_>': ('<VAR_LIST>', ''),
        '<IDENTIFIER>': ('<LETTER><IDENTIFIER_>',),
        '<IDENTIFIER_>': ('<IDENTIFIER>', ''),
        '<CONST>': [str(i) for i in range(10)],
        '<LETTER>': list(string.ascii_lowercase),
        '<EXPRESSION>': ('', ),
        '<ASSIGN>': ('', )
        # присваивание
        # выражение
        # подвыражение
        # операнд
        # унарный оператор
        # бинарный оператор
        # case
        # список функций
        # actions list
        # список выбора
        # выбор х2
    }
    a = Analyzer(rules, terms)
    print(a.init_transition_funcs())
    # analyze(code, rules)
