from flask import Blueprint, session, redirect, url_for, render_template_string, request
from database import fb_update, sanitizar

escoge_bp = Blueprint("escoge", __name__)

ESCOGE_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }
body {
    font-family: -apple-system, 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #6b73ff 0%, #ff6b9d 100%);
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; margin: 0; padding: 16px;
}
.card { background: white; padding: 48px; border-radius: 16px; width: 100%; max-width: 400px;
        text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.card h1 { color: #1a1a1a; margin: 0 0 8px; font-size: 22px; }
.card p { color: #666; font-size: 14px; margin-bottom: 28px; }
.opciones { display: flex; gap: 16px; flex-wrap: wrap; }
.opcion { flex: 1; min-width: 140px; padding: 24px 16px; border: 2px solid #e0e0e0; border-radius: 12px;
    cursor: pointer; background: none; font-family: inherit; font-size: 14px; font-weight: 600;
    color: #1a1a1a; width: 100%; }
.opcion:hover { border-color: #6b73ff; background: #f5f6ff; }
.opcion .icono { font-size: 32px; display: block; margin-bottom: 8px; }
@media (max-width: 480px) { .opciones { flex-direction: column; } }
</style>
"""

@escoge_bp.route("/escoge", methods=["GET", "POST"])
def escoge():
    if "usuario" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        rol = request.form.get("rol")
        clave = sanitizar(session["usuario"])
        fb_update(f"usuarios/{clave}", {"rol": rol})
        session["rol"] = rol
        return redirect(url_for("tecnico.panel" if rol == "tecnico" else "usuario.panel"))
    return render_template_string(ESCOGE_STYLE + """
        <div class="card">
            <h1>¿Qué quieres ser?</h1>
            <p>Elige cómo quieres usar la app</p>
            <div class="opciones">
                <form method="POST" style="flex:1;">
                    <input type="hidden" name="rol" value="tecnico">
                    <button type="submit" class="opcion"><span class="icono">🔧</span>Soy técnico</button>
                </form>
                <form method="POST" style="flex:1;">
                    <input type="hidden" name="rol" value="usuario">
                    <button type="submit" class="opcion"><span class="icono">🔍</span>Busco técnico</button>
                </form>
            </div>
        </div>
    """)
