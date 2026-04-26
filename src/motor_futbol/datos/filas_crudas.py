"""Filas crudas obtenidas directamente desde football_engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import fields as dataclass_fields

from motor_futbol.dominio.atributos import AtributosJugador
from motor_futbol.dominio.validaciones import (
    normalizar_cadena_opcional,
    obtener_cadena,
    obtener_cadena_opcional,
    obtener_entero,
    obtener_entero_opcional,
    validar_cadena_no_vacia,
    validar_entero_en_rango,
    validar_entero_opcional_en_rango,
    validar_identificador,
)


@dataclass(frozen=True, slots=True)
class FilaEquipoCruda:
    """Representa una fila cruda de la tabla Equipo."""

    id: int
    nombre: str

    def __post_init__(self) -> None:
        validar_identificador("id", self.id)
        validar_cadena_no_vacia("nombre", self.nombre)
        object.__setattr__(self, "nombre", self.nombre.strip())

    @classmethod
    def desde_mapping(cls, datos: Mapping[str, object]) -> FilaEquipoCruda:
        return cls(
            id=obtener_entero(datos, "id"),
            nombre=obtener_cadena(datos, "nombre"),
        )

    def a_dict(self) -> dict[str, object]:
        return {"id": self.id, "nombre": self.nombre}


@dataclass(frozen=True, slots=True)
class FilaJugadorCruda:
    """Representa una fila cruda de la tabla Jugador."""

    id: int
    nombre: str
    posicion: str
    overall: int
    equipo_id: int
    aceleracion: int
    agresividad: int
    cabeza: int
    reflejos: int
    regate: int
    resistencia: int
    salto: int
    tackles: int
    velocidad: int
    alcance: int
    atrape: int
    awareness_defensivo: int
    awareness_ofensivo: int
    awareness_portero: int
    contacto_fisico: int
    control_balon: int
    efecto: int
    engagement_defensivo: int
    equilibrio: int
    finalizacion: int
    lanzamiento_falta: int
    pase_bajo: int
    pase_elevado: int
    posesion_cerrada: int
    potencia_tiro: int
    rechazo: int
    altura: int | None = None
    edad: int | None = None
    nacionalidad: str | None = None
    peso: int | None = None
    pie_fuerte: str | None = None

    def __post_init__(self) -> None:
        validar_identificador("id", self.id)
        validar_identificador("equipo_id", self.equipo_id)
        validar_cadena_no_vacia("nombre", self.nombre)
        validar_cadena_no_vacia("posicion", self.posicion)
        validar_entero_en_rango("overall", self.overall, minimo=0, maximo=100)
        validar_entero_opcional_en_rango("edad", self.edad, minimo=14, maximo=60)
        validar_entero_opcional_en_rango("altura", self.altura, minimo=130, maximo=230)
        validar_entero_opcional_en_rango("peso", self.peso, minimo=40, maximo=130)

        for nombre in AtributosJugador.nombres_campos():
            valor = getattr(self, nombre)
            validar_entero_en_rango(nombre, valor, minimo=0, maximo=100)

        object.__setattr__(self, "nombre", self.nombre.strip())
        object.__setattr__(self, "posicion", self.posicion.strip())
        object.__setattr__(self, "nacionalidad", normalizar_cadena_opcional(self.nacionalidad))
        object.__setattr__(self, "pie_fuerte", normalizar_cadena_opcional(self.pie_fuerte))

    @classmethod
    def desde_mapping(cls, datos: Mapping[str, object]) -> FilaJugadorCruda:
        return cls(
            id=obtener_entero(datos, "id"),
            nombre=obtener_cadena(datos, "nombre"),
            posicion=obtener_cadena(datos, "posicion"),
            overall=obtener_entero(datos, "overall"),
            equipo_id=_obtener_entero_con_alias(datos, "equipoId", "equipo_id"),
            aceleracion=obtener_entero(datos, "aceleracion"),
            agresividad=obtener_entero(datos, "agresividad"),
            cabeza=obtener_entero(datos, "cabeza"),
            reflejos=obtener_entero(datos, "reflejos"),
            regate=obtener_entero(datos, "regate"),
            resistencia=obtener_entero(datos, "resistencia"),
            salto=obtener_entero(datos, "salto"),
            tackles=obtener_entero(datos, "tackles"),
            velocidad=obtener_entero(datos, "velocidad"),
            alcance=obtener_entero(datos, "alcance"),
            atrape=obtener_entero(datos, "atrape"),
            awareness_defensivo=obtener_entero(datos, "awareness_defensivo"),
            awareness_ofensivo=obtener_entero(datos, "awareness_ofensivo"),
            awareness_portero=obtener_entero(datos, "awareness_portero"),
            contacto_fisico=obtener_entero(datos, "contacto_fisico"),
            control_balon=obtener_entero(datos, "control_balon"),
            efecto=obtener_entero(datos, "efecto"),
            engagement_defensivo=obtener_entero(datos, "engagement_defensivo"),
            equilibrio=obtener_entero(datos, "equilibrio"),
            finalizacion=obtener_entero(datos, "finalizacion"),
            lanzamiento_falta=obtener_entero(datos, "lanzamiento_falta"),
            pase_bajo=obtener_entero(datos, "pase_bajo"),
            pase_elevado=obtener_entero(datos, "pase_elevado"),
            posesion_cerrada=obtener_entero(datos, "posesion_cerrada"),
            potencia_tiro=obtener_entero(datos, "potencia_tiro"),
            rechazo=obtener_entero(datos, "rechazo"),
            altura=obtener_entero_opcional(datos, "altura"),
            edad=obtener_entero_opcional(datos, "edad"),
            nacionalidad=obtener_cadena_opcional(datos, "nacionalidad"),
            peso=obtener_entero_opcional(datos, "peso"),
            pie_fuerte=obtener_cadena_opcional(datos, "pie_fuerte"),
        )

    def a_dict(self) -> dict[str, object]:
        datos = {campo.name: getattr(self, campo.name) for campo in dataclass_fields(self)}
        datos["equipoId"] = datos.pop("equipo_id")
        return datos


def _obtener_entero_con_alias(datos: Mapping[str, object], *claves: str) -> int:
    for clave in claves:
        if clave in datos:
            return obtener_entero(datos, clave)
    claves_texto = ", ".join(claves)
    raise KeyError(f"No se encontro ninguna de las claves esperadas: {claves_texto}.")

@dataclass(frozen=True, slots=True)
class FilaEntrenadorCruda:
    """Representa una fila cruda de la tabla Entrenador."""

    id: int
    nombre: str
    formacion: str
    posesion: int
    contraataque_rapido: int
    contraataque_largo: int
    por_las_bandas: int
    balon_largo: int
    equipo_nombre: str | None = None
    nacionalidad: str | None = None
    tipo: str | None = None
    edad: int | None = None

    def __post_init__(self) -> None:
        validar_identificador("id", self.id)
        validar_cadena_no_vacia("nombre", self.nombre)
        validar_entero_en_rango("posesion", self.posesion, minimo=0, maximo=100)
        validar_entero_en_rango("contraataque_rapido", self.contraataque_rapido, minimo=0, maximo=100)
        validar_entero_en_rango("contraataque_largo", self.contraataque_largo, minimo=0, maximo=100)
        validar_entero_en_rango("por_las_bandas", self.por_las_bandas, minimo=0, maximo=100)
        validar_entero_en_rango("balon_largo", self.balon_largo, minimo=0, maximo=100)

    @classmethod
    def desde_mapping(cls, datos: Mapping[str, object]) -> FilaEntrenadorCruda:
        return cls(
            id=obtener_entero(datos, "id_entrenador"),
            nombre=obtener_cadena(datos, "nombre"),
            formacion=obtener_cadena(datos, "formacion"),
            posesion=obtener_entero(datos, "posesion"),
            contraataque_rapido=obtener_entero(datos, "contraataque_rapido"),
            contraataque_largo=obtener_entero(datos, "contraataque_largo"),
            por_las_bandas=obtener_entero(datos, "por_las_bandas"),
            balon_largo=obtener_entero(datos, "balon_largo"),
            equipo_nombre=obtener_cadena_opcional(datos, "equipo"),
            nacionalidad=obtener_cadena_opcional(datos, "nacionalidad"),
            tipo=obtener_cadena_opcional(datos, "tipo"),
            edad=obtener_entero_opcional(datos, "edad"),
        )

    def a_dict(self) -> dict[str, object]:
        return {campo.name: getattr(self, campo.name) for campo in dataclass_fields(self)}
