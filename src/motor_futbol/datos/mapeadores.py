"""Transformacion desde filas crudas a entidades de dominio."""

from __future__ import annotations

from collections.abc import Sequence

from motor_futbol.datos.filas_crudas import FilaEquipoCruda, FilaJugadorCruda
from motor_futbol.dominio import AtributosJugador, Equipo, Jugador, PieDominante, PosicionJugador


def mapear_fila_jugador_a_dominio(fila: FilaJugadorCruda) -> Jugador:
    """Convierte una fila cruda de jugador a la entidad del dominio."""

    return Jugador(
        id=fila.id,
        id_equipo=fila.equipo_id,
        nombre=fila.nombre,
        posicion=PosicionJugador.desde_cadena(fila.posicion),
        overall=fila.overall,
        atributos=AtributosJugador(
            aceleracion=fila.aceleracion,
            agresividad=fila.agresividad,
            alcance=fila.alcance,
            atrape=fila.atrape,
            awareness_defensivo=fila.awareness_defensivo,
            awareness_ofensivo=fila.awareness_ofensivo,
            awareness_portero=fila.awareness_portero,
            cabeza=fila.cabeza,
            contacto_fisico=fila.contacto_fisico,
            control_balon=fila.control_balon,
            efecto=fila.efecto,
            engagement_defensivo=fila.engagement_defensivo,
            equilibrio=fila.equilibrio,
            finalizacion=fila.finalizacion,
            lanzamiento_falta=fila.lanzamiento_falta,
            pase_bajo=fila.pase_bajo,
            pase_elevado=fila.pase_elevado,
            posesion_cerrada=fila.posesion_cerrada,
            potencia_tiro=fila.potencia_tiro,
            rechazo=fila.rechazo,
            reflejos=fila.reflejos,
            regate=fila.regate,
            resistencia=fila.resistencia,
            salto=fila.salto,
            tackles=fila.tackles,
            velocidad=fila.velocidad,
        ),
        edad=fila.edad,
        nacionalidad=fila.nacionalidad,
        pie_dominante=PieDominante.desde_cadena(fila.pie_fuerte) if fila.pie_fuerte else None,
        altura_cm=fila.altura,
        peso_kg=fila.peso,
    )


def mapear_fila_equipo_a_dominio(fila: FilaEquipoCruda) -> Equipo:
    """Convierte una fila de equipo sin plantilla cargada."""

    return Equipo(id=fila.id, nombre=fila.nombre)


def mapear_equipo_con_plantilla(
    fila_equipo: FilaEquipoCruda, filas_jugadores: Sequence[FilaJugadorCruda]
) -> Equipo:
    """Convierte un equipo y su plantilla completa a dominio."""

    jugadores = tuple(mapear_fila_jugador_a_dominio(fila) for fila in filas_jugadores)
    return Equipo(id=fila_equipo.id, nombre=fila_equipo.nombre, jugadores=jugadores)
