"""Modulo para la logica de simulacion."""

from motor_futbol.simulacion.calibracion import (
    MetasLaLiga,
    RegistroCalibracion,
    ResultadoCalibracion,
    calibrar_parametros,
    validar_parametros,
)
from motor_futbol.simulacion.modelos import (
    EstadisticasEquipoPartido,
    EstadoIteracion,
    ParametrosSimulacionBaseline,
    ResultadoSimulacionPartido,
)
from motor_futbol.simulacion.motor_baseline import (
    simular_partido_baseline,
    simular_partido_iterativo,
)
from motor_futbol.simulacion.observabilidad import (
    AnalizadorPartido,
    EventoLog,
    PartidoLog,
    analizar_resultado,
    responder_pregunta,
)
from motor_futbol.simulacion.selector_alineacion import (
    SeleccionAlineacionError,
    construir_alineacion_baseline,
)
from motor_futbol.simulacion.temporada import (
    crear_equipos_default,
    generar_calendario_laliga,
    simular_temporada,
)
from motor_futbol.simulacion.xg import ResultadoXG, calcular_xg

__all__ = [
    "AnalizadorPartido",
    "EstadisticasEquipoPartido",
    "EstadoIteracion",
    "EventoLog",
    "MetasLaLiga",
    "ParametrosSimulacionBaseline",
    "PartidoLog",
    "RegistroCalibracion",
    "ResultadoCalibracion",
    "ResultadoSimulacionPartido",
    "ResultadoXG",
    "SeleccionAlineacionError",
    "analizar_resultado",
    "calcular_xg",
    "calibrar_parametros",
    "construir_alineacion_baseline",
    "crear_equipos_default",
    "generar_calendario_laliga",
    "responder_pregunta",
    "simular_partido_baseline",
    "simular_partido_iterativo",
    "simular_temporada",
    "validar_parametros",
]
