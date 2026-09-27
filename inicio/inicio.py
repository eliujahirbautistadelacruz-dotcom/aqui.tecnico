from flask import Blueprint, session, redirect, url_for, render_template_string

inicio_bp = Blueprint("inicio", __name__)

@inicio_bp.route("/")
@inicio_bp.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))
    rol = session.get("rol")
    if rol == "tecnico":
        return redirect(url_for("tecnico.panel"))
    elif rol == "usuario":
        return redirect(url_for("usuario.panel"))
    return redirect(url_for("escoge.escoge"))