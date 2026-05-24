from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Set

from ast_tree import ASTNode
from semantic import SemanticAnalyzer, SemanticError
from symbol_table import SymbolTable
from utils import BLOCK_ENDERS, STATEMENT_STARTERS, TIPOS_DATO, infer_literal_type, token_text


@dataclass
class SyntaxErrorCF:
    numero: int
    descripcion: str
    linea: int
    sugerencia: str
    tipo: str = "Sintactico"


class Parser:
    COND_OPS = {
        "TOKEN_MENOR",
        "TOKEN_MAYOR",
        "TOKEN_IGUAL_ASIG",
        "TOKEN_MENOR_IGUAL",
        "TOKEN_MAYOR_IGUAL",
        "TOKEN_IGUALDAD",
        "TOKEN_DIFERENTE",
    }
    ARIT_OPS = {"TOKEN_SUMA", "TOKEN_RESTA", "TOKEN_MULT", "TOKEN_DIV", "TOKEN_MOD"}
    VALUE_TOKENS = {"TOKEN_TEXTO", "TOKEN_NUM", "TOKEN_DECIMAL", "TOKEN_VERDADERO", "TOKEN_FALSO"}

    def __init__(self, tokens: Sequence):
        self.tokens = list(tokens)
        self.pos = 0
        self.errors: List[SyntaxErrorCF] = []
        self.symbols = SymbolTable()
        self.semantic = SemanticAnalyzer(self.symbols)

    def parse(self) -> tuple[ASTNode, List[SyntaxErrorCF], List[SemanticError], SymbolTable]:
        root = ASTNode("Programa")
        root.extend(self.parse_instructions(stop_words=set()))
        if self.current() is not None:
            self.error("Token inesperado al final del programa", "Revisa el orden de las instrucciones.")
        return root, self.errors, self.semantic.errors, self.symbols

    def parse_instructions(self, stop_words: Set[str]) -> List[ASTNode]:
        nodes: List[ASTNode] = []
        while self.current() is not None and self.current().lexema not in stop_words:
            token = self.current()
            if token.lexema in BLOCK_ENDERS and token.lexema not in stop_words:
                self.error(
                    f"Cierre o palabra de bloque inesperada: {token.lexema}",
                    "Verifica que exista una apertura de bloque correspondiente.",
                    token,
                )
                self.advance()
                continue
            node = self.parse_instruction()
            if node:
                nodes.append(node)
            else:
                self.synchronize(stop_words)
        return nodes

    def parse_instruction(self) -> Optional[ASTNode]:
        token = self.current()
        if token is None:
            return None
        if token.lexema == "definir":
            return self.parse_declaration()
        if token.lexema == "asignar":
            return self.parse_assignment()
        if token.lexema == "mostrar":
            return self.parse_show()
        if token.lexema == "pedir":
            return self.parse_input()
        if token.lexema == "si":
            return self.parse_if()
        if token.lexema == "segun":
            return self.parse_switch()
        if token.lexema == "mientras":
            return self.parse_while()
        if token.lexema == "repetir":
            return self.parse_repeat()
        if token.lexema == "hacer":
            return self.parse_do_until()
        if token.lexema in {"funcion", "función"}:
            return self.parse_function()
        if token.token == "TOKEN_ID" and self.peek_lexeme() in TIPOS_DATO:
            self.error(
                "Se esperaba palabra reservada definir",
                "Corrige la palabra inicial por 'definir'.",
                token,
            )
            self.synchronize(set())
            return None
        if token.token == "TOKEN_ID":
            return self.parse_arithmetic()
        self.error(
            f"Instruccion no valida: {token.lexema}",
            "Usa una instruccion valida: definir, asignar, mostrar, pedir, si, segun, mientras, repetir, hacer o funcion.",
            token,
        )
        self.advance()
        return None

    def parse_declaration(self) -> ASTNode:
        start = self.expect_lexeme("definir", "Se esperaba palabra reservada definir", "Escribe 'definir' al iniciar una declaracion.")
        node = ASTNode("Declaracion", line=self.line_of(start))
        tipo = self.expect_type()
        ident = self.expect_token("TOKEN_ID", "Se esperaba identificador", "El identificador debe iniciar con minuscula y no usar guion bajo.")
        value_node = None
        value_text = ""
        if self.match_token("TOKEN_IGUAL_ASIG"):
            value = self.parse_value()
            if value:
                value_node = ASTNode("Valor", value.lexema, value.linea)
                value_text = value.lexema
        self.expect_token("T_PUNTO_COMA", 'Se esperaba ";"', "Agrega punto y coma al final de la declaracion.")
        if tipo and ident:
            self.symbols.add(ident.token, ident.lexema, tipo.lexema, ident.linea, "declaracion", value_text, "variable")
            node.extend([ASTNode("Tipo", tipo.lexema, tipo.linea), ASTNode("Identificador", ident.lexema, ident.linea)])
        node.add(value_node)
        return node

    def parse_assignment(self) -> ASTNode:
        start = self.expect_lexeme("asignar", "Se esperaba palabra reservada asignar", "Inicia la asignacion con 'asignar'.")
        node = ASTNode("Asignacion", line=self.line_of(start))
        ident = self.expect_token("TOKEN_ID", "Se esperaba identificador", "Indica la variable que recibira el valor.")
        self.expect_token("TOKEN_IGUAL_ASIG", 'Se esperaba "="', "Usa '=' entre el identificador y el valor.")
        value = self.parse_value()
        self.expect_token("T_PUNTO_COMA", 'Se esperaba ";"', "Agrega punto y coma al final de la asignacion.")
        if ident:
            self.semantic.require_identifier(ident.lexema, ident.linea)
            node.add(ASTNode("Identificador", ident.lexema, ident.linea))
        if value:
            node.add(ASTNode("Valor", value.lexema, value.linea))
        return node

    def parse_show(self) -> ASTNode:
        start = self.expect_lexeme("mostrar", "Se esperaba palabra reservada mostrar", "Usa mostrar(expresion);")
        node = ASTNode("Mostrar", line=self.line_of(start))
        self.expect_token("T_PARENTESIS_ABRE", 'Se esperaba "("', "Abre parentesis despues de mostrar.")
        item = None
        if self.check_token("TOKEN_ID") or self.check_token("TOKEN_TEXTO"):
            item = self.advance()
        else:
            self.error("Se esperaba identificador o cadena", "Dentro de mostrar usa una variable o una cadena entre comillas.")
        self.expect_token("T_PARENTESIS_CIERRE", 'Se esperaba ")"', "Cierra el parentesis de mostrar.")
        self.expect_token("T_PUNTO_COMA", 'Se esperaba ";"', "Agrega punto y coma al final de mostrar.")
        if item:
            if item.token == "TOKEN_ID":
                self.semantic.require_identifier(item.lexema, item.linea)
            node.add(ASTNode("Expresion", item.lexema, item.linea))
        return node

    def parse_input(self) -> ASTNode:
        start = self.expect_lexeme("pedir", "Se esperaba palabra reservada pedir", "Usa pedir(identificador);")
        node = ASTNode("Pedir", line=self.line_of(start))
        self.expect_token("T_PARENTESIS_ABRE", 'Se esperaba "("', "Abre parentesis despues de pedir.")
        ident = self.expect_token("TOKEN_ID", "Se esperaba identificador", "pedir solo recibe un identificador.")
        self.expect_token("T_PARENTESIS_CIERRE", 'Se esperaba ")"', "Cierra el parentesis de pedir.")
        self.expect_token("T_PUNTO_COMA", 'Se esperaba ";"', "Agrega punto y coma al final de pedir.")
        if ident:
            self.semantic.require_identifier(ident.lexema, ident.linea)
            node.add(ASTNode("Identificador", ident.lexema, ident.linea))
        return node

    def parse_if(self) -> ASTNode:
        start = self.expect_lexeme("si", "Se esperaba palabra reservada si", "Inicia el condicional con si.")
        node = ASTNode("Si", line=self.line_of(start))
        self.symbols.push_scope(f"si@{self.line_of(start)}")
        node.add(self.parse_parenthesized_condition())
        if not self.expect_lexeme("entonces", 'Se esperaba "entonces"', "Agrega entonces despues de la condicion."):
            self.synchronize({"si_no", "final_si"} | STATEMENT_STARTERS)
        body = ASTNode("Entonces")
        body.extend(self.parse_instructions({"si_no", "final_si"}))
        node.add(body)
        if self.match_lexeme("si_no"):
            else_node = ASTNode("SiNo", line=self.previous().linea)
            else_node.extend(self.parse_instructions({"final_si"}))
            node.add(else_node)
        if not self.expect_lexeme("final_si", "Se esperaba TOKEN_FINAL_SI", "Cierra el bloque si con final_si."):
            self.error("Bloque si sin cierre final_si", "Agrega final_si al terminar las instrucciones del si.", start)
        self.symbols.pop_scope()
        return node

    def parse_switch(self) -> ASTNode:
        start = self.expect_lexeme("segun", "Se esperaba palabra reservada segun", "Usa segun(identificador).")
        node = ASTNode("Segun", line=self.line_of(start))
        self.symbols.push_scope(f"segun@{self.line_of(start)}")
        self.expect_token("T_PARENTESIS_ABRE", 'Se esperaba "("', "Abre parentesis despues de segun.")
        ident = self.expect_token("TOKEN_ID", "Se esperaba identificador", "segun requiere un identificador.")
        self.expect_token("T_PARENTESIS_CIERRE", 'Se esperaba ")"', "Cierra el parentesis de segun.")
        if ident:
            self.semantic.require_identifier(ident.lexema, ident.linea)
            node.add(ASTNode("Selector", ident.lexema, ident.linea))
        if not self.check_lexeme("caso"):
            self.error('Se esperaba "caso"', "Agrega al menos un caso dentro de segun.")
        while self.match_lexeme("caso"):
            case_node = ASTNode("Caso", line=self.previous().linea)
            value = self.parse_value()
            if value:
                case_node.add(ASTNode("Valor", value.lexema, value.linea))
            self.expect_token("T_DOS_PUNTOS", 'Se esperaba ":"', "Agrega dos puntos despues del valor del caso.")
            case_node.extend(self.parse_instructions({"caso", "defecto", "final_segun"}))
            node.add(case_node)
        if self.match_lexeme("defecto"):
            default = ASTNode("Defecto", line=self.previous().linea)
            self.expect_token("T_DOS_PUNTOS", 'Se esperaba ":"', "Agrega dos puntos despues de defecto.")
            default.extend(self.parse_instructions({"final_segun"}))
            node.add(default)
        if not self.expect_lexeme("final_segun", "Se esperaba TOKEN_FINAL_SEGUN", "Cierra el bloque segun con final_segun."):
            self.error("Bloque segun sin cierre final_segun", "Agrega final_segun al terminar los casos.", start)
        self.symbols.pop_scope()
        return node

    def parse_while(self) -> ASTNode:
        start = self.expect_lexeme("mientras", "Se esperaba palabra reservada mientras", "Usa mientras(condicion).")
        node = ASTNode("Mientras", line=self.line_of(start))
        self.symbols.push_scope(f"mientras@{self.line_of(start)}")
        node.add(self.parse_parenthesized_condition())
        body = ASTNode("Instrucciones")
        body.extend(self.parse_instructions({"final_mientras"}))
        node.add(body)
        if not self.expect_lexeme("final_mientras", "Se esperaba TOKEN_FINAL_MIENTRAS", "Cierra el ciclo con final_mientras."):
            self.error("Bloque mientras sin cierre final_mientras", "Agrega final_mientras al terminar el ciclo.", start)
        self.symbols.pop_scope()
        return node

    def parse_repeat(self) -> ASTNode:
        start = self.expect_lexeme("repetir", "Se esperaba palabra reservada repetir", "Usa repetir(inicializador, condicion, incremento).")
        node = ASTNode("Repetir", line=self.line_of(start))
        self.symbols.push_scope(f"repetir@{self.line_of(start)}")
        self.expect_token("T_PARENTESIS_ABRE", 'Se esperaba "("', "Abre parentesis despues de repetir.")
        node.add(self.parse_initializer())
        self.expect_token("T_COMA", 'Se esperaba ","', "Separa inicializador, condicion e incremento con comas.")
        node.add(self.parse_condition())
        self.expect_token("T_COMA", 'Se esperaba ","', "Separa la condicion del incremento con coma.")
        node.add(self.parse_increment())
        self.expect_token("T_PARENTESIS_CIERRE", 'Se esperaba ")"', "Cierra el parentesis de repetir.")
        body = ASTNode("Instrucciones")
        body.extend(self.parse_instructions({"final_repetir"}))
        node.add(body)
        if not self.expect_lexeme("final_repetir", "Se esperaba TOKEN_FINAL_REPETIR", "Cierra el ciclo con final_repetir."):
            self.error("Bloque repetir sin cierre final_repetir", "Agrega final_repetir al terminar el ciclo.", start)
        self.symbols.pop_scope()
        return node

    def parse_do_until(self) -> ASTNode:
        start = self.expect_lexeme("hacer", "Se esperaba palabra reservada hacer", "Inicia el bloque con hacer.")
        node = ASTNode("HacerHasta", line=self.line_of(start))
        self.symbols.push_scope(f"hacer@{self.line_of(start)}")
        body = ASTNode("Instrucciones")
        body.extend(self.parse_instructions({"hasta"}))
        node.add(body)
        if not self.expect_lexeme("hasta", 'Se esperaba "hasta"', "Cierra hacer con hasta(condicion)."):
            self.error("Bloque hacer sin condicion hasta", "Agrega hasta(condicion) al final del bloque.", start)
        else:
            node.add(self.parse_parenthesized_condition())
            self.match_token("T_PUNTO_COMA")
        self.symbols.pop_scope()
        return node

    def parse_function(self) -> ASTNode:
        start = self.current()
        if not (self.check_lexeme("funcion") or self.check_lexeme("función")):
            self.error("Se esperaba palabra reservada funcion", "Declara la funcion con funcion nombre(parametro).")
        else:
            self.advance()
        node = ASTNode("Funcion", line=self.line_of(start))
        name = self.expect_token("TOKEN_ID", "Se esperaba identificador", "La funcion necesita un nombre valido.")
        if name:
            self.symbols.add(name.token, name.lexema, "funcion", name.linea, "funcion", "", "funcion")
            node.add(ASTNode("Nombre", name.lexema, name.linea))
            self.symbols.push_scope(f"funcion:{name.lexema}")
        else:
            self.symbols.push_scope(f"funcion@{self.line_of(start)}")
        self.expect_token("T_PARENTESIS_ABRE", 'Se esperaba "("', "Abre parentesis para los parametros.")
        if self.check_token("TOKEN_ID"):
            param = self.advance()
            self.symbols.add(param.token, param.lexema, "parametro", param.linea, "funcion", "", "parametro")
            node.add(ASTNode("Parametro", param.lexema, param.linea))
        self.expect_token("T_PARENTESIS_CIERRE", 'Se esperaba ")"', "Cierra parentesis de parametros.")
        body = ASTNode("Instrucciones")
        body.extend(self.parse_instructions({"retorno", "final_funcion"}))
        node.add(body)
        if self.match_lexeme("retorno"):
            ret = ASTNode("Retorno", line=self.previous().linea)
            value = self.parse_value()
            if value:
                ret.add(ASTNode("Valor", value.lexema, value.linea))
            self.expect_token("T_PUNTO_COMA", 'Se esperaba ";"', "Agrega punto y coma despues del retorno.")
            node.add(ret)
        if not self.expect_lexeme("final_funcion", "Se esperaba TOKEN_FINAL_FUNCION", "Cierra la funcion con final_funcion."):
            self.error("Funcion sin cierre final_funcion", "Agrega final_funcion al terminar la funcion.", start)
        self.symbols.pop_scope()
        return node

    def parse_arithmetic(self) -> ASTNode:
        ident = self.expect_token("TOKEN_ID", "Se esperaba identificador", "La operacion aritmetica inicia con un identificador.")
        node = ASTNode("OperacionAritmetica", line=self.line_of(ident))
        op = self.expect_any_token(self.ARIT_OPS, "Se esperaba operador aritmetico", "Usa +, -, *, / o %.")
        number = self.expect_any_token({"TOKEN_NUM", "TOKEN_DECIMAL"}, "Se esperaba numero", "Las operaciones aritmeticas de esta gramatica usan numeros.")
        self.expect_token("T_PUNTO_COMA", 'Se esperaba ";"', "Agrega punto y coma al final de la operacion.")
        if ident:
            self.semantic.require_identifier(ident.lexema, ident.linea)
            node.add(ASTNode("Identificador", ident.lexema, ident.linea))
        if op:
            node.add(ASTNode("Operador", op.lexema, op.linea))
        if number:
            node.add(ASTNode("Numero", number.lexema, number.linea))
        return node

    def parse_initializer(self) -> ASTNode:
        node = ASTNode("Inicializador")
        tipo = self.expect_lexeme("entero", 'Se esperaba "entero"', "El inicializador debe ser entero identificador = numero.")
        ident = self.expect_token("TOKEN_ID", "Se esperaba identificador", "Agrega el identificador del contador.")
        self.expect_token("TOKEN_IGUAL_ASIG", 'Se esperaba "="', "Inicializa el contador con '='.")
        number = self.expect_token("TOKEN_NUM", "Se esperaba numero", "El contador debe iniciar con un numero entero.")
        if ident:
            self.symbols.add(ident.token, ident.lexema, "entero", ident.linea, "repetir", number.lexema if number else "", "contador")
            node.add(ASTNode("Identificador", ident.lexema, ident.linea))
        if tipo:
            node.add(ASTNode("Tipo", tipo.lexema, tipo.linea))
        if number:
            node.add(ASTNode("Valor", number.lexema, number.linea))
        return node

    def parse_increment(self) -> ASTNode:
        node = ASTNode("Incremento")
        ident = self.expect_token("TOKEN_ID", "Se esperaba identificador", "El incremento debe iniciar con el contador.")
        op = self.expect_any_token({"TOKEN_INCREMENTO", "TOKEN_DECREMENTO"}, 'Se esperaba "++" o "--"', "Usa contador++ o contador--.")
        if ident:
            self.semantic.require_identifier(ident.lexema, ident.linea)
            node.add(ASTNode("Identificador", ident.lexema, ident.linea))
        if op:
            node.add(ASTNode("Operador", op.lexema, op.linea))
        return node

    def parse_parenthesized_condition(self) -> ASTNode:
        self.expect_token("T_PARENTESIS_ABRE", 'Se esperaba "("', "Abre parentesis antes de la condicion.")
        node = self.parse_condition()
        self.expect_token("T_PARENTESIS_CIERRE", 'Se esperaba ")"', "Cierra parentesis despues de la condicion.")
        return node

    def parse_condition(self) -> ASTNode:
        node = ASTNode("Condicion")
        ident = self.expect_token("TOKEN_ID", "Se esperaba identificador", "La condicion debe iniciar con un identificador.")
        op = self.expect_any_token(self.COND_OPS, "Se esperaba operador condicional", "Usa <, >, =, <=, >=, == o !=.")
        value = self.parse_value()
        if ident:
            self.semantic.require_identifier(ident.lexema, ident.linea)
            node.add(ASTNode("Identificador", ident.lexema, ident.linea))
        if op:
            node.add(ASTNode("Operador", op.lexema, op.linea))
        if value:
            node.add(ASTNode("Valor", value.lexema, value.linea))
        return node

    def parse_value(self):
        token = self.current()
        if token and token.token in self.VALUE_TOKENS:
            return self.advance()
        self.error("Se esperaba valor", "Usa cadena, numero, verdadero o falso.", token)
        return None

    def expect_type(self):
        token = self.current()
        if token and token.lexema in TIPOS_DATO:
            return self.advance()
        self.error("Se esperaba tipo de dato", "Usa entero, decimal, texto o booleano.", token)
        return None

    def current(self):
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def previous(self):
        if self.pos == 0:
            return None
        return self.tokens[self.pos - 1]

    def peek_lexeme(self, offset: int = 1) -> str:
        index = self.pos + offset
        if index >= len(self.tokens):
            return ""
        return self.tokens[index].lexema

    def advance(self):
        token = self.current()
        if token is not None:
            self.pos += 1
        return token

    def check_token(self, token_name: str) -> bool:
        return self.current() is not None and self.current().token == token_name

    def check_lexeme(self, lexeme: str) -> bool:
        return self.current() is not None and self.current().lexema == lexeme

    def match_token(self, token_name: str) -> bool:
        if self.check_token(token_name):
            self.advance()
            return True
        return False

    def match_lexeme(self, lexeme: str) -> bool:
        if self.check_lexeme(lexeme):
            self.advance()
            return True
        return False

    def expect_token(self, token_name: str, description: str, suggestion: str):
        token = self.current()
        if token and token.token == token_name:
            return self.advance()
        self.error(description, suggestion, token)
        return None

    def expect_any_token(self, token_names: Iterable[str], description: str, suggestion: str):
        names = set(token_names)
        token = self.current()
        if token and token.token in names:
            return self.advance()
        self.error(description, suggestion, token)
        return None

    def expect_lexeme(self, lexeme: str, description: str, suggestion: str):
        token = self.current()
        if token and token.lexema == lexeme:
            return self.advance()
        self.error(description, suggestion, token)
        return None

    def error(self, description: str, suggestion: str, token=None) -> None:
        ref = token if token is not None else self.current()
        line = self.line_of(ref)
        found = token_text(ref)
        if ref is not None and "Se esperaba" in description:
            description = f"{description}. Encontrado {found}"
        self.errors.append(SyntaxErrorCF(len(self.errors) + 1, description, line, suggestion))

    def line_of(self, token) -> int:
        if token is not None:
            return token.linea
        if self.previous() is not None:
            return self.previous().linea
        return 1

    def synchronize(self, stop_words: Set[str]) -> None:
        while self.current() is not None:
            if self.current().lexema in stop_words or self.current().lexema in STATEMENT_STARTERS:
                return
            if self.current().token == "T_PUNTO_COMA":
                self.advance()
                return
            self.advance()


def analizar_sintactico(tokens: Sequence) -> tuple[ASTNode, List[SyntaxErrorCF], List[SemanticError], SymbolTable]:
    return Parser(tokens).parse()
