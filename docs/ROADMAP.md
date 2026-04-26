# Roadmap de Construcción — Football Simulation Engine
### Club President: El Manager de Managers

---

## Objetivo del proyecto

Construir un motor de simulación de partidos de fútbol con foco en realismo estadístico, empezando desde cero, creciendo en pasos muy pequeños y validando cada capa contra datos reales de LaLiga.

El objetivo no es "hacer un simulador que funcione", sino un sistema que:

- use datos reales de equipos y jugadores desde MySQL
- permita explicar por qué ocurre cada evento
- pueda calibrarse con evidencia
- tenga tests automáticos en todos los niveles
- se acerque de forma medible a distribuciones reales de LaLiga

---

## Principios no negociables

**1. Greenfield real.**
El proyecto se construye desde cero en este repositorio. No se hereda código de intentos anteriores.

**2. Complejidad incremental.**
No activaremos "todos los stats" en la primera simulación. Sí se ingieren y normalizan desde el inicio, pero se incorporan al motor por capas para poder medir el impacto real de cada grupo de atributos.

**3. Todo cambio exige validación.**
Ninguna mejora entra solo porque "suena realista". Debe pasar tests y mejorar o mantener las métricas de calibración.

**4. El realismo se mide, no se declara.**
Cada milestone tendrá métricas objetivo frente a datos reales de LaLiga.

**5. Arquitectura explicable.**
El motor debe poder responder preguntas como: *"¿por qué este equipo generó tan poco peligro?"* o *"¿qué stats empujaron este gol?"*.

**6. Determinismo controlado.**
Toda simulación debe poder ejecutarse con semilla fija para reproducir resultados y depurar.

---

## Enfoque técnico

### Stack

| Herramienta | Uso |
|---|---|
| Python | Núcleo de simulación |
| `pytest` | Test runner |
| `hypothesis` | Property-based testing |
| `mypy` | Tipado estático |
| `ruff` | Lint y formateo |
| `SQLAlchemy` / `mysql-connector` | Acceso a MySQL |
| `pandas`, `numpy`, `scipy` | Análisis y calibración |
| `.env` + settings tipados | Configuración |

Para un motor que necesita simulación masiva, calibración estadística y comparación con datasets reales, Python da mejor base que una stack orientada a frontend. Si más adelante se quiere API o dashboard, se añade encima del core.

---

## Estrategia general

El proyecto se divide en **16 grandes fases**. Las fases 0–12 construyen y calibran el motor. Las fases 13–16 convierten el motor en un juego de gestión.

Cada fase debe dejar un sistema usable, testeado y medible antes de pasar a la siguiente.

---

# PARTE I: EL MOTOR DE SIMULACIÓN
## Fases 0 – 12

---

## Fase 0. Fundación del proyecto

### Objetivo

Preparar un repositorio serio, reproducible y listo para construir el motor sin deuda accidental.

### Entregables

- Estructura inicial del repositorio
- Entorno virtual y dependencias base
- Configuración de `pytest`, `hypothesis`, `ruff`, `mypy`
- Carpetas `docs/`, `src/`, `tests/`, `scripts/`, `data_samples/`
- Archivo de configuración para conexión a MySQL
- Primer pipeline local de test/lint/type-check

### Estructura sugerida

```
football-motor/
  docs/
  src/
    domain/
    simulation/
    data/
    calibration/
    shared/
  tests/
    unit/
    integration/
    statistical/
    regression/
  scripts/
  data_samples/
  pyproject.toml
  .env.example
  README.md
```

### Tests obligatorios de salida

- Los tests arrancan en limpio
- La configuración carga correctamente
- Existe una seed reproducible
- Un comando único ejecuta lint, type-check y tests

### Criterio de cierre

No seguimos hasta tener una base de trabajo reproducible en una máquina nueva sin pasos ambiguos.

---

## Fase 1. Modelo de dominio puro

### Objetivo

Definir el lenguaje del sistema antes de simular nada.

### Entregables

**Entidades de dominio:** `Team`, `Player`, `MatchContext`, `Lineup`, `Tactic`, `PlayerAttributes`, `MatchState`, `Event`

**Tipos y enums:** posiciones, roles, pie dominante, estado físico, estados del partido

**Otros:** normalización de atributos, reglas de validación del dominio

### Decisión clave

Separar desde el principio: datos crudos de base de datos / atributos normalizados para simulación / variables derivadas calculadas por el motor.

### Variables derivadas futuras

- Capacidad de progresión y finalización
- Resistencia y presión defensiva efectiva
- Amenaza aérea y control bajo presión

### Tests obligatorios de salida

- Creación válida e inválida de entidades
- Validación de rangos
- Serialización y deserialización
- Invariantes de dominio

### Criterio de cierre

El dominio está definido sin depender de decisiones del motor minuto a minuto.

---

## Fase 2. Capa de datos y mapeo desde MySQL

### Objetivo

Conectar la base de datos real y convertir sus stats a un modelo utilizable por el simulador.

### Entregables

- Cliente de lectura a MySQL
- Repositorios de datos para equipos, jugadores y alineaciones
- Mapeador de columnas reales a atributos del dominio
- Catálogo de stats disponibles con sistema de versionado
- Fixtures pequeñas para tests sin depender siempre de la BD real

### Trabajo específico

1. Inventario completo de columnas disponibles en la BD
2. Clasificación por familias: físicos, técnicos, defensivos, mentales, portero, contexto biográfico, contexto táctico
3. Detección de nulos, outliers, columnas redundantes y escalas inconsistentes
4. Definición de normalización

> **Regla importante:** Aquí se cargan todos los stats disponibles, pero no se usan todos en el motor todavía. Primero se catalogan, limpian, documentan y normalizan.

### Tests obligatorios de salida

- Conexión real a la BD
- Mapeo correcto de un equipo completo
- Detección de datos inválidos
- Snapshots de importación y tests de regresión sobre el catálogo

### Criterio de cierre

Se pueden cargar dos equipos de LaLiga completos y obtener objetos de dominio limpios y consistentes.

---

## Fase 3. Baseline del simulador

### Objetivo

Construir la versión mínima del partido que sirva como banco de calibración.

### Qué simula esta versión

Marcador final, goles, tiros, tiros a puerta, posesión aproximada, faltas, córners, tarjetas básicas, fatiga simple.

### Qué NO intenta todavía

Trayectorias espaciales complejas, animación mental por jugador, microdecisiones segundo a segundo, uso exhaustivo de atributos.

### Arquitectura

Modelo híbrido por posesiones/eventos. Unidad base: posesión → subfase ofensiva → resolución del desenlace.

### Entregables

- Generador de partidos con semilla
- Pipeline de posesión
- Resolución básica de ataque/defensa
- Asignación de eventos a jugadores
- Salida estructurada del partido

