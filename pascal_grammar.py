from lexer_analyzer import LexerAnalyzer, Lexers
from nodes import (
    ParenthesesNode,
    ExpressionNode,
    AssignNode,
    ProgramNode,
    FuncNode,
    CaseNode,
)

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
}


class PascalLexerAnalyzer(LexerAnalyzer):
    def __init__(self):
        include_separators = ["+", "-", "/", "=", ":", ",", ";", "(", ")"]
        ignore_separators = [" ", "\n"]
        regex_terms = {"IDENTIFIER": r"^([A-Za-z]{1,11})$", "CONST": r"^([0-9]+)$"}
        super().__init__(
            regex_terms,
            reserved_words,
            include_separators=include_separators,
            ignore_separators=ignore_separators,
        )


def endswith(terms):
    def decorator(function):
        def wrapper(self, lexers, *args):
            result = function(self, lexers, *args)
            assert_terms_equal(terms, lexers)
            return result

        return wrapper

    return decorator


def startswith(terms, read_next=True):
    def decorator(function):
        def wrapper(self, lexers, *args):
            assert_terms_equal(terms, lexers, read_next)
            result = function(self, lexers, *args)
            return result

        return wrapper

    return decorator


endswith_semicolon = endswith([";"])


def assert_terms_equal(terms, lexers: Lexers, read_next=True):
    for term in terms:
        if not lexers.cur_lex:
            raise ValueError(f'Expected "{term}"')
        if lexers.cur_lex.name != term:
            raise ValueError(f'Unexpected "{lexers.cur_lex.name}", expected "{term}"')
        if read_next:
            lexers.read_next_lex()


class PascalSyntaxAnalyzer:
    def __init__(self):
        self.available_vars = []

    def translate(self, lexers: Lexers):
        return ProgramNode(
            variables=self.get_var_def(lexers), statements=self.get_statements(lexers)
        )

    @startswith(["VAR"])
    @endswith([":", "INTEGER", ";"])
    def get_var_def(self, lexers: Lexers):
        self.available_vars = self.get_identifier_list(lexers)
        return self.available_vars

    @startswith(["IDENTIFIER"], read_next=False)
    def get_identifier_list(self, lexers):
        identifiers = []
        while lexers.cur_lex.name == "IDENTIFIER":
            identifiers.append(lexers.cur_lex.value)
            lexers.read_next_lex()
            if lexers.cur_lex.name != ",":
                break
            lexers.read_next_lex()
        return identifiers

    @startswith(["BEGIN"])
    @endswith(["END"])
    def get_statements(self, lexers: Lexers):
        statements = []
        while lexers.cur_lex and lexers.cur_lex.name != "END":
            statements.append(self.get_statement(lexers))
        return statements

    @endswith_semicolon
    def get_statement(self, lexers: Lexers):
        if lexers.cur_lex.name == "IDENTIFIER":
            node = self.get_assign(lexers)
        elif lexers.cur_lex.name == "WRITE" or lexers.cur_lex.name == "READ":
            func_name = lexers.cur_lex.name.lower()
            lexers.read_next_lex()
            assert_terms_equal(["("], lexers)
            variables = self.get_identifier_list(lexers)
            assert_terms_equal([")"], lexers)
            node = FuncNode(name=func_name, args=variables)
        elif lexers.cur_lex.name == "CASE":
            node = self.get_case(lexers)
        else:
            raise ValueError("Invalid statement")
        return node

    @endswith(["END_CASE"])
    @startswith(["CASE"])
    def get_case(self, lexers):
        expr = self.get_expr(lexers)
        assert_terms_equal(["OF"], lexers)
        choices = self.get_choice_list(lexers)
        return CaseNode(expr=expr, choices=choices)

    def get_choice_list(self, lexers):
        choices = {}
        while lexers.cur_lex and lexers.cur_lex.name != "END_CASE":
            val, assign = self.get_choice(lexers)
            choices[val] = assign
        return choices

    @startswith(["CONST"], read_next=False)
    @endswith_semicolon
    def get_choice(self, lexers):
        val = lexers.cur_lex.value
        lexers.read_next_lex()
        assert_terms_equal([":"], lexers)
        return val, self.get_assign(lexers)

    @startswith(["IDENTIFIER"], read_next=False)
    def get_assign(self, lexers):
        if lexers.cur_lex.value not in self.available_vars:
            raise ValueError(f"Unknown variable {lexers.cur_lex.value}")
        left = lexers.cur_lex.value
        lexers.read_next_lex()
        assert_terms_equal(["="], lexers)
        return AssignNode(left=left, right=self.get_expr(lexers))

    def get_expr(self, lexers: Lexers):
        if lexers.cur_lex.name == "(":
            node = self.get_parentheses_expr(lexers)

            if lexers.cur_lex.name not in ("+", "-", "/"):
                if lexers.cur_lex.name == ')':
                    return node
                else:
                    raise ValueError(f'Unexpected {lexers.cur_lex}')
            operand1 = node
            op = lexers.cur_lex.name
            lexers.read_next_lex()
            operand2 = self.get_expr(lexers)
            return ExpressionNode(operand1=operand1, op=op, operand2=operand2)
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
            if not operand2:
                raise ValueError('Second argument not found.')
            return ExpressionNode(operand1=operand1, op=op, operand2=operand2)
        if lexers.cur_lex.name == "-":
            op = lexers.cur_lex.name
            lexers.read_next_lex()
            operand1 = self.get_expr(lexers)
            return ExpressionNode(operand1=operand1, op=op)

    @startswith(["("])
    @endswith([")"])
    def get_parentheses_expr(self, lexers):
        return ParenthesesNode(node=self.get_expr(lexers))
