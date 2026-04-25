"""Inventario del esquema real de la base de datos."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy import text

from motor_futbol.compartido.configuracion import Configuracion
from motor_futbol.datos.conexion_bd import crear_motor_bd


@dataclass(frozen=True, slots=True)
class ColumnaTabla:
    """Metadatos minimos de una columna del esquema."""

    tabla: str
    nombre: str
    tipo_sql: str
    admite_nulos: bool
    clave: str | None
    valor_por_defecto: str | None

    @classmethod
    def desde_mapping(cls, datos: Mapping[str, object]) -> ColumnaTabla:
        tabla = str(datos["tabla"])
        nombre = str(datos["columna"])
        tipo_sql = str(datos["tipo_sql"])
        admite_nulos = str(datos["admite_nulos"]) == "YES"
        clave = str(datos["clave"]) if datos["clave"] not in (None, "") else None
        valor_por_defecto = (
            str(datos["valor_por_defecto"]) if datos["valor_por_defecto"] is not None else None
        )
        return cls(
            tabla=tabla,
            nombre=nombre,
            tipo_sql=tipo_sql,
            admite_nulos=admite_nulos,
            clave=clave,
            valor_por_defecto=valor_por_defecto,
        )


@dataclass(frozen=True, slots=True)
class TablaEsquema:
    """Representa una tabla y sus columnas."""

    nombre: str
    columnas: tuple[ColumnaTabla, ...]

    @property
    def nombres_columnas(self) -> tuple[str, ...]:
        return tuple(columna.nombre for columna in self.columnas)

    def obtener_columna(self, nombre_columna: str) -> ColumnaTabla:
        for columna in self.columnas:
            if columna.nombre == nombre_columna:
                return columna
        raise KeyError(f"La tabla {self.nombre} no contiene la columna {nombre_columna}.")


@dataclass(frozen=True, slots=True)
class InventarioEsquema:
    """Describe el esquema visible de la BD activa."""

    nombre_bd: str
    tablas: tuple[TablaEsquema, ...]

    def obtener_tabla(self, nombre_tabla: str) -> TablaEsquema:
        for tabla in self.tablas:
            if tabla.nombre == nombre_tabla:
                return tabla
        raise KeyError(f"No existe la tabla {nombre_tabla} en la base de datos {self.nombre_bd}.")


def inspeccionar_esquema_bd(configuracion: Configuracion) -> InventarioEsquema:
    """Lee el esquema activo desde information_schema."""

    motor = crear_motor_bd(configuracion)
    consulta = text(
        """
        SELECT
          TABLE_NAME AS tabla,
          COLUMN_NAME AS columna,
          DATA_TYPE AS tipo_sql,
          IS_NULLABLE AS admite_nulos,
          COLUMN_KEY AS clave,
          COLUMN_DEFAULT AS valor_por_defecto
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
    )

    with motor.connect() as conexion:
        nombre_bd_obj = conexion.execute(text("SELECT DATABASE()")).scalar_one()
        filas = tuple(dict(fila) for fila in conexion.execute(consulta).mappings())

    if not isinstance(nombre_bd_obj, str) or nombre_bd_obj.strip() == "":
        raise ValueError("No se pudo obtener el nombre de la base de datos activa.")

    columnas = tuple(ColumnaTabla.desde_mapping(fila) for fila in filas)
    agrupadas: defaultdict[str, list[ColumnaTabla]] = defaultdict(list)
    for columna in columnas:
        agrupadas[columna.tabla].append(columna)

    tablas = tuple(
        TablaEsquema(nombre=nombre, columnas=tuple(columnas_tabla))
        for nombre, columnas_tabla in sorted(agrupadas.items())
    )
    return InventarioEsquema(nombre_bd=nombre_bd_obj, tablas=tablas)
