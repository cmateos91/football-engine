import requests
from bs4 import BeautifulSoup
import time
import re
import sys
import os

# Rutas para importar tu configuración y motor de base de datos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from motor_futbol.compartido.configuracion import cargar_configuracion
from motor_futbol.datos.conexion_bd import crear_motor_bd
from sqlalchemy import text

MAPEO_CAMPOS = {
    "Real Name": "nombre_real",
    "Nationality": "nacionalidad",
    "Formation": "formacion",
    "Type": "tipo",
    "Age": "edad",
    "Possession Game": "posesion",
    "Quick Counter": "contraataque_rapido",
    "Long Ball Counter": "contraataque_largo",
    "Out Wide": "por_las_bandas",
    "Long Ball": "balon_largo",
}

def obtener_datos_completos_managers():
    url_liga = "https://www.pesmaster.com/spanish-league/efootball-2022/league/119/"
    
    # Forzamos el idioma inglés para que las palabras clave de búsqueda no fallen
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    print("Obteniendo la lista de equipos...")
    try:
        respuesta_liga = requests.get(url_liga, headers=headers)
        respuesta_liga.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la página: {e}")
        return []

    sopa_liga = BeautifulSoup(respuesta_liga.text, 'html.parser')
    enlaces_equipos = []
    
    for enlace in sopa_liga.find_all('a', href=True):
        href = enlace['href']
        if '/team/' in href and 'efootball' in href:
            url_completa = "https://www.pesmaster.com" + href if href.startswith('/') else href
            if url_completa not in enlaces_equipos:
                enlaces_equipos.append(url_completa)

    print(f"Se encontraron {len(enlaces_equipos)} equipos. Extrayendo datos biográficos y estadísticas...\n")
    print("-" * 100)

    lista_final = []

    for url in enlaces_equipos:
        try:
            respuesta_equipo = requests.get(url, headers=headers)
            sopa_equipo = BeautifulSoup(respuesta_equipo.text, 'html.parser')
            
            titulo = sopa_equipo.find('h1')
            nombre_equipo = titulo.text.strip() if titulo else "Equipo desconocido"
            
            manager_nombre = "No especificado"
            url_manager = None
            
            etiquetas_manager = sopa_equipo.find_all(string=re.compile(r'(Manager|Coach)\s*:', re.IGNORECASE))
            for etiqueta in etiquetas_manager:
                padre = etiqueta.parent
                texto_completo = padre.text.strip()
                if ":" in texto_completo:
                    nombre = texto_completo.split(":", 1)[1].strip()
                    if nombre:
                        manager_nombre = nombre
                        enlace_tag = padre.find('a', href=True)
                        if enlace_tag:
                            url_manager = "https://www.pesmaster.com" + enlace_tag['href'] if enlace_tag['href'].startswith('/') else enlace_tag['href']
                        break

            stats = {}
            if url_manager:
                time.sleep(1) # Pausa de cortesía
                respuesta_manager = requests.get(url_manager, headers=headers)
                sopa_manager = BeautifulSoup(respuesta_manager.text, 'html.parser')
                
                # 1. BUSCAR DATOS BIOGRÁFICOS EN TABLAS
                filas_info = sopa_manager.find_all('tr')
                for fila in filas_info:
                    celdas = fila.find_all(['th', 'td'])
                    if len(celdas) >= 2:
                        clave = celdas[0].text.strip()
                        valor = celdas[1].text.strip()
                        
                        datos_deseados = ["Real Name", "Nationality", "Formation", "Type", "Age"]
                        if clave in datos_deseados:
                            stats[clave] = valor

                # 2. BUSCAR ESTILOS DE JUEGO (Con el sistema de texto)
                texto_pagina = sopa_manager.get_text(separator=' ', strip=True)
                
                estilos_juego = [
                    "Possession Game", 
                    "Quick Counter", 
                    "Long Ball Counter", 
                    "Out Wide", 
                    "Long Ball"
                ]

                for estilo in estilos_juego:
                    patron = rf'{estilo}.{{0,20}}?(\d{{1,2}})'
                    resultado = re.search(patron, texto_pagina, re.IGNORECASE)
                    
                    if resultado:
                        stats[estilo] = int(resultado.group(1))

            # Mapear campos de inglés a español
            datos_db = {}
            datos_db["equipo"] = nombre_equipo
            datos_db["nombre_manager"] = manager_nombre
            
            for clave_original, clave_db in MAPEO_CAMPOS.items():
                if clave_original in stats:
                    datos_db[clave_db] = stats[clave_original]
            
            print(f"Equipo: {nombre_equipo:<30} | Mánager: {manager_nombre}")
            
            lista_final.append(datos_db)
            
            time.sleep(1.5)

        except Exception as e:
            print(f"Error procesando {url}: {e}")

    print("-" * 100)
    print("\n¡Extracción de datos completada!")
    return lista_final


def insertar_entrenadores_bd(entrenadores: list[dict]):
    if not entrenadores:
        print("No hay entrenadores para insertar.")
        return

    config = cargar_configuracion()
    motor = crear_motor_bd(config)

    # Insertamos en la tabla 'Entrenador' (singular)
    consulta = text("""
        INSERT INTO Entrenador (
            equipo, nombre_manager, nombre_real, nacionalidad, 
            formacion, tipo, edad, posesion, contraataque_rapido, 
            contraataque_largo, por_las_bandas, balon_largo
        ) VALUES (
            :equipo, :nombre_manager, :nombre_real, :nacionalidad,
            :formacion, :tipo, :edad, :posesion, :contraataque_rapido,
            :contraataque_largo, :por_las_bandas, :balon_largo
        )
    """)

    insertados = 0
    # motor.begin() gestiona la transacción automáticamente y hace commit si no hay errores
    with motor.begin() as conn:
        for ent in entrenadores:
            # Usamos .get() para asegurarnos de enviar 'None' a la BD si el dato no existe
            # Esto previene errores de "missing key" en SQLAlchemy
            parametros = {
                "equipo": ent.get("equipo"),
                "nombre_manager": ent.get("nombre_manager"),
                "nombre_real": ent.get("nombre_real"),
                "nacionalidad": ent.get("nacionalidad"),
                "formacion": ent.get("formacion"),
                "tipo": ent.get("tipo"),
                "edad": ent.get("edad"),
                "posesion": ent.get("posesion"),
                "contraataque_rapido": ent.get("contraataque_rapido"),
                "contraataque_largo": ent.get("contraataque_largo"),
                "por_las_bandas": ent.get("por_las_bandas"),
                "balon_largo": ent.get("balon_largo"),
            }
            
            try:
                conn.execute(consulta, parametros)
                insertados += 1
            except Exception as e:
                print(f"Error insertando a {ent.get('nombre_manager', '?')}: {e}")

    print(f"Se insertaron exitosamente {insertados} entrenadores en la base de datos.")


if __name__ == "__main__":
    datos_obtenidos = obtener_datos_completos_managers()
    # Solo intentamos insertar si la lista no está vacía
    if datos_obtenidos:
        insertar_entrenadores_bd(datos_obtenidos)