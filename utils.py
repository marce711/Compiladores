TIPOS_DATO = {"entero", "decimal", "texto", "booleano"}
VALORES_BOOL = {"verdadero", "falso"}

STATEMENT_STARTERS = {
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

BLOCK_ENDERS = {
    "si_no",
    "final_si",
    "caso",
    "defecto",
    "final_segun",
    "final_mientras",
    "final_repetir",
    "hasta",
    "retorno",
    "final_funcion",
}


def token_text(token) -> str:
    if token is None:
        return "fin de archivo"
    return f"'{token.lexema}' ({token.token})"


def infer_literal_type(token) -> str:
    if token.token == "TOKEN_NUM":
        return "entero"
    if token.token == "TOKEN_DECIMAL":
        return "decimal"
    if token.token == "TOKEN_TEXTO":
        return "texto"
    if token.lexema in VALORES_BOOL:
        return "booleano"
    return "desconocido"
