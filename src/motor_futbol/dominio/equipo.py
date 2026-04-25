"""Entidad de dominio para equipos."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from motor_futbol.dominio.jugador import Jugador
from motor_futbol.dominio.validaciones import (
    obtener_cadena,
    obtener_entero,
    obtener_lista_de_mapeos,
    validar_cadena_no_vacia,
    validar_identificador,
    validar_secuencia_sin_duplicados,
)


@dataclass(frozen=True, slots=True)
class Equipo:
    """Representa un equipo y su plantilla."""

    id: int
    nombre: str
    jugadores: tuple[Jugador, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        validar_identificador("id", self.id)
        validar_cadena_no_vacia("nombre", self.nombre)
        object.__setattr__(self, "nombre", self.nombre.strip())

        ids = [jugador.id for jugador in self.jugadores]
        validar_secuencia_sin_duplicados("jugadores", ids)

        for jugador in self.jugadores:
            if jugador.id_equipo != self.id:
                raise ValueError(f"El jugador {jugador.id} no pertenece al equipo {self.id}.")

    @property
    def total_jugadores(self) -> int:
        return len(self.jugadores)

    def obtener_jugador(self, id_jugador: int) -> Jugador:
        for jugador in self.jugadores:
            if jugador.id == id_jugador:
                return jugador
        raise KeyError(f"No existe un jugador con id {id_jugador} en el equipo {self.id}.")

    def a_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "jugadores": [jugador.a_dict() for jugador in self.jugadores],
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, object]) -> Equipo:
        jugadores = tuple(
            Jugador.desde_dict(jugador) for jugador in obtener_lista_de_mapeos(datos, "jugadores")
        )
        return cls(
            id=obtener_entero(datos, "id"),
            nombre=obtener_cadena(datos, "nombre"),
            jugadores=jugadores,
        )
