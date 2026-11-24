from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id_usuario = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    nombre_completo = db.Column(
        db.String(120),
        nullable=False
    )

    correo = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    contrasenia_hash = db.Column(
        db.String(255),
        nullable=False
    )

    telefono = db.Column(
        db.String(20)
    )

    rol = db.Column(
        db.String(20),
        nullable=False
    )

    estado = db.Column(
        db.String(20),
        default="activo"
    )

    foto = db.Column(
        db.String(255),
        nullable=True
    )

    creado_en = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.current_timestamp()
    )



class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(60),
        unique=True,
        nullable=False
    )

    icono = db.Column(
        db.String(60)
    )

    tours = db.relationship(
        "Tour",
        backref="categoria",
        lazy=True
    )

class Tour(db.Model):
    __tablename__ = "tours"

    id_tour = db.Column(
        db.Integer,
        primary_key=True
    )

    id_operador = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("usuarios.id_usuario"),
        nullable=False
    )

    id_categoria = db.Column(
        db.Integer,
        db.ForeignKey("categorias.id"),
        nullable=False
    )

    titulo = db.Column(
        db.String(200),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=False
    )

    incluye = db.Column(
        db.Text,
        nullable=True
    )

    precio = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    cupo_maximo = db.Column(
        db.Integer,
        nullable=False
    )

    cupo_disponible = db.Column(
        db.Integer,
        nullable=False
    )

    dificultad = db.Column(
        db.String(50)
    )

    acceso_rampa = db.Column(
        db.Boolean,
        default=False
    )

    banos_cercanos = db.Column(
        db.Boolean,
        default=False
    )

    estado = db.Column(
        db.String(30),
        default="activo"
    )

    creado_en = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.current_timestamp()
    )

    ciudad = db.Column(
        db.String(100),
        nullable=False,
        default="No especificada"
    )

    operador = db.relationship(
        "Usuario",
        backref="tours_operados",
        lazy=True
    )


class Reserva(db.Model):
    __tablename__ = "reservas"

    id_reserva = db.Column(
        db.Integer,
        primary_key=True
    )

    id_viajero = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("usuarios.id_usuario"),
        nullable=False
    )

    id_tour = db.Column(
        db.Integer,
        db.ForeignKey("tours.id_tour"),
        nullable=False
    )

    cantidad_personas = db.Column(
        db.Integer,
        nullable=False
    )

    total_pago = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    estado_reserva = db.Column(
        db.String(20),
        default="confirmada"
    )

    fecha_reserva = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.current_timestamp()
    )

    tour = db.relationship(
        "Tour",
        backref="reservas"
    )

    viajero = db.relationship(
        "Usuario",
        backref="reservas"
    )

class TransporteReserva(db.Model):
    """Datos del transporte ficticio asociado a una reserva."""
    __tablename__ = "transporte_reservas"

    id = db.Column(db.Integer, primary_key=True)
    reserva_id = db.Column(
        db.Integer, db.ForeignKey("reservas.id_reserva"),
        nullable=False, unique=True, index=True
    )
    tipo_transporte = db.Column(db.String(20), nullable=False)
    origen = db.Column(db.String(120), nullable=False)
    destino = db.Column(db.String(120), nullable=False)
    fecha_viaje = db.Column(db.Date, nullable=False)
    hora_salida = db.Column(db.String(5), nullable=False)
    token_verificacion = db.Column(db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)

    reserva = db.relationship(
        "Reserva",
        backref=db.backref("transporte", uselist=False, cascade="all, delete-orphan")
    )


