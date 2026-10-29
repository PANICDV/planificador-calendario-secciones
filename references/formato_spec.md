# Formato de las especificaciones

Las rutas de los ejemplos son las de claude.ai (`/mnt/user-data/outputs`). En otro entorno,
usa su carpeta de salida; el script crea la carpeta si no existe.

## Modo 1: plan nuevo por secciones (`build_sections.py spec.json`)

```json
{
  "calendar_name": "Plan 3–11 oct",
  "timezone": "America/Lima",
  "output_dir": "/mnt/user-data/outputs",
  "range_end": "2026-10-11",
  "combined": false,
  "sections": [
    {"id": "tesis",    "name": "🎓 Tesis",                        "color": "#D50000", "color_name": "Tomate"},
    {"id": "tech",     "name": "🖥️ Servidor · Herramientas de IA", "color": "#8E24AA", "color_name": "Uva"},
    {"id": "tramites", "name": "🏦 Bancos y trámites",             "color": "#F4511E", "color_name": "Mandarina"},
    {"id": "rutina",   "name": "🏡 Rutina y hogar",                "color": "#33B679", "color_name": "Salvia"},
    {"id": "flexible", "name": "🔄 Espacios flexibles",            "color": "#616161", "color_name": "Grafito"}
  ],
  "events": [
    {"section": "rutina", "title": "😴 Dormir", "start": "2026-10-02T23:00", "end": "2026-10-03T07:00",
     "repeat": {"freq": "DAILY", "until": "2026-10-11"}},
    {"section": "tesis", "title": "🎓 Tesis: diapositivas (bloque 1)",
     "start": "2026-10-03T10:00", "end": "2026-10-03T12:30", "description": "Estructura completa."},
    {"section": "flexible", "title": "🔄 Espacio flexible",
     "start": "2026-10-03T18:15", "end": "2026-10-03T19:30"}
  ]
}
```

| Campo | Notas |
|---|---|
| `sections` | En el orden en que se numeran los archivos (`1_tesis.ics`, `2_tech.ics`…). Mantén el mismo orden e `id` en las actualizaciones. |
| `id` | En minúsculas, sin espacios ni tildes (`a-z`, `0-9`, `_`, `-`): es parte del nombre del archivo. |
| `name` | Nombre del calendario, con emoji. |
| `color` / `color_name` | Hex `#RRGGBB` y nombre de la paleta (ver `secciones.md`). |
| `combined` | `true` → también genera `todo_en_uno.ics`, útil para quien quiera ver todo en un calendario. |
| `lang` | Idioma de los mensajes del script: `es` (por defecto) o `en`. |
| `events[].section` | Obligatorio; debe coincidir con un `id`. |

Los demás campos de cada evento (`start`/`end` en hora local sin zona, `date`/`end_date` para
todo el día, `repeat`, `alarm_min`, `description`, `location`, `allow_overlap`) funcionan igual
que en el planificador de un solo calendario:

| Necesidad | `repeat` |
|---|---|
| Todos los días hasta el 11/10 | `{"freq": "DAILY", "until": "2026-10-11"}` |
| Lunes a viernes | `{"freq": "WEEKLY", "byday": ["MO","TU","WE","TH","FR"], "until": "2026-10-09"}` |
| Cada 30 días | `{"freq": "DAILY", "interval": 30}` |
| El 3 de cada mes | `{"freq": "MONTHLY", "bymonthday": 3}` |
| Último día de cada mes | `{"freq": "MONTHLY", "bymonthday": -1}` |
| Una vez al año (15 de marzo) | `{"freq": "YEARLY", "bymonth": 3, "bymonthday": 15}` |
| Regla libre | `{"rrule": "FREQ=MONTHLY;BYDAY=1MO"}` |

`until` es una fecha local inclusiva. Sin `until` ni `count` la repetición es indefinida, lo
correcto para los recordatorios.

### Recordatorios
Usa un segundo JSON con el mismo formato y sus propias secciones, por ejemplo:

```json
{"timezone": "America/Lima", "output_dir": "/mnt/user-data/outputs/recordatorios",
 "sections": [
   {"id": "pagos", "name": "💳 Pagos", "color": "#E67C73", "color_name": "Flamenco"},
   {"id": "mantenimiento", "name": "🧽 Mantenimiento", "color": "#0B8043", "color_name": "Albahaca"}],
 "events": [
   {"section": "pagos", "title": "💡 Pagar la luz", "date": "2026-11-03", "repeat": {"freq": "MONTHLY", "bymonthday": 3}},
   {"section": "mantenimiento", "title": "🧊 Limpiar el refrigerador", "start": "2026-10-10T10:00",
    "end": "2026-10-10T10:45", "repeat": {"freq": "DAILY", "interval": 30}}]}
```
Para que los archivos de recordatorios no pisen la numeración del plan, usa otra carpeta de
salida (como en el ejemplo) o `id` distintos. Un JSON solo con eventos de todo el día es
válido.

### Validación
Antes de escribir, el script revisa el JSON y lista **todos** los problemas de una vez (zona
desconocida, fecha inválida, fin antes del inicio, `id` con espacios o repetido, color que no
es hex, evento con una `section` que no existe). Si hay alguno, no escribe archivos: corrige y
vuelve a ejecutar. Con `--check` solo valida y muestra la tabla.

## Modo 2: separar un .ics existente (`--split plan.ics reglas.json`)

```json
{
  "output_dir": "/mnt/user-data/outputs",
  "default": "rutina",
  "sections": [
    {"id": "tesis",    "name": "🎓 Tesis",            "color": "#D50000", "color_name": "Tomate",
     "emojis": ["🎓", "🎤"], "keywords": ["tesis", "jurado"]},
    {"id": "tramites", "name": "🏦 Bancos y trámites", "color": "#F4511E", "color_name": "Mandarina",
     "emojis": ["🏦", "💳", "📄", "🚗", "📞"], "keywords": ["banco", "pago", "cita"]},
    {"id": "flexible", "name": "🔄 Espacios flexibles", "color": "#616161", "color_name": "Grafito",
     "emojis": ["🔄"]},
    {"id": "rutina",   "name": "🏡 Rutina y hogar",    "color": "#33B679", "color_name": "Salvia"}
  ]
}
```

Clasificación: primero el **emoji inicial** del título (en el orden de `sections`), luego las
**palabras clave** (sin distinguir mayúsculas), y si no coincide nada, la sección `default`
(debe ser uno de los `id`). Los emojis se comparan con y sin selector de variante, así que
`🖥` y `🖥️` cuentan como el mismo. Acepta archivos con saltos de línea CRLF o LF.
Conserva los eventos tal cual, incluida la zona horaria y las repeticiones; el color lo da
cada calendario. Antes de entregar, revisa la lista de eventos que cayeron en `default`.