### Tests obligatorios de salida

- Reproducibilidad por seed
- Invariantes del partido (no negativos, consistencia eventos/resultado)
- Tests de Monte Carlo básicos

### Criterio de cierre

Se pueden simular miles de partidos y obtener distribuciones estables.

---

## Fase 4. Marco formal de realismo y calibración

### Objetivo

Crear el sistema que decidirá si el motor se parece o no a LaLiga.

### Métricas a comparar con datos reales

**Por partido:** goles, goles local vs visitante, empates, tiros, tiros a puerta, posesión, faltas, tarjetas, córners, porterías a cero, resultados exactos, distribución de goles por tramo.

**Por equipo:** puntos esperados, goles a favor y en contra, victoria local, estabilidad de ranking.

**Por jugador:** cuota de tiros, goles y asistencias, impacto de fatiga, impacto posicional.

### Metodología

Cada métrica tendrá: fuente real / ventana temporal / valor objetivo / tolerancia aceptable / severidad si falla.

### Tests obligatorios de salida

- Suite `tests/statistical/`
- Informe automático de calibración
- Semilla y muestra fijas para regresión
- Comparación entre versiones del motor

### Criterio de cierre

El proyecto deja de depender de intuición y pasa a depender de evidencia.

---

## Fase 5. Activación progresiva de atributos reales

### Objetivo

Empezar a usar los stats reales de manera incremental y medible.

### Orden de activación

1. Finalización, pase, regate, tackle, reflejos, velocidad, resistencia
2. Posicionamiento, anticipación, agresividad, control, juego aéreo
3. Visión, toma de decisiones, presión, compostura, pie dominante
4. Rasgos contextuales o de menor señal

### Regla de activación

Cada nueva familia de stats entra con: hipótesis explícita / fórmula concreta / tests unitarios / test de sensibilidad / validación estadística antes y después.

> **Criterio correcto:** *"Añadir `decision_making` debe reducir tiros malos y mejorar la relación SOT/tiros en perfiles élite."*
>
> **Criterio incorrecto:** *"Añadir más stats para que el motor sea más realista."*

### Criterio de cierre

Se puede justificar matemáticamente por qué cada grupo de stats sigue dentro del modelo.

---

## Fase 6. Táctica, alineaciones y contexto de partido

### Objetivo

Pasar de un motor centrado en capacidad individual a uno donde importen la estructura y el contexto.

### Variables a introducir

Formación, roles por jugador, estilo de presión, altura de bloque, amplitud, ritmo, agresividad, ventaja de local, estado de marcador, gestión de fatiga, sustituciones.

### Entregables

- Representación táctica formal
- Modificadores contextuales
- Cambios de plan durante el partido
- Sustituciones con reglas y triggers

### Tests obligatorios de salida

- Una táctica ofensiva aumenta volumen ofensivo y exposición defensiva
- Una táctica defensiva hace lo contrario
- El marcador influye en el comportamiento
- Los cambios afectan a fatiga y output

### Criterio de cierre

Los equipos ya no son solo la suma plana de sus jugadores.

---

## Fase 7. Motor de eventos avanzado

### Objetivo

Refinar la simulación del partido sin caer en una física imposible de calibrar.

### Eventos a desarrollar

Secuencias de posesión más ricas, pérdidas en salida, transiciones, contraataques, centros, balón parado, penaltis, duelos aéreos, rebotes, bloqueos de disparo, asistencias, errores no forzados.

### Decisión de arquitectura

Seguir con un motor de eventos probabilístico explicable, enriquecido por estado contextual, antes de plantear simulación espacial de alta resolución. Si el modelo event-driven ya no captura la realidad con precisión suficiente, habrá evidencia para incorporar la capa espacial. No antes.

### Criterio de cierre

El partido produce narrativas plausibles además de números plausibles.

---

## Fase 8. Capa espacial del partido

### Objetivo

Introducir representación espacial para modelar eventos que dependen de la posición del balón y los jugadores en el campo.

### Por qué ahora

El motor funciona bien a nivel agregado, pero no puede capturar que un pase desde campo propio vs cerca del área tiene dificultad diferente, o que los contraataques son más efectivos cuando se capturan en campo rival.

### Arquitectura

```
Campo dividido en 3 zonas longitudinales:
  ZONA_DEFENSA:    x ∈ [0, 33]
  ZONA_MEDIOCAMPO: x ∈ [34, 66]
  ZONA_ATAQUE:     x ∈ [67, 100]

Eje Y: 0–100 (banda a banda)
Coordenadas del balón: (x, y)
```

```python
@dataclass
class EstadoEspacialPartido:
    posicion_balon: tuple[float, float] = (50.0, 50.0)
    posesion: int | None = None
    zona_actual: str = "MEDIOCAMPO"
    ultimo_pase: tuple[float, float] | None = None
    tiempo_en_zona: dict[str, float] = field(default_factory=dict)
    contracapturas: int = 0
```

### Implementación por etapas

**8.1** — Fundación espacial: estructuras de coordenadas y transiciones básicas de zona.

**8.2** — Pases con ubicación: probabilidad de progresión según calidad de pase.

**8.3** — Tiros contextuales: solo desde ZONA_ATAQUE, bonificador por proximidad.

**8.4** — Contraespacios: contracaptura más probable en campo contrario, métricas de territorio.

### Criterio de cierre

El motor produce métricas de posición además de globales, y los eventos tienen ubicación coherente con las reglas del fútbol.

---

## Fase 9. Modelo de Expected Goals (xG)

### Objetivo

Reemplazar la probabilidad de gol plana por un modelo de xG basado en atributos contextuales y espaciales.

### Variables del modelo

Distancia y ángulo al gol, zona de disparo, tipo de acción previa, pie de contacto, atributos del rematador (finalización, compostura, potencia), presión defensiva, cabeza vs pie, fatiga acumulada.

### Métricas de calibración

| Métrica | Target LaLiga |
|---|---|
| xG medio por tiro | 0.10 – 0.12 |
| Goles de cabeza | 20 – 25% |
| Correlación xG acumulado vs goles reales | Alta |

### Tests obligatorios de salida

- Un tiro desde el punto de penalti de un delantero élite tiene `xG ≥ 0.70`
- Un remate de cabeza desde 20 metros tiene `xG ≤ 0.05`
- `xG ∈ [0, 1]` para cualquier combinación de inputs válidos (property-based)
- La suma de goles simulados converge al xG total con suficientes muestras (LGN)

### Criterio de cierre

El motor produce xG por disparo explicable y calibrado, con relación entre xG acumulado y goles reales dentro de la varianza esperada en LaLiga.

---

## Fase 10. Simulación de temporada y competición

### Objetivo

Escalar el motor desde partidos individuales hasta temporadas completas reproducibles, con tabla de clasificación, estadísticas individuales acumuladas, rotaciones y efectos de calendario.

