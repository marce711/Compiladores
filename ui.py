import tkinter as tk
from tkinter import ttk, messagebox
from lexer import analizador_lexico, tabla_simbolos

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("CodeFlow Studio")
        self.root.geometry("1200x750")
        self.root.configure(bg="#F5F3FF")  # fondo claro

        self.configurar_estilos()
        self.construir_ui()

    def configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        self.morado = "#6D28D9"
        self.celeste = "#38BDF8"
        self.blanco = "#FFFFFF"
        self.fondo = "#F5F3FF"

        style.configure("TFrame", background=self.fondo)

        style.configure("Title.TLabel",
                        font=("Segoe UI", 18, "bold"),
                        background=self.fondo,
                        foreground=self.morado)

        style.configure("TButton",
                        font=("Segoe UI", 10, "bold"),
                        padding=10)

        style.map("TButton",
                  background=[("active", self.celeste)])

        style.configure("Treeview",
                        background=self.blanco,
                        foreground="black",
                        rowheight=25,
                        fieldbackground=self.blanco)

        style.configure("Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background=self.morado,
                        foreground="white")

    def construir_ui(self):
        ttk.Label(self.root, text="CodeFlow Studio", style="Title.TLabel").pack(pady=10)

        frame_editor = ttk.Frame(self.root)
        frame_editor.pack(fill="x", padx=20)

        self.editor = tk.Text(
            frame_editor,
            height=12,
            font=("Consolas", 12),
            bg="#1E1E2F",
            fg="#E0E7FF",
            insertbackground="white"
        )
        self.editor.pack(fill="x")

        frame_botones = ttk.Frame(self.root)
        frame_botones.pack(pady=10)

        tk.Button(frame_botones, text="Analizar",
                  bg=self.morado, fg="white",
                  font=("Segoe UI", 10, "bold"),
                  command=self.analizar).pack(side="left", padx=10)

        tk.Button(frame_botones, text="Limpiar",
                  bg=self.celeste, fg="white",
                  font=("Segoe UI", 10, "bold"),
                  command=self.limpiar).pack(side="left", padx=10)

        frame_tablas = ttk.Frame(self.root)
        frame_tablas.pack(fill="both", expand=True, padx=20, pady=10)

        frame_tokens = ttk.Frame(frame_tablas)
        frame_tokens.pack(side="left", fill="both", expand=True, padx=10)

        ttk.Label(frame_tokens, text="Tokens Detectados",
                  foreground=self.morado,
                  font=("Segoe UI", 11, "bold")).pack()

        self.tabla_tokens = ttk.Treeview(
            frame_tokens,
            columns=("n","token","lexema","tipo","linea"),
            show="headings"
        )

        for col in ("n","token","lexema","tipo","linea"):
            self.tabla_tokens.heading(col, text=col.upper())
            self.tabla_tokens.column(col, anchor="center", width=100)

        self.tabla_tokens.pack(fill="both", expand=True)

        frame_errores = ttk.Frame(frame_tablas)
        frame_errores.pack(side="right", fill="both", expand=True, padx=10)

        ttk.Label(frame_errores, text="Errores Léxicos",
                  foreground="red",
                  font=("Segoe UI", 11, "bold")).pack()

        self.tabla_errores = ttk.Treeview(
            frame_errores,
            columns=("n","descripcion","linea"),
            show="headings"
        )

        for col in ("n","descripcion","linea"):
            self.tabla_errores.heading(col, text=col.upper())
            self.tabla_errores.column(col, anchor="center", width=120)

        self.tabla_errores.pack(fill="both", expand=True)

    def limpiar(self):
        self.editor.delete("1.0", tk.END)

        for t in self.tabla_tokens.get_children():
            self.tabla_tokens.delete(t)

        for e in self.tabla_errores.get_children():
            self.tabla_errores.delete(e)

    def analizar(self):
        codigo = self.editor.get("1.0", tk.END)

        for t in self.tabla_tokens.get_children():
            self.tabla_tokens.delete(t)

        for e in self.tabla_errores.get_children():
            self.tabla_errores.delete(e)

        tokens, errores = analizador_lexico(codigo)

        for t in tabla_simbolos(tokens):
            self.tabla_tokens.insert("", tk.END, values=(
                t["numero"], t["token"], t["lexema"], t["tipo"], t["linea"]
            ))

        for e in errores:
            self.tabla_errores.insert("", tk.END, values=(
                e.numero, e.descripcion, e.linea
            ))
