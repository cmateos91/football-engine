"""Motor baseline de simulacion basado en posesiones y eventos."""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from random import Random

from motor_futbol.dominio import (
    Alineacion,
    ContextoPartido,
    Coordenada,
    Equipo,
    EstadoEspacialPartido,
    EstadoPartido,
    EstiloPresion,
    EventoPartido,
    FasePartido,
    Jugador,
    MentalidadTactica,
    PosicionJugador,
    TipoEventoPartido,
    ZonaCampo,
)
from motor_futbol.simulacion.modelos import (
    EstadisticasEquipoPartido,
    EstadoIteracion,
    ParametrosSimulacionBaseline,
    ResultadoSimulacionPartido,
)
from motor_futbol.simulacion.selector_alineacion import construir_alineacion_baseline
from motor_futbol.simulacion.xg import calcular_xg


@dataclass(slots=True)
class _EstadoEquipoMutable:
    equipo: Equipo
    alineacion: Alineacion
    posesiones: int = 0
    tiros: int = 0
    tiros_a_puerta: int = 0
    goles: int = 0
    faltas: int = 0
    corners: int = 0
    tarjetas_amarillas: int = 0
    tarjetas_rojas: int = 0
    energia_actual: float = 100.0
    energia_acumulada: float = 0.0
    energia_muestras: int = 0
    energia_minima: float = 100.0
    eventos: list[EventoPartido] = field(default_factory=list)

    def registrar_energia(self) -> None:
        self.energia_acumulada += self.energia_actual
        self.energia_muestras += 1
        self.energia_minima = min(self.energia_minima, self.energia_actual)

    @property
    def energia_media(self) -> float:
        if self.energia_muestras == 0:
            return self.energia_actual
        return self.energia_acumulada / self.energia_muestras


def simular_partido_baseline(
    contexto: ContextoPartido,
    *,
    parametros: ParametrosSimulacionBaseline | None = None,
) -> ResultadoSimulacionPartido:
    """Simula un partido baseline de forma determinista para una semilla dada."""

    parametros_resueltos = parametros or ParametrosSimulacionBaseline()
    semilla = contexto.semilla if contexto.semilla is not None else 20260423
    generador = Random(semilla)

    alineacion_local = contexto.alineacion_local or construir_alineacion_baseline(
        contexto.equipo_local
    )
    alineacion_visitante = contexto.alineacion_visitante or construir_alineacion_baseline(
        contexto.equipo_visitante
    )

    estado_local = _EstadoEquipoMutable(contexto.equipo_local, alineacion_local)
    estado_visitante = _EstadoEquipoMutable(contexto.equipo_visitante, alineacion_visitante)

    total_posesiones = _resolver_total_posesiones(generador, parametros_resueltos)
    estado_espacial = EstadoEspacialPartido()
    eventos: list[EventoPartido] = [EventoPartido(tipo=TipoEventoPartido.INICIO, minuto=0)]

    compartidas_local, compartidas_visitante = _calcular_cuotas_posesion(
        estado_local, estado_visitante
    )

    # Sistema de transicion de posesion
    ultimo_poseedor_id = None

    for indice in range(total_posesiones):
        minuto = min(95, 1 + int((indice / max(1, total_posesiones)) * 95))
        if minuto == 45 and not any(
            evento.tipo is TipoEventoPartido.DESCANSO for evento in eventos
        ):
            eventos.append(EventoPartido(tipo=TipoEventoPartido.DESCANSO, minuto=45))

        # Determinar nuevo poseedor con inercia
        # Si el equipo ya tenia el balon, tiene un bonus por conservarlo
        prob_local = compartidas_local
        if ultimo_poseedor_id == estado_local.equipo.id:
            prob_local += 0.15  # Inercia de posesion
        elif ultimo_poseedor_id == estado_visitante.equipo.id:
            prob_local -= 0.15

        prob_local = max(0.1, min(0.9, prob_local))

        if generador.random() < prob_local:
            atacante, defensor = estado_local, estado_visitante
        else:
            atacante, defensor = estado_visitante, estado_local

        # Si hay cambio de poseedor y no es el primer evento, narrar la transicion
        if ultimo_poseedor_id is not None and atacante.equipo.id != ultimo_poseedor_id:
            # Buscar razon de la perdida (simplificado por ahora)
            tipo_perdida = generador.choice(["Interceptacion", "Mal pase", "Presion rival"])
            transicion = EventoPartido(
                tipo=TipoEventoPartido.RECUPERACION,
                minuto=minuto,
                equipo_id=atacante.equipo.id,
                descripcion=(
                    f"Perdida de balon por {tipo_perdida}. "
                    f"Recupera {atacante.equipo.nombre}"
                ),
                metadatos={"causa": tipo_perdida},
            )
            eventos.append(transicion)

        ultimo_poseedor_id = atacante.equipo.id
        atacante.posesiones += 1
        defensor.registrar_energia()
        atacante.registrar_energia()

        eventos_posesion = _simular_posesion(
            generador=generador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            parametros=parametros_resueltos,
        )
        eventos.extend(eventos_posesion)

    eventos.append(EventoPartido(tipo=TipoEventoPartido.FINAL, minuto=95))

    estado_final = EstadoPartido(
        fase=FasePartido.FINALIZADO,
        minuto=95,
        goles_local=estado_local.goles,
        goles_visitante=estado_visitante.goles,
        eventos=tuple(eventos),
    )

    estadisticas_local = _construir_estadisticas(estado_local, total_posesiones=total_posesiones)
    estadisticas_visitante = _construir_estadisticas(
        estado_visitante, total_posesiones=total_posesiones
    )

    return ResultadoSimulacionPartido(
        contexto=contexto,
        semilla=semilla,
        parametros=parametros_resueltos,
        alineacion_local=alineacion_local,
        alineacion_visitante=alineacion_visitante,
        estado_final=estado_final,
        estado_espacial=estado_espacial,
        estadisticas_local=estadisticas_local,
        estadisticas_visitante=estadisticas_visitante,
    )


