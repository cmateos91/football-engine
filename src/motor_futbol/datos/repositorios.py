"""Repositorios MySQL para el esquema football_engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.sql.base import Executable

from motor_futbol.compartido.configuracion import Configuracion
from motor_futbol.datos.catalogo_mapeo import (
    VERSION_MAPEO_FOOTBALL_ENGINE,
    obtener_columnas_esperadas,
)
from motor_futbol.datos.conexion_bd import crear_motor_bd
from motor_futbol.datos.filas_crudas import FilaEquipoCruda, FilaJugadorCruda
from motor_futbol.datos.mapeadores import mapear_equipo_con_plantilla
from motor_futbol.dominio import Equipo


@dataclass(slots=True)
class RepositorioFootballEngine:
    """Repositorio principal de lectura para football_engine."""

    motor: Engine
    version_mapeo: str = VERSION_MAPEO_FOOTBALL_ENGINE

    @classmethod
    def desde_configuracion(cls, configuracion: Configuracion) -> RepositorioFootballEngine:
        return cls(motor=crear_motor_bd(configuracion))

    def listar_equipos_crudos(self) -> tuple[FilaEquipoCruda, ...]:
        consulta = text(f"SELECT {_seleccionar_columnas('Equipo')} FROM `Equipo` ORDER BY `id` ASC")
        filas = self._ejecutar_y_convertir(consulta)
        return tuple(FilaEquipoCruda.desde_mapping(fila) for fila in filas)

    def obtener_equipo_crudo_por_id(self, id_equipo: int) -> FilaEquipoCruda:
        consulta = text(
            f"SELECT {_seleccionar_columnas('Equipo')} FROM `Equipo` WHERE `id` = :id_equipo"
        )
        fila = self._ejecutar_una(consulta, {"id_equipo": id_equipo})
        if fila is None:
            raise LookupError(f"No existe el equipo con id {id_equipo}.")
        return FilaEquipoCruda.desde_mapping(fila)

    def obtener_equipo_crudo_por_nombre(self, nombre_equipo: str) -> FilaEquipoCruda:
        consulta = text(
            "SELECT "
            f"{_seleccionar_columnas('Equipo')} "
            "FROM `Equipo` "
            "WHERE `nombre` = :nombre_equipo"
        )
        fila = self._ejecutar_una(consulta, {"nombre_equipo": nombre_equipo})
        if fila is None:
            raise LookupError(f"No existe el equipo con nombre {nombre_equipo!r}.")
        return FilaEquipoCruda.desde_mapping(fila)

    def listar_jugadores_crudos_por_equipo(self, id_equipo: int) -> tuple[FilaJugadorCruda, ...]:
        consulta = text(
            f"""
            SELECT {_seleccionar_columnas("Jugador")}
            FROM `Jugador`
            WHERE `equipoId` = :id_equipo
            ORDER BY `overall` DESC, `nombre` ASC
            """
        )
        filas = self._ejecutar_y_convertir(consulta, {"id_equipo": id_equipo})
        return tuple(FilaJugadorCruda.desde_mapping(fila) for fila in filas)

    def obtener_equipo_por_id(self, id_equipo: int) -> Equipo:
        fila_equipo = self.obtener_equipo_crudo_por_id(id_equipo)
        jugadores = self.listar_jugadores_crudos_por_equipo(id_equipo)
        return mapear_equipo_con_plantilla(fila_equipo, jugadores)

    def obtener_equipo_por_nombre(self, nombre_equipo: str) -> Equipo:
        fila_equipo = self.obtener_equipo_crudo_por_nombre(nombre_equipo)
        jugadores = self.listar_jugadores_crudos_por_equipo(fila_equipo.id)
        return mapear_equipo_con_plantilla(fila_equipo, jugadores)

    def listar_equipos(self) -> tuple[Equipo, ...]:
        equipos_crudos = self.listar_equipos_crudos()
        return tuple(self.obtener_equipo_por_id(fila.id) for fila in equipos_crudos)

    def _ejecutar_y_convertir(
        self, consulta: Executable, parametros: Mapping[str, object] | None = None
    ) -> tuple[dict[str, object], ...]:
        with self.motor.connect() as conexion:
            resultado = conexion.execute(consulta, parametros or {})
            return tuple(dict(fila) for fila in resultado.mappings())

    def _ejecutar_una(
        self, consulta: Executable, parametros: Mapping[str, object] | None = None
    ) -> dict[str, object] | None:
        filas = self._ejecutar_y_convertir(consulta, parametros)
        if not filas:
            return None
        return filas[0]


def _seleccionar_columnas(tabla: str) -> str:
    columnas = obtener_columnas_esperadas(tabla)
    return ", ".join(f"`{columna}`" for columna in columnas)
