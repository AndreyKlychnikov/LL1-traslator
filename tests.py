import string
from unittest import TestCase

from analyzer import Analyzer, LexerAnalyzer
from lexem import ExtendedLexem, Lexem
from pascal_grammar import PascalSyntaxAnalyzer, PascalLexerAnalyzer, Lexers, ASTNode
from python_translator import PythonTranslator


class AnalyzerTestCase(TestCase):
    def test_normalize_rules(self):
        rules = {
            "<A>": ("abc<B>", "<B>z"),
            "<B>": ("z",),
        }
        terms = set(*string.ascii_lowercase.split())
        a = Analyzer(rules, terms)

        expected = {
            "<A>": [["a", "b", "c", "<B>"], ["<B>", "z"]],
            "<B>": [["z"]],
        }
        self.assertDictEqual(expected, a.rules)

    def test_get_first(self):
        rules = {
            "<A>": ("abc<B>", "<B>z"),
            "<B>": ("z", "<C>"),
            "<C>": ("d",),
        }
        terms = set(*string.ascii_lowercase.split())
        a = Analyzer(rules, terms)

        self.assertListEqual(a.get_first("a"), ["a"])
        self.assertListEqual(a.get_first("b"), ["b"])
        self.assertListEqual(a.get_first("c"), ["c"])
        self.assertListEqual(a.get_first("d"), ["d"])
        self.assertListEqual(a.get_first("z"), ["z"])
        self.assertListEqual(a.get_first("<A>"), ["a", "z", "d"])
        self.assertListEqual(a.get_first("<B>"), ["z", "d"])
        self.assertListEqual(a.get_first("<C>"), ["d"])

    def test_get_follow(self):
        rules = {
            "<A>": ("abc<B>", "<B>z"),
            "<B>": ("z", "<C>"),
            "<C>": ("d",),
        }
        terms = set(*string.ascii_lowercase.split())
        a = Analyzer(rules, terms)
        self.assertSetEqual(a.get_follow("<B>"), {"z"})

        rules = {
            "<A>": ("abc<B><A>", "<B>z"),
            "<B>": ("z", "<C>"),
            "<C>": ("d",),
        }
        a = Analyzer(rules, terms)
        self.assertSetEqual(set(), a.get_follow("<A>"))
        self.assertSetEqual(a.get_follow("<B>"), set(["z"] + a.get_first("<A>")))
        self.assertSetEqual(a.get_follow("<C>"), set())

    def test_normalize_rules_right(self):
        a = Analyzer({}, set())
        self.assertListEqual(["<A>", *list("bcd")], a.normalize_rules_right("<A>bcd"))

    def test_transition_table(self):
        rules = {"<A>": ("<B>cd",), "<B>": ("d",)}
        terms = set(*string.ascii_lowercase.split())
        a = Analyzer(rules, terms)
        self.assertEqual(
            {("<A>", "d"): ["<B>", "c", "d"], ("<B>", "d"): ["d"]}, a.transition_table
        )
        rules = {
            "<A>": ("abc<B><A>", "<B>z"),
            "<B>": ("z", "<C>"),
            "<C>": ("d",),
        }
        terms = set(*string.ascii_lowercase.split())
        a = Analyzer(rules, terms)
        self.assertEqual(
            {
                ("<A>", "a"): ["a", "b", "c", "<B>", "<A>"],
                ("<A>", "z"): ["<B>", "z"],
                ("<A>", "d"): ["<B>", "z"],
                ("<B>", "z"): ["z"],
                ("<B>", "d"): ["<C>"],
                ("<C>", "d"): ["d"],
            },
            a.transition_table,
        )

    def test_analyze(self):
        rules = {"<S>": ("<F>", "(<S>+<F>)"), "<F>": ("1",)}
        terms = {"1", "+"}
        a = Analyzer(rules, terms)
        print(a.analyze("(1+1)", "<S>"))

        with self.assertRaises(ValueError):
            a.analyze("(1+2)", "<S>")

        with self.assertRaises(ValueError):
            a.analyze("(1+1)abc", "<S>")

    def test_split_rules_right(self):
        a = Analyzer({}, {"AA", "BB", "C"})
        self.assertEqual(["AA", "BB", "C", "<V>"], a.split_rules_right("AABBC<V>"))


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
        regex_terms = {"IDENTIFIER": r"^([A-Za-z]+)$", "CONST": r"^([0-9]+)$"}

        code = """
            VAR a, b :INTEGER;
            BEGIN
            a = 1;
            b = 2999999999;
            END
            """
        include_separators = {
            "PLUS": "+",
            "MINUS": "-",
            "DIV": "/",
            "MUL": "*",
            "COLON": ":",
            "COMMA": ",",
            "SEMICOLON": ";",
            "OR": "OR",
            "EQ": "EQ",
        }
        ignore_separators = {"SPACE": " ", "NEW_LINE": "\n"}

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
            [ExtendedLexem(name="IDENTIFIER", value="BEGINEND")], lexers
        )

        code = "123 OR aaa"
        lexers = a.analyze(code)
        self.assertListEqual(
            [
                ExtendedLexem("CONST", "123"),
                Lexem("OR"),
                ExtendedLexem("IDENTIFIER", "aaa"),
            ],
            lexers,
        )


