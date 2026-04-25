"""Logging estructurado y análisis de simulaciones."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EventoLog:
    """Registro de un evento con contexto completo."""

    simulacion_id: str
    tipo_evento: str
    minuto: int
    equipo_id: int | None
    jugador_id: int | None
    probabilidad: float | None
    resultado: str | None
    factores: dict[str, float] = field(default_factory=dict)
    zona: str | None = None
    descripcion: str | None = None

    def a_dict(self) -> dict[str, Any]:
        return {
            "simulacion_id": self.simulacion_id,
            "tipo": self.tipo_evento,
            "minuto": self.minuto,
            "equipo": self.equipo_id,
            "jugador": self.jugador_id,
            "probabilidad": self.probabilidad,
            "resultado": self.resultado,
            "factores": self.factores,
            "zona": self.zona,
            "descripcion": self.descripcion,
        }


@dataclass
class PartidoLog:
    """Log completo de un partido."""

    simulacion_id: str
    semilla: int
    equipo_local_id: int
    equipo_visitante_id: int
    eventos: list[EventoLog] = field(default_factory=list)
    resumen: dict[str, Any] = field(default_factory=dict)

    def agregar_evento(self, evento: EventoLog) -> None:
        self.eventos.append(evento)

    def a_dict(self) -> dict[str, Any]:
        return {
            "simulacion_id": self.simulacion_id,
            "semilla": self.semilla,
            "equipo_local": self.equipo_local_id,
            "equipo_visitante": self.equipo_visitante_id,
            "eventos": [e.a_dict() for e in self.eventos],
            "resumen": self.resumen,
        }


class AnalizadorPartido:
    """Analiza un partido simulado para responder preguntas."""

    def __init__(self, log: PartidoLog):
        self.log = log
        self._calcular_resumen()

    def _calcular_resumen(self) -> None:
        eventos = self.log.eventos
        self.log.resumen = {
            "total_eventos": len(eventos),
            "goles_local": sum(
                1
                for e in eventos
                if e.tipo_evento == "GOL" and e.equipo_id == self.log.equipo_local_id
            ),
            "goles_visitante": sum(
                1
                for e in eventos
                if e.tipo_evento == "GOL" and e.equipo_id == self.log.equipo_visitante_id
            ),
            "tiros": sum(1 for e in eventos if e.tipo_evento == "TIRO"),
            "tiros_puerta": sum(1 for e in eventos if e.resultado == "PUERTA"),
            "goles": sum(1 for e in eventos if e.tipo_evento == "GOL"),
            "faltas": sum(1 for e in eventos if e.tipo_evento == "FALTA"),
            "corners": sum(1 for e in eventos if e.tipo_evento == "CORNER"),
            "posesiones": sum(1 for e in eventos if e.tipo_evento == "PASE"),
        }

    def por_que_poco_peligro(self, equipo_id: int) -> dict[str, Any]:
        """Responde: ¿por qué este equipo generó tan poco peligro?"""
        eventos_eq = [e for e in self.log.eventos if e.equipo_id == equipo_id]

        if not eventos_eq:
            return {"respuesta": "Sin posesiones registradas"}

        tipos: dict[str, int] = {}
        for e in eventos_eq:
            tipos[e.tipo_evento] = tipos.get(e.tipo_evento, 0) + 1

        if tipos.get("TIRO", 0) < 3:
            return {
                "respuesta": "Pocas llegadas al área",
                "detalle": f"Solo {tipos.get('TIRO', 0)} tiros en el partido",
                "causa_probable": "Baja progresión espacial o deficiencias en ataque",
            }

        prob_promedio = sum(e.probabilidad for e in eventos_eq if e.probabilidad is not None) / max(
            1, sum(1 for e in eventos_eq if e.probabilidad is not None)
        )

        if prob_promedio < 0.15:
            return {
                "respuesta": "Baja calidad de oportunidad",
                "detalle": f"Probabilidad promedio de gol: {prob_promedio:.2%}",
                "causa_probable": "Tiros desde posicionesdefavorables",
            }

        return {
            "respuesta": "Rendimiento dentro de lo esperado",
            "detalle": f"Tiros: {tipos.get('TIRO', 0)}, Prob avg: {prob_promedio:.2%}",
        }

    def que_factores_mas_importaron(self) -> dict[str, Any]:
        """Responde: ¿qué atributo tuvo mayor impacto?"""
        factores_totales: dict[str, float] = {}

        for evento in self.log.eventos:
            if evento.tipo_evento == "GOL" and evento.factores:
                for k, v in evento.factores.items():
                    factores_totales[k] = factores_totales.get(k, 0.0) + v

        if not factores_totales:
            return {"respuesta": "Sin goles paraanalizar"}

        sorted_factores = sorted(factores_totales.items(), key=lambda x: x[1], reverse=True)

        return {
            " factores con mayor peso en goles": {k: round(v, 3) for k, v in sorted_factores[:3]},
        }

    def que_habria_cambiado(self, atributo: str, cambio: int) -> dict[str, Any]:
        """Responde: ¿qué habría cambiado si X?"""
        eventos_gol = [e for e in self.log.eventos if e.tipo_evento == "GOL"]

        if not eventos_gol:
            return {"respuesta": "Sin goles en el partido paracomparar"}

        simulaciones = []
        for evento in eventos_gol:
            if evento.factores and atributo in evento.factores:
                actual = evento.factores[atributo]
                nuevo = min(1.0, actual + cambio / 100.0)
                simulaciones.append(
                    {
                        "evento": evento.tipo_evento,
                        "antes": actual,
                        "despues": nuevo,
                        "diferencia": nuevo - actual,
                    }
                )

        if not simulaciones:
            return {"respuesta": f"Atributo '{atributo}' no encontrado en los eventos"}

        return {
            "atributo": atributo,
            "cambio": cambio,
            "simulacion": simulaciones,
        }


def analizar_resultado(resultado: Any) -> PartidoLog:
    """Convierte un ResultadoSimulacionPartido en PartidoLog."""
    from uuid import uuid4

    eventos_logs: list[EventoLog] = []

    for evento in resultado.estado_final.eventos:
        factor_ejemplo: dict[str, float] = {}

        eventos_logs.append(
            EventoLog(
                simulacion_id=str(uuid4())[:8],
                tipo_evento=evento.tipo.value,
                minuto=evento.minuto,
                equipo_id=evento.equipo_id,
                jugador_id=evento.jugador_principal_id,
                probabilidad=None,
                resultado=None,
                factores=factor_ejemplo,
                descripcion=evento.descripcion,
            )
        )

    log = PartidoLog(
        simulacion_id=str(uuid4())[:8],
        semilla=resultado.semilla,
        equipo_local_id=resultado.contexto.equipo_local.id,
        equipo_visitante_id=resultado.contexto.equipo_visitante.id,
        eventos=eventos_logs,
    )

    return log


def responder_pregunta(pregunta: str, log: PartidoLog) -> dict[str, Any]:
    """Responde preguntas causales sobre un partido."""
    analizador = AnalizadorPartido(log)

    pregunta = pregunta.lower()

    if "por qué" in pregunta and "peligro" in pregunta:
        equipo_id = log.equipo_local_id
        if "visitante" in pregunta:
            equipo_id = log.equipo_visitante_id
        return analizador.por_que_poco_peligro(equipo_id)

    if "qué factores" in pregunta or "factor" in pregunta:
        return analizador.que_factores_mas_importaron()

    if "qué habría" in pregunta or "hubiera cambiado" in pregunta:
        return {"respuesta": "Simulation hipotética no implementada en esta versión"}

    return {"respuesta": "Pregunta no reconocida"}
