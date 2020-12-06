from pascal_grammar import ASTNode


class PythonTranslator:
    def get_code_from_ast(self, ast: ASTNode):
        program = ast
        variables = program.data["var_def"].data["variables"]
        ctx = {}
        for var in variables:
            ctx[var] = None
        code = []
        for statement in program.data["statements"].data["statements"]:
            code.append(self.get_statement_code_from_ast(statement))

        return '\n'.join(code)

    def get_statement_code_from_ast(self, statement):
        if statement.name == "assign":
            return f'{statement.data["left"]} = int({self.get_expr_code_from_ast(statement.data["right"])})'
        if statement.name == 'read':
            return f'{", ".join(statement.data["variables"])} = [int(v) for v in input().split(" ")]'
        if statement.name == 'write':
            return f'print({", ".join(statement.data["variables"])})'
        if statement.name == 'case':
            expr = self.get_expr_code_from_ast(statement.data['expr'])

            choices = statement.data['choices']
            val, assign = choices.popitem()
            code = f'if {expr} == {val}:\n\t{self.get_statement_code_from_ast(assign)}'
            for val, assign in choices.items():
                code += f'\nelif {expr} == {val}:\n\t{self.get_statement_code_from_ast(assign)}'
            return code

    def get_expr_code_from_ast(self, expr):
        if isinstance(expr, str):
            return expr
        if expr.name == 'parentheses_expr':
            return f'({self.get_expr_code_from_ast(expr.data["expr"])})'
        if "operand2" in expr.data:
            return f'{self.get_expr_code_from_ast(expr.data["operand1"])} {expr.data["op"]} {self.get_expr_code_from_ast(expr.data["operand2"])}'
        if "op" in expr.data:
            return f'{expr.data["op"]}{self.get_expr_code_from_ast(expr.data["operand1"])}'
        return self.get_expr_code_from_ast(expr.data["operand1"])
