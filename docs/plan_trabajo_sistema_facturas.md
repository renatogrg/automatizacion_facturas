# Plan de trabajo — Sistema Inteligente para la Gestión Automática de Facturas por Consorcio

## 1. Resumen de la solución

Aplicación Python que corre en segundo plano en cada PC (sin servidor compartido), vigila la carpeta `ENTRADA_FACTURA`, identifica el consorcio, clasifica y organiza cada factura en `Consorcio\Año\Mes`, y registra los datos en un Excel por consorcio. Solo llama a la API de Claude (Haiku 4.5) cuando la validación local gratuita no puede resolver el caso. Se controla con un ícono en la bandeja del sistema (encender/apagar), sin que el usuario vea ni edite código.

---

## 2. Tecnologías y librerías

| Capa | Tecnología | Uso |
|---|---|---|
| Lenguaje | **Python 3.12** (ya tienes 3.12.10 — perfecto, no reinstales nada) | Todo el sistema |
| Monitoreo de carpeta | `watchdog` | Detecta archivos nuevos en `ENTRADA_FACTURA` |
| Lectura de PDF nativo | `PyMuPDF` (fitz) | Extrae texto de facturas electrónicas (gratis, sin API) |
| OCR local | `pytesseract` + `pdf2image` + `Pillow` (requiere instalar **Tesseract-OCR** para Windows aparte) | Lee PDFs escaneados o fotos, gratis |
| Coincidencia local | `re` (regex) + `rapidfuzz` | Busca RUC y nombre de consorcio sin usar IA |
| IA (solo si hace falta) | `anthropic` (SDK oficial) → modelo `claude-haiku-4-5-20251001` | Resuelve casos ambiguos |
| Registro | `openpyxl` | Escribe/actualiza los Excel de cada consorcio y el de pendientes |
| Interfaz encendido/apagado | `pystray` + `Pillow` | Ícono en la bandeja de Windows, sin ventanas ni código visible |
| Configuración segura | `python-dotenv` | Carga la API key desde un archivo `.env`, nunca en el código |
| Autoarranque | Acceso directo en la carpeta de inicio de Windows o Programador de tareas | Se abre solo al encender la PC (más simple y estable que un servicio Windows real, con el mismo efecto para el usuario) |
| Empaquetado | `PyInstaller` | Convierte todo en un `.exe` para las PCs de los usuarios, que no necesitan instalar Python |
| Control de versiones | Git + GitHub (ya tienes el repo) | — |

No necesitas cambiar tu versión de Python: 3.12.10 es compatible con todas estas librerías.

---

## 3. Estrategia de ahorro: cascada de validación antes de usar la API

Cada factura pasa por pasos gratuitos antes de considerar siquiera llamar a Claude:

1. **Texto nativo del PDF** (PyMuPDF): la mayoría de facturas electrónicas ya traen el texto embebido → gratis y exacto.
2. **Si no hay texto** (foto o escaneo): OCR local con Tesseract → gratis, aunque con algo más de error.
3. **Con el texto obtenido**, se busca localmente:
   - El **RUC del consorcio** con una expresión regular (siempre 11 dígitos) comparado contra `consorcios.json`.
   - El **nombre/razón social** con coincidencia difusa (`rapidfuzz`) por si el RUC no aparece limpio.
   - La **fecha de emisión** con patrones regex.
4. **Si el RUC coincide exacto** → no se llama a la API. Se organiza y registra directo. En tus 4 ejemplos, el RUC del consorcio aparece siempre como texto plano, así que este paso debería resolver la mayoría de los casos reales.
5. **Solo si el texto es insuficiente o ambiguo**, se envía el **texto extraído** (no la imagen) a Claude Haiku 4.5, pidiéndole que devuelva un JSON con consorcio, RUC, proveedor, fecha y total. Enviar texto cuesta muchísimo menos que enviar una imagen.
6. **Solo en el peor caso** (OCR no obtuvo texto útil) se envía la imagen/PDF directamente a Claude Haiku 4.5 (puede leer imágenes). Este es el caso más caro y debería ser el menos frecuente.
7. Si ni la API puede resolverlo con confianza → el documento va a `PENDIENTES` para revisión manual.

### Costo estimado con Claude Haiku 4.5

