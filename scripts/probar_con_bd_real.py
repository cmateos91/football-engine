#!/usr/bin/env python3
"""
Script para validar el motor contra datos reales de la base de datos MySQL.
Carga equipos reales (Real Madrid vs Barcelona) y simula un partido de alta fidelidad.
"""

import json
import sys
from pathlib import Path

# Añadir src al path
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from motor_futbol.compartido.configuracion import cargar_configuracion
    from motor_futbol.datos.repositorios import RepositorioFootballEngine
    from motor_futbol.dominio.contexto_partido import ContextoPartido
    from motor_futbol.simulacion.modelos import ParametrosSimulacionBaseline
    from motor_futbol.simulacion.motor_baseline import simular_partido_baseline
except ImportError as e:
    print(f"Error al importar el motor: {e}")
    sys.exit(1)


def ejecutar_prueba_real():
    print("=" * 60)
    print(" PROBANDO MOTOR CON DATOS REALES (MySQL)")
    print("=" * 60)

    config = cargar_configuracion()
    if not config.base_de_datos_configurada:
        print("❌ Error: La base de datos no está configurada en el archivo .env")
        sys.exit(1)

    repo = RepositorioFootballEngine.desde_configuracion(config)

    print("Cargando plantillas desde la base de datos...")
    try:
        madrid = repo.obtener_equipo_por_nombre("Real Madrid")
        barca = repo.obtener_equipo_por_nombre("FC Barcelona")
    except Exception as e:
        print(f"❌ Error al cargar equipos: {e}")
        sys.exit(1)

    print(f"✅ Cargado: {madrid.nombre} ({len(madrid.jugadores)} jugadores)")
    print(f"✅ Cargado: {barca.nombre} ({len(barca.jugadores)} jugadores)")

    # Cargar los últimos parámetros calibrados si existen
    params = ParametrosSimulacionBaseline()
    calib_path = Path("docs/calibration/ultimo_resultado.json")
    if calib_path.exists():
        print(f"\nUsando parámetros calibrados desde {calib_path}")
        with open(calib_path) as f:
            data = json.load(f)["parametros"]
            params = ParametrosSimulacionBaseline(
                posesiones_base=data.get("posesiones_base", 114),
                variacion_posesiones=data.get("posesiones_variacion", 18),
                probabilidad_base_tiro=data.get("probabilidad_base_tiro", 0.105),
                probabilidad_base_falta=data.get("probabilidad_base_falta", 0.10),
                probabilidad_base_corner=data.get("probabilidad_base_corner", 0.20),
                probabilidad_base_tiro_puerta=data.get("probabilidad_base_tiro_puerta", 0.32),
                probabilidad_base_gol=data.get("probabilidad_base_gol", 0.28),
            )

    ctx = ContextoPartido(
        competicion="LaLiga",
        temporada="2024-2025",
        equipo_local=madrid,
        equipo_visitante=barca,
        semilla=20260424,
    )

    print("\nSimulando 'El Clásico'...")
    resultado = simular_partido_baseline(ctx, parametros=params)

    print("-" * 60)
    print(
        f" RESULTADO FINAL: {resultado.contexto.equipo_local.nombre} "
        f"{resultado.estadisticas_local.goles} - {resultado.estadisticas_visitante.goles} "
        f"{resultado.contexto.equipo_visitante.nombre}"
    )
    print("-" * 60)

    print("\nEstadísticas del Partido:")
    el = resultado.estadisticas_local
    ev = resultado.estadisticas_visitante

    print(f"  - Tiros: {el.tiros} (RM) vs {ev.tiros} (FCB)")
    print(f"  - Tiros a Puerta: {el.tiros_a_puerta} vs {ev.tiros_a_puerta}")
    print(f"  - Posesión: {el.posesion_pct:.1f}% vs {ev.posesion_pct:.1f}%")
    print(f"  - Faltas: {el.faltas} vs {ev.faltas}")
    print(f"  - Córners: {el.corners} vs {ev.corners}")

    print("\nEventos Destacados:")
    # Mostrar los últimos 5 eventos significativos (Goles, etc)
    goles = [e for e in resultado.estado_final.eventos if "Gol" in e.tipo.value]
    for gol in goles:
        print(f"  ⚽ Minuto {gol.minuto}: {gol.descripcion}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    ejecutar_prueba_real()
