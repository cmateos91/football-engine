#!/usr/bin/env python3
"""
Script de calibración automática del motor de fútbol.
Busca los parámetros óptimos para maximizar el realismo estadístico vs LaLiga.
"""

import json
import sys
from pathlib import Path

# Añadir src y tests al path
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent))

try:
    from tests.unit.fabrica_dominio import crear_equipo

    from motor_futbol.calibracion.benchmarks import RealismScorecard
    from motor_futbol.dominio import ContextoPartido
    from motor_futbol.simulacion.calibracion import calibrar_parametros
    from motor_futbol.simulacion.motor_baseline import simular_partido_baseline
except ImportError as e:
    print(f"Error al importar el motor o tests: {e}")
    print("Asegúrate de ejecutar este script desde la raíz del proyecto.")
    sys.exit(1)


def ejecutar_calibracion():
    print("=" * 60)
    print(" INICIANDO CALIBRACIÓN AUTOMÁTICA (Optimización Scipy)")
    print("=" * 60)
    print("Objetivo: Minimizar la distancia vs distribuciones reales de LaLiga.")
    print("Configuración: 40 iteraciones de optimización Nelder-Mead.")
    print("-" * 60)

    # 1. Ejecutar la calibración con equipos válidos
    def crear_equipos_calibracion():
        return [crear_equipo(i + 1, f"Equipo {i + 1}") for i in range(20)]

    # Patch temporal de crear_equipos_default para que use nuestra fabrica
    import motor_futbol.simulacion.calibracion as cal_mod

    cal_mod.crear_equipos_default = crear_equipos_calibracion
    import motor_futbol.simulacion.temporada as temp_mod

    temp_mod.crear_equipos_default = crear_equipos_calibracion

    resultado = calibrar_parametros(n_partidos=100, max_iteraciones=80)

    print(f"\n✅ Calibración finalizada en {resultado.iteraciones} iteraciones.")
    print(f"📈 Score de error final: {resultado.score:.4f} (menor es mejor)")

    print("\n[Parámetros Óptimos Encontrados]")
    params = resultado.parametros
    print(f"  - Posesiones Base: {params.posesiones_base}")
    print(f"  - Variación Posesiones: {params.variacion_posesiones}")
    print(f"  - Prob. Base Tiro: {params.probabilidad_base_tiro:.4f}")
    print(f"  - Prob. Base Falta: {params.probabilidad_base_falta:.4f}")
    print(f"  - Prob. Base Córner: {params.probabilidad_base_corner:.4f}")

    # 2. Validación final con una muestra más grande
    print("\n" + "-" * 60)
    print(" VALIDACIÓN DE REALISMO (Scorecard Final)")
    print("-" * 60)
    print("Simulando 200 partidos de prueba con los nuevos parámetros...")

    equipos = crear_equipos_calibracion()
    resultados_test = []
    for i in range(200):
        ctx = ContextoPartido(
            competicion="LaLiga",
            temporada="2025-2026",
            equipo_local=equipos[i % 20],
            equipo_visitante=equipos[(i + 1) % 20],
            semilla=999 + i,
        )
        res = simular_partido_baseline(ctx, parametros=params)
        resultados_test.append(res)

    scorecard = RealismScorecard(resultados_test)
    informe = scorecard.evaluar()

    print(f"\n⭐ AFINIDAD GLOBAL CON LALIGA: {informe['score_global']:.1f}%")
    estado_texto = "✅ PASADO" if informe["pasado"] else "❌ FALLADO (Revisar métricas CRITICAL)"
    print(f"📋 Estado: {estado_texto}")

    print("\nDesglose de métricas:")
    for metrica, detalle in informe["detalles"].items():
        estado = "✅" if detalle["cumple"] else "❌"
        print(
            f"  {estado} {metrica:25} | Valor: {detalle['valor']:.2f} "
            f"(Objetivo: {detalle['objetivo']:.2f}) | Delta: {detalle['delta']:.2f}"
        )

    # 3. Guardar resultados
    output_path = Path("docs/calibration/ultimo_resultado.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(resultado.a_dict(), f, indent=2)

    print(f"\n💾 Configuración guardada en: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    ejecutar_calibracion()