class ParserTestCase(TestCase):
    def test_analyze(self):
        lexer_analyzer = PascalLexerAnalyzer()
        parser = PascalSyntaxAnalyzer()
        lexers = lexer_analyzer.analyze("VAR a, b: INTEGER;")
        print(lexers)
        print(parser.translate(lexers))

    def test_get_expr(self):
        lexer_analyzer = PascalLexerAnalyzer()
        parser = PascalSyntaxAnalyzer()
        lexers = lexer_analyzer.analyze("23 + (1 - b) + 3 + 5")
        print(lexers)
        lexers = Lexers(lexers)
        print(parser.get_expr(lexers))

    def test_get_statement(self):
        lexer_analyzer = PascalLexerAnalyzer()
        parser = PascalSyntaxAnalyzer()
        lexers = lexer_analyzer.analyze("a = 54;")
        lexers = Lexers(lexers)
        self.assertEqual(
            ASTNode(name="assign", data={"left": "a", "right": "54"}),
            parser.get_statement(lexers),
        )
        lexers = lexer_analyzer.analyze("a = (54 + a);")
        lexers = Lexers(lexers)
        self.assertEqual(
            ASTNode(
                name="assign",
                data={
                    "left": "a",
                    "right": ASTNode(
                        name="parentheses_expr",
                        data={
                            "expr": ASTNode(
                                name="expr",
                                data={"operand1": "54", "op": "+", "operand2": "a"},
                            )
                        },
                    ),
                },
            ),
            parser.get_statement(lexers),
        )
        # WRITE
        lexers = lexer_analyzer.analyze("WRITE(a, sv, variable);")
        lexers = Lexers(lexers)
        self.assertEqual(
            ASTNode(name="write", data={"variables": ["a", "sv", "variable"]}),
            parser.get_statement(lexers),
        )

    def test_get_statements(self):
        lexer_analyzer = PascalLexerAnalyzer()
        parser = PascalSyntaxAnalyzer()
        lexers = lexer_analyzer.analyze("BEGIN a = 54;READ(a, b); END")
        lexers = Lexers(lexers)
        self.assertEqual(
            ASTNode(
                name="statements",
                data={
                    "statements": [
                        ASTNode(name="assign", data={"left": "a", "right": "54"}),
                        ASTNode(name="read", data={"variables": ["a", "b"]}),
                    ]
                },
            ),
            parser.get_statements(lexers),
        )

    def test_translate(self):
        lexer_analyzer = PascalLexerAnalyzer()
        parser = PascalSyntaxAnalyzer()
        lexers = lexer_analyzer.analyze("VAR a, b: INTEGER;BEGIN a = 123; END")
        self.assertEqual(
            ASTNode(
                name="PROGRAM",
                data={
                    "var_def": ASTNode(name="var_def", data={"variables": ["a", "b"]}),
                    "statements": ASTNode(
                        name="statements",
                        data={
                            "statements": [
                                ASTNode(
                                    name="assign", data={"left": "a", "right": "123"}
                                )
                            ]
                        },
                    ),
                },
            ),
            parser.translate(lexers),
        )
        code = """
        VAR a, b: INTEGER;
        BEGIN
            a = 123;
            CASE a OF
                1: b = 123;
                123: b = 1;
            END_CASE;
        END
        """
        lexers = lexer_analyzer.analyze(code)
        self.assertEqual(
            ASTNode(
                name="PROGRAM",
                data={
                    "var_def": ASTNode(name="var_def", data={"variables": ["a", "b"]}),
                    "statements": ASTNode(
                        name="statements",
                        data={
                            "statements": [
                                ASTNode(
                                    name="assign", data={"left": "a", "right": "123"}
                                ),
                                ASTNode(
                                    name="case",
                                    data={
                                        "expr": "a",
                                        "choices": {
                                            "1": ASTNode(
                                                name="assign",
                                                data={"left": "b", "right": "123"},
                                            ),
                                            "123": ASTNode(
                                                name="assign",
                                                data={"left": "b", "right": "1"},
                                            ),
                                        },
                                    },
                                ),
                            ]
                        },
                    ),
                },
            ),
            parser.translate(lexers),
        )
        code = """
               VAR a, b: INTEGER;
               BEGIN
                   a = (123 + a) - b;
               END
               """
        lexers = lexer_analyzer.analyze(code)
        print(parser.translate(lexers))


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
        compiled = compile(translator.get_code_from_ast(ast), '<string>', 'exec')

        exec(compiled)
