from __future__ import annotations

from tests.unit.fabrica_dominio import (
    crear_contexto_baseline_desde_equipos,
    crear_contexto_partido,
    crear_equipo_con_nivel,
)

from motor_futbol.dominio import TipoEventoPartido
from motor_futbol.simulacion import (
    ParametrosSimulacionBaseline,
    ResultadoSimulacionPartido,
    simular_partido_baseline,
)


def test_simulacion_baseline_es_reproducible_con_la_misma_semilla() -> None:
    contexto = crear_contexto_partido()

    primero = simular_partido_baseline(contexto)
    segundo = simular_partido_baseline(contexto)

    assert primero.a_dict() == segundo.a_dict()


def test_resultado_baseline_cumple_invariantes_basicos() -> None:
    contexto = crear_contexto_partido()
    resultado = simular_partido_baseline(contexto)

    assert resultado.total_posesiones > 0
    assert resultado.estadisticas_local.tiros_a_puerta <= resultado.estadisticas_local.tiros
    assert resultado.estadisticas_visitante.tiros_a_puerta <= resultado.estadisticas_visitante.tiros
    assert resultado.estado_final.marcador == (
        f"{resultado.estadisticas_local.goles}-{resultado.estadisticas_visitante.goles}"
    )
    assert resultado.estado_final.eventos[0].tipo is TipoEventoPartido.INICIO
    assert resultado.estado_final.eventos[-1].tipo is TipoEventoPartido.FINAL


def test_eventos_y_estadisticas_del_resultado_son_consistentes() -> None:
    contexto = crear_contexto_partido()
    resultado = simular_partido_baseline(contexto)

    goles_local = sum(
        1
        for evento in resultado.estado_final.eventos
        if evento.tipo is TipoEventoPartido.GOL
        and evento.equipo_id == resultado.contexto.equipo_local.id
    )
    goles_visitante = sum(
        1
        for evento in resultado.estado_final.eventos
        if evento.tipo is TipoEventoPartido.GOL
        and evento.equipo_id == resultado.contexto.equipo_visitante.id
    )
    tiros_local = sum(
        1
        for evento in resultado.estado_final.eventos
        if evento.tipo is TipoEventoPartido.TIRO
        and evento.equipo_id == resultado.contexto.equipo_local.id
    )
    tiros_visitante = sum(
        1
        for evento in resultado.estado_final.eventos
        if evento.tipo is TipoEventoPartido.TIRO
        and evento.equipo_id == resultado.contexto.equipo_visitante.id
    )

    assert goles_local == resultado.estadisticas_local.goles
    assert goles_visitante == resultado.estadisticas_visitante.goles
    assert tiros_local == resultado.estadisticas_local.tiros
    assert tiros_visitante == resultado.estadisticas_visitante.tiros


def test_resultado_baseline_hace_roundtrip_a_dict() -> None:
    contexto = crear_contexto_partido()
    resultado = simular_partido_baseline(contexto)

    restaurado = ResultadoSimulacionPartido.desde_dict(resultado.a_dict())

    assert restaurado.a_dict() == resultado.a_dict()


def test_equipo_mas_fuerte_genera_mas_peligro_que_uno_debil_en_un_escenario_controlado() -> None:
    equipo_fuerte = crear_equipo_con_nivel(
        id_equipo=10,
        nombre="Fuerte FC",
        nivel_general=82,
        bonus_ataque=10,
        bonus_defensa=8,
    )
    equipo_debil = crear_equipo_con_nivel(
        id_equipo=11,
        nombre="Debil FC",
        nivel_general=58,
        bonus_ataque=-6,
        bonus_defensa=-8,
    )
    contexto = crear_contexto_baseline_desde_equipos(
        equipo_local=equipo_fuerte,
        equipo_visitante=equipo_debil,
        semilla=777,
    )
    parametros = ParametrosSimulacionBaseline()

    resultado = simular_partido_baseline(contexto, parametros=parametros)

    assert resultado.estadisticas_local.tiros >= resultado.estadisticas_visitante.tiros
    assert resultado.estadisticas_local.goles >= resultado.estadisticas_visitante.goles


def test_corner_y_centro_conservan_el_mismo_lanzador() -> None:
    contexto = crear_contexto_partido()
    resultado = simular_partido_baseline(contexto)
    eventos = resultado.estado_final.eventos

    for indice, evento in enumerate(eventos[:-1]):
        if evento.tipo is not TipoEventoPartido.CORNER:
            continue
        siguiente = eventos[indice + 1]
        if (
            siguiente.tipo is TipoEventoPartido.CENTRO
            and siguiente.equipo_id == evento.equipo_id
            and siguiente.minuto == evento.minuto
        ):
            assert siguiente.jugador_principal_id == evento.jugador_principal_id


def test_penalti_se_resuelve_con_tiro_del_mismo_jugador_y_resultado() -> None:
    contexto = crear_contexto_partido()
    resultado = simular_partido_baseline(contexto)
    eventos = resultado.estado_final.eventos

    for indice, evento in enumerate(eventos[:-2]):
        if evento.tipo is not TipoEventoPartido.PENALTI:
            continue
        tiro = eventos[indice + 1]
        desenlace = eventos[indice + 2]

        assert tiro.tipo is TipoEventoPartido.TIRO
        assert tiro.jugador_principal_id == evento.jugador_principal_id
        assert desenlace.tipo in (TipoEventoPartido.GOL, TipoEventoPartido.PARADA)
        assert desenlace.minuto == evento.minuto
