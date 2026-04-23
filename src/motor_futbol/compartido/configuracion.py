"""Carga tipada de configuracion del proyecto."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

ARCHIVO_ENTORNO_POR_DEFECTO = ".env"


@dataclass(frozen=True, slots=True)
class Configuracion:
    """Configuracion base necesaria para arrancar el proyecto."""

    entorno: str = "desarrollo"
    nivel_log: str = "INFO"
    semilla_por_defecto: int = 20260423
    url_bd: str | None = None

    @property
    def base_de_datos_configurada(self) -> bool:
        """Indica si existe una URL de base de datos usable."""

        return self.url_bd is not None and self.url_bd.strip() != ""


def cargar_configuracion(
    *,
    variables: Mapping[str, str] | None = None,
    ruta_env: str | Path | None = None,
) -> Configuracion:
    """Construye la configuracion a partir de variables explicitas o de entorno."""

    fuente = dict(variables) if variables is not None else _cargar_fuente_desde_entorno(ruta_env)

    return Configuracion(
        entorno=fuente.get("ENTORNO", "desarrollo").strip() or "desarrollo",
        nivel_log=fuente.get("NIVEL_LOG", "INFO").strip().upper() or "INFO",
        semilla_por_defecto=_parsear_entero(
            nombre="SEMILLA_POR_DEFECTO",
            valor=fuente.get("SEMILLA_POR_DEFECTO"),
            por_defecto=20260423,
        ),
        url_bd=_normalizar_cadena_opcional(fuente.get("URL_BD")),
    )


def _cargar_fuente_desde_entorno(ruta_env: str | Path | None) -> dict[str, str]:
    ruta_resuelta = Path(ruta_env or ARCHIVO_ENTORNO_POR_DEFECTO)
    variables_archivo = _cargar_archivo_env(ruta_resuelta)
    variables_sistema = dict(os.environ)
    return {**variables_archivo, **variables_sistema}


def _cargar_archivo_env(ruta_env: Path) -> dict[str, str]:
    if not ruta_env.exists():
        return {}

    variables = dotenv_values(ruta_env)
    return {clave: valor for clave, valor in variables.items() if valor is not None}


def _parsear_entero(nombre: str, valor: str | None, por_defecto: int) -> int:
    if valor is None or valor.strip() == "":
        return por_defecto

    try:
        return int(valor)
    except ValueError as error:
        mensaje = f"La variable {nombre} debe ser un entero valido."
        raise ValueError(mensaje) from error


def _normalizar_cadena_opcional(valor: str | None) -> str | None:
    if valor is None:
        return None

    valor_limpio = valor.strip()
    return valor_limpio or None
