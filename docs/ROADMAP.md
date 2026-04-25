# Roadmap de Construcción

## Objetivo del proyecto

Construir un motor de simulación de partidos de fútbol con foco en realismo estadístico, empezando desde cero, creciendo en pasos muy pequeños y validando cada capa contra datos reales de LaLiga.

El objetivo no es "hacer un simulador que funcione", sino un sistema que:

- use datos reales de equipos y jugadores desde MySQL;
- permita explicar por qué ocurre cada evento;
- pueda calibrarse con evidencia;
- tenga tests automáticos en todos los niveles;
- se acerque de forma medible a distribuciones reales de LaLiga.

## Principios no negociables

1. Greenfield real.
   El proyecto se construye desde cero en este repositorio. No se hereda código de intentos anteriores.

2. Complejidad incremental.
   No activaremos "todos los stats" en la primera simulación. Sí se ingieren y normalizan desde el inicio, pero se incorporan al motor por capas para poder medir el impacto real de cada grupo de atributos.

3. Todo cambio exige validación.
   Ninguna mejora entra solo porque "suena realista". Debe pasar tests y mejorar o mantener las métricas de calibración.

4. El realismo se mide, no se declara.
   Cada milestone tendrá métricas objetivo frente a datos reales de LaLiga.

5. Arquitectura explicable.
   El motor debe poder responder preguntas como:
   "¿por qué este equipo generó tan poco x peligro?" o "¿qué stats empujaron este gol?".

6. Determinismo controlado.
   Toda simulación debe poder ejecutarse con semilla fija para reproducir resultados y depurar.

## Enfoque técnico recomendado

### Stack inicial

- Lenguaje del núcleo de simulación: Python
- Test runner: `pytest`
- Property-based testing: `hypothesis`
- Tipado: `mypy`
- Lint/format: `ruff`
- Acceso a MySQL: `SQLAlchemy` o `mysqlclient`/`mysql-connector`
- Análisis y calibración: `pandas`, `numpy`, `scipy`
- Configuración: `.env` + settings tipados

### Motivo de esta elección

Para un motor que necesita simulación masiva, calibración estadística, comparación con datasets reales y experimentación rápida, Python da mejor base que empezar con una stack orientada a frontend. Si más adelante queremos API o dashboard, se añade encima del core, no al revés.

## Estrategia general del proyecto

El proyecto se divide en 12 grandes fases. Cada fase debe dejar un sistema usable, testeado y medible antes de pasar a la siguiente.

## Fase 0. Fundación del proyecto

### Objetivo

Preparar un repositorio serio, reproducible y listo para construir el motor sin deuda accidental.

### Entregables

- estructura inicial del repositorio;
- entorno virtual y dependencias base;
- configuración de `pytest`, `hypothesis`, `ruff`, `mypy`;
- carpeta `docs/`;
- carpeta `src/`;
- carpeta `tests/`;
- carpeta `scripts/`;
- carpeta `data_samples/` para fixtures y snapshots controlados;
- archivo de configuración para conexión a MySQL;
- primer pipeline local de test/lint/type-check.

### Estructura sugerida

