import string
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Union

from analyzer import LexerAnalyzer, Analyzer
from lexem import Lexem


class Lexers:
    def __init__(self, lexers: List[Lexem]):
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


@dataclass
class ASTNode:
    name: str
    data: Dict = field(default_factory=dict)


reserved_words = {
    "VAR",
    "BEGIN",
    "END",
    "INTEGER",
    "CASE",
    "OF",
    "END_CASE",
    "WRITE",
    "READ",
    "AND",
    "LOGICAL",
    "OR",
    "EQ",
    "IF",
    "THEN",
    "ELSE",
    "ENDIF",
}


class PascalLexerAnalyzer(LexerAnalyzer):
    def __init__(self):
        include_separators = {
            "PLUS": "+",
            "MINUS": "-",
            "DIV": "/",
            "ASSIGN_OP": "=",
            "OR": "OR",
            "EQ": "EQ",
            "COLON": ":",
            "COMMA": ",",
            "SEMICOLON": ";",
            "PAR_OPEN": "(",
            "PAR_CLOSE": ")",
        }
        ignore_separators = {"SPACE": " ", "NEW_LINE": "\n"}
        regex_terms = {"IDENTIFIER": r"^([A-Za-z]{1,11})$", "CONST": r"^([0-9]+)$"}
        super().__init__(
            regex_terms,
            reserved_words,
            include_separators=include_separators,
            ignore_separators=ignore_separators,
        )


pascal_terms = {
    "VAR",
    "BEGIN",
    "END",
    "INTEGER",
    "CASE",
    "OF",
    "END_CASE",
    "=",
    "+",
    "-",
    "/",
    "WRITE",
    "READ",
    ":",
    ";",
    " ",
    "AND",
    "LOGICAL",
    "OR",
    "EQ",
    "IF",
    "THEN",
    "ELSE",
    "ENDIF",
}
pascal_terms.update(*string.ascii_lowercase.split())
pascal_terms.update(*[str(i) for i in range(10)])


