from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from motor_futbol.dominio import AtributosJugador


def test_atributos_base_crean_configuracion_valida() -> None:
    atributos = AtributosJugador.base(potencia_tiro=88, reflejos=72)

    assert atributos.potencia_tiro == 88
    assert atributos.reflejos == 72
    assert atributos.velocidad == 50


def test_atributo_fuera_de_rango_falla() -> None:
    with pytest.raises(ValueError, match="potencia_tiro"):
        AtributosJugador.base(potencia_tiro=101)


def test_serializacion_y_normalizacion_de_atributos() -> None:
    atributos = AtributosJugador.base(potencia_tiro=80, pase_bajo=65)

    serializado = atributos.a_dict()
    restaurado = AtributosJugador.desde_dict(serializado)

    assert restaurado == atributos
    assert atributos.valor_normalizado("potencia_tiro") == 0.8
    assert atributos.a_escala_unitaria()["pase_bajo"] == 0.65


@given(
    campo=st.sampled_from(AtributosJugador.nombres_campos()),
    valor=st.integers(min_value=0, max_value=100),
)
def test_normalizacion_de_atributos_se_mantiene_entre_0_y_1(campo: str, valor: int) -> None:
    atributos = AtributosJugador.base(**{campo: valor})
    normalizado = atributos.valor_normalizado(campo)

    assert 0.0 <= normalizado <= 1.0
    assert normalizado == valor / 100.0