```text
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

- los tests arrancan en limpio;
- la configuración carga correctamente;
- existe una seed reproducible;
- un comando único ejecuta lint, type-check y tests.

### Criterio para cerrar fase

No seguimos hasta tener una base de trabajo reproducible en una máquina nueva sin pasos ambiguos.

## Fase 1. Modelo de dominio puro

### Objetivo

Definir el lenguaje del sistema antes de simular nada.

### Entregables

- entidades de dominio:
  - `Team`
  - `Player`
  - `MatchContext`
  - `Lineup`
  - `Tactic`
  - `PlayerAttributes`
  - `MatchState`
  - `Event`
- tipos y enums:
  - posiciones;
  - roles;
  - pie dominante;
  - estado físico;
  - estados del partido;
- normalización de atributos;
- reglas de validación del dominio.

### Decisión clave

Separar desde el principio:

- datos crudos de base de datos;
- atributos normalizados para simulación;
- variables derivadas calculadas por el motor.

### Ejemplos de variables derivadas futuras

- capacidad de progresión;
- capacidad de finalización;
- resistencia efectiva;
- presión defensiva efectiva;
- amenaza aérea;
- control bajo presión.

### Tests obligatorios de salida

- creación válida e inválida de entidades;
- validación de rangos;
- serialización y deserialización;
- invariantes de dominio.

### Criterio para cerrar fase

El dominio debe estar definido sin depender todavía de decisiones del motor minuto a minuto.

## Fase 2. Capa de datos y mapeo desde MySQL

### Objetivo

Conectar la base de datos real y convertir sus stats a un modelo utilizable por el simulador.

### Entregables

- cliente de lectura a MySQL;
- repositorios de datos para equipos, jugadores y alineaciones;
- mapeador de columnas reales a atributos del dominio;
- catálogo de stats disponibles;
- sistema de versionado del mapeo;
- fixtures pequeñas para tests sin depender siempre de la BD real.

### Regla importante

Aquí sí cargamos todos los stats disponibles, pero no los usamos todos aún en el motor. Primero se catalogan, limpian, documentan y normalizan.

### Trabajo específico

1. Inventario completo de columnas disponibles en la BD.
2. Clasificación por familias:
   - físicos;
   - técnicos;
   - defensivos;
   - mentales;
   - portero;
   - contexto biográfico;
   - contexto táctico.
3. Detección de:
   - nulos;
   - outliers;
   - columnas redundantes;
   - columnas derivables;
   - stats con escala inconsistente.
4. Definición de normalización.

### Tests obligatorios de salida

- conexión real a la BD;
- mapeo correcto de un equipo completo;
- detección de datos inválidos;
- snapshots de importación;
- tests de regresión sobre el catálogo de columnas.

### Criterio para cerrar fase

Podemos cargar dos equipos de LaLiga completos y obtener objetos de dominio limpios y consistentes.

## Fase 3. Baseline del simulador

### Objetivo

Construir la versión mínima del partido que sirva como banco de calibración.

### Qué debe simular esta primera versión

- marcador final;
- goles;
- tiros;
- tiros a puerta;
- posesión aproximada;
- faltas;
- córners;
- tarjetas básicas;
- fatiga simple.

### Qué no debe intentar todavía

- trayectorias espaciales complejas;
- animación mental de cada jugador;
- microdecisiones segundo a segundo;
- uso exhaustivo de todos los atributos.

### Arquitectura propuesta

Modelo híbrido por posesiones/eventos, no simulación física continua.

Unidad base inicial:

- posesión;
- subfase ofensiva;
- resolución del desenlace de la posesión.

### Por qué empezar así

Es mucho más fácil calibrar primero distribuciones de partido que lanzar un simulador hipergranular imposible de ajustar.

### Entregables

- generador de partidos con semilla;
- pipeline de posesión;
- resolución básica de ataque/defensa;
- asignación de eventos a jugadores;
- salida estructurada del partido.

### Tests obligatorios de salida

- reproducibilidad por seed;
- invariantes del partido;
- no negativos;
- consistencia entre eventos y resultado final;
- tests de Monte Carlo básicos.

### Criterio para cerrar fase

Ya podemos simular miles de partidos y obtener distribuciones estables.

## Fase 4. Marco formal de realismo y calibración

### Objetivo

Crear el sistema que decidirá si el motor se parece o no a LaLiga.

### Métricas iniciales a comparar con datos reales

- goles por partido;
- goles local vs visitante;
- distribución de empates;
- tiros por partido;
- tiros a puerta por partido;
- posesión media y dispersión;
- faltas;
- tarjetas amarillas;
- tarjetas rojas;
- córners;
- porterías a cero;
- frecuencia de resultados exactos;
- distribución de goles por minuto o por tramo temporal.

### Métricas por equipo

- puntos esperados por fuerza;
- goles a favor;
- goles en contra;
- diferencia de gol;
- frecuencia de victoria local;
- estabilidad de ranking en simulaciones masivas.

### Métricas por jugador

- cuota de tiros del equipo;
- cuota de goles del equipo;
- cuota de asistencias;
- impacto de la fatiga;
- impacto posicional.

### Herramientas de validación

- tests estadísticos por rangos aceptables;
- comparación de distribuciones;
- dashboards de calibración;
- snapshots numéricos por versión del motor.

### Decisión metodológica

Cada métrica tendrá:

- fuente real;
- ventana temporal;
- valor objetivo;
- tolerancia aceptable;
- severidad si falla.

### Tests obligatorios de salida

- suite `tests/statistical/`;
- informe automático de calibración;
- semilla y muestra fijas para regresión;
- comparación entre versiones del motor.

### Criterio para cerrar fase

El proyecto deja de depender de intuición y pasa a depender de evidencia.

## Fase 5. Activación progresiva de atributos reales

### Objetivo

Empezar a usar los stats de verdad de manera incremental y medible.

### Orden recomendado de activación

1. Finalización, pase, regate, tackle, reflejos, velocidad, resistencia.
2. Posicionamiento, anticipación, agresividad, control, juego aéreo.
3. Visión, toma de decisiones, presión, compostura, pie dominante.
4. Rasgos más contextuales o de menor señal.

### Regla de activación

Cada nueva familia de stats entra con:

- hipótesis explícita;
- fórmula o mecanismo concreto;
- tests unitarios;
- test de sensibilidad;
- validación estadística antes/después.

### Ejemplo de criterio correcto

"Añadir `decision_making` debe reducir tiros malos y mejorar la relación tiros a puerta/tiros totales en perfiles élite."

### Ejemplo de criterio incorrecto

"Añadir más stats para que el motor sea más realista."

### Tests obligatorios de salida

- tests de contribución de atributo;
- tests de monotonicidad;
- property-based tests;
- pruebas A/B del motor con y sin cada grupo de stats.

### Criterio para cerrar fase

Podemos justificar matemáticamente por qué cada grupo de stats sigue dentro del modelo.

## Fase 6. Táctica, alineaciones y contexto de partido

### Objetivo

Pasar de un motor centrado en capacidad individual a uno donde importen también la estructura y el contexto.

### Variables a introducir

- formación;
- roles por jugador;
- estilo de presión;
- altura de bloque;
- amplitud;
- ritmo;
- agresividad;
- ventaja de local;
- estado de marcador;
- gestión de fatiga;
- sustituciones.

### Importancia

Sin esta fase, el motor puede parecer correcto a nivel agregado pero fallar mucho en comportamiento de equipos concretos.

### Entregables

- representación táctica formal;
- modificadores contextuales;
- cambios de plan durante el partido;
- sustituciones con reglas y triggers.

### Tests obligatorios de salida

- una táctica ofensiva debe aumentar volumen ofensivo y exposición defensiva;
- una táctica defensiva debe hacer lo contrario;
- el marcador influye en el comportamiento;
- los cambios afectan a la fatiga y al output ofensivo/defensivo.

### Criterio para cerrar fase

Los equipos ya no son solo la suma plana de sus jugadores.

## Fase 7. Motor de eventos avanzado

### Objetivo

Refinar la simulación del partido sin caer todavía en una física imposible de calibrar.

### Eventos a desarrollar

- secuencias de posesión más ricas;
- pérdidas en salida;
- transiciones;
- contraataques;
- centros;
- balón parado;
- penaltis;
- duelos aéreos;
- rebotes;
- bloqueos de disparo;
- asistencias;
- errores no forzados.

### Decisión de arquitectura

Seguir con un motor de eventos probabilístico explicable, enriquecido por estado contextual, antes de plantear una simulación espacial de alta resolución.

### Motivo

Si la versión event-driven ya no puede capturar la realidad con precisión suficiente, entonces habrá evidencia para incorporar una capa espacial posterior. No antes.

### Tests obligatorios de salida

- consistencia causal de eventos;
- validación por tipo de evento;
- regresión estadística;
- sensibilidad táctica;
- sensibilidad por perfil de jugador.

### Criterio para cerrar fase

El partido produce narrativas plausibles además de números plausibles.

## Fase 8. Capa espacial del partido

### Objetivo

Introducir representación espacial del partido para modelar eventos que dependen de la posición del balón y los jugadores en el campo.

### Por qué ahora

El motor actual funciona bien a nivel agregado para métricas globales (goles, posesión, tiros). Pero hay aspectos que no puede capturar:

- Un passe desde campo propio vs cerca del área tiene dificultad diferente
- Los contraataques son más efectivos cuando se capturan en campo rival
- Los córners solo ocurren cerca del área
- La presión alta solo tiene efecto en campo contrario

### Arquitectura propuesta

#### Representación del campo

```
Campo dividido en 3 zonas longitudinales:
- ZONA_DEFENSA: 0-33 (x)
- ZONA_MEDIOCAMPO: 34-66 (x)  
- ZONA_ATAQUE: 67-100 (x)

