
from flask import Flask
from models import db, Categoria, Administrador, ParametroSistema
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = os.path.join(
    BASE_DIR,
    "static",
    "uploads"
)

secret_key = os.environ.get("SECRET_KEY")

if not secret_key:
    raise RuntimeError("SECRET_KEY no configurada")

app.config["SECRET_KEY"] = secret_key

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("COOKIE_SECURE", "false").lower() == "true"
)

database_url = os.environ.get("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL no está configurada")

# Configurar explícitamente el controlador psycopg2
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql+psycopg2://",
        1
    )
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

from routes import *


CATEGORIAS_POR_DEFECTO = [
    ("Playa", "bi-umbrella"),
    ("Montaña", "bi-tree"),
    ("Cultural", "bi-bank"),
    ("Aventura", "bi-bicycle"),
    ("Naturaleza", "bi-water"),
]


PARAMETROS_POR_DEFECTO = [
    (
        "comision_plataforma",
        "10",
        "Porcentaje que Zuqara Tours cobra a los operadores por cada reserva"
    ),
    (
        "correo_soporte",
        "soporte@zuqara.com",
        "Correo de contacto que se muestra a los usuarios"
    ),
    (
        "mensaje_bienvenida",
        "¡Descubre nuevos lugares y vive experiencias inolvidables!",
        "Frase que aparece en el Dashboard"
    ),
    (
        "cupos_minimos_alerta",
        "3",
        "Cuando a un tour le quedan menos cupos que este número, se resalta"
    ),
]


with app.app_context():

    db.create_all()

    if Categoria.query.count() == 0:

        for nombre, icono in CATEGORIAS_POR_DEFECTO:
            db.session.add(
                Categoria(
                    nombre=nombre,
                    icono=icono
                )
            )

        db.session.commit()

    if ParametroSistema.query.count() == 0:

        for clave, valor, descripcion in PARAMETROS_POR_DEFECTO:
            db.session.add(
                ParametroSistema(
                    clave=clave,
                    valor=valor,
                    descripcion=descripcion
                )
            )

        db.session.commit()


if __name__ == "__main__":
    app.run(debug=True)