### Qué simula esta fase

Calendario completo de LaLiga (38 jornadas), rotaciones de alineación por fatiga y lesiones, degradación de atributos por fatiga de temporada, estadísticas acumuladas por jugador y equipo, tabla de clasificación completa.

### Métricas de calibración

| Métrica | Target LaLiga |
|---|---|
| Puntos del campeón | ~85 – 90 |
| Puntos del descenso | ~30 – 35 |
| Partidos de local por equipo | 19 exactos |

### Tests obligatorios de salida

- El campeón de 1000 temporadas no es siempre el mismo, pero el favorito gana con frecuencia estadísticamente superior
- Los puntos del campeón caen dentro del rango histórico de LaLiga
- La misma seed produce la misma tabla final
- La suma de puntos de todos los equipos es consistente con los partidos jugados

### Criterio de cierre

Se pueden simular 1000 temporadas completas y comparar la distribución de puntos y posiciones contra datos históricos dentro de tolerancias definidas.

---

## Fase 11. Observabilidad, explicabilidad y API

### Objetivo

Hacer que el motor sea consultable desde fuera, que cada simulación pueda auditarse evento por evento, y que el sistema pueda responder preguntas causales de forma programática.

### Capacidades a desarrollar

**Trazabilidad de eventos:** log estructurado por evento con inputs, probabilidades y resultado; visualización textual minuto a minuto; árbol de decisión de cada gol.

**Motor de preguntas causales:**
- *"¿Por qué este equipo generó tan poco peligro?"*
- *"¿Qué atributo tuvo mayor impacto en el resultado?"*
- *"¿Qué habría cambiado con 10 puntos más de finalización?"*

**API REST:**
- Endpoint de simulación de partido individual
- Endpoint de simulación de temporada
- Endpoint de calibración bajo demanda
- Endpoint de scorecard de realismo

**Alertas de regresión:** alerta automática si una nueva versión empeora el scorecard global en más de un umbral configurado.

### Criterio de cierre

Un usuario externo puede simular un partido, leer el log estructurado, hacer preguntas causales y recibir respuestas explicables sin necesidad de acceder al código del motor.

---

## Fase 12. Calibración automatizada y optimización de parámetros

### Objetivo

Sustituir el ajuste manual de parámetros por un sistema de calibración automática que minimiza la distancia entre distribuciones simuladas y reales de LaLiga.

### Función objetivo

Distancia total entre distribuciones simuladas y reales, ponderada por relevancia: KL divergence o Wasserstein distance en goles, tiros, posesión; error cuadrático medio en métricas agregadas por equipo; penalización por invariantes rotas.

### Métodos de optimización

1. Búsqueda aleatoria con constraints (primera iteración)
2. Optimización bayesiana (segunda iteración, más eficiente)
3. Algoritmos evolutivos si el espacio es no diferenciable
4. Grid search limitado para parámetros discretos

### Validación cruzada temporal

- Calibrar sobre temporadas pasadas (2019–2022)
- Validar sobre temporadas recientes no vistas (2023–2024)
- Detectar sobreajuste temporal

### Criterio de cierre

El motor puede recalibrarse automáticamente ante nuevos datos de LaLiga sin intervención manual, produciendo una versión nueva que mejora o mantiene el scorecard global y supera la validación cruzada temporal.

---

## Artefactos de datos de calibración

### Origen

Durante la planificación del proyecto se construyó un conjunto de datos de referencia a partir de estadísticas reales de LaLiga (temporada 2024-25 principal + histórico 2019-25). Vive en dos archivos complementarios:

```
docs/calibration/
  LaLiga_Stats_Calibracion_2024-25.xlsx   ← fuente de datos visual, exploración humana
  CALIBRATION_TARGETS.md                  ← fuente autoritativa para el código y los tests
```

### Contenido de `CALIBRATION_TARGETS.md`

| Sección | Descripción | Primera fase que la consume |
|---|---|---|
| `MATCH_TARGETS` (goles, resultados) | Métricas básicas por partido | Fase 3 |
| `MATCH_TARGETS` (tiros, SOT, xG) | Volumen ofensivo | Fase 4 |
| `MATCH_TARGETS` (posesión, eventos) | Contexto de partido | Fase 5 |
| `GOAL_TYPE_TARGETS` | Fracción de goles por tipo | Fase 7 |
| `GOAL_TIMING_TARGETS` | Distribución por tramo temporal | Fase 7 |
| `XG_ZONE_TARGETS`, `XG_MODIFIERS` | Modelo xG por zona | Fase 9 |
| `SEASON_TARGETS` | Puntos, goles de temporada | Fase 10 |
| `HARD_INVARIANTS` | 13 invariantes duros | Fase 3 en adelante |
| `HISTORICAL_SEASONS` | 6 temporadas 2019-25 | Fase 12 |

### Reglas de mantenimiento

1. El `.md` es la fuente autoritativa para el código. Si hay discrepancia, el `.md` manda.
2. Los targets no se tocan para que pasen los tests. Si el motor no pasa un target CRÍTICO, se abre una tarea de calibración documentada. No se relaja la tolerancia.
3. Actualización anual al finalizar cada temporada de LaLiga.
4. Los parámetros internos del motor viven en `src/simulation/config/` y son los que cambia la Fase 12, nunca los targets.
5. Los targets históricos nunca se eliminan, solo se marcan como `deprecated`.

---

## Sistema de testing del proyecto

| Tipo | Propósito |
|---|---|
| **Unitarios** | Fórmulas, normalizaciones, validaciones, mapeadores |
| **Integración** | BD real, carga de equipos, pipeline de simulación completo |
| **Estadísticos** | Miles de partidos, distribuciones dentro de umbrales definidos |
| **Regresión** | Seeds congeladas, outputs esperados por versión |
| **Property-based** | Invariantes para cualquier combinación de inputs |
| **Sensibilidad** | Subir/bajar un atributo desplaza el resultado en la dirección esperada |
| **Rendimiento** | Partidos por segundo, duración de una temporada completa |

---

## Sistema de validación de realismo

Cada versión del motor tendrá un **scorecard de realismo** con seis componentes: realismo global de partido / realismo por equipo / realismo por jugador / estabilidad en simulación masiva / explicabilidad / coste computacional.

**Regla de promoción de versión:** una versión no avanza si rompe invariantes, empeora claramente el scorecard sin razón aceptada, introduce parámetros inexplicables, o aumenta la complejidad sin mejorar métricas.

---

## Estado actual del proyecto (Abril 2026) — Calibración completada

### Fases completadas al 100%

