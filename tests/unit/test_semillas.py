from __future__ import annotations

import pytest

from motor_futbol.compartido.semillas import GeneradorDeterminista, muestra_determinista


def test_misma_semilla_produce_misma_secuencia() -> None:
    primera = muestra_determinista(semilla=17, cantidad=5)
    segunda = muestra_determinista(semilla=17, cantidad=5)

    assert primera == segunda


def test_generador_determinista_reutiliza_la_misma_logica() -> None:
    generador = GeneradorDeterminista(semilla=1234)

    assert generador.muestra(cantidad=4) == muestra_determinista(semilla=1234, cantidad=4)


def test_cantidad_negativa_falla() -> None:
    with pytest.raises(ValueError, match="cantidad"):
        muestra_determinista(semilla=5, cantidad=-1)
