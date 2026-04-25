from __future__ import annotations

import pytest

from motor_futbol.compartido.configuracion import cargar_configuracion
from motor_futbol.datos import RepositorioFootballEngine
from motor_futbol.dominio import ContextoPartido, TipoEventoPartido
from motor_futbol.simulacion import simular_partido_baseline


def test_simulacion_baseline_con_datos_reales_es_determinista() -> None:
    configuracion = cargar_configuracion()

    if not configuracion.base_de_datos_configurada:
        pytest.skip("No hay URL_BD configurada para pruebas de integracion reales.")

    repositorio = RepositorioFootballEngine.desde_configuracion(configuracion)
    real_madrid = repositorio.obtener_equipo_por_id(154)
    barcelona = repositorio.obtener_equipo_por_id(149)
    contexto = ContextoPartido(
        competicion="LaLiga",
        temporada="2025-2026",
        equipo_local=real_madrid,
        equipo_visitante=barcelona,
        semilla=20260423,
        jornada=10,
    )

    primero = simular_partido_baseline(contexto)
    segundo = simular_partido_baseline(contexto)

    assert primero.a_dict() == segundo.a_dict()
    assert primero.total_posesiones > 0
    assert primero.estado_final.eventos[0].tipo is TipoEventoPartido.INICIO
    assert primero.estado_final.eventos[-1].tipo is TipoEventoPartido.FINAL
