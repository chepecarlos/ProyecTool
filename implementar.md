# Plan de Implementación ProyecTool ↔ Notion

Avanzar en orden. Marcar cada ítem con ✅ al completarlo.

---

## ✅ Ya implementado

- `area add <url>` — extrae ID, consulta título en Notion, guarda url/id/titulo
- `area list` — muestra titulo, url e id del área
- `area remove` — elimina configuración del folder
- `proyecto add <url>` — igual que area add pero para proyectos
- `proyecto list` — muestra titulo, url e id del proyecto
- `proyecto remove` — elimina configuración del folder
- Validación mutua: un folder no puede ser área Y proyecto a la vez
- `notion config` — guarda token, db_proyectos, db_area

---

## Capa 1 — Leer estado desde Notion (solo GET)

- [ ] `proyecto estado <estado>` — cambia el estado del Kanban en Notion
      Estados válidos: idea, desarrollo, guion, grabado, edicion, tomab, revision, preparado, publicado, analizando
- [x] `proyecto info` — muestra estado, canal, asignado, cantidad de tareas pendientes
- [x] `area info` — muestra tipo (Area/Recurso), cantidad de proyectos, notas y recursos relacionados

---

## Capa 2 — Gestión de Tareas (GET + POST + PATCH)

Requiere estar dentro de un folder configurado como proyecto.

- [ ] `tarea list` — lista tareas del proyecto actual desde Notion
- [ ] `tarea add <nombre>` — crea tarea en Notion vinculada al proyecto, asignada a ChepeCarlos por defecto
- [ ] `tarea done <nombre>` — marca tarea como completada (Terminado = true)

---

## Capa 3 — Gestión de Notas

- [ ] `nota add <texto>` — crea nota en Notion vinculada al proyecto o área del folder
- [ ] `nota list` — lista notas del proyecto/área actual

---

## Capa 4 — Sync general

- [ ] `sync` — descarga snapshot del estado del proyecto/área desde Notion y lo guarda en `.proyectool/`

---

## Notas técnicas

**IDs de las bases de datos:**
- Tareas:         `19751238-fd9a-4ea2-b73b-794a9015daf0`
- Notas:          `1872c29b-b70c-4d21-99d7-7b29476a53f8`
- Proyectos:      `b03705b8-84cc-4044-8db3-c77165d3461b`
- Áreas/Recursos: `97e621bb-db85-4163-aa5f-4875fd65b65e`

**Reglas Notion:**
- Asignación por defecto: ChepeCarlos (sin preguntar)
- Siempre devolver URL al crear o modificar páginas

**Archivos clave:**
- `src/proyectool/notion_api.py` — funciones base para la API de Notion
- `src/proyectool/commands/area.py` — comandos de área
- `src/proyectool/commands/proyecto.py` — comandos de proyecto
- `src/proyectool/commands/tarea.py` — (por implementar)
- `~/.config/proyectool/notion.md` — token y configuración de Notion
