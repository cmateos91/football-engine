from __future__ import annotations

import pytest
from tests.unit.fabrica_dominio import (
    crear_alineacion,
    crear_jugador,
    crear_tactica,
    crear_titulares,
)

from motor_futbol.dominio import Alineacion, Tactica


def test_tactica_valida_expone_lineas_de_formacion() -> None:
    tactica = crear_tactica()

    assert tactica.lineas_formacion == (4, 3, 3)
    assert Tactica.desde_dict(tactica.a_dict()) == tactica


def test_tactica_invalida_si_la_formacion_no_suma_10() -> None:
    with pytest.raises(ValueError, match="sumar 10"):
        Tactica(nombre="Rota", formacion="4-4-1")


def test_alineacion_valida_se_serializa_y_recupera() -> None:
    alineacion = crear_alineacion(1)

    restaurada = Alineacion.desde_dict(alineacion.a_dict())

    assert restaurada == alineacion
    assert len(restaurada.titulares) == 11


def test_alineacion_falla_sin_once_titular_completo() -> None:
    titulares = crear_titulares(1)[:10]
    with pytest.raises(ValueError, match="11 titulares"):
        Alineacion(id_equipo=1, tactica=crear_tactica(), titulares=titulares)


def test_alineacion_falla_si_hay_dos_porteros_titulares() -> None:
    titulares = list(crear_titulares(1))
    titulares[1] = crear_jugador(id_jugador=999, id_equipo=1, posicion=titulares[0].posicion)

    with pytest.raises(ValueError, match="exactamente un portero"):
        Alineacion(id_equipo=1, tactica=crear_tactica(), titulares=tuple(titulares))


def test_alineacion_falla_si_el_capitan_no_esta_convocado() -> None:
    with pytest.raises(ValueError, match="capitan"):
        Alineacion(
            id_equipo=1,
            tactica=crear_tactica(),
            titulares=crear_titulares(1),
            capitan_id=999_999,
        )
