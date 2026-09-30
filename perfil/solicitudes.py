from datetime import datetime
from flask import Blueprint, session, redirect, url_for, render_template_string, request
from database import fb_get, fb_push, fb_update

solicitudes_bp = Blueprint("solicitudes", __name__)

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
.card { background: white; padding: 36px; border-radius: 16px; width: 100%; max-width: 400px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.card h2 { color: #1a1a1a; margin: 0 0 4px; font-size: 20px; }
.card p.sub { color: #666; font-size: 13px; margin-bottom: 20px; }
textarea { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #d9d9d9;
           font-size: 15px; font-family: inherit; margin-bottom: 16px; }
button { width: 100%; padding: 13px; background: #6b73ff; color: white; border: none;
         border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 15px; }
.volver { text-align: center; margin-top: 14px; font-size: 13px; }
.volver a { color: #6b73ff; text-decoration: none; }
</style>
"""

ESTILO_LISTA = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }
body { font-family: -apple-system, 'Segoe UI', sans-serif; background: #f4f5ff; margin: 0; padding: 16px; }
.panel { max-width: 520px; margin: 0 auto; }
h1 { font-size: 19px; }
.item { background: white; padding: 14px; border-radius: 10px; margin-bottom: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.item .top { display: flex; justify-content: space-between; align-items: center; }
.item .tecnico { font-weight: 600; }
.badge { font-size: 11px; padding: 4px 10px; border-radius: 12px; font-weight: 600; }
.badge.pendiente { background: #fff3cd; color: #856404; }
.badge.aceptada { background: #d4edda; color: #155724; }
.badge.rechazada { background: #f8d7da; color: #721c24; }
.desc { font-size: 13px; color: #555; margin-top: 6px; }
.volver { display: block; text-align: center; margin-top: 16px; color: #6b73ff; text-decoration: none; }
</style>
"""

@solicitudes_bp.route("/solicitar/<tecnico>", methods=["GET", "POST"])
def solicitar(tecnico):
    if "usuario" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        descripcion = request.form.get("descripcion", "")
        fb_push("solicitudes", {
            "cliente": session["usuario"],
            "tecnico": tecnico,
            "descripcion": descripcion,
            "estado": "pendiente",
            "fecha": datetime.utcnow().isoformat()
        })
        return redirect(url_for("solicitudes.mis_solicitudes"))
    return render_template_string(ESTILO + """
        <div class="card">
            <h2>Pedir servicio a {{ tecnico }}</h2>
            <p class="sub">Cuéntale qué necesitas. Él decide si acepta tu solicitud.</p>
            <form method="POST">
                <textarea name="descripcion" rows="4"
                    placeholder="Ej: se me tapó el drenaje de la cocina, es urgente" required></textarea>
                <button type="submit">Enviar solicitud</button>
            </form>
            <p class="volver"><a href="/usuario/panel">Volver</a></p>
        </div>
    """, tecnico=tecnico)

@solicitudes_bp.route("/usuario/mis-solicitudes")
def mis_solicitudes():
    if "usuario" not in session:
        return redirect(url_for("login"))
    todas = fb_get("solicitudes") or {}
    mias = [v for v in todas.values() if v.get("cliente") == session["usuario"]]
    mias.sort(key=lambda s: s.get("fecha", ""), reverse=True)

    items = ""
    if mias:
        for s in mias:
            estado = s.get("estado", "pendiente")
            contacto = ""
            if estado == "aceptada":
                datos_tec = fb_get(f"usuarios/{s['tecnico'].lower()}") or {}
                tel = (datos_tec.get("telefono") or "").replace(" ", "")
                if tel:
                    contacto = f'<a href="https://wa.me/{tel}" style="color:#25d366; font-weight:600; font-size:13px;">Contactar por WhatsApp →</a>'
            items += f"""
            <div class="item">
                <div class="top">
                    <span class="tecnico">{s.get('tecnico')}</span>
                    <span class="badge {estado}">{estado.title()}</span>
                </div>
                <div class="desc">{s.get('descripcion', '')}</div>
                {f'<div style="margin-top:8px;">{contacto}</div>' if contacto else ''}
            </div>"""
    else:
        items = "<p style='color:#999;'>Aún no has pedido ningún servicio.</p>"

    return render_template_string(ESTILO_LISTA + """
        <div class="panel">
            <h1>Mis solicitudes</h1>
            """ + items + """
            <a class="volver" href="/usuario/panel">← Volver</a>
        </div>
    """)

@solicitudes_bp.route("/tecnico/solicitud/<sid>/responder", methods=["POST"])
def responder(sid):
    if session.get("rol") != "tecnico":
        return redirect(url_for("login"))
    estado = request.form.get("estado")
    fb_update(f"solicitudes/{sid}", {"estado": estado})
    return redirect(url_for("tecnico.panel"))
