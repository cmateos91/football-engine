# Football Motor

Proyecto greenfield para construir un motor de simulación de partidos de fútbol con validación estadística contra datos reales de LaLiga.

## Convenciones iniciales

- El código se escribe en español siempre que no choque con convenciones del ecosistema Python.
- La complejidad se añade por capas.
- Todo cambio debe pasar lint, type-check y tests.
- El realismo se valida con evidencia, no con intuición.

## Estructura inicial

```text
docs/
src/motor_futbol/
tests/
scripts/
data_samples/
```

## Preparación del entorno

```bash
./scripts/preparar_entorno.sh
```

## Verificación de calidad

```bash
./scripts/verificar_calidad.sh
```

## Configuración

Parte de la configuración se carga desde `.env`. Hay una plantilla mínima en `.env.example`.

