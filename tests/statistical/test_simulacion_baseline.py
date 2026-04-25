from __future__ import annotations

from tests.unit.fabrica_dominio import crear_contexto_baseline_desde_equipos, crear_equipo_con_nivel

from motor_futbol.simulacion import simular_partido_baseline


def test_monte_carlo_basico_favorece_al_equipo_mas_fuerte() -> None:
    equipo_fuerte = crear_equipo_con_nivel(
        id_equipo=20,
        nombre="Dominante FC",
        nivel_general=84,
        bonus_ataque=12,
        bonus_defensa=10,
    )
    equipo_debil = crear_equipo_con_nivel(
        id_equipo=21,
        nombre="Fragil FC",
        nivel_general=56,
        bonus_ataque=-8,
        bonus_defensa=-10,
    )

    victorias_local = 0
    victorias_visitante = 0
    empates = 0
    goles_local = 0
    goles_visitante = 0

    for semilla in range(100, 300):
        contexto = crear_contexto_baseline_desde_equipos(
            equipo_local=equipo_fuerte,
            equipo_visitante=equipo_debil,
            semilla=semilla,
        )
        resultado = simular_partido_baseline(contexto)
        goles_local += resultado.estadisticas_local.goles
        goles_visitante += resultado.estadisticas_visitante.goles
        if resultado.estadisticas_local.goles > resultado.estadisticas_visitante.goles:
            victorias_local += 1
        elif resultado.estadisticas_local.goles < resultado.estadisticas_visitante.goles:
            victorias_visitante += 1
        else:
            empates += 1

    assert victorias_local > victorias_visitante
    assert goles_local > goles_visitante
    assert empates < 180
