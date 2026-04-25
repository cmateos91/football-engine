import sys
from pathlib import Path
sys.path.append(str(Path("src").resolve()))
from motor_futbol.compartido.configuracion import cargar_configuracion
from motor_futbol.datos.repositorios import RepositorioFootballEngine
from motor_futbol.simulacion.motor_baseline import simular_partido_baseline
from motor_futbol.simulacion.modelos import ParametrosSimulacionBaseline
from motor_futbol.dominio import ContextoPartido
from motor_futbol.simulacion.selector_alineacion import construir_alineacion_baseline

config = cargar_configuracion()
repo = RepositorioFootballEngine.desde_configuracion(config)
madrid = repo.obtener_equipo_por_nombre("Real Madrid")
barca = repo.obtener_equipo_por_nombre("FC Barcelona")

ctx = ContextoPartido(
    competicion="LaLiga", temporada="2024", 
    equipo_local=madrid, equipo_visitante=barca,
    semilla=123
)
res = simular_partido_baseline(ctx)
print("Tiros local:", res.estadisticas_local.tiros)
print("Total eventos:", len(res.estado_final.eventos))
