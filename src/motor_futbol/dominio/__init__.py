"""Modulo para entidades y reglas del dominio."""

from motor_futbol.dominio.alineacion import Alineacion
from motor_futbol.dominio.atributos import AtributosJugador
from motor_futbol.dominio.contexto_partido import ContextoPartido
from motor_futbol.dominio.enums import (
    EstadoFisico,
    EstiloPresion,
    FasePartido,
    MentalidadTactica,
    PieDominante,
    PosicionJugador,
    RolTactico,
    TipoEventoPartido,
)
from motor_futbol.dominio.equipo import Equipo
from motor_futbol.dominio.espacial import Coordenada, EstadoEspacialPartido, ZonaCampo
from motor_futbol.dominio.estado_partido import EstadoPartido
from motor_futbol.dominio.evento import EventoPartido
from motor_futbol.dominio.jugador import Jugador
from motor_futbol.dominio.tactica import Tactica

__all__ = [
    "Alineacion",
    "AtributosJugador",
    "ContextoPartido",
    "Coordenada",
    "Equipo",
    "EstadoEspacialPartido",
    "EstadoFisico",
    "EstadoPartido",
    "EstiloPresion",
    "EventoPartido",
    "FasePartido",
    "Jugador",
    "MentalidadTactica",
    "PieDominante",
    "PosicionJugador",
    "RolTactico",
    "Tactica",
    "TipoEventoPartido",
    "ZonaCampo",
]
