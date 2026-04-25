# Contratos de la API (v1)

Este documento define la estructura de datos (JSON) para la comunicación entre el motor de simulación (Backend) y la interfaz de usuario (Frontend).

## 1. Equipos y Jugadores

### `GET /api/v1/teams`
Lista resumida de todos los equipos disponibles.

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Real Madrid",
    "nombre_corto": "RMA",
    "overall_medio": 86.2,
    "colores": {
      "principal": "#FFFFFF",
      "secundario": "#FEBE10"
    }
  }
]
```

### `GET /api/v1/teams/{id}`
Información detallada de un equipo, incluyendo su plantilla actual.

**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Real Madrid",
  "nombre_corto": "RMA",
  "overall_medio": 86.2,
  "estadio": "Santiago Bernabéu",
  "plantilla": [
    {
      "id": 101,
      "nombre": "Kylian Mbappé",
      "posicion": "DELANTERO",
      "overall": 91,
      "estado_fisico": 100
    }
  ]
}
```

### `GET /api/v1/players/{id}`
Ficha completa de un jugador con todos sus atributos.

**Respuesta:**
```json
{
  "id": 101,
  "nombre": "Kylian Mbappé",
  "posicion": "DELANTERO",
  "atributos": {
    "finalizacion": 94,
    "velocidad": 97,
    "regate": 92,
    "awareness_ofensivo": 91
  },
  "estadisticas_temporada": {
    "partidos": 24,
    "goles": 18,
    "asistencias": 5,
    "xg_acumulado": 14.5
  }
}
```

## 2. Simulación de Partidos

### `POST /api/v1/simulations/match`
Inicia una simulación de partido.

**Cuerpo (Request):**
```json
{
  "local_id": 1,
  "visitante_id": 2,
  "modo": "LIVE", 
  "semilla": 2026
}
```

**Respuesta (Modo INSTANT):**
Devuelve el resultado final y todos los eventos de una vez.

**Respuesta (Modo LIVE):**
Devuelve un `simulation_id` para conectar vía WebSocket.

---

## 3. WebSockets (Streaming de Partido)

### `WS /ws/v1/match/{simulation_id}`
El backend envía eventos en tiempo real según el motor avanza.

**Mensaje de Evento:**
```json
{
  "tipo": "EVENTO",
  "data": {
    "minuto": 12,
    "tipo_evento": "GOL",
    "equipo_id": 1,
    "jugador_id": 101,
    "descripcion": "¡GOL de Kylian Mbappé!",
    "marcador": [1, 0],
    "ubicacion": {"x": 88, "y": 45}
  }
}
```

**Mensaje de Estadísticas (cada N segundos):**
```json
{
  "tipo": "STATS",
  "data": {
    "posesion": [60, 40],
    "tiros": [8, 3],
    "xg": [1.2, 0.4]
  }
}
```
