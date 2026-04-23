"""Conexion minima a la base de datos del proyecto."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from motor_futbol.compartido.configuracion import Configuracion


@dataclass(frozen=True, slots=True)
class EstadoConexionBD:
    """Resume el estado minimo de la base de datos configurada."""

    nombre_bd: str
    tablas: tuple[str, ...]
    total_equipos: int
    total_jugadores: int


def crear_motor_bd(configuracion: Configuracion) -> Engine:
    """Crea un motor SQLAlchemy a partir de la configuracion actual."""

    if not configuracion.base_de_datos_configurada or configuracion.url_bd is None:
        raise ValueError("La variable URL_BD es obligatoria para conectar a la base de datos.")

    return create_engine(configuracion.url_bd, future=True)


def inspeccionar_estado_basico_bd(configuracion: Configuracion) -> EstadoConexionBD:
    """Comprueba que la BD responda y devuelve el estado minimo esperado."""

    motor = crear_motor_bd(configuracion)

    with motor.connect() as conexion:
        nombre_bd = _leer_nombre_bd(conexion)
        tablas = _leer_tablas(conexion)
        total_equipos = _contar_registros(conexion, tabla="Equipo")
        total_jugadores = _contar_registros(conexion, tabla="Jugador")

    return EstadoConexionBD(
        nombre_bd=nombre_bd,
        tablas=tablas,
        total_equipos=total_equipos,
        total_jugadores=total_jugadores,
    )


def _leer_nombre_bd(conexion: Connection) -> str:
    fila = conexion.execute(text("SELECT DATABASE()")).one()
    nombre_bd = fila[0]
    if not isinstance(nombre_bd, str) or nombre_bd.strip() == "":
        raise ValueError("No se pudo determinar el nombre de la base de datos activa.")
    return nombre_bd


def _leer_tablas(conexion: Connection) -> tuple[str, ...]:
    filas = conexion.execute(text("SHOW TABLES")).all()
    tablas = tuple(str(fila[0]) for fila in filas)
    if not tablas:
        raise ValueError("La base de datos no contiene tablas visibles.")
    return tablas


def _contar_registros(conexion: Connection, *, tabla: str) -> int:
    fila = conexion.execute(text(f"SELECT COUNT(*) FROM `{tabla}`")).one()
    total = fila[0]
    if not isinstance(total, int):
        raise TypeError(f"El conteo de la tabla {tabla} no devolvio un entero.")
    return total
