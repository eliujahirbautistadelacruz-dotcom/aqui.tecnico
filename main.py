import os
import sqlite3
from flask import Flask, request, redirect, render_template_string, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "tu_clave_secreta_super_segura"
DB = "usuarios.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

BASE_STYLE = """
<style>
body { font-family: 'Segoe UI', sans-serif; background: #1e1e2f; color: white;
       display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.box { background: #2a2a40; padding: 40px; border-radius: 12px; width: 300px; }
h2 { text-align: center; margin-bottom: 20px; }
input { width: 100%; padding: 10px; margin: 8px 0; border-radius: 6px; border: none;
        box-sizing: border-box; }
button { width: 100%; padding: 10px; margin-top: 10px; border: none; border-radius: 6px;
         background: #3a3af0; color: white; font-weight: bold; cursor: pointer; }
button:hover { background: #2a2ad0; }
a { color: #8a8aff; text-decoration: none; }
.msg { color: #ff6b6b; text-align: center; }
</style>
"""

@app.route("/")
def home():
    if "usuario" in session:
        return render_template_string(BASE_STYLE + """
            <div class="box">
                <h2>Bienvenido, {{ usuario }}</h2>
                <a href="/logout">Cerrar sesión</a>
            </div>
        """, usuario=session["usuario"])
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]
        conn = sqlite3.connect(DB)
        row = conn.execute("SELECT password FROM usuarios WHERE usuario = ?", (usuario,)).fetchone()
        conn.close()
        if row and check_password_hash(row[0], password):
            session["usuario"] = usuario
            return redirect(url_for("home"))
        error = "Usuario o contraseña incorrectos"
    return render_template_string(BASE_STYLE + """
        <div class="box">
            <h2>Iniciar sesión</h2>
            {% if error %}<p class="msg">{{ error }}</p>{% endif %}
            <form method="POST">
                <input name="usuario" placeholder="Usuario" required>
                <input name="password" type="password" placeholder="Contraseña" required>
                <button type="submit">Entrar</button>
            </form>
            <p style="text-align:center; margin-top:10px;">
                ¿No tienes cuenta? <a href="/registro">Regístrate</a>
            </p>
        </div>
    """, error=error)

@app.route("/registro", methods=["GET", "POST"])
def registro():
    error = None
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]
        conn = sqlite3.connect(DB)
        try:
            conn.execute(
                "INSERT INTO usuarios (usuario, password) VALUES (?, ?)",
                (usuario, generate_password_hash(password))
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            error = "Ese usuario ya existe"
            conn.close()
    return render_template_string(BASE_STYLE + """
        <div class="box">
            <h2>Crear cuenta</h2>
            {% if error %}<p class="msg">{{ error }}</p>{% endif %}
            <form method="POST">
                <input name="usuario" placeholder="Usuario" required>
                <input name="password" type="password" placeholder="Contraseña" required>
                <button type="submit">Registrarse</button>
            </form>
            <p style="text-align:center; margin-top:10px;">
                <a href="/login">Ya tengo cuenta</a>
            </p>
        </div>
    """, error=error)

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    