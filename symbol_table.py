from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class SymbolEntry:
    token: str
    orden: int
    estructura: str
    tipo_dato: str
    linea: int
    lexema: str
    alcance: str = "global"
    valor: str = ""
    categoria: str = "variable"


@dataclass
class SymbolTable:
    entries: List[SymbolEntry] = field(default_factory=list)
    scopes: List[str] = field(default_factory=lambda: ["global"])
    _counter: int = 1

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
            orden=self._counter,
            estructura=estructura,
            tipo_dato=tipo_dato,
            linea=linea,
            lexema=lexema,
            alcance=self.current_scope,
            valor=valor,
            categoria=categoria,
        )
        self.entries.append(entry)
        self._counter += 1
        return entry

    def find(self, lexema: str) -> Optional[SymbolEntry]:
        for entry in reversed(self.entries):
            if entry.lexema == lexema:
                return entry
        return None

    def find_in_current_scope(self, lexema: str) -> Optional[SymbolEntry]:
        scope = self.current_scope
        for entry in reversed(self.entries):
            if entry.lexema == lexema and entry.alcance == scope:
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
