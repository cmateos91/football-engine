from motor_futbol.compartido.configuracion import cargar_configuracion
from motor_futbol.datos.repositorios import RepositorioFootballEngine

def probar_ia_entrenador():
    config = cargar_configuracion()
    repo = RepositorioFootballEngine.desde_configuracion(config)
    
    print("Buscando entrenadores en la base de datos...")
    entrenadores = repo.listar_entrenadores_crudos()
    
    if not entrenadores:
        print("No se encontraron entrenadores.")
        return

    # Probar con el primero
    fila_viva = entrenadores[0]
    entrenador = repo.obtener_entrenador_por_id(fila_viva.id)
    
    print(f"\nEntrenador: {entrenador.nombre}")
    print(f"Estilo Posesion: {entrenador.posesion}")
    print(f"Estilo Contraataque Rapido: {entrenador.contraataque_rapido}")
    print(f"Formacion Favorita: {entrenador.formacion_favorita}")
    
    tactica = entrenador.preparar_tactica()
    
    print("\n--- TACTICA GENERADA POR LA IA DEL ENTRENADOR ---")
    print(f"Nombre del Plan: {tactica.nombre}")
    print(f"Mentalidad: {tactica.mentalidad.name}")
    print(f"Ritmo: {tactica.ritmo}")
    print(f"Altura de Bloque: {tactica.altura_bloque}")
    print(f"Presion: {tactica.presion.name}")
    print(f"Agresividad: {tactica.agresividad}")

if __name__ == "__main__":
    probar_ia_entrenador()
