from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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
simulaciones_activas: Dict[str, ContextoPartido] = {}
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
    
    simulaciones_activas[sim_id] = ctx
    eventos_simulacion[sim_id] = []
    
    return {"simulation_id": sim_id, "local": local.nombre, "visitante": visitante.nombre}

@app.websocket("/ws/v1/match/{sim_id}")
async def match_websocket(websocket: WebSocket, sim_id: str):
    await websocket.accept()
    
    # Recuperar contexto real de la simulación
    if sim_id in simulaciones_activas:
        ctx = simulaciones_activas[sim_id]
    else:
        # Fallback para pruebas si no existe el sim_id
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
    
    local_id = ctx.equipo_local.id
    marcador_local = 0
    marcador_visita = 0
    posesiones_local = 0
    total_iteraciones = 0
    ultima_clave_evento: tuple[int | None, str, str] | None = None
    ultimo_minuto_por_tipo: dict[str, int] = {}
    minuto_actual = 0

    DELAYS = {
        "GOL": 4.5,
        "TIRO": 2.2,
        "PARADA": 2.0,
        "TARJETA_ROJA": 3.0,
        "TARJETA_AMARILLA": 2.0,
        "FALTA": 1.5,
        "INICIO": 1.5,
        "DESCANSO": 2.0,
        "FINAL": 3.0,
    }
    DEFAULT_DELAY = 1.2
    TICK_DELAY = 0.1
    try:
        for estado in simulador:
            total_iteraciones += 1
            if estado.posesion_equipo_id == local_id:
                posesiones_local += 1
            
            # Sincronizar el reloj minuto a minuto
            while minuto_actual < estado.minuto:
                minuto_actual += 1
                pct_local = int((posesiones_local / total_iteraciones) * 100) if total_iteraciones > 0 else 50
                await websocket.send_json({
                    "tipo": "TICK",
                    "data": {
                        "minuto": minuto_actual,
                        "marcador": [marcador_local, marcador_visita],
                        "posesion": [pct_local, 100 - pct_local]
                    }
                })
                await asyncio.sleep(TICK_DELAY)

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
                    and estado.minuto - minuto_ultimo_tipo < 3
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
                
                # Velocidad de narración dinámica
                delay = DELAYS.get(estado.evento_actual.tipo.name, DEFAULT_DELAY)
                await asyncio.sleep(delay)
                
    except WebSocketDisconnect:
        print(f"Client disconnected from simulation {sim_id}")
    except Exception as e:
        print(f"Error in simulation stream: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