- **Fase 0–6:** Cimentación, dominio, datos, motor baseline, calibración, atributos y tácticas
- **Fase 7:** Eventos avanzados. Contraataques, transiciones y gestión de fatiga
- **Fase 8:** Capa espacial. Sistema de coordenadas (x,y) y zonas del campo
- **Fase 9:** Modelo xG multiplicativo calibrado que distingue calidad y contexto
- **Fase 10:** Simulación de temporada. 38 jornadas validadas
- **Fase 11:** Observabilidad. Narración minuto a minuto y logs estructurados
- **Fase 12:** Calibración. Tests estadísticos en verde en todas las métricas críticas

### Estado final de calibración (N = 1.000 partidos)

| Métrica | Resultado | Target | Estado |
|---|---|---|---|
| Goles / partido | 2.67 | 2.62 ± 0.20 | ✅ PASS |
| Tiros / partido | 22.4 | 23.0 ± 2.0 | ✅ PASS |
| Puntos campeón | 83–92 | 88 ± 6 | ✅ PASS |
| Puntos descenso | 35–40 | 40 ± 5 | ✅ PASS |
| % Victoria local | 44% | 44% ± 4% | ✅ PASS |
| Dominancia top | 79% wins | Real Madrid vs Elche | ✅ REALISTA |

---

# PARTE II: EL JUEGO DE GESTIÓN
## Fases 13 – 16: Club President

---

## Introducción al bloque de gestión

Tras completar la base estadística del motor, el proyecto evoluciona hacia un **juego de gestión** donde el usuario asume el rol de Presidente de club. El foco se desplaza de *"cómo se juega el partido"* a *"quién gestiona el club"*.

### Principios del juego de gestión

Estos principios se suman a los principios técnicos ya establecidos:

**1. El presidente no toca el césped.**
El usuario nunca da instrucciones directas a jugadores. Todo pasa a través de los empleados que contrata y gestiona.

**2. Cada decisión tiene coste y consecuencia.**
Contratar, despedir, invertir o recortar cambia el estado del club de forma medible y persistente.

**3. La información es imperfecta por diseño.**
El presidente no sabe todo. Lo que sabe depende de la calidad de su staff.

**4. Los empleados tienen agencia.**
El entrenador toma decisiones. El director deportivo propone. Los ojeadores reportan. El presidente filtra, aprueba o veta.

**5. El éxito es multidimensional.**
Ganar la liga es un tipo de éxito. Sanear las finanzas es otro. Cumplir los objetivos del consejo es otro. Pueden entrar en conflicto.

---

## Fase 13. Infraestructura de Empleados e IA del Entrenador

### Objetivo

Dar vida a los entrenadores —actualmente entidades inertes en la base de datos— y construir el sistema de delegación técnica que es el corazón del juego. Sin esta fase, el resto del juego no tiene sentido: no hay nadie a quien delegar.

### Por qué esta fase es la primera del juego

El motor ya simula partidos, pero lo hace con tácticas fijas o elegidas directamente. Para que el juego funcione como juego de gestión, necesitamos que **alguien dentro del sistema** tome las decisiones tácticas de forma autónoma, con una personalidad coherente y con impacto real en el resultado. Ese alguien es el entrenador.

---

### 13.1 Entidad `Entrenador` con atributos funcionales

El entrenador pasa de ser un nombre en la base de datos a una entidad con peso real en el motor. Sus atributos se dividen en dos familias:

**Atributos de personalidad** (escala 1–100, afectan al vestuario y a la gestión de presión):

| Atributo | Descripción | Efecto en juego |
|---|---|---|
| `motivacion` | Capacidad para elevar el rendimiento del grupo | Bonus de rendimiento en partidos clave |
| `disciplina` | Rigor táctico y exigencia de cumplimiento de roles | Reduce desviación de jugadores del plan. Penaliza creatividad individual |
| `adaptabilidad` | Capacidad de cambiar el plan cuando el partido no sale bien | Velocidad y calidad de los cambios tácticos en tiempo real |
| `gestion_vestuario` | Habilidad para mantener a suplentes comprometidos | Reduce penalización de rendimiento en jugadores con poca participación |
| `manejo_presion` | Estabilidad emocional bajo resultados malos | Evita espirales negativas. Modera la caída de moral del equipo |

**Atributos técnicos** (escala 1–100, afectan directamente a la simulación):

| Atributo | Descripción | Efecto en motor |
|---|---|---|
| `conocimiento_tactico` | Profundidad de su catálogo de esquemas | Determina qué formaciones puede ejecutar bien |
| `lectura_del_juego` | Velocidad con que detecta problemas durante el partido | Reduce el tiempo de reacción ante un marcador adverso |
| `desarrollo_juvenil` | Calidad con que mejora a jugadores jóvenes | Modifica la tasa de progresión de jugadores sub-23 |
| `gestion_plantilla` | Habilidad para distribuir minutos y mantener al grupo fresco | Reduce fatiga acumulada. Mejora rendimiento en la segunda vuelta |
| `experiencia` | Años en élite. Valor estático por historial real | Umbral mínimo de calidad. Sin experiencia, el entrenador comete más errores aleatorios |

**Fuentes de datos:**
- Entrenadores con historial real de LaLiga: derivar atributos de resultados, estilo táctico y estadísticas de plantilla.
- Entrenadores ficticios: generador con distribuciones realistas por perfil (motivador, táctico, desarrollador).

---

### 13.2 Motor de Decisión Táctica del Entrenador

Un servicio que recibe `(Equipo, Entrenador, ContextoTemporada, EstadoPartido)` y devuelve una `Tactica` válida. Este es el cerebro autónomo que el presidente no controla directamente.

```python
@dataclass
class ContextoDecisionTactica:
    equipo: Equipo
    entrenador: Entrenador
    rival: Equipo
    jornada: int
    posicion_en_tabla: int
    objetivo_temporada: ObjetivoClub
    jugadores_disponibles: List[Jugador]
    jugadores_sancionados: List[Jugador]
    jugadores_lesionados: List[Jugador]
    estado_moral_vestuario: float        # 0.0–1.0
    racha_resultados: List[Resultado]    # últimos 5 partidos
    importancia_partido: ImportanciaPartido  # NORMAL, CLAVE, DECISIVO
```

**El entrenador toma decisiones en tres momentos:**

**1. Decisión pre-partido** — El algoritmo pondera las fortalezas de la plantilla contra el rival, el estilo preferido del entrenador, la importancia del partido y el estado de los jugadores.

> *Ejemplo de regla concreta: si `importancia_partido == DECISIVO` y `entrenador.motivacion > 75` y `equipo.racha_negativa >= 3`, el entrenador abandona su estilo base y elige la táctica más segura de su catálogo.*

**2. Decisión en tiempo real** — El entrenador reacciona al `EstadoPartido`, filtrado por su `lectura_del_juego` y `adaptabilidad`. Si va perdiendo con más de 30 minutos: evalúa cambio ofensivo. Si va ganando por 1 con menos de 15: evalúa repliegue. Un valor bajo de `lectura_del_juego` añade retraso de N minutos antes de que el entrenador "note" el problema.

