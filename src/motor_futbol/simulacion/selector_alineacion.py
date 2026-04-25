"""Construccion automatica de una alineacion baseline."""

from __future__ import annotations

from collections.abc import Iterable

from motor_futbol.dominio import Alineacion, Equipo, Jugador, PosicionJugador, Tactica
from motor_futbol.dominio.enums import EstiloPresion, MentalidadTactica


class SeleccionAlineacionError(ValueError):
    """Error al construir una alineacion automatica."""


def construir_alineacion_baseline(equipo: Equipo) -> Alineacion:
    """Construye una alineacion 4-3-3 aproximada a partir de la plantilla."""

    porteros = _ordenar_por_overall(
        jugador for jugador in equipo.jugadores if jugador.posicion is PosicionJugador.PORTERO
    )
    if not porteros:
        raise SeleccionAlineacionError(
            f"El equipo {equipo.nombre} no tiene porteros para construir una alineacion."
        )

    titulares: list[Jugador] = [porteros[0]]
    usados = {porteros[0].id}
    restante = [jugador for jugador in equipo.jugadores if jugador.id not in usados]

    for posicion, total in (
        (PosicionJugador.CENTRAL, 2),
        (PosicionJugador.LATERAL, 2),
        (PosicionJugador.MEDIOCENTRO, 2),
        (PosicionJugador.MEDIAPUNTA, 1),
        (PosicionJugador.EXTREMO, 2),
        (PosicionJugador.DELANTERO, 1),
    ):
        elegidos = _tomar_jugadores(restante, posicion=posicion, total=total)
        titulares.extend(elegidos)
        usados.update(jugador.id for jugador in elegidos)
        restante = [jugador for jugador in restante if jugador.id not in usados]

    if len(titulares) < 11:
        faltan = 11 - len(titulares)
        candidatos = _ordenar_por_overall(restante)
        titulares.extend(candidatos[:faltan])
        usados.update(jugador.id for jugador in candidatos[:faltan])
        restante = [jugador for jugador in restante if jugador.id not in usados]

    if len(titulares) != 11:
        raise SeleccionAlineacionError(
            f"No se pudieron seleccionar 11 titulares para el equipo {equipo.nombre}."
        )

    suplentes = tuple(_ordenar_por_overall(restante)[:7])
    capitan = max(titulares, key=lambda jugador: (jugador.overall, -jugador.id))

    return Alineacion(
        id_equipo=equipo.id,
        tactica=_crear_tactica_baseline(),
        titulares=tuple(titulares),
        suplentes=suplentes,
        capitan_id=capitan.id,
    )


def _crear_tactica_baseline() -> Tactica:
    return Tactica(
        nombre="Baseline 4-3-3",
        formacion="4-3-3",
        mentalidad=MentalidadTactica.EQUILIBRADA,
        presion=EstiloPresion.MEDIA,
        ritmo=52,
        altura_bloque=50,
        anchura=56,
        agresividad=50,
    )


def _ordenar_por_overall(jugadores: Iterable[Jugador]) -> list[Jugador]:
    return sorted(jugadores, key=lambda jugador: (jugador.overall, jugador.id), reverse=True)


def _tomar_jugadores(
    candidatos: Iterable[Jugador], *, posicion: PosicionJugador, total: int
) -> list[Jugador]:
    filtrados = [jugador for jugador in candidatos if jugador.posicion is posicion]
    return _ordenar_por_overall(filtrados)[:total]
