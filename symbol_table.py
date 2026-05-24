from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class SymbolEntry:
    token: str
    lexema: str
    tipo_dato: str
    linea: int
    alcance: str
    estructura: str
    valor: str = ""
    categoria: str = "variable"


@dataclass
class SymbolTable:
    entries: List[SymbolEntry] = field(default_factory=list)
    scopes: List[str] = field(default_factory=lambda: ["global"])

    @property
    def current_scope(self) -> str:
        return "/".join(self.scopes)

    def push_scope(self, name: str) -> None:
        self.scopes.append(name)

    def pop_scope(self) -> None:
        if len(self.scopes) > 1:
            self.scopes.pop()

    def add(
        self,
        token: str,
        lexema: str,
        tipo_dato: str,
        linea: int,
        estructura: str,
        valor: str = "",
        categoria: str = "variable",
    ) -> SymbolEntry:
        entry = SymbolEntry(
            token=token,
            lexema=lexema,
            tipo_dato=tipo_dato,
            linea=linea,
            alcance=self.current_scope,
            estructura=estructura,
            valor=valor,
            categoria=categoria,
        )
        self.entries.append(entry)
        return entry

    def find(self, lexema: str) -> Optional[SymbolEntry]:
        for entry in reversed(self.entries):
            if entry.lexema == lexema:
                return entry
        return None

    def as_rows(self) -> List[Dict[str, str]]:
        return [entry.__dict__.copy() for entry in self.entries]


def build_token_symbol_rows(tokens: Iterable) -> List[Dict[str, str]]:
    return [
        {
            "token": token.token,
            "lexema": token.lexema,
            "tipo_dato": token.tipo,
            "linea": token.linea,
            "alcance": "global",
            "estructura": "token",
            "valor": token.lexema,
            "categoria": token.tipo,
        }
        for token in tokens
    ]