def simular_partido_iterativo(
    contexto: ContextoPartido,
    *,
    parametros: ParametrosSimulacionBaseline | None = None,
) -> Generator[EstadoIteracion, None, ResultadoSimulacionPartido]:
    """Simula un partido yielding estado en cada iteración."""
    parametros_resueltos = parametros or ParametrosSimulacionBaseline()
    semilla = contexto.semilla if contexto.semilla is not None else 20260423
    generador = Random(semilla)

    alineacion_local = contexto.alineacion_local or construir_alineacion_baseline(
        contexto.equipo_local
    )
    alineacion_visitante = contexto.alineacion_visitante or construir_alineacion_baseline(
        contexto.equipo_visitante
    )

    estado_local = _EstadoEquipoMutable(contexto.equipo_local, alineacion_local)
    estado_visitante = _EstadoEquipoMutable(contexto.equipo_visitante, alineacion_visitante)

    total_posesiones = _resolver_total_posesiones(generador, parametros_resueltos)
    estado_espacial = EstadoEspacialPartido()
    eventos: list[EventoPartido] = [EventoPartido(tipo=TipoEventoPartido.INICIO, minuto=0)]

    yield EstadoIteracion.desde_estado(
        minuto=0,
        posesion_id=None,
        evento=None,
        estado_espacial=estado_espacial,
        energia_local=estado_local.energia_actual,
        energia_visitante=estado_visitante.energia_actual,
        goles_local=0,
        goles_visitante=0,
    )

    compartidas_local, compartidas_visitante = _calcular_cuotas_posesion(
        estado_local, estado_visitante
    )

    ultimo_poseedor_id = None

    for indice in range(total_posesiones):
        minuto = min(95, 1 + int((indice / max(1, total_posesiones)) * 95))

        if minuto == 45 and not any(
            evento.tipo is TipoEventoPartido.DESCANSO for evento in eventos
        ):
            eventos.append(EventoPartido(tipo=TipoEventoPartido.DESCANSO, minuto=45))
            yield EstadoIteracion.desde_estado(
                minuto=45,
                posesion_id=None,
                evento=eventos[-1],
                estado_espacial=estado_espacial,
                energia_local=estado_local.energia_actual,
                energia_visitante=estado_visitante.energia_actual,
                goles_local=estado_local.goles,
                goles_visitante=estado_visitante.goles,
            )

        # Inercia de posesion
        prob_local = compartidas_local
        if ultimo_poseedor_id == estado_local.equipo.id:
            prob_local += 0.15
        elif ultimo_poseedor_id == estado_visitante.equipo.id:
            prob_local -= 0.15
        prob_local = max(0.1, min(0.9, prob_local))

        if generador.random() < prob_local:
            atacante, defensor = estado_local, estado_visitante
        else:
            atacante, defensor = estado_visitante, estado_local

        # Transicion explicita si hay cambio de equipo
        if ultimo_poseedor_id is not None and atacante.equipo.id != ultimo_poseedor_id:
            tipo_p = generador.choice(["Interceptacion", "Mal pase", "Presion rival"])
            transicion = EventoPartido(
                tipo=TipoEventoPartido.PASE,
                minuto=minuto,
                equipo_id=ultimo_poseedor_id,
                descripcion=f"Perdida de balon ({tipo_p}). Recupera {atacante.equipo.nombre}",
            )
            yield EstadoIteracion.desde_estado(
                minuto=minuto,
                posesion_id=ultimo_poseedor_id,
                evento=transicion,
                estado_espacial=estado_espacial,
                energia_local=estado_local.energia_actual,
                energia_visitante=estado_visitante.energia_actual,
                goles_local=estado_local.goles,
                goles_visitante=estado_visitante.goles,
            )

        ultimo_poseedor_id = atacante.equipo.id
        atacante.posesiones += 1
        defensor.registrar_energia()
        atacante.registrar_energia()

        evento_posesion = _simular_posesion(
            generador=generador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            parametros=parametros_resueltos,
        )
        eventos.extend(evento_posesion)

        for evento in evento_posesion:
            yield EstadoIteracion.desde_estado(
                minuto=minuto,
                posesion_id=atacante.equipo.id,
                evento=evento,
                estado_espacial=estado_espacial,
                energia_local=estado_local.energia_actual,
                energia_visitante=estado_visitante.energia_actual,
                goles_local=estado_local.goles,
                goles_visitante=estado_visitante.goles,
            )

    eventos.append(EventoPartido(tipo=TipoEventoPartido.FINAL, minuto=95))

    yield EstadoIteracion.desde_estado(
        minuto=95,
        posesion_id=None,
        evento=eventos[-1],
        estado_espacial=estado_espacial,
        energia_local=estado_local.energia_actual,
        energia_visitante=estado_visitante.energia_actual,
        goles_local=estado_local.goles,
        goles_visitante=estado_visitante.goles,
    )

    estado_final = EstadoPartido(
        fase=FasePartido.FINALIZADO,
        minuto=95,
        goles_local=estado_local.goles,
        goles_visitante=estado_visitante.goles,
        eventos=tuple(eventos),
    )

    estadisticas_local = _construir_estadisticas(estado_local, total_posesiones=total_posesiones)
    estadisticas_visitante = _construir_estadisticas(
        estado_visitante, total_posesiones=total_posesiones
    )

    return ResultadoSimulacionPartido(
        contexto=contexto,
        semilla=semilla,
        parametros=parametros_resueltos,
        alineacion_local=alineacion_local,
        alineacion_visitante=alineacion_visitante,
        estado_final=estado_final,
        estado_espacial=estado_espacial,
        estadisticas_local=estadisticas_local,
        estadisticas_visitante=estadisticas_visitante,
    )


