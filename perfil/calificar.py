import sqlite3
import os
from flask import Blueprint, session, redirect, url_for, render_template_string, request

calificar_bp = Blueprint("calificar", __name__)
DB = os.environ.get("DB_PATH", "usuarios.db")

ESTILO = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }
body {
    font-family: -apple-system, 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #6b73ff 0%, #ff6b9d 100%);
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; margin: 0; padding: 16px;
}
.card { background: white; padding: 36px; border-radius: 16px; width: 100%; max-width: 360px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.card h2 { color: #1a1a1a; margin: 0 0 4px; font-size: 20px; }
.card p.sub { color: #666; font-size: 13px; margin-bottom: 20px; }
.estrellas { display: flex; gap: 6px; font-size: 34px; margin-bottom: 18px; justify-content: center; }
.estrellas label { cursor: pointer; color: #ddd; }
.estrellas input { display: none; }
.estrellas input:checked ~ label,
.estrellas label:hover, .estrellas label:hover ~ label { color: #f5a623; }
textarea { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #d9d9d9;
           font-size: 15px; font-family: inherit; margin-bottom: 16px; }
button { width: 100%; padding: 13px; background: #6b73ff; color: white; border: none;
         border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 15px; }
.volver { text-align: center; margin-top: 14px; font-size: 13px; }
.volver a { color: #6b73ff; text-decoration: none; }
</style>
"""

@calificar_bp.route("/calificar/<tecnico>", methods=["GET", "POST"])
def calificar(tecnico):
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        estrellas = int(request.form["estrellas"])
        comentario = request.form.get("comentario", "")
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT INTO calificaciones (tecnico, autor, estrellas, comentario) VALUES (?, ?, ?, ?)",
            (tecnico, session["usuario"], estrellas, comentario)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("usuario.panel"))

    return render_template_string(ESTILO + """
        <div class="card">
            <h2>Calificar a {{ tecnico }}</h2>
            <p class="sub">¿Cómo te fue con este técnico?</p>
            <form method="POST">
                <div class="estrellas">
                    <input type="radio" name="estrellas" value="5" id="e5"><label for="e5">★</label>
                    <input type="radio" name="estrellas" value="4" id="e4"><label for="e4">★</label>
                    <input type="radio" name="estrellas" value="3" id="e3" checked><label for="e3">★</label>
                    <input type="radio" name="estrellas" value="2" id="e2"><label for="e2">★</label>
                    <input type="radio" name="estrellas" value="1" id="e1"><label for="e1">★</label>
                </div>
                <textarea name="comentario" rows="3" placeholder="Cuéntale a otros cómo te fue (opcional)"></textarea>
                <button type="submit">Enviar calificación</button>
            </form>
            <p class="volver"><a href="/usuario/panel">Volver</a></p>
        </div>
    """, tecnico=tecnico)
