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

El proyecto se divide en 8 grandes fases. Cada fase debe dejar un sistema usable, testeado y medible antes de pasar a la siguiente.

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

## Fase 8. Capa espacial opcional

### Objetivo

Evaluar si merece la pena introducir una capa espacial simplificada para mejorar realismo en ciertos eventos.

### Importante

Esta fase es opcional. Solo se abre si hay evidencia de que el motor actual falla en problemas que no pueden resolverse con un modelo de eventos/contexto.

### Casos que sí justificarían esta fase

- mala modelización sistemática de centros;
- mala relación entre posesión territorial y producción ofensiva;
- comportamientos irreales en presión alta o bloque bajo;
- reparto deficiente de tiros por zonas.

### Casos que no la justifican

- ganas de hacer algo más complejo;
- sensación subjetiva de "sería más realista";
- problemas que realmente son de calibración y no de representación.

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

## Orden de construcción inmediato

### Milestone 0

Montar el repositorio Python y la infraestructura de calidad.

### Milestone 1

Definir el dominio y conectar la BD MySQL.

### Milestone 2

Simular partidos baseline reproducibles y guardar salida estructurada.

### Milestone 3

Construir la primera suite de validación contra estadísticas reales de LaLiga.

### Milestone 4

Introducir la primera capa real de atributos de jugador y medir impacto.

## Riesgos principales

1. Usar demasiados stats demasiado pronto.
   Riesgo: sobreajuste, ruido y un motor imposible de calibrar.

2. Diseñar un motor hipergranular sin baseline estable.
   Riesgo: mucha complejidad y poca capacidad de validación.

3. Confundir realismo narrativo con realismo estadístico.
   Riesgo: partidos "bonitos" pero irreales en volumen y distribución.

4. Depender demasiado de una sola temporada o una sola fuente.
   Riesgo: sesgo de calibración.

5. No separar datos crudos, features derivadas y parámetros calibrados.
   Riesgo: caos técnico y poca trazabilidad.

## Definición de éxito de la primera etapa del proyecto

La primera etapa estará bien hecha si conseguimos todo esto:

- cargar equipos y jugadores reales desde MySQL;
- simular partidos reproducibles;
- ejecutar miles de simulaciones;
- comparar sus resultados con estadísticas reales de LaLiga;
- detectar automáticamente cuándo el motor se aleja de la realidad;
- tener una base lo bastante limpia como para añadir complejidad sin romperlo todo.

## Siguiente documento recomendado

Después de este roadmap, el siguiente documento a crear debe ser:

`docs/ARCHITECTURE.md`

y debe concretar:

- módulos exactos del código;
- contratos entre capas;
- formato de eventos;
- política de seeds;
- estrategia de configuración;
- plan de importación desde MySQL.