def _resolver_total_posesiones(generador: Random, parametros: ParametrosSimulacionBaseline) -> int:
    minimo = max(30, parametros.posesiones_base - parametros.variacion_posesiones)
    maximo = parametros.posesiones_base + parametros.variacion_posesiones
    return generador.randint(minimo, maximo)


def _calcular_cuotas_posesion(
    local: _EstadoEquipoMutable, visitante: _EstadoEquipoMutable
) -> tuple[float, float]:
    posesion_local = _fortaleza_posesion(local.alineacion)
    posesion_visitante = _fortaleza_posesion(visitante.alineacion)
    razon = posesion_local / max(1.0, posesion_visitante)
    razon_base = min(razon, 1.06)
    razon_base = max(razon_base, 0.94)
    posesion_50 = 50.0
    cuota_local = posesion_50 + (razon_base - 1.0) * 60.0 + 4.2
    return cuota_local / 100.0, (100.0 - cuota_local) / 100.0


def _resolver_poseedor(
    *,
    generador: Random,
    local: _EstadoEquipoMutable,
    visitante: _EstadoEquipoMutable,
    posesion_local: float,
    posesion_visitante: float,
) -> tuple[_EstadoEquipoMutable, _EstadoEquipoMutable]:
    del posesion_visitante
    if generador.random() < posesion_local:
        return local, visitante
    return visitante, local


def _obtener_modificador_mentalidad(alineacion: Alineacion) -> float:
    modificador = {
        MentalidadTactica.DEFENSIVA: 0.82,
        MentalidadTactica.EQUILIBRADA: 1.0,
        MentalidadTactica.OFENSIVA: 1.18,
    }
    return modificador[alineacion.tactica.mentalidad]


def _obtener_modificador_presion(alineacion: Alineacion) -> float:
    modificador = {
        EstiloPresion.BAJA: 0.90,
        EstiloPresion.MEDIA: 1.0,
        EstiloPresion.ALTA: 1.12,
    }
    return modificador[alineacion.tactica.presion]


def _obtener_modificador_ritmo(alineacion: Alineacion) -> float:
    return 0.85 + (alineacion.tactica.ritmo / 100.0) * 0.30


def _obtener_modificador_agresividad_tactica(alineacion: Alineacion) -> float:
    return 0.85 + (alineacion.tactica.agresividad / 100.0) * 0.30


def _obtener_modificador_marcador(
    goles_atacante: int, goles_defensor: int, es_atacante: bool
) -> float:
    diferencia = goles_atacante - goles_defensor
    if diferencia >= 2:
        return 1.15 if es_atacante else 0.88
    if diferencia <= -2:
        return 0.85 if es_atacante else 1.12
    return 1.0


