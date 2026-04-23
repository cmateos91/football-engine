from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from motor_futbol.compartido.semillas import muestra_determinista


@given(
    semilla=st.integers(min_value=0, max_value=10_000_000),
    cantidad=st.integers(min_value=0, max_value=25),
)
def test_la_misma_semilla_siempre_repite_la_misma_muestra(semilla: int, cantidad: int) -> None:
    assert muestra_determinista(semilla=semilla, cantidad=cantidad) == muestra_determinista(
        semilla=semilla,
        cantidad=cantidad,
    )
