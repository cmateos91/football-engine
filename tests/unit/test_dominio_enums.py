from __future__ import annotations

import pytest

from motor_futbol.dominio import PieDominante, PosicionJugador


def test_posicion_desde_cadena_usa_valores_reales_de_bd() -> None:
    assert PosicionJugador.desde_cadena("Central") is PosicionJugador.CENTRAL
    assert PosicionJugador.desde_cadena("Unknown") is PosicionJugador.DESCONOCIDA


def test_pie_dominante_desde_cadena_acepta_alias() -> None:
    assert PieDominante.desde_cadena("Derecho") is PieDominante.DERECHO
    assert PieDominante.desde_cadena("left") is PieDominante.IZQUIERDO


def test_posicion_invalida_lanza_error() -> None:
    with pytest.raises(ValueError, match="Posicion"):
        PosicionJugador.desde_cadena("Libero")
