import sys
import os
sys.path.append(os.path.join(os.getcwd(), "src"))

from motor_futbol.compartido.configuracion import cargar_configuracion
from motor_futbol.datos.conexion_bd import inspeccionar_estado_basico_bd

try:
    config = cargar_configuracion()
    print(f"Cargando config: URL_BD={config.url_bd}")
    estado = inspeccionar_estado_basico_bd(config)
    print("Conexión exitosa!")
    print(f"Base de datos: {estado.nombre_bd}")
    print(f"Tablas encontradas: {estado.tablas}")
    print(f"Total equipos: {estado.total_equipos}")
    print(f"Total jugadores: {estado.total_jugadores}")
except Exception as e:
    print(f"Error conectando a la BD: {e}")
    import traceback
    traceback.print_exc()
