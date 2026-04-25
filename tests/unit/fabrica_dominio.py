from __future__ import annotations

from motor_futbol.dominio import (
    Alineacion,
    AtributosJugador,
    ContextoPartido,
    Equipo,
    EstadoFisico,
    EstiloPresion,
    Jugador,
    MentalidadTactica,
    PieDominante,
    PosicionJugador,
    Tactica,
)
from motor_futbol.simulacion import construir_alineacion_baseline


def crear_atributos(**cambios: int) -> AtributosJugador:
    return AtributosJugador.base(**cambios)


def crear_jugador(
    *,
    id_jugador: int,
    id_equipo: int,
    nombre: str | None = None,
    posicion: PosicionJugador = PosicionJugador.CENTRAL,
    overall: int = 75,
    atributos: AtributosJugador | None = None,
    edad: int | None = 25,
    nacionalidad: str | None = "Espana",
    pie_dominante: PieDominante | None = PieDominante.DERECHO,
    altura_cm: int | None = 180,
    peso_kg: int | None = 75,
    estado_fisico: EstadoFisico = EstadoFisico.DISPONIBLE,
) -> Jugador:
    return Jugador(
        id=id_jugador,
        id_equipo=id_equipo,
        nombre=nombre or f"Jugador {id_jugador}",
        posicion=posicion,
        overall=overall,
        atributos=atributos or crear_atributos(),
        edad=edad,
        nacionalidad=nacionalidad,
        pie_dominante=pie_dominante,
        altura_cm=altura_cm,
        peso_kg=peso_kg,
        estado_fisico=estado_fisico,
    )


def crear_titulares(id_equipo: int) -> tuple[Jugador, ...]:
    posiciones = (
        PosicionJugador.PORTERO,
        PosicionJugador.CENTRAL,
        PosicionJugador.CENTRAL,
        PosicionJugador.LATERAL,
        PosicionJugador.LATERAL,
        PosicionJugador.MEDIOCENTRO,
        PosicionJugador.MEDIOCENTRO,
        PosicionJugador.MEDIAPUNTA,
        PosicionJugador.EXTREMO,
        PosicionJugador.EXTREMO,
        PosicionJugador.DELANTERO,
    )
    return tuple(
        crear_jugador(
            id_jugador=id_equipo * 100 + indice + 1, id_equipo=id_equipo, posicion=posicion
        )
        for indice, posicion in enumerate(posiciones)
    )


def crear_suplentes(id_equipo: int, total: int = 7) -> tuple[Jugador, ...]:
    posiciones = (
        PosicionJugador.PORTERO,
        PosicionJugador.CENTRAL,
        PosicionJugador.LATERAL,
        PosicionJugador.MEDIOCENTRO,
        PosicionJugador.MEDIAPUNTA,
        PosicionJugador.EXTREMO,
        PosicionJugador.DELANTERO,
    )
    return tuple(
        crear_jugador(
            id_jugador=id_equipo * 100 + 100 + indice + 1,
            id_equipo=id_equipo,
            posicion=posiciones[indice],
        )
        for indice in range(total)
    )


def crear_tactica() -> Tactica:
    return Tactica(
        nombre="4-3-3 Equilibrado",
        formacion="4-3-3",
        mentalidad=MentalidadTactica.EQUILIBRADA,
        presion=EstiloPresion.MEDIA,
        ritmo=55,
        altura_bloque=52,
        anchura=60,
        agresividad=48,
    )


def crear_alineacion(id_equipo: int) -> Alineacion:
    titulares = crear_titulares(id_equipo)
    suplentes = crear_suplentes(id_equipo)
    return Alineacion(
        id_equipo=id_equipo,
        tactica=crear_tactica(),
        titulares=titulares,
        suplentes=suplentes,
        capitan_id=titulares[0].id,
    )


def crear_equipo(id_equipo: int, nombre: str | None = None) -> Equipo:
    titulares = crear_titulares(id_equipo)
    suplentes = crear_suplentes(id_equipo)
    return Equipo(
        id=id_equipo,
        nombre=nombre or f"Equipo {id_equipo}",
        jugadores=titulares + suplentes,
    )


