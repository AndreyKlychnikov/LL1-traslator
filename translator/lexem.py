from dataclasses import dataclass


@dataclass
class Lexem:
    name: str

    def __str__(self):
        return self.name


@dataclass
class ExtendedLexem:
    name: str
    value: str

    def __str__(self):
        return f'{self.name} with value {self.value}'
