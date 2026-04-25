"""Entidad de dominio para alineaciones."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from motor_futbol.dominio.jugador import Jugador
from motor_futbol.dominio.tactica import Tactica
from motor_futbol.dominio.validaciones import (
    obtener_entero,
    obtener_entero_opcional,
    obtener_lista_de_mapeos,
    obtener_mapeo,
    validar_identificador,
    validar_secuencia_sin_duplicados,
)


@dataclass(frozen=True, slots=True)
class Alineacion:
    """Representa una alineacion valida para un partido."""

    id_equipo: int
    tactica: Tactica
    titulares: tuple[Jugador, ...]
    suplentes: tuple[Jugador, ...] = field(default_factory=tuple)
    capitan_id: int | None = None

    def __post_init__(self) -> None:
        validar_identificador("id_equipo", self.id_equipo)
        if len(self.titulares) != 11:
            raise ValueError("Una alineacion debe tener exactamente 11 titulares.")

        todos = self.titulares + self.suplentes
        ids = [jugador.id for jugador in todos]
        validar_secuencia_sin_duplicados("jugadores de la alineacion", ids)

        porteros_titulares = sum(1 for jugador in self.titulares if jugador.es_portero)
        if porteros_titulares != 1:
            raise ValueError("La alineacion titular debe incluir exactamente un portero.")

        for jugador in todos:
            if jugador.id_equipo != self.id_equipo:
                raise ValueError(
                    f"El jugador {jugador.id} no pertenece al equipo {self.id_equipo}."
                )

        if self.capitan_id is not None:
            validar_identificador("capitan_id", self.capitan_id)
            if self.capitan_id not in ids:
                raise ValueError("El capitan debe pertenecer a la convocatoria.")

    @property
    def todos_los_jugadores(self) -> tuple[Jugador, ...]:
        return self.titulares + self.suplentes

    def a_dict(self) -> dict[str, object]:
        return {
            "id_equipo": self.id_equipo,
            "tactica": self.tactica.a_dict(),
            "titulares": [jugador.a_dict() for jugador in self.titulares],
            "suplentes": [jugador.a_dict() for jugador in self.suplentes],
            "capitan_id": self.capitan_id,
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, object]) -> Alineacion:
        titulares = tuple(
            Jugador.desde_dict(jugador) for jugador in obtener_lista_de_mapeos(datos, "titulares")
        )
        suplentes = tuple(
            Jugador.desde_dict(jugador) for jugador in obtener_lista_de_mapeos(datos, "suplentes")
        )

        return cls(
            id_equipo=obtener_entero(datos, "id_equipo"),
            tactica=Tactica.desde_dict(obtener_mapeo(datos, "tactica")),
            titulares=titulares,
            suplentes=suplentes,
            capitan_id=obtener_entero_opcional(datos, "capitan_id"),
        )
