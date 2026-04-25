from random import Random

from motor_futbol.dominio.espacial import ZonaCampo
from motor_futbol.simulacion.narracion import NarradorPartido


def test_narrador_evita_repeticion_inmediata():
    narrador = NarradorPartido(Random(42))
    opciones = ("A", "B", "C")

    resultados = [narrador.elegir("tiro", opciones) for _ in range(15)]

    for anterior, actual in zip(resultados, resultados[1:]):
        assert anterior != actual


def test_narrador_zona_humana():
    narrador = NarradorPartido(Random(1))

    assert narrador.zona(ZonaCampo.ATAQUE_CNT) == "la media luna"
