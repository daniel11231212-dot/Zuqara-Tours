
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    make_response
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from datetime import datetime

from decimal import Decimal

from functools import wraps

from sqlalchemy.dialects.postgresql import UUID

from app import app

from models import (
    db,
    Usuario,
    Empresa,
    Tour,
    Reserva,
    Favorito,
    Comentario,
    Conversacion,
    Mensaje,
    Categoria,
    ItinerarioViaje,
    ItinerarioViajeTour,
    PerfilViajero,
    Administrador,
    Pago,
    IntentoPagoSimulado,
    TransporteReserva,
    TourImagen,
    ItinerarioTourDia,
    Notificacion,
    ParametroSistema,
    PasajeroReserva,
    Guardado,
    SolicitudGuia,
    Guia,
    AsignacionGuia,
    CalificacionTour
)

import os
import uuid

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError



from dotenv import load_dotenv

load_dotenv()


from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "No se encontró GEMINI_API_KEY. "
        "Verifica que tengas configurado el archivo .env."
    )

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=30000
    )
)

def _borrar_relacionados_de_tour(tour):

    TransporteReserva.query.filter_by(
        tour_id=tour.id_tour
    ).delete(synchronize_session=False)

    Favorito.query.filter_by(
        tour_id=tour.id_tour
    ).delete(
        synchronize_session=False
    )

    Guardado.query.filter_by(
        tour_id=tour.id_tour
    ).delete(
        synchronize_session=False
    )

    ItinerarioViajeTour.query.filter_by(
        tour_id=tour.id_tour
    ).delete(
        synchronize_session=False
    )

    TourImagen.query.filter_by(
        tour_id=tour.id_tour
    ).delete(
        synchronize_session=False
    )

    ItinerarioTourDia.query.filter_by(
        tour_id=tour.id_tour
    ).delete(
        synchronize_session=False
    )

    Notificacion.query.filter_by(
        tour_id=tour.id_tour
    ).delete(
        synchronize_session=False
    )

    conversaciones = Conversacion.query.filter_by(
        tour_id=tour.id_tour
    ).all()

    for conv in conversaciones:

        Mensaje.query.filter_by(
            conversacion_id=conv.id
        ).delete(
            synchronize_session=False
        )

        db.session.delete(conv)

    Comentario.query.filter_by(
        tour_id=tour.id_tour
    ).delete(
        synchronize_session=False
    )

    reservas_del_tour = Reserva.query.filter_by(
        id_tour=tour.id_tour
    ).all()

    for reserva in reservas_del_tour:

        Pago.query.filter_by(
            reserva_id=reserva.id_reserva
        ).delete(
            synchronize_session=False
        )

        PasajeroReserva.query.filter_by(
            reserva_id=reserva.id_reserva
        ).delete(
            synchronize_session=False
        )

        db.session.delete(reserva)
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
    http_options=types.HttpOptions(
        timeout=30000
    )
)
def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        admin_id = session.get("admin_id")

        if not admin_id:
            return redirect(
                url_for("admin_login")
            )

        admin = db.session.get(
            Administrador,
            admin_id
        )

        if not admin:
            session.clear()
            flash(
                "La sesión administrativa ya no es válida.",
                "danger"
            )
            return redirect(
                url_for("admin_login")
            )

        response = make_response(
            view(*args, **kwargs)
        )

        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response

    return wrapped_view

def _guardar_imagen(archivo):

    if not archivo or archivo.filename == "":
        return None

    nombre_imagen = secure_filename(
        archivo.filename
    )

    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    ruta = os.path.join(
        app.config["UPLOAD_FOLDER"],
        nombre_imagen
    )

    archivo.save(ruta)

    return "uploads/" + nombre_imagen
def _borrar_relacionados_de_usuario(usuario):

    tours = Tour.query.filter_by(
        id_operador=usuario.id_usuario
    ).all()

    for tour in tours:

        _borrar_relacionados_de_tour(tour)

        db.session.delete(tour)

    Favorito.query.filter_by(
        usuario_id=usuario.id_usuario
    ).delete(
        synchronize_session=False
    )

    Comentario.query.filter_by(
        usuario_id=usuario.id_usuario
    ).delete(
        synchronize_session=False
    )

    conversaciones = Conversacion.query.filter_by(
        usuario_id=usuario.id_usuario
    ).all()

    for conv in conversaciones:

        Mensaje.query.filter_by(
            conversacion_id=conv.id
        ).delete(
            synchronize_session=False
        )

        db.session.delete(conv)

    itinerarios = ItinerarioViaje.query.filter_by(
        usuario_id=usuario.id_usuario
    ).all()

    for itinerario in itinerarios:

        ItinerarioViajeTour.query.filter_by(
            itinerario_id=itinerario.id
        ).delete(
            synchronize_session=False
        )

        db.session.delete(itinerario)

    PerfilViajero.query.filter_by(
        usuario_id=usuario.id_usuario
    ).delete(
        synchronize_session=False
    )

    reservas_del_usuario = Reserva.query.filter_by(
        id_viajero=usuario.id_usuario
    ).all()

    for reserva in reservas_del_usuario:

        Pago.query.filter_by(
            reserva_id=reserva.id_reserva
        ).delete(
            synchronize_session=False
        )

        PasajeroReserva.query.filter_by(
            reserva_id=reserva.id_reserva
        ).delete(
            synchronize_session=False
        )

        db.session.delete(reserva)


def _borrar_relacionados_de_empresa(empresa):

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if usuario_operador:

        tours = Tour.query.filter_by(
            id_operador=usuario_operador.id_usuario
        ).all()

        for tour in tours:

            _borrar_relacionados_de_tour(tour)

            db.session.delete(tour)

    conversaciones = Conversacion.query.filter_by(
        empresa_id=empresa.id
    ).all()

    for conv in conversaciones:

        Mensaje.query.filter_by(
            conversacion_id=conv.id
        ).delete(
            synchronize_session=False
        )

        db.session.delete(conv)

    Notificacion.query.filter_by(
        empresa_id=empresa.id
    ).delete(
        synchronize_session=False
    )


def _calificacion_tour(tour):

    calificaciones = [
        c.calificacion
        for c in tour.comentarios
        if c.calificacion is not None
    ]

    if not calificaciones:
        return None, 0

    promedio = round(
        sum(calificaciones) / len(calificaciones),
        1
    )

    return promedio, len(calificaciones)


def _adjuntar_calificaciones(lista_tours):

    for tour in lista_tours:
        promedio, total = _calificacion_tour(tour)

        tour.promedio_calificacion = promedio
        tour.total_calificaciones = total

    return lista_tours


@app.context_processor
def inject_notificaciones_sin_leer():

    if "empresa_id" in session:

        return dict(
            notificaciones_sin_leer=Notificacion.query.filter_by(
                empresa_id=session["empresa_id"],
                leida=False
            ).count()
        )

    return dict(notificaciones_sin_leer=0)


@app.after_request
def no_guardar_en_cache(response):

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )

    response.headers["Pragma"] = "no-cache"

    return response


@app.route("/")
def index():
    return render_template("iniciar_sesion.html")


@app.route("/principal")
def principal():

    total_tours = Tour.query.count()
    total_empresas = Empresa.query.count()

    tours = _adjuntar_calificaciones(
        Tour.query.limit(6).all()
    )

    usuario_actual = None
    mis_calificaciones = []
    tiene_perfil_viajero = True

    if "usuario_id" in session:

        usuario_actual = db.session.get(
            Usuario,
            session["usuario_id"]
        )

        mis_calificaciones = Comentario.query.filter_by(
            usuario_id=session["usuario_id"]
        ).order_by(
            Comentario.fecha.desc()
        ).limit(5).all()

        tiene_perfil_viajero = (
            PerfilViajero.query.filter_by(
                usuario_id=session["usuario_id"]
            ).first()
            is not None
        )

    return render_template(
        "principal.html",
        total_tours=total_tours,
        total_empresas=total_empresas,
        tours=tours,
        usuario_actual=usuario_actual,
        mis_calificaciones=mis_calificaciones,
        tiene_perfil_viajero=tiene_perfil_viajero
    )


@app.route("/login-usuario")
def login_usuario():
    return render_template("login_usuario.html")


@app.route("/login-usuario", methods=["POST"])
def login_usuario_post():

    correo = request.form["correo"]
    password = request.form["password"]

    usuario = Usuario.query.filter_by(
        correo=correo
    ).first()

    if usuario and check_password_hash(
        usuario.contrasenia_hash,
        password
    ):

        if usuario.rol == "guia":

            if usuario.estado == "pendiente":
                flash(
                    "Tu cuenta de guía está pendiente de aprobación por la empresa.",
                    "warning"
                )
                return redirect(
                    url_for("login_usuario")
                )

            if usuario.estado != "activo":
                flash(
                    "Tu cuenta de guía no está activa.",
                    "danger"
                )
                return redirect(
                    url_for("login_usuario")
                )

        session["usuario_id"] = str(
            usuario.id_usuario
        )

        session["usuario_nombre"] = (
            usuario.nombre_completo
        )

        if usuario.rol == "guia":
            return redirect(
                url_for("dashboard_guia")
            )

        return redirect(
            url_for("principal")
        )

    flash(
        "Correo o contraseña incorrectos",
        "danger"
    )

    return redirect(
        url_for("login_usuario")
    )


@app.route("/login_empresa")
def login_empresa():
    return render_template("login_empresa.html")


@app.route("/registro")
def registro():
    return render_template("registro.html")


@app.route("/registro_empresa")
def registro_empresa():
    return render_template("registro_empresa.html")


@app.route("/registro_usuario")
def registro_usuario():
    return render_template("registro_usuario.html")


@app.route("/registro_usuario", methods=["POST"])
def registro_usuario_post():

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    password = request.form["password"]
    confirmar = request.form["confirmar_password"]

    if password != confirmar:
        flash("Las contraseñas no coinciden")
        return redirect(
            url_for("registro_usuario")
        )

    usuario = Usuario.query.filter_by(
        correo=correo
    ).first()

    if usuario:
        flash("Este correo ya está registrado")
        return redirect(
            url_for("registro_usuario")
        )

    nuevo = Usuario(
        nombre_completo=nombre,
        correo=correo,
        contrasenia_hash=generate_password_hash(password),
        rol="viajero",
        estado="activo"
    )

    db.session.add(nuevo)
    db.session.commit()

    flash("Usuario registrado correctamente")

    return redirect(
        url_for("login_usuario")
    )
@app.route("/registro_guia")
def registro_guia():
    empresas = Empresa.query.filter_by(
        aprobado=True
    ).order_by(
        Empresa.nombre
    ).all()

    return render_template(
        "registro_guia.html",
        empresas=empresas
    )
@app.route("/registro_guia", methods=["POST"])
def registro_guia_post():

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    password = request.form["password"]
    confirmar = request.form["confirmar_password"]
    telefono = request.form["telefono"]
    empresa_id = request.form["empresa_id"]
    experiencia = request.form["experiencia"]
    especialidad = request.form["especialidad"]
    ciudad_base = request.form["ciudad_base"]
    descripcion = request.form["descripcion"]

    if password != confirmar:
        flash("Las contraseñas no coinciden", "danger")
        return redirect(url_for("registro_guia"))

    usuario_existente = Usuario.query.filter_by(
        correo=correo
    ).first()

    if usuario_existente:
        flash("Este correo ya está registrado", "danger")
        return redirect(url_for("registro_guia"))

    empresa = Empresa.query.filter_by(
        id=empresa_id,
        aprobado=True
    ).first()

    if not empresa:
        flash("La empresa seleccionada no está disponible.", "danger")
        return redirect(url_for("registro_guia"))

    nuevo_usuario = Usuario(
        nombre_completo=nombre,
        correo=correo,
        contrasenia_hash=generate_password_hash(password),
        telefono=telefono,
        rol="guia",
        estado="pendiente"
    )

    db.session.add(nuevo_usuario)
    db.session.flush()

    nuevo_guia = Guia(
        id_guia=nuevo_usuario.id_usuario,
        experiencia=experiencia,
        especialidad=especialidad,
        ciudad_base=ciudad_base,
        descripcion=descripcion,
        disponible=True
    )

    solicitud = SolicitudGuia(
        id_guia=nuevo_usuario.id_usuario,
        empresa_id=empresa.id,
        estado="pendiente"
    )

    db.session.add(nuevo_guia)
    db.session.add(solicitud)

    db.session.commit()

    flash(
        "Cuenta creada correctamente. Tu solicitud fue enviada a la empresa para aprobación.",
        "success"
    )

    return redirect(url_for("login_usuario"))
