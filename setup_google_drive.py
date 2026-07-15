"""
Script de setup para autenticar con Google Drive.

Pasos:
1. Descarga credenciales desde Google Cloud Console
2. Copia el archivo .json a config/google_credentials.json
3. Ejecuta este script: python setup_google_drive.py
4. Abre el navegador que se abre automáticamente
5. Autoriza la aplicación
6. El token se guarda en config/google_token.json
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.cloud.google_drive_client import prueba_conexion, _obtener_credentials


def main():
    print()
    print("=" * 70)
    print("SETUP: AUTENTICACIÓN CON GOOGLE DRIVE")
    print("=" * 70)
    print()

    # Verificar que google_credentials.json existe
    creds_path = Path("config/google_credentials.json")
    if not creds_path.exists():
        print("❌ ERROR: No encontré config/google_credentials.json")
        print()
        print("Pasos para obtenerlo:")
        print("1. Ve a https://console.cloud.google.com/")
        print("2. Crea un proyecto nuevo")
        print("3. Habilita 'Google Drive API'")
        print("4. Ve a 'Credenciales' → 'Crear credencial' → 'OAuth 2.0 - Aplicación de escritorio'")
        print("5. Descarga el JSON y guárdalo como: config/google_credentials.json")
        print()
        return False

    print(f"✓ Encontrado: {creds_path}")
    print()
    print("Iniciando autenticación...")
    print("Se abrirá tu navegador en 3 segundos...")
    print()

    try:
        creds = _obtener_credentials()
        print()
        print("✓ Autenticación completada exitosamente")
        print(f"✓ Token guardado en: config/google_token.json")
        print()

        # Prueba de conexión
        if prueba_conexion():
            print("=" * 70)
            print("SETUP COMPLETADO")
            print("=" * 70)
            print()
            print("Ahora puedes ejecutar el sistema normalmente:")
            print("  python test_fase4.py")
            print()
            return True
        else:
            print("⚠ Conexión fallida. Revisa los permisos en Google Drive.")
            return False

    except Exception as e:
        print(f"❌ Error durante autenticación: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)