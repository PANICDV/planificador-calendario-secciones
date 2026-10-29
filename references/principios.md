# Principios de diseño del horario

Léelo antes de diseñar. Cada principio tiene un porqué: aplícalos con criterio.

## Principios

- **El sueño es un evento visible.** Si no aparece en el calendario, el plan se lo come. Respeta las horas que la persona indique y deja ~30 min entre despertar y la primera actividad exigente.
- **Trabajo profundo en las horas de más energía.** Pregunta cuáles son; si no lo sabe, usa la mañana. Lo mecánico (correos, trámites cortos) va en horas de menor energía.
- **Trámites en horario hábil.** Bancos, llamadas, clínicas y oficinas: L–V aprox. 9:00–18:00, sábados por la mañana. Pon antes un bloque de preparación de documentos si el trámite lo necesita.
- **Bloques de tamaño útil.** Trabajo profundo: 60–150 min. Tareas pequeñas: 15–45 min, agrupadas. Menos de 45 min no alcanza para concentrarse en algo complejo; más de 2,5 h seguidas rinde poco.
- **Variedad diaria.** Ningún día dedicado a un solo tema; máximo ~2 bloques del mismo tema por día, separados por otra cosa. Alterna lo exigente con lo liviano.
- **Proyectos grandes en bloques numerados.** "Tesis: diapositivas (bloque 3)". En la descripción pon el objetivo concreto del bloque. Pon el bloque de cierre ("TERMINAR …") con margen antes de la fecha límite.
- **Fechas inciertas → opción A / opción B.** Si un trámite puede caer en dos días, reserva un bloque en cada uno y escribe en la descripción que el que no se use se convierte en tiempo para el tema prioritario. Así no se pierde tiempo ni se sobrecarga el plan.
- **Espacios flexibles 🔄.** Aproximadamente uno por día (10–15 % del tiempo disponible), para mover lo que no se cumplió. Un plan sin holgura se rompe al primer imprevisto y la persona lo abandona.
- **Márgenes tras eventos variables.** Si el almuerzo a veces se alarga 15 min, el siguiente bloque empieza 15 min después.
- **No llenar hasta la hora de dormir.** Deja tiempo libre o familiar al final del día y días más ligeros (por ejemplo, viernes por la noche y parte del domingo).
- **Revisión semanal.** Un bloque corto para revisar avances y pedir el ajuste del plan, y otro para planificar la semana siguiente.
- **Prioridades explícitas mandan.** Si la persona dice "dale más a X", reasigna tiempo desde lo menos urgente y muestra una tabla antes/después de horas por tema.
- **Alarmas solo en lo crítico.** Citas, trámites con hora, pagos, votaciones, recojo de hijos. Si todo suena, nada suena.

## Según el horizonte
| Tipo | Cómo planificar |
|---|---|
| Diaria | Bloques detallados de toda la jornada. |
| Semanal / periodo corto (≤ 3 semanas) | Detalle completo día por día. |
| Periodo largo / trimestral | Detalle fino solo para las primeras 1–2 semanas. Después: rutina recurrente + hitos semanales por proyecto ("Semana 5: informe listo") + revisiones semanales. Los planes detallados a largo plazo caducan rápido, así que es mejor revisarlos y ajustarlos cada semana. |

## Formato de los eventos

- **Rutina como eventos repetitivos** (`repeat`), no como copias: es más limpio y más fácil de borrar.
- **Título**: emoji + tema + detalle. El emoji sirve para reconocer la categoría y para buscar (borrar o filtrar) en el calendario. Usa el mismo emoji para el mismo tema durante todo el plan.

| Emoji | Uso típico |
|---|---|
| 😴 🏃 🍳 🍽️ | Sueño, ejercicio, comidas |
| 🐕 🎒 🧹 | Mascotas, hijos/colegio, limpieza |
| 🎓 🎤 | Estudios, tesis, ensayos/presentaciones |
| 🖥️ 🤖 🧩 | Tecnología, proyectos técnicos, herramientas |
| 🏦 💳 📄 🚗 📞 | Bancos, pagos, documentos, vehículo, llamadas |
| 🗂️ 📧 🎨 📋 | Organización, correo, diseño, revisión o planificación |
| 📈 💾 | Inversiones/mercado, ventas |
| 🔄 | Espacio flexible |

- **Descripción**: el objetivo concreto, la alternativa si la hay y los datos útiles (nombre del médico, qué documentos llevar).

## Recordatorios recurrentes

Van en archivos aparte, en su propia sección ("🔔 Recordatorios"), o en varias si la persona lo prefiere ("💳 Pagos", "🧽 Mantenimiento").
- Pagos: evento de todo el día en la fecha de pago. Si piden aviso previo, agrega un segundo evento el día anterior, porque las alarmas de eventos de todo el día se comportan distinto según la app.
- "Cada N días": `freq DAILY` + `interval N`. "Día X de cada mes": `freq MONTHLY` + `bymonthday X`. Para fin de mes usa `bymonthday -1`. Si X es 29–31, avisa que los meses cortos se saltan ese día y ofrece usar el último día del mes.
- Sin fecha de fin, salvo que la persona la dé: los recordatorios son permanentes.
- Las tareas de mantenimiento (limpiar el refrigerador) pueden llevar hora sugerida en un hueco típico de la rutina de la persona.

