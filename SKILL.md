---
name: planificador-calendario-secciones
description: Diseña horarios optimizados (diarios, semanales, por periodos cortos o largos, trimestrales) y los entrega como VARIOS calendarios .ics, uno por sección (tesis, trabajo, trámites, rutina, etc.), cada uno con su color, para importar a Google Calendar, Apple u Outlook; los recordatorios recurrentes (pagos, limpiezas) van en su propio calendario. Usar SIEMPRE que la persona quiera su plan o calendario separado por categorías, secciones, áreas o colores, quiera "que se vea más distintivo", quiera poder ocultar o mostrar temas, o pida separar por colores un .ics o un plan que ya tiene. Si pide un plan sin mencionar secciones ni colores, basta con la versión de un solo calendario (planificador-calendario) si está disponible.
---

# Planificador de calendario por secciones

Hace lo mismo que un planificador normal (entrevista, diseño optimizado, archivos
importables), pero entrega **un calendario por sección, cada uno con su color**. Así se
reconoce cada tema de un vistazo y se puede ocultar o mostrar una sección con un clic.

Por qué un archivo por sección: Google Calendar ignora el color de cada evento que trae un
.ics; el color lo da el calendario. Un calendario por sección es la única forma de que los
colores se vean en Google. Apple sí respeta el color que trae el archivo.

Modos:
- **Plan nuevo por secciones**: entrevista, diseño, un .ics por sección.
- **Separar un plan existente**: la persona trae un .ics (por ejemplo, uno hecho con la versión de un solo color) y quiere separarlo por colores. Ve directo al paso 3 (proponer secciones) y usa el modo `--split`.
- **Solo recordatorios por secciones**: por ejemplo, "💳 Pagos" y "🧽 Mantenimiento" en calendarios separados.
- **Actualizar**: ver "Actualizaciones".

## Flujo de trabajo

### 1. Reunir lo que ya se sabe
Revisa la conversación y la memoria (rutina, sueño, trabajo, preferencias de planificación,
secciones o colores que la persona ya eligió antes). Lo conocido no se pregunta: se confirma
en una línea. Si la persona ya tiene secciones y colores de un plan anterior, **reutilízalos**:
ya creó esos calendarios en su app y cambiarlos la obliga a rehacer el trabajo.

### 2. Entrevista por bloques
Lee `references/cuestionario.md` y pregunta un bloque por mensaje, en lista numerada, solo lo
que falte (periodo, rutina fija, pendientes, recordatorios, preferencias). No más de 3–4
rondas; lo que la persona no sepa, estímalo tú y dilo.

### 3. Proponer las secciones (bloque extra, siempre)
Con los pendientes ya conocidos, propón las secciones en una tabla (emoji + nombre, color,
qué incluye) y pide confirmación o cambios en un solo mensaje. Guía para armarlas en
`references/secciones.md`. En resumen:
- **4–8 secciones.** Menos no distingue; más satura la lista de calendarios y el trabajo de importar.
- Agrupa por **tipo de atención**, no por tarea suelta: "Servidor · Herramientas de IA · Cursos" juntos (técnico), "Bancos y trámites" juntos (horario hábil).
- Siempre: una sección de **rutina y hogar** y una de **espacios flexibles** (gris). Las **prioridades** van en colores fuertes y distintos entre sí.
- Los recordatorios recurrentes van en su(s) propia(s) sección(es) y en archivos aparte.

### 4. Diseñar el horario
Aplica `references/principios.md` (sueño visible, trabajo profundo en horas de energía,
trámites en horario hábil, bloques de 60–150 min, variedad diaria, opciones A/B para fechas
inciertas, un espacio flexible al día, revisión semanal, horizonte largo con detalle solo en
las primeras 1–2 semanas). Asigna cada evento a una sección.

### 5. Generar y validar
Escribe el JSON (formato en `references/formato_spec.md`) y ejecuta:

```bash
# plan nuevo
python <ruta-skill>/scripts/build_sections.py <carpeta-de-trabajo>/spec.json
# separar un .ics existente
python <ruta-skill>/scripts/build_sections.py --split <ruta>/plan.ics <carpeta-de-trabajo>/reglas.json
```

El script valida el JSON (si hay errores, los lista todos y no escribe nada), revisa choques
sobre el plan completo, escribe un .ics por sección (`1_tesis.ics`, `2_tech.ics`…) y muestra
la tabla sección → color → eventos → horas. Corrige los choques no intencionales. Si avisa que
falta `python-dateutil`, instálalo (`pip install python-dateutil`) y vuelve a ejecutar. En el
modo `--split` revisa la lista de eventos que cayeron en la sección por defecto: si alguno
está mal, ajusta las reglas y vuelve a ejecutar.
Para los recordatorios usa un JSON aparte (también por secciones si son varias).
Guarda los archivos en la carpeta de salida del entorno (en claude.ai: `/mnt/user-data/outputs/`;
el script crea la carpeta si no existe) y entrégalos todos juntos, en el orden numerado, con la
herramienta del entorno para compartir archivos (en claude.ai: una sola llamada a `present_files`).

### 6. Entregar
Mensaje breve en el idioma de la persona:
- **Leyenda**: tabla con archivo, nombre del calendario, color (nombre + hex) y qué incluye.
- 3–6 decisiones clave en prosa y los supuestos que tomaste.
- Pasos de importación de `references/importar.md` para su app. Lo esencial: crear un calendario por sección con el nombre de la tabla, importar cada archivo en su calendario y ponerle su color. Nunca importar en el calendario principal.
- Crear los calendarios se hace una sola vez; en las actualizaciones se reutilizan.

## Actualizaciones
- Mantén **las mismas secciones, nombres, números de archivo y colores**: la persona ya creó esos calendarios.
- Cambia solo lo pedido y reequilibra lo mínimo. Si pidió "dale más a X", muestra una tabla antes/después de horas por sección.
- Entrega **solo los archivos de las secciones que cambiaron** y di cuáles son. Para cada una: borrar ese calendario y volver a crearlo con el mismo nombre y color antes de importar, porque Google no reemplaza de forma fiable los eventos ya importados y quedarían duplicados. Las secciones sin cambios no se tocan.
- Los recordatorios solo se regeneran si cambiaron.
- Si la persona dice que algo le gustó, aplícalo también en las proyecciones futuras.

## Archivos de referencia
- `references/cuestionario.md`: bloques de preguntas de la entrevista.
- `references/secciones.md`: cómo armar las secciones, paleta de colores y secciones sugeridas.
- `references/principios.md`: principios para diseñar el horario y formato de los eventos.
- `references/formato_spec.md`: JSON del plan por secciones y de las reglas de `--split`.
- `references/importar.md`: crear calendarios, importar, colorear y borrar en Google, Apple y Outlook.