class AsientoTransporte(db.Model):
    """Un asiento ficticio reservado para un servicio y horario."""
    __tablename__ = "asientos_transporte"
    __table_args__ = (
        UniqueConstraint(
            "tipo_transporte", "origen", "destino",
            "fecha_viaje", "hora_salida", "asiento",
            name="uq_asiento_servicio_fecha_hora"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    transporte_reserva_id = db.Column(
        db.Integer, db.ForeignKey("transporte_reservas.id"),
        nullable=False, index=True
    )
    tipo_transporte = db.Column(db.String(20), nullable=False)
    origen = db.Column(db.String(120), nullable=False)
    destino = db.Column(db.String(120), nullable=False)
    fecha_viaje = db.Column(db.Date, nullable=False)
    hora_salida = db.Column(db.String(5), nullable=False)
    asiento = db.Column(db.String(5), nullable=False)

    transporte = db.relationship(
        "TransporteReserva",
        backref=db.backref("asientos", cascade="all, delete-orphan", lazy=True)
    )


class Favorito(db.Model):
    __tablename__ = "favoritos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("usuarios.id_usuario"),
        nullable=False
    )

    tour_id = db.Column(
        db.Integer,
        db.ForeignKey("tours.id_tour"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    usuario = db.relationship(
        "Usuario",
        backref="favoritos"
    )

    tour = db.relationship(
        "Tour",
        backref="favoritos"
    )


class Administrador(db.Model):
    __tablename__ = "administradores"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    correo = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    contrasena = db.Column(
        "contraseña",
        db.String(255),
        nullable=False
    )

class Empresa(db.Model):
    __tablename__ = "empresas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(120),
        nullable=False
    )

    nit = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    correo = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    telefono = db.Column(
        db.String(20),
        nullable=False
    )

    direccion = db.Column(
        db.String(200),
        nullable=False
    )

    contrasena = db.Column(
        "contraseña",
        db.String(255),
        nullable=False
    )

    aprobado = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    estado_verificacion = db.Column(
        db.String(30),
        default="pendiente",
        nullable=False
    )

    datos_verificados = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    nit_verificado = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    contacto_verificado = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    documentacion_verificada = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    representante_verificado = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    requisitos_verificados = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    motivo_revision = db.Column(
        db.Text,
        nullable=True
    )

    revisado_por = db.Column(
        db.Integer,
        nullable=True
    )

    fecha_revision = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.current_timestamp()
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )



class Comentario(db.Model):
    __tablename__ = "comentarios"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("usuarios.id_usuario"),
        nullable=False
    )

    tour_id = db.Column(
        db.Integer,
        db.ForeignKey("tours.id_tour"),
        nullable=False
    )

    reserva_id = db.Column(
        db.Integer,
        db.ForeignKey("reservas.id_reserva"),
        nullable=False
    )

    calificacion = db.Column(
        db.Integer
    )

    comentario = db.Column(
        db.Text
    )

    visible = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    fecha = db.Column(
        db.DateTime(timezone=True)
    )

    created_at = db.Column(
        db.DateTime(timezone=True)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True)
    )

    usuario = db.relationship(
        "Usuario",
        backref="comentarios"
    )

    tour = db.relationship(
        "Tour",
        backref="comentarios"
    )

    reserva = db.relationship(
        "Reserva",
        backref="comentarios"
    )

class Conversacion(db.Model):
    __tablename__ = "conversaciones"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("usuarios.id_usuario"),
        nullable=False
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    tour_id = db.Column(
        db.Integer,
        db.ForeignKey("tours.id_tour"),
        nullable=False
    )

    usuario = db.relationship(
        "Usuario"
    )

    empresa = db.relationship(
        "Empresa"
    )

    tour = db.relationship(
        "Tour"
    )


class Mensaje(db.Model):
    __tablename__ = "mensajes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    conversacion_id = db.Column(
        db.Integer,
        db.ForeignKey("conversaciones.id"),
        nullable=False
    )

    remitente = db.Column(
        db.String(20)
    )

    mensaje = db.Column(
        db.Text
    )

    fecha = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    conversacion = db.relationship(
        "Conversacion",
        backref="mensajes"
    )


