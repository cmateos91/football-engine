#!/usr/bin/env python3
"""
Narrador de partidos en tiempo real.
Muestra la simulación minuto a minuto con comentarios dinámicos.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Añadir src al path
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from motor_futbol.compartido.configuracion import cargar_configuracion
    from motor_futbol.datos.repositorios import RepositorioFootballEngine
    from motor_futbol.dominio.contexto_partido import ContextoPartido
    from motor_futbol.dominio.enums import TipoEventoPartido
    from motor_futbol.simulacion.modelos import ParametrosSimulacionBaseline
    from motor_futbol.simulacion.motor_baseline import simular_partido_iterativo
except ImportError as e:
    print(f"Error al importar el motor: {e}")
    sys.exit(1)


# Colores para la consola
class Colores:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    VERDE = "\033[92m"
    ROJO = "\033[91m"
    AMARILLO = "\033[93m"
    AZUL = "\033[94m"
    CYAN = "\033[96m"


def narrar_evento(evento, local_id, nombre_local, nombre_visita):
    if not evento:
        return

    # Omitimos los pases estándar para que la narración se centre en las jugadas clave (highlights)
    if getattr(evento, "tipo", None) == TipoEventoPartido.PASE:
        return

    emoji = "⏱️"
    color = Colores.RESET
    descripcion = evento.descripcion

    if evento.tipo == TipoEventoPartido.GOL:
        emoji = "⚽ "
        color = Colores.VERDE + Colores.BOLD
    elif evento.tipo == TipoEventoPartido.TARJETA_AMARILLA:
        emoji = "🟨 "
        color = Colores.AMARILLO
    elif evento.tipo == TipoEventoPartido.TARJETA_ROJA:
        emoji = "🟥 "
        color = Colores.ROJO
    elif evento.tipo == TipoEventoPartido.TIRO:
        emoji = "🚀 "
    elif evento.tipo == TipoEventoPartido.FALTA:
        emoji = "⚠️ "
    elif evento.tipo == TipoEventoPartido.INICIO:
        emoji = "🏁 "
        color = Colores.CYAN
    elif evento.tipo == TipoEventoPartido.FINAL:
        emoji = "🔚 "
        color = Colores.CYAN
    elif evento.tipo == TipoEventoPartido.CENTRO:
        emoji = "🏹 "
    elif evento.tipo == TipoEventoPartido.DUELO_AEREO:
        emoji = "✈️  "
    elif evento.tipo == TipoEventoPartido.RECUPERACION:
        emoji = "🔄 "
        # Transformar "Perdida de balon (X). Recupera Y" en "Recuperación de balón (X)"
        descripcion = descripcion.replace("Perdida de balon", "Recuperación de balón")
        if ". Recupera" in descripcion:
            descripcion = descripcion.split(". Recupera")[0]

    # Formatear el mensaje
    equipo_str = (
        f"[{nombre_local if evento.equipo_id == local_id else nombre_visita}]"
        if evento.equipo_id
        else ""
    )
    mensaje = (
        f"{Colores.BOLD}{evento.minuto:2}'{Colores.RESET} {emoji} "
        f"{color}{equipo_str} {descripcion}{Colores.RESET}"
    )

    print(mensaje)


def ejecutar_narracion():
    print(f"{Colores.CYAN}{'=' * 70}{Colores.RESET}")
    print(
        f"{Colores.BOLD} 🏟️  BIENVENIDOS A LA NARRACIÓN EN VIVO - FOOTBALL MOTOR CLI{Colores.RESET}"
    )
    print(f"{Colores.CYAN}{'=' * 70}{Colores.RESET}\n")

    config = cargar_configuracion()
    repo = RepositorioFootballEngine.desde_configuracion(config)

    try:
        madrid = repo.obtener_equipo_por_nombre("Real Madrid")
        barca = repo.obtener_equipo_por_nombre("FC Barcelona")
    except Exception:
        print("Cargando equipos genéricos por falta de BD...")
        from tests.unit.fabrica_dominio import crear_equipo

        madrid, barca = crear_equipo(154, "Real Madrid"), crear_equipo(149, "FC Barcelona")

    params = ParametrosSimulacionBaseline()
    params = ParametrosSimulacionBaseline()

    ctx = ContextoPartido(
        competicion="LaLiga",
        temporada="2024-2025",
        equipo_local=madrid,
        equipo_visitante=barca,
        semilla=int(datetime.now().timestamp()),
    )

    print(f"{Colores.BOLD}HOY: {madrid.nombre} vs {barca.nombre}{Colores.RESET}")
    print(f"Competición: {ctx.competicion} | Sede: Estadio Santiago Bernabéu\n")
    print("El árbitro pita el inicio... ¡Arranca el partido!\n")
    print("-" * 70)

    marcador_local = 0
    marcador_visita = 0

    # Bucle de simulación iterativa
    simulador = simular_partido_iterativo(ctx, parametros=params)

    try:
        for estado in simulador:
            if estado.evento_actual:
                # Si hay gol, actualizar marcador local antes de narrar
                if estado.evento_actual.tipo == TipoEventoPartido.GOL:
                    if estado.evento_actual.equipo_id == madrid.id:
                        marcador_local += 1
                    else:
                        marcador_visita += 1

                narrar_evento(estado.evento_actual, madrid.id, madrid.nombre, barca.nombre)

                if estado.evento_actual.tipo == TipoEventoPartido.GOL:
                    print(
                        f"\n{Colores.BOLD}📊 MARCADOR ACTUAL: "
                        f"{madrid.nombre} {marcador_local} - {marcador_visita} "
                        f"{barca.nombre}{Colores.RESET}\n"
                    )

                # Simular tiempo real (ajustar para ir más rápido o lento)
                time.sleep(0.01)
    except StopIteration:
        print("\n" + "-" * 70)
        print(f"{Colores.BOLD}🏁 FINAL DEL PARTIDO{Colores.RESET}")
        print(
            f"{Colores.CYAN}{madrid.nombre} {marcador_local} - "
            f"{marcador_visita} {barca.nombre}{Colores.RESET}"
        )
        print("-" * 70)


if __name__ == "__main__":
    ejecutar_narracion()
