"""Utilidades de validacion y carga tipada del dominio."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast


def validar_identificador(nombre: str, valor: int) -> None:
    _validar_entero(nombre=nombre, valor=valor)
    if valor <= 0:
        raise ValueError(f"{nombre} debe ser un entero positivo.")


def validar_cadena_no_vacia(nombre: str, valor: str) -> None:
    if not isinstance(valor, str):
        raise TypeError(f"{nombre} debe ser una cadena.")
    if valor.strip() == "":
        raise ValueError(f"{nombre} no puede estar vacio.")


def validar_entero_en_rango(nombre: str, valor: int, *, minimo: int, maximo: int) -> None:
    _validar_entero(nombre=nombre, valor=valor)
    if valor < minimo or valor > maximo:
        raise ValueError(f"{nombre} debe estar entre {minimo} y {maximo}.")


def validar_entero_opcional_en_rango(
    nombre: str, valor: int | None, *, minimo: int, maximo: int
) -> None:
    if valor is None:
        return
    validar_entero_en_rango(nombre=nombre, valor=valor, minimo=minimo, maximo=maximo)


def validar_secuencia_sin_duplicados(nombre: str, valores: Sequence[int]) -> None:
    if len(set(valores)) != len(valores):
        raise ValueError(f"{nombre} no puede contener elementos duplicados.")


def normalizar_cadena_opcional(valor: str | None) -> str | None:
    if valor is None:
        return None
    valor_limpio = valor.strip()
    return valor_limpio or None


def obtener_cadena(datos: Mapping[str, object], clave: str) -> str:
    valor = datos.get(clave)
    if not isinstance(valor, str):
        raise TypeError(f"{clave} debe ser una cadena.")
    return valor


def obtener_cadena_opcional(datos: Mapping[str, object], clave: str) -> str | None:
    valor = datos.get(clave)
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise TypeError(f"{clave} debe ser una cadena o None.")
    return valor


def obtener_entero(datos: Mapping[str, object], clave: str) -> int:
    valor = datos.get(clave)
    _validar_entero(nombre=clave, valor=valor)
    return cast(int, valor)


def obtener_entero_opcional(datos: Mapping[str, object], clave: str) -> int | None:
    valor = datos.get(clave)
    if valor is None:
        return None
    _validar_entero(nombre=clave, valor=valor)
    return cast(int, valor)


def obtener_lista(datos: Mapping[str, object], clave: str) -> Sequence[object]:
    valor = datos.get(clave)
    if not isinstance(valor, list):
        raise TypeError(f"{clave} debe ser una lista.")
    return valor


def obtener_lista_de_mapeos(
    datos: Mapping[str, object], clave: str
) -> tuple[Mapping[str, object], ...]:
    lista = obtener_lista(datos, clave)
    resultado: list[Mapping[str, object]] = []
    for indice, valor in enumerate(lista):
        if not isinstance(valor, Mapping):
            raise TypeError(f"{clave}[{indice}] debe ser un mapeo.")
        resultado.append(valor)
    return tuple(resultado)


def obtener_mapeo(datos: Mapping[str, object], clave: str) -> Mapping[str, object]:
    valor = datos.get(clave)
    if not isinstance(valor, Mapping):
        raise TypeError(f"{clave} debe ser un mapeo.")
    return valor


def obtener_mapeo_opcional(datos: Mapping[str, object], clave: str) -> Mapping[str, object] | None:
    valor = datos.get(clave)
    if valor is None:
        return None
    if not isinstance(valor, Mapping):
        raise TypeError(f"{clave} debe ser un mapeo o None.")
    return valor


def _validar_entero(nombre: str, valor: object) -> None:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(f"{nombre} debe ser un entero.")
