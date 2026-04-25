"""Entidad de dominio para jugadores."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from motor_futbol.dominio.atributos import AtributosJugador
from motor_futbol.dominio.enums import EstadoFisico, PieDominante, PosicionJugador, RolTactico
from motor_futbol.dominio.validaciones import (
    normalizar_cadena_opcional,
    obtener_cadena,
    obtener_cadena_opcional,
    obtener_entero,
    obtener_entero_opcional,
    obtener_mapeo,
    validar_cadena_no_vacia,
    validar_entero_en_rango,
    validar_entero_opcional_en_rango,
    validar_identificador,
)


@dataclass(frozen=True, slots=True)
class Jugador:
    """Representa un jugador listo para entrar en el dominio."""

    id: int
    id_equipo: int
    nombre: str
    posicion: PosicionJugador
    overall: int
    atributos: AtributosJugador
    edad: int | None = None
    nacionalidad: str | None = None
    pie_dominante: PieDominante | None = None
    altura_cm: int | None = None
    peso_kg: int | None = None
    estado_fisico: EstadoFisico = EstadoFisico.DISPONIBLE
    rol_tactico: RolTactico | None = None

    def __post_init__(self) -> None:
        validar_identificador("id", self.id)
        validar_identificador("id_equipo", self.id_equipo)
        validar_cadena_no_vacia("nombre", self.nombre)
        validar_entero_en_rango("overall", self.overall, minimo=0, maximo=100)
        validar_entero_opcional_en_rango("edad", self.edad, minimo=14, maximo=60)
        validar_entero_opcional_en_rango("altura_cm", self.altura_cm, minimo=130, maximo=230)
        validar_entero_opcional_en_rango("peso_kg", self.peso_kg, minimo=40, maximo=130)

        object.__setattr__(self, "nombre", self.nombre.strip())
        object.__setattr__(self, "nacionalidad", normalizar_cadena_opcional(self.nacionalidad))

    @property
    def es_portero(self) -> bool:
        return self.posicion is PosicionJugador.PORTERO

    def a_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "id_equipo": self.id_equipo,
            "nombre": self.nombre,
            "posicion": self.posicion.value,
            "overall": self.overall,
            "atributos": self.atributos.a_dict(),
            "edad": self.edad,
            "nacionalidad": self.nacionalidad,
            "pie_dominante": self.pie_dominante.value if self.pie_dominante is not None else None,
            "altura_cm": self.altura_cm,
            "peso_kg": self.peso_kg,
            "estado_fisico": self.estado_fisico.value,
            "rol_tactico": self.rol_tactico.value if self.rol_tactico is not None else None,
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, object]) -> Jugador:
        pie_dominante = obtener_cadena_opcional(datos, "pie_dominante")
        rol_tactico = obtener_cadena_opcional(datos, "rol_tactico")

        return cls(
            id=obtener_entero(datos, "id"),
            id_equipo=obtener_entero(datos, "id_equipo"),
            nombre=obtener_cadena(datos, "nombre"),
            posicion=PosicionJugador.desde_cadena(obtener_cadena(datos, "posicion")),
            overall=obtener_entero(datos, "overall"),
            atributos=AtributosJugador.desde_dict(dict(obtener_mapeo(datos, "atributos"))),
            edad=obtener_entero_opcional(datos, "edad"),
            nacionalidad=obtener_cadena_opcional(datos, "nacionalidad"),
            pie_dominante=PieDominante.desde_cadena(pie_dominante) if pie_dominante else None,
            altura_cm=obtener_entero_opcional(datos, "altura_cm"),
            peso_kg=obtener_entero_opcional(datos, "peso_kg"),
            estado_fisico=EstadoFisico.desde_cadena(obtener_cadena(datos, "estado_fisico")),
            rol_tactico=RolTactico.desde_cadena(rol_tactico) if rol_tactico else None,
        )
