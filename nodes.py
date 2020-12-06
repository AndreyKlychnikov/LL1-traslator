from dataclasses import dataclass
from typing import List, Union, Dict, Optional


@dataclass
class ASTNode:
    pass


@dataclass
class ExpressionNode(ASTNode):
    operand1: Optional[Union["ExpressionNode", "ParenthesesNode", str]] = None
    operand2: Optional[Union["ExpressionNode", "ParenthesesNode", str]] = None
    op: str = ""


@dataclass
class ParenthesesNode(ASTNode):
    node: ExpressionNode


@dataclass
class AssignNode(ASTNode):
    left: str
    right: Union[ExpressionNode, str]


@dataclass
class FuncNode(ASTNode):
    name: str
    args: List[str]


@dataclass
class ProgramNode(ASTNode):
    variables: List[str]
    statements: List[Union[AssignNode, FuncNode]]


@dataclass
class CaseNode(ASTNode):
    expr: Union[ExpressionNode, str]
    choices: Dict
