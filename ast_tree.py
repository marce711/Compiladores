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

    def pretty(self, prefix: str = "", is_last: bool = True) -> str:
        node_label = f"<{self.name}>" if self.children else self.name
        if self.value:
            node_label += f" -> {self.value}"
        if self.line:
            node_label += f" [linea {self.line}]"

        branch = "`-- " if is_last else "|-- "
        result = prefix + branch + node_label + "\n"
        new_prefix = prefix + ("    " if is_last else "|   ")
        for index, child in enumerate(self.children):
            result += child.pretty(new_prefix, index == len(self.children) - 1)
        return result


def print_ast(root: ASTNode) -> None:
    print("\nARBOL DE ANALISIS SINTACTICO")
    print(root.pretty("", True), end="")


def to_bnf_tree(root: ASTNode) -> ASTNode:
    bnf_root = ASTNode("programa", line=root.line)
    for child in root.children:
        bnf_root.add(_to_bnf_node(child))
    return bnf_root


def _terminal(value: str, line: int = 0) -> ASTNode:
    return ASTNode(value, line=line)


def _production(name: str, children: Iterable[ASTNode], line: int = 0) -> ASTNode:
    node = ASTNode(name, line=line)
    node.extend(children)
    return node


def _value_of(node: ASTNode, name: str) -> str:
    for child in node.children:
        if child.name == name:
            return child.value
    return ""


def _node_by_name(node: ASTNode, name: str) -> Optional[ASTNode]:
    for child in node.children:
        if child.name == name:
            return child
    return None


def _value_node(value: str, line: int = 0) -> ASTNode:
    node = ASTNode("valor", line=line)
    if value.startswith('"'):
        node.add(_cadena_node(value, line))
    elif value in {"verdadero", "falso"}:
        node.add(_production("bool", [_terminal(value, line)], line))
    elif value == "nulo":
        node.add(_terminal("nulo", line))
    else:
        node.add(_numeros_node(value, line))
    return node


def _tipo_node(value: str, line: int = 0) -> ASTNode:
    return _production("tipo", [_terminal(value, line)], line)


def _identificador_node(value: str, line: int = 0) -> ASTNode:
    node = ASTNode("identificador", line=line)
    if not value:
        return node
    node.add(_minus_node(value[0], line))
    for char in value[1:]:
        if char.isdigit():
            node.add(_numero_node(char, line))
        else:
            node.add(_letras_node(char, line))
    return node


def _letras_node(char: str, line: int = 0) -> ASTNode:
    branch = _mayus_node(char, line) if char.isupper() else _minus_node(char, line)
    return _production("letras", [branch], line)


def _minus_node(char: str, line: int = 0) -> ASTNode:
    return _production("minus", [_terminal(char, line)], line)


def _mayus_node(char: str, line: int = 0) -> ASTNode:
    return _production("mayus", [_terminal(char, line)], line)


def _numero_node(char: str, line: int = 0) -> ASTNode:
    return _production("numero", [_terminal(char, line)], line)


def _numeros_node(value: str, line: int = 0) -> ASTNode:
    node = ASTNode("numeros", line=line)
    for char in value:
        if char == ".":
            node.add(_terminal(".", line))
        else:
            node.add(_numero_node(char, line))
    return node


def _cadena_node(value: str, line: int = 0) -> ASTNode:
    node = ASTNode("cadena", line=line)
    text = value[1:-1] if len(value) >= 2 and value.startswith('"') and value.endswith('"') else value
    node.add(_terminal('"', line))
    words = text.split(" ")
    for index, word in enumerate(words):
        if index:
            node.add(_terminal("espacio", line))
        node.add(_palabra_node(word, line))
    node.add(_terminal('"', line))
    return node


def _palabra_node(value: str, line: int = 0) -> ASTNode:
    node = ASTNode("palabra", line=line)
    for char in value:
        node.add(_letras_node(char, line))
    return node


def _operador_node(name: str, value: str, line: int = 0) -> ASTNode:
    return _production(name, [_terminal(value, line)], line)


