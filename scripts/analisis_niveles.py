#!/usr/bin/env python3
"""
Script para analizar cómo el nivel de los equipos afecta a las estadísticas
del motor de simulación. Juega múltiples partidos entre diferentes combinaciones
de equipos de LaLiga.
"""

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


def analizar_enfrentamiento(equipo_a, equipo_b, num_partidos=100):
    print(f"\nAnalizando {num_partidos} partidos: {equipo_a.nombre} vs {equipo_b.nombre}")
    print("-" * 60)
    
    victorias_a = 0
    victorias_b = 0
    empates = 0
    
    goles_a = 0
    goles_b = 0
    tiros_a = 0
    tiros_b = 0
    posesion_a = 0.0

    params = ParametrosSimulacionBaseline(
        posesiones_base=145,
        probabilidad_base_gol=3.25,
    )
    
    for i in range(num_partidos):
        ctx = ContextoPartido(
            competicion="Test",
            temporada="24-25",
            equipo_local=equipo_a,
            equipo_visitante=equipo_b,
            semilla=202604 + i
        )
        
        res = simular_partido_baseline(ctx, parametros=params)
        
        gl = res.estadisticas_local.goles
        gv = res.estadisticas_visitante.goles
        
        goles_a += gl
        goles_b += gv
        tiros_a += res.estadisticas_local.tiros
        tiros_b += res.estadisticas_visitante.tiros
        posesion_a += res.estadisticas_local.posesion_pct
        
        if gl > gv:
            victorias_a += 1
        elif gv > gl:
            victorias_b += 1
        else:
            empates += 1

    print(f"Resultados:")
    print(f"  Victorias {equipo_a.nombre[:15]:<15}: {victorias_a:>3} ({victorias_a/num_partidos*100:.1f}%)")
    print(f"  Empates{' '*16}: {empates:>3} ({empates/num_partidos*100:.1f}%)")
    print(f"  Victorias {equipo_b.nombre[:15]:<15}: {victorias_b:>3} ({victorias_b/num_partidos*100:.1f}%)")
    print(f"\nPromedios por partido:")
    print(f"  Goles: {goles_a/num_partidos:.2f} - {goles_b/num_partidos:.2f}")
    print(f"  Tiros: {tiros_a/num_partidos:.1f} - {tiros_b/num_partidos:.1f}")
    print(f"  Posesión: {posesion_a/num_partidos:.1f}% - {100 - posesion_a/num_partidos:.1f}%")


def ejecutar():
    config = cargar_configuracion()
    repo = RepositorioFootballEngine.desde_configuracion(config)
    
    madrid = repo.obtener_equipo_por_nombre("Real Madrid")
    barca = repo.obtener_equipo_por_nombre("FC Barcelona")
    elche = repo.obtener_equipo_por_nombre("Elche CF")
    alaves = repo.obtener_equipo_por_nombre("Alavés")

    print("=" * 60)
    print(" ANÁLISIS DE BALANCE POR NIVELES DE EQUIPO")
    print("=" * 60)

    # 1. Top vs Top
    analizar_enfrentamiento(madrid, barca, 100)
    
    # 2. Bajo vs Bajo
    analizar_enfrentamiento(elche, alaves, 100)
    
    # 3. Top vs Bajo
    analizar_enfrentamiento(madrid, elche, 100)
    
    # 4. Bajo vs Top (para ver factor localía si lo hubiera)
    analizar_enfrentamiento(alaves, barca, 100)


if __name__ == "__main__":
    ejecutar()