def _simular_posesion(
    *,
    generador: Random,
    minuto: int,
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    estado_espacial: EstadoEspacialPartido,
    parametros: ParametrosSimulacionBaseline,
) -> list[EventoPartido]:
    _aplicar_fatiga(atacante, defensor, parametros)

    mod_ataque = _obtener_modificador_mentalidad(atacante.alineacion)
    mod_defensa = _obtener_modificador_mentalidad(defensor.alineacion)
    mod_presion = _obtener_modificador_presion(defensor.alineacion)
    mod_ritmo = _obtener_modificador_ritmo(atacante.alineacion)
    mod_marcador_ataca = _obtener_modificador_marcador(atacante.goles, defensor.goles, True)
    mod_marcador_defiende = _obtener_modificador_marcador(atacante.goles, defensor.goles, False)

    ataque = (
        _fortaleza_ataque(atacante.alineacion, atacante.energia_actual)
        * mod_ataque
        * mod_ritmo
        * mod_marcador_ataca
    )
    defensa = (
        _fortaleza_defensa(defensor.alineacion, defensor.energia_actual)
        * mod_defensa
        * mod_presion
        * mod_marcador_defiende
    )
    porteria = _fortaleza_porteria(defensor.alineacion, defensor.energia_actual)

    duel = ataque / max(1.0, ataque + defensa + porteria)
    probabilidad_tiro = _acotar(
        parametros.probabilidad_base_tiro + (duel - 0.33) * 0.45,
        minimo=0.03,
        maximo=0.38,
    )
    zona_actual = estado_espacial.posicion_balon.zona
    en_zona_ataque = zona_actual in (
        ZonaCampo.ATAQUE_IZQ,
        ZonaCampo.ATAQUE_CNT,
        ZonaCampo.ATAQUE_DER,
    )
    en_banda_ataque = zona_actual in (ZonaCampo.ATAQUE_IZQ, ZonaCampo.ATAQUE_DER)

    if not en_zona_ataque:
        probabilidad_tiro *= parametros.probabilidad_base_tiro_fuera_zona

    # Si estamos en banda de ataque, probabilidad de centro
    if en_banda_ataque and generador.random() < parametros.probabilidad_centro:
        return _resolver_centro(
            generador=generador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            parametros=parametros,
        )

    if generador.random() < probabilidad_tiro:
        if not en_zona_ataque:
            nueva_posicion = _mover_a_zona_ataque(generador, estado_espacial)
            estado_espacial.mover_a(nueva_posicion)
        return _resolver_tiro(
            generador=generador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            ataque=ataque,
            defensa=defensa,
            porteria=porteria,
            parametros=parametros,
        )
    probabilidad_contraataque = _acotar(
        parametros.probabilidad_contraataque
        + (defensor.energia_actual - atacante.energia_actual) / 600,
        minimo=0.01,
        maximo=0.10,
    )
    probabilidad_falta = _acotar(
        parametros.probabilidad_base_falta
        + (_indice_agresividad(defensor.alineacion) - 50.0) / 500
        + (_obtener_modificador_agresividad_tactica(defensor.alineacion) - 1.0) * 0.15,
        minimo=0.03,
        maximo=0.28,
    )

    if generador.random() < probabilidad_contraataque and minuto > 20:
        return _resolver_contraataque(
            generador=generador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            parametros=parametros,
        )

    if generador.random() < probabilidad_tiro:
        return _resolver_tiro(
            generador=generador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            ataque=ataque,
            defensa=defensa,
            porteria=porteria,
            parametros=parametros,
        )

    if generador.random() < probabilidad_falta:
        return _resolver_falta(
            generador=generador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            parametros=parametros,
        )

    pasador = _elegir_jugador_para_pase(generador, atacante.alineacion.titulares)
    _procesar_pase(generador, estado_espacial, pasador)
    evento = EventoPartido(
        tipo=TipoEventoPartido.PASE,
        minuto=minuto,
        equipo_id=atacante.equipo.id,
        jugador_principal_id=pasador.id,
        descripcion=f"Posesion elaborada de {atacante.equipo.nombre}",
    )
    atacante.eventos.append(evento)
    return [evento]


