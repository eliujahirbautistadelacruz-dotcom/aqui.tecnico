import tkinter as tk
from tkinter import ttk, messagebox

USUARIOS = {"jahir": "1234"}  # usuario: contraseña

def iniciar_sesion():
    user = entry_user.get()
    pw = entry_pw.get()
    if USUARIOS.get(user) == pw:
        messagebox.showinfo("Éxito", f"Bienvenido, {user}")
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")

root = tk.Tk()
root.title("Inicio de sesión")
root.geometry("360x420")
root.configure(bg="#1e1e2f")
root.resizable(False, False)

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#1e1e2f", foreground="white", font=("Segoe UI", 11))
style.configure("TEntry", padding=6, font=("Segoe UI", 11))
style.configure("TButton", padding=8, font=("Segoe UI", 11, "bold"))
style.map("TButton", background=[("active", "#3a3af0")])

frame = tk.Frame(root, bg="#2a2a40", padx=30, pady=30)
frame.place(relx=0.5, rely=0.5, anchor="center")

tk.Label(frame, text="Bienvenido", bg="#2a2a40", fg="white",
          font=("Segoe UI", 18, "bold")).pack(pady=(0, 20))

ttk.Label(frame, text="Usuario").pack(anchor="w")
entry_user = ttk.Entry(frame, width=25)
entry_user.pack(pady=(0, 15))

ttk.Label(frame, text="Contraseña").pack(anchor="w")
entry_pw = ttk.Entry(frame, width=25, show="•")
entry_pw.pack(pady=(0, 25))

ttk.Button(frame, text="Iniciar sesión", command=iniciar_sesion).pack(fill="x")

root.mainloop()