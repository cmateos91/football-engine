"""Estado espacial del partido."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from math import hypot

from motor_futbol.dominio.validaciones import (
    validar_entero_en_rango,
)


class ZonaCampo(StrEnum):
    """Zonas del campo en cuadrícula 3x3."""

    DEFENSA_IZQ = "Defensa Izquierda"
    DEFENSA_CNT = "Defensa Centro"
    DEFENSA_DER = "Defensa Derecha"
    MEDIO_IZQ = "Mediocampo Izquierda"
    MEDIO_CNT = "Mediocampo Centro"
    MEDIO_DER = "Mediocampo Derecha"
    ATAQUE_IZQ = "Ataque Izquierda"
    ATAQUE_CNT = "Ataque Centro"
    ATAQUE_DER = "Ataque Derecha"

    @classmethod
    def desde_xy(cls, x: float, y: float) -> ZonaCampo:
        if x < 33:
            zona_x = "DEFENSA"
        elif x < 67:
            zona_x = "MEDIO"
        else:
            zona_x = "ATAQUE"

        if y < 33:
            zona_y = "IZQ"
        elif y < 67:
            zona_y = "CNT"
        else:
            zona_y = "DER"

        nombre = f"{zona_x}_{zona_y}"
        return cls[nombre.upper()]


@dataclass(frozen=True, slots=True)
class Coordenada:
    """Coordenada en el campo 0-100."""

    x: float
    y: float

    def __post_init__(self) -> None:
        validar_entero_en_rango("x", int(self.x), minimo=0, maximo=100)
        validar_entero_en_rango("y", int(self.y), minimo=0, maximo=100)

    @property
    def zona(self) -> ZonaCampo:
        return ZonaCampo.desde_xy(self.x, self.y)

    def distancia_a(self, otra: Coordenada) -> float:
        return float(hypot(self.x - otra.x, self.y - otra.y))


@dataclass(slots=True)
class EstadoEspacialPartido:
    """Estado espacial mutable durante la simulación."""

    posicion_balon: Coordenada = field(default_factory=lambda: Coordenada(50.0, 50.0))
    posesion_equipo_id: int | None = None
    ultimo_pase: Coordenada | None = None
    tiempo_en_zona: dict[str, float] = field(default_factory=dict)
    progreciones_exitosas: int = 0
    progreciones_fallidas: int = 0

    def _inicializar_zonas(self) -> None:
        if not self.tiempo_en_zona:
            for z in ZonaCampo:
                self.tiempo_en_zona[z.value] = 0.0

    def actualizar(self, equipo_id: int, incremento: float = 1.0) -> None:
        self._inicializar_zonas()
        zona_actual = self.posicion_balon.zona.value
        self.tiempo_en_zona[zona_actual] = self.tiempo_en_zona.get(zona_actual, 0.0) + incremento

    def mover_a(self, coords: Coordenada) -> None:
        zona_anterior = self.posicion_balon.zona
        self.posicion_balon = coords
        zona_nueva = coords.zona

        if zona_anterior not in (
            ZonaCampo.ATAQUE_IZQ,
            ZonaCampo.ATAQUE_CNT,
            ZonaCampo.ATAQUE_DER,
        ) and zona_nueva in (
            ZonaCampo.ATAQUE_IZQ,
            ZonaCampo.ATAQUE_CNT,
            ZonaCampo.ATAQUE_DER,
        ):
            self.progreciones_exitosas += 1

        if zona_anterior in (
            ZonaCampo.ATAQUE_IZQ,
            ZonaCampo.ATAQUE_CNT,
            ZonaCampo.ATAQUE_DER,
        ) and zona_nueva not in (
            ZonaCampo.ATAQUE_IZQ,
            ZonaCampo.ATAQUE_CNT,
            ZonaCampo.ATAQUE_DER,
        ):
            self.progreciones_fallidas += 1

        self.ultimo_pase = self.posicion_balon

    def posesion_cambia(self, equipo_id: int) -> None:
        self.posesion_equipo_id = equipo_id

    def a_dict(self) -> dict[str, object]:
        return {
            "posicion_balon": (self.posicion_balon.x, self.posicion_balon.y),
            "posesion_equipo_id": self.posesion_equipo_id,
            "ultimo_pase": (self.ultimo_pase.x, self.ultimo_pase.y) if self.ultimo_pase else None,
            "tiempo_en_zona": self.tiempo_en_zona.copy(),
            "progreciones_exitosas": self.progreciones_exitosas,
            "progreciones_fallidas": self.progreciones_fallidas,
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, object]) -> EstadoEspacialPartido:
        pos = datos.get("posicion_balon")
        if pos and isinstance(pos, tuple | list):
            posicion_balon = Coordenada(float(pos[0]), float(pos[1]))
        else:
            posicion_balon = Coordenada(50.0, 50.0)

        instance = cls()
        instance.posicion_balon = posicion_balon

        if pid := datos.get("posesion_equipo_id"):
            if not isinstance(pid, int | float | str):
                raise ValueError("posesion_equipo_id inválido")
            instance.posesion_equipo_id = int(pid)

        uk = datos.get("ultimo_pase")
        if uk and isinstance(uk, tuple | list):
            instance.ultimo_pase = Coordenada(float(uk[0]), float(uk[1]))

        tiempo = datos.get("tiempo_en_zona", {})
        if not isinstance(tiempo, Mapping):
            raise ValueError("tiempo_en_zona inválido")
        instance.tiempo_en_zona = {str(k): float(v) for k, v in tiempo.items()}

        prog_ex = datos.get("progreciones_exitosas", 0)
        if not isinstance(prog_ex, int | float | str):
            raise ValueError("progreciones_exitosas inválido")
        instance.progreciones_exitosas = int(prog_ex)

        prog_fa = datos.get("progreciones_fallidas", 0)
        if not isinstance(prog_fa, int | float | str):
            raise ValueError("progreciones_fallidas inválido")
        instance.progreciones_fallidas = int(prog_fa)
        return instance
