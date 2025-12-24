<p align="center">
  <img src="https://raw.githubusercontent.com/psdani9xo/webshot-mailer/main/static/logo.png" width="128">
</p>

<h1 align="center">WebShot Mailer</h1>

<p align="center">
  Captura paginas web automaticamente y las envia por correo usando Docker
</p>

<p align="center">
  <b>Simple · Autonomo · Ideal para servidores en casa</b>
</p>

---

## Que es WebShot Mailer

**WebShot Mailer** es una aplicacion web autoalojada que permite:

- Capturar paginas web con Selenium
- Programar envios diarios, semanales o por intervalo
- Enviar las capturas por correo (Gmail u otros SMTP)
- Eliminar popups (cookies, Telegram, banners, etc.)
- Gestionar todo desde una interfaz web sencilla

Pensado para:
- dashboards
- webcams
- paginas de estado
- informes automaticos
- uso personal en LAN

---

## Caracteristicas principales

- 🌐 Captura paginas web en segundo plano (headless Chromium)
- ⏰ Programaciones flexibles (diario, semanal, intervalos)
- 📧 Envio por SMTP (Gmail, servidores propios)
- 🧹 Eliminacion de popups por selectores CSS
- 🖼️ Imagen incrustada en el correo (CID)
- 🧪 Boton de prueba y captura manual
- 🗂️ Historial de ejecuciones
- ♻️ Limpieza automatica de capturas antiguas
- 🐳 100% Docker

---

## Interfaz web

La aplicacion incluye una interfaz web para:

- Crear y editar tareas
- Configurar SMTP
- Probar envios
- Ver historial y errores
- Descargar capturas

Por defecto:

```
http://localhost:1234
```

---

## Instalacion rapida (Docker)

### 1️⃣ Crear archivo `.env`

```env
TZ=Europe/Madrid
APP_SECRET=change-me
SMTP_PASS_GMAIL=tu_app_password_de_16_caracteres
```

**Nota:** Usa una **App Password** de Gmail.  
No uses tu contrasena normal de Google.

---

### 2️⃣ docker-compose.yml

```yaml
services:
  webshot:
    image: psdani9xo/webshot-mailer:latest
    container_name: webshot-mailer
    ports:
      - "1234:1234"
    environment:
      - TZ=${TZ}
      - APP_SECRET=${APP_SECRET}
      - SMTP_PASS_GMAIL=${SMTP_PASS_GMAIL}
    volumes:
      - ./data:/app/data
      - ./captures:/app/captures
    restart: unless-stopped
```

---

### 3️⃣ Arrancar el servicio

```bash
docker compose up -d
```

Abre el navegador en:

```
http://localhost:1234
```

---

## Configuracion SMTP (Gmail)

En la interfaz web crea un perfil SMTP con:

| Campo | Valor |
|-----|------|
| Host | smtp.gmail.com |
| Puerto | 587 |
| Encryption | STARTTLS |
| Username | tu_correo@gmail.com |
| Password env | SMTP_PASS_GMAIL |
| From email | tu_correo@gmail.com |

Pulsa **Probar SMTP** antes de crear tareas.

---

## Eliminar popups (ejemplo Telegram)

En una tarea, en **Remove selectors (JSON)**:

```json
["#WolfTelegram"]
```

O varios:

```json
["#WolfTelegram", ".cookie", ".cookies-banner"]
```

Tambien puedes combinar acciones especificas para popups que requieren hacer clic o solo ocultarlos:

```json
[
  "#WolfTelegram",
  {"selector": ".cookie", "action": "hide"},
  {"selector": "button.close", "action": "click"}
]
```

Acciones disponibles:

- `remove` (por defecto): elimina los elementos encontrados.
- `hide`: oculta y deshabilita interacciones (display/visibility/pointer-events).
- `click`: ejecuta `click()` sobre los elementos que matcheen el selector.

En el formulario de tareas hay plantillas seleccionables con los popups mas habituales para no tener que escribir JSON a mano. Incluyen:

- Banners de cookies genericos (`.cookie`, `.cookies`, `.cookie-banner`, etc.) ocultados automaticamente.
- Consentimiento con OneTrust (clic en `#onetrust-accept-btn-handler`).
- Modales de newsletter/registro (oculta modal y backdrop de Bootstrap).
- Gestores GDPR/CMP habituales (Didomi, Quantcast) combinando `hide` y `click`.

Tambien puedes pegar el HTML del popup (el `<div>` o contenedor principal) en el formulario para que detecte automaticamente un selector util (`#id`, `.clase`, o `tag.clase`). El selector se añade sin duplicados a la lista JSON.

---

## Seguridad

- Las contrasenas **no se guardan en la base de datos**
- Se leen desde **variables de entorno**
- Pensado para uso personal en LAN
- No expongas el puerto a internet sin proteccion adicional

---

## Estructura del proyecto

```
webshot-mailer/
├── app.py
├── capture.py
├── mailer.py
├── scheduler.py
├── models.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── templates/
├── static/
├── data/        (volumen Docker)
└── captures/    (volumen Docker)
```

---

## Autor

Creado por **psdani9xo**

---

## Licencia

MIT
