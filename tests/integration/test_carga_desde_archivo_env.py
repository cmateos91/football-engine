from __future__ import annotations

from pathlib import Path

from motor_futbol.compartido.configuracion import cargar_configuracion


def test_carga_configuracion_desde_archivo_env(tmp_path: Path) -> None:
    archivo_entorno = tmp_path / ".env"
    archivo_entorno.write_text(
        "\n".join(
            [
                "ENTORNO=integracion",
                "NIVEL_LOG=warning",
                "SEMILLA_POR_DEFECTO=31415",
                "URL_BD=mysql+pymysql://usuario:clave@localhost/futbol",
            ]
        ),
        encoding="utf-8",
    )

    configuracion = cargar_configuracion(ruta_env=archivo_entorno)

    assert configuracion.entorno == "integracion"
    assert configuracion.nivel_log == "WARNING"
    assert configuracion.semilla_por_defecto == 31415
    assert configuracion.url_bd == "mysql+pymysql://usuario:clave@localhost/futbol"
    assert configuracion.base_de_datos_configurada is True