**3. Ruido y error humano** — Un entrenador con `experiencia < 40` tiene probabilidad `p` de no hacer el cambio correcto. Un entrenador con `manejo_presion < 30` en racha negativa puede elegir una táctica subóptima (pánico táctico).

---

### 13.3 Modificadores del Entrenador sobre el Motor

| Atributo | Variable del motor afectada | Fórmula |
|---|---|---|
| `motivacion` | Rendimiento en partidos `DECISIVO` | `rendimiento_base * (1 + 0.001 * motivacion)` |
| `disciplina` | Desviación de rol táctico por jugador | `desviacion_rol * (1 - 0.006 * disciplina)` |
| `gestion_plantilla` | Fatiga acumulada semana a semana | `fatiga_acumulada * (1 - 0.004 * gestion_plantilla)` |
| `desarrollo_juvenil` | Tasa de mejora anual sub-23 | `mejora_anual * (1 + 0.005 * desarrollo_juvenil)` |
| `conocimiento_tactico` | Ejecución real de la táctica elegida | `eficiencia_tactica * (0.5 + 0.005 * conocimiento_tactico)` |

> **Regla crítica:** un entrenador con todos los atributos a 100 no debe producir resultados físicamente imposibles. Los modificadores se validan con tests de sensibilidad.

---

### 13.4 Sistema de Relación Entrenador–Presidente

La relación entre el presidente y el entrenador es dinámica y tiene consecuencias reales.

```python
@dataclass
class RelacionEntrenadorPresidente:
    confianza: float           # 0.0–1.0
    tension: float             # 0.0–1.0
    contrato_meses_restantes: int
    renovacion_pendiente: bool
    clausula_rescision: int
    ultima_conversacion: Semana
```

| Acción del presidente | Efecto |
|---|---|
| Renovar con mejora salarial tras buena temporada | `confianza += 0.15`, `tension -= 0.10` |
| Fichar un jugador que el entrenador no quería | `tension += 0.10`, `confianza -= 0.05` |
| Defender públicamente al entrenador tras racha mala | `confianza += 0.20` |
| Filtrar críticas al entrenador a los medios | `tension += 0.30`, riesgo de dimisión |
| No ampliar plantilla cuando el entrenador lo solicitó | `tension += 0.15` |

Cuando `tension > 0.8` el entrenador solicita una reunión. Si `tension > 0.95` puede dimitir o exigir ser despedido.

---

### Tests obligatorios de la Fase 13

- Creación válida e inválida de `Entrenador` con todos los atributos
- El `MotorDecisionTactica` devuelve siempre una `Tactica` válida para cualquier combinación de inputs
- Tests de sensibilidad: subir `conocimiento_tactico` de 40 a 90 mejora la ejecución táctica de forma medible
- Tests de sensibilidad: alta `motivacion` produce mejor rendimiento en partidos `DECISIVO`
- Test de regresión: misma seed + mismo entrenador + mismo equipo = misma táctica
- Tests de relación: las acciones del presidente modifican las variables dentro de los rangos esperados
- Tests de límite: `tension = 1.0` dispara el evento de crisis de entrenador

### Criterio de cierre

El motor puede simular una temporada completa donde el entrenador toma todas las decisiones tácticas de forma autónoma, con comportamiento diferencial medible entre perfiles distintos, y la relación con el presidente evoluciona de forma coherente con las acciones del usuario.

---

## Fase 14. El Despacho del Presidente (UI y Economía del Club)

### Objetivo

Crear el entorno de trabajo del usuario y el sistema financiero que convierte el juego en un reto de gestión real. Si la Fase 13 crea el *"quién manda en el campo"*, esta fase crea el *"quién manda en el club"*. El presidente no puede ganar si no tiene dinero para pagar las nóminas ni el apoyo del consejo.

### Por qué esta fase es la segunda

La economía es la restricción que da sentido a todas las decisiones del presidente. Sin ella, fichar al mejor entrenador del mundo no tiene coste. El juego degeneraría en una fantasía sin tensión. La economía no es un añadido; es el eje central del diseño.

---

### 14.1 Modelo Económico del Club

El club tiene un estado financiero que se actualiza cada semana simulada:

```python
@dataclass
class EstadoFinanciero:
    # Activo
    caja_disponible: int
    presupuesto_fichajes_restante: int
    valor_mercado_plantilla: int
    # Pasivo
    deuda_total: int
    coste_salarial_mensual: int
    amortizaciones_pendientes: List[Amortizacion]
    # Flujo
    ingresos_proyectados_temporada: int
    gastos_proyectados_temporada: int
    resultado_ejercicio_anterior: int
```

**Fuentes de ingresos:**

| Fuente | Cómo se calcula | Lever del presidente |
|---|---|---|
| Taquilla | `aforo × ocupacion × precio × partidos_casa` | Precio de entradas, inversión en matchday |
| Derechos televisivos | Fijo por liga + variable por posición final | No controlable. Depende del rendimiento |
| Patrocinios | Base + bonus por visibilidad (posición, europeos) | Negociación de contratos |
| Premios de competición | Fijo por ronda superada | Decisión de rotar en competiciones menores |
| Venta de jugadores | Precio venta – valor amortizado | Decisión de vender, cuándo y a quién |
| Academia | Valor de mercado de jugadores de cantera vendidos | Inversión en instalaciones |

**Fuentes de gastos:**

| Gasto | Descripción | Lever del presidente |
|---|---|---|
| Salarios plantilla | Fijo mensual, sube con cada fichaje | Política salarial, masa salarial máxima |
| Salarios staff técnico | Entrenador, ayudantes, preparadores | Calidad del cuerpo técnico |
| Salarios staff de gestión | Director deportivo, ojeadores, médicos | Red de scouting y departamento médico |
| Amortizaciones de fichajes | Coste fichaje / años contrato | Estructura de contratos |
| Instalaciones | Mantenimiento estadio y ciudad deportiva | Inversión en infraestructura |
| Finiquitos | Coste de despidos | Política de despidos |

Si el `balance_proyectado` es negativo en más del umbral definido, el consejo activa una alerta. Sin medidas correctoras en N semanas: venta forzada de jugadores o restricción de presupuesto.

---

### 14.2 Sistema de Contratación y Despido de Staff

**Contratación:** el presidente elige desde un pool de candidatos. Los candidatos tienen atributos, salario pedido, disponibilidad y fit táctico con el entrenador actual. El proceso es una negociación simplificada: el presidente expresa interés → el candidato presenta condiciones → acepta, contraoferta o rechaza. Si rechaza una oferta razonable repetidamente, el candidato puede retirarse del mercado.

