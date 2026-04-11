import re
from dataclasses import dataclass

PALABRAS_RESERVADAS = {
    "definir","asignar","entero","decimal","texto","booleano","nulo",
    "mostrar","pedir","si","entonces","si_no","final_si",
    "segun","caso","defecto","final_segun",
    "mientras","final_mientras","repetir","final_repetir",
    "hacer","hasta",
    "funcion","retorno","fin_funcion",
    "verdadero","falso","y","o","no"
}

TOKENS_RESERVADOS = {palabra: f"TOKEN_{palabra.upper()}" for palabra in PALABRAS_RESERVADAS}

OPERADORES = {
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

SIMBOLOS = {
    "(": "T_PARENTESIS_ABRE",
    ")": "T_PARENTESIS_CIERRE",
    ";": "T_PUNTO_COMA",
    ":": "T_DOS_PUNTOS",
}

IDENT = r"[a-z][a-z0-9]*"

REGEX_DECLARACION = re.compile(
    rf"^definir\s+(entero|decimal|texto|booleano|nulo)\s+{IDENT}\s*=?\s*(\d+(\.\d+)?|\"[^\"]*\"|verdadero|falso|nulo)*\s*;$"
)

REGEX_ASIGNACION = re.compile(
    rf"^asignar\s+{IDENT}\s*=\s*({IDENT}|\d+(\.\d+)?|\"[^\"]*\"|verdadero|falso|null)(\s*[\+\-\*/]\s*({IDENT}|\d+(\.\d+)?))*\s*;$"
)

REGEX_VALOR = re.compile(r'^(\d+|\d+\.\d+|"[^"]*"|verdadero|falso|nulo)$')

REGEX_MOSTRAR = re.compile(r"^mostrar\s*\((.*)\)\s*;$")
REGEX_PEDIR = re.compile(rf"^pedir\s*\({IDENT}\)\s*;$")

REGEX_SI = re.compile(r"^si\s*\([^()]+\)\s*entonces\s*([\s\S]*?)(\s*si_no\s*[\s\S]*?)?\s*final_si$")
REGEX_SEGUN = re.compile(r"^segun\s*\([^()]+\)\s*(\s*caso\s+[^:]+:\s*[\s\S]*?;)+(\s*defecto:\s*[\s\S]*?;)?\s*final_segun$")

REGEX_MIENTRAS = re.compile(r"^mientras\s*\([^()]+\)\s*([\s\S]*?)\s*final_mientras\s*$")
REGEX_REPETIR = re.compile(r"^repetir\s*\([^,]+,[^,]+,[^,]+\)\s*([\s\S]*?)\s*final_repetir$")
REGEX_HACER = re.compile(r"^hacer\s*([\s\S]*?)\s*hasta\s*\([^()]+\)\s*;$")

REGEX_FUNCION = re.compile(
    rf"^funcion\s+{IDENT}\s*\([^()]*\)\s*([\s\S]*?)\s*retorno\s+.*;\s*final_funcion$"
)

PATRON_TOKEN = re.compile(r"""
    (?P<COMENTARIO>//[^\n]*|\#[^\n]*)
    |(?P<TEXTO>"[^"\n]*")
    |(?P<DECIMAL>\d+\.\d+)
    |(?P<ENTERO>\d+)
    |(?P<RESERVADA_COMPUESTA>si_no|final_si|final_segun|final_mientras|final_repetir|final_funcion)
    |(?P<IDENTIFICADOR>[a-z][a-z0-9]*)
    |(?P<OPERADOR>==|!=|<=|>=|=|\+|-|\*|/|%|<|>)
    |(?P<SIMBOLO>[();:])
    |(?P<SALTO>\n)
    |(?P<ESPACIO>[ \t\r]+)
    |(?P<DESCONOCIDO>.)
""", re.VERBOSE)

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

def validar_linea(linea):
    linea = linea.strip()

    if not linea:
        return True

    palabras_bloque = {
        "si", "si_no", "final_si",
        "segun", "caso", "defecto", "final_segun",
        "mientras", "final_mientras",
        "repetir", "final_repetir",
        "hacer", "hasta",
        "funcion", "retorno", "final_funcion"
    }

    primera = linea.split()[0]

    if primera in palabras_bloque:
        return True

    patrones = [
        REGEX_DECLARACION,
        REGEX_ASIGNACION,
        REGEX_MOSTRAR,
        REGEX_PEDIR
    ]

    return any(p.fullmatch(linea) for p in patrones)

def analizador_lexico(codigo):
    tokens = []
    errores = []

    linea_actual = 1
    t = 1
    e = 1

    for linea in codigo.split("\n"):
        if not linea.strip():
            linea_actual += 1
            continue

        if not validar_linea(linea):
            errores.append(Error(e, f"Estructura invalida: {linea}", linea_actual))
            e += 1

        linea_actual += 1

    linea_actual = 1

    for match in PATRON_TOKEN.finditer(codigo):
        tipo = match.lastgroup
        lexema = match.group()

        if tipo == "SALTO":
            linea_actual += 1
            continue

        if tipo in ("ESPACIO", "COMENTARIO"):
            continue

        if tipo == "DESCONOCIDO":
            errores.append(Error(e, f"Caracter invalido: {lexema}", linea_actual))
            e += 1
            continue

        if tipo in ("IDENTIFICADOR", "RESERVADA_COMPUESTA"):
            if lexema in PALABRAS_RESERVADAS:
                token = TOKENS_RESERVADOS[lexema]
                tipo_desc = "Reservada"
            else:
                token = "TOKEN_ID"
                tipo_desc = "Identificador"

        elif tipo == "ENTERO":
            token = "TOKEN_NUM"
            tipo_desc = "Numero"

        elif tipo == "DECIMAL":
            token = "TOKEN_DECIMAL"
            tipo_desc = "Decimal"

        elif tipo == "TEXTO":
            token = "TOKEN_TEXTO"
            tipo_desc = "Texto"

        elif tipo == "OPERADOR":
            token = OPERADORES.get(lexema, "TOKEN_OP")
            tipo_desc = "Operador"

        elif tipo == "SIMBOLO":
            token = SIMBOLOS.get(lexema, "TOKEN_SIM")
            tipo_desc = "Simbolo"

        else:
            continue

        tokens.append(Token(t, token, lexema, tipo_desc, linea_actual))
        t += 1

    return tokens, errores

def tabla_simbolos(tokens):
    return [vars(t) for t in tokens]