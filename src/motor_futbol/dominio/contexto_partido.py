"""Contexto base de un partido antes de iniciar la simulacion."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from motor_futbol.dominio.alineacion import Alineacion
from motor_futbol.dominio.equipo import Equipo
from motor_futbol.dominio.validaciones import (
    normalizar_cadena_opcional,
    obtener_cadena,
    obtener_cadena_opcional,
    obtener_entero_opcional,
    obtener_mapeo,
    obtener_mapeo_opcional,
    validar_cadena_no_vacia,
    validar_entero_opcional_en_rango,
)


@dataclass(frozen=True, slots=True)
class ContextoPartido:
    """Describe todo lo necesario para preparar un partido."""

    competicion: str
    temporada: str
    equipo_local: Equipo
    equipo_visitante: Equipo
    alineacion_local: Alineacion | None = None
    alineacion_visitante: Alineacion | None = None
    jornada: int | None = None
    semilla: int | None = None
    estadio: str | None = None

    def __post_init__(self) -> None:
        validar_cadena_no_vacia("competicion", self.competicion)
        validar_cadena_no_vacia("temporada", self.temporada)
        validar_entero_opcional_en_rango("jornada", self.jornada, minimo=1, maximo=99)
        validar_entero_opcional_en_rango("semilla", self.semilla, minimo=0, maximo=2_147_483_647)

        object.__setattr__(self, "competicion", self.competicion.strip())
        object.__setattr__(self, "temporada", self.temporada.strip())
        object.__setattr__(self, "estadio", normalizar_cadena_opcional(self.estadio))

        if self.equipo_local.id == self.equipo_visitante.id:
            raise ValueError("El equipo local y visitante deben ser distintos.")

        if (
            self.alineacion_local is not None
            and self.alineacion_local.id_equipo != self.equipo_local.id
        ):
            raise ValueError("La alineacion local no corresponde al equipo local.")
        if (
            self.alineacion_visitante is not None
            and self.alineacion_visitante.id_equipo != self.equipo_visitante.id
        ):
            raise ValueError("La alineacion visitante no corresponde al equipo visitante.")

    def a_dict(self) -> dict[str, object]:
        return {
            "competicion": self.competicion,
            "temporada": self.temporada,
            "equipo_local": self.equipo_local.a_dict(),
            "equipo_visitante": self.equipo_visitante.a_dict(),
            "alineacion_local": (
                self.alineacion_local.a_dict() if self.alineacion_local is not None else None
            ),
            "alineacion_visitante": (
                self.alineacion_visitante.a_dict()
                if self.alineacion_visitante is not None
                else None
            ),
            "jornada": self.jornada,
            "semilla": self.semilla,
            "estadio": self.estadio,
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, object]) -> ContextoPartido:
        datos_alineacion_local = obtener_mapeo_opcional(datos, "alineacion_local")
        datos_alineacion_visitante = obtener_mapeo_opcional(datos, "alineacion_visitante")

        return cls(
            competicion=obtener_cadena(datos, "competicion"),
            temporada=obtener_cadena(datos, "temporada"),
            equipo_local=Equipo.desde_dict(obtener_mapeo(datos, "equipo_local")),
            equipo_visitante=Equipo.desde_dict(obtener_mapeo(datos, "equipo_visitante")),
            alineacion_local=(
                Alineacion.desde_dict(datos_alineacion_local)
                if datos_alineacion_local is not None
                else None
            ),
            alineacion_visitante=(
                Alineacion.desde_dict(datos_alineacion_visitante)
                if datos_alineacion_visitante is not None
                else None
            ),
            jornada=obtener_entero_opcional(datos, "jornada"),
            semilla=obtener_entero_opcional(datos, "semilla"),
            estadio=obtener_cadena_opcional(datos, "estadio"),
        )
