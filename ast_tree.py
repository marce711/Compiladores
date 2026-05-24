from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass
class ASTNode:
    name: str
    value: str = ""
    line: int = 0
    children: List["ASTNode"] = field(default_factory=list)

    def add(self, child: Optional["ASTNode"]) -> Optional["ASTNode"]:
        if child is not None:
            self.children.append(child)
        return child

    def extend(self, children: Iterable["ASTNode"]) -> None:
        self.children.extend(child for child in children if child is not None)

    def pretty(self, level: int = 0) -> str:
        indent = "  " * level
        label = self.name if not self.value else f"{self.name}: {self.value}"
        line = f" [linea {self.line}]" if self.line else ""
        rows = [f"{indent}{label}{line}"]
        for child in self.children:
            rows.append(child.pretty(level + 1))
        return "\n".join(rows)


def print_ast(root: ASTNode) -> None:
    print("\nARBOL SINTACTICO CODEFLOW")
    print(root.pretty())
