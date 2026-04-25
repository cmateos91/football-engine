"""Simulación de temporada completa."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING, Any

from motor_futbol.dominio import ContextoPartido, Equipo
from motor_futbol.simulacion.modelos import ParametrosSimulacionBaseline, ResultadoSimulacionPartido
from motor_futbol.simulacion.motor_baseline import simular_partido_baseline

if TYPE_CHECKING:
    pass


@dataclass
class EstadisticasJugadorTemporada:
    """Estadísticas acumuladas de un jugador en una temporada."""

    jugador_id: int
    nombre: str
    equipo_id: int
    partidos: int = 0
    minutos: int = 0
    goles: int = 0
    assistencias: int = 0
    tarjetas_amarillas: int = 0
    tarjetas_rojas: int = 0
    xg_acumulado: float = 0.0
    lesiones: int = 0
    titular: int = 0

    def a_dict(self) -> dict[str, Any]:
        return {
            "jugador_id": self.jugador_id,
            "nombre": self.nombre,
            "equipo_id": self.equipo_id,
            "partidos": self.partidos,
            "minutos": self.minutos,
            "goles": self.goles,
            "asistencias": self.assistencias,
            "tarjetas_amarillas": self.tarjetas_amarillas,
            "tarjetas_rojas": self.tarjetas_rojas,
            "xg_acumulado": round(self.xg_acumulado, 3),
            "lesiones": self.lesiones,
            "titular": self.titular,
        }


@dataclass
class EstadisticasEquipoTemporada:
    """Estadísticas acumuladas de un equipo en una temporada."""

    equipo_id: int
    nombre: str
    partidos: int = 0
    victorias: int = 0
    empates: int = 0
    derrotas: int = 0
    goles_favor: int = 0
    goles_contra: int = 0
    puntos: int = 0
    local_victorias: int = 0
    local_partidos: int = 0
    visitante_victorias: int = 0
    visitante_partidos: int = 0

    @property
    def diferencia_gol(self) -> int:
        return self.goles_favor - self.goles_contra

    @property
    def local_pct(self) -> float:
        if self.local_partidos == 0:
            return 0.0
        return (self.local_victorias / self.local_partidos) * 100.0

    def a_dict(self) -> dict[str, Any]:
        return {
            "equipo_id": self.equipo_id,
            "nombre": self.nombre,
            "partidos": self.partidos,
            "victorias": self.victorias,
            "empates": self.empates,
            "derrotas": self.derrotas,
            "goles_favor": self.goles_favor,
            "goles_contra": self.goles_contra,
            "puntos": self.puntos,
            "diferencia_gol": self.diferencia_gol,
            "local_pct": round(self.local_pct, 1),
        }


@dataclass
class Clasificacion:
    """Posición en la tabla."""

    posicion: int
    equipo_id: int
    nombre: str
    puntos: int
    partidos: int
    victoria: int
    empate: int
    derrota: int
    gf: int
    gc: int
    dg: int


@dataclass
class PartidoJornada:
    """Partido programado en una jornada."""

    jornada: int
    equipo_local_id: int
    equipo_visitante_id: int


@dataclass
class ResultadoTemporada:
    """Resultado completo de una temporada."""

    año_inicio: int
    equipos: list[Equipo]
    calendario: list[list[PartidoJornada]]
    resultados: dict[int, ResultadoSimulacionPartido]
    estadisticas_jugadores: dict[int, EstadisticasJugadorTemporada]
    estadisticas_equipos: dict[int, EstadisticasEquipoTemporada]
    clasificacion: list[Clasificacion]

    def a_dict(self) -> dict[str, Any]:
        return {
            "año_inicio": self.año_inicio,
            "equipos": [eq.id for eq in self.equipos],
            "jornadas": len(self.calendario),
            "partidos": len(self.resultados),
            "estadisticas_equipos": {
                eq_id: est.a_dict() for eq_id, est in self.estadisticas_equipos.items()
            },
            "clasificacion": [
                {
                    "pos": c.posicion,
                    "equipo": c.nombre,
                    "pts": c.puntos,
                    "pj": c.partidos,
                    "gf": c.gf,
                    "gc": c.gc,
                    "dg": c.dg,
                }
                for c in self.clasificacion
            ],
        }


def generar_calendario_laliga(
    equipos: list[Equipo], generador: Random
) -> list[list[PartidoJornada]]:
    """Genera calendario de 38 jornadas."""
    n = len(equipos)
    if n != 20:
        raise ValueError("LaLiga requiere exactamente 20 equipos")

    ids = [eq.id for eq in equipos]
    jornadas: list[list[PartidoJornada]] = []

    partidos_ida = []
    for i in range(n):
        for j in range(i + 1, n):
            partidos_ida.append((ids[i], ids[j]))

    partidos_vuelta = [(e2, e1) for e1, e2 in partidos_ida]
    generador.shuffle(partidos_ida)

    todos_partidos = partidos_ida + partidos_vuelta

    jornada_actual = 1
    while todos_partidos:
        jornada: list[PartidoJornada] = []
        partidos_usados = set()

        for eq in ids:
            for pidx, (local, visita) in enumerate(todos_partidos):
                if local == eq and visita not in partidos_usados:
                    jornada.append(PartidoJornada(jornada_actual, local, visita))
                    partidos_usados.add(visita)
                    todos_partidos.pop(pidx)
                    break
                elif visita == eq and local not in partidos_usados:
                    jornada.append(PartidoJornada(jornada_actual, local, visita))
                    partidos_usados.add(local)
                    todos_partidos.pop(pidx)
                    break

        if jornada:
            jornadas.append(jornada)
            jornada_actual += 1

        if jornada_actual > 50:
            break

    return jornadas


def crear_equipos_default() -> list[Equipo]:
    """Crea los 20 equipos de LaLiga."""
    from motor_futbol.dominio import Equipo

    nombres = [
        "Real Madrid",
        "Barcelona",
        "Atlético Madrid",
        "Real Sociedad",
        "Real Betis",
        "Sevilla",
        "Villarreal",
        "Athletic Bilbao",
        "Valencia",
        "Celta Vigo",
        "Espanyol",
        "Girona",
        "Osasuna",
        "Mallorca",
        "Almería",
        "Rayo Vallecano",
        "Real Valladolid",
        "Cádiz",
        "Granada",
        "Alavés",
    ]

    return [Equipo(id=i + 1, nombre=nombre) for i, nombre in enumerate(nombres)]


@dataclass
class EstadoJugadorTemporada:
    """Estado dinámico de un jugador durante la temporada."""

    jugador_id: int
    energia: float = 100.0
    lesionado_hasta: int = 0  # Jornada hasta la que está lesionado


def simular_temporada(
    *,
    equipos: list[Equipo] | None = None,
    lineup_builder: Callable[[Equipo], Any] | None = None,
    parametros: ParametrosSimulacionBaseline | None = None,
    semilla: int = 20250601,
) -> ResultadoTemporada:
    """Simula una temporada completa de LaLiga."""
    from motor_futbol.simulacion.selector_alineacion import (
        construir_alineacion_baseline,
    )

    equipos = equipos or crear_equipos_default()
    parametros = parametros or ParametrosSimulacionBaseline()
    generador = Random(semilla)

    # Inicializar estado de jugadores
    estados_jugadores: dict[int, EstadoJugadorTemporada] = {}
    for eq in equipos:
        for j in eq.jugadores:
            estados_jugadores[j.id] = EstadoJugadorTemporada(j.id)

    calendario = generar_calendario_laliga(equipos, generador)

    resultados: dict[int, ResultadoSimulacionPartido] = {}
    stats_jugs: dict[int, EstadisticasJugadorTemporada] = {}
    stats_eqs: dict[int, EstadisticasEquipoTemporada] = {
        eq.id: EstadisticasEquipoTemporada(eq.id, eq.nombre) for eq in equipos
    }

    partido_id = 0

    for jornada_idx, jornada in enumerate(calendario):
        jornada_actual = jornada_idx + 1

        # Recuperación entre jornadas
        _aplicar_recuperacion(estados_jugadores)

        for partido_j in jornada:
            eq_local = next(e for e in equipos if e.id == partido_j.equipo_local_id)
            eq_visita = next(e for e in equipos if e.id == partido_j.equipo_visitante_id)

            # Filtrar jugadores disponibles para este partido
            eq_local_disp = _filtrar_disponibles(eq_local, estados_jugadores, jornada_actual)
            eq_visita_disp = _filtrar_disponibles(eq_visita, estados_jugadores, jornada_actual)

            # Construir alineaciones considerando estado/fatiga
            # (se pasarían estados si el builder lo soporta).
            # Por ahora el builder baseline no lo soporta, así que simulamos la rotación
            # enviando solo los jugadores disponibles.
            try:
                alineacion_local = construir_alineacion_baseline(eq_local_disp)
                alineacion_visita = construir_alineacion_baseline(eq_visita_disp)
            except Exception:
                # Fallback a la plantilla completa si falla por falta de jugadores (no ideal)
                alineacion_local = construir_alineacion_baseline(eq_local)
                alineacion_visita = construir_alineacion_baseline(eq_visita)

            contexto = ContextoPartido(
                competicion="LaLiga",
                temporada=f"{2025}-{2026}",
                equipo_local=eq_local,
                equipo_visitante=eq_visita,
                alineacion_local=alineacion_local,
                alineacion_visitante=alineacion_visita,
                semilla=semilla + partido_id,
            )

            resultado = simular_partido_baseline(contexto, parametros=parametros)
            resultados[partido_id] = resultado

            _actualizar_estadisticas(
                resultado=resultado,
                eq_local_id=eq_local.id,
                eq_visitante_id=eq_visita.id,
                stats_eqs=stats_eqs,
                stats_jugs=stats_jugs,
            )

            # Actualizar fatiga y posibles lesiones
            _actualizar_estado_tras_partido(resultado, estados_jugadores, jornada_actual, generador)

            partido_id += 1

    clasificacion = _calcular_clasificacion(stats_eqs)

    return ResultadoTemporada(
        año_inicio=2025,
        equipos=equipos,
        calendario=calendario,
        resultados=resultados,
        estadisticas_jugadores=stats_jugs,
        estadisticas_equipos=stats_eqs,
        clasificacion=clasificacion,
    )


def _filtrar_disponibles(
    equipo: Equipo, estados: dict[int, EstadoJugadorTemporada], jornada: int
) -> Equipo:
    """Retorna una copia del equipo con jugadores disponibles y overall afectado por energía."""
    jugadores_disp = []
    for j in equipo.jugadores:
        estado = estados.get(j.id)
        if estado and estado.lesionado_hasta < jornada:
            # Penalización por baja energía (ej: si tiene 50% energía, pierde un 10% de overall)
            factor_energia = 0.8 + (estado.energia / 100.0) * 0.2
            nuevo_overall = int(j.overall * factor_energia)

            # Crear copia del jugador con overall modificado
            # Nota: Al ser frozen=True, usamos dataclasses.replace
            import dataclasses

            j_mod = dataclasses.replace(j, overall=nuevo_overall)
            jugadores_disp.append(j_mod)

    import dataclasses

    return dataclasses.replace(equipo, jugadores=tuple(jugadores_disp))


def _aplicar_recuperacion(estados: dict[int, EstadoJugadorTemporada]) -> None:
    for estado in estados.values():
        if estado.lesionado_hasta == 0:  # Si no está lesionado, recupera
            estado.energia = min(100.0, estado.energia + 15.0)


def _actualizar_estado_tras_partido(
    resultado: ResultadoSimulacionPartido,
    estados: dict[int, EstadoJugadorTemporada],
    jornada: int,
    generador: Random,
) -> None:
    # Reducir energía a los que jugaron
    todos_jugadores = list(resultado.alineacion_local.titulares) + list(
        resultado.alineacion_visitante.titulares
    )

    for j in todos_jugadores:
        estado = estados[j.id]
        # Gasto de energía base por partido
        gasto = generador.uniform(20.0, 35.0)
        estado.energia = max(0.0, estado.energia - gasto)

        # Probabilidad de lesión basada en fatiga
        prob_lesion = 0.005 + (1.0 - estado.energia / 100.0) * 0.05
        if generador.random() < prob_lesion:
            duracion = generador.randint(1, 4)
            estado.lesionado_hasta = jornada + duracion
            estado.energia = 50.0  # La lesión baja la energía drásticamente


def _actualizar_estadisticas(
    resultado: ResultadoSimulacionPartido,
    eq_local_id: int,
    eq_visitante_id: int,
    stats_eqs: dict[int, EstadisticasEquipoTemporada],
    stats_jugs: dict[int, EstadisticasJugadorTemporada],
) -> None:
    gl = resultado.estadisticas_local.goles
    gv = resultado.estadisticas_visitante.goles

    # Actualizar local
    stats_local = stats_eqs[eq_local_id]
    stats_local.partidos += 1
    stats_local.local_partidos += 1
    stats_local.goles_favor += gl
    stats_local.goles_contra += gv

    # Actualizar visitante
    stats_visita = stats_eqs[eq_visitante_id]
    stats_visita.partidos += 1
    stats_visita.visitante_partidos += 1
    stats_visita.goles_favor += gv
    stats_visita.goles_contra += gl

    if gl > gv:
        stats_local.victorias += 1
        stats_local.local_victorias += 1
        stats_local.puntos += 3
        stats_visita.derrotas += 1
    elif gl == gv:
        stats_local.empates += 1
        stats_visita.empates += 1
        stats_local.puntos += 1
        stats_visita.puntos += 1
    else:
        stats_visita.victorias += 1
        stats_visita.visitante_victorias += 1
        stats_visita.puntos += 3
        stats_local.derrotas += 1

    # Actualizar jugadores
    for e in resultado.estado_final.eventos:
        if e.jugador_principal_id is None:
            continue

        jid = e.jugador_principal_id
        if jid not in stats_jugs:
            # Buscar nombre del jugador y equipo
            # Nota: Esto es un poco ineficiente, en una implementación real
            # vendría precargado o el evento tendría más contexto.
            # Por ahora buscamos en las alineaciones del resultado.
            jugador = None
            for j in resultado.alineacion_local.titulares:
                if j.id == jid:
                    jugador = j
                    break
            if not jugador:
                for j in resultado.alineacion_visitante.titulares:
                    if j.id == jid:
                        jugador = j
                        break

            if jugador:
                stats_jugs[jid] = EstadisticasJugadorTemporada(
                    jugador_id=jid, nombre=jugador.nombre, equipo_id=jugador.id_equipo
                )

        if jid in stats_jugs:
            s = stats_jugs[jid]
            from motor_futbol.dominio import TipoEventoPartido

            if e.tipo is TipoEventoPartido.GOL:
                s.goles += 1
            elif e.tipo is TipoEventoPartido.TIRO:
                # Sumamos xG si el evento lo tuviera, o de forma simplificada
                pass

    # Registrar titularidades y minutos (baseline: 90 min)
    for j in resultado.alineacion_local.titulares:
        if j.id not in stats_jugs:
            stats_jugs[j.id] = EstadisticasJugadorTemporada(j.id, j.nombre, j.id_equipo)
        stats_jugs[j.id].partidos += 1
        stats_jugs[j.id].titular += 1
        stats_jugs[j.id].minutos += 90

    for j in resultado.alineacion_visitante.titulares:
        if j.id not in stats_jugs:
            stats_jugs[j.id] = EstadisticasJugadorTemporada(j.id, j.nombre, j.id_equipo)
        stats_jugs[j.id].partidos += 1
        stats_jugs[j.id].titular += 1
        stats_jugs[j.id].minutos += 90


def _calcular_clasificacion(stats: dict[int, EstadisticasEquipoTemporada]) -> list[Clasificacion]:
    equipos_ord = sorted(
        stats.values(),
        key=lambda e: (-e.puntos, -e.diferencia_gol, -e.goles_favor),
    )

    return [
        Clasificacion(
            posicion=i + 1,
            equipo_id=eq.equipo_id,
            nombre=eq.nombre,
            puntos=eq.puntos,
            partidos=eq.partidos,
            victoria=eq.victorias,
            empate=eq.empates,
            derrota=eq.derrotas,
            gf=eq.goles_favor,
            gc=eq.goles_contra,
            dg=eq.diferencia_gol,
        )
        for i, eq in enumerate(equipos_ord)
    ]