Precio oficial: **US$ 1.00 por millón de tokens de entrada** y **US$ 5.00 por millón de tokens de salida**.

| Escenario | Tokens aprox. por factura | Costo aprox. por factura |
|---|---|---|
| Llamada solo con texto (caso típico cuando sí se necesita la API) | ~800 entrada / ~200 salida | ~US$ 0.0018 |
| Llamada con imagen (peor caso) | ~1600 entrada / ~250 salida | ~US$ 0.0028 |

Si de 300 facturas al mes solo un 15% necesita la API (el resto se resuelve gratis por RUC/regex), el gasto mensual estimado es de **menos de US$ 0.15 por consorcio**. El sistema está diseñado para que este porcentaje baje aún más con el tiempo.

---

## 4. Estructura de carpetas del código fuente (repositorio GitHub)

```
sistema-facturas/
├── .git/
├── .gitignore
├── README.md
├── requirements.txt
├── config/
│   ├── consorcios.json        ← editable, aquí se agregan nuevos consorcios
│   ├── settings.json          ← rutas, umbrales de confianza, etc.
│   └── .env.example           ← plantilla (la real .env NO se sube a git)
├── src/
│   ├── main.py                 # punto de entrada, arranca el ícono de bandeja
│   ├── watcher.py               # monitorea ENTRADA_FACTURA
│   ├── extractor/
│   │   ├── pdf_text.py          # texto nativo del PDF
│   │   ├── ocr.py                # OCR local con Tesseract
│   │   └── claude_client.py     # llamadas a la API (solo si es necesario)
│   ├── classifier/
│   │   └── consorcio_matcher.py # regex + fuzzy matching contra consorcios.json
│   ├── organizer/
│   │   └── file_organizer.py    # crea carpetas Consorcio/Año/Mes y mueve el archivo
│   ├── registry/
│   │   └── excel_registry.py    # escribe en Registro Facturas.xlsx / Registro_Pendientes.xlsx
│   ├── tray/
│   │   └── tray_icon.py         # interruptor ON/OFF en la bandeja de Windows
│   └── utils/
│       ├── logger.py
│       └── config_loader.py
├── tests/
│   └── sample_invoices/         # tus 4 ejemplos, para pruebas (⚠ no subir a git, ver .gitignore)
└── build/
    └── build_exe.py             # script para generar el .exe con PyInstaller
```

---

## 5. Ubicaciones fijas en la PC del usuario final

- **Programa instalado (el .exe y sus archivos internos):** `C:\SistemaFacturas\`
- **Configuración editable (JSON de consorcios, settings, .env):** `C:\SistemaFacturas\config\` — el usuario **no edita código**, pero si en el futuro se agrega un consorcio nuevo, alguien de confianza puede abrir `consorcios.json` con el Bloc de notas y agregar un bloque como los existentes. Es texto plano, no código ejecutable.
- **Carpetas de trabajo diario (entrada y facturas organizadas):** `C:\FACTURAS\`

```
C:\FACTURAS\
├── ENTRADA_FACTURA\
├── Consorcio El Milagro\
│   └── 2026\01-Enero\...  (creadas automáticamente por año/mes, nunca por el usuario)
├── Consorcio V Y J\
├── Consorcio Salud Primavera\
├── Consorcio Wayayo\
└── PENDIENTES\
    ├── Registro_Pendientes.xlsx
    └── (archivos no resueltos)
