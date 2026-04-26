"""Entidad de dominio para el Entrenador."""

from __future__ import annotations

from dataclasses import dataclass
from motor_futbol.dominio.tactica import Tactica
from motor_futbol.dominio.enums import MentalidadTactica, EstiloPresion
from motor_futbol.dominio.validaciones import (
    validar_cadena_no_vacia,
    validar_entero_en_rango,
)

@dataclass(frozen=True, slots=True)
class Entrenador:
    """Representa a un entrenador con sus preferencias y estilo."""

    id: int
    nombre: str
    formacion_favorita: str
    posesion: int  # 0-100
    contraataque_rapido: int
    contraataque_largo: int
    por_las_bandas: int
    balon_largo: int
    edad: int | None = None
    nacionalidad: str | None = None

    def __post_init__(self) -> None:
        validar_cadena_no_vacia("nombre", self.nombre)
        validar_entero_en_rango("posesion", self.posesion, minimo=0, maximo=100)
        validar_entero_en_rango("contraataque_rapido", self.contraataque_rapido, minimo=0, maximo=100)
        validar_entero_en_rango("contraataque_largo", self.contraataque_largo, minimo=0, maximo=100)
        validar_entero_en_rango("por_las_bandas", self.por_las_bandas, minimo=0, maximo=100)
        validar_entero_en_rango("balon_largo", self.balon_largo, minimo=0, maximo=100)

    def preparar_tactica(self) -> Tactica:
        """
        Genera una Tactica basada en el perfil del entrenador.
        Esta es la primera version de la 'IA' del entrenador.
        """
        # Determinar mentalidad principal
        if self.posesion > 70:
            mentalidad = MentalidadTactica.OFENSIVA
            ritmo = 40  # Mas pausado
            altura = 70
        elif self.contraataque_rapido > 70:
            mentalidad = MentalidadTactica.MUY_OFENSIVA
            ritmo = 85
            altura = 40
        else:
            mentalidad = MentalidadTactica.EQUILIBRADA
            ritmo = 50
            altura = 50

        # Ajustar presion segun agresividad de contraataque
        if self.contraataque_rapido > 60:
            presion = EstiloPresion.ALTA
        elif self.posesion > 60:
            presion = EstiloPresion.MEDIA
        else:
            presion = EstiloPresion.BAJA

        return Tactica(
            nombre=f"Plan de {self.nombre}",
            formacion=self.formacion_favorita,
            mentalidad=mentalidad,
            presion=presion,
            ritmo=ritmo,
            altura_bloque=altura,
            anchura=60 if self.por_las_bandas > 60 else 45,
            agresividad=max(self.contraataque_rapido, self.balon_largo)
        )
