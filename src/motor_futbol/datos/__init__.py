"""Modulo para acceso a datos y mapeo desde fuentes externas."""

from motor_futbol.datos.catalogo_mapeo import (
    DEFINICIONES_COLUMNAS_EQUIPO,
    DEFINICIONES_COLUMNAS_JUGADOR,
    VERSION_MAPEO_FOOTBALL_ENGINE,
    DefinicionColumna,
    FamiliaColumna,
    obtener_columnas_esperadas,
    obtener_definiciones_estadisticas_jugador,
    obtener_definiciones_tabla,
    validar_catalogo_con_dominio,
)
from motor_futbol.datos.conexion_bd import (
    EstadoConexionBD,
    crear_motor_bd,
    inspeccionar_estado_basico_bd,
)
from motor_futbol.datos.esquema import (
    ColumnaTabla,
    InventarioEsquema,
    TablaEsquema,
    inspeccionar_esquema_bd,
)
from motor_futbol.datos.filas_crudas import FilaEquipoCruda, FilaJugadorCruda
from motor_futbol.datos.mapeadores import (
    mapear_equipo_con_plantilla,
    mapear_fila_equipo_a_dominio,
    mapear_fila_jugador_a_dominio,
)
from motor_futbol.datos.repositorios import RepositorioFootballEngine

__all__ = [
    "DEFINICIONES_COLUMNAS_EQUIPO",
    "DEFINICIONES_COLUMNAS_JUGADOR",
    "VERSION_MAPEO_FOOTBALL_ENGINE",
    "ColumnaTabla",
    "DefinicionColumna",
    "EstadoConexionBD",
    "FamiliaColumna",
    "FilaEquipoCruda",
    "FilaJugadorCruda",
    "InventarioEsquema",
    "RepositorioFootballEngine",
    "TablaEsquema",
    "crear_motor_bd",
    "inspeccionar_esquema_bd",
    "inspeccionar_estado_basico_bd",
    "mapear_equipo_con_plantilla",
    "mapear_fila_equipo_a_dominio",
    "mapear_fila_jugador_a_dominio",
    "obtener_columnas_esperadas",
    "obtener_definiciones_estadisticas_jugador",
    "obtener_definiciones_tabla",
    "validar_catalogo_con_dominio",
]
