"""Atributos puros de rendimiento del jugador."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from typing import ClassVar

from motor_futbol.dominio.validaciones import (
    obtener_entero,
    validar_entero_en_rango,
)


@dataclass(frozen=True, slots=True)
class AtributosJugador:
    """Coleccion de stats base del jugador en escala 0-100."""

    CAMPOS_ESTADISTICOS: ClassVar[tuple[str, ...]] = (
        "aceleracion",
        "agresividad",
        "alcance",
        "atrape",
        "awareness_defensivo",
        "awareness_ofensivo",
        "awareness_portero",
        "cabeza",
        "contacto_fisico",
        "control_balon",
        "efecto",
        "engagement_defensivo",
        "equilibrio",
        "finalizacion",
        "lanzamiento_falta",
        "pase_bajo",
        "pase_elevado",
        "posesion_cerrada",
        "potencia_tiro",
        "rechazo",
        "reflejos",
        "regate",
        "resistencia",
        "salto",
        "tackles",
        "velocidad",
    )

    aceleracion: int
    agresividad: int
    alcance: int
    atrape: int
    awareness_defensivo: int
    awareness_ofensivo: int
    awareness_portero: int
    cabeza: int
    contacto_fisico: int
    control_balon: int
    efecto: int
    engagement_defensivo: int
    equilibrio: int
    finalizacion: int
    lanzamiento_falta: int
    pase_bajo: int
    pase_elevado: int
    posesion_cerrada: int
    potencia_tiro: int
    rechazo: int
    reflejos: int
    regate: int
    resistencia: int
    salto: int
    tackles: int
    velocidad: int

    def __post_init__(self) -> None:
        for nombre in self.CAMPOS_ESTADISTICOS:
            valor = getattr(self, nombre)
            validar_entero_en_rango(nombre, valor, minimo=0, maximo=100)

    @classmethod
    def base(cls, valor_inicial: int = 50, **cambios: int) -> AtributosJugador:
        """Crea una configuracion de atributos uniforme y admite overrides."""

        validar_entero_en_rango("valor_inicial", valor_inicial, minimo=0, maximo=100)
        nombres_validos = set(cls.CAMPOS_ESTADISTICOS)
        nombres_invalidos = set(cambios) - nombres_validos
        if nombres_invalidos:
            nombres = ", ".join(sorted(nombres_invalidos))
            raise ValueError(f"Campos de atributos no soportados: {nombres}.")

        datos = dict.fromkeys(cls.CAMPOS_ESTADISTICOS, valor_inicial)
        datos.update(cambios)
        return cls(**datos)

    @classmethod
    def desde_dict(cls, datos: dict[str, object]) -> AtributosJugador:
        return cls(
            **{nombre: obtener_entero(datos, nombre) for nombre in cls.CAMPOS_ESTADISTICOS},
        )

    @classmethod
    def nombres_campos(cls) -> tuple[str, ...]:
        return cls.CAMPOS_ESTADISTICOS

    def a_dict(self) -> dict[str, int]:
        return {campo.name: getattr(self, campo.name) for campo in dataclass_fields(self)}

    def a_escala_unitaria(self) -> dict[str, float]:
        return {nombre: getattr(self, nombre) / 100.0 for nombre in self.CAMPOS_ESTADISTICOS}

    def valor_normalizado(self, nombre: str) -> float:
        if nombre not in self.CAMPOS_ESTADISTICOS:
            raise ValueError(f"El atributo {nombre!r} no existe en AtributosJugador.")
        valor = getattr(self, nombre)
        assert isinstance(valor, int)
        return valor / 100.0