class ItinerarioViaje(db.Model):
    __tablename__ = "itinerarios_viaje"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("usuarios.id_usuario"),
        nullable=False
    )

    nombre = db.Column(
        db.String(120),
        nullable=False
    )

    fecha_inicio = db.Column(
        db.Date
    )

    fecha_fin = db.Column(
        db.Date
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    usuario = db.relationship(
        "Usuario",
        backref="itinerarios"
    )

    tours_incluidos = db.relationship(
        "ItinerarioViajeTour",
        backref="itinerario",
        cascade="all, delete-orphan",
        order_by="ItinerarioViajeTour.fecha_programada"
    )



class ItinerarioViajeTour(db.Model):
    __tablename__ = "itinerario_viaje_tours"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    itinerario_id = db.Column(
        db.Integer,
        db.ForeignKey("itinerarios_viaje.id"),
        nullable=False
    )

    tour_id = db.Column(
        db.Integer,
        db.ForeignKey("tours.id_tour"),
        nullable=False
    )

    fecha_programada = db.Column(
        db.Date
    )

    tour = db.relationship(
        "Tour"
    )


class PerfilViajero(db.Model):
    __tablename__ = "perfiles_viajero"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("usuarios.id_usuario"),
        nullable=False,
        unique=True
    )

    nivel_actividad = db.Column(
        db.String(20),
        default="Moderado"
    )

    viaja_con = db.Column(
        db.String(40)
    )

    requiere_accesibilidad = db.Column(
        db.Boolean,
        default=False
    )

    restricciones_alimenticias = db.Column(
        db.String(255)
    )

    presupuesto_promedio = db.Column(
        db.Float
    )

    notas = db.Column(
        db.Text
    )

    fecha_actualizacion = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    usuario = db.relationship(
        "Usuario",
        backref=db.backref(
            "perfil_viajero",
            uselist=False,
            cascade="all, delete-orphan"
        )
    )



class Pago(db.Model):
    __tablename__ = "pagos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    reserva_id = db.Column(
        db.Integer,
        db.ForeignKey("reservas.id_reserva"),
        nullable=False,
        unique=True
    )

    monto = db.Column(
        db.Float,
        nullable=False
    )

    metodo_pago = db.Column(
        db.String(30)
    )

    referencia = db.Column(
        db.String(80)
    )

    estado = db.Column(
        db.String(20),
        default="Aprobado"
    )

    fecha_pago = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    reserva = db.relationship(
        "Reserva",
        backref=db.backref(
            "pago",
            uselist=False,
            cascade="all, delete-orphan"
        )
    )


class IntentoPagoSimulado(db.Model):
    """Historial de intentos de pago de demostración; nunca procesa dinero real."""
    __tablename__ = "intentos_pago_simulado"

    id = db.Column(db.Integer, primary_key=True)
    reserva_id = db.Column(
        db.Integer,
        db.ForeignKey("reservas.id_reserva"),
        nullable=False,
        index=True
    )
    metodo_pago = db.Column(db.String(40), nullable=False)
    estado = db.Column(db.String(20), nullable=False)
    referencia = db.Column(db.String(40), unique=True, nullable=False)
    fecha_intento = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    reserva = db.relationship(
        "Reserva",
        backref=db.backref("intentos_pago_simulado", lazy=True)
    )


class TourImagen(db.Model):
    __tablename__ = "tour_imagenes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tour_id = db.Column(
        db.Integer,
        db.ForeignKey("tours.id_tour"),
        nullable=False
    )

    url = db.Column(
        db.String(255),
        nullable=False
    )

    orden = db.Column(
        db.Integer,
        default=0
    )

    tour = db.relationship(
        "Tour",
        backref=db.backref(
            "imagenes",
            cascade="all, delete-orphan",
            order_by="TourImagen.orden"
        )
    )


class ItinerarioTourDia(db.Model):
    __tablename__ = "itinerario_tour_dias"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tour_id = db.Column(
        db.Integer,
        db.ForeignKey("tours.id_tour"),
        nullable=False
    )

    numero_dia = db.Column(
        db.Integer,
        nullable=False
    )

    titulo = db.Column(
        db.String(120)
    )

    descripcion = db.Column(
        db.Text
    )

    tour = db.relationship(
        "Tour",
        backref=db.backref(
            "itinerario_dias",
            cascade="all, delete-orphan",
            order_by="ItinerarioTourDia.numero_dia"
        )
    )


class Notificacion(db.Model):
    __tablename__ = "notificaciones"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    tour_id = db.Column(
        db.Integer,
        db.ForeignKey("tours.id_tour"),
        nullable=True
    )

    tipo = db.Column(
        db.String(30)
    )

    mensaje = db.Column(
        db.String(255),
        nullable=False
    )

    leida = db.Column(
        db.Boolean,
        default=False
    )

    fecha = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    empresa = db.relationship(
        "Empresa",
        backref=db.backref(
            "notificaciones",
            cascade="all, delete-orphan"
        )
    )

    tour = db.relationship(
        "Tour"
    )


