"""Modelos de salida del baseline de simulacion."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from motor_futbol.dominio import (
    Alineacion,
    ContextoPartido,
    Coordenada,
    EstadoEspacialPartido,
    EstadoPartido,
    EventoPartido,
)
from motor_futbol.dominio.validaciones import (
    obtener_cadena,
    obtener_entero,
    obtener_mapeo,
    validar_entero_en_rango,
    validar_identificador,
)


@dataclass(frozen=True, slots=True)
class EstadisticasEquipoPartido:
    """Resumen agregado del partido por equipo."""

    equipo_id: int
    nombre_equipo: str
    posesiones: int
    posesion_pct: float
    tiros: int
    tiros_a_puerta: int
    goles: int
    faltas: int
    corners: int
    tarjetas_amarillas: int
    tarjetas_rojas: int
    energia_media: float
    energia_minima: float

    def __post_init__(self) -> None:
        validar_identificador("equipo_id", self.equipo_id)
        validar_entero_en_rango("posesiones", self.posesiones, minimo=0, maximo=300)
        validar_entero_en_rango("tiros", self.tiros, minimo=0, maximo=100)
        validar_entero_en_rango("tiros_a_puerta", self.tiros_a_puerta, minimo=0, maximo=100)
        validar_entero_en_rango("goles", self.goles, minimo=0, maximo=50)
        validar_entero_en_rango("faltas", self.faltas, minimo=0, maximo=100)
        validar_entero_en_rango("corners", self.corners, minimo=0, maximo=50)
        validar_entero_en_rango("tarjetas_amarillas", self.tarjetas_amarillas, minimo=0, maximo=20)
        validar_entero_en_rango("tarjetas_rojas", self.tarjetas_rojas, minimo=0, maximo=11)
        if self.tiros_a_puerta > self.tiros:
            raise ValueError("Los tiros a puerta no pueden superar los tiros totales.")
        if self.goles > self.tiros_a_puerta:
            raise ValueError("Los goles no pueden superar los tiros a puerta.")
        if not 0.0 <= self.posesion_pct <= 100.0:
            raise ValueError("La posesion debe estar entre 0 y 100.")
        if not 0.0 <= self.energia_media <= 100.0:
            raise ValueError("La energia media debe estar entre 0 y 100.")
        if not 0.0 <= self.energia_minima <= 100.0:
            raise ValueError("La energia minima debe estar entre 0 y 100.")
        if self.energia_minima > self.energia_media:
            raise ValueError("La energia minima no puede superar la energia media.")

    def a_dict(self) -> dict[str, object]:
        return {
            "equipo_id": self.equipo_id,
            "nombre_equipo": self.nombre_equipo,
            "posesiones": self.posesiones,
            "posesion_pct": self.posesion_pct,
            "tiros": self.tiros,
            "tiros_a_puerta": self.tiros_a_puerta,
            "goles": self.goles,
            "faltas": self.faltas,
            "corners": self.corners,
            "tarjetas_amarillas": self.tarjetas_amarillas,
            "tarjetas_rojas": self.tarjetas_rojas,
            "energia_media": self.energia_media,
            "energia_minima": self.energia_minima,
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, object]) -> EstadisticasEquipoPartido:
        return cls(
            equipo_id=obtener_entero(datos, "equipo_id"),
            nombre_equipo=obtener_cadena(datos, "nombre_equipo"),
            posesiones=obtener_entero(datos, "posesiones"),
            posesion_pct=_obtener_flotante(datos, "posesion_pct"),
            tiros=obtener_entero(datos, "tiros"),
            tiros_a_puerta=obtener_entero(datos, "tiros_a_puerta"),
            goles=obtener_entero(datos, "goles"),
            faltas=obtener_entero(datos, "faltas"),
            corners=obtener_entero(datos, "corners"),
            tarjetas_amarillas=obtener_entero(datos, "tarjetas_amarillas"),
            tarjetas_rojas=obtener_entero(datos, "tarjetas_rojas"),
            energia_media=_obtener_flotante(datos, "energia_media"),
            energia_minima=_obtener_flotante(datos, "energia_minima"),
        )


@dataclass(frozen=True, slots=True)
class ParametrosSimulacionBaseline:
    """Parametros ajustables del baseline."""

    posesiones_base: int = 180
    variacion_posesiones: int = 30

    probabilidad_base_tiro: float = 0.20
    probabilidad_base_tiro_fuera_zona: float = 0.08
    probabilidad_base_tiro_puerta: float = 0.32

    probabilidad_base_gol: float = 1.95

    probabilidad_base_corner: float = 0.42
    probabilidad_centro: float = 0.04

    probabilidad_base_falta: float = 0.06
    probabilidad_penalti: float = 0.45
    probabilidad_amarilla: float = 0.08
    probabilidad_roja: float = 0.001

    probabilidad_contraataque: float = 0.008

    coste_energia_equipo_poseedor: float = 0.46
    coste_energia_equipo_defensor: float = 0.22

    def __post_init__(self) -> None:
        validar_entero_en_rango("posesiones_base", self.posesiones_base, minimo=30, maximo=300)
        validar_entero_en_rango(
            "variacion_posesiones", self.variacion_posesiones, minimo=0, maximo=100
        )
        for nombre in (
            "probabilidad_base_tiro",
            "probabilidad_base_tiro_fuera_zona",
            "probabilidad_base_tiro_puerta",
            "probabilidad_base_corner",
            "probabilidad_centro",
            "probabilidad_base_falta",
            "probabilidad_penalti",
            "probabilidad_amarilla",
            "probabilidad_roja",
            "probabilidad_contraataque",
        ):
            valor = getattr(self, nombre)
            if not 0.0 <= valor <= 1.0:
                raise ValueError(f"{nombre} debe estar entre 0 y 1.")
        if not 0.0 <= self.probabilidad_base_gol <= 5.0:
            raise ValueError("probabilidad_base_gol debe estar entre 0 y 5.0")
        for nombre in ("coste_energia_equipo_poseedor", "coste_energia_equipo_defensor"):
            valor = getattr(self, nombre)
            if not 0.0 <= valor <= 5.0:
                raise ValueError(f"{nombre} debe estar entre 0 y 5.")


@dataclass(frozen=True, slots=True)
class ResultadoSimulacionPartido:
    """Salida estructurada de una simulacion baseline."""

    contexto: ContextoPartido
    semilla: int
    parametros: ParametrosSimulacionBaseline
    alineacion_local: Alineacion
    alineacion_visitante: Alineacion
    estado_final: EstadoPartido
    estado_espacial: EstadoEspacialPartido
    estadisticas_local: EstadisticasEquipoPartido
    estadisticas_visitante: EstadisticasEquipoPartido

    def __post_init__(self) -> None:
        if self.estado_final.goles_local != self.estadisticas_local.goles:
            raise ValueError(
                "Los goles locales del estado final no coinciden con las estadisticas."
            )
        if self.estado_final.goles_visitante != self.estadisticas_visitante.goles:
            raise ValueError(
                "Los goles visitantes del estado final no coinciden con las estadisticas."
            )
        posesion_total = (
            self.estadisticas_local.posesion_pct + self.estadisticas_visitante.posesion_pct
        )
        if round(posesion_total, 3) != 100.0:
            raise ValueError("La posesion total del partido debe sumar 100.")

    @property
    def total_goles(self) -> int:
        return self.estadisticas_local.goles + self.estadisticas_visitante.goles

    @property
    def total_tiros(self) -> int:
        return self.estadisticas_local.tiros + self.estadisticas_visitante.tiros

    @property
    def total_posesiones(self) -> int:
        return self.estadisticas_local.posesiones + self.estadisticas_visitante.posesiones

    def a_dict(self) -> dict[str, object]:
        return {
            "contexto": self.contexto.a_dict(),
            "semilla": self.semilla,
            "alineacion_local": self.alineacion_local.a_dict(),
            "alineacion_visitante": self.alineacion_visitante.a_dict(),
            "estado_final": self.estado_final.a_dict(),
            "estado_espacial": self.estado_espacial.a_dict(),
            "estadisticas_local": self.estadisticas_local.a_dict(),
            "estadisticas_visitante": self.estadisticas_visitante.a_dict(),
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, object]) -> ResultadoSimulacionPartido:
        return cls(
            contexto=ContextoPartido.desde_dict(obtener_mapeo(datos, "contexto")),
            semilla=obtener_entero(datos, "semilla"),
            parametros=ParametrosSimulacionBaseline(),
            alineacion_local=Alineacion.desde_dict(obtener_mapeo(datos, "alineacion_local")),
            alineacion_visitante=Alineacion.desde_dict(
                obtener_mapeo(datos, "alineacion_visitante")
            ),
            estado_final=EstadoPartido.desde_dict(obtener_mapeo(datos, "estado_final")),
            estado_espacial=EstadoEspacialPartido.desde_dict(
                obtener_mapeo(datos, "estado_espacial")
            ),
            estadisticas_local=EstadisticasEquipoPartido.desde_dict(
                obtener_mapeo(datos, "estadisticas_local")
            ),
            estadisticas_visitante=EstadisticasEquipoPartido.desde_dict(
                obtener_mapeo(datos, "estadisticas_visitante")
            ),
        )


def _obtener_flotante(datos: Mapping[str, object], clave: str) -> float:
    valor = datos.get(clave)
    if isinstance(valor, bool) or not isinstance(valor, int | float):
        raise TypeError(f"{clave} debe ser un numero.")
    return float(valor)


@dataclass(frozen=True, slots=True)
class EstadoIteracion:
    """Estado del partido en un momento dado de la simulación."""

    minuto: int
    posesion_equipo_id: int | None
    evento_actual: EventoPartido | None
    posicion_balon: Coordenada
    energia_local: float
    energia_visitante: float
    goles_local: int
    goles_visitante: int
    zona: str

    @classmethod
    def desde_estado(
        cls,
        minuto: int,
        posesion_id: int | None,
        evento: EventoPartido | None,
        estado_espacial: EstadoEspacialPartido,
        energia_local: float,
        energia_visitante: float,
        goles_local: int,
        goles_visitante: int,
    ) -> EstadoIteracion:
        return cls(
            minuto=minuto,
            posesion_equipo_id=posesion_id,
            evento_actual=evento,
            posicion_balon=estado_espacial.posicion_balon,
            energia_local=energia_local,
            energia_visitante=energia_visitante,
            goles_local=goles_local,
            goles_visitante=goles_visitante,
            zona=estado_espacial.posicion_balon.zona.value,
        )
