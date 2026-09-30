from datetime import datetime
from flask import Blueprint, session, redirect, url_for, render_template_string, request, jsonify
from database import fb_get, fb_update, sanitizar

tecnico_bp = Blueprint("tecnico", __name__, url_prefix="/tecnico")

OFICIOS = [
    "plomero", "electricista", "aire_acondicionado", "gas",
    "cerrajero", "pintor", "albanil", "carpintero", "jardineria", "otro"
]

ESTILO = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }
body { font-family: -apple-system, 'Segoe UI', sans-serif; background: #f4f5ff; margin: 0; padding: 16px; }
.card { background: white; padding: 28px; border-radius: 16px; width: 100%; max-width: 480px;
        margin: 24px auto; box-shadow: 0 10px 40px rgba(0,0,0,0.08); }
.card h1 { color: #1a1a1a; font-size: 19px; margin: 0 0 6px; }
.rating { color: #f5a623; font-size: 15px; margin-bottom: 20px; }
label { font-size: 13px; color: #4a4a4a; font-weight: 600; display: block; margin-bottom: 6px; }
select, input, textarea, button { width: 100%; padding: 12px; border-radius: 8px; font-size: 15px;
        margin-bottom: 14px; font-family: inherit; }
select, input, textarea { border: 1px solid #d9d9d9; }
.btn-guardar { background: #333; color: white; border: none; cursor: pointer; font-weight: 600; }
.btn-ubicacion { background: #6b73ff; color: white; border: none; cursor: pointer; font-weight: 600; }
.estado { font-size: 13px; color: #666; text-align: center; margin-bottom: 14px; }
.ok { color: #2ecc71; font-weight: 600; }
.salir { text-align: center; font-size: 13px; padding-bottom: 8px; }
.salir a { color: #6b73ff; text-decoration: none; }
.seccion { margin-top: 24px; border-top: 1px solid #eee; padding-top: 16px; }
.seccion h3 { font-size: 15px; margin-bottom: 10px; }
.item { background: #f9f9ff; padding: 10px 12px; border-radius: 8px; margin-bottom: 8px; font-size: 13px; }
.item .top { display: flex; justify-content: space-between; color: #f5a623; font-weight: 600; }
.item .autor { color: #666; font-weight: 400; }
.solicitud { background: #fff8ee; border: 1px solid #f5d98c; padding: 12px; border-radius: 8px; margin-bottom: 10px; }
.solicitud .cliente { font-weight: 600; font-size: 13px; }
.solicitud .desc { font-size: 13px; color: #555; margin: 6px 0; }
.acciones-sol { display: flex; gap: 8px; }
.acciones-sol button { padding: 8px; font-size: 12px; margin-bottom: 0; }
.btn-aceptar { background: #2ecc71; color: white; border: none; }
.btn-rechazar { background: #e74c3c; color: white; border: none; }
</style>
"""

@tecnico_bp.route("/panel")
def panel():
    if session.get("rol") != "tecnico":
        return redirect(url_for("login"))
    usuario_actual = session["usuario"]
    clave = sanitizar(usuario_actual)
    datos = fb_get(f"usuarios/{clave}") or {}

    todas_calif = fb_get("calificaciones") or {}
    resenas = [v for v in todas_calif.values() if v.get("tecnico") == usuario_actual]
    resenas.sort(key=lambda r: r.get("fecha", ""), reverse=True)
    total_calif = len(resenas)
    promedio = round(sum(r["estrellas"] for r in resenas) / total_calif, 1) if total_calif else 0

    todas_sol = fb_get("solicitudes") or {}
    pendientes = [(k, v) for k, v in todas_sol.items()
                  if v.get("tecnico") == usuario_actual and v.get("estado") == "pendiente"]
    pendientes.sort(key=lambda kv: kv[1].get("fecha", ""), reverse=True)

    ubicacion_guardada = datos.get("latitud") is not None and datos.get("longitud") is not None

    opciones_html = "".join(
        f'<option value="{o}" {"selected" if o == datos.get("oficio") else ""}>{o.replace("_", " ").title()}</option>'
        for o in OFICIOS
    )

    sol_html = ""
    if pendientes:
        for sid, s in pendientes:
            sol_html += f"""
            <div class="solicitud">
                <div class="cliente">{s.get('cliente')}</div>
                <div class="desc">{s.get('descripcion', '')}</div>
                <div class="acciones-sol">
                    <form method="POST" action="/tecnico/solicitud/{sid}/responder" style="flex:1;">
                        <input type="hidden" name="estado" value="aceptada">
                        <button type="submit" class="btn-aceptar">Aceptar</button>
                    </form>
                    <form method="POST" action="/tecnico/solicitud/{sid}/responder" style="flex:1;">
                        <input type="hidden" name="estado" value="rechazada">
                        <button type="submit" class="btn-rechazar">Rechazar</button>
                    </form>
                </div>
            </div>"""
    else:
        sol_html = "<p style='color:#999; font-size:13px;'>No tienes solicitudes pendientes.</p>"

    resenas_html = ""
    if resenas:
        for r in resenas[:10]:
            resenas_html += f"""
            <div class="item">
                <div class="top"><span>{'⭐' * r['estrellas']}</span><span class="autor">{r.get('autor','')}</span></div>
                {f"<div>{r['comentario']}</div>" if r.get('comentario') else ''}
            </div>"""
    else:
        resenas_html = "<p style='color:#999; font-size:13px;'>Todavía no tienes reseñas.</p>"

    return render_template_string(ESTILO + """
        <div class="card">
            <h1>Panel de técnico — {{ usuario }}</h1>
            <div class="rating">
                {% if total > 0 %}⭐ {{ promedio }} ({{ total }} calificación{{ 'es' if total != 1 else '' }})
                {% else %}Aún no tienes calificaciones{% endif %}
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
                {% if ubicacion %}<span class="ok">✓ Ubicación guardada</span>
                {% else %}Aún no has compartido tu ubicación{% endif %}
            </div>
            <button class="btn-ubicacion" onclick="compartirUbicacion()">📍 Compartir mi ubicación</button>

            <div class="seccion">
                <h3>Solicitudes de servicio pendientes</h3>
                """ + sol_html + """
            </div>

            <div class="seccion">
                <h3>Tus últimas reseñas</h3>
                """ + resenas_html + """
            </div>

            <p class="salir"><a href="/logout">Cerrar sesión</a></p>
        </div>

        <script>
        function compartirUbicacion() {
            if (!navigator.geolocation) { alert("Tu navegador no soporta geolocalización"); return; }
            navigator.geolocation.getCurrentPosition(function(pos) {
                fetch("/tecnico/ubicacion", {
                    method: "POST", headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ lat: pos.coords.latitude, lng: pos.coords.longitude })
                }).then(() => {
                    document.getElementById("estado").innerHTML = '<span class="ok">✓ Ubicación guardada</span>';
                });
            }, function() { alert("No se pudo obtener tu ubicación. Revisa los permisos."); });
        }
        </script>
    """, usuario=usuario_actual, ubicacion=ubicacion_guardada,
         telefono=datos.get("telefono"), precio=datos.get("precio_desde"),
         descripcion=datos.get("descripcion"), total=total_calif, promedio=promedio)

@tecnico_bp.route("/perfil", methods=["POST"])
def guardar_perfil():
    if session.get("rol") != "tecnico":
        return redirect(url_for("login"))
    clave = sanitizar(session["usuario"])
    fb_update(f"usuarios/{clave}", {
        "oficio": request.form["oficio"],
        "telefono": request.form.get("telefono", ""),
        "precio_desde": request.form.get("precio_desde") or None,
        "descripcion": request.form.get("descripcion", "")
    })
    return redirect(url_for("tecnico.panel"))

@tecnico_bp.route("/ubicacion", methods=["POST"])
def guardar_ubicacion():
    if session.get("rol") != "tecnico":
        return jsonify({"error": "no autorizado"}), 403
    datos = request.get_json()
    clave = sanitizar(session["usuario"])
    fb_update(f"usuarios/{clave}", {"latitud": datos["lat"], "longitud": datos["lng"]})
    return jsonify({"ok": True})
