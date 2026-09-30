from math import radians, sin, cos, sqrt, atan2
from flask import Blueprint, session, redirect, url_for, render_template_string, request, jsonify
from database import fb_get

usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuario")

OFICIOS = [
    "plomero", "electricista", "aire_acondicionado", "gas",
    "cerrajero", "pintor", "albanil", "carpintero", "jardineria", "otro"
]

def distancia_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return round(R * 2 * atan2(sqrt(a), sqrt(1 - a)), 1)

ESTILO = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }
body { font-family: -apple-system, 'Segoe UI', sans-serif; margin: 0; background: #f4f5ff; }
#mapa { height: 46vh; width: 100%; min-height: 240px; }
.filtros { display: flex; gap: 8px; padding: 12px 16px; background: white; flex-wrap: wrap; }
.filtros select, .filtros button { padding: 10px 12px; border-radius: 8px; border: 1px solid #d9d9d9;
    font-size: 14px; font-family: inherit; }
.filtros button { background: #6b73ff; color: white; border: none; cursor: pointer; font-weight: 600; }
.panel { padding: 16px; max-width: 560px; margin: 0 auto; }
h1 { font-size: 19px; color: #1a1a1a; margin: 4px 0 12px; }
.tecnico-item { background: white; padding: 14px; border-radius: 10px; margin-bottom: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.tecnico-item .fila { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px; }
.tecnico-item .nombre { font-weight: 600; }
.tecnico-item .oficio { font-size: 12px; color: #666; }
.tecnico-item .rating { font-size: 12px; color: #f5a623; margin-top: 2px; }
.tecnico-item .dist { color: #6b73ff; font-weight: 600; font-size: 13px; }
.tecnico-item .desc { font-size: 12px; color: #555; margin-top: 6px; }
.acciones { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.acciones a, .acciones button { flex: 1; min-width: 100px; text-align: center; padding: 9px;
    border-radius: 6px; font-size: 12px; text-decoration: none; border: none; cursor: pointer; font-weight: 600; }
.btn-pedir { background: #6b73ff; color: white; }
.btn-whats { background: #25d366; color: white; }
.btn-resenas { background: #eee; color: #333; }
.top-links { text-align: center; font-size: 13px; margin-top: 16px; padding-bottom: 20px; }
.top-links a { color: #6b73ff; text-decoration: none; margin: 0 8px; }
@media (max-width: 480px) { .filtros { flex-direction: column; } #mapa { height: 36vh; } }
</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
"""

@usuario_bp.route("/panel")
def panel():
    if session.get("rol") != "usuario":
        return redirect(url_for("login"))
    opciones_oficio = "".join(f'<option value="{o}">{o.replace("_"," ").title()}</option>' for o in OFICIOS)
    return render_template_string(ESTILO + """
        <div class="filtros">
            <select id="filtroOficio" onchange="filtrar()">
                <option value="">Todos los oficios</option>
                """ + opciones_oficio + """
            </select>
            <button onclick="ubicarme()">📍 Ubicarme de nuevo</button>
        </div>
        <div id="mapa"></div>
        <div class="panel">
            <h1>Técnicos cerca de ti</h1>
            <div id="lista">Obteniendo tu ubicación...</div>
            <p class="top-links"><a href="/usuario/mis-solicitudes">Mis solicitudes</a> · <a href="/logout">Cerrar sesión</a></p>
        </div>

        <script>
        var mapa = L.map('mapa').setView([23.6, -102.5], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(mapa);
        var marcadores = [], datosActuales = [], miLat, miLng;

        function pintar(data) {
            marcadores.forEach(m => mapa.removeLayer(m));
            marcadores = [];
            var lista = document.getElementById("lista");
            if (data.length === 0) { lista.innerHTML = "<p>No hay técnicos que coincidan.</p>"; return; }
            lista.innerHTML = "";
            data.forEach(t => {
                var m = L.marker([t.lat, t.lng]).addTo(mapa).bindPopup(t.usuario + " — " + t.oficio);
                marcadores.push(m);
                var rating = t.total > 0 ? ("⭐ " + t.promedio + " (" + t.total + ")") : "Sin calificaciones";
                var tel = t.telefono ? t.telefono.replace(/[^0-9]/g, "") : "";
                lista.innerHTML += `
                    <div class="tecnico-item">
                        <div class="fila">
                            <div>
                                <div class="nombre">${t.usuario}</div>
                                <div class="oficio">${t.oficio || 'Sin oficio definido'}</div>
                                <div class="rating">${rating}</div>
                            </div>
                            <div class="dist">${t.distancia} km</div>
                        </div>
                        ${t.descripcion ? '<div class="desc">' + t.descripcion + '</div>' : ''}
                        ${t.precio_desde ? '<div class="desc">Desde $' + t.precio_desde + '</div>' : ''}
                        <div class="acciones">
                            <a class="btn-pedir" href="/solicitar/${t.usuario}">Pedir servicio</a>
                            ${tel ? '<a class="btn-whats" href="https://wa.me/' + tel + '" target="_blank">WhatsApp</a>' : ''}
                            <a class="btn-resenas" href="/usuario/resenas/${t.usuario}">Reseñas</a>
                        </div>
                    </div>`;
            });
        }
        function cargar() {
            fetch("/usuario/cercanos?lat=" + miLat + "&lng=" + miLng)
                .then(r => r.json()).then(data => { datosActuales = data; filtrar(); });
        }
        function filtrar() {
            var oficio = document.getElementById("filtroOficio").value;
            pintar(oficio ? datosActuales.filter(t => t.oficio === oficio) : datosActuales);
        }
        function ubicarme() {
            if (!navigator.geolocation) return;
            navigator.geolocation.getCurrentPosition(function(pos) {
                miLat = pos.coords.latitude; miLng = pos.coords.longitude;
                mapa.setView([miLat, miLng], 13);
                L.marker([miLat, miLng]).addTo(mapa).bindPopup("Tú estás aquí").openPopup();
                cargar();
            }, function() { document.getElementById("lista").innerHTML = "No se pudo obtener tu ubicación."; });
        }
        ubicarme();
        </script>
    """)

@usuario_bp.route("/cercanos")
def cercanos():
    lat = float(request.args.get("lat"))
    lng = float(request.args.get("lng"))
    todos = fb_get("usuarios") or {}
    todas_calif = fb_get("calificaciones") or {}

    resultado = []
    for clave, u in todos.items():
        if u.get("rol") != "tecnico" or u.get("latitud") is None or u.get("longitud") is None:
            continue
        nombre = u.get("usuario", clave)
        calif_de_el = [c for c in todas_calif.values() if c.get("tecnico") == nombre]
        total = len(calif_de_el)
        promedio = round(sum(c["estrellas"] for c in calif_de_el) / total, 1) if total else 0
        resultado.append({
            "usuario": nombre, "oficio": u.get("oficio"), "telefono": u.get("telefono"),
            "precio_desde": u.get("precio_desde"), "descripcion": u.get("descripcion"),
            "lat": u["latitud"], "lng": u["longitud"],
            "distancia": distancia_km(lat, lng, u["latitud"], u["longitud"]),
            "total": total, "promedio": promedio
        })
    resultado.sort(key=lambda t: t["distancia"])
    return jsonify(resultado)

@usuario_bp.route("/resenas/<tecnico>")
def ver_resenas(tecnico):
    if "usuario" not in session:
        return redirect(url_for("login"))
    todas = fb_get("calificaciones") or {}
    resenas = [v for v in todas.values() if v.get("tecnico") == tecnico]
    resenas.sort(key=lambda r: r.get("fecha", ""), reverse=True)

    items = ""
    if resenas:
        for r in resenas:
            items += f"""
            <div class="tecnico-item">
                <div class="fila"><span>{'⭐' * r['estrellas']}</span><span style="color:#666;font-size:12px;">{r.get('autor','')}</span></div>
                {f"<div class='desc'>{r['comentario']}</div>" if r.get('comentario') else ''}
            </div>"""
    else:
        items = "<p style='color:#999;'>Este técnico aún no tiene reseñas.</p>"

    return render_template_string("""
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, 'Segoe UI', sans-serif; background: #f4f5ff; margin: 0; padding: 16px; }
    .panel { max-width: 500px; margin: 0 auto; }
    h1 { font-size: 19px; }
    .tecnico-item { background: white; padding: 14px; border-radius: 10px; margin-bottom: 10px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    .fila { display: flex; justify-content: space-between; color: #f5a623; font-weight: 600; }
    .desc { font-size: 13px; color: #555; margin-top: 6px; }
    .volver { display: block; text-align: center; margin-top: 16px; color: #6b73ff; text-decoration: none; }
    </style>
    <div class="panel">
        <h1>Reseñas de {{ tecnico }}</h1>
        """ + items + """
        <a class="volver" href="/usuario/panel">← Volver</a>
    </div>
    """, tecnico=tecnico)
