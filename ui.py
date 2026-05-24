import tkinter as tk
from tkinter import ttk

from ast_tree import print_ast
from lexer import analizador_lexico, tabla_simbolos
from parser import analizar_sintactico


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("CodeFlow Studio")
        self.root.geometry("1280x820")
        self.root.configure(bg="#F5F3FF")

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
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"), background=self.fondo, foreground=self.morado)
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=10)
        style.configure("Treeview", background=self.blanco, foreground="black", rowheight=25, fieldbackground=self.blanco)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.morado, foreground="white")
        style.map("TButton", background=[("active", self.celeste)])

    def construir_ui(self):
        ttk.Label(self.root, text="CodeFlow Studio", style="Title.TLabel").pack(pady=10)

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
        self.editor.tag_configure("error_line", background=self.error_bg, underline=True)

        frame_botones = ttk.Frame(self.root)
        frame_botones.pack(pady=10)

        tk.Button(
            frame_botones,
            text="Analizar",
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

        self.tabla_tokens = self.crear_tabla(
            "Tokens",
            ("n", "token", "lexema", "tipo", "linea"),
            {"n": 60, "token": 170, "lexema": 160, "tipo": 120, "linea": 70},
        )
        self.tabla_errores_lexicos = self.crear_tabla(
            "Errores lexicos",
            ("n", "descripcion", "linea"),
            {"n": 60, "descripcion": 650, "linea": 80},
        )
        self.tabla_errores_sintacticos = self.crear_tabla(
            "Errores sintacticos",
            ("n", "tipo", "descripcion", "linea", "sugerencia"),
            {"n": 50, "tipo": 100, "descripcion": 430, "linea": 70, "sugerencia": 430},
        )
        self.tabla_errores_semanticos = self.crear_tabla(
            "Errores semanticos",
            ("n", "tipo", "descripcion", "linea", "sugerencia"),
            {"n": 50, "tipo": 100, "descripcion": 430, "linea": 70, "sugerencia": 430},
        )
        self.tabla_simbolos = self.crear_tabla(
            "Tabla de simbolos",
            ("token", "lexema", "tipo_dato", "linea", "alcance", "estructura", "valor", "categoria"),
            {
                "token": 150,
                "lexema": 120,
                "tipo_dato": 100,
                "linea": 70,
                "alcance": 180,
                "estructura": 130,
                "valor": 130,
                "categoria": 120,
            },
        )
        self.arbol = self.crear_arbol("Arbol sintactico")

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

    def crear_arbol(self, titulo):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=titulo)
        tree = ttk.Treeview(frame, show="tree")
        y_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=y_scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return tree

    def limpiar(self):
        self.editor.delete("1.0", tk.END)
        self.editor.tag_remove("error_line", "1.0", tk.END)
        for tabla in self.tablas():
            for item in tabla.get_children():
                tabla.delete(item)

    def analizar(self):
        codigo = self.editor.get("1.0", tk.END)
        self.editor.tag_remove("error_line", "1.0", tk.END)
        for tabla in self.tablas():
            for item in tabla.get_children():
                tabla.delete(item)

        tokens, errores_lexicos = analizador_lexico(codigo)

        for token in tabla_simbolos(tokens):
            self.tabla_tokens.insert(
                "",
                tk.END,
                values=(token["numero"], token["token"], token["lexema"], token["tipo"], token["linea"]),
            )

        for error in errores_lexicos:
            self.tabla_errores_lexicos.insert("", tk.END, values=(error.numero, error.descripcion, error.linea))
            self.resaltar_linea(error.linea)

        ast_root, errores_sintacticos, errores_semanticos, simbolos = analizar_sintactico(tokens)
        print_ast(ast_root)

        for error in errores_sintacticos:
            self.tabla_errores_sintacticos.insert(
                "",
                tk.END,
                values=(error.numero, error.tipo, error.descripcion, error.linea, error.sugerencia),
            )
            self.resaltar_linea(error.linea)

        for error in errores_semanticos:
            self.tabla_errores_semanticos.insert(
                "",
                tk.END,
                values=(error.numero, error.tipo, error.descripcion, error.linea, error.sugerencia),
            )
            self.resaltar_linea(error.linea)

        for symbol in simbolos.as_rows():
            self.tabla_simbolos.insert(
                "",
                tk.END,
                values=(
                    symbol["token"],
                    symbol["lexema"],
                    symbol["tipo_dato"],
                    symbol["linea"],
                    symbol["alcance"],
                    symbol["estructura"],
                    symbol["valor"],
                    symbol["categoria"],
                ),
            )

        self.insertar_nodo_ast("", ast_root)

    def tablas(self):
        return [
            self.tabla_tokens,
            self.tabla_errores_lexicos,
            self.tabla_errores_sintacticos,
            self.tabla_errores_semanticos,
            self.tabla_simbolos,
            self.arbol,
        ]

    def insertar_nodo_ast(self, parent, node):
        label = node.name if not node.value else f"{node.name}: {node.value}"
        if node.line:
            label = f"{label} (linea {node.line})"
        item = self.arbol.insert(parent, tk.END, text=label, open=True)
        for child in node.children:
            self.insertar_nodo_ast(item, child)

    def resaltar_linea(self, linea):
        if linea <= 0:
            return
        start = f"{linea}.0"
        end = f"{linea}.end"
        self.editor.tag_add("error_line", start, end)