**Despido:** no es gratuito ni sin consecuencias.

| Variable | Descripción |
|---|---|
| `coste_finiquito` | Calculado según contrato. Los contratos largos con cláusulas altas son más caros de romper |
| `impacto_reputacion` | Reduce la reputación del presidente entre candidatos del mismo perfil durante N semanas |
| `reaccion_vestuario` | Si el entrenador tenía alta relación con los jugadores, el vestuario reacciona negativamente |
| `mercado_entrenadores` | Despedir buenos entrenadores frecuentemente hace que candidatos de nivel rechacen el club |

---

### 14.3 Sistema de Objetivos del Consejo

El consejo define los objetivos al inicio de cada temporada. El presidente no fija sus propios criterios de éxito: los recibe.

```python
@dataclass
class ObjetivoTemporada:
    objetivo_deportivo: ObjetivoDeportivo    # SALVACION, TOP_MITAD, EUROPEOS, TITULO
    objetivo_financiero: ObjetivoFinanciero  # REDUCIR_DEUDA, EQUILIBRIO, INVERSION_NETA
    objetivo_desarrollo: ObjetivoDesarrollo  # NINGUNO, PROMOVER_CANTERA, REDUCIR_EDAD_MEDIA
    plazo: int                               # Semanas hasta evaluación
    consecuencia_fallo: ConsecuenciaFallo    # ADVERTENCIA, PRESION_VENTA, DESPIDO
```

| Objetivo | Condición de cumplimiento | Penalización por fallo |
|---|---|---|
| `SALVACION` | Terminar fuera de las 3 últimas posiciones | Advertencia. Segunda temporada con margen reducido |
| `TOP_MITAD_TABLA` | Terminar entre los 10 primeros | Presión pública. Posible cambio de presidente |
| `CLASIFICACION_EUROPEA` | Posición de acceso a competición europea | Reducción de presupuesto de fichajes siguiente temporada |
| `GANAR_LIGA` | Campeón de liga | Riesgo de despido si se falla por más de X puntos |

> **Tensión entre objetivos (intencionada):** el consejo puede pedir `REDUCIR_DEUDA` y `CLASIFICACION_EUROPEA` a la vez, siendo incompatibles con el presupuesto disponible. Estas tensiones son parte central del diseño del juego.

---

### 14.4 Sistema de Reputación del Presidente

La reputación no es un número cosmético. Afecta a lo que el presidente puede hacer.

```python
@dataclass
class ReputacionPresidente:
    reputacion_global: float
    reputacion_entre_entrenadores: float
    reputacion_entre_jugadores: float
    reputacion_financiera: float      # Puntualidad de pagos, solidez del club
    reputacion_mediatica: float       # Presencia y coherencia en comunicados
```

| Con reputación alta | Con reputación baja |
|---|---|
| Acceso a candidatos de mayor nivel | Candidatos de nivel rechazan el club |
| Mejores condiciones en negociaciones | Las negociaciones parten desde posición débil |
| Jugadores aceptan renovar con descuento | Los jugadores exigen primas para renovar |
| El consejo da más margen antes de intervenir | El consejo interviene más rápido ante malos resultados |

---

### Tests obligatorios de la Fase 14

- El balance financiero se actualiza correctamente semana a semana con todas las fuentes activas
- Se puede simular una temporada completa sin quiebra con un presupuesto ajustado
- El coste de finiquito se calcula correctamente para distintos tipos de contrato
- Un objetivo `SALVACION` fallado activa la consecuencia correcta
- La reputación sube y baja coherentemente con las acciones del presidente
- Tests de límite: con `caja_disponible = 0` no se puede contratar personal nuevo
- Tests de coherencia: los gastos proyectados nunca pueden ser negativos

### Criterio de cierre

El presidente puede gestionar una temporada completa, tomando decisiones de staff, respetando el presupuesto, y recibiendo una evaluación de objetivos al final con consecuencias reales y coherentes.

---

## Fase 15. Dirección Deportiva y Sistema de Scouting

### Objetivo

Crear la capa de construcción de plantilla. El presidente no ficha directamente: supervisa, aprueba o veta. La calidad de las decisiones de fichaje depende de la red de scouting y del director deportivo contratado.

### Por qué esta fase es la tercera

Sin esta fase, la plantilla es estática y el juego pierde profundidad a partir de la primera temporada. La delegación en el director deportivo es uno de los pilares del concepto de "presidente que gestiona desde arriba".

---

### 15.1 Entidad `DirectorDeportivo`

| Atributo | Descripción | Efecto |
|---|---|---|
| `red_de_contactos` | Amplitud de su red en el mercado | Determina cuántas opciones de fichaje aparecen en cada ventana |
| `capacidad_negociacion` | Habilidad para cerrar acuerdos favorables | Reduce precio de compra y mejora condiciones de venta |
| `vision_tactica` | Compatibilidad con el estilo del entrenador | Un mal fit propone jugadores que no encajan con el sistema |
| `gestion_salarios` | Habilidad para estructurar contratos eficientes | Reduce la masa salarial al firmar contratos más inteligentes |
| `ojo_cantera` | Detección de talento joven | Aumenta la probabilidad de proponer sub-23 de alto potencial |

**Relación Director Deportivo – Entrenador:** si sus perfiles son incompatibles, aparecen fricciones. El entrenador puede rechazar usar jugadores fichados por el director si no encajan en su estilo. El director puede proponer vender jugadores que el entrenador considera intocables. El presidente debe mediar o elegir a quién apoya, con consecuencias sobre la relación con el que no apoya.

---

### 15.2 Sistema de Mercado de Fichajes

El mercado opera en dos ventanas al año (enero y verano) más operaciones de libre fichaje fuera de ventana.

**Proceso de cada ventana:**
1. El director deportivo genera una lista de objetivos priorizados
2. El presidente revisa y puede aprobar, vetar o añadir nombres propios
3. El director negocia. El presidente puede intervenir (con coste en la relación si lo hace demasiado)
4. Si hay acuerdo, el presidente da la aprobación final

```python
@dataclass
class OperacionFichaje:
    jugador: Jugador
    club_origen: Club
    tipo: TipoOperacion          # COMPRA, CESION, LIBRE, TRASPASO_MAS_JUGADOR
    precio_compra: int
    salario_propuesto: int
    duracion_contrato_anios: int
    clausula_rescision: int
    opciones_clausulas: List[Clausula]   # Bonus por goles, europeos, etc.
    probabilidad_cierre: float           # Estimación del director. Depende de su atributo
    fecha_limite: Semana
```

**Mercado dinámico:** los otros 19 clubes también compran y venden. Los jugadores pueden ser interceptados por otra oferta mejor. Los jugadores de la propia plantilla reciben ofertas externas. El valor de mercado fluctúa según rendimiento y edad.

