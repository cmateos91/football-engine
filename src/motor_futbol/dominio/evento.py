"""Evento generico del partido."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from motor_futbol.dominio.enums import TipoEventoPartido
from motor_futbol.dominio.validaciones import (
    normalizar_cadena_opcional,
    obtener_cadena,
    obtener_cadena_opcional,
    obtener_entero,
    obtener_entero_opcional,
    obtener_mapeo_opcional,
    validar_cadena_no_vacia,
    validar_entero_en_rango,
    validar_identificador,
)

ValorMetadato = str | int | float | bool | None

TIPOS_CON_EQUIPO = frozenset(
    {
        TipoEventoPartido.GOL,
        TipoEventoPartido.TIRO,
        TipoEventoPartido.PASE,
        TipoEventoPartido.FALTA,
        TipoEventoPartido.TARJETA_AMARILLA,
        TipoEventoPartido.TARJETA_ROJA,
        TipoEventoPartido.CORNER,
        TipoEventoPartido.PARADA,
        TipoEventoPartido.SUSTITUCION,
    }
)
TIPOS_CON_JUGADOR_PRINCIPAL = frozenset(
    {
        TipoEventoPartido.GOL,
        TipoEventoPartido.TIRO,
        TipoEventoPartido.PASE,
        TipoEventoPartido.FALTA,
        TipoEventoPartido.TARJETA_AMARILLA,
        TipoEventoPartido.TARJETA_ROJA,
        TipoEventoPartido.PARADA,
        TipoEventoPartido.SUSTITUCION,
    }
)


@dataclass(frozen=True, slots=True)
class EventoPartido:
    """Unidad de historial de lo ocurrido durante un partido."""

    tipo: TipoEventoPartido
    minuto: int
    equipo_id: int | None = None
    jugador_principal_id: int | None = None
    jugador_secundario_id: int | None = None
    descripcion: str | None = None
    metadatos: Mapping[str, ValorMetadato] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validar_entero_en_rango("minuto", self.minuto, minimo=0, maximo=130)

        if self.equipo_id is not None:
            validar_identificador("equipo_id", self.equipo_id)
        if self.jugador_principal_id is not None:
            validar_identificador("jugador_principal_id", self.jugador_principal_id)
        if self.jugador_secundario_id is not None:
            validar_identificador("jugador_secundario_id", self.jugador_secundario_id)

        object.__setattr__(self, "descripcion", normalizar_cadena_opcional(self.descripcion))
        object.__setattr__(self, "metadatos", dict(self.metadatos))

        if self.tipo in TIPOS_CON_EQUIPO and self.equipo_id is None:
            raise ValueError(f"El evento {self.tipo.value} requiere equipo_id.")
        if self.tipo in TIPOS_CON_JUGADOR_PRINCIPAL and self.jugador_principal_id is None:
            raise ValueError(f"El evento {self.tipo.value} requiere jugador_principal_id.")
        if self.tipo is TipoEventoPartido.SUSTITUCION and self.jugador_secundario_id is None:
            raise ValueError("El evento Sustitucion requiere jugador_secundario_id.")

        for clave, valor in self.metadatos.items():
            validar_cadena_no_vacia("clave de metadatos", clave)
            if not isinstance(valor, str | int | float | bool) and valor is not None:
                raise TypeError("Los metadatos solo admiten tipos primitivos serializables.")

    def a_dict(self) -> dict[str, object]:
        return {
            "tipo": self.tipo.value,
            "minuto": self.minuto,
            "equipo_id": self.equipo_id,
            "jugador_principal_id": self.jugador_principal_id,
            "jugador_secundario_id": self.jugador_secundario_id,
            "descripcion": self.descripcion,
            "metadatos": dict(self.metadatos),
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, object]) -> EventoPartido:
        metadatos = obtener_mapeo_opcional(datos, "metadatos") or {}
        return cls(
            tipo=TipoEventoPartido.desde_cadena(obtener_cadena(datos, "tipo")),
            minuto=obtener_entero(datos, "minuto"),
            equipo_id=obtener_entero_opcional(datos, "equipo_id"),
            jugador_principal_id=obtener_entero_opcional(datos, "jugador_principal_id"),
            jugador_secundario_id=obtener_entero_opcional(datos, "jugador_secundario_id"),
            descripcion=obtener_cadena_opcional(datos, "descripcion"),
            metadatos={
                str(clave): valor
                for clave, valor in metadatos.items()
                if isinstance(valor, str | int | float | bool) or valor is None
            },
        )