def _instructions_node(nodes: Iterable[ASTNode]) -> ASTNode:
    wrapper = ASTNode("instrucciones")
    for child in nodes:
        wrapper.add(_to_bnf_node(child))
    return wrapper


def _to_bnf_node(node: ASTNode) -> ASTNode:
    if node.name == "Declaracion":
        result = ASTNode("declaracion", line=node.line)
        result.add(_terminal("definir", node.line))
        result.add(_tipo_node(_value_of(node, "Tipo"), node.line))
        result.add(_identificador_node(_value_of(node, "Identificador"), node.line))
        value = _node_by_name(node, "Valor")
        if value:
            result.add(_terminal("=", value.line))
            result.add(_value_node(value.value, value.line))
        result.add(_terminal(";", node.line))
        return result

    if node.name == "Asignacion":
        result = ASTNode("asignacion", line=node.line)
        result.add(_terminal("asignar", node.line))
        result.add(_identificador_node(_value_of(node, "Identificador"), node.line))
        result.add(_terminal("=", node.line))
        value = _node_by_name(node, "Valor")
        result.add(_value_node(value.value, value.line) if value else ASTNode("valor"))
        result.add(_terminal(";", node.line))
        return result

    if node.name == "Mostrar":
        result = ASTNode("mostrar", line=node.line)
        expr = _value_of(node, "Expresion")
        result.extend([_terminal("mostrar", node.line), _terminal("(", node.line)])
        result.add(_cadena_node(expr, node.line) if expr.startswith('"') else _identificador_node(expr, node.line))
        result.extend([_terminal(")", node.line), _terminal(";", node.line)])
        return result

    if node.name == "Pedir":
        result = ASTNode("pedir", line=node.line)
        result.extend([_terminal("pedir", node.line), _terminal("(", node.line)])
        result.add(_identificador_node(_value_of(node, "Identificador"), node.line))
        result.extend([_terminal(")", node.line), _terminal(";", node.line)])
        return result

    if node.name == "Condicion":
        result = ASTNode("condicion", line=node.line)
        result.add(_identificador_node(_value_of(node, "Identificador"), node.line))
        result.add(_operador_node("operador_cond", _value_of(node, "Operador"), node.line))
        value = _node_by_name(node, "Valor")
        result.add(_value_node(value.value, value.line) if value else ASTNode("valor"))
        return result

    if node.name == "Si":
        result = ASTNode("si", line=node.line)
        condition = _node_by_name(node, "Condicion")
        then_node = _node_by_name(node, "Entonces")
        else_node = _node_by_name(node, "SiNo")
        result.extend([_terminal("si", node.line), _terminal("(", node.line)])
        result.add(_to_bnf_node(condition) if condition else ASTNode("condicion"))
        result.extend([_terminal(")", node.line), _terminal("entonces", node.line)])
        result.add(_instructions_node(then_node.children if then_node else []))
        if else_node:
            result.add(_terminal("si_no", else_node.line))
            result.add(_instructions_node(else_node.children))
        result.add(_terminal("final_si", node.line))
        return result

    if node.name == "Mientras":
        result = ASTNode("mientras", line=node.line)
        condition = _node_by_name(node, "Condicion")
        instructions = _node_by_name(node, "Instrucciones")
        result.extend([_terminal("mientras", node.line), _terminal("(", node.line)])
        result.add(_to_bnf_node(condition) if condition else ASTNode("condicion"))
        result.add(_terminal(")", node.line))
        result.add(_instructions_node(instructions.children if instructions else []))
        result.add(_terminal("final_mientras", node.line))
        return result

    if node.name == "Segun":
        result = ASTNode("segun", line=node.line)
        result.extend([_terminal("segun", node.line), _terminal("(", node.line)])
        result.add(_identificador_node(_value_of(node, "Selector"), node.line))
        result.add(_terminal(")", node.line))
        for child in node.children:
            if child.name in {"Caso", "Defecto"}:
                result.add(_to_bnf_node(child))
        result.add(_terminal("final_segun", node.line))
        return result

    if node.name == "Caso":
        result = ASTNode("caso", line=node.line)
        value = _node_by_name(node, "Valor")
        result.add(_terminal("caso", node.line))
        result.add(_value_node(value.value, value.line) if value else ASTNode("valor"))
        result.add(_terminal(":", node.line))
        result.add(_instructions_node(child for child in node.children if child.name != "Valor"))
        return result

    if node.name == "Defecto":
        result = ASTNode("defecto", line=node.line)
        result.extend([_terminal("defecto", node.line), _terminal(":", node.line)])
        result.add(_instructions_node(node.children))
        return result

    if node.name == "Repetir":
        result = ASTNode("repetir", line=node.line)
        result.extend([_terminal("repetir", node.line), _terminal("(", node.line)])
        for index, child in enumerate([c for c in node.children if c.name in {"Inicializador", "Condicion", "Incremento"}]):
            if index:
                result.add(_terminal(",", child.line))
            result.add(_to_bnf_node(child))
        result.add(_terminal(")", node.line))
        instructions = _node_by_name(node, "Instrucciones")
        result.add(_instructions_node(instructions.children if instructions else []))
        result.add(_terminal("final_repetir", node.line))
        return result

    if node.name == "Inicializador":
        result = ASTNode("inicializador", line=node.line)
        result.add(_production("tipo", [_terminal("entero", node.line)], node.line))
        result.add(_identificador_node(_value_of(node, "Identificador"), node.line))
        result.add(_terminal("=", node.line))
        result.add(_numero_node(_value_of(node, "Valor"), node.line))
        return result

    if node.name == "Incremento":
        result = ASTNode("incremento", line=node.line)
        result.add(_identificador_node(_value_of(node, "Identificador"), node.line))
        result.add(_operador_node("operador", _value_of(node, "Operador"), node.line))
        return result

    if node.name == "HacerHasta":
        result = ASTNode("hacer", line=node.line)
        instructions = _node_by_name(node, "Instrucciones")
        condition = _node_by_name(node, "Condicion")
        result.add(_terminal("hacer", node.line))
        result.add(_instructions_node(instructions.children if instructions else []))
        result.extend([_terminal("hasta", node.line), _terminal("(", node.line)])
        result.add(_to_bnf_node(condition) if condition else ASTNode("condicion"))
        result.add(_terminal(")", node.line))
        return result

    if node.name == "Funcion":
        result = ASTNode("funcion", line=node.line)
        body = _node_by_name(node, "Instrucciones")
        ret = _node_by_name(node, "Retorno")
        result.add(_terminal("función", node.line))
        result.add(_identificador_node(_value_of(node, "Nombre"), node.line))
        result.add(_terminal("(", node.line))
        param = _value_of(node, "Parametro")
        if param:
            result.add(_identificador_node(param, node.line))
        result.add(_terminal(")", node.line))
        result.add(_instructions_node(body.children if body else []))
        if ret:
            result.add(_to_bnf_node(ret))
        result.add(_terminal("final_funcion", node.line))
        return result

    if node.name == "Retorno":
        result = ASTNode("retorno", line=node.line)
        value = _node_by_name(node, "Valor")
        result.add(_terminal("retorno", node.line))
        result.add(_value_node(value.value, value.line) if value else ASTNode("valor"))
        result.add(_terminal(";", node.line))
        return result

    if node.name == "OperacionAritmetica":
        result = ASTNode("operacion_arit", line=node.line)
        result.add(_identificador_node(_value_of(node, "Identificador"), node.line))
        result.add(_operador_node("operador_arit", _value_of(node, "Operador"), node.line))
        result.add(_numeros_node(_value_of(node, "Numero"), node.line))
        result.add(_terminal(";", node.line))
        return result

    result = ASTNode(node.name.lower(), node.value, node.line)
    for child in node.children:
        result.add(_to_bnf_node(child))
    return result
