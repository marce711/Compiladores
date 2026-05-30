from dataclasses import dataclass
from typing import List, Optional

from symbol_table import SymbolEntry, SymbolTable
from utils import infer_literal_type, types_compatible


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

    def declare_identifier(
        self,
        token: str,
        lexema: str,
        tipo_dato: str,
        linea: int,
        estructura: str,
        value_token=None,
        categoria: str = "variable",
    ) -> Optional[SymbolEntry]:
        if self.symbols.find(lexema):
            self.add_error(
                f"Variable '{lexema}' declarada mas de una vez",
                linea,
                "Usa otro identificador o elimina la declaracion repetida.",
            )
            return None

        value_text = value_token.lexema if value_token else ""
        if value_token:
            self.check_assignment_type(lexema, tipo_dato, value_token)

        return self.symbols.add(token, lexema, tipo_dato, linea, estructura, value_text, categoria)

    def require_identifier(self, lexema: str, linea: int) -> Optional[SymbolEntry]:
        entry = self.symbols.find(lexema)
        if not entry:
            self.add_error(
                f"Identificador '{lexema}' usado antes de ser declarado",
                linea,
                "Declara el identificador con definir antes de usarlo.",
            )
        return entry

    def assign_identifier(self, ident_token, value_token) -> None:
        entry = self.require_identifier(ident_token.lexema, ident_token.linea)
        if entry and value_token:
            self.check_assignment_type(ident_token.lexema, entry.tipo_dato, value_token)

    def check_assignment_type(self, lexema: str, expected_type: str, value_token) -> None:
        received_type = infer_literal_type(value_token)
        if not types_compatible(expected_type, received_type):
            self.add_error(
                f"Tipo incompatible para '{lexema}': se esperaba {expected_type} y se recibio {received_type}",
                value_token.linea,
                "Asigna un valor compatible con el tipo declarado.",
            )

    def check_condition(self, ident_token, operator_token, value_token) -> None:
        entry = self.require_identifier(ident_token.lexema, ident_token.linea)
        if not entry or not value_token:
            return

        received_type = infer_literal_type(value_token)
        operator = operator_token.lexema if operator_token else ""
        if operator in {"<", ">", "<=", ">="}:
            compatible = entry.tipo_dato in {"entero", "decimal"} and received_type in {"entero", "decimal"}
        else:
            compatible = types_compatible(entry.tipo_dato, received_type, operator)

        if not compatible:
            self.add_error(
                f"Condicion incompatible: '{ident_token.lexema}' es {entry.tipo_dato} y se compara con {received_type}",
                value_token.linea,
                "Compara valores del mismo tipo; usa operadores de orden solo con entero o decimal.",
            )

    def check_numeric_identifier(self, ident_token) -> None:
        entry = self.require_identifier(ident_token.lexema, ident_token.linea)
        if entry and entry.tipo_dato not in {"entero", "decimal"}:
            self.add_error(
                f"Operacion aritmetica invalida: '{ident_token.lexema}' es {entry.tipo_dato}",
                ident_token.linea,
                "Usa operaciones aritmeticas solamente con variables enteras o decimales.",
            )

    def add_error(self, descripcion: str, linea: int, sugerencia: str) -> None:
        self.errors.append(SemanticError(len(self.errors) + 1, descripcion, linea, sugerencia))
