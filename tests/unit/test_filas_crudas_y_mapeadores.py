from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from motor_futbol.datos import (
    FilaEquipoCruda,
    FilaJugadorCruda,
    mapear_equipo_con_plantilla,
    mapear_fila_jugador_a_dominio,
)


def test_fila_jugador_cruda_hace_roundtrip_desde_fixture() -> None:
    muestra = _cargar_muestra()
    jugadores = cast(list[dict[str, object]], muestra["jugadores"])

    fila = FilaJugadorCruda.desde_mapping(jugadores[0])
    restaurada = FilaJugadorCruda.desde_mapping(fila.a_dict())

    assert restaurada == fila
    assert restaurada.pie_fuerte == "Derecho"


def test_mapper_convierte_fila_jugador_a_entidad_de_dominio() -> None:
    muestra = _cargar_muestra()
    jugadores = cast(list[dict[str, object]], muestra["jugadores"])

    jugador = mapear_fila_jugador_a_dominio(FilaJugadorCruda.desde_mapping(jugadores[1]))

    assert jugador.nombre == "Delantero Muestra"
    assert jugador.posicion.value == "Delantero"
    assert jugador.pie_dominante is not None
    assert jugador.atributos.finalizacion == 88


def test_mapper_convierte_equipo_y_plantilla_desde_fixture() -> None:
    muestra = _cargar_muestra()
    fila_equipo = FilaEquipoCruda.desde_mapping(cast(dict[str, object], muestra["equipo"]))
    filas_jugadores = tuple(
        FilaJugadorCruda.desde_mapping(datos)
        for datos in cast(list[dict[str, object]], muestra["jugadores"])
    )

    equipo = mapear_equipo_con_plantilla(fila_equipo, filas_jugadores)

    assert equipo.id == 901
    assert equipo.nombre == "Equipo Muestra"
    assert equipo.total_jugadores == 2
    assert {jugador.id_equipo for jugador in equipo.jugadores} == {901}


def test_fila_jugador_cruda_detecta_datos_invalidos() -> None:
    muestra = _cargar_muestra()
    datos = dict(cast(dict[str, object], cast(list[dict[str, object]], muestra["jugadores"])[0]))
    datos["overall"] = 120

    with pytest.raises(ValueError, match="overall"):
        FilaJugadorCruda.desde_mapping(datos)


def _cargar_muestra() -> dict[str, object]:
    ruta = Path(__file__).resolve().parents[2] / "data_samples" / "football_engine_muestra.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return cast(dict[str, object], datos)
