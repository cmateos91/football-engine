"""Estado agregado del partido en un instante dado."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from motor_futbol.dominio.enums import FasePartido
from motor_futbol.dominio.evento import EventoPartido
from motor_futbol.dominio.validaciones import (
    obtener_cadena,
    obtener_entero,
    obtener_entero_opcional,
    obtener_lista_de_mapeos,
    validar_entero_en_rango,
    validar_identificador,
)


@dataclass(frozen=True, slots=True)
class EstadoPartido:
    """Snapshot del estado de partido."""

    fase: FasePartido
    minuto: int = 0
    tiempo_descuento: int = 0
    goles_local: int = 0
    goles_visitante: int = 0
    posesion_equipo_id: int | None = None
    eventos: tuple[EventoPartido, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        validar_entero_en_rango("minuto", self.minuto, minimo=0, maximo=130)
        validar_entero_en_rango("tiempo_descuento", self.tiempo_descuento, minimo=0, maximo=30)
        validar_entero_en_rango("goles_local", self.goles_local, minimo=0, maximo=99)
        validar_entero_en_rango("goles_visitante", self.goles_visitante, minimo=0, maximo=99)

        if self.posesion_equipo_id is not None:
            validar_identificador("posesion_equipo_id", self.posesion_equipo_id)

        for evento in self.eventos:
            if evento.minuto > self.minuto:
                raise ValueError("No puede haber eventos posteriores al minuto del estado.")

        if self.fase is FasePartido.NO_INICIADO and self.minuto != 0:
            raise ValueError("Un partido no iniciado debe estar en el minuto 0.")

    @property
    def marcador(self) -> str:
        return f"{self.goles_local}-{self.goles_visitante}"

    def a_dict(self) -> dict[str, object]:
        return {
            "fase": self.fase.value,
            "minuto": self.minuto,
            "tiempo_descuento": self.tiempo_descuento,
            "goles_local": self.goles_local,
            "goles_visitante": self.goles_visitante,
            "posesion_equipo_id": self.posesion_equipo_id,
            "eventos": [evento.a_dict() for evento in self.eventos],
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, object]) -> EstadoPartido:
        return cls(
            fase=FasePartido.desde_cadena(obtener_cadena(datos, "fase")),
            minuto=obtener_entero(datos, "minuto"),
            tiempo_descuento=obtener_entero(datos, "tiempo_descuento"),
            goles_local=obtener_entero(datos, "goles_local"),
            goles_visitante=obtener_entero(datos, "goles_visitante"),
            posesion_equipo_id=obtener_entero_opcional(datos, "posesion_equipo_id"),
            eventos=tuple(
                EventoPartido.desde_dict(evento)
                for evento in obtener_lista_de_mapeos(datos, "eventos")
            ),
        )