---

### 15.3 Sistema de Scouting y Niebla de Guerra

El presidente no tiene información perfecta sobre jugadores de otros clubes. Lo que sabe depende de su red de ojeadores.

```python
@dataclass
class InformeOjeador:
    jugador_id: int
    atributos_visibles: Dict[str, float]
    confianza_informe: float          # Precisión (0.0–1.0)
    sesgo_estimacion: float           # Error sistemático. Puede ser positivo o negativo
    fecha_informe: Semana
    coste_informe: int
```

| Nivel de scouting | Información disponible |
|---|---|
| Sin ojeadores | Solo estadísticas públicas básicas (goles, asistencias) |
| Ojeadores de nivel bajo | Atributos físicos y técnicos con margen de error alto (±20 pts) |
| Ojeadores de nivel medio | Atributos completos con margen de error medio (±10 pts) |
| Ojeadores de nivel alto | Atributos completos con margen de error bajo (±5 pts). Acceso internacional |

**Tipos de ojeador:**

| Tipo | Especialidad | Coste |
|---|---|---|
| Ojeador nacional | Liga doméstica. Alta cobertura | Bajo |
| Ojeador internacional | Liga específica en el extranjero | Medio |
| Jefe de scouting | Coordina la red. Mejora calidad de todos los informes | Alto |
| Analista de datos | Complementa el scouting. Reduce sesgos | Medio-alto |

---

### 15.4 Evolución de Jugadores

Los jugadores no son estáticos. Sus atributos y valor de mercado cambian con la temporada.

```python
@dataclass
class EvolucionJugador:
    progresion_anual: float    # Función de edad, atributos actuales y desarrollo_juvenil del entrenador
    regresion_anual: float     # Función de edad (regresión progresiva a partir de los 30)
    impacto_lesiones: float    # Las lesiones largas pueden reducir atributos físicos
    impacto_minutos: float     # Jugadores sin minutos no progresan
    impacto_entrenador: float  # El desarrollo_juvenil multiplica la progresión sub-23
```

**Curva de edad:**

| Rango | Tendencia | Notas |
|---|---|---|
| 16–20 años | +3 a +8 pts/año en atributos clave | Muy dependiente del entrenador y los minutos |
| 21–26 años | +1 a +4 pts/año | Pico de mejora técnica y táctica |
| 27–29 años | 0 a +2 pts/año | Máximo rendimiento. Inicio de regresión física |
| 30–32 años | -1 a -3 pts/año en atributos físicos | Atributos mentales pueden seguir subiendo |
| 33+ años | -3 a -6 pts/año | Riesgo elevado de lesión. Valor de mercado cae rápido |

---

### Tests obligatorios de la Fase 15

- El director deportivo genera una lista coherente con las necesidades de plantilla y el estilo del entrenador
- Un ojeador de nivel bajo produce informes con error dentro del rango esperado (±20 pts)
- El mercado dinámico: otros clubes no venden a sus mejores jugadores por debajo de su valor
- La evolución de jugadores sigue la curva de edad esperada en simulaciones multi-temporada
- Tests de stress: una ventana con muchas operaciones simultáneas no produce estados financieros incoherentes
- Las fricciones director deportivo–entrenador se activan en los casos esperados

### Criterio de cierre

El presidente puede gestionar dos temporadas consecutivas construyendo plantilla a través del director deportivo, con una red de scouting que da información imperfecta pero útil, y los jugadores evolucionan de forma coherente con su edad y contexto.

---

## Fase 16. Match Center: La Llotja (El Palco)

### Objetivo

Crear la interfaz desde la que el presidente observa los partidos. No controla. No da instrucciones. Observa, siente la tensión, y puede tomar decisiones de gestión que tienen efecto diferido —no inmediato— en el partido.

### Por qué esta fase es la última del bloque

Esta fase cierra el ciclo. El presidente ha contratado su staff (Fase 13), ha gestionado las finanzas y objetivos (Fase 14), ha construido la plantilla (Fase 15). Ahora llega el momento de la verdad: el partido. Y en este juego, el momento de la verdad es el momento en que el presidente tiene **menos poder**. Esa impotencia controlada es la experiencia central del juego.

---

### 16.1 Feed de Eventos del Partido

La narración para el presidente no es técnica. Es una selección de eventos significativos, filtrada por lo que un presidente en su palco percibiría.

```python
@dataclass
class EventoPresidente:
    minuto: int
    tipo: TipoEventoPresidente
    descripcion: str              # Narrativa en tono de crónica deportiva
    impacto_emocional: float      # Contribuye al estado de ánimo del vestuario
    relevancia_para_objetivo: float
```

| Tipo de evento | Ejemplos | Frecuencia |
|---|---|---|
| `GOL` | Gol a favor, en contra, en el descuento | Baja (media 2.67/partido) |
| `OCASION_CLARA` | Mano a mano fallado, disparo al palo | Media |
| `TARJETA_ROJA` | Expulsión propia o rival | Baja |
| `CAMBIO_TACTICO` | El entrenador hace una sustitución | Media |
| `LESION` | Un jugador clave sale lesionado | Baja |
| `PRESION_RIVAL` | El rival domina por completo el partido | Alta en partidos desfavorables |
| `DOMINIO_PROPIO` | El equipo está siendo claramente superior | Alta en partidos favorables |
| `MOMENTO_CLAVE` | 0-0 en el 85 con el equipo atacando | Baja |
| `REACCION_ENTRENADOR` | El entrenador cambia de plan o se queda sin opciones | Media |

**Ejemplos de narración:**

> *Min. 67 — El entrenador ha pedido más presión alta. El equipo responde pero se nota el cansancio. Si el rival aprovecha una transición en los próximos minutos, puede ser peligroso.*

> *Min. 89 — 0-1. Se acaba el tiempo. El entrenador ha agotado los cambios. En el palco se respira tensión. Nada más que hacer.*

---

### 16.2 Panel de Información del Partido

**Información siempre visible:** marcador, minuto, tarjetas y expulsiones, sustituciones realizadas.

**Información disponible bajo demanda:**

| Información | Requiere | Actualización |
|---|---|---|
| Estado físico del equipo (fatiga media) | Nada. Perceptible desde el palco | Cada 15 minutos |
| Estadísticas básicas (posesión, tiros) | Analista contratado en el staff | Cada 15 minutos |
| Rendimiento individual de jugadores | Analista de alto nivel | En tiempo real |
| Evaluación táctica del entrenador rival | Jefe de scouting con partidos analizados | Solo si el rival fue escaneado antes |

**Información que el presidente nunca tiene en tiempo real:**
- Las probabilidades internas del motor (xG acumulado, tasas exactas de fatiga)
- Lo que el entrenador va a hacer en el siguiente minuto
- El estado emocional exacto de cada jugador

