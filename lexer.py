import re
from dataclasses import dataclass

palabrasReserv = {
    "definir",
    "asignar",
    "entero",
    "decimal",
    "texto",
    "booleano",
    "nulo",
    "mostrar",
    "pedir",
    "si",
    "entonces",
    "si_no",
    "final_si",
    "segun",
    "caso",
    "defecto",
    "final_segun",
    "mientras",
    "final_mientras",
    "repetir",
    "final_repetir",
    "hacer",
    "hasta",
    "funcion",
    "función",
    "retorno",
    "final_funcion",
    "verdadero",
    "falso",
    "y",
    "o",
    "no",
}

tokensReserv = {palabra: f"TOKEN_{palabra.upper()}" for palabra in palabrasReserv}

operadores = {
    "++": "TOKEN_INCREMENTO",
    "--": "TOKEN_DECREMENTO",
    "==": "TOKEN_IGUALDAD",
    "!=": "TOKEN_DIFERENTE",
    "<=": "TOKEN_MENOR_IGUAL",
    ">=": "TOKEN_MAYOR_IGUAL",
    "=": "TOKEN_IGUAL_ASIG",
    "+": "TOKEN_SUMA",
    "-": "TOKEN_RESTA",
    "*": "TOKEN_MULT",
    "/": "TOKEN_DIV",
    "%": "TOKEN_MOD",
    "<": "TOKEN_MENOR",
    ">": "TOKEN_MAYOR",
}

simbolos = {
    "(": "T_PARENTESIS_ABRE",
    ")": "T_PARENTESIS_CIERRE",
    ";": "T_PUNTO_COMA",
    ":": "T_DOS_PUNTOS",
    ",": "T_COMA",
}

patronToken = re.compile(
    r"""
    (?P<TEXTO>"[^"\n]*")
    |(?P<TEXTO_INCOMPLETO>"[^"\n]*(?=$|\n))
    |(?P<COMILLA_SUELTA>")
    |(?P<IDENTIFICADOR_INVALIDO>\d+[a-zA-Z][a-zA-Z0-9]*)
    |(?P<IDENTIFICADOR_MAYUS>[A-Z][a-zA-Z0-9]*)
    |(?P<DECIMAL>\d+\.\d+)
    |(?P<DECIMAL_INVALIDO>\d+\.)
    |(?P<ENTERO>\d+)
    |(?P<RESERVADA_COMPUESTA>si_no|final_si|final_segun|final_mientras|final_repetir|final_funcion|función)
    |(?P<IDENTIFICADOR>[a-z][a-z0-9]*)
    |(?P<OPERADOR>\+\+|--|==|!=|<=|>=|=|\+|-|\*|/|%|<|>)
    |(?P<SIMBOLO>[();:,])
    |(?P<SALTO>\n)
    |(?P<ESPACIO>[ \t\r]+)
    |(?P<DESCONOCIDO>.)
    """,
    re.VERBOSE,
)


@dataclass
class Token:
    numero: int
    token: str
    lexema: str
    tipo: str
    linea: int


@dataclass
class Error:
    numero: int
    descripcion: str
    linea: int


INICIOS_INSTRUCCION = {
    "definir",
    "asignar",
    "mostrar",
    "pedir",
    "si",
    "segun",
    "mientras",
    "repetir",
    "hacer",
    "funcion",
    "función",
}

TIPOS_RESERVADOS = {"entero", "decimal", "texto", "booleano"}


def distancia_levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, char_a in enumerate(a, 1):
        curr = [i]
        for j, char_b in enumerate(b, 1):
            curr.append(
                min(
                    curr[j - 1] + 1,
                    prev[j] + 1,
                    prev[j - 1] + (char_a != char_b),
                )
            )
        prev = curr
    return prev[-1]


def palabra_reservada_cercana(lexema):
    mejor = min(palabrasReserv, key=lambda palabra: distancia_levenshtein(lexema, palabra))
    distancia = distancia_levenshtein(lexema, mejor)
    limite = 1 if len(mejor) <= 4 else 2
    if distancia <= limite:
        return mejor
    return None


def analizador_lexico(codigo):
    tokens = []
    errores = []
    linea_actual = 1
    token_numero = 1
    error_numero = 1
    inicio_linea = True
    lexema_anterior = ""

    for match in patronToken.finditer(codigo):
        tipo = match.lastgroup
        lexema = match.group()

        if tipo == "SALTO":
            linea_actual += 1
            inicio_linea = True
            lexema_anterior = ""
            continue
        if tipo == "ESPACIO":
            continue
        if tipo in {"TEXTO_INCOMPLETO", "COMILLA_SUELTA"}:
            errores.append(Error(error_numero, "Cadena de texto incompleta", linea_actual))
            error_numero += 1
            continue
        if tipo == "IDENTIFICADOR_INVALIDO":
            errores.append(Error(error_numero, f"Identificador invalido: {lexema}. Debe iniciar con letra minuscula.", linea_actual))
            error_numero += 1
            continue
        if tipo == "IDENTIFICADOR_MAYUS":
            errores.append(Error(error_numero, f"Palabra o identificador invalido: {lexema}. FlowCode usa minusculas.", linea_actual))
            error_numero += 1
            continue
        if tipo == "DECIMAL_INVALIDO":
            errores.append(Error(error_numero, f"Decimal invalido: {lexema}. Debe tener digitos despues del punto.", linea_actual))
            error_numero += 1
            continue
        if tipo == "DESCONOCIDO":
            errores.append(Error(error_numero, f"Caracter invalido: {lexema}", linea_actual))
            error_numero += 1
            continue

        if tipo in {"IDENTIFICADOR", "RESERVADA_COMPUESTA"}:
            if lexema in palabrasReserv:
                token = tokensReserv[lexema]
                tipo_desc = "Reservada"
            else:
                sugerida = palabra_reservada_cercana(lexema)
                espera_tipo = lexema_anterior == "definir" and sugerida in TIPOS_RESERVADOS
                if (inicio_linea and sugerida in INICIOS_INSTRUCCION) or espera_tipo:
                    errores.append(
                        Error(
                            error_numero,
                            f"Palabra reservada mal escrita: {lexema}. ¿Quisiste decir '{sugerida}'?",
                            linea_actual,
                        )
                    )
                    error_numero += 1
                    inicio_linea = False
                    lexema_anterior = lexema
                    continue
                token = "TOKEN_ID"
                tipo_desc = "Identificador"
        elif tipo == "ENTERO":
            token = "TOKEN_NUM"
            tipo_desc = "Entero"
        elif tipo == "DECIMAL":
            token = "TOKEN_DECIMAL"
            tipo_desc = "Decimal"
        elif tipo == "TEXTO":
            token = "TOKEN_TEXTO"
            tipo_desc = "Texto"
        elif tipo == "OPERADOR":
            token = operadores.get(lexema, "TOKEN_OP")
            tipo_desc = "Operador"
        elif tipo == "SIMBOLO":
            token = simbolos.get(lexema, "TOKEN_SIM")
            tipo_desc = "Simbolo"
        else:
            continue

        tokens.append(Token(token_numero, token, lexema, tipo_desc, linea_actual))
        token_numero += 1
        inicio_linea = False
        lexema_anterior = lexema

    return tokens, errores


def tabla_simbolos(tokens):
    return [vars(t) for t in tokens]
