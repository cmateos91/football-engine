"""Herramientas para reproducibilidad y generacion determinista."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True, slots=True)
class GeneradorDeterminista:
    """Encapsula una semilla para generar secuencias reproducibles."""

    semilla: int

    def crear(self) -> Random:
        """Devuelve un generador inicializado con la semilla dada."""

        return Random(self.semilla)

    def muestra(self, cantidad: int) -> list[float]:
        """Genera una muestra determinista de numeros pseudoaleatorios."""

        return muestra_determinista(semilla=self.semilla, cantidad=cantidad)


def muestra_determinista(semilla: int, cantidad: int) -> list[float]:
    """Genera una secuencia reproducible para pruebas y depuracion."""

    if cantidad < 0:
        raise ValueError("La cantidad no puede ser negativa.")

    generador = Random(semilla)
    return [generador.random() for _ in range(cantidad)]
