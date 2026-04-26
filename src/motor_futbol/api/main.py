from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState
from typing import List, Dict
import asyncio
import uuid
import time
from pydantic import BaseModel

# Importar lógica del motor
from motor_futbol.compartido.configuracion import cargar_configuracion
from motor_futbol.datos.repositorios import RepositorioFootballEngine
from motor_futbol.dominio.contexto_partido import ContextoPartido
from motor_futbol.simulacion.motor_baseline import simular_partido_iterativo
from motor_futbol.simulacion.modelos import ParametrosSimulacionBaseline
from motor_futbol.dominio.enums import TipoEventoPartido

app = FastAPI(title="Football Engine API", version="1.0.0")

# Habilitar CORS para el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar repositorio
config = cargar_configuracion()
repo = RepositorioFootballEngine.desde_configuracion(config)

# Gestor de simulaciones en memoria
simulaciones_activas: Dict[str, asyncio.Task] = {}
eventos_simulacion: Dict[str, list] = {}

# Modelos API
class MatchRequest(BaseModel):
    local_id: int
    visitante_id: int
    semilla: int | None = None
class EquipoResumen(BaseModel):
    id: int
    nombre: str
    nombre_corto: str
    overall_medio: float

class JugadorResumen(BaseModel):
    id: int
    nombre: str
    posicion: str
    overall: float

class EquipoDetalle(EquipoResumen):
    plantilla: List[JugadorResumen]

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Football Engine API is running"}

@app.get("/api/v1/teams", response_model=List[EquipoResumen])
def get_teams():
    equipos = repo.listar_equipos()
    return [
        {
            "id": e.id,
            "nombre": e.nombre,
            "nombre_corto": e.nombre_corto,
            "overall_medio": e.overall_medio
        } for e in equipos
    ]

@app.get("/api/v1/teams/{team_id}", response_model=EquipoDetalle)
def get_team(team_id: int):
    equipo = repo.obtener_equipo_por_id(team_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    plantilla = [
        {
            "id": j.id,
            "nombre": j.nombre,
            "posicion": j.posicion.name,
            "overall": j.overall
        } for j in equipo.jugadores
    ]
    
    return {
        "id": equipo.id,
        "nombre": equipo.nombre,
        "nombre_corto": equipo.nombre_corto,
        "overall_medio": equipo.overall_medio,
        "plantilla": plantilla
    }

@app.post("/api/v1/simulations/match")
async def create_match_simulation(req: MatchRequest):
    sim_id = str(uuid.uuid4())
    
    local = repo.obtener_equipo_por_id(req.local_id)
    visitante = repo.obtener_equipo_por_id(req.visitante_id)
    
    if not local or not visitante:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
        
    ctx = ContextoPartido(
        competicion="LaLiga",
        temporada="2024-2025",
        equipo_local=local,
        equipo_visitante=visitante,
        semilla=req.semilla or int(time.time())
    )
    
    eventos_simulacion[sim_id] = []
    
    # La tarea se ejecutará al conectar al websocket o se puede lanzar aquí
    return {"simulation_id": sim_id, "local": local.nombre, "visitante": visitante.nombre}

@app.websocket("/ws/v1/match/{sim_id}")
async def match_websocket(websocket: WebSocket, sim_id: str):
    await websocket.accept()
    
    # Para simplificar, obtenemos los equipos de la "base de datos" de nuevo o los pasamos
    # En un sistema real usaríamos el sim_id para recuperar el contexto persistido
    # Por ahora simulamos un partido genérico o el usuario elige
    # Pero necesitamos el contexto. Vamos a guardarlo.
    
    # TODO: Recuperar contexto real. Por ahora simulamos uno nuevo para probar el stream.
    # Usaremos el Madrid vs Barça si no hay datos.
    madrid = repo.obtener_equipo_por_nombre("Real Madrid")
    barca = repo.obtener_equipo_por_nombre("FC Barcelona")
    
    ctx = ContextoPartido(
        competicion="LaLiga",
        temporada="2024-2025",
        equipo_local=madrid,
        equipo_visitante=barca,
        semilla=int(time.time())
    )
    
    simulador = simular_partido_iterativo(ctx, parametros=ParametrosSimulacionBaseline())
    
    marcador_local = 0
    marcador_visita = 0
    posesiones_local = 0
    total_iteraciones = 0
    ultima_clave_evento: tuple[int | None, str, str] | None = None
    ultimo_minuto_por_tipo: dict[str, int] = {}
    
    try:
        for estado in simulador:
            total_iteraciones += 1
            if estado.posesion_equipo_id == madrid.id:
                posesiones_local += 1
                
            if estado.evento_actual:
                # Omitir pases para el feed en vivo (highlights)
                if estado.evento_actual.tipo == TipoEventoPartido.PASE:
                    continue

                clave = (
                    estado.evento_actual.equipo_id,
                    estado.evento_actual.tipo.name,
                    estado.evento_actual.descripcion or "",
                )
                minuto_ultimo_tipo = ultimo_minuto_por_tipo.get(estado.evento_actual.tipo.name, -99)
                if clave == ultima_clave_evento:
                    continue
                if (
                    estado.evento_actual.tipo == TipoEventoPartido.RECUPERACION
                    and estado.minuto - minuto_ultimo_tipo < 2
                ):
                    continue
                
                if estado.evento_actual.tipo == TipoEventoPartido.GOL:
                    if estado.evento_actual.equipo_id == madrid.id:
                        marcador_local += 1
                    else:
                        marcador_visita += 1
                
                # Calcular posesión aproximada
                pct_local = int((posesiones_local / total_iteraciones) * 100) if total_iteraciones > 0 else 50
                
                # Preparar mensaje
                msg = {
                    "tipo": "EVENTO",
                    "data": {
                        "minuto": estado.minuto,
                        "tipo_evento": estado.evento_actual.tipo.name,
                        "equipo_id": estado.evento_actual.equipo_id,
                        "descripcion": estado.evento_actual.descripcion,
                        "marcador": [marcador_local, marcador_visita],
                        "posesion": [pct_local, 100 - pct_local]
                    }
                }
                
                await websocket.send_json(msg)
                ultima_clave_evento = clave
                ultimo_minuto_por_tipo[estado.evento_actual.tipo.name] = estado.minuto
                
                # Velocidad de narración (ajustable)
                await asyncio.sleep(0.8)
                
    except WebSocketDisconnect:
        print(f"Client disconnected from simulation {sim_id}")
    except Exception as e:
        print(f"Error in simulation stream: {e}")
    finally:
        if websocket.client_state is not WebSocketState.DISCONNECTED:
            await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