> Esta restricción es **intencionada y central al diseño**. El presidente toma decisiones con información incompleta, igual que en la realidad.

---

### 16.3 Decisiones del Presidente Durante el Partido

El presidente no puede cambiar la táctica ni hacer sustituciones. Pero sí puede tomar decisiones con efecto diferido.

| Decisión | Efecto | Momento disponible |
|---|---|---|
| **Bajar al vestuario en el descanso** | Bonus de `motivacion` al segundo tiempo. Reduce confianza del entrenador si se abusa | Solo en el descanso |
| **Enviar mensaje al entrenador** | Puede acelerar o retrasar una decisión táctica que el entrenador consideraba. El efecto depende de la relación | Cualquier momento |
| **Llamada de urgencia al director deportivo** | Activa análisis de alternativas de mercado para la ventana siguiente. Sin efecto en el partido actual | Cualquier momento |
| **Hablar con la prensa post-partido** | Modifica la moral del vestuario y la presión sobre el entrenador durante los días siguientes | Solo al final |

**Efecto de "bajar al vestuario":**

- `confianza > 0.7` — El entrenador recibe bien el mensaje. Posible ajuste del plan con bonus.
- `confianza 0.4–0.7` — El entrenador lo percibe como interferencia. Sin efecto positivo.
- `confianza < 0.4` — El entrenador reacciona mal. La `tension` sube y el rendimiento del segundo tiempo puede empeorar.

---

### 16.4 Reacciones del Entrenador en Tiempo Real

| Estado | Descripción | Señal en el palco |
|---|---|---|
| `PLAN_EN_MARCHA` | El partido va según lo esperado | El entrenador está tranquilo en el banquillo |
| `EVALUANDO_CAMBIO` | El entrenador considera una sustitución | Está consultando con sus ayudantes |
| `CAMBIO_TACTICO_ACTIVO` | Se ha ordenado un cambio de sistema | El equipo está reorganizándose |
| `PREOCUPADO` | El partido no va bien y hay presión | Narración describe al entrenador inquieto |
| `SIN_OPCIONES` | Cambios agotados y resultado adverso | Narración de impotencia |
| `GESTIONANDO_VICTORIA` | El equipo va ganando y administra | El equipo baja el ritmo intencionalmente |

---

### 16.5 Análisis Post-Partido

Cuando termina el partido, el presidente recibe un informe generado por su staff. La calidad del informe depende de quién trabaje para él.

**Resumen ejecutivo** *(siempre disponible):*
- Resultado final y contexto (local/visitante, importancia del partido)
- Valoración del rendimiento global (Bueno / Irregular / Malo)
- Impacto en los objetivos de temporada

**Análisis táctico** *(requiere analista contratado):*
- Qué táctica usó el entrenador y por qué
- Dónde funcionó y dónde no
- Qué hizo el equipo rival

**Rendimiento individual** *(requiere analista de alto nivel):*
- Los 3 mejores y los 3 peores jugadores del partido
- Señales de lesión o fatiga preocupante

**Perspectiva de mercado** *(requiere director deportivo activo):*
- Jugadores rivales que hayan destacado como candidatos de fichaje
- Jugadores propios que hayan bajado de valor por su rendimiento

---

### Tests obligatorios de la Fase 16

- El feed produce entre N y M eventos por partido según su importancia
- Los eventos visibles son un subconjunto coherente del log completo del motor
- La decisión "bajar al vestuario" produce el efecto correcto según el estado de la relación
- Los informes incluyen exactamente las secciones correspondientes al staff contratado, ni más ni menos
- Un partido sin analistas produce un informe más pobre que uno con staff completo
- El estado del entrenador durante el partido es consistente con lo que el motor registra internamente
- La misma seed produce el mismo feed de eventos y el mismo informe post-partido

### Criterio de cierre

El presidente puede vivir un partido completo desde el palco, percibir la tensión del marcador, observar las reacciones de su entrenador, tomar las pocas decisiones disponibles, y recibir al final un informe diferenciado según la calidad de su staff. El ciclo completo **partido → análisis → preparación → partido siguiente** funciona de forma fluida.

---

## Dependencias entre fases

```
Fase 13 — Entrenador e IA táctica
    ├── necesaria para Fase 14 (el sistema de objetivos necesita que el entrenador simule autónomamente)
    ├── necesaria para Fase 15 (el director deportivo propone fichajes según el estilo del entrenador)
    └── necesaria para Fase 16 (las reacciones del entrenador en el partido dependen de su IA)

Fase 14 — Economía
    ├── necesaria para Fase 15 (el mercado de fichajes requiere el sistema financiero)
    └── necesaria para Fase 16 (el análisis post-partido incluye impacto económico)

Fase 15 — Scouting y mercado
    └── necesaria para Fase 16 (el informe post-partido incluye perspectiva de mercado)
```

Las fases se construyen en orden estricto. No hay atajos.

---

## Métricas de éxito del bloque de gestión

Al igual que las Fases 0–12 tenían calibración estadística contra LaLiga, el bloque de gestión tiene sus propias métricas de validación:

| Métrica | Cómo medirla | Target |
|---|---|---|
| Diversidad de estilos de entrenador | En 100 temporadas simuladas, distribución de tácticas amplia y diferenciada | Sin estilo dominante con > 60% de cuota |
| Coherencia de decisiones del entrenador | El entrenador toma la decisión "esperable" según su perfil | > 80% de los casos |
| Viabilidad financiera base | Una gestión neutral no quiebra el club en 3 temporadas | 100% de las simulaciones |
| Precisión de scouting | Error de ojeador de nivel bajo dentro del rango declarado (±20 pts) | 95% de los informes |
| Diferenciación de informes | Informe con staff completo contiene al menos el doble de información que sin staff | Siempre |

---

## Plan de ejecución inmediato

En orden estricto de dependencia técnica:

1. **Refactor de la entidad `Entrenador`** en la BD y en el dominio. Mapear datos existentes al nuevo modelo de atributos.
2. **Implementar `MotorDecisionTactica`** como servicio desacoplado. Primero la decisión pre-partido; las decisiones en tiempo real son complejidad adicional.
3. **Validar que el motor existente acepta tácticas generadas por el entrenador** sin cambios en el núcleo de simulación.
4. **Construir el modelo económico básico**: ingresos fijos y salarios. Sin mercado todavía.
5. **Implementar el sistema de objetivos del consejo** con las consecuencias simples (advertencia, presión).
6. **Primer prototipo del feed de eventos del partido** usando el log existente del motor como fuente.
7. **Director deportivo básico**: solo propuestas de fichaje. El mercado dinámico es fase posterior.
8. **Integración completa de la Fase 16** con feed real, panel de información y análisis post-partido.

---

*Versión del documento: Abril 2026*
