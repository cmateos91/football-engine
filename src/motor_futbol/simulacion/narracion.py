"""Sistema de narración contextual para los eventos de partido."""

from __future__ import annotations

from collections import defaultdict, deque
from random import Random

from motor_futbol.dominio.espacial import ZonaCampo


class NarradorPartido:
    """Genera textos variados evitando repeticiones inmediatas."""

    def __init__(self, generador: Random) -> None:
        self._generador = generador
        self._recientes: dict[str, deque[str]] = defaultdict(lambda: deque(maxlen=3))

    def elegir(self, clave: str, opciones: tuple[str, ...]) -> str:
        recientes = self._recientes[clave]
        candidatas = [opcion for opcion in opciones if opcion not in recientes]
        if not candidatas:
            candidatas = list(opciones)
        elegida = self._generador.choice(candidatas)
        recientes.append(elegida)
        return elegida

    def zona(self, zona: ZonaCampo) -> str:
        mapa = {
            ZonaCampo.DEFENSA_IZQ: "su propio costado izquierdo",
            ZonaCampo.DEFENSA_CNT: "la base de la jugada",
            ZonaCampo.DEFENSA_DER: "su propio costado derecho",
            ZonaCampo.MEDIO_IZQ: "el carril izquierdo",
            ZonaCampo.MEDIO_CNT: "la medular",
            ZonaCampo.MEDIO_DER: "el carril derecho",
            ZonaCampo.ATAQUE_IZQ: "la frontal por izquierda",
            ZonaCampo.ATAQUE_CNT: "la media luna",
            ZonaCampo.ATAQUE_DER: "la frontal por derecha",
        }
        return mapa[zona]