Eje Y: 0-100 (banda a banda)

Coordenadas del balón: (x, y) donde x∈[0,100], y∈[0,100]
```

#### Modelo de estado espacial

```python
@dataclass
class EstadoEspacialPartido:
    """Estado espacial mutable durante la simulación."""
    
    posicion_balon: tuple[float, float] = (50.0, 50.0)
    posesion: int | None = None  # id del equipo con posesión
    zona_actual: str = "MEDIOCAMPO"
    ultimo_pase: tuple[float, float] | None = None
    tiempo_en_zona: dict[str, float] = field(default_factory=dict)
    contracapturas: int = 0
```

#### Transiciones entre zonas

- **Saquetiro de inicio**: (50, 50) → posseedor aleatorio
- **Pase progresivo**: probabilidad de avanzar zona basada en calidad de pase
- **Pérdida**: transition a otro equipo, vuelve a zona media
- **Tiro**: siempre desde ZONA_ATAQUE
- **Corner**: siempre desde ZONA_ATAQUE en banda

### Variables a introducir

1. **Coordenadas del balón** - posición (x, y) en el campo
2. **Zona del campo** - defensa/medio/ataque
3. **Tiempo en cada zona** -para medir dominio territorial
4. **Evento de transición** - cambios de zona con probabilidad
5. **Dificultad contextual** - un passe en zona defensiva es más seguro

### Métricas nuevas a validar

- Posesión territorial: % tiempo en cada zona
- Progresión: cuántas transiciones zona defensa → ataque
- Efficiency de passe según zona: éxito en campo propio vs rival
- Concentración de tiros: 80%+ deben ser desde zona ataque
- Concentración de córners: 100% desde ataque

### Implementación por etapas

#### Etapa 8.1: Fundación espacial

- Definir estructuras de coordenadas y zonas
- Añadir estado espacial al contexto del partido
- Implementar transiciones básicas de zona

#### Etapa 8.2: Pases con ubicación

- Añadir probabilidad de progresión según calidad de pase
- Dificultar passes retrospectivos hacia atrás
- Modelar retención en zona propia

#### Etapa 8.3: Tiros contextuales

- Solo permitir tiros desde ZONA_ATAQUE
- Añadir bonificador por proximidad a portería
- Distinguir tiro desde zona media vs área

#### Etapa 8.4: Contraespacios

- Contracaptura más probable en campo contrario
- Transiciones rápidas defensa → ataque
- Métricas de contraespacio territorio

### Tests obligatorios de salida

- un passe tiene diferentes probabilidades según zona de origen
- los tiros ocurren exclusivamente desde zona de ataque
- los córners solo se lanzan desde zona de ataque
- laposesión territorial refleja diferencias de equipo
- los contraataques progresan más rápido a zona de ataque

### Criterio para cerrar fase

El motor produce métricas de posición además de globales, y los eventos tienen ubicación coherente con las reglas del fútbol.

## Fase 9. Modelo de expected goals (xG) y calidad de finalización

### Objetivo

Reemplazar la probabilidad de gol plana por un modelo de xG basado en atributos contextuales y espaciales, para que el motor distinga entre un tiro bien ejecutado desde el área pequeña y un remate desde 35 metros.

### Por qué ahora

Con la capa espacial de la Fase 8, el balón ya tiene ubicación. El siguiente paso natural es que esa ubicación, junto con el perfil del rematador y el contexto defensivo, determine la calidad real del disparo. Sin esto, la relación entre tiros y goles es mecánica e independiente de quien y desde donde dispara.

### Variables que entran al modelo de xG

- distancia al centro de la portería;
- ángulo de tiro;
- zona de disparo (área pequeña, área grande, frontal, lateral, lejana);
- tipo de acción previa (centro, pase de ruptura, contraataque, balón parado);
- pie de contacto (dominante vs no dominante);
- atributos del rematador: finalización, compostura, potencia;
- presión defensiva en el momento del disparo;
- si el disparo es de cabeza;
- si hay portero posicionado o en movimiento (implícito por zona y contexto);
- fatiga acumulada del rematador.

### Métricas de calibración

- xG medio por tiro vs datos reales de LaLiga (~0.10-0.12 por tiro);
- correlación xG acumulado vs goles reales por equipo en simulación de temporada;
- distribución de goles por tipo de acción (centro, contraataque, balón parado, juego abierto);
- porcentaje de goles de cabeza (~20-25% en LaLiga);
- tasa de conversión por zona de disparo.

### Entregables

- modelo de xG explicable con peso por variable;
- calculadora de xG por disparo con log de factores;
- separación entre xG por partido y goles reales (varianza);
- comparador automático xG simulado vs xG histórico LaLiga.

### Tests obligatorios de salida

- un tiro desde el punto de penalti de un delantero élite tiene xG ≥ 0.70;
- un remate de cabeza desde 20 metros tiene xG ≤ 0.05;
- un jugador con alta finalización genera mayor xG en igualdad de posición;
- el xG acumulado por equipo en 1000 partidos está correlacionado con puntos;
- subir la compostura del rematador no empeora el xG en ningún escenario;
- la suma de goles simulados converge al xG total con suficientes muestras (LGN);
- property-based: xG ∈ [0, 1] para cualquier combinación de inputs válidos.

### Criterio para cerrar fase

El motor produce xG por disparo explicable y calibrado, y la relación entre xG acumulado y goles reales por equipo se mantiene dentro de la varianza esperada en LaLiga.

---

## Fase 10. Simulación de temporada y competición

### Objetivo

Escalar el motor desde partidos individuales hasta temporadas completas reproducibles, con tabla de clasificación, estadísticas individuales acumuladas, rotaciones y efectos de calendario.

### Por qué ahora

El motor ya produce partidos realistas. Para validar que los equipos se comportan de forma coherente a lo largo de 38 jornadas y que el campeón no es aleatorio, hay que simular temporadas enteras y comparar con datos históricos de LaLiga.

### Qué debe simular esta fase

- generación automática del calendario de LaLiga (38 jornadas, local/visitante simétrico);
- rotaciones de alineación basadas en fatiga acumulada y lesiones simples;
- degradación de atributos por fatiga de temporada;
- estadísticas acumuladas por jugador (goles, asistencias, tiros, minutos, xG);
- tabla de clasificación con puntos, diferencia de gol, goles a favor y en contra;
- estadísticas de rendimiento de local vs visitante por equipo a lo largo de la temporada.

### Métricas de calibración

- % de veces que el favorito (por calidad de plantilla) gana la liga en 1000 temporadas;
- distribución de puntos del campeón (media ~85-90 en LaLiga);
- distribución de puntos del descenso (~30-35);
- diferencia entre el mejor y peor equipo en goles a favor;
- coeficiente de concentración de goles por jugador (los 5 máximos goleadores vs el resto);
- correlación entre calidad de plantilla y posición final.

### Entregables

- generador de calendario de temporada;
- acumulador de estadísticas por jugador y equipo;
- sistema de rotación de alineaciones;
- exportador de tabla de clasificación y estadísticas al final de temporada;
- comparador automático de distribución de puntos vs LaLiga histórica.

### Tests obligatorios de salida

- el campeón de 1000 temporadas no es siempre el mismo equipo, pero el favorito gana con frecuencia estadísticamente superior;
- los puntos del campeón caen dentro del rango histórico de LaLiga;
- ningún equipo acumula más de 38 victorias en 38 partidos;
- las estadísticas individuales de un jugador lesionado reflejan menos minutos;
- el calendario garantiza exactamente 19 partidos de local y 19 de visitante por equipo;
- reproducibilidad: la misma seed produce la misma tabla final;
- property-based: la suma de puntos de todos los equipos siempre es consistente con el número de partidos jugados.

### Criterio para cerrar fase

Podemos simular 1000 temporadas completas de LaLiga y comparar la distribución de puntos, goleadores y posiciones finales contra datos históricos dentro de tolerancias definidas.

---

## Fase 11. Capa de observabilidad, explicabilidad y API

### Objetivo

Hacer que el motor sea consultable desde fuera, que cada simulación pueda auditarse evento por evento, y que el sistema pueda responder preguntas causales de forma programática.

### Por qué ahora

El motor es cada vez más complejo. Sin una capa de observabilidad, depurar un partido extraño o entender por qué un equipo rinde muy por debajo de lo esperado requiere leer código. Esta fase convierte el motor en un sistema explicable por diseño.

### Capacidades a desarrollar

#### Trazabilidad de eventos

- log estructurado de cada evento con sus inputs, probabilidades y resultado;
- visualización textual del partido minuto a minuto con causas;
- acceso al árbol de decisión de cada gol: "¿qué factores llevaron a este gol?".

#### Motor de preguntas causales

- "¿por qué este equipo generó tan poco peligro en este partido?";
- "¿qué atributo tuvo mayor impacto en el resultado?";
- "¿qué habría cambiado si el delantero tuviera 10 puntos más de finalización?".

#### API REST del simulador

- endpoint de simulación de partido individual;
- endpoint de simulación de temporada;
- endpoint de calibración bajo demanda;
- endpoint de scorecard de realismo.

#### Sistema de alertas de regresión

- alerta automática si una nueva versión empeora el scorecard global en más de un umbral configurado;
- comparación de distribuciones entre versiones con p-value.

### Entregables

- log estructurado en JSON por simulación;
- módulo de consulta causal sobre el log;
- API REST con FastAPI o equivalente;
- documentación de contratos de la API;
- sistema de alertas de regresión automático.

### Tests obligatorios de salida

- el log de un partido contiene al menos un registro por evento con sus factores explicativos;
- una pregunta causal sobre un gol devuelve los tres factores con mayor peso;
- el endpoint de simulación devuelve un partido válido en menos de 200ms;
- la alerta de regresión se dispara si el scorecard de goles baja del umbral definido;
- property-based: el log de cualquier partido válido es parseble y no contiene estados contradictorios.

### Criterio para cerrar fase

Un usuario externo puede simular un partido, leer el log estructurado, hacer preguntas causales y recibir respuestas explicables sin necesidad de acceder al código del motor.

---

## Fase 12. Calibración automatizada y optimización de parámetros

### Objetivo

Sustituir el ajuste manual de parámetros del motor por un sistema de calibración automática que minimiza la distancia entre las distribuciones simuladas y las distribuciones reales de LaLiga.

### Por qué ahora

Llegados a este punto, el motor tiene decenas de parámetros: pesos de atributos, modificadores tácticos, curvas de fatiga, multiplicadores de xG, probabilidades base de evento. Ajustarlos a mano es ineficiente y no garantiza un óptimo global. Esta fase convierte la calibración en un proceso científico y repetible.

### Estrategia de calibración

#### Función objetivo

Distancia total entre distribuciones simuladas y reales, ponderada por relevancia:

- KL divergence o Wasserstein distance en goles, tiros, posesión;
- error cuadrático medio en métricas agregadas por equipo;
- error en correlación xG vs goles reales;
- penalización por invariantes rotas.

#### Métodos de optimización a considerar

- búsqueda aleatoria con constraints (primera iteración);
- optimización bayesiana (segunda iteración, más eficiente);
- algoritmos evolutivos si el espacio es no diferenciable;
- grid search limitado para parámetros discretos o de baja dimensión.

#### Validación cruzada temporal

- calibrar sobre temporadas pasadas (por ejemplo, 2019-2022);
- validar sobre temporadas recientes no vistas (2023-2024);
- detectar sobreajuste temporal.

### Entregables

- módulo de calibración automatizada con interfaz configurable;
- registro de cada experimento de calibración con parámetros y scores;
- comparador de versiones calibradas;
- informe automático de calibración con gráficas de convergencia;
- sistema de congelación de parámetros validados.

### Tests obligatorios de salida

- la calibración automática con seed fija produce el mismo resultado en dos ejecuciones;
- los parámetros calibrados pasan todos los invariantes del motor;
- el scorecard de una versión calibrada es estrictamente mejor o igual que la versión anterior;
- la calibración detecta y rechaza configuraciones que rompen invariantes aunque mejoren métricas locales;
- el proceso de calibración completo termina en tiempo acotado definido en la configuración;
- property-based: ningún parámetro calibrado sale de sus rangos válidos declarados.

### Criterio para cerrar fase

El motor puede recalibrarse automáticamente ante nuevos datos de LaLiga sin intervención manual, produciendo una versión nueva que mejora o mantiene el scorecard global y supera la validación cruzada temporal.

---

## Artefactos de datos de calibración

### Origen

Durante la fase de planificación del proyecto se construyó un conjunto de datos de referencia
a partir de estadísticas reales de LaLiga (temporada 2024-25 principal + histórico 2019-25).
Este conjunto vive en dos archivos complementarios dentro del repositorio:

```
docs/
  calibration/
    LaLiga_Stats_Calibracion_2024-25.xlsx   ← fuente de datos visual, exploración humana
    CALIBRATION_TARGETS.md                  ← fuente autoritativa para el código y los tests
