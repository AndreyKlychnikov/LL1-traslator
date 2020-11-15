import string

from analyzer import LexerAnalyzer, Analyzer

reserved_words = {
    'VAR', 'BEGIN', 'END', 'INTEGER', 'CASE', 'OF', 'END_CASE', 'WRITE', 'READ', 'AND',
    'LOGICAL', 'OR', 'EQ', 'IF', 'THEN', 'ELSE', 'ENDIF'
}


class PascalLexerAnalyzer(LexerAnalyzer):
    def __init__(self):
        include_separators = {
            'PLUS': '+',
            'MINUS': '-',
            'DIV': '/',
            'ASSIGN_OP': '=',
            'OR': 'OR',
            'EQ': 'EQ',
            'COLON': ':',
            'COMMA': ',',
            'SEMICOLON': ';',
            'PAR_OPEN': '(',
            'PAR_CLOSE': ')',
        }
        ignore_separators = {
            'SPACE': ' ',
            'NEW_LINE': '\n'
        }
        regex_terms = {'IDENTIFIER': r'^([A-Za-z]+)$', 'CONST': r'^([0-9]+)$'}
        super().__init__(
            regex_terms,
            reserved_words,
            include_separators=include_separators,
            ignore_separators=ignore_separators
        )


pascal_terms = {
    'VAR', 'BEGIN', 'END', 'INTEGER', 'CASE', 'OF', 'END_CASE', '=', '+',
    '-', '/', 'WRITE', 'READ', ':', ';', ' ', 'AND', 'LOGICAL', 'OR', 'EQ',
    'IF', 'THEN', 'ELSE', 'ENDIF'
}
pascal_terms.update(*string.ascii_lowercase.split())
pascal_terms.update(*[str(i) for i in range(10)])


class PascalSyntaxAnalyzer(Analyzer):
    def __init__(self):
        rules = {
            '<PROGRAM>': ('<VAR_DEFINITION><COMPUTATIONS>',),
            '<VAR_DEFINITION>': ('VAR <VAR_LIST> :INTEGER;',),
            '<COMPUTATIONS>': ('BEGIN <VAR_LIST> END',),
            '<ASSIGN_LIST>': ('<ASSIGN><ASSIGN_LIST_>',),
            '<ASSIGN_LIST_>': ('<ASSIGN_LIST>', ''),
            '<VAR_LIST>': ('<IDENTIFIER><VAR_LIST_>',),
            '<VAR_LIST_>': ('<VAR_LIST>', ''),
            '<IDENTIFIER>': ('<LETTER><IDENTIFIER_>',),
            '<IDENTIFIER_>': ('<IDENTIFIER>', ''),
            '<CONST>': [str(i) for i in range(10)],
            '<LETTER>': list(string.ascii_lowercase),
            '<EXPRESSION>': ('<UNARY_OPERATOR><SUB_EXPRESSION>', '<SUB_EXPRESSION>'),
            '<ASSIGN>': ('<IDENTIFIER> = <EXPRESSION>;',),
            '<SUB_EXPRESSION>': ('(<EXPRESSION>)',
                                 '<OPERAND>',
                                 '<SUB_EXPRESSION> <BINARY_OPERATOR> <SUB_EXPRESSION>'),
            '<BINARY_OPERATOR>': ('+', '-', '/'),
            '<UNARY_OPERATOR>': ('-',),
            '<OPERAND>': ('<IDENTIFIER>', '<CONST>'),
            '<FUNCTION>': ('READ(<VAR_LIST>)', 'WRITE(<VAR_LIST>)'),
            '<CASE>': ('CASE <EXPRESSION> OF <CHOICE_LIST> <ENDCASE>',),
            '<CHOICE_LIST>': ('<CHOICE>', '<CHOICE><CHOICE_LIST>'),
            '<CHOICE>': ('<CONST>: <ASSIGN>',),
        }
        super().__init__(rules, pascal_terms)
