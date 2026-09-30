import sqlite3
from math import radians, sin, cos, sqrt, atan2
from flask import Blueprint, session, redirect, url_for, render_template_string, request, jsonify

usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuario")
DB = "usuarios.db"

def distancia_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return round(R * 2 * atan2(sqrt(a), sqrt(1 - a)), 1)

ESTILO = """
<style>
* { box-sizing: border-box; }
body { font-family: -apple-system, 'Segoe UI', sans-serif; margin: 0; background: #f4f5ff; }
#mapa { height: 55vh; width: 100%; }
.panel { padding: 20px; max-width: 520px; margin: 0 auto; }
h1 { font-size: 20px; color: #1a1a1a; }
.tecnico-item { background: white; padding: 14px; border-radius: 10px; margin-bottom: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.tecnico-item .fila { display: flex; justify-content: space-between; align-items: center; }
.tecnico-item .nombre { font-weight: 600; }
.tecnico-item .oficio { font-size: 12px; color: #666; }
.tecnico-item .rating { font-size: 12px; color: #f5a623; margin-top: 2px; }
.tecnico-item .dist { color: #6b73ff; font-weight: 600; font-size: 13px; }
.tecnico-item .desc { font-size: 12px; color: #555; margin-top: 6px; }
.acciones { display: flex; gap: 8px; margin-top: 10px; }
.acciones a, .acciones button {
    flex: 1; text-align: center; padding: 8px; border-radius: 6px; font-size: 12px;
    text-decoration: none; border: none; cursor: pointer; font-weight: 600;
}
.btn-whats { background: #25d366; color: white; }
.btn-calificar { background: #6b73ff; color: white; }
.salir { text-align: center; font-size: 13px; margin-top: 16px; }
.salir a { color: #6b73ff; text-decoration: none; }
</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
"""

@usuario_bp.route("/panel")
def panel():
    if session.get("rol") != "usuario":
        return redirect(url_for("login"))
    return render_template_string(ESTILO + """
        <div id="mapa"></div>
        <div class="panel">
            <h1>Técnicos cerca de ti</h1>
            <div id="lista">Obteniendo tu ubicación...</div>
            <p class="salir"><a href="/logout">Cerrar sesión</a></p>
        </div>

        <script>
        var mapa = L.map('mapa').setView([23.6, -102.5], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(mapa);

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(pos) {
                var lat = pos.coords.latitude, lng = pos.coords.longitude;
                mapa.setView([lat, lng], 13);
                L.marker([lat, lng]).addTo(mapa).bindPopup("Tú estás aquí").openPopup();

                fetch("/usuario/cercanos?lat=" + lat + "&lng=" + lng)
                    .then(r => r.json())
                    .then(data => {
                        var lista = document.getElementById("lista");
                        if (data.length === 0) {
                            lista.innerHTML = "<p>No hay técnicos registrados cerca todavía.</p>";
                            return;
                        }
                        lista.innerHTML = "";
                        data.forEach(t => {
                            L.marker([t.lat, t.lng]).addTo(mapa).bindPopup(t.usuario + " — " + t.oficio);
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
                                    </div>
                                </div>`;
                        });
                    });
            }, function() {
                document.getElementById("lista").innerHTML = "No se pudo obtener tu ubicación.";
            });
        }
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
