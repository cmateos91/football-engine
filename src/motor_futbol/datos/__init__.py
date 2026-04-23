"""Modulo para acceso a datos y mapeo desde fuentes externas."""

from motor_futbol.datos.conexion_bd import (
    EstadoConexionBD,
    crear_motor_bd,
    inspeccionar_estado_basico_bd,
)

__all__ = [
    "EstadoConexionBD",
    "crear_motor_bd",
    "inspeccionar_estado_basico_bd",
]
