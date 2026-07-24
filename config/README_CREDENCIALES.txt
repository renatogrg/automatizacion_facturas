===================================================================
  CÓMO CAMBIAR LAS CREDENCIALES DE GOOGLE DRIVE
===================================================================

Esta carpeta contiene los archivos de acceso a Google Drive.
Si necesitas cambiar la cuenta de Google donde se suben las facturas,
sigue estos pasos:

-------------------------------------------------------------------
ARCHIVOS IMPORTANTES:
-------------------------------------------------------------------

  google_credentials.json
    → Identifica tu aplicación ante Google (Client ID / Secret).
      Se descarga desde Google Cloud Console una sola vez.

  google_token.json
    → Token de acceso de la cuenta de Google que guarda las facturas.
      Se genera automáticamente la primera vez que autorizas el acceso.

-------------------------------------------------------------------
PARA CAMBIAR DE CUENTA DE GOOGLE DRIVE:
-------------------------------------------------------------------

  1. Borra el archivo:  google_token.json
  2. Inicia el programa normalmente (doble clic en el acceso directo).
  3. Se abrirá el navegador pidiendo que inicies sesión en Google.
  4. Inicia sesión con la nueva cuenta de Google.
  5. Listo — desde ese momento las facturas se subirán a esa cuenta.

-------------------------------------------------------------------
PARA CAMBIAR DE PROYECTO DE GOOGLE CLOUD (client_id / client_secret):
-------------------------------------------------------------------

  1. Ve a https://console.cloud.google.com/apis/credentials
  2. Descarga el nuevo "credentials.json" de tu cliente OAuth.
  3. Renómbralo a "google_credentials.json".
  4. Reemplaza el archivo en esta carpeta (C:\SistemaFacturas\config\).
  5. Borra también "google_token.json" (el token viejo ya no sirve).
  6. Inicia el programa y autoriza la nueva cuenta.

-------------------------------------------------------------------
PARA CAMBIAR LA CLAVE DE API DE GROQ:
-------------------------------------------------------------------

  1. Abre el archivo ".env" en esta misma carpeta (con el Bloc de notas).
  2. Cambia el valor de GROQ_API_KEY=gsk_...
  3. Guarda el archivo y reinicia el programa.

===================================================================