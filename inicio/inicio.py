from flask import Blueprint, session, redirect, url_for, render_template_string

inicio_bp = Blueprint("inicio", __name__)

INICIO_STYLE = """
<style>
* { box-sizing: border-box; }
body {
    font-family: -apple-system, 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #6b73ff 0%, #ff6b9d 100%);
    display: flex; justify-content: center; align-items: center;
    height: 100vh; margin: 0;
}
.card {
    background: white; padding: 48px; border-radius: 16px;
    width: 380px; text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.card h1 { color: #1a1a1a; margin: 0 0 8px; font-size: 24px; }
.card p { color: #666; font-size: 14px; margin-bottom: 28px; }
.btn-salir {
    padding: 10px 24px; background: #f5f5f5; color: #333;
    border: 1px solid #d9d9d9; border-radius: 8px; font-size: 14px;
    cursor: pointer; text-decoration: none; display: inline-block;
}
.btn-salir:hover { background: #eaeaea; }
</style>
"""

@inicio_bp.route("/")
@inicio_bp.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))
    usuario = session["usuario"]
    return render_template_string(INICIO_STYLE + """
        <div class="card">
            <h1>Bienvenido, {{ usuario }}</h1>
            <p>Has iniciado sesión correctamente.</p>
            <a href="/logout" class="btn-salir">Cerrar sesión</a>
        </div>
    """, usuario=usuario)