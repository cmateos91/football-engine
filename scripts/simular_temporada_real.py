#!/usr/bin/env python3
"""
Script para simular una temporada completa usando los equipos reales de la BD
y validar los resultados globales contra los targets de calibración.
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from motor_futbol.compartido.configuracion import cargar_configuracion
    from motor_futbol.datos.repositorios import RepositorioFootballEngine
    from motor_futbol.simulacion.modelos import ParametrosSimulacionBaseline
    from motor_futbol.simulacion.temporada import simular_temporada
    from motor_futbol.calibracion.targets import SEASON_TARGETS
except ImportError as e:
    print(f"Error al importar el motor: {e}")
    sys.exit(1)


def ejecutar_temporada_real():
    print("=" * 70)
    print(" SIMULANDO TEMPORADA COMPLETA (DATOS MYSQL)")
    print("=" * 70)

    config = cargar_configuracion()
    if not config.base_de_datos_configurada:
        print("❌ Error: La base de datos no está configurada.")
        sys.exit(1)

    repo = RepositorioFootballEngine.desde_configuracion(config)

    print("Cargando 20 equipos desde la base de datos...")
    equipos = list(repo.listar_equipos())
    if len(equipos) != 20:
        print(f"❌ Error: Se encontraron {len(equipos)} equipos, LaLiga requiere 20.")
        sys.exit(1)
        
    params = ParametrosSimulacionBaseline(
        posesiones_base=160,
        probabilidad_base_gol=4.95,
    )

    print("\nSimulando las 38 jornadas...")
    resultado = simular_temporada(equipos=equipos, parametros=params, semilla=2026)
    
    print("\n" + "=" * 70)
    print(" CLASIFICACIÓN FINAL")
    print("=" * 70)
    print(f"{'Pos':>3} | {'Equipo':<20} | {'Pts':>3} | {'PJ':>2} | {'G':>2} | {'E':>2} | {'P':>2} | {'GF':>3} | {'GC':>3} | {'DG':>3}")
    print("-" * 70)
    for c in resultado.clasificacion:
        print(f"{c.posicion:>3} | {c.nombre[:20]:<20} | {c.puntos:>3} | {c.partidos:>2} | {c.victoria:>2} | {c.empate:>2} | {c.derrota:>2} | {c.gf:>3} | {c.gc:>3} | {c.dg:>3}")

    print("\n" + "=" * 70)
    print(" ESTADÍSTICAS INDIVIDUALES TOP 5")
    print("=" * 70)
    
    jugadores = list(resultado.estadisticas_jugadores.values())
    
    # Goleadores
    print("\n⚽ MÁXIMOS GOLEADORES (Pichichi):")
    goleadores = sorted(jugadores, key=lambda j: (-j.goles, -j.partidos))[:5]
    for i, j in enumerate(goleadores):
        print(f"{i+1}. {j.nombre[:25]:<25} - {j.goles} goles (xG: {j.xg_acumulado:.2f})")
        
    # Asistentes
    print("\n🎯 MÁXIMOS ASISTENTES:")
    asistentes = sorted(jugadores, key=lambda j: (-j.assistencias, -j.partidos))[:5]
    for i, j in enumerate(asistentes):
        print(f"{i+1}. {j.nombre[:25]:<25} - {j.assistencias} asistencias")

    print("\n" + "=" * 70)
    print(" VALIDACIÓN CONTRA TARGETS DE CALIBRACIÓN")
    print("=" * 70)
    
    puntos_campeon = resultado.clasificacion[0].puntos
    pts_18 = resultado.clasificacion[17].puntos
    goles_totales = sum(c.gf for c in resultado.clasificacion)
    equipos_60 = sum(1 for c in resultado.clasificacion if c.puntos > 60)
    
    targets = [
        ("Puntos del Campeón", puntos_campeon, SEASON_TARGETS["champion_points"]),
        ("Puntos del 18º (Descenso)", pts_18, SEASON_TARGETS["relegation_pts_18th"]),
        ("Goles Totales Liga", goles_totales, SEASON_TARGETS["total_league_goals"])
    ]
    
    todos_cumplen = True
    for nombre, valor, target in targets:
        obj = target['value']
        tol = target['tolerance']
        delta = abs(valor - obj)
        cumple = delta <= tol
        estado = "✅ PASS" if cumple else "❌ FAIL"
        if not cumple: todos_cumplen = False
        print(f"{estado} | {nombre:<25} | Resultado: {valor:>5} | Objetivo: {obj} ± {tol}")
        
    target_60 = SEASON_TARGETS["teams_over_60_pts"]
    r_min, r_max = target_60['range']
    cumple_60 = r_min <= equipos_60 <= r_max
    if not cumple_60: todos_cumplen = False
    estado_60 = "✅ PASS" if cumple_60 else "❌ FAIL"
    print(f"{estado_60} | Equipos >60 Puntos      | Resultado: {equipos_60:>5} | Objetivo: [{r_min}, {r_max}]")

    print("\nResultado Final de Calibración de Temporada: ", "✅ ÉXITO" if todos_cumplen else "❌ HAY DESVIACIONES")
    
if __name__ == "__main__":
    ejecutar_temporada_real()