@app.route("/tours")
def tours():

    buscar = request.args.get("buscar", "")
    categoria_id = request.args.get("categoria_id", "")
    dificultad = request.args.get("dificultad", "")
    precio_min = request.args.get("precio_min", "")
    precio_max = request.args.get("precio_max", "")
    accesibilidad = request.args.get("accesibilidad", "")
    cupos_min = request.args.get("cupos_min", "")
    orden = request.args.get("orden", "")

    consulta = Tour.query.filter(
        Tour.estado == "activo"
    )

    if buscar:
        consulta = consulta.filter(
            Tour.titulo.ilike(f"%{buscar}%") |
            Tour.descripcion.ilike(f"%{buscar}%")
        )

    if categoria_id:
        consulta = consulta.filter(
            Tour.id_categoria == int(categoria_id)
        )

    if dificultad:
        consulta = consulta.filter(
            Tour.dificultad == dificultad
        )

    if precio_min:
        consulta = consulta.filter(
            Tour.precio >= float(precio_min)
        )

    if precio_max:
        consulta = consulta.filter(
            Tour.precio <= float(precio_max)
        )

    if accesibilidad:
        consulta = consulta.filter(
            Tour.acceso_rampa == True
        )

    if cupos_min:
        consulta = consulta.filter(
            Tour.cupo_disponible >= int(cupos_min)
        )

    if orden == "precio_asc":
        consulta = consulta.order_by(
            Tour.precio.asc()
        )

    elif orden == "precio_desc":
        consulta = consulta.order_by(
            Tour.precio.desc()
        )

    elif orden == "nombre":
        consulta = consulta.order_by(
            Tour.titulo.asc()
        )

    lista_tours = _adjuntar_calificaciones(
        consulta.all()
    )

    categorias = Categoria.query.order_by(
        Categoria.nombre
    ).all()

    idiomas_disponibles = [
        "Español",
        "Inglés",
        "Francés",
        "Italiano",
        "Portugués",
        "Alemán",
        "Español e Inglés"
    ]

    tiene_perfil_viajero = True

    if "usuario_id" in session:

        tiene_perfil_viajero = (
            PerfilViajero.query.filter_by(
                usuario_id=session["usuario_id"]
            ).first()
            is not None
        )

    return render_template(
        "tours.html",
        tours=lista_tours,
        buscar=buscar,
        categorias=categorias,
        categoria_id=categoria_id,
        dificultad=dificultad,
        idiomas_disponibles=idiomas_disponibles,
        precio_min=precio_min,
        precio_max=precio_max,
        accesibilidad=accesibilidad,
        cupos_min=cupos_min,
        orden=orden,
        tiene_perfil_viajero=tiene_perfil_viajero
    )



@app.route("/crear_tour")
def crear_tour():

    if "empresa_id" not in session:
        flash("Debes iniciar sesión como empresa.")
        return redirect(url_for("login_empresa"))

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    categorias = Categoria.query.order_by(
        Categoria.nombre
    ).all()

    guias = (
        db.session.query(Usuario)
        .join(
            SolicitudGuia,
            SolicitudGuia.id_guia == Usuario.id_usuario
        )
        .filter(
            SolicitudGuia.empresa_id == empresa.id,
            SolicitudGuia.estado == "aprobada",
            Usuario.rol == "guia",
            Usuario.estado == "activo"
        )
        .order_by(
            Usuario.nombre_completo.asc()
        )
        .all()
    )

    print("EMPRESA SESSION:", session["empresa_id"])
    print("EMPRESA BD:", empresa.id, empresa.nombre)
    print("TOTAL GUIAS:", len(guias))

    for guia in guias:
        print(
            "GUIA:",
            guia.nombre_completo,
            "| ID:",
            guia.id_usuario,
            "| ROL:",
            guia.rol,
            "| ESTADO:",
            guia.estado
        )

    return render_template(
        "crear_tour.html",
        categorias=categorias,
        guias=guias
    )


@app.route("/guardar_tour", methods=["POST"])
def guardar_tour():

    if "empresa_id" not in session:
        flash("Debes iniciar sesión como empresa.")
        return redirect(
            url_for("login_empresa")
        )

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash("No se encontró el usuario operador asociado a la empresa.")
        return redirect(
            url_for("login_empresa")
        )

    categoria_id = request.form.get("categoria_id")

    cupo_maximo = int(
        request.form.get("cupos", 0)
    )

    incluye = request.form.getlist("incluye")

    incluye_texto = "\n".join(incluye)

    nuevo = Tour(
        id_operador=usuario_operador.id_usuario,
        id_categoria=int(categoria_id),
        titulo=request.form["titulo"],
        ciudad=request.form["ciudad"],
        descripcion=request.form["descripcion"],
        incluye=incluye_texto,
        precio=float(request.form["precio"]),
        cupo_maximo=cupo_maximo,
        cupo_disponible=cupo_maximo,
        dificultad=request.form.get(
            "dificultad",
            "Fácil"
        ),
        acceso_rampa=(
            "apto_movilidad_reducida" in request.form
        ),
        banos_cercanos=False,
        estado="pendiente"
    )

    db.session.add(nuevo)
    db.session.commit()

    imagen_portada = request.files.get("imagen")

    if imagen_portada:

        ruta = _guardar_imagen(imagen_portada)

        if ruta:

            db.session.add(
                TourImagen(
                    tour_id=nuevo.id_tour,
                    url=ruta,
                    orden=0
                )
            )

    for archivo in request.files.getlist("galeria"):

        ruta = _guardar_imagen(archivo)

        if ruta:

            db.session.add(
                TourImagen(
                    tour_id=nuevo.id_tour,
                    url=ruta,
                    orden=1
                )
            )

    db.session.commit()

    flash(
        "Tu tour fue enviado a revisión. "
        "Será publicado cuando un administrador "
        "de Zuqara lo apruebe."
    )

    return redirect(
        url_for("mis_tours")
    )


@app.route("/perfil")
def perfil():

    if "usuario_id" in session:

        usuario = db.session.get(
            Usuario,
            session["usuario_id"]
        )

        return render_template(
            "perfil.html",
            usuario=usuario
        )

    if "empresa_id" in session:

        empresa = db.session.get(
            Empresa,
            session["empresa_id"]
        )

        return render_template(
            "perfil.html",
            empresa=empresa
        )

    flash("Debes iniciar sesión")

    return redirect(
        url_for("index")
    )


@app.route("/editar_perfil", methods=["POST"])
def editar_perfil():

    if "usuario_id" in session:

        usuario = db.session.get(
            Usuario,
            session["usuario_id"]
        )

        usuario.nombre_completo = request.form[
            "nombre"
        ]

        usuario.correo = request.form[
            "correo"
        ]

        db.session.commit()

        flash(
            "Perfil actualizado correctamente"
        )

    elif "empresa_id" in session:

        empresa = db.session.get(
            Empresa,
            session["empresa_id"]
        )

        empresa.nombre = request.form[
            "nombre"
        ]

        empresa.correo = request.form[
            "correo"
        ]

        empresa.telefono = request.form[
            "telefono"
        ]

        empresa.direccion = request.form[
            "direccion"
        ]

        db.session.commit()

        flash(
            "Perfil actualizado correctamente"
        )

    return redirect(
        url_for("perfil")
    )


@app.route("/subir_foto_perfil", methods=["POST"])
def subir_foto_perfil():

    if (
        "usuario_id" not in session
        and "empresa_id" not in session
    ):
        flash("Debes iniciar sesión")
        return redirect(
            url_for("index")
        )

    archivo = request.files.get("foto")

    if not archivo or archivo.filename == "":
        flash(
            "Selecciona una imagen antes de subirla."
        )
        return redirect(
            url_for("perfil")
        )

    ruta_imagen = _guardar_imagen(
        archivo
    )

    if not ruta_imagen:
        flash(
            "No se pudo subir la imagen."
        )
        return redirect(
            url_for("perfil")
        )

    if "usuario_id" in session:

        usuario = db.session.get(
            Usuario,
            session["usuario_id"]
        )

        usuario.foto = ruta_imagen

    elif "empresa_id" in session:

        empresa = db.session.get(
            Empresa,
            session["empresa_id"]
        )

        empresa.foto = ruta_imagen

    db.session.commit()

    flash(
        "Foto de perfil actualizada correctamente."
    )

    return redirect(
        url_for("perfil")
    )


@app.route("/cambiar_password", methods=["POST"])
def cambiar_password():

    if "usuario_id" in session:

        usuario = db.session.get(
            Usuario,
            session["usuario_id"]
        )

        actual = request.form["actual"]
        nueva = request.form["nueva"]
        confirmar = request.form["confirmar"]

        if not check_password_hash(
            usuario.contrasenia_hash,
            actual
        ):
            flash(
                "La contraseña actual es incorrecta"
            )
            return redirect(
                url_for("perfil")
            )

        if nueva != confirmar:
            flash(
                "Las nuevas contraseñas no coinciden"
            )
            return redirect(
                url_for("perfil")
            )

        usuario.contrasenia_hash = (
            generate_password_hash(nueva)
        )

        db.session.commit()

        flash(
            "Contraseña actualizada correctamente"
        )

    elif "empresa_id" in session:

        empresa = db.session.get(
            Empresa,
            session["empresa_id"]
        )

        actual = request.form["actual"]
        nueva = request.form["nueva"]
        confirmar = request.form["confirmar"]

        if not check_password_hash(
            empresa.contrasena,
            actual
        ):
            flash(
                "La contraseña actual es incorrecta"
            )
            return redirect(
                url_for("perfil")
            )

        if nueva != confirmar:
            flash(
                "Las nuevas contraseñas no coinciden"
            )
            return redirect(
                url_for("perfil")
            )

        empresa.contrasena = (
            generate_password_hash(nueva)
        )

        db.session.commit()

        flash(
            "Contraseña actualizada correctamente"
        )

    return redirect(
        url_for("perfil")
    )


@app.route("/guardar_perfil_viajero", methods=["POST"])
def guardar_perfil_viajero():

    if "usuario_id" not in session:
        flash(
            "Debes iniciar sesión para configurar "
            "tu perfil de viajero."
        )
        return redirect(
            url_for("login_usuario")
        )

    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    perfil_viajero = usuario.perfil_viajero

    if perfil_viajero is None:

        perfil_viajero = PerfilViajero(
            usuario_id=usuario.id_usuario
        )

        db.session.add(
            perfil_viajero
        )

        es_nuevo = True

    else:
        es_nuevo = False

    perfil_viajero.nivel_actividad = (
        request.form.get(
            "nivel_actividad",
            "Moderado"
        )
    )

    perfil_viajero.viaja_con = (
        request.form.get(
            "viaja_con",
            ""
        )
    )

    perfil_viajero.requiere_accesibilidad = (
        "requiere_accesibilidad"
        in request.form
    )

    perfil_viajero.restricciones_alimenticias = (
        request.form.get(
            "restricciones_alimenticias",
            ""
        )
    )

    perfil_viajero.notas = (
        request.form.get(
            "notas",
            ""
        )
    )

    presupuesto = request.form.get(
        "presupuesto_promedio"
    )

    perfil_viajero.presupuesto_promedio = (
        float(presupuesto)
        if presupuesto
        else None
    )

    db.session.commit()

    flash(
        "Tu perfil de viajero fue creado."
        if es_nuevo
        else "Tu perfil de viajero fue actualizado."
    )

    return redirect(
        url_for("perfil")
    )


@app.route("/eliminar_perfil_viajero")
def eliminar_perfil_viajero():

    if "usuario_id" not in session:
        flash("Debes iniciar sesión.")
        return redirect(
            url_for("login_usuario")
        )

    usuario = db.session.get(
        Usuario,
        session["usuario_id"]
    )

    if usuario.perfil_viajero:

        db.session.delete(
            usuario.perfil_viajero
        )

        db.session.commit()

        flash(
            "Tu perfil de viajero fue eliminado."
        )

    return redirect(
        url_for("perfil")
    )


@app.route("/reservas")
def reservas():

    if "usuario_id" not in session:
        flash(
            "Debes iniciar sesión como usuario."
        )
        return redirect(
            url_for("login_usuario")
        )

    reservas = Reserva.query.filter_by(
        id_viajero=session["usuario_id"]
    ).all()

    reserva_comentarios = {}

    for reserva in reservas:

        comentario = Comentario.query.filter_by(
            reserva_id=reserva.id_reserva
        ).first()

        reserva_comentarios[
            reserva.id_reserva
        ] = comentario

    return render_template(
        "reservas.html",
        reservas=reservas,
        reserva_comentarios=reserva_comentarios
    )


