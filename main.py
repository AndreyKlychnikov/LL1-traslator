from translator.pascal_grammar import PascalLexerAnalyzer, PascalSyntaxAnalyzer

from translator.python_translator import PythonTranslator

if __name__ == "__main__":
    lex_analyzer = PascalLexerAnalyzer()
    parser = PascalSyntaxAnalyzer()
    with open("test_program.txt", "r") as file:
        code = "".join(file.readlines())

    lexers = lex_analyzer.analyze(code)
    ast = parser.translate(lexers)
    translator = PythonTranslator()
    print(translator.get_code_from_ast(ast))