```

### Rol de cada archivo

#### `LaLiga_Stats_Calibracion_2024-25.xlsx`

Archivo Excel de consulta humana con siete hojas:

- **Resumen General** — 20 métricas clave por partido con valor real, rango observado y tolerancia.
- **Clasificación 2024-25** — tabla final oficial de los 20 equipos con estadísticas derivadas.
- **Stats por Equipo** — xG estimado, posesión, top scorer y rendimiento relativo por equipo.
- **Goleadores Top 20** — ranking Pichichi con estadísticas de finalización.
- **xG y Modelo Disparo** — xG base por zona de disparo y tabla de modificadores multiplicativos.
- **Scorecard Calibración** — plantilla para registrar manualmente el valor simulado vs el real.
- **Histórico Multi-Temporada** — datos de las 6 temporadas 2019-25 para calibración temporal.

Este archivo se usa para exploración, discusión y presentación. No lo lee el código directamente.

#### `CALIBRATION_TARGETS.md`

Documento estructurado con todos los valores de referencia embebidos como bloques Python válidos.
Lo importa `src/calibration/targets.py` y lo consumen los tests estadísticos.

Contiene seis secciones de datos:

- `MATCH_TARGETS` — métricas por partido (goles, tiros, xG, posesión, eventos, resultados).
- `GOAL_TIMING_TARGETS` — distribución de goles por tramo temporal de 15 minutos.
- `GOAL_TYPE_TARGETS` — fracción de goles por tipo de acción (juego abierto, penalti, córner…).
- `XG_ZONE_TARGETS` — xG medio y distribución por zona de disparo (10 zonas).
- `XG_MODIFIERS` — modificadores multiplicativos del xG base (pie, presión, fatiga, compostura).
- `SEASON_TARGETS` — puntos del campeón, descenso, goles totales, distribución de equipos.
- `HARD_INVARIANTS` — 13 invariantes duros que deben cumplirse en toda simulación.
- `HISTORICAL_SEASONS` — datos de las 6 temporadas para validación cruzada temporal.

### Relación con las fases del proyecto

| Sección de datos | Primera fase que la consume | Tests asociados |
|---|---|---|
| `MATCH_TARGETS` (goles, resultados) | **Fase 3** — Baseline | `tests/statistical/test_match_distributions.py` |
| `MATCH_TARGETS` (tiros, SOT, xG) | **Fase 4** — Marco de calibración | `tests/statistical/test_match_distributions.py` |
| `MATCH_TARGETS` (posesión, eventos) | **Fase 5** — Atributos reales | `tests/statistical/test_match_distributions.py` |
| `GOAL_TYPE_TARGETS` | **Fase 7** — Eventos avanzado | `tests/statistical/test_event_distributions.py` |
| `GOAL_TIMING_TARGETS` | **Fase 7** — Eventos avanzado | `tests/statistical/test_event_distributions.py` |
| `XG_ZONE_TARGETS`, `XG_MODIFIERS` | **Fase 9** — Modelo xG | `tests/statistical/test_xg_model.py` |
| `SEASON_TARGETS` | **Fase 10** — Temporada | `tests/statistical/test_season_distributions.py` |
| `HARD_INVARIANTS` | **Fase 3** en adelante | `tests/unit/test_invariants.py` |
| `HISTORICAL_SEASONS` | **Fase 12** — Calibración automática | `tests/statistical/test_temporal_validation.py` |

### Reglas de mantenimiento

1. **El `.md` es la fuente autoritativa para el código.** Si hay discrepancia entre el `.xlsx` y el `.md`, el `.md` manda.
2. **Los targets no se tocan para que pasen los tests.** Si el motor no pasa un target CRÍTICO, se abre una tarea de calibración documentada. No se relaja la tolerancia.
3. **Actualización anual.** Al finalizar cada temporada de LaLiga se actualiza el `.xlsx` con los nuevos datos, se revisan los valores en el `.md` y se registra la versión en el header del archivo.
4. **Separación de responsabilidades.** `CALIBRATION_TARGETS.md` contiene los targets reales. Los parámetros internos del motor (multiplicadores, curvas, probabilidades base) viven en `src/simulation/config/` y son los que cambia la Fase 12, nunca los targets.
5. **Los targets históricos nunca se eliminan.** Se marcan como `deprecated` si una temporada queda fuera de la ventana de calibración, pero permanecen para trazabilidad.

---

## Sistema de testing del proyecto

## 1. Tests unitarios

Para fórmulas, normalizaciones, validaciones, mapeadores y reglas básicas.

## 2. Tests de integración

Para BD real, carga de equipos, construcción de lineups, pipeline de simulación completo.

## 3. Tests estadísticos

Para simular miles de partidos y comprobar que las distribuciones se mueven dentro de umbrales definidos.

## 4. Tests de regresión

Para congelar seeds, outputs esperados e informes de calibración por versión.

## 5. Property-based testing

Para asegurar invariantes aunque cambien inputs, seeds y combinaciones de stats.

## 6. Tests de sensibilidad

Para comprobar que subir o bajar un atributo clave desplaza el resultado en la dirección esperada.

## 7. Tests de rendimiento

Para medir cuántos partidos por segundo podemos simular y cuánto tarda una temporada completa o una batería Monte Carlo.

## Sistema de validación de realismo

Cada versión del motor tendrá un "scorecard" de realismo.

### Componentes del scorecard

- realismo global de partido;
- realismo por equipo;
- realismo por jugador;
- estabilidad en simulación masiva;
- explicabilidad;
- coste computacional.

### Regla de promoción de versión

Una versión nueva no avanza de milestone si:

- rompe invariantes;
- empeora claramente el scorecard sin una razón aceptada;
- introduce parámetros imposibles de explicar;
- aumenta mucho la complejidad sin mejorar métricas.

---

## Estado Actual del Proyecto (Abril 2026) - CALIBRACIÓN COMPLETADA

Tras un intenso proceso de ajuste fino y amplificación de diferencias de calidad, el motor de simulación ha alcanzado un estado de madurez profesional, cumpliendo con los exigentes targets de LaLiga 2024-25.

### ✅ Fases Completadas (100%)

- **Fase 0 a 6:** Cimentación, dominio, datos, motor baseline, marco de calibración, atributos y tácticas.
- **Fase 7. Eventos Avanzados:** Implementación rica de contraataques, transiciones y gestión de fatiga.
- **Fase 8. Capa Espacial:** Sistema de coordenadas (x,y) y zonas del campo totalmente operativo.
- **Fase 9. Modelo de xG:** Modelo multiplicativo calibrado que distingue calidad de finalización y contexto.
- **Fase 10. Simulación de Temporada:** Validación exitosa de 38 jornadas (Puntos campeón 83, Descenso 39, Goles 1000+).
- **Fase 11. Observabilidad:** Narración minuto a minuto en tiempo real y logs estructurados de eventos.
- **Fase 12. Calibración:** Los tests estadísticos pasan con severidad verde en todas las métricas críticas.

### 📊 Estado Final de Calibración (N=1000 partidos)

| Métrica | Resultado | Target | Estado |
|--------|-----------|--------|--------|
| Goles/partido | 2.67 | 2.62 ± 0.20 | ✅ PASS |
| Tiros/partido | 22.4 | 23.0 ± 2.0 | ✅ PASS |
| Puntos Campeón | 83-92 | 88 ± 6 | ✅ PASS |
| Puntos Descenso | 35-40 | 40 ± 5 | ✅ PASS |
| % Victoria Local | 44% | 44% ± 4% | ✅ PASS |
| Dominancia Top | 79% wins | Real Madrid vs Elche | ✅ REALISTA |

---

## NUEVAS FASES: Frontend y Gestión (Simulador de Manager)

Una vez el motor es sólido, el proyecto evoluciona hacia una aplicación web interactiva.

## Fase 13. Infraestructura Web y API de Consumo

### Objetivo
Crear la capa de servicios que exponga el motor al mundo exterior y preparar el stack de frontend.

### Entregables
- **Backend**: Servidor FastAPI para servir datos de equipos, jugadores y lanzar simulaciones.
- **Frontend Base**: Configuración de Next.js/React con un sistema de diseño premium (vibrant dark mode).
- **WebSockets**: Implementación de canales de comunicación para recibir la narración del partido en vivo.

## Fase 14. Match Center: Visualización en Tiempo Real

### Objetivo
Transformar el script de consola `narrar_partido.py` en una experiencia visual impactante.

### Funcionalidades
- **Live Feed**: Pantalla de narración con animaciones para eventos clave (GOAL, VAR, RED CARD).
- **Stats Dinámicas**: Posesión, tiros y xG actualizándose segundo a segundo.
- **Campo Visual**: Representación 2D simplificada del estado espacial (dónde está el balón).

## Fase 15. Dashboard de Gestión y Base de Datos

### Objetivo
Permitir al usuario explorar el universo del juego y gestionar su equipo.

### Funcionalidades
- **Vista de Club**: Plantilla, palmarés y estado financiero.
- **Perfil de Jugador**: Ficha técnica con radar de atributos y estadísticas históricas.
- **Editor Táctico**: Interfaz visual para arrastrar jugadores y cambiar la mentalidad/presión antes de un partido.

## Fase 16. Ciclo de Vida de Carrera y Persistencia

### Objetivo
Convertir la simulación en un juego de larga duración.

### Funcionalidades
- **Guardado de Partida**: Persistencia del estado de la liga en MySQL.
- **Mercado de Fichajes**: Sistema básico de compra/venta basado en valor de mercado (stats + edad).
- **Progresión**: Evolución (o declive) de atributos de jugadores entre temporadas.

---

## Próximos Pasos Inmediatos
1. Definir los contratos de la API (JSON) para Equipos y Jugadores.
2. Iniciar el boilerplate del Frontend con un diseño inspirado en plataformas de scouting profesional.
3. Conectar el primer endpoint de "Simular Partido Live".