@app.route("/factura/<int:reserva_id>")
def factura(reserva_id):

    if "usuario_id" not in session:
        flash(
            "Debes iniciar sesión como usuario."
        )
        return redirect(
            url_for("login_usuario")
        )

    reserva = Reserva.query.get_or_404(
        reserva_id
    )

    if str(reserva.id_viajero) != str(session["usuario_id"]):
        flash(
            "No tienes permiso para ver esta factura."
        )
        return redirect(
            url_for("reservas")
        )

    if not reserva.pago:
        flash(
            "Esta reserva todavía no tiene "
            "un pago registrado."
        )
        return redirect(
            url_for("reservas")
        )

    usuario_operador = Usuario.query.get(
        reserva.tour.id_operador
    )

    empresa = None

    if usuario_operador:
        empresa = Empresa.query.filter_by(
            correo=usuario_operador.correo
        ).first()

    numero_factura = (
        f"ZT-{reserva.pago.fecha_pago.year}-"
        f"{reserva.id_reserva:05d}"
    )

    return render_template(
        "factura.html",
        reserva=reserva,
        pago=reserva.pago,
        empresa=empresa,
        numero_factura=numero_factura
    )

@app.route("/registro_empresa", methods=["POST"])
def registro_empresa_post():

    nombre = request.form["nombre"]
    nit = request.form["nit"]
    correo = request.form["correo"]
    telefono = request.form["telefono"]
    direccion = request.form["direccion"]
    password = request.form["password"]
    confirmar = request.form["confirmar_password"]

    if password != confirmar:
        flash("Las contraseñas no coinciden")
        return redirect(
            url_for("registro_empresa")
        )

    empresa = Empresa.query.filter_by(
        correo=correo
    ).first()

    if empresa:
        flash("Este correo ya está registrado")
        return redirect(
            url_for("registro_empresa")
        )

    usuario_existente = Usuario.query.filter_by(
        correo=correo
    ).first()

    if usuario_existente:
        flash("Este correo ya está registrado")
        return redirect(
            url_for("registro_empresa")
        )

    nueva = Empresa(
        nombre=nombre,
        nit=nit,
        correo=correo,
        telefono=telefono,
        direccion=direccion,
        contrasena=generate_password_hash(password)
    )

    db.session.add(nueva)

    nuevo_usuario = Usuario(
        nombre_completo=nombre,
        correo=correo,
        contrasenia_hash=generate_password_hash(password),
        telefono=telefono,
        rol="operador",
        estado="activo"
    )

    db.session.add(nuevo_usuario)

    db.session.commit()

    flash("Empresa registrada correctamente")

    return redirect(
        url_for("login_empresa")
    )

@app.route("/login_empresa", methods=["POST"])
def login_empresa_post():

    correo = request.form["correo"]
    password = request.form["password"]

    empresa = Empresa.query.filter_by(
        correo=correo
    ).first()

    if empresa and check_password_hash(
        empresa.contrasena,
        password
    ):

        if not empresa.aprobado:
            flash(
                "Tu empresa está pendiente de "
                "aprobación por Zuqara."
            )
            return redirect(
                url_for("login_empresa")
            )

        session["empresa_id"] = empresa.id
        session["empresa_nombre"] = empresa.nombre

        return redirect(
            url_for("dashboard_empresa")
        )

    flash(
        "Correo o contraseña incorrectos"
    )

    return redirect(
        url_for("login_empresa")
    )