```

Separar `C:\SistemaFacturas\` (programa + config) de `C:\FACTURAS\` (datos del día a día) evita problemas de permisos y hace más simple explicarle al usuario "tus facturas viven en C:\FACTURAS".

### `consorcios.json` (ya generado con tus 4 ejemplos)

Identificación por **nombre y por RUC**, extraídos de las facturas que enviaste:

```json
{
  "consorcios": [
    { "id": "el_milagro", "nombre": "Consorcio El Milagro", "ruc": "20614915391" },
    { "id": "salud_primavera", "nombre": "Consorcio Salud Primavera", "ruc": "20614411784" },
    { "id": "v_y_j", "nombre": "Consorcio V Y J", "ruc": "20614936739" },
    { "id": "wayayo", "nombre": "Consorcio Wayayo", "ruc": "20615343928" }
  ]
}
```

Cuando aparezca un quinto consorcio, solo se agrega otro bloque igual a este JSON — el código no cambia.

---

## 6. Interruptor de encendido/apagado

- Un **ícono en la bandeja del sistema** (junto al reloj de Windows), hecho con `pystray`.
- Clic derecho → menú con: **Encender / Apagar procesamiento**, **Abrir carpeta de pendientes**, **Salir**.
- El estado (ON/OFF) se guarda en `config/settings.json`; cuando está en OFF, el `watcher` deja de procesar nuevos archivos pero la app sigue visible en la bandeja.
- Arranca solo al iniciar sesión en Windows (acceso directo en la carpeta de inicio), así el usuario nunca tiene que abrir nada manualmente.
- El usuario **nunca ve una consola ni código**: solo el ícono y ese menú.

---

## 7. Manejo de facturas no clasificadas

Si tras el paso local y el paso con la API no hay confianza suficiente (texto ilegible, RUC no encontrado, formato desconocido):

- El archivo se mueve a `C:\FACTURAS\PENDIENTES\`.
- Se agrega una fila en `Registro_Pendientes.xlsx` con fecha de proceso, nombre del archivo y motivo (si se pudo determinar; si no, se deja en blanco).

---

## 8. Fases de desarrollo

| Fase | Contenido | Resultado esperado |
|---|---|---|
| **0. Preparación** | Repo, entorno virtual, estructura de carpetas, `.gitignore`, `requirements.txt` | Proyecto listo para programar (hoy) |
| **1. Extracción y clasificación local** | Lectura de texto nativo de PDF + regex/fuzzy contra `consorcios.json`, sin IA | El sistema clasifica correctamente facturas electrónicas "limpias" |
| **2. OCR local** | Integrar Tesseract para fotos y PDFs escaneados | Cubre facturas de baja calidad, sigue sin usar la API |
| **3. Integración con Claude Haiku 4.5** | Llamada de respaldo (texto o imagen) cuando el paso local falla, con salida en JSON | Cobertura casi total de casos, con costo mínimo |
| **4. Organización y registro** | Creación automática de carpetas Año/Mes y escritura en el Excel del consorcio | Archivos ordenados y registrados sin intervención manual |
| **5. Pendientes** | Carpeta y Excel de pendientes | Ninguna factura se pierde |
| **6. Interfaz encendido/apagado** | Ícono de bandeja, sin código visible al usuario | Control amigable del servicio |
| **7. Empaquetado** | `.exe` con PyInstaller, instalable en `C:\SistemaFacturas\` en cualquier PC | Listo para distribuir a otras computadoras |
| **8. Pruebas con tus 4 consorcios reales** | Usar las facturas que ya compartiste como casos de prueba | Validación antes de entregar |
| **9. Versión 2 (futura)** | Migrar a Google Drive + Google Sheets manteniendo la misma lógica | Evolución sin rehacer el núcleo |

---

## 9. Requisitos de la PC del usuario final (8 GB de RAM)

- El `.exe` empaquetado con PyInstaller no requiere Python instalado.
- Tesseract-OCR se instala una sola vez junto con el programa (instalador liviano, ~50 MB).
- El procesamiento es por archivo (uno a la vez), así que el consumo de RAM se mantiene bajo incluso con 8 GB; no se cargan modelos de IA en la PC del usuario, todo el trabajo pesado de IA ocurre en la nube (API de Anthropic).

---

## 10. `.gitignore` recomendado

Protege la API key, datos reales de facturas y archivos generados:

```
# Entornos virtuales
venv/
.venv/
__pycache__/
*.pyc

# Configuración sensible
.env
config/.env

# Facturas y datos reales (privacidad)
tests/sample_invoices/*.pdf
tests/sample_invoices/*.jpg
tests/sample_invoices/*.jpeg
tests/sample_invoices/*.png
!tests/sample_invoices/.gitkeep

# Logs
logs/
*.log

# Build / empaquetado
build/dist/
dist/
*.spec

# IDE
.vscode/
.idea/
```

---

## 11. Primeros pasos (hoy)

Ver el mensaje de chat con los comandos exactos paso a paso para PowerShell y la estructura de archivos inicial ya generada.