def _resolver_tiro(
    *,
    generador: Random,
    minuto: int,
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    estado_espacial: EstadoEspacialPartido,
    ataque: float,
    defensa: float,
    porteria: float,
    parametros: ParametrosSimulacionBaseline,
) -> list[EventoPartido]:
    atacante.tiros += 1
    tirador = _elegir_tirador(generador, atacante.alineacion.titulares)

    eventos: list[EventoPartido] = [
        EventoPartido(
            tipo=TipoEventoPartido.TIRO,
            minuto=minuto,
            equipo_id=atacante.equipo.id,
            jugador_principal_id=tirador.id,
            descripcion=f"Tiro de {tirador.nombre}",
        )
    ]

    calidad_tiro = _calidad_individual_tiro(tirador, atacante.energia_actual)
    bloque_defensivo = defensa * 0.55 + porteria * 0.45
    probabilidad_puerta = _acotar(
        parametros.probabilidad_base_tiro_puerta + (calidad_tiro - bloque_defensivo) / 300,
        minimo=0.18,
        maximo=0.65,
    )
    if generador.random() >= probabilidad_puerta:
        if generador.random() < parametros.probabilidad_base_corner:
            atacante.corners += 1
            corner = EventoPartido(
                tipo=TipoEventoPartido.CORNER,
                minuto=minuto,
                equipo_id=atacante.equipo.id,
                descripcion=f"Corner para {atacante.equipo.nombre}",
            )
            atacante.eventos.append(corner)
            eventos.append(corner)
        atacante.eventos.extend(eventos)
        return eventos

    atacante.tiros_a_puerta += 1
    posicion_tiro = (estado_espacial.posicion_balon.x, estado_espacial.posicion_balon.y)
    resultado_xg = calcular_xg(
        tirador=tirador,
        posicion_tiro=posicion_tiro,
        energia=atacante.energia_actual,
    )
    probabilidad_gol = _acotar(
        resultado_xg.xg * (parametros.probabilidad_base_gol / 0.28),
        minimo=0.001,
        maximo=0.85,
    )
    # Rebalance temporal de goles para acercar la distribución a LaLiga.
    if minuto <= 15:
        probabilidad_gol *= 0.62
    elif minuto <= 30:
        probabilidad_gol *= 0.90
    elif minuto <= 45:
        probabilidad_gol *= 0.82
    elif minuto <= 60:
        probabilidad_gol *= 0.98
    elif minuto <= 75:
        probabilidad_gol *= 1.06
    elif minuto <= 90:
        probabilidad_gol *= 1.45
    else:
        probabilidad_gol *= 2.20
    probabilidad_gol = _acotar(probabilidad_gol, minimo=0.001, maximo=0.92)

    if generador.random() < probabilidad_gol:
        atacante.goles += 1
        gol = EventoPartido(
            tipo=TipoEventoPartido.GOL,
            minuto=minuto,
            equipo_id=atacante.equipo.id,
            jugador_principal_id=tirador.id,
            descripcion=f"Gol de {tirador.nombre}",
        )
        atacante.eventos.append(gol)
        eventos.append(gol)
        return eventos

    portero = _obtener_portero(defensor.alineacion)
    parada = EventoPartido(
        tipo=TipoEventoPartido.PARADA,
        minuto=minuto,
        equipo_id=defensor.equipo.id,
        jugador_principal_id=portero.id,
        descripcion=f"Parada de {portero.nombre}",
    )
    defensor.eventos.append(parada)
    eventos.append(parada)
    return eventos


def _resolver_centro(
    *,
    generador: Random,
    minuto: int,
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    estado_espacial: EstadoEspacialPartido,
    parametros: ParametrosSimulacionBaseline,
) -> list[EventoPartido]:
    """Resuelve una jugada de centro al área."""
    pasador = _elegir_jugador_para_pase(generador, atacante.alineacion.titulares)
    eventos = [
        EventoPartido(
            tipo=TipoEventoPartido.CENTRO,
            minuto=minuto,
            equipo_id=atacante.equipo.id,
            jugador_principal_id=pasador.id,
            descripcion=f"Centro al área de {pasador.nombre}",
        )
    ]

    calidad_centro = pasador.atributos.pase_elevado * 0.7 + pasador.atributos.efecto * 0.3
    dificultad = 40 + generador.uniform(0, 40)

    if generador.random() * 100 < calidad_centro - dificultad:
        # Centro exitoso -> Duelo aéreo
        rematador = _elegir_tirador(generador, atacante.alineacion.titulares)
        defensor_aire = _elegir_defensor_agresivo(generador, defensor.alineacion.titulares)

        if _resolver_duelo_aereo(generador, rematador, defensor_aire):
            # Remate exitoso
            duelo = EventoPartido(
                tipo=TipoEventoPartido.DUELO_AEREO,
                minuto=minuto,
                equipo_id=atacante.equipo.id,
                jugador_principal_id=rematador.id,
                descripcion=f"{rematador.nombre} gana el duelo aéreo",
            )
            eventos.append(duelo)
            atacante.eventos.append(duelo)

            return eventos + _resolver_tiro(
                generador=generador,
                minuto=minuto,
                atacante=atacante,
                defensor=defensor,
                estado_espacial=estado_espacial,
                ataque=70.0,
                defensa=50.0,
                porteria=60.0,
                parametros=parametros,
            )

    return eventos


