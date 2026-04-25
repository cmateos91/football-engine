"""Tests de la capa espacial."""

from motor_futbol.dominio.espacial import Coordenada, EstadoEspacialPartido, ZonaCampo


def test_coordenada_zonas_3x3() -> None:
    assert Coordenada(10, 10).zona is ZonaCampo.DEFENSA_IZQ
    assert Coordenada(50, 50).zona is ZonaCampo.MEDIO_CNT
    assert Coordenada(80, 90).zona is ZonaCampo.ATAQUE_DER
    assert Coordenada(10, 60).zona is ZonaCampo.DEFENSA_CNT
    assert Coordenada(50, 10).zona is ZonaCampo.MEDIO_IZQ
    assert Coordenada(80, 60).zona is ZonaCampo.ATAQUE_CNT
    assert Coordenada(50, 90).zona is ZonaCampo.MEDIO_DER


def test_estado_espacial_mover() -> None:
    estado = EstadoEspacialPartido()
    estado.mover_a(Coordenada(80.0, 30.0))

    assert estado.posicion_balon.x == 80.0
    assert estado.posicion_balon.zona is ZonaCampo.ATAQUE_IZQ

    estado.mover_a(Coordenada(20.0, 50.0))
    assert estado.posicion_balon.zona is ZonaCampo.DEFENSA_CNT
    assert estado.progreciones_fallidas == 1


def test_estado_espacial_posesion() -> None:
    estado = EstadoEspacialPartido()
    estado.posesion_cambia(1)
    assert estado.posesion_equipo_id == 1

    estado.posesion_cambia(2)
    assert estado.posesion_equipo_id == 2


def test_estado_espacial_tiempo_zona() -> None:
    estado = EstadoEspacialPartido()
    estado.mover_a(Coordenada(10, 50))
    estado.actualizar(1, 5.0)
    estado.mover_a(Coordenada(80, 50))
    estado.actualizar(1, 3.0)

    assert estado.tiempo_en_zona["Defensa Centro"] == 5.0
    assert estado.tiempo_en_zona["Ataque Centro"] == 3.0


def test_distancia_coordenadas() -> None:
    inicio = Coordenada(50, 50)
    final = Coordenada(80, 50)

    distancia = inicio.distancia_a(final)
    assert distancia == 30.0


def test_estado_dict_roundtrip() -> None:
    estado = EstadoEspacialPartido()
    estado.mover_a(Coordenada(75.0, 25.0))
    estado.posesion_cambia(1)
    estado.actualizar(1, 5.0)
    estado.progreciones_exitosas = 2

    datos = estado.a_dict()
    estado_copy = EstadoEspacialPartido.desde_dict(datos)

    assert estado_copy.posicion_balon.x == 75.0
    assert estado_copy.posesion_equipo_id == 1
    assert estado_copy.tiempo_en_zona["Ataque Izquierda"] == 5.0
    assert estado_copy.progreciones_exitosas == 2


def test_progresion_ofensiva() -> None:
    estado = EstadoEspacialPartido()
    estado.mover_a(Coordenada(10, 50))
    estado.mover_a(Coordenada(30, 50))
    estado.mover_a(Coordenada(70, 50))
    estado.mover_a(Coordenada(90, 50))

    assert estado.progreciones_exitosas == 1
    assert estado.progreciones_fallidas == 0


def test_todas_las_zonas() -> None:
    for z in ZonaCampo:
        estado = EstadoEspacialPartido()
        x = 15.0 if "Defensa" in z.value else 50.0 if "Medio" in z.value else 85.0
        y = 15.0 if "Izquierda" in z.value else 50.0 if "Centro" in z.value else 85.0
        estado.mover_a(Coordenada(x, y))
        assert estado.posicion_balon.zona is z, f"{z} expected but got {estado.posicion_balon.zona}"
