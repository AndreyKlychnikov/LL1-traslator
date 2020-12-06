from pascal_grammar import PascalLexerAnalyzer
from pprint import pprint

if __name__ == "__main__":
    lex_analyzer = PascalLexerAnalyzer()
    with open("test_program.txt", "r") as file:
        code = "".join(file.readlines())

    lexers = lex_analyzer.analyze(code)
    pprint(lexers)
