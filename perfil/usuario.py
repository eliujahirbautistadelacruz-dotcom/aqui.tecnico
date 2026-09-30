import sqlite3
import os
from math import radians, sin, cos, sqrt, atan2
from flask import Blueprint, session, redirect, url_for, render_template_string, request, jsonify

usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuario")
DB = os.environ.get("DB_PATH", "usuarios.db")

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
#mapa { height: 48vh; width: 100%; min-height: 260px; }
.filtros { display: flex; gap: 8px; padding: 12px 16px; background: white; flex-wrap: wrap; }
.filtros select, .filtros button {
    padding: 10px 12px; border-radius: 8px; border: 1px solid #d9d9d9; font-size: 14px; font-family: inherit;
}
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
.acciones a, .acciones button {
    flex: 1; min-width: 100px; text-align: center; padding: 9px; border-radius: 6px; font-size: 12px;
    text-decoration: none; border: none; cursor: pointer; font-weight: 600;
}
.btn-whats { background: #25d366; color: white; }
.btn-calificar { background: #6b73ff; color: white; }
.btn-resenas { background: #eee; color: #333; }
.salir { text-align: center; font-size: 13px; margin-top: 16px; padding-bottom: 20px; }
.salir a { color: #6b73ff; text-decoration: none; }
@media (max-width: 480px) {
    .filtros { flex-direction: column; }
    #mapa { height: 40vh; }
}
</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
"""

@usuario_bp.route("/panel")
def panel():
    if session.get("rol") != "usuario":
        return redirect(url_for("login"))

    opciones_oficio = "".join(
        f'<option value="{o}">{o.replace("_", " ").title()}</option>' for o in OFICIOS
    )

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
            <p class="salir"><a href="/logout">Cerrar sesión</a></p>
        </div>

        <script>
        var mapa = L.map('mapa').setView([23.6, -102.5], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(mapa);
        var marcadores = [];
        var datosActuales = [];
        var miLat, miLng;

        function pintar(data) {
            marcadores.forEach(m => mapa.removeLayer(m));
            marcadores = [];
            var lista = document.getElementById("lista");
            if (data.length === 0) {
                lista.innerHTML = "<p>No hay técnicos que coincidan con tu búsqueda.</p>";
                return;
            }
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
                            ${tel ? '<a class="btn-whats" href="https://wa.me/' + tel + '" target="_blank">WhatsApp</a>' : ''}
                            <a class="btn-calificar" href="/calificar/${t.usuario}">Calificar</a>
                            <a class="btn-resenas" href="/usuario/resenas/${t.usuario}">Reseñas</a>
                        </div>
                    </div>`;
            });
        }

        function cargar() {
            fetch("/usuario/cercanos?lat=" + miLat + "&lng=" + miLng)
                .then(r => r.json())
                .then(data => { datosActuales = data; filtrar(); });
        }

        function filtrar() {
            var oficio = document.getElementById("filtroOficio").value;
            var filtrado = oficio ? datosActuales.filter(t => t.oficio === oficio) : datosActuales;
            pintar(filtrado);
        }

        function ubicarme() {
            if (!navigator.geolocation) return;
            navigator.geolocation.getCurrentPosition(function(pos) {
                miLat = pos.coords.latitude; miLng = pos.coords.longitude;
                mapa.setView([miLat, miLng], 13);
                L.marker([miLat, miLng]).addTo(mapa).bindPopup("Tú estás aquí").openPopup();
                cargar();
            }, function() {
                document.getElementById("lista").innerHTML = "No se pudo obtener tu ubicación.";
            });
        }

        ubicarme();
        </script>
    """)

@usuario_bp.route("/cercanos")
def cercanos():
    lat = float(request.args.get("lat"))
    lng = float(request.args.get("lng"))
    conn = sqlite3.connect(DB)
    filas = conn.execute(
        "SELECT usuario, oficio, telefono, precio_desde, descripcion, latitud, longitud FROM usuarios "
        "WHERE rol = 'tecnico' AND latitud IS NOT NULL AND longitud IS NOT NULL"
    ).fetchall()

    resultado = []
    for usuario, oficio, telefono, precio, descripcion, tlat, tlng in filas:
        calif = conn.execute(
            "SELECT COUNT(*), AVG(estrellas) FROM calificaciones WHERE tecnico = ?", (usuario,)
        ).fetchone()
        total, promedio = calif
        resultado.append({
            "usuario": usuario, "oficio": oficio, "telefono": telefono,
            "precio_desde": precio, "descripcion": descripcion,
            "lat": tlat, "lng": tlng,
            "distancia": distancia_km(lat, lng, tlat, tlng),
            "total": total, "promedio": round(promedio, 1) if promedio else 0
        })
    conn.close()
    resultado.sort(key=lambda t: t["distancia"])
    return jsonify(resultado)

@usuario_bp.route("/resenas/<tecnico>")
def ver_resenas(tecnico):
    if "usuario" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB)
    resenas = conn.execute(
        "SELECT autor, estrellas, comentario, fecha FROM calificaciones WHERE tecnico = ? ORDER BY fecha DESC",
        (tecnico,)
    ).fetchall()
    conn.close()

    items = ""
    if resenas:
        for autor, estrellas, comentario, fecha in resenas:
            items += f"""
            <div class="tecnico-item">
                <div class="fila"><span>{'⭐' * estrellas}</span><span style="color:#666;font-size:12px;">{autor}</span></div>
                {f'<div class="desc">{comentario}</div>' if comentario else ''}
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
