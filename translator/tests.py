from unittest import TestCase

from lexem import ExtendedLexem, Lexem
from lexer_analyzer import LexerAnalyzer
from nodes import (
    ProgramNode,
    AssignNode,
    CaseNode,
    ExpressionNode,
    FuncNode,
)
from pascal_grammar import PascalSyntaxAnalyzer, PascalLexerAnalyzer
from python_translator import PythonTranslator


class LexerAnalyzerTestCase(TestCase):
    def test_analyze(self):
        terms = {
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

        code = """
            VAR a, b :INTEGER;
            BEGIN
            a = 1;
            b = 2999999999;
            END
            """
        include_separators = ["+", "-", "/", "=", ":", ",", ";", "(", ")", "OR"]
        ignore_separators = [" ", "\n"]
        regex_terms = {"IDENTIFIER": r"^([A-Za-z]{1,11})$", "CONST": r"^([0-9]+)$"}

        a = LexerAnalyzer(
            regex_terms,
            terms,
            include_separators=include_separators,
            ignore_separators=ignore_separators,
        )
        print(a.analyze(code))

        code = "BEGINEND"

        lexers = a.analyze(code)
        self.assertListEqual(
            [ExtendedLexem(name="IDENTIFIER", value="BEGINEND")], lexers.lexers
        )

        code = "123 OR aaa"
        lexers = a.analyze(code)
        self.assertListEqual(
            [
                ExtendedLexem("CONST", "123"),
                Lexem("OR"),
                ExtendedLexem("IDENTIFIER", "aaa"),
            ],
            lexers.lexers,
        )


class ParserTestCase(TestCase):
    def test_analyze(self):
        lexer_analyzer = PascalLexerAnalyzer()
        parser = PascalSyntaxAnalyzer()
        code = """
                VAR a, b: INTEGER;
                BEGIN
                    a = 2;
                    CASE a OF
                        1: a = 2;
                        2: b = -a + 2;
                    END_CASE;
                    WRITE(a, b);
                END
                """
        lexers = lexer_analyzer.analyze(code)
        ast = parser.translate(lexers)
        self.assertEqual(
            ProgramNode(
                variables=["a", "b"],
                statements=[
                    AssignNode(left="a", right="2"),
                    CaseNode(
                        expr="a",
                        choices={
                            "1": AssignNode(left="a", right="2"),
                            "2": AssignNode(
                                left="b",
                                right=ExpressionNode(
                                    operand1=ExpressionNode(
                                        operand1="a", operand2="2", op="+"
                                    ),
                                    operand2=None,
                                    op="-",
                                ),
                            ),
                        },
                    ),
                    FuncNode(name="write", args=["a", "b"]),
                ],
            ),
            ast,
        )
        print(ast)


class PythonTranslatorTestCase(TestCase):
    def test_get_statement_code(self):
        lexer_analyzer = PascalLexerAnalyzer()
        parser = PascalSyntaxAnalyzer()
        code = """
        VAR a, b, c: INTEGER;
        BEGIN
            a = 2;
            b = 3;
            c = 4;
            CASE a / 2 OF
                1: b = 4;
                2: c = -b + c;
                3: b = (654 - 54 + a) + 12;
            END_CASE;
            WRITE(a, b, c);
        END
        """
        lexers = lexer_analyzer.analyze(code)
        ast = parser.translate(lexers)
        print(ast)
        translator = PythonTranslator()
        print(translator.get_code_from_ast(ast))
        compiled = compile(translator.get_code_from_ast(ast), "<string>", "exec")

        exec(compiled)

    def test_raise_error(self):
        lexer_analyzer = PascalLexerAnalyzer()
        parser = PascalSyntaxAnalyzer()
        code = "VAR a, b, c; INTEGER;"
        lexers = lexer_analyzer.analyze(code)
        with self.assertRaises(ValueError):
            parser.translate(lexers)

        code = "VAR a, b, c: IVTEGER;"
        lexers = lexer_analyzer.analyze(code)
        with self.assertRaises(ValueError):
            parser.translate(lexers)

        code = "VAR a, b, c: INTEGER"
        lexers = lexer_analyzer.analyze(code)
        with self.assertRaises(ValueError):
            parser.translate(lexers)

    def test_get_statement_raise_error(self):
        lexer_analyzer = PascalLexerAnalyzer()
        parser = PascalSyntaxAnalyzer()
        code = "a = 1 + 2"
        lexers = lexer_analyzer.analyze(code)
        parser.available_vars = ["a"]
        with self.assertRaises(ValueError):
            parser.get_statement(lexers)
