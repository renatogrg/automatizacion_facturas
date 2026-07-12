"""
Punto de entrada del sistema.
Arranca el icono de bandeja (encendido/apagado) y el watcher de la carpeta ENTRADA_FACTURA.
"""

from src.tray.tray_icon import iniciar_icono_bandeja
from src.watcher import iniciar_watcher
from src.utils.config_loader import cargar_settings


def main():
    settings = cargar_settings()
    iniciar_watcher(settings)
    iniciar_icono_bandeja(settings)


if __name__ == "__main__":
    main()
