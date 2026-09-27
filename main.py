import os
import sqlite3
from flask import Flask, request, redirect, render_template_string, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from inicio.inicio import inicio_bp

app = Flask(__name__)
app.secret_key = "tu_clave_secreta_super_segura"
app.register_blueprint(inicio_bp)

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

LOGIN_STYLE = """
<style>
* { box-sizing: border-box; }
body {
    font-family: -apple-system, 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #6b73ff 0%, #ff6b9d 100%);
    display: flex; justify-content: center; align-items: center;
    height: 100vh; margin: 0;
}
.card {
    background: white; padding: 40px; border-radius: 16px;
    width: 360px; box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.card h2 { color: #1a1a1a; margin: 0 0 24px; font-size: 22px; }
label { display: block; color: #4a4a4a; font-size: 13px; margin-bottom: 6px; font-weight: 600; }
input {
    width: 100%; padding: 11px 12px; margin-bottom: 16px;
    border: 1px solid #d9d9d9; border-radius: 8px; font-size: 14px;
}
input:focus { outline: none; border-color: #6b73ff; }
.btn-primary {
    width: 100%; padding: 11px; background: #6b73ff; color: white;
    border: none; border-radius: 8px; font-weight: 600; font-size: 14px;
    cursor: pointer; margin-bottom: 16px;
}
.btn-primary:hover { background: #5a61e0; }
.footer-link { text-align: center; margin-top: 20px; font-size: 13px; color: #666; }
.footer-link a { color: #6b73ff; text-decoration: none; font-weight: 600; }
.msg { color: #e74c3c; font-size: 13px; text-align: center; margin-bottom: 12px; }
</style>
"""

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
            return redirect(url_for("inicio.home"))
        error = "Usuario o contraseña incorrectos"
    return render_template_string(LOGIN_STYLE + """
        <div class="card">
            <h2>Inicia sesión en tu cuenta</h2>
            {% if error %}<p class="msg">{{ error }}</p>{% endif %}
            <form method="POST">
                <label>Usuario</label>
                <input name="usuario" placeholder="Tu usuario" required>
                <label>Contraseña</label>
                <input type="password" name="password" placeholder="••••••••" required>
                <button type="submit" class="btn-primary">Iniciar sesión</button>
            </form>
            <p class="footer-link">¿Nuevo aquí? <a href="/registro">Crear cuenta</a></p>
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
    return render_template_string(LOGIN_STYLE + """
        <div class="card">
            <h2>Crear cuenta</h2>
            {% if error %}<p class="msg">{{ error }}</p>{% endif %}
            <form method="POST">
                <label>Usuario</label>
                <input name="usuario" placeholder="Elige un usuario" required>
                <label>Contraseña</label>
                <input type="password" name="password" placeholder="••••••••" required>
                <button type="submit" class="btn-primary">Registrarse</button>
            </form>
            <p class="footer-link">¿Ya tienes cuenta? <a href="/login">Inicia sesión</a></p>
        </div>
    """, error=error)

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)