def _resolver_duelo_aereo(generador: Random, atacante: Jugador, defensor: Jugador) -> bool:
    """Resuelve un duelo por arriba entre dos jugadores."""
    power_at = (
        atacante.atributos.salto * 0.4
        + atacante.atributos.contacto_fisico * 0.3
        + atacante.atributos.cabeza * 0.3
    )
    power_def = (
        defensor.atributos.salto * 0.4
        + defensor.atributos.contacto_fisico * 0.4
        + defensor.atributos.awareness_defensivo * 0.2
    )

    total = power_at + power_def
    prob_at = power_at / max(1.0, total)
    return generador.random() < prob_at


def _resolver_contraataque(
    *,
    generador: Random,
    minuto: int,
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    estado_espacial: EstadoEspacialPartido,
    parametros: ParametrosSimulacionBaseline,
) -> list[EventoPartido]:
    evento = EventoPartido(
        tipo=TipoEventoPartido.CONTRAATAQUE,
        minuto=minuto,
        equipo_id=atacante.equipo.id,
        descripcion=f"Contraataque de {atacante.equipo.nombre}",
    )
    atacante.eventos.append(evento)

    eventos = [evento]

    ataque = _fortaleza_ataque(atacante.alineacion, atacante.energia_actual) * 0.50
    defensa = _fortaleza_defensa(defensor.alineacion, defensor.energia_actual) * 0.35
    porteria = _fortaleza_porteria(defensor.alineacion, defensor.energia_actual) * 0.15

    probabilidad_tiro = _acotar(0.40 + ataque / 200, minimo=0.20, maximo=0.65)

    if generador.random() < probabilidad_tiro:
        return _resolver_tiro(
            generador=generador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            ataque=ataque,
            defensa=defensa,
            porteria=porteria,
            parametros=parametros,
        )

    return eventos


def _resolver_falta(
    *,
    generador: Random,
    minuto: int,
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    parametros: ParametrosSimulacionBaseline,
) -> list[EventoPartido]:
    infractor = _elegir_defensor_agresivo(generador, defensor.alineacion.titulares)
    defensor.faltas += 1
    eventos = [
        EventoPartido(
            tipo=TipoEventoPartido.FALTA,
            minuto=minuto,
            equipo_id=defensor.equipo.id,
            jugador_principal_id=infractor.id,
            descripcion=f"Falta cometida por {infractor.nombre}",
        )
    ]

    probabilidad_roja = _acotar(
        parametros.probabilidad_roja + (infractor.atributos.agresividad - 50) / 5000,
        minimo=0.001,
        maximo=0.03,
    )
    probabilidad_amarilla = _acotar(
        parametros.probabilidad_amarilla
        + (infractor.atributos.agresividad + infractor.atributos.engagement_defensivo - 100) / 400,
        minimo=0.02,
        maximo=0.45,
    )

    if generador.random() < probabilidad_roja:
        defensor.tarjetas_rojas += 1
        roja = EventoPartido(
            tipo=TipoEventoPartido.TARJETA_ROJA,
            minuto=minuto,
            equipo_id=defensor.equipo.id,
            jugador_principal_id=infractor.id,
            descripcion=f"Tarjeta roja para {infractor.nombre}",
        )
        eventos.append(roja)
    elif generador.random() < probabilidad_amarilla:
        defensor.tarjetas_amarillas += 1
        amarilla = EventoPartido(
            tipo=TipoEventoPartido.TARJETA_AMARILLA,
            minuto=minuto,
            equipo_id=defensor.equipo.id,
            jugador_principal_id=infractor.id,
            descripcion=f"Tarjeta amarilla para {infractor.nombre}",
        )
        eventos.append(amarilla)

    defensor.eventos.extend(eventos)
    return eventos


def _construir_estadisticas(
    estado: _EstadoEquipoMutable, *, total_posesiones: int
) -> EstadisticasEquipoPartido:
    posesion_pct = 0.0 if total_posesiones == 0 else (estado.posesiones / total_posesiones) * 100.0
    return EstadisticasEquipoPartido(
        equipo_id=estado.equipo.id,
        nombre_equipo=estado.equipo.nombre,
        posesiones=estado.posesiones,
        posesion_pct=round(posesion_pct, 3),
        tiros=estado.tiros,
        tiros_a_puerta=estado.tiros_a_puerta,
        goles=estado.goles,
        faltas=estado.faltas,
        corners=estado.corners,
        tarjetas_amarillas=estado.tarjetas_amarillas,
        tarjetas_rojas=estado.tarjetas_rojas,
        energia_media=round(estado.energia_media, 3),
        energia_minima=round(estado.energia_minima, 3),
    )


def _aplicar_fatiga(
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    parametros: ParametrosSimulacionBaseline,
) -> None:
    atacante.energia_actual = max(
        35.0, atacante.energia_actual - parametros.coste_energia_equipo_poseedor
    )
    defensor.energia_actual = max(
        35.0, defensor.energia_actual - parametros.coste_energia_equipo_defensor
    )


