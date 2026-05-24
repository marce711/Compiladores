from dataclasses import dataclass
from typing import List

from symbol_table import SymbolTable


@dataclass
class SemanticError:
    numero: int
    descripcion: str
    linea: int
    sugerencia: str
    tipo: str = "Semantico"


class SemanticAnalyzer:
    def __init__(self, symbols: SymbolTable):
        self.symbols = symbols
        self.errors: List[SemanticError] = []

    def require_identifier(self, lexema: str, linea: int) -> None:
        if not self.symbols.find(lexema):
            self.errors.append(
                SemanticError(
                    len(self.errors) + 1,
                    f"Identificador '{lexema}' usado antes de ser declarado",
                    linea,
                    "Declara el identificador con definir antes de usarlo.",
                )
            )
