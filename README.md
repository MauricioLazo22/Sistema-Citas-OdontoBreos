# Sistema de Citas Odontológicas — Grupo D

Módulo para la **Guerra de Testers** — TIyMS, Universidad Católica de Santa María.

- **Letra del grupo:** D
- **Tema:** Módulo de Citas / Reservas (Odontología)
- **Lenguaje:** Python 3.10+
- **Framework:** Django 5.2
- **Base de datos:** SQLite — archivo `citas.db` dentro del proyecto

## Integrantes

| Código | Nombre |
|---|---|
| 2023223181 | Lazo Franco, Mauricio Paolo |
| 2023223291 | Lonasco Sanamarina, Leonardo Olier |
| 2023224941 | Reaño Soto, Iván Edgardo |

## Funcionalidades implementadas

- **RF-01 Registrar Cita** — con todas las validaciones del PDF (DNI 8 dígitos, teléfono 9 dígitos, no domingos, fechas no pasadas, turnos disponibles, motivos válidos, no duplicados por DNI/fecha, no doble booking de turno).
- **RF-02 Consultar Cita** — búsqueda por DNI o por fecha, con resultados ordenados cronológicamente.
- **RF-03 Cancelar Cita** — flujo de búsqueda por ID + confirmación S/N, no permite cancelar dos veces ni fechas pasadas.

> Nota: **RF-04 (Reasignar)** y **RF-05 (Listar Agenda)** quedan pendientes para una segunda iteración.

## Cómo levantarlo

### 1. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Crear la base de datos y cargar dentistas iniciales

```bash
python manage.py migrate
python manage.py loaddata dentistas_iniciales
```

Esto genera el archivo `citas.db` en la raíz del proyecto.

> Para cargar también las 2 citas de ejemplo:
> ```bash
> python manage.py loaddata citas_demo
> ```

### 3. (Opcional) Crear superusuario para el panel de admin

```bash
python manage.py createsuperuser
```

### 4. Levantar el servidor

```bash
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ en el navegador.

- Menú principal: `/`
- Registrar Cita: `/registrar/`
- Consultar Cita: `/consultar/`
- Cancelar Cita: `/cancelar/`
- Panel de Admin: `/admin/`

## Estructura del proyecto

```
Sistema-Citas-OdontoVros/
├── manage.py
├── requirements.txt
├── README.md
├── citas.db                      ← se genera al correr migrate
├── odontovros/                   ← configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── citas/                        ← app principal
    ├── models.py                 ← Dentista, Cita
    ├── forms.py                  ← formularios con validaciones
    ├── validators.py             ← validaciones reutilizables
    ├── views.py                  ← lógica RF-01, RF-02, RF-03
    ├── urls.py
    ├── admin.py
    ├── migrations/
    ├── fixtures/
    │   ├── dentistas_iniciales.json
    │   └── citas_demo.json
    └── templates/citas/
        ├── base.html
        ├── menu.html
        ├── registrar.html
        ├── consultar.html
        └── cancelar.html
```

## Datos de prueba

| Tipo | Valor de ejemplo |
|---|---|
| Nombre paciente | `Ana Lopez Martinez` |
| DNI | `12345678` (exactamente 8 dígitos) |
| Teléfono | `987654321` (exactamente 9 dígitos) |
| Fecha | `15/06/2026` (DD/MM/AAAA, no domingo, no pasada) |
| Hora | `08:00`, `09:00`, `10:00`, `11:00`, `14:00`, `15:00`, `16:00`, `17:00` |
| Motivo | `Limpieza`, `Extraccion`, `Endodoncia`, `Ortodoncia`, `Revision general` |
| ID cita | Formato `CIT-YYYYMMDD-NNN` (ej. `CIT-20260605-001`) |

## Reglas de negocio (resumen)

- DNI inválido → "DNI invalido. Ingrese exactamente 8 digitos."
- Teléfono inválido → "Telefono invalido. Ingrese exactamente 9 digitos."
- Fecha pasada → "No se pueden registrar citas en fechas pasadas."
- Fecha en domingo → "No se atiende los domingos."
- Turno ya ocupado → "El turno seleccionado no esta disponible para ese dentista."
- Mismo paciente mismo día → "El paciente ya tiene una cita registrada para esa fecha."
- ID inválido → "Formato de ID invalido. Use CIT-YYYYMMDD-NNN."
- Cita ya cancelada → "La cita ya fue cancelada previamente."
- Cancelar fecha pasada → "No se pueden cancelar citas de fechas pasadas."

## Notas de limpieza

El repo contenía un scaffold inicial de Node/Express + Tailwind que fue reemplazado por este proyecto Python/Django. Si todavía ves los siguientes archivos/carpetas, puedes borrarlos manualmente — **no son usados por el sistema**:

```
node_modules/
package.json
package-lock.json
postcss.config.js
tailwind.config.js
src/
public/
```

## Pendientes para la siguiente entrega

- [ ] Implementar **RF-04 Reasignar Cita** (penalización -5 pts si no se entrega)
- [ ] Implementar **RF-05 Listar Agenda del Día / Rango de Fechas** (penalización -5 pts si no se entrega)
- [ ] Documentar casos de prueba para la fase de Testing