def _fortaleza_posesion(alineacion: Alineacion) -> float:
    total = 0.0
    pesos = 0.0
    for jugador in alineacion.titulares:
        if jugador.es_portero:
            continue
        peso = {
            PosicionJugador.MEDIOCENTRO: 1.3,
            PosicionJugador.MEDIAPUNTA: 1.2,
            PosicionJugador.EXTREMO: 1.05,
            PosicionJugador.DELANTERO: 0.95,
            PosicionJugador.LATERAL: 0.9,
            PosicionJugador.CENTRAL: 0.8,
            PosicionJugador.DESCONOCIDA: 0.8,
            PosicionJugador.PORTERO: 0.0,
        }[jugador.posicion]
        total += peso * (
            jugador.atributos.pase_bajo * 0.30
            + jugador.atributos.control_balon * 0.25
            + jugador.atributos.posesion_cerrada * 0.20
            + jugador.atributos.pase_elevado * 0.10
            + jugador.atributos.regate * 0.10
            + jugador.atributos.resistencia * 0.05
        )
        pesos += peso
    return total / max(1.0, pesos)


def _fortaleza_ataque(alineacion: Alineacion, energia_actual: float) -> float:
    energia_factor = 0.72 + (energia_actual / 100.0) * 0.28
    total = 0.0
    pesos = 0.0
    for jugador in alineacion.titulares:
        if jugador.es_portero:
            continue
        peso = {
            PosicionJugador.DELANTERO: 1.45,
            PosicionJugador.EXTREMO: 1.25,
            PosicionJugador.MEDIAPUNTA: 1.18,
            PosicionJugador.MEDIOCENTRO: 1.0,
            PosicionJugador.LATERAL: 0.85,
            PosicionJugador.CENTRAL: 0.65,
            PosicionJugador.DESCONOCIDA: 0.8,
            PosicionJugador.PORTERO: 0.0,
        }[jugador.posicion]
        total += peso * (
            jugador.atributos.finalizacion * 0.28
            + jugador.atributos.potencia_tiro * 0.20
            + jugador.atributos.control_balon * 0.12
            + jugador.atributos.regate * 0.12
            + jugador.atributos.awareness_ofensivo * 0.14
            + jugador.atributos.pase_bajo * 0.08
            + jugador.atributos.velocidad * 0.06
        )
        pesos += peso
    return (total / max(1.0, pesos)) * energia_factor


def _fortaleza_defensa(alineacion: Alineacion, energia_actual: float) -> float:
    energia_factor = 0.74 + (energia_actual / 100.0) * 0.26
    total = 0.0
    pesos = 0.0
    for jugador in alineacion.titulares:
        if jugador.es_portero:
            continue
        peso = {
            PosicionJugador.CENTRAL: 1.35,
            PosicionJugador.LATERAL: 1.05,
            PosicionJugador.MEDIOCENTRO: 1.05,
            PosicionJugador.MEDIAPUNTA: 0.75,
            PosicionJugador.EXTREMO: 0.65,
            PosicionJugador.DELANTERO: 0.55,
            PosicionJugador.DESCONOCIDA: 0.75,
            PosicionJugador.PORTERO: 0.0,
        }[jugador.posicion]
        total += peso * (
            jugador.atributos.awareness_defensivo * 0.28
            + jugador.atributos.tackles * 0.23
            + jugador.atributos.engagement_defensivo * 0.20
            + jugador.atributos.contacto_fisico * 0.10
            + jugador.atributos.velocidad * 0.09
            + jugador.atributos.salto * 0.10
        )
        pesos += peso
    return (total / max(1.0, pesos)) * energia_factor


def _fortaleza_porteria(alineacion: Alineacion, energia_actual: float) -> float:
    portero = _obtener_portero(alineacion)
    energia_factor = 0.78 + (energia_actual / 100.0) * 0.22
    return (
        portero.atributos.awareness_portero * 0.35
        + portero.atributos.reflejos * 0.35
        + portero.atributos.atrape * 0.15
        + portero.atributos.alcance * 0.15
    ) * energia_factor


def _indice_agresividad(alineacion: Alineacion) -> float:
    total = 0.0
    for jugador in alineacion.titulares:
        total += jugador.atributos.agresividad * 0.6 + jugador.atributos.engagement_defensivo * 0.4
    return total / max(1, len(alineacion.titulares))


def _calidad_individual_tiro(jugador: Jugador, energia_actual: float) -> float:
    energia_factor = 0.72 + (energia_actual / 100.0) * 0.28
    return (
        jugador.atributos.finalizacion * 0.35
        + jugador.atributos.potencia_tiro * 0.25
        + jugador.atributos.control_balon * 0.10
        + jugador.atributos.awareness_ofensivo * 0.15
        + jugador.atributos.regate * 0.10
        + jugador.overall * 0.05
    ) * energia_factor


