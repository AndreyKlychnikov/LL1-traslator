from typing import Union

from nodes import (
    ProgramNode,
    AssignNode,
    FuncNode,
    CaseNode,
    ParenthesesNode,
    ExpressionNode,
)


class PythonTranslator:
    def get_code_from_ast(self, ast: ProgramNode):
        program = ast
        code = []
        for statement in program.statements:
            code.append(self.get_statement_code_from_ast(statement))

        return "\n".join(code)

    def get_statement_code_from_ast(
        self, statement: Union[AssignNode, CaseNode, FuncNode]
    ):
        if isinstance(statement, AssignNode):
            return f"{statement.left} = int({self.get_expr_code_from_ast(statement.right)})"
        if isinstance(statement, FuncNode):
            if statement.name == "read":
                return f'{", ".join(statement.args)} = [int(v) for v in input().split(" ")]'
            if statement.name == "write":
                return f'print({", ".join(statement.args)})'
        if isinstance(statement, CaseNode):
            expr = self.get_expr_code_from_ast(statement.expr)

            lines = []
            for val, assign in statement.choices.items():
                lines.append(
                    f"elif {expr} == {val}:\n\t{self.get_statement_code_from_ast(assign)}"
                )
            lines[0] = lines[0][2:]  # elif -> if
            return "\n".join(lines)

    def get_expr_code_from_ast(self, expr: Union[ExpressionNode, ParenthesesNode]):
        if isinstance(expr, str):
            return expr
        if isinstance(expr, ParenthesesNode):
            return f"({self.get_expr_code_from_ast(expr.node)})"
        if expr.operand2:
            return f"{self.get_expr_code_from_ast(expr.operand1)} {expr.op} {self.get_expr_code_from_ast(expr.operand2)}"
        if expr.op:
            return f"{expr.op}{self.get_expr_code_from_ast(expr.operand1)}"
        return self.get_expr_code_from_ast(expr.operand1)
