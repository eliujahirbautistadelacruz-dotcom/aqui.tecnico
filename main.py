import os
import sqlite3
from flask import Flask, request, redirect, render_template_string, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from inicio.inicio import inicio_bp
from perfil.escoge import escoge_bp
from perfil.tecnico import tecnico_bp
from perfil.usuario import usuario_bp
from perfil.calificar import calificar_bp

app = Flask(__name__)
app.secret_key = "tu_clave_secreta_super_segura"
app.config["PREFERRED_URL_SCHEME"] = "https"
app.register_blueprint(inicio_bp)
app.register_blueprint(escoge_bp)
app.register_blueprint(tecnico_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(calificar_bp)

# Si existe la variable DB_PATH (volumen persistente en Railway), la usa.
# Si no, usa un archivo local (para pruebas en tu laptop).
DB = os.environ.get("DB_PATH", "usuarios.db")

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT,
            email TEXT,
            metodo TEXT DEFAULT 'local',
            rol TEXT,
            oficio TEXT,
            telefono TEXT,
            precio_desde REAL,
            descripcion TEXT,
            latitud REAL,
            longitud REAL,
            fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tecnico TEXT NOT NULL,
            autor TEXT NOT NULL,
            estrellas INTEGER NOT NULL,
            comentario TEXT,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

BASE_HEAD = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }
body {
    font-family: -apple-system, 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #6b73ff 0%, #ff6b9d 100%);
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; margin: 0; padding: 16px;
}
.card { background: white; padding: 40px; border-radius: 16px; width: 100%; max-width: 360px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.card h2 { color: #1a1a1a; margin: 0 0 24px; font-size: 22px; }
label { display: block; color: #4a4a4a; font-size: 13px; margin-bottom: 6px; font-weight: 600; }
input { width: 100%; padding: 12px; margin-bottom: 16px;
        border: 1px solid #d9d9d9; border-radius: 8px; font-size: 16px; }
.btn-primary { width: 100%; padding: 13px; background: #6b73ff; color: white;
               border: none; border-radius: 8px; font-weight: 600; cursor: pointer;
               margin-bottom: 16px; font-size: 15px; }
.divider { display: flex; align-items: center; color: #999; font-size: 12px; margin: 16px 0; }
.divider::before, .divider::after { content: ""; flex: 1; border-bottom: 1px solid #e0e0e0; }
.divider span { padding: 0 10px; }
.btn-google { width: 100%; padding: 11px; background: white; color: #333;
              border: 1px solid #d9d9d9; border-radius: 8px; cursor: pointer;
              display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; }
.footer-link { text-align: center; margin-top: 20px; font-size: 13px; color: #666; }
.footer-link a { color: #6b73ff; text-decoration: none; font-weight: 600; }
.msg { color: #e74c3c; font-size: 13px; text-align: center; margin-bottom: 12px; }
@media (max-width: 480px) {
    .card { padding: 28px 22px; border-radius: 12px; }
}
</style>
"""

GOOGLE_BTN = """
<div class="divider"><span>O</span></div>
<a href="/login/google" class="btn-google">
    <svg width="18" height="18" viewBox="0 0 18 18">
        <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84c-.21 1.13-.84 2.09-1.8 2.73v2.27h2.91c1.7-1.57 2.69-3.88 2.69-6.64z"/>
        <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.91-2.27c-.81.54-1.84.86-3.05.86-2.34 0-4.33-1.58-5.04-3.71H.96v2.33C2.44 15.98 5.48 18 9 18z"/>
        <path fill="#FBBC05" d="M3.96 10.7c-.18-.54-.28-1.11-.28-1.7s.1-1.16.28-1.7V4.97H.96C.35 6.17 0 7.55 0 9s.35 2.83.96 4.03l3-2.33z"/>
        <path fill="#EA4335" d="M9 3.58c1.32 0 2.51.45 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0 5.48 0 2.44 2.02.96 4.97l3 2.33C4.67 5.16 6.66 3.58 9 3.58z"/>
    </svg>
    Iniciar sesión con Google
</a>
"""

def redirigir_tras_login(usuario):
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT rol FROM usuarios WHERE usuario = ?", (usuario,)).fetchone()
    conn.close()
    session["usuario"] = usuario
    if row and row[0]:
        session["rol"] = row[0]
        return redirect(url_for("tecnico.panel" if row[0] == "tecnico" else "usuario.panel"))
    return redirect(url_for("escoge.escoge"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]
        conn = sqlite3.connect(DB)
        row = conn.execute("SELECT password FROM usuarios WHERE usuario = ?", (usuario,)).fetchone()
        conn.close()
        if row and row[0] and check_password_hash(row[0], password):
            return redirigir_tras_login(usuario)
        error = "Usuario o contraseña incorrectos"
    return render_template_string(BASE_HEAD + """
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
            """ + GOOGLE_BTN + """
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
                "INSERT INTO usuarios (usuario, password, metodo) VALUES (?, ?, 'local')",
                (usuario, generate_password_hash(password))
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            error = "Ese usuario ya existe"
            conn.close()
    return render_template_string(BASE_HEAD + """
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
            """ + GOOGLE_BTN + """
            <p class="footer-link">¿Ya tienes cuenta? <a href="/login">Inicia sesión</a></p>
        </div>
    """, error=error)

@app.route("/login/google")
def login_google():
    redirect_uri = url_for("authorized", _external=True, _scheme="https")
    return google.authorize_redirect(redirect_uri)

@app.route("/authorized")
def authorized():
    token = google.authorize_access_token()
    user_info = token.get("userinfo")
    email = user_info["email"]
    nombre = user_info.get("name", email)

    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT usuario FROM usuarios WHERE email = ?", (email,)).fetchone()
    if not row:
        conn.execute(
            "INSERT INTO usuarios (usuario, email, metodo) VALUES (?, ?, 'google')",
            (nombre, email)
        )
        conn.commit()
    conn.close()

    return redirigir_tras_login(nombre)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