def crear_contexto_partido() -> ContextoPartido:
    equipo_local = crear_equipo(1, "Local FC")
    equipo_visitante = crear_equipo(2, "Visitante FC")
    return ContextoPartido(
        competicion="LaLiga",
        temporada="2025-2026",
        equipo_local=equipo_local,
        equipo_visitante=equipo_visitante,
        alineacion_local=crear_alineacion(1),
        alineacion_visitante=crear_alineacion(2),
        jornada=1,
        semilla=12345,
        estadio="Estadio Central",
    )


def crear_equipo_con_nivel(
    *,
    id_equipo: int,
    nombre: str,
    nivel_general: int,
    bonus_ataque: int = 0,
    bonus_defensa: int = 0,
) -> Equipo:
    titulares = crear_titulares(id_equipo)
    suplentes = crear_suplentes(id_equipo)
    plantilla = tuple(
        _ajustar_jugador_por_nivel(
            jugador=jugador,
            nivel_general=nivel_general,
            bonus_ataque=bonus_ataque,
            bonus_defensa=bonus_defensa,
        )
        for jugador in (titulares + suplentes)
    )
    return Equipo(id=id_equipo, nombre=nombre, jugadores=plantilla)


def crear_contexto_baseline_desde_equipos(
    equipo_local: Equipo,
    equipo_visitante: Equipo,
    *,
    semilla: int = 12345,
) -> ContextoPartido:
    return ContextoPartido(
        competicion="LaLiga",
        temporada="2025-2026",
        equipo_local=equipo_local,
        equipo_visitante=equipo_visitante,
        alineacion_local=construir_alineacion_baseline(equipo_local),
        alineacion_visitante=construir_alineacion_baseline(equipo_visitante),
        jornada=1,
        semilla=semilla,
        estadio="Estadio Baseline",
    )


def _ajustar_jugador_por_nivel(
    *,
    jugador: Jugador,
    nivel_general: int,
    bonus_ataque: int,
    bonus_defensa: int,
) -> Jugador:
    ajuste_posicional = {
        PosicionJugador.PORTERO: 0,
        PosicionJugador.CENTRAL: bonus_defensa,
        PosicionJugador.LATERAL: bonus_defensa // 2,
        PosicionJugador.MEDIOCENTRO: (bonus_ataque + bonus_defensa) // 2,
        PosicionJugador.MEDIAPUNTA: bonus_ataque,
        PosicionJugador.EXTREMO: bonus_ataque,
        PosicionJugador.DELANTERO: bonus_ataque,
        PosicionJugador.DESCONOCIDA: 0,
    }[jugador.posicion]
    base = max(1, min(99, nivel_general + ajuste_posicional))

    atributos = crear_atributos(
        aceleracion=base,
        agresividad=max(1, min(99, base + bonus_defensa // 2)),
        alcance=base,
        atrape=base,
        awareness_defensivo=max(1, min(99, base + bonus_defensa)),
        awareness_ofensivo=max(1, min(99, base + bonus_ataque)),
        awareness_portero=base,
        cabeza=base,
        contacto_fisico=base,
        control_balon=max(1, min(99, base + bonus_ataque // 2)),
        efecto=base,
        engagement_defensivo=max(1, min(99, base + bonus_defensa)),
        equilibrio=base,
        finalizacion=max(1, min(99, base + bonus_ataque)),
        lanzamiento_falta=base,
        pase_bajo=base,
        pase_elevado=base,
        posesion_cerrada=max(1, min(99, base + bonus_ataque // 2)),
        potencia_tiro=max(1, min(99, base + bonus_ataque)),
        rechazo=base,
        reflejos=base,
        regate=max(1, min(99, base + bonus_ataque // 2)),
        resistencia=base,
        salto=base,
        tackles=max(1, min(99, base + bonus_defensa)),
        velocidad=base,
    )

    return crear_jugador(
        id_jugador=jugador.id,
        id_equipo=jugador.id_equipo,
        nombre=jugador.nombre,
        posicion=jugador.posicion,
        overall=base,
        atributos=atributos,
        edad=jugador.edad,
        nacionalidad=jugador.nacionalidad,
        pie_dominante=jugador.pie_dominante,
        altura_cm=jugador.altura_cm,
        peso_kg=jugador.peso_kg,
        estado_fisico=jugador.estado_fisico,
    )
