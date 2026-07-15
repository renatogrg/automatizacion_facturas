# Setup de Google Drive para hipervínculos funcionales

Esta integración permite que los hipervínculos en el Excel de Drive apunten directamente a los archivos en Google Drive.

## Pasos previos

### 1. Crear proyecto en Google Cloud Console

1. Ve a https://console.cloud.google.com/
2. Crea un proyecto nuevo (ej. "Sistema Facturas")
3. Ve a "APIs y servicios" → "Biblioteca"
4. Busca "Google Drive API" y habilítala

### 2. Crear credenciales OAuth 2.0

1. Ve a "APIs y servicios" → "Credenciales"
2. Haz clic en "Crear credencial" → "OAuth 2.0 - Aplicación de escritorio"
3. Descarga el archivo JSON
4. Guarda el archivo como: `config/google_credentials.json`

### 3. Ejecutar el setup

```bash
python setup_google_drive.py
```

Esto:
- Abre tu navegador automáticamente
- Te pide que autorices la aplicación
- Guarda el token en `config/google_token.json`

## Estructura de directorios esperada

```
config/
├── google_credentials.json  ← Descargar de Google Cloud Console
├── google_token.json        ← Se crea automáticamente tras autorizar
├── consorcios.json
├── settings.json
└── .env
```

## Verificar conexión

```bash
python -c "from src.cloud.google_drive_client import prueba_conexion; prueba_conexion()"
```

Debe mostrar: `✓ Conexión a Google Drive exitosa`

## Archivos modificados

Estos archivos ahora soportan URLs de Drive:

- `src/cloud/google_drive_client.py` — cliente de Drive API
- `src/registry/excel_registry.py` — hipervínculos funcionales en Drive
- `src/processor.py` — obtiene URLs de Drive
- `config/settings.json` — agregar `"drive_habilitado": true`

## Solución de problemas

Si falla la autenticación:
1. Verifica que `config/google_credentials.json` existe
2. Asegúrate que la Google Drive API está habilitada
3. Elimina `config/google_token.json` y corre `setup_google_drive.py` de nuevo

Si los hipervínculos no funcionan:
1. Verifica que `drive_habilitado` es `true` en `config/settings.json`
2. Abre los archivos Excel de Drive directamente en el navegador (Google Drive web)
3. Los hipervínculos file:/// NO funcionan en Drive — solo las URLs https://