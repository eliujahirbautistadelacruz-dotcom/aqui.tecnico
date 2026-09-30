import requests

BASE_URL = "https://proyecto-3791b-default-rtdb.firebaseio.com"

def sanitizar(clave):
    """Convierte un nombre de usuario en una llave válida para Firebase."""
    for ch in ['.', '#', '$', '[', ']', '/', ' ']:
        clave = clave.replace(ch, '_')
    return clave.lower()

def fb_get(ruta):
    try:
        r = requests.get(f"{BASE_URL}/{ruta}.json", timeout=10)
        return r.json()
    except Exception:
        return None

def fb_set(ruta, datos):
    try:
        requests.put(f"{BASE_URL}/{ruta}.json", json=datos, timeout=10)
    except Exception:
        pass

def fb_update(ruta, datos):
    try:
        requests.patch(f"{BASE_URL}/{ruta}.json", json=datos, timeout=10)
    except Exception:
        pass

def fb_push(ruta, datos):
    try:
        r = requests.post(f"{BASE_URL}/{ruta}.json", json=datos, timeout=10)
        return r.json().get("name")
    except Exception:
        return None

def fb_delete(ruta):
    try:
        requests.delete(f"{BASE_URL}/{ruta}.json", timeout=10)
    except Exception:
        pass
