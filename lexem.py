from dataclasses import dataclass


@dataclass
class ExtendedLexem:
    name: str
    value: str


@dataclass
class Separator:
    name: str
    val: str
    ignore: bool

    def __eq__(self, other):
        return self.val == other
