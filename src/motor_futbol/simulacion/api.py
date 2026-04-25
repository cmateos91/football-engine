"""API REST simple para el simulador de fútbol."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse

from motor_futbol.dominio import ContextoPartido, Equipo
from motor_futbol.simulacion.modelos import ParametrosSimulacionBaseline
from motor_futbol.simulacion.motor_baseline import simular_partido_baseline
from motor_futbol.simulacion.observabilidad import (
    analizar_resultado,
    responder_pregunta,
)
from motor_futbol.simulacion.temporada import crear_equipos_default, simular_temporada


class SolicitudInvalidaError(Exception):
    """Error de solicitud inválida."""

    pass


def _parsear_contexto(json_data: dict[str, Any]) -> ContextoPartido:
    """Convierte JSON a ContextoPartido."""
    eq_local = Equipo(
        id=json_data.get("equipo_local_id", 1),
        nombre=json_data.get("equipo_local_nombre", "Local"),
    )
    eq_visita = Equipo(
        id=json_data.get("equipo_visitante_id", 2),
        nombre=json_data.get("equipo_visitante_nombre", "Visitante"),
    )

    return ContextoPartido(
        competicion=json_data.get("competicion", "LaLiga"),
        temporada=json_data.get("temporada", "2025-2026"),
        equipo_local=eq_local,
        equipo_visitante=eq_visita,
        semilla=json_data.get("semilla"),
    )


class ManejadorAPI(BaseHTTPRequestHandler):
    """Manejador de requests HTTP."""

    def do_GET(self) -> None:  # noqa: N802
        """Maneja GET requests."""
        ruta = urlparse(self.path).path

        if ruta == "/salud":
            self._responder({"estado": "ok", "version": "1.0.0"})
        elif ruta == "/equipos":
            equipos = crear_equipos_default()
            self._responder({"equipos": [{"id": e.id, "nombre": e.nombre} for e in equipos]})
        else:
            self._responder_error(404, "No encontrado")

    def do_POST(self) -> None:  # noqa: N802
        """Maneja POST requests."""
        ruta = urlparse(self.path).path
        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo = self.rfile.read(longitud) if longitud > 0 else b"{}"

        try:
            datos = json.loads(cuerpo)
        except json.JSONDecodeError:
            self._responder_error(400, "JSON inválido")
            return

        try:
            if ruta == "/api/partido":
                self._endpoint_simular_partido(datos)
            elif ruta == "/api/temporada":
                self._endpoint_simular_temporada(datos)
            elif ruta == "/api/analizar":
                self._endpoint_analizar(datos)
            elif ruta == "/api/pregunta":
                self._endpoint_pregunta(datos)
            else:
                self._responder_error(404, "No encontrado")
        except Exception as e:
            self._responder_error(500, str(e))

    def _endpoint_simular_partido(self, datos: dict[str, Any]) -> None:
        """Endpoint: /api/partido"""
        contexto = _parsear_contexto(datos)
        parametros = None

        if "parametros" in datos:
            p = datos["parametros"]
            parametros = ParametrosSimulacionBaseline(
                posesiones_base=p.get("posesiones_base", 114),
                variacion_posesiones=p.get("variacion_posesiones", 18),
                probabilidad_base_tiro=p.get("probabilidad_base_tiro", 0.105),
            )

        resultado = simular_partido_baseline(contexto, parametros=parametros)

        self._responder(
            {
                "semilla": resultado.semilla,
                "goles_local": resultado.estado_final.goles_local,
                "goles_visitante": resultado.estado_final.goles_visitante,
                "estadisticas_local": resultado.estadisticas_local.a_dict(),
                "estadisticas_visitante": resultado.estadisticas_visitante.a_dict(),
            }
        )

    def _endpoint_simular_temporada(self, datos: dict[str, Any]) -> None:
        """Endpoint: /api/temporada"""
        semilla = datos.get("semilla", 20250601)
        resultado = simular_temporada(semilla=semilla)

        self._responder(
            {
                "año": resultado.año_inicio,
                "partidos": len(resultado.resultados),
                "clasificacion": [
                    {
                        "posicion": c.posicion,
                        "equipo": c.nombre,
                        "puntos": c.puntos,
                    }
                    for c in resultado.clasificacion[:5]
                ],
            }
        )

    def _endpoint_analizar(self, datos: dict[str, Any]) -> None:
        """Endpoint: /api/analizar"""
        semilla = datos.get("semilla")
        if not semilla:
            raise SolicitudInvalidaError("Se requiere 'semilla'")

        contexto = _parsear_contexto(datos)
        resultado = simular_partido_baseline(contexto)

        log = analizar_resultado(resultado)
        self._responder(log.a_dict())

    def _endpoint_pregunta(self, datos: dict[str, Any]) -> None:
        """Endpoint: /api/pregunta"""
        semilla = datos.get("semilla")
        pregunta = datos.get("pregunta", "")

        if not semilla or not pregunta:
            raise SolicitudInvalidaError("Se requiere 'semilla' y 'pregunta'")

        contexto = _parsear_contexto(datos)
        resultado = simular_partido_baseline(contexto)

        log = analizar_resultado(resultado)
        respuesta = responder_pregunta(pregunta, log)

        self._responder(respuesta)

    def _responder(self, datos: dict[str, Any]) -> None:
        """Responde con JSON."""
        respuesta = json.dumps(datos, ensure_ascii=False)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(respuesta.encode("utf-8"))

    def _responder_error(self, codigo: int, mensaje: str) -> None:
        """Responde con error."""
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        error = json.dumps({"error": mensaje})
        self.wfile.write(error.encode("utf-8"))

    def log_message(self, formato: str, *args: object) -> None:
        """Override to suppress default logging."""
        pass


def iniciar_api(puerto: int = 8080) -> None:
    """Inicia el servidor API."""
    servidor = HTTPServer(("localhost", puerto), ManejadorAPI)
    print(f"API iniciada en http://localhost:{puerto}")
    print("Endpoints:")
    print("  GET /salud")
    print("  GET /equipos")
    print("  POST /api/partido")
    print("  POST /api/temporada")
    print("  POST /api/analizar")
    print("  POST /api/pregunta")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
        servidor.shutdown()


if __name__ == "__main__":
    iniciar_api()
