# planificador-calendario-secciones

Skill de Claude que diseña horarios y los entrega como **varios calendarios .ics, uno por
sección y cada uno con su color**, para importar a Google Calendar, Apple u Outlook. Los
recordatorios recurrentes (pagos, limpiezas, mantenimientos) van en su propio calendario.

## Requisito
Python 3 y `python-dateutil` (`pip install python-dateutil`) para generar los archivos.

## Instalación
- **Claude (web/escritorio)**: sube el ZIP en Customize → Skills → + → Upload a skill
  (activa antes "Code execution and file creation" en Settings → Capabilities).
- **Claude Code**: copia la carpeta `planificador-calendario-secciones/` en `~/.claude/skills/`.

## Uso rápido
> Quiero mi plan de las próximas dos semanas separado por secciones y colores.

## Relacionada
`planificador-familiar`: organiza pareja o familia y usa esta skill para generar los .ics.

## Licencia
MIT (ver `LICENSE`).
