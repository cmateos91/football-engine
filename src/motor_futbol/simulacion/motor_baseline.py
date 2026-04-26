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
from motor_futbol.simulacion.narracion import NarradorPartido
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
    es_local: bool = False
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
    narrador = NarradorPartido(generador)

    alineacion_local = contexto.alineacion_local or construir_alineacion_baseline(
        contexto.equipo_local
    )
    alineacion_visitante = contexto.alineacion_visitante or construir_alineacion_baseline(
        contexto.equipo_visitante
    )

    estado_local = _EstadoEquipoMutable(contexto.equipo_local, alineacion_local)
    estado_local.es_local = True
    estado_visitante = _EstadoEquipoMutable(contexto.equipo_visitante, alineacion_visitante)

    total_posesiones = _resolver_total_posesiones(generador, parametros_resueltos)
    estado_espacial = EstadoEspacialPartido()
    eventos: list[EventoPartido] = [EventoPartido(tipo=TipoEventoPartido.INICIO, minuto=0)]

    compartidas_local, compartidas_visitante = _calcular_cuotas_posesion(
        estado_local, estado_visitante
    )

    # Sistema de transicion de posesion
    ultimo_poseedor_id = None
    ultimo_minuto_recuperacion = -10

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
        if (
            ultimo_poseedor_id is not None
            and atacante.equipo.id != ultimo_poseedor_id
            and minuto - ultimo_minuto_recuperacion >= 2
            and generador.random() < 0.72
        ):
            # Buscar razon de la perdida (simplificado por ahora)
            tipo_perdida = generador.choice(["Interceptacion", "Mal pase", "Presion rival"])
            transicion = EventoPartido(
                tipo=TipoEventoPartido.RECUPERACION,
                minuto=minuto,
                equipo_id=atacante.equipo.id,
                descripcion=_descripcion_recuperacion(
                    narrador=narrador,
                    equipo=atacante.equipo.nombre,
                    causa=tipo_perdida,
                    zona=estado_espacial.posicion_balon.zona,
                ),
                metadatos={"causa": tipo_perdida},
            )
            eventos.append(transicion)
            ultimo_minuto_recuperacion = minuto

        ultimo_poseedor_id = atacante.equipo.id
        atacante.posesiones += 1
        defensor.registrar_energia()
        atacante.registrar_energia()

        eventos_posesion = _simular_posesion(
            generador=generador,
            narrador=narrador,
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
    narrador = NarradorPartido(generador)

    alineacion_local = contexto.alineacion_local or construir_alineacion_baseline(
        contexto.equipo_local
    )
    alineacion_visitante = contexto.alineacion_visitante or construir_alineacion_baseline(
        contexto.equipo_visitante
    )

    estado_local = _EstadoEquipoMutable(contexto.equipo_local, alineacion_local)
    estado_local.es_local = True
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
    ultimo_minuto_recuperacion = -10

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
        if (
            ultimo_poseedor_id is not None
            and atacante.equipo.id != ultimo_poseedor_id
            and minuto - ultimo_minuto_recuperacion >= 2
            and generador.random() < 0.72
        ):
            tipo_p = generador.choice(["Interceptacion", "Mal pase", "Presion rival"])
            transicion = EventoPartido(
                tipo=TipoEventoPartido.RECUPERACION,
                minuto=minuto,
                equipo_id=atacante.equipo.id,
                descripcion=_descripcion_recuperacion(
                    narrador=narrador,
                    equipo=atacante.equipo.nombre,
                    causa=tipo_p,
                    zona=estado_espacial.posicion_balon.zona,
                ),
            )
            yield EstadoIteracion.desde_estado(
                minuto=minuto,
                posesion_id=atacante.equipo.id,
                evento=transicion,
                estado_espacial=estado_espacial,
                energia_local=estado_local.energia_actual,
                energia_visitante=estado_visitante.energia_actual,
                goles_local=estado_local.goles,
                goles_visitante=estado_visitante.goles,
            )
            ultimo_minuto_recuperacion = minuto

        ultimo_poseedor_id = atacante.equipo.id
        atacante.posesiones += 1
        defensor.registrar_energia()
        atacante.registrar_energia()

        evento_posesion = _simular_posesion(
            generador=generador,
            narrador=narrador,
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
    # Ampliar el rango de posesión para reflejar mejor las diferencias de calidad
    razon_base = min(razon, 1.18)
    razon_base = max(razon_base, 0.82)
    posesion_50 = 50.0
    cuota_local = posesion_50 + (razon_base - 1.0) * 100.0 + 6.5
    return cuota_local / 100.0, (100.0 - cuota_local) / 100.0


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
    narrador: NarradorPartido,
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
    if atacante.es_local:
        ataque *= 1.08

    defensa = (
        _fortaleza_defensa(defensor.alineacion, defensor.energia_actual)
        * mod_defensa
        * mod_presion
        * mod_marcador_defiende
    )
    if defensor.es_local:
        defensa *= 1.08
    porteria = _fortaleza_porteria(defensor.alineacion, defensor.energia_actual)

    # Usar exponente para amplificar las diferencias de calidad entre equipos
    ratio_bruto = ataque / max(1.0, defensa + porteria)
    duel = ratio_bruto ** 1.8 / (1.0 + ratio_bruto ** 1.8)
    probabilidad_tiro = _acotar(
        parametros.probabilidad_base_tiro + (duel - 0.33) * 0.60,
        minimo=0.03,
        maximo=0.45,
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

    # 1. Triggers de eventos a balón parado / especiales
    # Si estamos en banda de ataque, probabilidad de centro
    if en_banda_ataque and generador.random() < parametros.probabilidad_centro:
        return _resolver_centro(
            generador=generador,
            narrador=narrador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            parametros=parametros,
        )

    # Probabilidad de contraataque
    probabilidad_contraataque = _acotar(
        parametros.probabilidad_contraataque
        + (defensor.energia_actual - atacante.energia_actual) / 600,
        minimo=0.01,
        maximo=0.10,
    )
    if generador.random() < probabilidad_contraataque and minuto > 20:
        return _resolver_contraataque(
            generador=generador,
            narrador=narrador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            parametros=parametros,
        )

    # Probabilidad de falta (puede derivar en penalti o falta directa)
    probabilidad_falta = _acotar(
        parametros.probabilidad_base_falta
        + (_indice_agresividad(defensor.alineacion) - 50.0) / 500
        + (_obtener_modificador_agresividad_tactica(defensor.alineacion) - 1.0) * 0.15,
        minimo=0.03,
        maximo=0.28,
    )
    if generador.random() < probabilidad_falta:
        return _resolver_falta(
            generador=generador,
            narrador=narrador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            parametros=parametros,
        )

    # 2. Tiro de campo
    if generador.random() < probabilidad_tiro:
        if not en_zona_ataque:
            nueva_posicion = _mover_a_zona_ataque(generador, estado_espacial)
            estado_espacial.mover_a(nueva_posicion)
        return _resolver_tiro(
            generador=generador,
            narrador=narrador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            ataque=ataque,
            defensa=defensa,
            porteria=porteria,
            parametros=parametros,
            tipo_jugada="open_play",
        )

    # 3. Posesión elaborada (Pase)
    pasador = _elegir_jugador_para_pase(generador, atacante.alineacion.titulares)
    _procesar_pase(generador, estado_espacial, pasador)
    evento = EventoPartido(
        tipo=TipoEventoPartido.PASE,
        minuto=minuto,
        equipo_id=atacante.equipo.id,
        jugador_principal_id=pasador.id,
        descripcion=_descripcion_posesion(
            narrador=narrador,
            equipo=atacante.equipo.nombre,
            jugador=pasador.nombre,
            zona=estado_espacial.posicion_balon.zona,
        ),
    )
    atacante.eventos.append(evento)
    return [evento]


def _resolver_tiro(
    *,
    generador: Random,
    narrador: NarradorPartido,
    minuto: int,
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    estado_espacial: EstadoEspacialPartido,
    ataque: float,
    defensa: float,
    porteria: float,
    parametros: ParametrosSimulacionBaseline,
    tipo_jugada: str = "open_play",
    es_balon_parado: bool = False,
    forzar_a_puerta: bool = False,
    tirador_fijado: Jugador | None = None,
) -> list[EventoPartido]:
    atacante.tiros += 1
    tirador = tirador_fijado or _elegir_tirador(generador, atacante.alineacion.titulares)

    posicion_tiro = (estado_espacial.posicion_balon.x, estado_espacial.posicion_balon.y)
    resultado_xg = calcular_xg(
        tirador=tirador,
        posicion_tiro=posicion_tiro,
        energia=atacante.energia_actual,
    )

    eventos: list[EventoPartido] = [
        EventoPartido(
            tipo=TipoEventoPartido.TIRO,
            minuto=minuto,
            equipo_id=atacante.equipo.id,
            jugador_principal_id=tirador.id,
            descripcion=_descripcion_tiro(
                narrador=narrador,
                jugador=tirador.nombre,
                equipo=atacante.equipo.nombre,
                minuto=minuto,
                zona=estado_espacial.posicion_balon.zona,
                tipo_jugada=tipo_jugada,
            ),
            metadatos={"xg": resultado_xg.xg},
        )
    ]

    calidad_tiro = _calidad_individual_tiro(tirador, atacante.energia_actual)
    bloque_defensivo = defensa * 0.55 + porteria * 0.45
    probabilidad_puerta = _acotar(
        parametros.probabilidad_base_tiro_puerta + (calidad_tiro - bloque_defensivo) / 180,
        minimo=0.18,
        maximo=0.65,
    )
    forzar_tiro_a_puerta = locals().get("forzar_a_puerta", False)
    if not forzar_tiro_a_puerta and generador.random() >= probabilidad_puerta:
        # Si el tiro no va a puerta, puede ser corner (evitar recursión infinita)
        if not es_balon_parado and generador.random() < parametros.probabilidad_base_corner * 1.2:
            return eventos + _resolver_corner(
                generador=generador,
                narrador=narrador,
                minuto=minuto,
                atacante=atacante,
                defensor=defensor,
                estado_espacial=estado_espacial,
                parametros=parametros,
            )
        atacante.eventos.extend(eventos)
        return eventos

    atacante.tiros_a_puerta += 1
    probabilidad_gol = _acotar(
        resultado_xg.xg * (parametros.probabilidad_base_gol / 0.28),
        minimo=0.001,
        maximo=0.85,
    )
    # Rebalance temporal de goles
    if minuto <= 15:
        probabilidad_gol *= 0.55
    elif minuto <= 30:
        probabilidad_gol *= 0.82
    elif minuto <= 45:
        probabilidad_gol *= 0.72
    elif minuto <= 60:
        probabilidad_gol *= 0.85
    elif minuto <= 75:
        probabilidad_gol *= 1.08
    elif minuto <= 90:
        probabilidad_gol *= 1.55
    else:
        probabilidad_gol *= 4.50
    probabilidad_gol = _acotar(probabilidad_gol, minimo=0.001, maximo=0.92)

    if generador.random() < probabilidad_gol:
        atacante.goles += 1
        asistidor = None
        if generador.random() < 0.65 and tipo_jugada != "penalty":
            candidatos_asistencia = [j for j in atacante.alineacion.titulares if j.id != tirador.id]
            if candidatos_asistencia:
                asistidor = _elegir_jugador_para_pase(generador, tuple(candidatos_asistencia))

        gol = EventoPartido(
            tipo=TipoEventoPartido.GOL,
            minuto=minuto,
            equipo_id=atacante.equipo.id,
            jugador_principal_id=tirador.id,
            jugador_secundario_id=asistidor.id if asistidor else None,
            descripcion=_descripcion_gol(
                narrador=narrador,
                jugador=tirador.nombre,
                asistidor=asistidor.nombre if asistidor else None,
                tipo_jugada=tipo_jugada,
                minuto=minuto,
            ),
            metadatos={"tipo_gol": tipo_jugada},
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
        descripcion=_descripcion_parada(
            narrador=narrador,
            portero=portero.nombre,
            equipo=defensor.equipo.nombre,
        ),
    )
    defensor.eventos.append(parada)
    eventos.append(parada)

    # Tras una parada, también puede haber corner (evitar recursión infinita)
    if not es_balon_parado and generador.random() < parametros.probabilidad_base_corner * 1.8:
        return eventos + _resolver_corner(
            generador=generador,
            narrador=narrador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            parametros=parametros,
        )

    return eventos


def _resolver_centro(
    *,
    generador: Random,
    narrador: NarradorPartido,
    minuto: int,
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    estado_espacial: EstadoEspacialPartido,
    parametros: ParametrosSimulacionBaseline,
    es_balon_parado: bool = False,
    centrador_fijado: Jugador | None = None,
) -> list[EventoPartido]:
    """Resuelve una jugada de centro al área."""
    pasador = centrador_fijado or _elegir_jugador_para_pase(generador, atacante.alineacion.titulares)
    eventos = [
        EventoPartido(
            tipo=TipoEventoPartido.CENTRO,
            minuto=minuto,
            equipo_id=atacante.equipo.id,
            jugador_principal_id=pasador.id,
            descripcion=_descripcion_centro(
                narrador=narrador, jugador=pasador.nombre, equipo=atacante.equipo.nombre
            ),
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
                descripcion=_descripcion_duelo_aereo(
                    narrador=narrador, jugador=rematador.nombre, contexto="en el área"
                ),
            )
            eventos.append(duelo)
            atacante.eventos.append(duelo)

            # Movemos el balón al área para el tiro
            estado_espacial.mover_a(Coordenada(92.0, 50.0))

            return eventos + _resolver_tiro(
                generador=generador,
                narrador=narrador,
                minuto=minuto,
                atacante=atacante,
                defensor=defensor,
                estado_espacial=estado_espacial,
                ataque=75.0,
                defensa=45.0,
                porteria=60.0,
                parametros=parametros,
                tipo_jugada="cross",
                es_balon_parado=es_balon_parado,
            )
        else:
            # Si el defensor gana el duelo, hay una pequeña probabilidad de autogol
            if generador.random() < 0.04:
                atacante.goles += 1
                atacante.tiros += 1
                atacante.tiros_a_puerta += 1
                autogol = EventoPartido(
                    tipo=TipoEventoPartido.GOL,
                    minuto=minuto,
                    equipo_id=atacante.equipo.id,  # El gol sube al atacante
                    jugador_principal_id=defensor_aire.id,
                    descripcion=_descripcion_autogol(
                        narrador=narrador, jugador=defensor_aire.nombre
                    ),
                    metadatos={"tipo_gol": "own_goal"},
                )
                atacante.eventos.append(autogol)
                eventos.append(autogol)
                return eventos

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
    narrador: NarradorPartido,
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
        descripcion=_descripcion_contraataque(narrador=narrador, equipo=atacante.equipo.nombre),
    )
    atacante.eventos.append(evento)

    eventos = [evento]

    # Progresión rápida al área
    estado_espacial.mover_a(Coordenada(85.0, generador.uniform(30, 70)))

    ataque = _fortaleza_ataque(atacante.alineacion, atacante.energia_actual) * 0.50
    defensa = _fortaleza_defensa(defensor.alineacion, defensor.energia_actual) * 0.35
    porteria = _fortaleza_porteria(defensor.alineacion, defensor.energia_actual) * 0.15

    probabilidad_tiro = _acotar(0.40 + ataque / 200, minimo=0.20, maximo=0.65)

    if generador.random() < probabilidad_tiro:
        return eventos + _resolver_tiro(
            generador=generador,
            narrador=narrador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            ataque=ataque,
            defensa=defensa,
            porteria=porteria,
            parametros=parametros,
            tipo_jugada="counter",
        )

    return eventos


def _resolver_falta(
    *,
    generador: Random,
    narrador: NarradorPartido,
    minuto: int,
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    estado_espacial: EstadoEspacialPartido,
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
            descripcion=_descripcion_falta(
                narrador=narrador,
                infractor=infractor.nombre,
                zona=estado_espacial.posicion_balon.zona,
            ),
        )
    ]

    # Tarjetas
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
            descripcion=_descripcion_tarjeta(narrador=narrador, infractor=infractor.nombre, roja=True),
        )
        eventos.append(roja)
    elif generador.random() < probabilidad_amarilla:
        defensor.tarjetas_amarillas += 1
        amarilla = EventoPartido(
            tipo=TipoEventoPartido.TARJETA_AMARILLA,
            minuto=minuto,
            equipo_id=defensor.equipo.id,
            jugador_principal_id=infractor.id,
            descripcion=_descripcion_tarjeta(
                narrador=narrador, infractor=infractor.nombre, roja=False
            ),
        )
        eventos.append(amarilla)

    defensor.eventos.extend(eventos)

    # ¿Penalti, Falta Directa o Falta simple?
    zona = estado_espacial.posicion_balon.zona
    en_area = zona == ZonaCampo.ATAQUE_CNT and estado_espacial.posicion_balon.x > 84

    if en_area and generador.random() < parametros.probabilidad_penalti:
        return eventos + _resolver_penalti(
            generador=generador,
            narrador=narrador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            parametros=parametros,
        )

    if zona in (ZonaCampo.ATAQUE_CNT, ZonaCampo.MEDIO_CNT) and generador.random() < 0.30:
        return eventos + _resolver_falta_directa(
            generador=generador,
            narrador=narrador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            parametros=parametros,
        )

    return eventos


def _resolver_penalti(
    *,
    generador: Random,
    narrador: NarradorPartido,
    minuto: int,
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    estado_espacial: EstadoEspacialPartido,
    parametros: ParametrosSimulacionBaseline,
) -> list[EventoPartido]:
    tirador = _elegir_tirador(generador, atacante.alineacion.titulares)
    evento_penalti = EventoPartido(
        tipo=TipoEventoPartido.PENALTI,
        minuto=minuto,
        equipo_id=atacante.equipo.id,
        jugador_principal_id=tirador.id,
        descripcion=_descripcion_penalti(
            narrador=narrador, equipo=atacante.equipo.nombre, tirador=tirador.nombre
        ),
    )
    atacante.eventos.append(evento_penalti)

    # Ubicamos el balón en el punto de penalti
    estado_espacial.mover_a(Coordenada(88.5, 50.0))

    return [
        evento_penalti,
        *_resolver_tiro(
            generador=generador,
            narrador=narrador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            ataque=100.0,  # Máxima probabilidad de acierto individual
            defensa=0.0,  # Solo importa el portero
            porteria=80.0,
            parametros=parametros,
            tipo_jugada="penalty",
            es_balon_parado=True,
            forzar_a_puerta=True,
            tirador_fijado=tirador,
        ),
    ]


def _resolver_corner(
    *,
    generador: Random,
    narrador: NarradorPartido,
    minuto: int,
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    estado_espacial: EstadoEspacialPartido,
    parametros: ParametrosSimulacionBaseline,
) -> list[EventoPartido]:
    atacante.corners += 1
    pasador = _elegir_jugador_para_pase(generador, atacante.alineacion.titulares)
    evento_corner = EventoPartido(
        tipo=TipoEventoPartido.CORNER,
        minuto=minuto,
        equipo_id=atacante.equipo.id,
        jugador_principal_id=pasador.id,
        descripcion=_descripcion_corner(
            narrador=narrador, equipo=atacante.equipo.nombre, lanzador=pasador.nombre
        ),
    )
    atacante.eventos.append(evento_corner)

    # El corner ocurre desde una esquina de ataque
    x_corner = 100.0
    y_corner = 0.0 if generador.random() < 0.5 else 100.0
    estado_espacial.mover_a(Coordenada(x_corner, y_corner))

    # El corner suele derivar en un duelo aéreo directo o un centro elaborado
    if generador.random() < 0.20:
        # Intento directo de remate de corner
        rematador = _elegir_tirador(generador, atacante.alineacion.titulares)
        defensor_aire = _elegir_defensor_agresivo(generador, defensor.alineacion.titulares)

        if _resolver_duelo_aereo(generador, rematador, defensor_aire):
            # Remate exitoso de corner
            duelo = EventoPartido(
                tipo=TipoEventoPartido.DUELO_AEREO,
                minuto=minuto,
                equipo_id=atacante.equipo.id,
                jugador_principal_id=rematador.id,
                descripcion=_descripcion_duelo_aereo(
                    narrador=narrador, jugador=rematador.nombre, contexto="tras el saque de esquina"
                ),
            )
            atacante.eventos.append(duelo)

            estado_espacial.mover_a(Coordenada(94.0, 50.0))
            return [
                evento_corner,
                duelo,
                *_resolver_tiro(
                    generador=generador,
                    narrador=narrador,
                    minuto=minuto,
                    atacante=atacante,
                    defensor=defensor,
                    estado_espacial=estado_espacial,
                    ataque=65.0,
                    defensa=45.0,
                    porteria=60.0,
                    parametros=parametros,
                    tipo_jugada="corner",
                    es_balon_parado=True,
                ),
            ]

    return [
        evento_corner,
        *_resolver_centro(
            generador=generador,
            narrador=narrador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            parametros=parametros,
            es_balon_parado=True,
            centrador_fijado=pasador,
        ),
    ]


def _resolver_falta_directa(
    *,
    generador: Random,
    narrador: NarradorPartido,
    minuto: int,
    atacante: _EstadoEquipoMutable,
    defensor: _EstadoEquipoMutable,
    estado_espacial: EstadoEspacialPartido,
    parametros: ParametrosSimulacionBaseline,
) -> list[EventoPartido]:
    tirador = _elegir_tirador(generador, atacante.alineacion.titulares)
    evento_fk = EventoPartido(
        tipo=TipoEventoPartido.TIRO_LIBRE,
        minuto=minuto,
        equipo_id=atacante.equipo.id,
        jugador_principal_id=tirador.id,
        descripcion=_descripcion_tiro_libre(
            narrador=narrador, equipo=atacante.equipo.nombre, tirador=tirador.nombre
        ),
    )
    atacante.eventos.append(evento_fk)

    return [
        evento_fk,
        *_resolver_tiro(
            generador=generador,
            narrador=narrador,
            minuto=minuto,
            atacante=atacante,
            defensor=defensor,
            estado_espacial=estado_espacial,
            ataque=80.0,
            defensa=60.0,
            porteria=70.0,
            parametros=parametros,
            tipo_jugada="set_piece_fk",
            es_balon_parado=True,
        ),
    ]


def _descripcion_recuperacion(
    *, narrador: NarradorPartido, equipo: str, causa: str, zona: ZonaCampo
) -> str:
    causa_txt = causa.lower()
    return narrador.elegir(
        "recuperacion",
        (
            f"Robo de {equipo} en {narrador.zona(zona)} tras {causa_txt}",
            f"{equipo} muerde y recupera por {causa_txt}",
            f"Se corta la jugada: vuelve la pelota para {equipo}",
            f"{equipo} lee la acción y recupera en campo rival",
            f"Pérdida forzada por {causa_txt}; la tiene {equipo}",
            f"{equipo} roba y ordena desde {narrador.zona(zona)}",
            f"Buena presión: {equipo} vuelve a mandar",
            f"Cambio de dueño del balón, ahora para {equipo}",
        ),
    )


def _descripcion_posesion(
    *, narrador: NarradorPartido, equipo: str, jugador: str, zona: ZonaCampo
) -> str:
    return narrador.elegir(
        "posesion",
        (
            f"{equipo} pausa y mueve con {jugador} desde {narrador.zona(zona)}",
            f"{jugador} ordena una circulación larga de {equipo}",
            f"{equipo} administra la pelota y busca huecos",
        ),
    )


def _descripcion_tiro(
    *,
    narrador: NarradorPartido,
    jugador: str,
    equipo: str,
    minuto: int,
    zona: ZonaCampo,
    tipo_jugada: str = "open_play",
) -> str:
    if tipo_jugada == "penalty":
        return narrador.elegir(
            "tiro_penalti",
            (
                f"{jugador} ejecuta el penalti para {equipo}",
                f"Ahí va {jugador} con el disparo desde los once metros",
                f"{jugador} toma carrera y golpea la pena máxima de {equipo}",
            ),
        )

    cierre = "en transición" if minuto > 75 else "en jugada elaborada"
    return narrador.elegir(
        "tiro",
        (
            f"Disparo de {jugador} para {equipo} {cierre}",
            f"{jugador} prueba desde {narrador.zona(zona)}",
            f"Remate de {jugador}; {equipo} acelera",
            f"{jugador} suelta el latigazo para {equipo}",
            f"Finalización de {jugador} tras atacar el espacio",
            f"{equipo} encuentra hueco y {jugador} arma el tiro",
        ),
    )


def _descripcion_gol(
    *,
    narrador: NarradorPartido,
    jugador: str,
    asistidor: str | None,
    tipo_jugada: str,
    minuto: int,
) -> str:
    tramo = "en el tramo final" if minuto >= 75 else "en pleno partido"
    if asistidor:
        return narrador.elegir(
            "gol_asistido",
            (
                f"¡Gol de {jugador}! Asistencia de {asistidor} {tramo}",
                f"Definición de {jugador} tras pase de {asistidor}",
                f"{jugador} firma el gol después de la conexión con {asistidor}",
            ),
        )
    return narrador.elegir(
        "gol",
        (
            f"¡Gol de {jugador}! Acción de {tipo_jugada}",
            f"{jugador} rompe la red y culmina la jugada",
            f"Golazo de {jugador}, definición limpia",
        ),
    )


def _descripcion_parada(*, narrador: NarradorPartido, portero: str, equipo: str) -> str:
    return narrador.elegir(
        "parada",
        (
            f"Paradón de {portero} para sostener a {equipo}",
            f"{portero} bloca el remate y salva a los suyos",
            f"Gran reacción de {portero} bajo palos",
        ),
    )


def _descripcion_centro(*, narrador: NarradorPartido, jugador: str, equipo: str) -> str:
    return narrador.elegir(
        "centro",
        (
            f"{jugador} carga el área con un centro de {equipo}",
            f"Centro tenso de {jugador} buscando rematador",
            f"{equipo} abre a banda y {jugador} pone el envío",
        ),
    )


def _descripcion_duelo_aereo(*, narrador: NarradorPartido, jugador: str, contexto: str) -> str:
    return narrador.elegir(
        "duelo_aereo",
        (
            f"{jugador} gana por arriba {contexto}",
            f"Salto imperial de {jugador} {contexto}",
            f"{jugador} se impone en el juego aéreo {contexto}",
        ),
    )


def _descripcion_autogol(*, narrador: NarradorPartido, jugador: str) -> str:
    return narrador.elegir(
        "autogol",
        (
            f"Gol en propia de {jugador}; jugada desafortunada",
            f"Desvío fatal de {jugador} hacia su portería",
            f"{jugador} marca en propia puerta en un rebote cruel",
        ),
    )


def _descripcion_contraataque(*, narrador: NarradorPartido, equipo: str) -> str:
    return narrador.elegir(
        "contraataque",
        (
            f"{equipo} sale lanzado al contraataque",
            f"Transición vertiginosa de {equipo}",
            f"{equipo} roba y corre con muchos metros por delante",
        ),
    )


def _descripcion_falta(*, narrador: NarradorPartido, infractor: str, zona: ZonaCampo) -> str:
    return narrador.elegir(
        "falta",
        (
            f"Falta de {infractor} en {narrador.zona(zona)}",
            f"{infractor} llega tarde y derriba al rival",
            f"Contacto duro de {infractor}; el árbitro no duda",
            f"{infractor} frena la transición con infracción",
            f"Infracción señalada a {infractor} por juego brusco",
            f"Entrada de {infractor}; se detiene el juego",
        ),
    )


def _descripcion_tarjeta(*, narrador: NarradorPartido, infractor: str, roja: bool) -> str:
    if roja:
        return narrador.elegir(
            "tarjeta_roja",
            (
                f"Roja directa para {infractor}",
                f"{infractor} se va expulsado",
                f"El colegiado muestra roja a {infractor}",
            ),
        )
    return narrador.elegir(
        "tarjeta_amarilla",
        (
            f"Amarilla para {infractor}",
            f"{infractor} entra en la libreta del árbitro",
            f"Cartulina para {infractor} por la acción anterior",
        ),
    )


def _descripcion_penalti(*, narrador: NarradorPartido, equipo: str, tirador: str) -> str:
    return narrador.elegir(
        "penalti",
        (
            f"¡Penalti para {equipo}! Va {tirador}",
            f"Pena máxima para {equipo}; se prepara {tirador}",
            f"El árbitro señala el punto fatídico para {equipo}",
        ),
    )


def _descripcion_corner(*, narrador: NarradorPartido, equipo: str, lanzador: str) -> str:
    return narrador.elegir(
        "corner",
        (
            f"Corner para {equipo}, lo ejecuta {lanzador}",
            f"Saque de esquina de {equipo}; balón al área de {lanzador}",
            f"{equipo} fuerza el córner y {lanzador} se acerca al banderín",
        ),
    )


def _descripcion_tiro_libre(*, narrador: NarradorPartido, equipo: str, tirador: str) -> str:
    return narrador.elegir(
        "tiro_libre",
        (
            f"Falta frontal para {equipo}; preparado {tirador}",
            f"Tiro libre peligroso de {equipo} con {tirador}",
            f"{tirador} acomoda el balón para la falta directa",
        ),
    )


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


def _amplificar_atributo(valor: float, centro: float = 77.0, factor_alto: float = 2.1, factor_bajo: float = 1.1) -> float:
    """Amplifica las diferencias de atributos respecto a un centro.

    Aplica amplificación asimétrica: los atributos por encima del centro
    se amplifican más que los que están por debajo. Centro en 77 para
    equilibrar la media de LaLiga.
    """
    desviacion = valor - centro
    factor = factor_alto if desviacion >= 0 else factor_bajo
    return centro + desviacion * factor


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
            _amplificar_atributo(jugador.atributos.pase_bajo) * 0.30
            + _amplificar_atributo(jugador.atributos.control_balon) * 0.25
            + _amplificar_atributo(jugador.atributos.posesion_cerrada) * 0.20
            + _amplificar_atributo(jugador.atributos.pase_elevado) * 0.10
            + _amplificar_atributo(jugador.atributos.regate) * 0.10
            + _amplificar_atributo(jugador.atributos.resistencia) * 0.05
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
            _amplificar_atributo(jugador.atributos.finalizacion) * 0.28
            + _amplificar_atributo(jugador.atributos.potencia_tiro) * 0.20
            + _amplificar_atributo(jugador.atributos.control_balon) * 0.12
            + _amplificar_atributo(jugador.atributos.regate) * 0.12
            + _amplificar_atributo(jugador.atributos.awareness_ofensivo) * 0.14
            + _amplificar_atributo(jugador.atributos.pase_bajo) * 0.08
            + _amplificar_atributo(jugador.atributos.velocidad) * 0.06
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
            _amplificar_atributo(jugador.atributos.awareness_defensivo) * 0.28
            + _amplificar_atributo(jugador.atributos.tackles) * 0.23
            + _amplificar_atributo(jugador.atributos.engagement_defensivo) * 0.20
            + _amplificar_atributo(jugador.atributos.contacto_fisico) * 0.10
            + _amplificar_atributo(jugador.atributos.velocidad) * 0.09
            + _amplificar_atributo(jugador.atributos.salto) * 0.10
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
