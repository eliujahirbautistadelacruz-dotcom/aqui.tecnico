import sqlite3
from flask import Blueprint, session, redirect, url_for, render_template_string, request, jsonify

tecnico_bp = Blueprint("tecnico", __name__, url_prefix="/tecnico")
DB = "usuarios.db"

OFICIOS = [
    "plomero", "electricista", "aire_acondicionado", "gas",
    "cerrajero", "pintor", "albanil", "carpintero", "jardineria", "otro"
]

ESTILO = """
<style>
* { box-sizing: border-box; }
body {
    font-family: -apple-system, 'Segoe UI', sans-serif;
    background: #f4f5ff; margin: 0; padding: 24px;
}
.card { background: white; padding: 32px; border-radius: 16px; width: 420px;
        margin: 40px auto; box-shadow: 0 10px 40px rgba(0,0,0,0.08); }
.card h1 { color: #1a1a1a; font-size: 20px; margin: 0 0 20px; }
select, button { width: 100%; padding: 11px; border-radius: 8px; font-size: 14px; margin-bottom: 14px; }
select { border: 1px solid #d9d9d9; }
.btn-ubicacion { background: #6b73ff; color: white; border: none; cursor: pointer; font-weight: 600; }
.btn-ubicacion:hover { background: #5a61e0; }
.estado { font-size: 13px; color: #666; text-align: center; margin-bottom: 14px; }
.ok { color: #2ecc71; font-weight: 600; }
.salir { text-align: center; font-size: 13px; }
.salir a { color: #6b73ff; text-decoration: none; }
</style>
"""

@tecnico_bp.route("/panel")
def panel():
    if session.get("rol") != "tecnico":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT oficio, latitud, longitud FROM usuarios WHERE usuario = ?",
        (session["usuario"],)
    ).fetchone()
    conn.close()
    oficio_actual, lat, lng = row if row else (None, None, None)
    ubicacion_guardada = lat is not None and lng is not None

    opciones_html = "".join(
        f'<option value="{o}" {"selected" if o == oficio_actual else ""}>{o.replace("_", " ").title()}</option>'
        for o in OFICIOS
    )

    return render_template_string(ESTILO + """
        <div class="card">
            <h1>Panel de técnico — {{ usuario }}</h1>

            <form method="POST" action="/tecnico/oficio">
                <label style="font-size:13px; color:#4a4a4a; font-weight:600;">Tu oficio</label>
                <select name="oficio">""" + opciones_html + """</select>
                <button type="submit" class="btn-ubicacion" style="background:#333;">Guardar oficio</button>
            </form>

            <div class="estado" id="estado">
                {% if ubicacion %}
                    <span class="ok">✓ Ubicación guardada</span>
                {% else %}
                    Aún no has compartido tu ubicación
                {% endif %}
            </div>
            <button class="btn-ubicacion" onclick="compartirUbicacion()">📍 Compartir mi ubicación</button>

            <p class="salir"><a href="/logout">Cerrar sesión</a></p>
        </div>

        <script>
        function compartirUbicacion() {
            if (!navigator.geolocation) {
                alert("Tu navegador no soporta geolocalización");
                return;
            }
            navigator.geolocation.getCurrentPosition(function(pos) {
                fetch("/tecnico/ubicacion", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        lat: pos.coords.latitude,
                        lng: pos.coords.longitude
                    })
                }).then(() => {
                    document.getElementById("estado").innerHTML = '<span class="ok">✓ Ubicación guardada</span>';
                });
            }, function() {
                alert("No se pudo obtener tu ubicación. Revisa los permisos del navegador.");
            });
        }
        </script>
    """, usuario=session["usuario"], ubicacion=ubicacion_guardada)

@tecnico_bp.route("/ubicacion", methods=["POST"])
def guardar_ubicacion():
    if session.get("rol") != "tecnico":
        return jsonify({"error": "no autorizado"}), 403
    datos = request.get_json()
    conn = sqlite3.connect(DB)
    conn.execute(
        "UPDATE usuarios SET latitud = ?, longitud = ? WHERE usuario = ?",
        (datos["lat"], datos["lng"], session["usuario"])
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@tecnico_bp.route("/oficio", methods=["POST"])
def guardar_oficio():
    if session.get("rol") != "tecnico":
        return redirect(url_for("login"))
    oficio = request.form["oficio"]
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE usuarios SET oficio = ? WHERE usuario = ?", (oficio, session["usuario"]))
    conn.commit()
    conn.close()
    return redirect(url_for("tecnico.panel"))