class PascalSyntaxAnalyzer(Analyzer):
    def __init__(self):
        rules: Dict[str, List[Union[Tuple[str]], str]] = {
            "<PROGRAM>": [("<VAR_DEFINITION>", "<COMPUTATIONS>")],
            "<VAR_DEFINITION>": [("VAR", "<VAR_LIST>", ":", "INTEGER", ";")],
            "<COMPUTATIONS>": [("BEGIN", "<ASSIGN_LIST>", "END")],
            "<ASSIGN_LIST>": [("<ASSIGN>", "<ASSIGN_LIST_>")],
            "<ASSIGN_LIST_>": ["<ASSIGN_LIST>", ";"],
            "<VAR_LIST>": [("<IDENTIFIER>", "<VAR_LIST_>")],
            "<VAR_LIST_>": ["<VAR_LIST>", ""],
            "<EXPRESSION>": [
                ("<UNARY_OPERATOR>", "<SUB_EXPRESSION>"),
                ("<SUB_EXPRESSION>",),
            ],
            "<ASSIGN>": [("<IDENTIFIER>", "=", "<EXPRESSION>", ";")],
            "<SUB_EXPRESSION>": [
                ("(", "<EXPRESSION>", ")"),
                "<OPERAND>",
                ("<SUB_EXPRESSION>", "<BINARY_OPERATOR>", "<SUB_EXPRESSION>"),
            ],
            "<BINARY_OPERATOR>": ["+", "-", "/"],
            "<UNARY_OPERATOR>": ["-"],
            "<OPERAND>": ["<IDENTIFIER>", "<CONST>"],
            "<FUNCTION>": [
                ("READ", "(", "<VAR_LIST>", ")"),
                ("WRITE", "(", "<VAR_LIST>", ")"),
            ],
            "<CASE>": [("CASE", "<EXPRESSION>", "OF", "<CHOICE_LIST>", "END_CASE")],
            "<CHOICE_LIST>": ["<CHOICE>", ("<CHOICE>", "<CHOICE_LIST>")],
            "<CHOICE>": [("<CONST>", ":", "<ASSIGN>")],
        }
        self.available_vars = []
        super().__init__(rules, pascal_terms)

    def translate(self, lexers: List[Lexem]):
        lexers = Lexers(lexers)

        root = ASTNode(
            "PROGRAM",
            {
                "var_def": self.get_var_def(lexers),
                "statements": self.get_statements(lexers),
            },
        )
        return root

    def get_var_def(self, lexers: Lexers):
        if lexers.cur_lex.name != "VAR":
            raise ValueError('Expected VAR')

        lexers.read_next_lex()
        variables = self.get_identifier_list(lexers)
        if lexers.cur_lex.name != ':':
            raise ValueError('Expected ":"')
        lexers.read_next_lex()
        if lexers.cur_lex.name != 'INTEGER':
            raise ValueError('Expected "INTEGER"')
        lexers.read_next_lex()
        if lexers.cur_lex.name != ';':
            raise ValueError
        lexers.read_next_lex()

        self.available_vars = variables

        return ASTNode("var_def", {"variables": variables})

    def get_identifier_list(self, lexers):
        if lexers.cur_lex.name != "IDENTIFIER":
            raise ValueError
        variables = []
        while lexers.cur_lex.name == "IDENTIFIER":
            variables.append(lexers.cur_lex.value)
            lexers.read_next_lex()
            if lexers.cur_lex.name != ",":
                break
            lexers.read_next_lex()
        return variables

    def get_statements(self, lexers: Lexers):
        if lexers.cur_lex.name != "BEGIN":
            raise ValueError
        lexers.read_next_lex()
        statements = []
        while lexers.cur_lex and lexers.cur_lex.name != "END":
            statements.append(self.get_statement(lexers))

        if lexers.cur_lex.name != "END":
            raise ValueError
        lexers.read_next_lex()

        data = {"statements": statements}
        return ASTNode("statements", data)

    def get_statement(self, lexers: Lexers):
        if lexers.cur_lex.name == "IDENTIFIER":
            node = self.get_assign(lexers)
        elif lexers.cur_lex.name == "WRITE" or lexers.cur_lex.name == "READ":
            node_name = lexers.cur_lex.name.lower()
            lexers.read_next_lex()
            if lexers.cur_lex.name != '(':
                raise ValueError('( expected')
            lexers.read_next_lex()
            variables = self.get_identifier_list(lexers)
            if lexers.cur_lex.name != ')':
                raise ValueError(') expected')
            lexers.read_next_lex()
            node = ASTNode(node_name, {"variables": variables})
        elif lexers.cur_lex.name == "CASE":
            lexers.read_next_lex()
            expr = self.get_expr(lexers)
            if lexers.cur_lex.name != "OF":
                raise ValueError
            lexers.read_next_lex()
            choices = self.get_choice_list(lexers)
            if lexers.cur_lex.name != "END_CASE":
                raise ValueError
            lexers.read_next_lex()
            node = ASTNode("case", {"expr": expr, "choices": choices})
        else:
            raise ValueError
        if lexers.cur_lex.name != ";":
            raise ValueError
        lexers.read_next_lex()
        return node

    def get_choice_list(self, lexers):
        choices = {}
        while True:
            if lexers.cur_lex.name != "CONST":
                raise ValueError
            val = lexers.cur_lex.value
            lexers.read_next_lex()
            if lexers.cur_lex.name != ":":
                raise ValueError
            lexers.read_next_lex()
            assign = self.get_assign(lexers)
            if lexers.cur_lex.name != ";":
                raise ValueError
            choices[val] = assign

            lexers.read_next_lex()
            if lexers.cur_lex.name == "END_CASE":
                return choices

    def get_assign(self, lexers):
        if lexers.cur_lex.value not in self.available_vars:
            raise ValueError(f'Unknown variable {lexers.cur_lex.value}')
        data = {"left": lexers.cur_lex.value}
        lexers.read_next_lex()
        if lexers.cur_lex.name != "=":
            raise ValueError('= expected')
        lexers.read_next_lex()
        data["right"] = self.get_expr(lexers)
        return ASTNode("assign", data)

    def get_expr(self, lexers: Lexers):
        if lexers.cur_lex.name == "(":
            lexers.read_next_lex()
            expr = self.get_expr(lexers)
            if lexers.cur_lex.name != ")":
                return ValueError
            lexers.read_next_lex()

            node = ASTNode("parentheses_expr", {"expr": expr})

            if (
                not lexers.cur_lex
                or lexers.cur_lex.name == ")"
                or lexers.cur_lex.name == ";"
            ):
                return node
            if lexers.cur_lex.name not in ("+", "-", "/"):
                raise ValueError
            operand1 = node
            op = lexers.cur_lex.name
            lexers.read_next_lex()
            operand2 = self.get_expr(lexers)
            # lexers.read_next_lex()  # (
            return ASTNode(
                "expr", {"operand1": operand1, "op": op, "operand2": operand2}
            )
        if lexers.cur_lex.name == "CONST" or lexers.cur_lex.name == "IDENTIFIER":
            operand1 = lexers.cur_lex.value
            lexers.read_next_lex()
            if (
                not lexers.cur_lex
                or lexers.cur_lex.name == ")"
                or lexers.cur_lex.name == ";"
                or lexers.cur_lex.name == "OF"
            ):
                return operand1

            if lexers.cur_lex.name not in ("+", "-", "/"):
                raise ValueError
            op = lexers.cur_lex.name
            lexers.read_next_lex()
            operand2 = self.get_expr(lexers)
            return ASTNode(
                "expr", {"operand1": operand1, "op": op, "operand2": operand2}
            )
        if lexers.cur_lex.name == "-":
            op = lexers.cur_lex.name
            lexers.read_next_lex()
            operand1 = self.get_expr(lexers)
            return ASTNode("expr", {"operand1": operand1, "op": op})
