"""Enumeraciones base del dominio."""

from __future__ import annotations

from enum import StrEnum


def _normalizar_token(valor: str) -> str:
    return valor.strip().casefold().replace("_", " ").replace("-", " ")


class PosicionJugador(StrEnum):
    """Posiciones soportadas por el dominio."""

    PORTERO = "Portero"
    CENTRAL = "Central"
    LATERAL = "Lateral"
    MEDIOCENTRO = "Mediocentro"
    MEDIAPUNTA = "Mediapunta"
    EXTREMO = "Extremo"
    DELANTERO = "Delantero"
    DESCONOCIDA = "Unknown"

    @classmethod
    def desde_cadena(cls, valor: str) -> PosicionJugador:
        token = _normalizar_token(valor)
        mapa = {
            "portero": cls.PORTERO,
            "goalkeeper": cls.PORTERO,
            "gk": cls.PORTERO,
            "central": cls.CENTRAL,
            "defensa central": cls.CENTRAL,
            "lateral": cls.LATERAL,
            "mediocentro": cls.MEDIOCENTRO,
            "medio centro": cls.MEDIOCENTRO,
            "mediapunta": cls.MEDIAPUNTA,
            "media punta": cls.MEDIAPUNTA,
            "extremo": cls.EXTREMO,
            "delantero": cls.DELANTERO,
            "unknown": cls.DESCONOCIDA,
            "desconocida": cls.DESCONOCIDA,
        }
        if token not in mapa:
            raise ValueError(f"Posicion de jugador no soportada: {valor!r}.")
        return mapa[token]


class PieDominante(StrEnum):
    """Pie dominante del jugador."""

    DERECHO = "Derecho"
    IZQUIERDO = "Izquierdo"
    AMBIDIESTRO = "Ambidiestro"

    @classmethod
    def desde_cadena(cls, valor: str) -> PieDominante:
        token = _normalizar_token(valor)
        mapa = {
            "derecho": cls.DERECHO,
            "right": cls.DERECHO,
            "izquierdo": cls.IZQUIERDO,
            "left": cls.IZQUIERDO,
            "ambidiestro": cls.AMBIDIESTRO,
            "ambos": cls.AMBIDIESTRO,
            "both": cls.AMBIDIESTRO,
        }
        if token not in mapa:
            raise ValueError(f"Pie dominante no soportado: {valor!r}.")
        return mapa[token]


class EstadoFisico(StrEnum):
    """Estado fisico disponible para el jugador."""

    DISPONIBLE = "Disponible"
    CANSADO = "Cansado"
    TOCADO = "Tocado"
    LESIONADO = "Lesionado"
    SANCIONADO = "Sancionado"

    @classmethod
    def desde_cadena(cls, valor: str) -> EstadoFisico:
        token = _normalizar_token(valor)
        mapa = {estado.value.casefold(): estado for estado in cls}
        if token not in mapa:
            raise ValueError(f"Estado fisico no soportado: {valor!r}.")
        return mapa[token]


class RolTactico(StrEnum):
    """Roles tacticos de alto nivel."""

    PORTERO = "Portero"
    DEFENSA_CIERRE = "Defensa cierre"
    DEFENSA_LATERAL = "Defensa lateral"
    MEDIO_RECUPERADOR = "Medio recuperador"
    MEDIO_ORGANIZADOR = "Medio organizador"
    MEDIO_LLEGADOR = "Medio llegador"
    CREADOR = "Creador"
    EXTREMO_DESEQUILIBRANTE = "Extremo desequilibrante"
    DELANTERO_REFERENCIA = "Delantero referencia"
    DELANTERO_MOVIL = "Delantero movil"

    @classmethod
    def desde_cadena(cls, valor: str) -> RolTactico:
        token = _normalizar_token(valor)
        for rol in cls:
            if _normalizar_token(rol.value) == token:
                return rol
        raise ValueError(f"Rol tactico no soportado: {valor!r}.")


class MentalidadTactica(StrEnum):
    """Mentalidad general de la tactica."""

    DEFENSIVA = "Defensiva"
    EQUILIBRADA = "Equilibrada"
    OFENSIVA = "Ofensiva"

    @classmethod
    def desde_cadena(cls, valor: str) -> MentalidadTactica:
        token = _normalizar_token(valor)
        for mentalidad in cls:
            if mentalidad.value.casefold() == token:
                return mentalidad
        raise ValueError(f"Mentalidad tactica no soportada: {valor!r}.")


class EstiloPresion(StrEnum):
    """Altura o intensidad general de presion."""

    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"

    @classmethod
    def desde_cadena(cls, valor: str) -> EstiloPresion:
        token = _normalizar_token(valor)
        for estilo in cls:
            if estilo.value.casefold() == token:
                return estilo
        raise ValueError(f"Estilo de presion no soportado: {valor!r}.")


class FasePartido(StrEnum):
    """Fases del estado del partido."""

    NO_INICIADO = "No iniciado"
    PRIMER_TIEMPO = "Primer tiempo"
    DESCANSO = "Descanso"
    SEGUNDO_TIEMPO = "Segundo tiempo"
    PRORROGA = "Prorroga"
    TANDA_PENALES = "Tanda de penales"
    FINALIZADO = "Finalizado"

    @classmethod
    def desde_cadena(cls, valor: str) -> FasePartido:
        token = _normalizar_token(valor)
        for fase in cls:
            if _normalizar_token(fase.value) == token:
                return fase
        raise ValueError(f"Fase de partido no soportada: {valor!r}.")


class TipoEventoPartido(StrEnum):
    """Tipos de eventos soportados por el historial del partido."""

    INICIO = "Inicio"
    DESCANSO = "Descanso"
    FINAL = "Final"
    GOL = "Gol"
    TIRO = "Tiro"
    PASE = "Pase"
    FALTA = "Falta"
    TARJETA_AMARILLA = "Tarjeta Amarilla"
    TARJETA_ROJA = "Tarjeta Roja"
    CORNER = "Corner"
    PARADA = "Parada"
    SUSTITUCION = "Sustitucion"
    CONTRAATAQUE = "Contraataque"
    TIRO_LIBRE = "Tiro Libre"
    PENALTI = "Penalti"
    DUELO_AEREO = "Duelo Aereo"
    REBOTE = "Rebote"
    CENTRO = "Centro"
    BLOQUEO = "Bloqueo"
    RECUPERACION = "Recuperacion"

    @classmethod
    def desde_cadena(cls, valor: str) -> TipoEventoPartido:
        token = _normalizar_token(valor)
        for tipo in cls:
            if _normalizar_token(tipo.value) == token:
                return tipo
        raise ValueError(f"Tipo de evento no soportado: {valor!r}.")