def _elegir_tirador(generador: Random, jugadores: tuple[Jugador, ...]) -> Jugador:
    pesos: list[float] = []
    candidatos = list(jugadores)
    for jugador in candidatos:
        peso_posicion = {
            PosicionJugador.DELANTERO: 1.8,
            PosicionJugador.EXTREMO: 1.45,
            PosicionJugador.MEDIAPUNTA: 1.25,
            PosicionJugador.MEDIOCENTRO: 0.85,
            PosicionJugador.LATERAL: 0.55,
            PosicionJugador.CENTRAL: 0.35,
            PosicionJugador.PORTERO: 0.05,
            PosicionJugador.DESCONOCIDA: 0.4,
        }[jugador.posicion]
        peso = peso_posicion * (
            jugador.atributos.finalizacion * 0.45
            + jugador.atributos.awareness_ofensivo * 0.20
            + jugador.atributos.potencia_tiro * 0.20
            + jugador.overall * 0.15
        )
        pesos.append(max(0.1, peso))
    return generador.choices(candidatos, weights=pesos, k=1)[0]


def _elegir_jugador_para_pase(generador: Random, jugadores: tuple[Jugador, ...]) -> Jugador:
    candidatos = [jugador for jugador in jugadores if not jugador.es_portero]
    pesos = [
        max(
            0.1,
            jugador.atributos.pase_bajo * 0.4
            + jugador.atributos.control_balon * 0.25
            + jugador.atributos.posesion_cerrada * 0.15
            + jugador.atributos.awareness_ofensivo * 0.1
            + jugador.overall * 0.1,
        )
        for jugador in candidatos
    ]
    return generador.choices(candidatos, weights=pesos, k=1)[0]


def _elegir_defensor_agresivo(generador: Random, jugadores: tuple[Jugador, ...]) -> Jugador:
    candidatos = [jugador for jugador in jugadores if not jugador.es_portero]
    pesos = [
        max(
            0.1,
            jugador.atributos.agresividad * 0.5
            + jugador.atributos.engagement_defensivo * 0.3
            + jugador.atributos.tackles * 0.2,
        )
        for jugador in candidatos
    ]
    return generador.choices(candidatos, weights=pesos, k=1)[0]


def _obtener_portero(alineacion: Alineacion) -> Jugador:
    for jugador in alineacion.titulares:
        if jugador.es_portero:
            return jugador
    raise ValueError("La alineacion no contiene portero.")


def _mover_a_zona_ataque(generador: Random, estado_espacial: EstadoEspacialPartido) -> Coordenada:
    zona_actual = estado_espacial.posicion_balon.zona
    if zona_actual in (
        ZonaCampo.DEFENSA_IZQ,
        ZonaCampo.DEFENSA_CNT,
        ZonaCampo.DEFENSA_DER,
    ):
        x_base = 67.0
    else:
        x_base = 80.0
    y = generador.uniform(20.0, 80.0)
    return Coordenada(x_base, y)


def _procesar_pase(
    generador: Random, estado_espacial: EstadoEspacialPartido, pasador: Jugador
) -> None:
    zona_actual = estado_espacial.posicion_balon.zona
    probabilidad_avance = _calcular_probabilidad_avance(pasador, zona_actual)

    if generador.random() < probabilidad_avance:
        nueva_posicion = _avanzar_en_el_campo(generador)
        estado_espacial.mover_a(nueva_posicion)
    else:
        nueva_posicion = _mover_lateralmente(generador)
        estado_espacial.mover_a(nueva_posicion)


def _calcular_probabilidad_avance(pasador: Jugador, zona_actual: ZonaCampo) -> float:
    calidad_pase = (
        pasador.atributos.pase_bajo * 0.35
        + pasador.atributos.control_balon * 0.25
        + pasador.atributos.pase_elevado * 0.20
        + pasador.atributos.awareness_ofensivo * 0.10
        + pasador.atributos.regate * 0.10
    )
    if zona_actual in (
        ZonaCampo.DEFENSA_IZQ,
        ZonaCampo.DEFENSA_CNT,
        ZonaCampo.DEFENSA_DER,
    ):
        base = 0.72
    elif zona_actual in (
        ZonaCampo.MEDIO_IZQ,
        ZonaCampo.MEDIO_CNT,
        ZonaCampo.MEDIO_DER,
    ):
        base = 0.48
    else:
        base = 0.35
    return _acotar(calidad_pase / 100 * base, minimo=0.15, maximo=0.85)


def _avanzar_en_el_campo(generador: Random) -> Coordenada:
    x = generador.uniform(67.0, 100.0)
    y = generador.uniform(15.0, 85.0)
    return Coordenada(x, y)


def _mover_lateralmente(generador: Random) -> Coordenada:
    x = generador.uniform(20.0, 80.0)
    y = generador.uniform(15.0, 85.0)
    return Coordenada(x, y)


def _acotar(valor: float, *, minimo: float, maximo: float) -> float:
    return max(minimo, min(maximo, valor))
