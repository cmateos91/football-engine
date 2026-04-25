"""Catalogo y versionado del mapeo desde football_engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from motor_futbol.dominio.atributos import AtributosJugador

VERSION_MAPEO_FOOTBALL_ENGINE = "football_engine.v1"


class FamiliaColumna(StrEnum):
    """Familias semanticas de columnas dentro del origen de datos."""

    IDENTIDAD = "Identidad"
    PERFIL = "Perfil"
    FISICO = "Fisico"
    REGATE = "Regate"
    DEFENSA = "Defensa"
    PORTERIA = "Porteria"
    PASE = "Pase"
    DISPARO = "Disparo"


@dataclass(frozen=True, slots=True)
class DefinicionColumna:
    """Describe como una columna del origen se proyecta al dominio."""

    tabla: str
    columna: str
    destino: str
    familia: FamiliaColumna
    obligatorio: bool

    @property
    def es_estadistica(self) -> bool:
        return self.destino.startswith("atributos.")

    @property
    def nombre_atributo(self) -> str | None:
        if not self.es_estadistica:
            return None
        return self.destino.split(".", maxsplit=1)[1]


DEFINICIONES_COLUMNAS_EQUIPO: tuple[DefinicionColumna, ...] = (
    DefinicionColumna("Equipo", "id", "id", FamiliaColumna.IDENTIDAD, True),
    DefinicionColumna("Equipo", "nombre", "nombre", FamiliaColumna.IDENTIDAD, True),
)

DEFINICIONES_COLUMNAS_JUGADOR: tuple[DefinicionColumna, ...] = (
    DefinicionColumna("Jugador", "id", "id", FamiliaColumna.IDENTIDAD, True),
    DefinicionColumna("Jugador", "nombre", "nombre", FamiliaColumna.IDENTIDAD, True),
    DefinicionColumna("Jugador", "posicion", "posicion", FamiliaColumna.PERFIL, True),
    DefinicionColumna("Jugador", "overall", "overall", FamiliaColumna.PERFIL, True),
    DefinicionColumna("Jugador", "equipoId", "id_equipo", FamiliaColumna.IDENTIDAD, True),
    DefinicionColumna(
        "Jugador", "aceleracion", "atributos.aceleracion", FamiliaColumna.FISICO, True
    ),
    DefinicionColumna(
        "Jugador", "agresividad", "atributos.agresividad", FamiliaColumna.DEFENSA, True
    ),
    DefinicionColumna("Jugador", "cabeza", "atributos.cabeza", FamiliaColumna.DEFENSA, True),
    DefinicionColumna("Jugador", "reflejos", "atributos.reflejos", FamiliaColumna.PORTERIA, True),
    DefinicionColumna("Jugador", "regate", "atributos.regate", FamiliaColumna.REGATE, True),
    DefinicionColumna(
        "Jugador", "resistencia", "atributos.resistencia", FamiliaColumna.FISICO, True
    ),
    DefinicionColumna("Jugador", "salto", "atributos.salto", FamiliaColumna.FISICO, True),
    DefinicionColumna("Jugador", "tackles", "atributos.tackles", FamiliaColumna.DEFENSA, True),
    DefinicionColumna("Jugador", "velocidad", "atributos.velocidad", FamiliaColumna.FISICO, True),
    DefinicionColumna("Jugador", "alcance", "atributos.alcance", FamiliaColumna.PORTERIA, True),
    DefinicionColumna("Jugador", "atrape", "atributos.atrape", FamiliaColumna.PORTERIA, True),
    DefinicionColumna(
        "Jugador",
        "awareness_defensivo",
        "atributos.awareness_defensivo",
        FamiliaColumna.DEFENSA,
        True,
    ),
    DefinicionColumna(
        "Jugador",
        "awareness_ofensivo",
        "atributos.awareness_ofensivo",
        FamiliaColumna.PERFIL,
        True,
    ),
    DefinicionColumna(
        "Jugador",
        "awareness_portero",
        "atributos.awareness_portero",
        FamiliaColumna.PORTERIA,
        True,
    ),
    DefinicionColumna(
        "Jugador",
        "contacto_fisico",
        "atributos.contacto_fisico",
        FamiliaColumna.FISICO,
        True,
    ),
    DefinicionColumna(
        "Jugador",
        "control_balon",
        "atributos.control_balon",
        FamiliaColumna.REGATE,
        True,
    ),
    DefinicionColumna("Jugador", "efecto", "atributos.efecto", FamiliaColumna.PASE, True),
    DefinicionColumna(
        "Jugador",
        "engagement_defensivo",
        "atributos.engagement_defensivo",
        FamiliaColumna.DEFENSA,
        True,
    ),
    DefinicionColumna(
        "Jugador",
        "equilibrio",
        "atributos.equilibrio",
        FamiliaColumna.REGATE,
        True,
    ),
    DefinicionColumna(
        "Jugador",
        "finalizacion",
        "atributos.finalizacion",
        FamiliaColumna.DISPARO,
        True,
    ),
    DefinicionColumna(
        "Jugador",
        "lanzamiento_falta",
        "atributos.lanzamiento_falta",
        FamiliaColumna.PASE,
        True,
    ),
    DefinicionColumna("Jugador", "pase_bajo", "atributos.pase_bajo", FamiliaColumna.PASE, True),
    DefinicionColumna(
        "Jugador",
        "pase_elevado",
        "atributos.pase_elevado",
        FamiliaColumna.PASE,
        True,
    ),
    DefinicionColumna(
        "Jugador",
        "posesion_cerrada",
        "atributos.posesion_cerrada",
        FamiliaColumna.REGATE,
        True,
    ),
    DefinicionColumna(
        "Jugador",
        "potencia_tiro",
        "atributos.potencia_tiro",
        FamiliaColumna.DISPARO,
        True,
    ),
    DefinicionColumna("Jugador", "rechazo", "atributos.rechazo", FamiliaColumna.PORTERIA, True),
    DefinicionColumna("Jugador", "edad", "edad", FamiliaColumna.PERFIL, False),
    DefinicionColumna("Jugador", "nacionalidad", "nacionalidad", FamiliaColumna.PERFIL, False),
    DefinicionColumna("Jugador", "pie_fuerte", "pie_dominante", FamiliaColumna.PERFIL, False),
    DefinicionColumna("Jugador", "altura", "altura_cm", FamiliaColumna.PERFIL, False),
    DefinicionColumna("Jugador", "peso", "peso_kg", FamiliaColumna.PERFIL, False),
)

DEFINICIONES_POR_TABLA: tuple[DefinicionColumna, ...] = (
    *DEFINICIONES_COLUMNAS_EQUIPO,
    *DEFINICIONES_COLUMNAS_JUGADOR,
)


def obtener_columnas_esperadas(tabla: str) -> tuple[str, ...]:
    """Devuelve las columnas catalogadas para una tabla dada."""

    return tuple(
        definicion.columna for definicion in DEFINICIONES_POR_TABLA if definicion.tabla == tabla
    )


def obtener_definiciones_tabla(tabla: str) -> tuple[DefinicionColumna, ...]:
    """Devuelve las definiciones registradas para una tabla."""

    return tuple(definicion for definicion in DEFINICIONES_POR_TABLA if definicion.tabla == tabla)


def obtener_definiciones_estadisticas_jugador() -> tuple[DefinicionColumna, ...]:
    """Devuelve solo las columnas estadisticas del jugador."""

    return tuple(
        definicion for definicion in DEFINICIONES_COLUMNAS_JUGADOR if definicion.es_estadistica
    )


def validar_catalogo_con_dominio() -> None:
    """Asegura que el catalogo estadistico sigue cubriendo el dominio."""

    atributos_catalogados = {
        definicion.nombre_atributo
        for definicion in obtener_definiciones_estadisticas_jugador()
        if definicion.nombre_atributo is not None
    }
    atributos_dominio = set(AtributosJugador.nombres_campos())
    if atributos_catalogados != atributos_dominio:
        raise ValueError("El catalogo de columnas del jugador ya no coincide con AtributosJugador.")