class ParametroSistema(db.Model):
    __tablename__ = "parametros_sistema"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    clave = db.Column(
        db.String(80),
        nullable=False,
        unique=True
    )

    valor = db.Column(
        db.String(255)
    )

    descripcion = db.Column(
        db.String(255)
    )


class PasajeroReserva(db.Model):
    __tablename__ = "pasajeros_reserva"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    reserva_id = db.Column(
        db.Integer,
        db.ForeignKey("reservas.id_reserva"),
        nullable=False
    )

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    tipo_documento = db.Column(
        db.String(30),
        nullable=False
    )

    documento = db.Column(
        db.String(30),
        nullable=False
    )

    telefono = db.Column(
        db.String(20),
        nullable=False
    )

    tipo = db.Column(
        db.String(20),
        nullable=False
    )

    reserva = db.relationship(
        "Reserva",
        backref=db.backref(
            "pasajeros",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )
class Guardado(db.Model):
    __tablename__ = "guardados"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("usuarios.id_usuario"),
        nullable=False
    )

    tour_id = db.Column(
        db.Integer,
        db.ForeignKey("tours.id_tour"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.current_timestamp()
    )

    usuario = db.relationship(
        "Usuario",
        backref="guardados"
    )

    tour = db.relationship(
        "Tour",
        backref="guardados"
    )
class Guia(db.Model):
    __tablename__ = "guias"

    id_guia = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("usuarios.id_usuario", ondelete="CASCADE"),
        primary_key=True
    )

    experiencia = db.Column(db.Text)
    especialidad = db.Column(db.String(150))
    ciudad_base = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    disponible = db.Column(db.Boolean, default=True)
    creado_en = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )
class SolicitudGuia(db.Model):
    __tablename__ = "solicitudes_guia"

    id_solicitud = db.Column(
        db.Integer,
        primary_key=True
    )

    id_guia = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "empresas.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="pendiente"
    )

    fecha_solicitud = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    fecha_respuesta = db.Column(
        db.DateTime,
        nullable=True
    )

    motivo_rechazo = db.Column(
        db.Text,
        nullable=True
    )

    guia = db.relationship(
        "Usuario",
        foreign_keys=[id_guia]
    )

    perfil_guia = db.relationship(
        "Guia",
        foreign_keys=[id_guia],
        primaryjoin="SolicitudGuia.id_guia == Guia.id_guia",
        uselist=False,
        viewonly=True,
        overlaps="guia"
    )

    empresa = db.relationship(
        "Empresa"
    )
class AsignacionGuia(db.Model):
    __tablename__ = "asignaciones_guia"

    id_asignacion = db.Column(
        db.Integer,
        primary_key=True
    )

    id_guia = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    id_tour = db.Column(
        db.Integer,
        db.ForeignKey(
            "tours.id_tour",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "empresas.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    fecha_asignacion = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="activo"
    )

    guia = db.relationship(
        "Usuario",
        foreign_keys=[id_guia]
    )

    tour = db.relationship(
        "Tour",
        foreign_keys=[id_tour]
    )

    empresa = db.relationship(
        "Empresa",
        foreign_keys=[empresa_id]
    )
class CalificacionTour(db.Model):
    __tablename__ = "calificaciones_tour"

    id_calificacion = db.Column(
        db.Integer,
        primary_key=True
    )

    id_reserva = db.Column(
        db.Integer,
        db.ForeignKey(
            "reservas.id_reserva",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True
    )

    id_viajero = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    id_tour = db.Column(
        db.Integer,
        db.ForeignKey(
            "tours.id_tour",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    id_guia = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    puntuacion = db.Column(
        db.Integer,
        nullable=False
    )

    comentario = db.Column(
        db.Text,
        nullable=True
    )

    fecha_calificacion = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.current_timestamp()
    )

    reserva = db.relationship(
        "Reserva",
        foreign_keys=[id_reserva]
    )

    viajero = db.relationship(
        "Usuario",
        foreign_keys=[id_viajero]
    )

    tour = db.relationship(
        "Tour",
        foreign_keys=[id_tour]
    )

    guia = db.relationship(
        "Usuario",
        foreign_keys=[id_guia]
    )