"""
Punto de entrada del sistema.
Carga configuración y consorcios, e inicia el watcher.
"""

from src.watcher import iniciar_watcher
from src.utils.config_loader import cargar_settings, cargar_consorcios
from src.utils.logger import obtener_logger

logger = obtener_logger("main")


def main():
    print("\n" + "="*70)
    print("SISTEMA DE GESTIÓN AUTOMÁTICA DE FACTURAS")
    print("="*70 + "\n")
    
    try:
        # Cargar configuración
        settings = cargar_settings("config/settings.json")
        consorcios = cargar_consorcios("config/consorcios.json")
        
        print(f"✓ Configuración cargada")
        print(f"✓ Consorcios: {len(consorcios)}")
        for c in consorcios:
            print(f"  - {c['nombre']} ({c['ruc']})")
        print()
        
        # Iniciar watcher
        iniciar_watcher(settings, consorcios)
        
    except Exception as e:
        logger.error(f"Error en main: {e}")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()