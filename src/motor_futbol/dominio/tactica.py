"""Entidad de dominio para tacticas."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from motor_futbol.dominio.enums import EstiloPresion, MentalidadTactica
from motor_futbol.dominio.validaciones import (
    obtener_cadena,
    obtener_entero,
    validar_cadena_no_vacia,
    validar_entero_en_rango,
)


@dataclass(frozen=True, slots=True)
class Tactica:
    """Representacion declarativa de una tactica."""

    nombre: str
    formacion: str
    mentalidad: MentalidadTactica = MentalidadTactica.EQUILIBRADA
    presion: EstiloPresion = EstiloPresion.MEDIA
    ritmo: int = 50
    altura_bloque: int = 50
    anchura: int = 50
    agresividad: int = 50

    def __post_init__(self) -> None:
        validar_cadena_no_vacia("nombre", self.nombre)
        validar_cadena_no_vacia("formacion", self.formacion)
        validar_entero_en_rango("ritmo", self.ritmo, minimo=0, maximo=100)
        validar_entero_en_rango("altura_bloque", self.altura_bloque, minimo=0, maximo=100)
        validar_entero_en_rango("anchura", self.anchura, minimo=0, maximo=100)
        validar_entero_en_rango("agresividad", self.agresividad, minimo=0, maximo=100)

        object.__setattr__(self, "nombre", self.nombre.strip())
        object.__setattr__(self, "formacion", self.formacion.strip())
        self._validar_formacion()

    @property
    def lineas_formacion(self) -> tuple[int, ...]:
        return tuple(int(token) for token in self.formacion.split("-"))

    def a_dict(self) -> dict[str, object]:
        return {
            "nombre": self.nombre,
            "formacion": self.formacion,
            "mentalidad": self.mentalidad.value,
            "presion": self.presion.value,
            "ritmo": self.ritmo,
            "altura_bloque": self.altura_bloque,
            "anchura": self.anchura,
            "agresividad": self.agresividad,
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, object]) -> Tactica:
        return cls(
            nombre=obtener_cadena(datos, "nombre"),
            formacion=obtener_cadena(datos, "formacion"),
            mentalidad=MentalidadTactica.desde_cadena(obtener_cadena(datos, "mentalidad")),
            presion=EstiloPresion.desde_cadena(obtener_cadena(datos, "presion")),
            ritmo=obtener_entero(datos, "ritmo"),
            altura_bloque=obtener_entero(datos, "altura_bloque"),
            anchura=obtener_entero(datos, "anchura"),
            agresividad=obtener_entero(datos, "agresividad"),
        )

    def _validar_formacion(self) -> None:
        partes = self.formacion.split("-")
        if len(partes) < 3 or len(partes) > 5:
            raise ValueError("La formacion debe tener entre 3 y 5 lineas.")

        try:
            lineas = tuple(int(parte) for parte in partes)
        except ValueError as error:
            raise ValueError(
                "La formacion solo puede contener enteros separados por guiones."
            ) from error

        if any(linea <= 0 or linea > 6 for linea in lineas):
            raise ValueError("Cada linea de la formacion debe estar entre 1 y 6 jugadores.")
        if sum(lineas) != 10:
            raise ValueError("La formacion debe sumar 10 jugadores de campo.")
