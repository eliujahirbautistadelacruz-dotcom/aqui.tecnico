import sqlite3
import os
from flask import Blueprint, session, redirect, url_for, render_template_string, request, jsonify

tecnico_bp = Blueprint("tecnico", __name__, url_prefix="/tecnico")
DB = os.environ.get("DB_PATH", "usuarios.db")

OFICIOS = [
    "plomero", "electricista", "aire_acondicionado", "gas",
    "cerrajero", "pintor", "albanil", "carpintero", "jardineria", "otro"
]

ESTILO = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }
body { font-family: -apple-system, 'Segoe UI', sans-serif; background: #f4f5ff; margin: 0; padding: 16px; }
.card { background: white; padding: 28px; border-radius: 16px; width: 100%; max-width: 460px;
        margin: 24px auto; box-shadow: 0 10px 40px rgba(0,0,0,0.08); }
.card h1 { color: #1a1a1a; font-size: 19px; margin: 0 0 6px; }
.rating { color: #f5a623; font-size: 15px; margin-bottom: 20px; }
label { font-size: 13px; color: #4a4a4a; font-weight: 600; display: block; margin-bottom: 6px; }
select, input, textarea, button { width: 100%; padding: 12px; border-radius: 8px; font-size: 15px;
        margin-bottom: 14px; font-family: inherit; }
select, input, textarea { border: 1px solid #d9d9d9; }
.btn-guardar { background: #333; color: white; border: none; cursor: pointer; font-weight: 600; }
.btn-ubicacion { background: #6b73ff; color: white; border: none; cursor: pointer; font-weight: 600; }
.btn-ubicacion:hover { background: #5a61e0; }
.estado { font-size: 13px; color: #666; text-align: center; margin-bottom: 14px; }
.ok { color: #2ecc71; font-weight: 600; }
.salir { text-align: center; font-size: 13px; }
.salir a { color: #6b73ff; text-decoration: none; }
.resenas { margin-top: 24px; border-top: 1px solid #eee; padding-top: 16px; }
.resenas h3 { font-size: 15px; margin-bottom: 10px; }
.resena-item { background: #f9f9ff; padding: 10px 12px; border-radius: 8px; margin-bottom: 8px; font-size: 13px; }
.resena-item .top { display: flex; justify-content: space-between; color: #f5a623; font-weight: 600; }
.resena-item .autor { color: #666; font-weight: 400; }
</style>
"""

@tecnico_bp.route("/panel")
def panel():
    if session.get("rol") != "tecnico":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT oficio, telefono, precio_desde, descripcion, latitud, longitud FROM usuarios WHERE usuario = ?",
        (session["usuario"],)
    ).fetchone()
    calif = conn.execute(
        "SELECT COUNT(*), AVG(estrellas) FROM calificaciones WHERE tecnico = ?",
        (session["usuario"],)
    ).fetchone()
    resenas = conn.execute(
        "SELECT autor, estrellas, comentario, fecha FROM calificaciones WHERE tecnico = ? ORDER BY fecha DESC LIMIT 10",
        (session["usuario"],)
    ).fetchall()
    conn.close()

    oficio_actual, telefono, precio, descripcion, lat, lng = row if row else (None, None, None, None, None, None)
    total_calif, promedio = calif
    promedio = round(promedio, 1) if promedio else 0
    ubicacion_guardada = lat is not None and lng is not None

    opciones_html = "".join(
        f'<option value="{o}" {"selected" if o == oficio_actual else ""}>{o.replace("_", " ").title()}</option>'
        for o in OFICIOS
    )

    resenas_html = ""
    if resenas:
        for autor, estrellas, comentario, fecha in resenas:
            estrellitas = "⭐" * estrellas
            resenas_html += f"""
            <div class="resena-item">
                <div class="top"><span>{estrellitas}</span><span class="autor">{autor}</span></div>
                {f'<div>{comentario}</div>' if comentario else ''}
            </div>"""
    else:
        resenas_html = "<p style='color:#999; font-size:13px;'>Todavía no tienes reseñas.</p>"

    return render_template_string(ESTILO + """
        <div class="card">
            <h1>Panel de técnico — {{ usuario }}</h1>
            <div class="rating">
                {% if total > 0 %}
                    ⭐ {{ promedio }} ({{ total }} calificación{{ 'es' if total != 1 else '' }})
                {% else %}
                    Aún no tienes calificaciones
                {% endif %}
            </div>

            <form method="POST" action="/tecnico/perfil">
                <label>Tu oficio</label>
                <select name="oficio">""" + opciones_html + """</select>
                <label>Teléfono / WhatsApp</label>
                <input name="telefono" value="{{ telefono or '' }}" placeholder="523311234567">
                <label>Precio desde ($)</label>
                <input name="precio_desde" type="number" step="0.01" value="{{ precio or '' }}" placeholder="300">
                <label>Descripción de tu servicio</label>
                <textarea name="descripcion" rows="3" placeholder="Cuéntale al cliente qué haces...">{{ descripcion or '' }}</textarea>
                <button type="submit" class="btn-guardar">Guardar datos</button>
            </form>

            <div class="estado" id="estado">
                {% if ubicacion %}
                    <span class="ok">✓ Ubicación guardada</span>
                {% else %}
                    Aún no has compartido tu ubicación
                {% endif %}
            </div>
            <button class="btn-ubicacion" onclick="compartirUbicacion()">📍 Compartir mi ubicación</button>

            <div class="resenas">
                <h3>Tus últimas reseñas</h3>
                """ + resenas_html + """
            </div>

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
    """, usuario=session["usuario"], ubicacion=ubicacion_guardada,
         telefono=telefono, precio=precio, descripcion=descripcion,
         total=total_calif, promedio=promedio)

@tecnico_bp.route("/perfil", methods=["POST"])
def guardar_perfil():
    if session.get("rol") != "tecnico":
        return redirect(url_for("login"))
    oficio = request.form["oficio"]
    telefono = request.form.get("telefono", "")
    precio = request.form.get("precio_desde") or None
    descripcion = request.form.get("descripcion", "")
    conn = sqlite3.connect(DB)
    conn.execute(
        "UPDATE usuarios SET oficio = ?, telefono = ?, precio_desde = ?, descripcion = ? WHERE usuario = ?",
        (oficio, telefono, precio, descripcion, session["usuario"])
    )
    conn.commit()
    conn.close()
    return redirect(url_for("tecnico.panel"))

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