@app.route(
    "/reservar/<int:tour_id>",
    methods=["GET", "POST"]
)
def reservar_tour(tour_id):

    if "usuario_id" not in session:
        flash("Debes iniciar sesión.")
        return redirect(url_for("login_usuario"))

    tour = Tour.query.get_or_404(tour_id)

    if request.method == "POST":
        try:
            adultos = int(request.form.get("adultos", 1))
            ninos = int(request.form.get("ninos", 0))
        except (TypeError, ValueError):
            flash("La cantidad de personas no es válida.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))

        if adultos < 1 or ninos < 0:
            flash("Debe haber al menos un adulto y los niños no pueden ser negativos.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))

        total_personas = adultos + ninos
        if total_personas > tour.cupo_disponible:
            flash("No hay suficientes cupos disponibles para esa cantidad de personas.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))

        nombres = request.form.getlist("pasajeros_nombre[]")
        tipos_documento = request.form.getlist("pasajeros_tipo_documento[]")
        documentos = request.form.getlist("pasajeros_documento[]")
        telefonos = request.form.getlist("pasajeros_telefono[]")

        if any(len(lista) != total_personas for lista in (nombres, tipos_documento, documentos, telefonos)):
            flash("Debes completar la información de todos los pasajeros.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))

        try:
            fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            flash("La fecha seleccionada no es válida.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))

        if fecha < datetime.today().date():
            flash("La fecha del viaje no puede estar en el pasado.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))

        tipo_transporte = request.form.get("tipo_transporte", "").strip().lower()
        origen = request.form.get("origen", "").strip()
        destino = request.form.get("destino", "").strip()
        hora_salida = request.form.get("hora_salida", "").strip()
        asientos = request.form.getlist("asientos[]")
        horarios_permitidos = {"07:00", "09:00", "13:00", "16:00"}

        if tipo_transporte not in {"avion", "bus"}:
            flash("Selecciona si viajarás en avión o bus.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))
        if not origen or not destino or origen.casefold() == destino.casefold():
            flash("Indica un origen y un destino diferentes.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))
        if hora_salida not in horarios_permitidos:
            flash("Selecciona un horario de salida válido.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))
        if len(asientos) != total_personas or len(set(asientos)) != total_personas:
            flash(f"Debes seleccionar exactamente {total_personas} asientos diferentes.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))

        filas = 12 if tipo_transporte == "avion" else 10
        letras = "ABCDEF" if tipo_transporte == "avion" else "ABCD"
        asientos_validos = {f"{fila}{letra}" for fila in range(1, filas + 1) for letra in letras}
        if any(asiento not in asientos_validos for asiento in asientos):
            flash("Uno de los asientos seleccionados no existe en este vehículo.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))

        ocupados = {
            fila.asiento for fila in TransporteReserva.query.filter_by(
                tour_id=tour.id_tour, fecha_viaje=fecha, tipo_transporte=tipo_transporte
            ).all()
        }
        if ocupados.intersection(asientos):
            flash("Uno de los asientos ya fue reservado. Selecciona otros asientos.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))

        precio_total = adultos * tour.precio + ninos * tour.precio * Decimal("0.5")
        reserva = Reserva(
            id_viajero=session["usuario_id"],
            id_tour=tour.id_tour,
            cantidad_personas=total_personas,
            total_pago=precio_total,
            estado_reserva="pendiente"
        )

        try:
            db.session.add(reserva)
            db.session.flush()

            for i in range(total_personas):
                tipo_pasajero = "Adulto" if i < adultos else "Niño"
                db.session.add(PasajeroReserva(
                    reserva_id=reserva.id_reserva,
                    nombre=nombres[i].strip(),
                    tipo_documento=tipos_documento[i],
                    documento=documentos[i].strip(),
                    telefono=telefonos[i].strip(),
                    tipo=tipo_pasajero
                ))
                db.session.add(TransporteReserva(
                    reserva_id=reserva.id_reserva,
                    tour_id=tour.id_tour,
                    fecha_viaje=fecha,
                    tipo_transporte=tipo_transporte,
                    origen=origen[:120],
                    destino=destino[:120],
                    hora_salida=hora_salida,
                    asiento=asientos[i],
                    pasajero_indice=i + 1
                ))

            tour.cupo_disponible -= total_personas
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Otro cliente acaba de ocupar uno de esos asientos. Vuelve a seleccionar.", "error")
            return redirect(url_for("reservar_tour", tour_id=tour.id_tour))
        except Exception:
            db.session.rollback()
            raise

        flash("Reserva creada correctamente. Ya casi, solo falta el pago.", "success")
        return redirect(url_for("pagar_reserva", reserva_id=reserva.id_reserva))

    return render_template("reservar_tour.html", tour=tour)


@app.route("/api/transporte/<int:tour_id>/asientos")
def consultar_asientos_transporte(tour_id):
    if "usuario_id" not in session:
        return jsonify({"error": "Inicia sesión para consultar los asientos."}), 401

    Tour.query.get_or_404(tour_id)
    fecha_texto = request.args.get("fecha", "")
    tipo = request.args.get("tipo", "").strip().lower()
    try:
        fecha = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Fecha no válida."}), 400
    if tipo not in {"avion", "bus"}:
        return jsonify({"error": "Tipo de transporte no válido."}), 400

    ocupados = [fila.asiento for fila in TransporteReserva.query.filter_by(
        tour_id=tour_id, fecha_viaje=fecha, tipo_transporte=tipo
    ).all()]
    return jsonify({"ocupados": ocupados})

@app.route(
    "/pagar_reserva/<int:reserva_id>",
    methods=["GET", "POST"]
)
def pagar_reserva(reserva_id):
    """Pago académico simulado: no recibe ni almacena datos bancarios."""
    if "usuario_id" not in session:
        flash("Debes iniciar sesión.")
        return redirect(url_for("login_usuario"))

    reserva = Reserva.query.get_or_404(reserva_id)

    if str(reserva.id_viajero) != str(session["usuario_id"]):
        flash("No tienes permiso para pagar esta reserva.")
        return redirect(url_for("reservas"))

    if reserva.estado_reserva == "confirmada":
        flash("Esta reserva ya está confirmada.")
        return redirect(url_for("reservas"))

    if reserva.estado_reserva != "pendiente":
        flash("Esta reserva no está disponible para pago.")
        return redirect(url_for("reservas"))

    usuario = Usuario.query.get(reserva.id_viajero)

    if request.method == "POST":
        metodo_pago = request.form.get("metodo_pago", "").strip()
        resultado = request.form.get("resultado_simulado", "").strip()

        metodos_permitidos = {
            "Tarjeta simulada",
            "Transferencia simulada",
            "Efectivo simulado"
        }
        resultados_permitidos = {"aprobado", "rechazado"}

        if metodo_pago not in metodos_permitidos or resultado not in resultados_permitidos:
            flash("Selecciona un método y un resultado de simulación válidos.", "error")
            return redirect(url_for("pagar_reserva", reserva_id=reserva.id_reserva))

        estado_intento = "Aprobado" if resultado == "aprobado" else "Rechazado"
        referencia = "SIM-" + uuid.uuid4().hex[:12].upper()

        intento = IntentoPagoSimulado(
            reserva_id=reserva.id_reserva,
            metodo_pago=metodo_pago,
            estado=estado_intento,
            referencia=referencia
        )
        db.session.add(intento)

        if resultado == "aprobado":
            # La tabla pagos actual admite un registro por reserva.
            # Se crea solo al aprobar para que una factura nunca represente un rechazo.
            pago = Pago.query.filter_by(reserva_id=reserva.id_reserva).first()
            if pago is None:
                pago = Pago(
                    reserva_id=reserva.id_reserva,
                    monto=float(reserva.total_pago),
                    metodo_pago=metodo_pago,
                    referencia=referencia,
                    estado="Aprobado"
                )
                db.session.add(pago)
            else:
                pago.monto = float(reserva.total_pago)
                pago.metodo_pago = metodo_pago
                pago.referencia = referencia
                pago.estado = "Aprobado"
                pago.fecha_pago = datetime.utcnow()

            reserva.estado_reserva = "confirmada"
            db.session.flush()

            usuario_operador = Usuario.query.get(reserva.tour.id_operador)
            empresa = None
            if usuario_operador:
                empresa = Empresa.query.filter_by(correo=usuario_operador.correo).first()

            if empresa:
                notificacion = Notificacion(
                    empresa_id=empresa.id,
                    tour_id=reserva.id_tour,
                    tipo="reserva",
                    mensaje=(
                        f'Nueva reserva confirmada para "{reserva.tour.titulo}" '
                        f'({reserva.cantidad_personas} persona(s)).'
                    )
                )
                db.session.add(notificacion)

            db.session.commit()
            flash("¡Pago simulado aprobado! Tu reserva quedó confirmada.", "success")
            return redirect(url_for("reservas"))

        # Un rechazo queda en el historial, pero la reserva sigue pendiente.
        db.session.commit()
        flash("El pago simulado fue rechazado. Puedes intentarlo nuevamente.", "error")
        return redirect(url_for("pagar_reserva", reserva_id=reserva.id_reserva))

    intentos = (
        IntentoPagoSimulado.query
        .filter_by(reserva_id=reserva.id_reserva)
        .order_by(IntentoPagoSimulado.fecha_intento.desc())
        .all()
    )

    return render_template(
        "pagar_reserva.html",
        reserva=reserva,
        usuario=usuario,
        intentos=intentos
    )



@app.route(
    "/finalizar_reserva/<int:reserva_id>"
)
def finalizar_reserva(reserva_id):

    if "empresa_id" not in session:
        flash("Debes iniciar sesión como empresa.")
        return redirect(
            url_for("login_empresa")
        )

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    reserva = Reserva.query.get_or_404(
        reserva_id
    )

    usuario_operador = Usuario.query.get(
        reserva.tour.id_operador
    )

    if not usuario_operador:
        flash(
            "No se encontró el operador del tour."
        )
        return redirect(
            url_for("reservas_empresa")
        )

    empresa_tour = Empresa.query.filter_by(
        correo=usuario_operador.correo
    ).first()

    if not empresa_tour:
        flash(
            "No se encontró la empresa asociada al tour."
        )
        return redirect(
            url_for("reservas_empresa")
        )

    if empresa_tour.id != empresa.id:
        flash(
            "No tienes permiso para finalizar esta reserva."
        )
        return redirect(
            url_for("reservas_empresa")
        )

    if reserva.estado_reserva != "confirmada":
        flash(
            "Solo puedes finalizar reservas confirmadas."
        )
        return redirect(
            url_for("reservas_empresa")
        )

    reserva.estado_reserva = "finalizada"

    db.session.commit()

    flash(
        "La reserva fue marcada como finalizada correctamente."
    )

    return redirect(
        url_for("reservas_empresa")
    )


@app.route("/mis_tours")
def mis_tours():

    if "empresa_id" not in session:
        flash("Debes iniciar sesión como empresa.")
        return redirect(
            url_for("login_empresa")
        )

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash("No se encontró el usuario operador asociado a esta empresa.")
        return redirect(
            url_for("login_empresa")
        )

    tours = Tour.query.filter_by(
        id_operador=usuario_operador.id_usuario
    ).all()

    return render_template(
        "mis_tours.html",
        tours=tours
    )

@app.route("/editar_tour/<int:id>")
def editar_tour(id):

    if "empresa_id" not in session:
        flash(
            "Debes iniciar sesión como empresa."
        )
        return redirect(
            url_for("login_empresa")
        )

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash(
            "No se encontró el usuario operador asociado a la empresa."
        )
        return redirect(
            url_for("login_empresa")
        )

    tour = Tour.query.get_or_404(id)

    if tour.id_operador != usuario_operador.id_usuario:
        flash(
            "No tienes permiso para editar este tour."
        )
        return redirect(
            url_for("mis_tours")
        )

    categorias = Categoria.query.order_by(
        Categoria.nombre
    ).all()

    guias = (
        db.session.query(Usuario)
        .join(
            SolicitudGuia,
            SolicitudGuia.id_guia == Usuario.id_usuario
        )
        .filter(
            SolicitudGuia.empresa_id == empresa.id,
            SolicitudGuia.estado == "aprobada",
            Usuario.rol == "guia",
            Usuario.estado == "activo"
        )
        .order_by(
            Usuario.nombre_completo.asc()
        )
        .all()
    )

    asignacion = AsignacionGuia.query.filter_by(
        id_tour=tour.id_tour,
        empresa_id=empresa.id,
        estado="activo"
    ).first()

    guia_asignado = None

    if asignacion:
        guia_asignado = asignacion.guia

    return render_template(
        "editar_tour.html",
        tour=tour,
        categorias=categorias,
        guias=guias,
        guia_asignado=guia_asignado
    )

@app.route(
    "/actualizar_tour/<int:id>",
    methods=["POST"]
)
def actualizar_tour(id):

    if "empresa_id" not in session:
        flash(
            "Debes iniciar sesión como empresa."
        )
        return redirect(
            url_for("login_empresa")
        )

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash(
            "No se encontró el usuario operador asociado a la empresa."
        )
        return redirect(
            url_for("login_empresa")
        )

    tour = Tour.query.get_or_404(id)

    if tour.id_operador != usuario_operador.id_usuario:
        flash(
            "No tienes permiso para editar este tour."
        )
        return redirect(
            url_for("mis_tours")
        )

    tour.titulo = request.form["titulo"]

    tour.descripcion = request.form["descripcion"]

    tour.ciudad = request.form["ciudad"]

    tour.precio = float(
        request.form["precio"]
    )

    nuevo_cupo = int(
        request.form["cupos"]
    )

    diferencia_cupos = (
        nuevo_cupo - tour.cupo_maximo
    )

    tour.cupo_maximo = nuevo_cupo

    tour.cupo_disponible = max(
        0,
        tour.cupo_disponible + diferencia_cupos
    )

    categoria_id = (
        request.form.get("categoria_id")
        or None
    )

    if categoria_id:
        tour.id_categoria = int(
            categoria_id
        )

    tour.dificultad = request.form.get(
        "dificultad",
        tour.dificultad
    )

    tour.acceso_rampa = (
        "apto_movilidad_reducida"
        in request.form
    )

    guia_id = request.form.get("guia_id")

    print("====================================")
    print("TOUR:", tour.id_tour)
    print("GUIA RECIBIDO:", guia_id)
    print("EMPRESA:", empresa.id)
    print("====================================")

    if not guia_id:
        flash(
            "Debes seleccionar un guía."
        )
        return redirect(
            url_for(
                "editar_tour",
                id=tour.id_tour
            )
        )

    guia = (
        db.session.query(Usuario)
        .join(
            SolicitudGuia,
            SolicitudGuia.id_guia == Usuario.id_usuario
        )
        .filter(
            Usuario.id_usuario == guia_id,
            Usuario.rol == "guia",
            Usuario.estado == "activo",
            SolicitudGuia.empresa_id == empresa.id,
            SolicitudGuia.estado == "aprobada"
        )
        .first()
    )

    if not guia:
        flash(
            "El guía seleccionado no está aprobado o no pertenece a tu empresa."
        )
        return redirect(
            url_for(
                "editar_tour",
                id=tour.id_tour
            )
        )

    asignacion = AsignacionGuia.query.filter_by(
        id_tour=tour.id_tour,
        empresa_id=empresa.id
    ).first()

    if asignacion:
        asignacion.id_guia = guia.id_usuario
        asignacion.estado = "activo"
        asignacion.fecha_asignacion = datetime.now()

        print("ASIGNACION EXISTENTE ACTUALIZADA")
        print("GUIA:", asignacion.id_guia)
        print("TOUR:", asignacion.id_tour)
        print("EMPRESA:", asignacion.empresa_id)

    else:
        nueva_asignacion = AsignacionGuia(
            id_guia=guia.id_usuario,
            id_tour=tour.id_tour,
            empresa_id=empresa.id,
            estado="activo"
        )

        db.session.add(nueva_asignacion)

        print("NUEVA ASIGNACION CREADA")
        print("GUIA:", nueva_asignacion.id_guia)
        print("TOUR:", nueva_asignacion.id_tour)
        print("EMPRESA:", nueva_asignacion.empresa_id)
        print("ESTADO:", nueva_asignacion.estado)

    db.session.commit()

    asignacion_guardada = AsignacionGuia.query.filter_by(
        id_tour=tour.id_tour,
        empresa_id=empresa.id
    ).first()

    print("====================================")
    print("ASIGNACION DESPUES DEL COMMIT:")

    if asignacion_guardada:
        print(
            "ID ASIGNACION:",
            asignacion_guardada.id_asignacion
        )
        print(
            "ID GUIA:",
            asignacion_guardada.id_guia
        )
        print(
            "ID TOUR:",
            asignacion_guardada.id_tour
        )
        print(
            "EMPRESA:",
            asignacion_guardada.empresa_id
        )
        print(
            "ESTADO:",
            asignacion_guardada.estado
        )
    else:
        print("NO SE GUARDO LA ASIGNACION")

    print("====================================")

    flash(
        "Tour actualizado y guía asignado correctamente."
    )

    return redirect(
        url_for("mis_tours")
    )

@app.route(
    "/tour/<int:id>/agregar_imagenes",
    methods=["POST"]
)
def agregar_imagenes_tour(id):

    if "empresa_id" not in session:
        flash(
            "Debes iniciar sesión como empresa."
        )
        return redirect(
            url_for("login_empresa")
        )

    tour = Tour.query.get_or_404(id)

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash(
            "No se encontró el usuario operador asociado a la empresa."
        )
        return redirect(
            url_for("mis_tours")
        )

    if tour.id_operador != usuario_operador.id_usuario:
        flash(
            "No tienes permiso para editar este tour."
        )
        return redirect(
            url_for("mis_tours")
        )

    agregadas = 0

    for archivo in request.files.getlist(
        "galeria"
    ):

        ruta = _guardar_imagen(archivo)

        if ruta:

            db.session.add(
                TourImagen(
                    tour_id=tour.id_tour,
                    url=ruta
                )
            )

            agregadas += 1

    db.session.commit()

    flash(
        f"Se agregaron {agregadas} foto(s) a la galería."
        if agregadas
        else "No se subió ninguna foto."
    )

    return redirect(
        url_for(
            "editar_tour",
            id=tour.id_tour
        )
    )

@app.route(
    "/tour_imagen/eliminar/<int:id>"
)
def eliminar_imagen_tour(id):

    imagen = TourImagen.query.get_or_404(id)

    if (
        imagen.tour.empresa_id
        != session.get("empresa_id")
    ):
        flash(
            "No tienes permiso para hacer esto."
        )
        return redirect(
            url_for("mis_tours")
        )

    tour_id = imagen.tour_id

    db.session.delete(imagen)
    db.session.commit()

    flash(
        "Foto eliminada de la galería."
    )

    return redirect(
        url_for(
            "editar_tour",
            id=tour_id
        )
    )


@app.route(
    "/tour/<int:id>/agregar_dia",
    methods=["POST"]
)
def agregar_dia_tour(id):

    if "empresa_id" not in session:
        flash(
            "Debes iniciar sesión como empresa."
        )
        return redirect(
            url_for("login_empresa")
        )

    tour = Tour.query.get_or_404(id)

    if tour.empresa_id != session["empresa_id"]:
        flash(
            "No tienes permiso para editar este tour."
        )
        return redirect(
            url_for("mis_tours")
        )

    numero_dia = request.form.get(
        "numero_dia"
    )

    titulo = request.form.get(
        "titulo",
        ""
    ).strip()

    if not numero_dia or not titulo:
        flash(
            "El número de día y el título son obligatorios."
        )
        return redirect(
            url_for(
                "editar_tour",
                id=tour.id
            )
        )

    dia = ItinerarioTourDia(
        tour_id=tour.id,
        numero_dia=int(numero_dia),
        titulo=titulo,
        descripcion=request.form.get(
            "descripcion",
            ""
        )
    )

    db.session.add(dia)
    db.session.commit()

    flash(
        "Día agregado al itinerario del tour."
    )

    return redirect(
        url_for(
            "editar_tour",
            id=tour.id
        )
    )

@app.route(
    "/itinerario_tour/eliminar_dia/<int:id>"
)
def eliminar_dia_tour(id):

    if "empresa_id" not in session:
        flash(
            "Debes iniciar sesión como empresa."
        )
        return redirect(
            url_for("login_empresa")
        )

    dia = ItinerarioTourDia.query.get_or_404(id)

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash(
            "No se encontró el usuario operador asociado a la empresa."
        )
        return redirect(
            url_for("mis_tours")
        )

    if dia.tour.id_operador != usuario_operador.id_usuario:
        flash(
            "No tienes permiso para hacer esto."
        )
        return redirect(
            url_for("mis_tours")
        )

    tour_id = dia.tour_id

    db.session.delete(dia)
    db.session.commit()

    flash(
        "Día eliminado del itinerario del tour."
    )

    return redirect(
        url_for(
            "editar_tour",
            id=tour_id
        )
    )

@app.route("/eliminar_tour/<int:tour_id>")
def eliminar_tour(tour_id):

    if "empresa_id" not in session:
        flash("Debes iniciar sesión como empresa.")
        return redirect(url_for("login_empresa"))

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash("No se encontró el usuario operador asociado a la empresa.")
        return redirect(url_for("login_empresa"))

    tour = Tour.query.get_or_404(tour_id)

    if tour.id_operador != usuario_operador.id_usuario:
        flash("No tienes permiso para eliminar este tour.")
        return redirect(url_for("mis_tours"))

    notificaciones = Notificacion.query.filter_by(
        tour_id=tour.id_tour
    ).all()

    for notificacion in notificaciones:
        db.session.delete(notificacion)

    relaciones_itinerario = ItinerarioViajeTour.query.filter_by(
        tour_id=tour.id_tour
    ).all()

    for relacion in relaciones_itinerario:
        db.session.delete(relacion)

    conversaciones = Conversacion.query.filter_by(
        tour_id=tour.id_tour
    ).all()

    for conversacion in conversaciones:

        mensajes = Mensaje.query.filter_by(
            conversacion_id=conversacion.id
        ).all()

        for mensaje in mensajes:
            db.session.delete(mensaje)

        db.session.delete(conversacion)

    favoritos = Favorito.query.filter_by(
        tour_id=tour.id_tour
    ).all()

    for favorito in favoritos:
        db.session.delete(favorito)

    guardados = Guardado.query.filter_by(
        tour_id=tour.id_tour
    ).all()

    for guardado in guardados:
        db.session.delete(guardado)

    imagenes = TourImagen.query.filter_by(
        tour_id=tour.id_tour
    ).all()

    for imagen in imagenes:
        db.session.delete(imagen)

    reservas = Reserva.query.filter_by(
        id_tour=tour.id_tour
    ).all()

    for reserva in reservas:

        comentarios = Comentario.query.filter_by(
            reserva_id=reserva.id_reserva
        ).all()

        for comentario in comentarios:
            db.session.delete(comentario)

        db.session.delete(reserva)

    db.session.delete(tour)

    db.session.commit()

    flash("Tour eliminado correctamente.")

    return redirect(url_for("mis_tours"))

@app.route("/reservas_empresa")
def reservas_empresa():

    if "empresa_id" not in session:
        flash("Debes iniciar sesión como empresa.")
        return redirect(
            url_for("login_empresa")
        )

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash("No se encontró el usuario operador asociado a esta empresa.")
        return redirect(
            url_for("login_empresa")
        )

    reservas = (
        Reserva.query
        .join(Tour)
        .filter(
            Tour.id_operador == usuario_operador.id_usuario
        )
        .all()
    )

    return render_template(
        "reservas_empresa.html",
        reservas=reservas
    )

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Sesión cerrada correctamente"
    )

    return redirect(
        url_for("index")
    )

@app.route("/favoritos")
def favoritos():

    if "usuario_id" not in session:
        flash("Debes iniciar sesión para ver tus favoritos.")
        return redirect(url_for("login_usuario"))

    favoritos = (
        Favorito.query
        .filter_by(
            usuario_id=session["usuario_id"]
        )
        .order_by(
            Favorito.created_at.desc()
        )
        .all()
    )

    guardados = (
        Guardado.query
        .filter_by(
            usuario_id=session["usuario_id"]
        )
        .order_by(
            Guardado.created_at.desc()
        )
        .all()
    )

    return render_template(
        "favoritos.html",
        favoritos=favoritos,
        guardados=guardados
    )


@app.route("/agregar_favorito/<int:tour_id>")
def agregar_favorito(tour_id):

    if "usuario_id" not in session:
        flash("Debes iniciar sesión.")
        return redirect(url_for("login_usuario"))

    tour = Tour.query.get_or_404(tour_id)

    existe = Favorito.query.filter_by(
        usuario_id=session["usuario_id"],
        tour_id=tour.id_tour
    ).first()

    if existe:
        db.session.delete(existe)
        db.session.commit()

        flash("Tour eliminado de favoritos.")

    else:
        nuevo_favorito = Favorito(
            usuario_id=session["usuario_id"],
            tour_id=tour.id_tour,
            created_at=db.func.current_timestamp()
        )

        db.session.add(nuevo_favorito)
        db.session.commit()

        flash("Tour agregado a favoritos.")

    return redirect(
        request.referrer or url_for("tours")
    )

@app.route("/itinerarios")
def itinerarios():

    if "usuario_id" not in session:
        flash(
            "Debes iniciar sesión para ver tus itinerarios."
        )
        return redirect(
            url_for("login_usuario")
        )

    lista = (
        ItinerarioViaje.query
        .filter_by(
            usuario_id=session["usuario_id"]
        )
        .order_by(
            ItinerarioViaje.fecha_creacion.desc()
        )
        .all()
    )

    return render_template(
        "itinerarios.html",
        itinerarios=lista
    )


@app.route(
    "/itinerarios/crear",
    methods=["POST"]
)
def crear_itinerario():

    if "usuario_id" not in session:
        flash(
            "Debes iniciar sesión para crear un itinerario."
        )
        return redirect(
            url_for("login_usuario")
        )

    nombre = request.form.get(
        "nombre",
        ""
    ).strip()

    if not nombre:
        flash(
            "Ponle un nombre a tu itinerario."
        )
        return redirect(
            url_for("itinerarios")
        )

    fecha_inicio = (
        request.form.get("fecha_inicio")
        or None
    )

    fecha_fin = (
        request.form.get("fecha_fin")
        or None
    )

    nuevo = ItinerarioViaje(
        usuario_id=session["usuario_id"],
        nombre=nombre,
        fecha_inicio=(
            datetime.strptime(
                fecha_inicio,
                "%Y-%m-%d"
            ).date()
            if fecha_inicio
            else None
        ),
        fecha_fin=(
            datetime.strptime(
                fecha_fin,
                "%Y-%m-%d"
            ).date()
            if fecha_fin
            else None
        )
    )

    db.session.add(nuevo)
    db.session.commit()

    flash(
        "Itinerario creado. Ahora agrégale tours "
        "desde la ficha de cada destino."
    )

    return redirect(
        url_for(
            "itinerario_detalle",
            id=nuevo.id
        )
    )

@app.route(
    "/itinerarios/<int:id>"
)
def itinerario_detalle(id):

    if "usuario_id" not in session:
        flash(
            "Debes iniciar sesión para ver tus itinerarios."
        )
        return redirect(
            url_for("login_usuario")
        )

    itinerario = ItinerarioViaje.query.get_or_404(
        id
    )

    if str(itinerario.usuario_id) != str(
        session["usuario_id"]
    ):
        flash(
            "No tienes permiso para ver este itinerario."
        )
        return redirect(
            url_for("itinerarios")
        )

    return render_template(
        "itinerario_detalle.html",
        itinerario=itinerario
    )

@app.route(
    "/itinerarios/eliminar/<int:id>"
)
def eliminar_itinerario(id):

    if "usuario_id" not in session:
        flash(
            "Debes iniciar sesión."
        )
        return redirect(
            url_for("login_usuario")
        )

    itinerario = ItinerarioViaje.query.get_or_404(
        id
    )

    if str(itinerario.usuario_id) != str(
        session["usuario_id"]
    ):
        flash(
            "No tienes permiso para eliminar este itinerario."
        )
        return redirect(
            url_for("itinerarios")
        )

    db.session.delete(itinerario)
    db.session.commit()

    flash(
        "Itinerario eliminado correctamente."
    )

    return redirect(
        url_for("itinerarios")
    )

@app.route(
    "/itinerarios/agregar_tour/<int:tour_id>",
    methods=["POST"]
)
def agregar_tour_itinerario(tour_id):

    if "usuario_id" not in session:
        flash(
            "Debes iniciar sesión para armar un itinerario."
        )
        return redirect(
            url_for("login_usuario")
        )

    tour = Tour.query.get_or_404(
        tour_id
    )

    itinerario_id = request.form.get(
        "itinerario_id"
    )

    fecha_programada = (
        request.form.get(
            "fecha_programada"
        )
        or None
    )

    if not itinerario_id:
        flash(
            "Elige o crea un itinerario primero."
        )
        return redirect(
            url_for(
                "detalle_tour",
                id=tour_id
            )
        )

    itinerario = ItinerarioViaje.query.get_or_404(
        int(itinerario_id)
    )

    if str(itinerario.usuario_id) != str(
        session["usuario_id"]
    ):
        flash(
            "No tienes permiso para usar este itinerario."
        )
        return redirect(
            url_for(
                "detalle_tour",
                id=tour_id
            )
        )

    ya_incluido = ItinerarioViajeTour.query.filter_by(
        itinerario_id=itinerario.id,
        tour_id=tour.id_tour
    ).first()

    if ya_incluido:
        flash(
            "Ese tour ya está en el itinerario."
        )
        return redirect(
            url_for(
                "itinerario_detalle",
                id=itinerario.id
            )
        )

    fecha = None

    if fecha_programada:
        fecha = datetime.strptime(
            fecha_programada,
            "%Y-%m-%d"
        ).date()

    item = ItinerarioViajeTour(
        itinerario_id=itinerario.id,
        tour_id=tour.id_tour,
        fecha_programada=fecha
    )

    db.session.add(item)
    db.session.commit()

    flash(
        "Tour agregado al itinerario."
    )

    return redirect(
        url_for(
            "itinerario_detalle",
            id=itinerario.id
        )
    )


@app.route(
    "/itinerarios/quitar_tour/<int:item_id>"
)
def quitar_tour_itinerario(item_id):

    item = ItinerarioViajeTour.query.get_or_404(
        item_id
    )

    itinerario = item.itinerario

    if itinerario.usuario_id != session.get(
        "usuario_id"
    ):
        flash("No autorizado.")
        return redirect(
            url_for("itinerarios")
        )

    db.session.delete(item)
    db.session.commit()

    flash(
        "Tour quitado del itinerario."
    )

    return redirect(
        url_for(
            "itinerario_detalle",
            id=itinerario.id
        )
    )


@app.route("/admin/login")
def admin_login():
    return render_template(
        "admin_login.html"
    )


@app.route("/admin/logout")
def admin_logout():

    session.clear()

    flash(
        "Sesión administrativa cerrada correctamente.",
        "success"
    )

    return redirect(
        url_for("admin_login")
    )


@app.route("/admin")
@admin_required
def admin_dashboard():

    return render_template(
        "admin_dashboard.html",
        total_usuarios=Usuario.query.count(),
        total_empresas=Empresa.query.count(),
        total_tours=Tour.query.count(),
        total_reservas=Reserva.query.count()
    )


@app.route(
    "/admin/parametros",
    methods=["GET", "POST"]
)
@admin_required
def admin_parametros():

    if request.method == "POST":

        parametros = ParametroSistema.query.all()

        for parametro in parametros:

            nuevo_valor = request.form.get(
                parametro.clave
            )

            if nuevo_valor is not None:
                parametro.valor = nuevo_valor

        db.session.commit()

        flash(
            "Parámetros del sistema actualizados."
        )

        return redirect(
            url_for("admin_parametros")
        )

    parametros = ParametroSistema.query.order_by(
        ParametroSistema.clave
    ).all()

    return render_template(
        "admin_parametros.html",
        parametros=parametros
    )


@app.route("/admin/comentarios")
@admin_required
def admin_comentarios():

    comentarios = (
        Comentario.query
        .order_by(
            Comentario.fecha.desc()
        )
        .all()
    )

    return render_template(
        "admin_comentarios.html",
        comentarios=comentarios
    )

@app.route(
    "/admin/comentarios/<int:id>/ocultar"
)
@admin_required
def admin_ocultar_comentario(id):

    comentario = Comentario.query.get_or_404(
        id
    )

    comentario.visible = not comentario.visible

    db.session.commit()

    flash(
        "Comentario ocultado."
        if not comentario.visible
        else "Comentario vuelto a mostrar."
    )

    return redirect(
        url_for("admin_comentarios")
    )

@app.route("/admin/usuarios")
@admin_required
def admin_usuarios():

    usuarios = Usuario.query.filter(
        Usuario.rol != "empresa"
    ).all()

    return render_template(
        "admin_usuarios.html",
        usuarios=usuarios
    )



@app.route(
    "/admin/eliminar_usuario/<string:id>"
)
@admin_required
def admin_eliminar_usuario(id):

    usuario = db.session.get(
        Usuario,
        id
    )

    if not usuario:
        flash(
            "Usuario no encontrado."
        )
        return redirect(
            url_for("admin_usuarios")
        )

    _borrar_relacionados_de_usuario(
        usuario
    )

    db.session.delete(usuario)
    db.session.commit()

    flash(
        "Usuario eliminado correctamente."
    )

    return redirect(
        url_for("admin_usuarios")
    )


@app.route("/admin_empresas")
@admin_required
def admin_empresas():

    empresas = Empresa.query.order_by(
        Empresa.id.desc()
    ).all()

    return render_template(
        "admin_empresas.html",
        empresas=empresas
    )
@app.route("/admin/tours")
@admin_required
def admin_tours():

    tours = Tour.query.all()

    print("========== ADMIN TOURS ==========")
    print("CANTIDAD DE TOURS:", len(tours))

    for tour in tours:
        print(
            "ID:",
            tour.id_tour,
            "| TITULO:",
            tour.titulo,
            "| CIUDAD:",
            tour.ciudad,
            "| ESTADO:",
            tour.estado
        )

    print("=================================")

    return render_template(
        "admin_tours.html",
        tours=tours
    )


@app.route(
    "/login_admin",
    methods=["POST"]
)
def admin_login_post():

    correo = request.form["correo"]
    password = request.form["password"]

    admin = Administrador.query.filter_by(
        correo=correo
    ).first()

    if admin and check_password_hash(
        admin.contrasena,
        password
    ):

        session.clear()

        session["admin_id"] = admin.id
        session["admin_nombre"] = admin.nombre

        return redirect(
            url_for("admin_dashboard")
        )

    flash(
        "Credenciales incorrectas"
    )

    return redirect(
        url_for("admin_login")
    )

@app.route(
    "/admin/cambiar_password",
    methods=["GET", "POST"]
)
@admin_required
def admin_cambiar_password():

    admin = db.session.get(
        Administrador,
        session["admin_id"]
    )

    if request.method == "POST":

        password_actual = request.form.get(
            "password_actual",
            ""
        )

        password_nueva = request.form.get(
            "password_nueva",
            ""
        )

        confirmar_password = request.form.get(
            "confirmar_password",
            ""
        )

        if not check_password_hash(
            admin.contrasena,
            password_actual
        ):
            flash(
                "La contraseña actual es incorrecta.",
                "danger"
            )

            return redirect(
                url_for("admin_cambiar_password")
            )

        if len(password_nueva) < 8:
            flash(
                "La nueva contraseña debe tener mínimo 8 caracteres.",
                "danger"
            )

            return redirect(
                url_for("admin_cambiar_password")
            )

        if password_nueva != confirmar_password:
            flash(
                "Las contraseñas nuevas no coinciden.",
                "danger"
            )

            return redirect(
                url_for("admin_cambiar_password")
            )

        if password_nueva == password_actual:
            flash(
                "La nueva contraseña debe ser diferente a la actual.",
                "danger"
            )

            return redirect(
                url_for("admin_cambiar_password")
            )

        admin.contrasena = generate_password_hash(
            password_nueva
        )

        db.session.commit()

        flash(
            "Contraseña actualizada correctamente.",
            "success"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "admin/cambiar_password.html"
    )
@app.route("/aprobar_empresa/<int:id>", methods=["POST"])
@admin_required
def aprobar_empresa(id):
    empresa = Empresa.query.get_or_404(id)

    empresa.datos_verificados = True
    empresa.nit_verificado = True
    empresa.contacto_verificado = True
    empresa.documentacion_verificada = True
    empresa.representante_verificado = True
    empresa.requisitos_verificados = True

    empresa.aprobado = True
    empresa.estado_verificacion = "verificada"
    empresa.revisado_por = session["admin_id"]
    empresa.fecha_revision = db.func.current_timestamp()
    empresa.motivo_revision = None

    db.session.commit()

    flash(
        "Empresa verificada y aprobada correctamente.",
        "success"
    )

    return redirect(url_for("admin_empresas"))

@app.route(
    "/eliminar_empresa_admin/<int:id>"
)
@admin_required
def eliminar_empresa_admin(id):

    empresa = Empresa.query.get_or_404(id)

    _borrar_relacionados_de_empresa(
        empresa
    )

    db.session.delete(empresa)

    db.session.commit()

    flash(
        "Empresa eliminada."
    )

    return redirect(
        url_for("admin_empresas")
    )
@app.route("/admin/empresas/revisar/<int:id>", methods=["GET", "POST"])
@admin_required
def revisar_empresa(id):
    empresa = Empresa.query.get_or_404(id)

    if request.method == "POST":
        empresa.datos_verificados = "datos_verificados" in request.form
        empresa.nit_verificado = "nit_verificado" in request.form
        empresa.contacto_verificado = "contacto_verificado" in request.form
        empresa.documentacion_verificada = "documentacion_verificada" in request.form
        empresa.representante_verificado = "representante_verificado" in request.form
        empresa.requisitos_verificados = "requisitos_verificados" in request.form

        empresa.estado_verificacion = "en_revision"
        empresa.revisado_por = session["admin_id"]
        empresa.fecha_revision = db.func.current_timestamp()

        todos_verificados = all([
            empresa.datos_verificados,
            empresa.nit_verificado,
            empresa.contacto_verificado,
            empresa.documentacion_verificada,
            empresa.representante_verificado,
            empresa.requisitos_verificados
        ])

        if todos_verificados:
            empresa.estado_verificacion = "en_revision"
            flash("Revisión guardada. Todos los requisitos están completos. Ahora puedes aprobar la empresa.", "success")
        else:
            flash("Revisión guardada. Faltan requisitos por verificar.", "warning")

        db.session.commit()

        return redirect(url_for("revisar_empresa", id=empresa.id))

    return render_template(
    "revisar_empresa.html",
    empresa=empresa
)
 


@app.route(
    "/eliminar_tour_admin/<int:id>"
)
@admin_required
def eliminar_tour_admin(id):

    tour = Tour.query.get_or_404(id)

    _borrar_relacionados_de_tour(
        tour
    )

    db.session.delete(tour)

    db.session.commit()

    flash(
        "Tour eliminado."
    )

    return redirect(
        url_for("admin_tours")
    )
@app.route("/aprobar_tour/<int:id>", methods=["POST"])
@admin_required
def aprobar_tour(id):

    tour = Tour.query.get_or_404(id)

    if not tour.operador:
        flash(
            "No se puede aprobar el tour porque no tiene un operador asociado.",
            "danger"
        )
        return redirect(url_for("admin_tours"))

    empresa = getattr(tour.operador, "empresa", None)

    if empresa and not empresa.aprobado:
        flash(
            "No se puede aprobar el tour porque la empresa del operador no está verificada.",
            "danger"
        )
        return redirect(url_for("admin_tours"))

    tour.estado = "activo"

    if hasattr(tour, "estado_verificacion"):
        tour.estado_verificacion = "verificada"

    if hasattr(tour, "datos_verificados"):
        tour.datos_verificados = True

    if hasattr(tour, "seguridad_verificada"):
        tour.seguridad_verificada = True

    if hasattr(tour, "ubicacion_verificada"):
        tour.ubicacion_verificada = True

    if hasattr(tour, "precio_verificado"):
        tour.precio_verificado = True

    if hasattr(tour, "cupos_verificados"):
        tour.cupos_verificados = True

    if hasattr(tour, "dificultad_verificada"):
        tour.dificultad_verificada = True

    if hasattr(tour, "accesibilidad_verificada"):
        tour.accesibilidad_verificada = True

    if hasattr(tour, "contenido_verificado"):
        tour.contenido_verificado = True

    if hasattr(tour, "requisitos_verificados"):
        tour.requisitos_verificados = True

    if hasattr(tour, "revisado_por"):
        tour.revisado_por = session["admin_id"]

    if hasattr(tour, "fecha_revision"):
        tour.fecha_revision = db.func.current_timestamp()

    if hasattr(tour, "motivo_revision"):
        tour.motivo_revision = None

    db.session.commit()

    flash(
        "Tour verificado y aprobado correctamente.",
        "success"
    )

    return redirect(url_for("admin_tours"))
@app.route("/empresa/dashboard")
def dashboard_empresa():

    if "empresa_id" not in session:
        return redirect(url_for("login_empresa"))

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash(
            "No se encontró el usuario operador asociado a esta empresa"
        )
        return redirect(
            url_for("login_empresa")
        )

    tours = Tour.query.filter_by(
        id_operador=usuario_operador.id_usuario
    ).all()

    total_tours = len(tours)

    tour_ids = [
        tour.id_tour
        for tour in tours
    ]

    reservas = (
        Reserva.query.filter(
            Reserva.id_tour.in_(tour_ids)
        ).all()
        if tour_ids
        else []
    )

    total_reservas = len(reservas)

    cupos_disponibles = sum(
        tour.cupo_disponible or 0
        for tour in tours
    )

    notificaciones_sin_leer = Notificacion.query.filter_by(
        empresa_id=empresa.id,
        leida=False
    ).count()

    solicitudes_guias = SolicitudGuia.query.filter_by(
        empresa_id=empresa.id,
        estado="pendiente"
    ).count()

    reservas_por_tour = []

    for tour in tours:

        cantidad_reservas = Reserva.query.filter_by(
            id_tour=tour.id_tour
        ).count()

        porcentaje = (
            (cantidad_reservas / total_reservas) * 100
            if total_reservas > 0
            else 0
        )

        if porcentaje < 8 and cantidad_reservas > 0:
            porcentaje = 8

        reservas_por_tour.append({
            "tour": tour,
            "reservas": cantidad_reservas,
            "porcentaje": round(porcentaje, 2)
        })

    reservas_por_tour.sort(
        key=lambda x: x["reservas"],
        reverse=True
    )

    tour_mas_popular = (
        reservas_por_tour[0]
        if reservas_por_tour
        and reservas_por_tour[0]["reservas"] > 0
        else None
    )

    return render_template(
        "dashboard_empresa.html",
        empresa=empresa,
        tours=tours,
        total_tours=total_tours,
        total_reservas=total_reservas,
        cupos_disponibles=cupos_disponibles,
        notificaciones_sin_leer=notificaciones_sin_leer,
        solicitudes_guias=solicitudes_guias,
        reservas_por_tour=reservas_por_tour,
        tour_mas_popular=tour_mas_popular
    )

@app.route("/solicitudes_guias")
def solicitudes_guias():

    if "empresa_id" not in session:
        return redirect(url_for("login_empresa"))

    solicitudes = SolicitudGuia.query.filter_by(
        empresa_id=session["empresa_id"],
        estado="pendiente"
    ).order_by(
        SolicitudGuia.fecha_solicitud.desc()
    ).all()

    return render_template(
        "solicitudes_guias.html",
        solicitudes=solicitudes
    )


@app.route("/aprobar_guia/<int:id_solicitud>", methods=["POST"])
def aprobar_guia(id_solicitud):

    if "empresa_id" not in session:
        return redirect(url_for("login_empresa"))

    solicitud = SolicitudGuia.query.filter_by(
        id_solicitud=id_solicitud,
        empresa_id=session["empresa_id"],
        estado="pendiente"
    ).first_or_404()

    guia = Usuario.query.filter_by(
        id_usuario=solicitud.id_guia,
        rol="guia"
    ).first_or_404()

    solicitud.estado = "aprobada"
    solicitud.fecha_respuesta = datetime.utcnow()
    guia.estado = "activo"

    db.session.commit()

    flash(
        f"La solicitud de {guia.nombre_completo} fue aprobada correctamente.",
        "success"
    )

    return redirect(url_for("solicitudes_guias"))


@app.route("/rechazar_guia/<int:id_solicitud>", methods=["POST"])
def rechazar_guia(id_solicitud):

    if "empresa_id" not in session:
        return redirect(url_for("login_empresa"))

    solicitud = SolicitudGuia.query.filter_by(
        id_solicitud=id_solicitud,
        empresa_id=session["empresa_id"],
        estado="pendiente"
    ).first_or_404()

    motivo = request.form.get(
        "motivo_rechazo",
        ""
    ).strip()

    solicitud.estado = "rechazada"
    solicitud.fecha_respuesta = datetime.utcnow()
    solicitud.motivo_rechazo = motivo

    db.session.commit()

    flash(
        "La solicitud del guía fue rechazada.",
        "warning"
    )

    return redirect(url_for("solicitudes_guias"))

@app.route("/empresa/notificaciones")
def notificaciones_empresa():

    if "empresa_id" not in session:
        return redirect(
            url_for("login_empresa")
        )

    notificaciones = (
        Notificacion.query
        .filter_by(
            empresa_id=session["empresa_id"]
        )
        .order_by(
            Notificacion.fecha.desc()
        )
        .all()
    )

    for notificacion in notificaciones:
        notificacion.leida = True

    db.session.commit()

    return render_template(
        "notificaciones_empresa.html",
        notificaciones=notificaciones
    )


@app.route(
    "/comentar/<int:reserva_id>",
    methods=["GET", "POST"]
)
def comentar(reserva_id):

    if "usuario_id" not in session:
        return redirect(url_for("login_usuario"))

    reserva = Reserva.query.get_or_404(reserva_id)

    if str(reserva.id_viajero) != str(session["usuario_id"]):
        flash("No tienes permiso.")
        return redirect(url_for("reservas"))

    if reserva.estado_reserva.lower() != "finalizada":
        flash("Solo puedes comentar tours finalizados.")
        return redirect(url_for("reservas"))

    existe = Comentario.query.filter_by(
        reserva_id=reserva.id_reserva
    ).first()

    if existe:
        flash("Ya calificaste este tour.")
        return redirect(url_for("reservas"))

    if request.method == "POST":

        ahora = datetime.now()

        comentario = Comentario(
            usuario_id=session["usuario_id"],
            tour_id=reserva.id_tour,
            reserva_id=reserva.id_reserva,
            calificacion=int(request.form["calificacion"]),
            comentario=request.form["comentario"],
            visible=True,
            fecha=ahora,
            created_at=ahora,
            updated_at=ahora
        )

        try:
            db.session.add(comentario)
            db.session.flush()

            usuario_operador = Usuario.query.get(
                reserva.tour.id_operador
            )

            if usuario_operador:
                empresa = Empresa.query.filter_by(
                    correo=usuario_operador.correo
                ).first()

                if empresa:
                    db.session.add(
                        Notificacion(
                            empresa_id=empresa.id,
                            tour_id=reserva.id_tour,
                            tipo="comentario",
                            mensaje=(
                                f'Tu tour "{reserva.tour.titulo}" '
                                f'recibió una calificación de '
                                f'{comentario.calificacion}/5.'
                            )
                        )
                    )

            db.session.commit()

            flash("Gracias por tu opinión.")

        except Exception:
            db.session.rollback()
            raise

        return redirect(url_for("reservas"))

    return render_template(
        "comentar.html",
        reserva=reserva
    )



@app.route(
    "/cancelar_reserva/<int:reserva_id>"
)
def cancelar_reserva(reserva_id):

    if "usuario_id" not in session:
        return redirect(
            url_for("login_usuario")
        )

    reserva = Reserva.query.get_or_404(
        reserva_id
    )

    if reserva.id_viajero != session["usuario_id"]:
        flash(
            "No tienes permiso para cancelar esta reserva."
        )
        return redirect(
            url_for("reservas")
        )

    if reserva.estado_reserva == "cancelada":
        flash(
            "Esta reserva ya fue cancelada."
        )
        return redirect(
            url_for("reservas")
        )

    reserva.estado_reserva = "cancelada"

    TransporteReserva.query.filter_by(
        reserva_id=reserva.id_reserva
    ).delete(synchronize_session=False)

    db.session.commit()

    flash(
        "Reserva cancelada correctamente."
    )

    return redirect(
        url_for("reservas")
    )


@app.route("/chat/<int:tour_id>")
def chat_tour(tour_id):

    if "usuario_id" not in session:
        flash(
            "Debes iniciar sesión."
        )
        return redirect(
            url_for("login_usuario")
        )

    tour = Tour.query.get_or_404(
        tour_id
    )

    usuario_operador = Usuario.query.get_or_404(
        tour.id_operador
    )

    empresa = Empresa.query.filter_by(
        correo=usuario_operador.correo
    ).first()

    if not empresa:
        flash(
            "No se encontró la empresa asociada al tour."
        )
        return redirect(
            url_for("principal")
        )

    conversacion = Conversacion.query.filter_by(
        usuario_id=session["usuario_id"],
        empresa_id=empresa.id,
        tour_id=tour.id_tour
    ).first()

    if not conversacion:

        conversacion = Conversacion(
            usuario_id=session["usuario_id"],
            empresa_id=empresa.id,
            tour_id=tour.id_tour
        )

        db.session.add(
            conversacion
        )

        db.session.commit()

    return redirect(
        url_for(
            "ver_chat",
            conversacion_id=conversacion.id
        )
    )
@app.route(
    "/chat/ver/<int:conversacion_id>",
    methods=["GET", "POST"]
)
def ver_chat(conversacion_id):

    if "usuario_id" not in session:
        flash(
            "Debes iniciar sesión."
        )
        return redirect(
            url_for("login_usuario")
        )

    conversacion = Conversacion.query.get_or_404(
        conversacion_id
    )

    usuario_id = session["usuario_id"]

    if str(conversacion.usuario_id) != str(usuario_id):
        flash(
            "No tienes permiso para ver esta conversación."
        )
        return redirect(
            url_for("tours")
        )

    mensajes = (
        Mensaje.query
        .filter_by(
            conversacion_id=conversacion.id
        )
        .order_by(
            Mensaje.fecha
        )
        .all()
    )

    return render_template(
        "chat.html",
        conversacion=conversacion,
        mensajes=mensajes
    )


@app.route(
    "/enviar_mensaje/<int:conversacion_id>",
    methods=["POST"]
)
def enviar_mensaje(conversacion_id):

    if "usuario_id" not in session:
        return redirect(
            url_for("login_usuario")
        )

    conversacion = Conversacion.query.get_or_404(
        conversacion_id
    )

    usuario_id = session["usuario_id"]

    if str(conversacion.usuario_id) != str(usuario_id):
        flash(
            "No tienes permiso para escribir "
            "en esta conversación."
        )
        return redirect(
            url_for("tours")
        )

    texto = request.form["mensaje"]

    nuevo = Mensaje(
        conversacion_id=conversacion.id,
        remitente="usuario",
        mensaje=texto
    )

    db.session.add(nuevo)
    db.session.commit()

    return redirect(
        url_for(
            "ver_chat",
            conversacion_id=conversacion.id
        )
    )


@app.route("/chats_empresa")
def chats_empresa():

    if "empresa_id" not in session:
        return redirect(
            url_for("login_empresa")
        )

    conversaciones = Conversacion.query.filter_by(
        empresa_id=session["empresa_id"]
    ).all()

    return render_template(
        "chats_empresa.html",
        conversaciones=conversaciones
    )


@app.route(
    "/empresa/chat/<int:conversacion_id>",
    methods=["GET", "POST"]
)
def chat_empresa(conversacion_id):

    if "empresa_id" not in session:
        return redirect(
            url_for("login_empresa")
        )

    conversacion = Conversacion.query.get_or_404(
        conversacion_id
    )

    if conversacion.empresa_id != session["empresa_id"]:
        flash(
            "No tienes permiso para ver esta conversación."
        )
        return redirect(
            url_for("chats_empresa")
        )

    if request.method == "POST":

        nuevo = Mensaje(
            conversacion_id=conversacion.id,
            remitente="empresa",
            mensaje=request.form["mensaje"]
        )

        db.session.add(nuevo)
        db.session.commit()

        return redirect(
            url_for(
                "chat_empresa",
                conversacion_id=conversacion.id
            )
        )

    mensajes = (
        Mensaje.query
        .filter_by(
            conversacion_id=conversacion.id
        )
        .order_by(
            Mensaje.fecha
        )
        .all()
    )

    return render_template(
        "chat_empresa.html",
        conversacion=conversacion,
        mensajes=mensajes
    )

@app.route("/detalle_tour/<int:id>")
def detalle_tour(id):

    tour = Tour.query.get_or_404(id)

    if tour.estado != "activo" and "admin_id" not in session:
        flash(
            "Este tour todavía no está disponible para los viajeros.",
            "warning"
        )
        return redirect(url_for("tours"))

    itinerarios = []

    if "usuario_id" in session:
        itinerarios = (
            ItinerarioViaje.query
            .filter_by(
                usuario_id=session["usuario_id"]
            )
            .order_by(
                ItinerarioViaje.fecha_creacion.desc()
            )
            .all()
        )

    comentarios = (
        Comentario.query
        .filter_by(
            tour_id=tour.id_tour
        )
        .order_by(
            Comentario.created_at.desc()
        )
        .all()
    )

    calificaciones = [
        c.calificacion
        for c in comentarios
        if c.calificacion is not None
    ]

    promedio_calificacion = (
        round(
            sum(calificaciones) / len(calificaciones),
            1
        )
        if calificaciones
        else None
    )

    return render_template(
        "detalle_tour.html",
        tour=tour,
        itinerarios=itinerarios,
        comentarios=comentarios,
        promedio_calificacion=promedio_calificacion
    )

@app.route("/guardar_tour_usuario/<int:tour_id>", methods=["POST"])
def guardar_tour_usuario(tour_id):

    if "usuario_id" not in session:
        flash("Debes iniciar sesión.")
        return redirect(url_for("login_usuario"))

    tour = Tour.query.get_or_404(tour_id)

    existe = Guardado.query.filter_by(
        usuario_id=session["usuario_id"],
        tour_id=tour.id_tour
    ).first()

    if existe:
        db.session.delete(existe)
        db.session.commit()

        flash("Tour eliminado de guardados.")

    else:
        nuevo = Guardado(
            usuario_id=session["usuario_id"],
            tour_id=tour.id_tour
        )

        db.session.add(nuevo)
        db.session.commit()

        flash("Tour guardado correctamente.")

    return redirect(
        request.referrer or url_for("tours")
    )

@app.route("/asistente")
def asistente():

    return render_template(
        "asistente.html"
    )

@app.route("/api/asistente", methods=["POST"])
def api_asistente():

    print("===================================")
    print("ENTRÓ A /api/asistente")

    try:

        datos = request.get_json()

        print("DATOS RECIBIDOS:", datos)

        mensaje = datos.get("mensaje", "").strip()

        print("MENSAJE RECIBIDO:", mensaje)

        if not mensaje:
            return jsonify({
                "error": "Escribe un mensaje."
            }), 400

        tours = Tour.query.filter(
            Tour.estado == "activo",
            Tour.cupo_disponible > 0
        ).all()

        print("TOURS DISPONIBLES:", len(tours))

        if not tours:

            return jsonify({
                "respuesta": "Actualmente no hay tours disponibles con cupos."
            })

        prompt = f"""
Eres el asistente virtual de Zuqara Tours.

El usuario escribió:
"{mensaje}"

Estos son los tours disponibles actualmente:

"""

        for tour in tours:

            prompt += f"""
ID: {tour.id_tour}
Título: {tour.titulo}
Ciudad: {tour.ciudad}
Descripción: {tour.descripcion}
Precio: ${tour.precio}
Cupos disponibles: {tour.cupo_disponible}
Dificultad: {tour.dificultad}
Acceso para silla de ruedas: {"Sí" if tour.acceso_rampa else "No"}
Baños cercanos: {"Sí" if tour.banos_cercanos else "No"}
"""

        prompt += """

IMPORTANTE:
- Solo puedes recomendar tours que aparecen en la lista.
- No inventes tours.
- Si el usuario menciona una ciudad, presupuesto, cantidad de personas,
  niños, adultos mayores, dificultad o accesibilidad, tenlo en cuenta.
- Si ningún tour coincide exactamente, indícalo y muestra las opciones
  disponibles más relacionadas.
- Responde en español de forma clara y amigable.
"""

        print("PROBANDO GEMINI...")

        try:

            chat = client.chats.create(
                model="gemini-3.6-flash"
            )

            print("CHAT CREADO")

            respuesta = chat.send_message(
                mensaje + "\n\n" + prompt
            )

            print("GEMINI RESPONDIÓ")

            texto = respuesta.text

            print("RESPUESTA:", texto)

            return jsonify({
                "respuesta": texto
            })

        except Exception as error_gemini:

            print("===================================")
            print("GEMINI NO DISPONIBLE")
            print(type(error_gemini).__name__)
            print(error_gemini)
            print("USANDO RESPALDO...")
            print("===================================")

            respuesta_respaldo = (
                "🤖 El asistente IA está temporalmente limitado, "
                "pero encontré estas opciones disponibles:\n\n"
            )

            for tour in tours:

                respuesta_respaldo += (
                    f"📍 {tour.titulo}\n"
                    f"Ciudad: {tour.ciudad}\n"
                    f"Precio: ${tour.precio:,.0f}\n"
                    f"Cupos disponibles: {tour.cupo_disponible}\n"
                    f"Dificultad: {tour.dificultad or 'No especificada'}\n\n"
                )

            return jsonify({
                "respuesta": respuesta_respaldo
            })

    except Exception as e:

        print("===================================")
        print("ERROR DEL ASISTENTE")
        print(type(e).__name__)
        print(e)
        print("===================================")

        return jsonify({
            "error": str(e)
        }), 500

@app.route("/cambiar_estado_tour/<int:tour_id>")
def cambiar_estado_tour(tour_id):

    if "empresa_id" not in session:
        flash("Debes iniciar sesión como empresa.")
        return redirect(url_for("login_empresa"))

    empresa = Empresa.query.get_or_404(
        session["empresa_id"]
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash("No se encontró el usuario operador asociado a la empresa.")
        return redirect(url_for("login_empresa"))

    tour = Tour.query.get_or_404(tour_id)

    if tour.id_operador != usuario_operador.id_usuario:
        flash("No tienes permiso para cambiar el estado de este tour.")
        return redirect(url_for("mis_tours"))

    if tour.estado == "activo":
        tour.estado = "inactivo"
    else:
        tour.estado = "activo"

    db.session.commit()

    flash("Estado del tour actualizado correctamente.")

    return redirect(url_for("mis_tours"))
@app.route("/dashboard_guia")
def dashboard_guia():

    if "usuario_id" not in session:
        return redirect(url_for("login_usuario"))

    usuario = Usuario.query.filter_by(
        id_usuario=session["usuario_id"],
        rol="guia"
    ).first()

    if not usuario:
        session.clear()
        flash("No tienes permisos para acceder a este panel.", "danger")
        return redirect(url_for("login_usuario"))

    solicitud = SolicitudGuia.query.filter_by(
        id_guia=usuario.id_usuario,
        estado="aprobada"
    ).order_by(
        SolicitudGuia.fecha_respuesta.desc()
    ).first()

    if not solicitud:
        flash(
            "Tu cuenta todavía no ha sido aprobada por una empresa.",
            "warning"
        )
        return redirect(url_for("login_usuario"))

    guia = Guia.query.filter_by(
        id_guia=usuario.id_usuario
    ).first()

    return render_template(
        "dashboard_guia.html",
        usuario=usuario,
        guia=guia,
        solicitud=solicitud
    )
@app.route("/login-guia")
def login_guia():
    return render_template("login_guia.html")


@app.route("/login-guia", methods=["POST"])
def login_guia_post():

    correo = request.form["correo"]
    password = request.form["password"]

    usuario = Usuario.query.filter_by(
        correo=correo,
        rol="guia"
    ).first()

    if not usuario:
        flash(
            "No existe una cuenta registrada como guía turístico.",
            "danger"
        )
        return redirect(url_for("login_guia"))

    if not check_password_hash(
        usuario.contrasenia_hash,
        password
    ):
        flash(
            "Correo o contraseña incorrectos.",
            "danger"
        )
        return redirect(url_for("login_guia"))

    if usuario.estado == "pendiente":
        flash(
            "Tu cuenta está pendiente de aprobación por la empresa.",
            "warning"
        )
        return redirect(url_for("login_guia"))

    if usuario.estado != "activo":
        flash(
            "Tu cuenta de guía no está activa.",
            "danger"
        )
        return redirect(url_for("login_guia"))

    session["usuario_id"] = str(
        usuario.id_usuario
    )

    session["usuario_nombre"] = usuario.nombre_completo

    return redirect(
        url_for("dashboard_guia")
    )
@app.route("/guia/perfil")
def perfil_guia():

    if "usuario_id" not in session:
        return redirect(url_for("login_guia"))

    usuario = Usuario.query.filter_by(
        id_usuario=session["usuario_id"],
        rol="guia"
    ).first_or_404()

    guia = Guia.query.filter_by(
        id_guia=usuario.id_usuario
    ).first()

    if not guia:
        flash(
            "No se encontró el perfil del guía.",
            "danger"
        )
        return redirect(url_for("dashboard_guia"))

    return render_template(
        "perfil_guia.html",
        usuario=usuario,
        guia=guia
    )


@app.route("/guia/perfil", methods=["POST"])
def actualizar_perfil_guia():

    if "usuario_id" not in session:
        return redirect(url_for("login_guia"))

    usuario = Usuario.query.filter_by(
        id_usuario=session["usuario_id"],
        rol="guia"
    ).first_or_404()

    guia = Guia.query.filter_by(
        id_guia=usuario.id_usuario
    ).first()

    if not guia:
        flash(
            "No se encontró el perfil del guía.",
            "danger"
        )
        return redirect(url_for("dashboard_guia"))

    nombre = request.form.get(
        "nombre_completo",
        ""
    ).strip()

    telefono = request.form.get(
        "telefono",
        ""
    ).strip()

    especialidad = request.form.get(
        "especialidad",
        ""
    ).strip()

    ciudad_base = request.form.get(
        "ciudad_base",
        ""
    ).strip()

    experiencia = request.form.get(
        "experiencia",
        ""
    ).strip()

    descripcion = request.form.get(
        "descripcion",
        ""
    ).strip()

    if not nombre:
        flash(
            "El nombre completo es obligatorio.",
            "danger"
        )
        return redirect(url_for("perfil_guia"))

    usuario.nombre_completo = nombre
    usuario.telefono = telefono

    guia.especialidad = especialidad
    guia.ciudad_base = ciudad_base
    guia.experiencia = experiencia
    guia.descripcion = descripcion

    session["usuario_nombre"] = usuario.nombre_completo

    db.session.commit()

    flash(
        "Tu perfil fue actualizado correctamente.",
        "success"
    )

    return redirect(url_for("perfil_guia"))
@app.route("/guia/tours")
def mis_tours_guia():

    if "usuario_id" not in session:
        return redirect(url_for("login_guia"))

    usuario = Usuario.query.filter_by(
        id_usuario=session["usuario_id"],
        rol="guia",
        estado="activo"
    ).first_or_404()

    asignaciones = AsignacionGuia.query.filter_by(
        id_guia=usuario.id_usuario,
        estado="activo"
    ).order_by(
        AsignacionGuia.fecha_asignacion.desc()
    ).all()

    return render_template(
        "mis_tours_guia.html",
        usuario=usuario,
        asignaciones=asignaciones
    )
@app.route("/guia/agenda")
def agenda_guia():

    if "usuario_id" not in session:
        return redirect(url_for("login_guia"))

    usuario = Usuario.query.filter_by(
        id_usuario=session["usuario_id"],
        rol="guia",
        estado="activo"
    ).first_or_404()

    asignaciones = AsignacionGuia.query.filter_by(
        id_guia=usuario.id_usuario,
        estado="activo"
    ).order_by(
        AsignacionGuia.fecha_asignacion.asc()
    ).all()

    return render_template(
        "agenda_guia.html",
        usuario=usuario,
        asignaciones=asignaciones
    )

@app.route("/empresa/guias")
def guias_empresa():

    if "empresa_id" not in session:
        return redirect(url_for("login_empresa"))

    empresa_id = session["empresa_id"]

    solicitudes = SolicitudGuia.query.filter_by(
        empresa_id=empresa_id,
        estado="aprobada"
    ).all()

    guia_ids = [
        solicitud.id_guia
        for solicitud in solicitudes
    ]

    guias = Usuario.query.filter(
        Usuario.id_usuario.in_(guia_ids),
        Usuario.rol == "guia",
        Usuario.estado == "activo"
    ).all() if guia_ids else []

    perfiles_lista = Guia.query.filter(
        Guia.id_guia.in_(guia_ids)
    ).all() if guia_ids else []

    perfiles = {
        str(perfil.id_guia): perfil
        for perfil in perfiles_lista
    }

    return render_template(
        "guias_empresa.html",
        guias=guias,
        perfiles=perfiles
    )    
@app.route("/empresa/asignar-tour/<uuid:id_guia>")
def asignar_tour_guia(id_guia):

    if "empresa_id" not in session:
        return redirect(url_for("login_empresa"))

    empresa_id = session["empresa_id"]

    solicitud = SolicitudGuia.query.filter_by(
        id_guia=id_guia,
        empresa_id=empresa_id,
        estado="aprobada"
    ).first()

    if not solicitud:
        flash(
            "Este guía no pertenece a tu empresa o no está aprobado.",
            "danger"
        )
        return redirect(url_for("guias_empresa"))

    guia = Usuario.query.filter_by(
        id_usuario=id_guia,
        rol="guia",
        estado="activo"
    ).first_or_404()

    empresa = Empresa.query.get_or_404(
        empresa_id
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash(
            "No se encontró el usuario operador asociado a la empresa.",
            "danger"
        )
        return redirect(url_for("guias_empresa"))

    tours = Tour.query.filter_by(
        id_operador=usuario_operador.id_usuario,
        estado="activo"
    ).order_by(
        Tour.titulo.asc()
    ).all()

    asignaciones = AsignacionGuia.query.filter_by(
        id_guia=id_guia,
        empresa_id=empresa_id
    ).all()

    tours_asignados = {
        asignacion.id_tour
        for asignacion in asignaciones
        if asignacion.estado == "activo"
    }

    return render_template(
        "asignar_tour_guia.html",
        guia=guia,
        tours=tours,
        tours_asignados=tours_asignados
    )
@app.route("/empresa/asignar-tour/<uuid:id_guia>", methods=["POST"])
def guardar_asignacion_tour(id_guia):

    if "empresa_id" not in session:
        return redirect(url_for("login_empresa"))

    empresa_id = session["empresa_id"]

    solicitud = SolicitudGuia.query.filter_by(
        id_guia=id_guia,
        empresa_id=empresa_id,
        estado="aprobada"
    ).first()

    if not solicitud:
        flash(
            "No puedes asignar tours a este guía.",
            "danger"
        )
        return redirect(url_for("guias_empresa"))

    guia = Usuario.query.filter_by(
        id_usuario=id_guia,
        rol="guia",
        estado="activo"
    ).first_or_404()

    id_tour = request.form.get("id_tour")

    if not id_tour:
        flash(
            "Debes seleccionar un tour.",
            "danger"
        )
        return redirect(
            url_for(
                "asignar_tour_guia",
                id_guia=id_guia
            )
        )

    empresa = Empresa.query.get_or_404(
        empresa_id
    )

    usuario_operador = Usuario.query.filter_by(
        correo=empresa.correo
    ).first()

    if not usuario_operador:
        flash(
            "No se encontró el usuario operador de la empresa.",
            "danger"
        )
        return redirect(url_for("guias_empresa"))

    tour = Tour.query.filter_by(
        id_tour=id_tour,
        id_operador=usuario_operador.id_usuario,
        estado="activo"
    ).first()

    if not tour:
        flash(
            "El tour seleccionado no pertenece a tu empresa.",
            "danger"
        )
        return redirect(
            url_for(
                "asignar_tour_guia",
                id_guia=id_guia
            )
        )

    asignacion_existente = AsignacionGuia.query.filter_by(
        id_guia=id_guia,
        id_tour=tour.id_tour
    ).first()

    if asignacion_existente:

        if asignacion_existente.estado == "activo":
            flash(
                "Este tour ya está asignado a este guía.",
                "warning"
            )
            return redirect(
                url_for(
                    "asignar_tour_guia",
                    id_guia=id_guia
                )
            )

        asignacion_existente.estado = "activo"
        asignacion_existente.empresa_id = empresa_id
        asignacion_existente.fecha_asignacion = datetime.utcnow()

    else:

        nueva_asignacion = AsignacionGuia(
            id_guia=id_guia,
            id_tour=tour.id_tour,
            empresa_id=empresa_id,
            estado="activo"
        )

        db.session.add(nueva_asignacion)

    db.session.commit()

    flash(
        f"El tour '{tour.titulo}' fue asignado correctamente a {guia.nombre_completo}.",
        "success"
    )

    return redirect(
        url_for(
            "asignar_tour_guia",
            id_guia=id_guia
        )
    )

@app.route("/guia/viajeros")
def viajeros_guia():

    if "usuario_id" not in session:
        return redirect(url_for("login_guia"))

    usuario = Usuario.query.filter_by(
        id_usuario=session["usuario_id"],
        rol="guia",
        estado="activo"
    ).first_or_404()

    asignaciones = AsignacionGuia.query.filter_by(
        id_guia=usuario.id_usuario,
        estado="activo"
    ).all()

    tour_ids = [
        asignacion.id_tour
        for asignacion in asignaciones
    ]

    reservas = Reserva.query.filter(
        Reserva.id_tour.in_(tour_ids),
        Reserva.estado_reserva == "confirmada"
    ).order_by(
        Reserva.fecha_reserva.desc()
    ).all() if tour_ids else []

    return render_template(
        "viajeros_guia.html",
        usuario=usuario,
        reservas=reservas
    )
@app.route("/guia/calificaciones")
def calificaciones_guia():

    if "usuario_id" not in session:
        return redirect(url_for("login_guia"))

    usuario = Usuario.query.filter_by(
        id_usuario=session["usuario_id"],
        rol="guia",
        estado="activo"
    ).first_or_404()

    calificaciones = CalificacionTour.query.filter_by(
        id_guia=usuario.id_usuario
    ).order_by(
        CalificacionTour.fecha_calificacion.desc()
    ).all()

    total = len(calificaciones)

    promedio = (
        sum(calificacion.puntuacion for calificacion in calificaciones) / total
        if total > 0
        else 0
    )

    estrellas = {
        5: sum(1 for c in calificaciones if c.puntuacion == 5),
        4: sum(1 for c in calificaciones if c.puntuacion == 4),
        3: sum(1 for c in calificaciones if c.puntuacion == 3),
        2: sum(1 for c in calificaciones if c.puntuacion == 2),
        1: sum(1 for c in calificaciones if c.puntuacion == 1)
    }

    return render_template(
        "calificaciones_guia.html",
        usuario=usuario,
        calificaciones=calificaciones,
        total=total,
        promedio=round(promedio, 1),
        estrellas=estrellas
    )