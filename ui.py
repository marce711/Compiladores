import tkinter as tk
from tkinter import ttk

from ast_tree import print_ast, to_bnf_tree
from lexer import analizador_lexico
from parser import analizar_sintactico


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("FlowCode Studio - Compilador")
        self.root.geometry("1280x820")
        self.root.configure(bg="#F5F3FF")
        self.last_ast_root = None
        self.tree_zoom = 1.0
        self.configurar_estilos()
        self.construir_ui()

    def configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        self.morado = "#6D28D9"
        self.celeste = "#38BDF8"
        self.blanco = "#FFFFFF"
        self.fondo = "#F5F3FF"
        self.error_bg = "#7F1D1D"

        style.configure("TFrame", background=self.fondo)
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), background=self.fondo, foreground=self.morado)
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=10)
        style.configure("Treeview", background=self.blanco, foreground="black", rowheight=25, fieldbackground=self.blanco)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.morado, foreground="white")
        style.map("TButton", background=[("active", self.celeste)])

    def construir_ui(self):
        ttk.Label(self.root, text="FlowCode Studio", style="Title.TLabel").pack(pady=10)

        frame_editor = ttk.Frame(self.root)
        frame_editor.pack(fill="x", padx=20)

        self.editor = tk.Text(
            frame_editor,
            height=14,
            font=("Consolas", 12),
            bg="#1E1E2F",
            fg="#E0E7FF",
            insertbackground="white",
            wrap="none",
        )
        self.editor.pack(fill="x")
        self.editor.tag_configure("error_line", background=self.error_bg, foreground="white", underline=True)

        frame_botones = ttk.Frame(self.root)
        frame_botones.pack(pady=10)

        tk.Button(
            frame_botones,
            text="Analizar Código",
            bg=self.morado,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.analizar,
        ).pack(side="left", padx=10)

        tk.Button(
            frame_botones,
            text="Limpiar",
            bg=self.celeste,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.limpiar,
        ).pack(side="left", padx=10)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        self.tabla_unificada = self.crear_tabla(
            "Tabla de Símbolos y Tokens",
            ("token", "categoria", "linea", "lexema"),
            {"token": 220, "categoria": 180, "linea": 90, "lexema": 260},
        )

        self.tabla_estructuras = self.crear_tabla(
            "Estructuras del Programa",
            ("orden", "tipo_estructura", "linea", "descripcion"),
            {"orden": 80, "tipo_estructura": 200, "linea": 100, "descripcion": 720},
        )

        self.tabla_errores_lexicos = self.crear_tabla(
            "Errores Léxicos",
            ("n", "descripcion", "linea"),
            {"n": 60, "descripcion": 650, "linea": 80},
        )

        self.tabla_errores_sintacticos = self.crear_tabla(
            "Errores Sintácticos",
            ("n", "tipo", "descripcion", "linea", "sugerencia"),
            {"n": 50, "tipo": 110, "descripcion": 430, "linea": 70, "sugerencia": 430},
        )

        self.tabla_errores_semanticos = self.crear_tabla(
            "Errores Semánticos",
            ("n", "tipo", "descripcion", "linea", "sugerencia"),
            {"n": 50, "tipo": 110, "descripcion": 430, "linea": 70, "sugerencia": 430},
        )

        self.frame_arbol = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_arbol, text="Árbol Sintáctico")
        frame_zoom = ttk.Frame(self.frame_arbol)
        frame_zoom.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        tk.Button(frame_zoom, text="-", width=4, command=lambda: self.cambiar_zoom(0.85)).pack(side="left", padx=3)
        tk.Button(frame_zoom, text="100%", width=6, command=self.restablecer_zoom).pack(side="left", padx=3)
        tk.Button(frame_zoom, text="+", width=4, command=lambda: self.cambiar_zoom(1.18)).pack(side="left", padx=3)

        self.canvas_arbol = tk.Canvas(self.frame_arbol, bg="#FAFAF9", highlightthickness=0)
        y_scroll = ttk.Scrollbar(self.frame_arbol, orient="vertical", command=self.canvas_arbol.yview)
        x_scroll = ttk.Scrollbar(self.frame_arbol, orient="horizontal", command=self.canvas_arbol.xview)
        self.canvas_arbol.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.canvas_arbol.grid(row=1, column=0, sticky="nsew")
        y_scroll.grid(row=1, column=1, sticky="ns")
        x_scroll.grid(row=2, column=0, sticky="ew")
        self.frame_arbol.rowconfigure(1, weight=1)
        self.frame_arbol.columnconfigure(0, weight=1)

    def crear_tabla(self, titulo, columnas, anchos):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=titulo)

        tree = ttk.Treeview(frame, columns=columnas, show="headings")
        y_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        for col in columnas:
            tree.heading(col, text=col.upper())
            tree.column(col, anchor="center", width=anchos.get(col, 120), stretch=True)

        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return tree

    def limpiar(self):
        self.editor.delete("1.0", tk.END)
        self.editor.tag_remove("error_line", "1.0", tk.END)
        for tabla in self.tablas():
            for item in tabla.get_children():
                tabla.delete(item)
        self.canvas_arbol.delete("all")
        self.last_ast_root = None

    def analizar(self):
        codigo = self.editor.get("1.0", tk.END).strip()
        if not codigo:
            return

        self.editor.tag_remove("error_line", "1.0", tk.END)
        for tabla in self.tablas():
            for item in tabla.get_children():
                tabla.delete(item)
        self.canvas_arbol.delete("all")

        tokens, errores_lexicos = analizador_lexico(codigo)

        for token in tokens:
            self.tabla_unificada.insert(
                "",
                tk.END,
                values=(token.token, token.tipo, token.linea, token.lexema),
            )

        for error in errores_lexicos:
            self.tabla_errores_lexicos.insert("", tk.END, values=(error.numero, error.descripcion, error.linea))
            self.resaltar_linea(error.linea)

        if errores_lexicos:
            self.last_ast_root = None
            return

        ast_root, errores_sintacticos, errores_semanticos, _ = analizar_sintactico(tokens)
        self.last_ast_root = ast_root

        for error in errores_sintacticos:
            self.tabla_errores_sintacticos.insert(
                "",
                tk.END,
                values=(error.numero, error.tipo, error.descripcion, error.linea, error.sugerencia),
            )
            self.resaltar_linea(error.linea)

        if errores_sintacticos:
            self.last_ast_root = None
            self.canvas_arbol.delete("all")
            self.canvas_arbol.create_text(
                40,
                40,
                anchor="nw",
                text="No se genera árbol sintáctico porque existen errores sintácticos.",
                fill="#7F1D1D",
                font=("Segoe UI", 12, "bold"),
            )
            return

        for error in errores_semanticos:
            self.tabla_errores_semanticos.insert(
                "",
                tk.END,
                values=(error.numero, error.tipo, error.descripcion, error.linea, error.sugerencia),
            )
            self.resaltar_linea(error.linea)

        self._estructura_orden = 1
        self.extraer_estructuras_recursivo(ast_root)
        print_ast(to_bnf_tree(ast_root))
        self.dibujar_arbol()

    def extraer_estructuras_recursivo(self, node):
        if not node:
            return

        estructuras = {
            "Declaracion": "Declaración de variable",
            "Asignacion": "Asignación de valor",
            "Si": "Estructura condicional (si)",
            "Entonces": "Bloque de instrucciones",
            "SiNo": "Bloque alternativo (si_no)",
            "Mientras": "Bucle condicional (mientras)",
            "Repetir": "Bucle iterativo (repetir)",
            "HacerHasta": "Bucle hacer...hasta",
            "Funcion": "Definición de función",
            "Segun": "Estructura de selección (segun)",
            "Caso": "Opción de selección (caso)",
            "Defecto": "Opción por defecto",
            "Mostrar": "Instrucción de salida (mostrar)",
            "Pedir": "Instrucción de entrada (pedir)",
            "OperacionAritmetica": "Operación aritmética",
        }

        if node.name in estructuras:
            self.tabla_estructuras.insert(
                "",
                tk.END,
                values=(self._estructura_orden, node.name, node.line, self.descripcion_estructura(node, estructuras[node.name])),
            )
            self._estructura_orden += 1

        for child in node.children:
            self.extraer_estructuras_recursivo(child)

    def descripcion_estructura(self, node, descripcion):
        valores = [child.value for child in node.children if child.value]
        if valores:
            return f"{descripcion}: {' '.join(valores)}"
        return descripcion

    def dibujar_arbol(self):
        self.canvas_arbol.delete("all")
        if not self.last_ast_root:
            return

        bnf_root = to_bnf_tree(self.last_ast_root)
        positions = {}
        leaf_counter = [0]
        zoom = self.tree_zoom
        x_gap = 120 * zoom
        y_gap = 86 * zoom
        margin = 45 * zoom

        def layout(node, depth=0):
            if not node.children:
                x = margin + leaf_counter[0] * x_gap
                leaf_counter[0] += 1
            else:
                child_xs = [layout(child, depth + 1) for child in node.children]
                x = (child_xs[0] + child_xs[-1]) / 2
            positions[id(node)] = (x, margin + depth * y_gap)
            return x

        layout(bnf_root)

        def label_for(node):
            label = f"<{node.name}>" if node.children else node.name
            if node.value:
                label = f"{label}\n{node.value}" if node.children else node.value
            return label

        def draw_edges(node):
            x1, y1 = positions[id(node)]
            for child in node.children:
                x2, y2 = positions[id(child)]
                self.canvas_arbol.create_line(x1, y1 + 20, x2, y2 - 20, fill="#64748B", width=2)
                draw_edges(child)

        def draw_nodes(node):
            x, y = positions[id(node)]
            label = label_for(node)
            width = max(62 * zoom, min(170 * zoom, len(max(label.splitlines(), key=len)) * 8 * zoom + 24 * zoom))
            height = (40 if "\n" not in label else 56) * zoom
            font_size = max(7, int(9 * zoom))
            fill = "#EDE9FE" if node.children else "#FFFFFF"
            outline = "#7C3AED" if node.children else "#CBD5E1"
            self.canvas_arbol.create_rectangle(x - width / 2, y - height / 2, x + width / 2, y + height / 2, fill=fill, outline=outline, width=2)
            self.canvas_arbol.create_text(x, y, text=label, fill="#111827", font=("Segoe UI", font_size), justify="center", width=width - 10 * zoom)
            for child in node.children:
                draw_nodes(child)

        draw_edges(bnf_root)
        draw_nodes(bnf_root)

        bbox = self.canvas_arbol.bbox("all")
        if bbox:
            self.canvas_arbol.configure(scrollregion=(bbox[0] - 40, bbox[1] - 40, bbox[2] + 40, bbox[3] + 40))

    def cambiar_zoom(self, factor):
        self.tree_zoom = max(0.35, min(2.8, self.tree_zoom * factor))
        self.dibujar_arbol()

    def restablecer_zoom(self):
        self.tree_zoom = 1.0
        self.dibujar_arbol()

    def tablas(self):
        return [
            self.tabla_unificada,
            self.tabla_estructuras,
            self.tabla_errores_lexicos,
            self.tabla_errores_sintacticos,
            self.tabla_errores_semanticos,
        ]

    def resaltar_linea(self, linea):
        if linea <= 0:
            return
        self.editor.tag_add("error_line", f"{linea}.0", f"{linea}.end")
