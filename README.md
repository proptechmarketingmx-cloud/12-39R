# CRM Inmobiliario

Resumen del proyecto, estado actual, funciones implementadas y pasos
recomendados para instalación y actualización.

## Objetivo

Aplicación de escritorio (Tkinter) para gestión inmobiliaria: clientes,
propiedades, autenticación y flujos básicos de CRM. El repositorio contiene
un prototipo funcional y una base organizada para migrar a una solución
productiva (BD MySQL/MariaDB, despliegue y empaquetado).

## Estado actual (resumen)

- Login visual completo en `ui/login_window.py`, integrado con un
	`auth_manager` de prueba en `modules/auth.py` (usuario por defecto
	`admin` / `admin123`).
- Diálogo modal para cambio de contraseña en `ui/change_password_dialog.py`.
- Ventana principal demo `ui/main_window.py` con menú para abrir:
	- Formulario de clientes `ui/clientes/cliente_form.py` (crear/editar,
		validaciones CURP/teléfonos, cálculo de edad y scoring, persistencia
		fallback en `database/seeds/clientes_store.json`).
	- Formulario de propiedades `ui/propiedades/propiedad_form.py` (3 pestañas,
		gestión demo de fotos, persistencia fallback en
		`database/seeds/propiedades_store.json`).
- Persistencia de desarrollo: módulos `modules/clientes.py` y
	`modules/propiedades.py` soportan operaciones básicas y sirven como
	punto de migración a una base de datos real.
- Tests unitarios (pytest) añadidos bajo `tests/` y `requirements.txt`
	contiene dependencias de desarrollo.

## Archivos clave

- `main.py` — punto de entrada (invoca GUI).
- `ui/login_window.py` — ventana de login (centrada 400x500, binds,
	validaciones, integración con `auth_manager`).
- `ui/change_password_dialog.py` — diálogo modal para cambio de contraseña.
- `ui/main_window.py` — ventana principal demo con menú y acceso a módulos.
- `ui/clientes/cliente_form.py` — formulario clientes (5 pestañas).
- `ui/propiedades/propiedad_form.py` — formulario propiedades.
- `modules/auth.py` — gestor de autenticación de desarrollo (bcrypt + store
	JSON).
- `modules/clientes.py`, `modules/propiedades.py` — persistencia simple y
	funciones auxiliares.
- `database/seeds/*.json` — stores JSON de ejemplo para pruebas.

## Arquitectura

La aplicación sigue una arquitectura ligera en capas pensada para:
- Separar la interfaz de usuario (UI) de la lógica de negocio y de la
	persistencia.
- Permitir un desarrollo rápido con stores JSON y una migración clara a
	MySQL/MariaDB.

Capas y componentes principales:
- Capa UI (`ui/`): widgets y ventanas de Tkinter. Contiene vistas,
	formularios y widgets reutilizables (`ui/login_window.py`,
	`ui/main_window.py`, `ui/clientes/`, `ui/propiedades/`).
- Lógica de dominio (`modules/`): controladores y adaptadores que
	implementan reglas de negocio y CRUD. Ejemplos: `modules/auth.py`,
	`modules/clientes.py`, `modules/propiedades.py`, (nuevo)
	`modules/asesores.py`.
- Persistencia (`database/`): adaptadores de acceso a BD y scripts de
	migración. `database/db.py` expone `get_connection()`; `database/schema.sql`
	define tablas principales.
- Utilidades (`utils/`): validadores y helpers (`utils/validators.py`).
- Scripts y DevOps (`scripts/`): build, migración y empaquetado
	(`scripts/build_exe.ps1`, `scripts/installer.iss`,
	`scripts/migrate_json_to_mysql.py`).

Modelo de datos (tablas principales en `schema.sql`):
- `asesores` (id, username, password_hash, rol, nombres, apellidos, activo,
	requiere_cambio_password, ultimo_acceso)
- `clientes` (id, nombres, apellidos, curp, telefono_principal, estado_cliente,
	fecha_registro, scoring, asesor_id, ...)
- `propiedades` (id, titulo, descripcion, precio, metros, ubicacion, ...)
- `visitas` / `interacciones` (registro de interacciones cliente↔propiedad)
- `audits` / `logs` (registro de operaciones críticas)

Flujo de autenticación y permisos:
- `ui/login_window` invoca `modules.auth.auth_manager.login()`.
- `modules/auth` se conecta a la tabla `asesores` para validar credenciales
	y exponer `get_current_user()` / `is_admin()` para la UI.
- Las operaciones de escritura (crear cliente, editar propiedad) deben
	validar `auth_manager.get_current_user()` y verificar permisos.

Estrategia de migración JSON → MySQL:
1. Usar scripts en `scripts/migrate_json_to_mysql.py` para importar los
	 stores `database/seeds/*.json` a tablas SQL.
2. Actualizar módulos en `modules/` para usar `database/db.get_connection()`
	 y queries parametrizados.
3. Añadir transacciones y tests de integración para cada operación.

Consideraciones de seguridad y producción:
- No guardar credenciales en `config.py`; usar variables de entorno o
	un `.env` con permisos restringidos.
- Hashear contraseñas con `bcrypt` (ya usado en `modules/auth.py`).
- Implementar backups y migraciones versionadas (Flyway/ Alembic para
	SQL si se necesita).

## Estructura de carpetas

Vista rápida de la organización principal del repositorio:

```
12-39R/ (root)
├─ README.md
├─ requirements.txt
├─ main.py
├─ config/
│  └─ config.py
├─ database/
│  ├─ db.py
│  ├─ schema.sql
│  └─ seeds/
│     ├─ clientes_store.json
│     └─ propiedades_store.json
├─ modules/
│  ├─ auth.py
│  ├─ clientes.py
│  ├─ propiedades.py
│  └─ asesores.py (planned)
├─ ui/
│  ├─ login_window.py
│  ├─ change_password_dialog.py
│  ├─ main_window.py
│  ├─ dashboard/
│  │  └─ kpi_cards.py (planned)
│  ├─ clientes/
│  │  ├─ cliente_form.py
│  │  └─ cliente_lista.py (planned)
│  └─ propiedades/
│     └─ propiedad_form.py
├─ ui/widgets/
│  ├─ phone_entry.py
│  └─ money_entry.py
├─ utils/
│  └─ validators.py
├─ scripts/
│  ├─ build_exe.ps1
│  ├─ installer.iss
│  └─ migrate_json_to_mysql.py
├─ static/ (assets)
├─ tests/
└─ docs/
```

Los archivos marcados como `(planned)` aún están por implementar o
refinar; la estructura sirve como guía para navegación y futuras tareas.


## Cómo ejecutar en desarrollo (Windows)

1. Activar el entorno virtual (desde la raíz del repo):

```powershell
& .venv\Scripts\Activate.ps1
```

2. Ejecutar la ventana de login (modo prueba):

```powershell
python -m ui.login_window
```

Credenciales por defecto: `admin` / `admin123` (se solicita cambio de
contraseña en primer inicio).

## Tests

Instalar dependencias de desarrollo y ejecutar `pytest`:

```powershell
& .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest -q
```

Nota: los tests actuales son unitarios para los módulos de persistencia
de ejemplo.

## Opciones de empaquetado e instalación (recomendación)

1. Empaquetado rápido (recomendado para distribución interna):
	 - Usar PyInstaller para generar `EXE` y luego crear un instalador con
		 Inno Setup o NSIS.
	 - Comandos básicos:

```powershell
& .venv\Scripts\Activate.ps1
python -m pip install pyinstaller
pyinstaller --onefile --windowed --name CRMInmobiliario main.py
```

2. Instalación simple (repositorio): clonar repo, activar venv,
	 instalar `requirements.txt` y ejecutar `python main.py` o el exe.

3. Actualizaciones:
	 - Opción A (sencilla): mantener el repo en el equipo y actualizar con
		 `git pull`, reinstalar dependencias y reiniciar la app.
	 - Opción B (robusta): publicar releases (GitHub Releases) y añadir un
		 componente `updater` que descargue/verifique el EXE y reemplace la
		 versión local. Requiere firmar y validar hashes para seguridad.

4. Distribuidores del sistema (opcional): crear paquetes Chocolatey o
	 Winget para actualizaciones centralizadas en Windows.

### Decisión de distribución (actual)

Se eligió el flujo siguiente como estrategia principal de distribución:

- PyInstaller: generar `EXE` autónomo para Windows (`--onefile --windowed`).
- Inno Setup: crear un instalador profesional que incluya el EXE,
	accesos directos y desinstalador.
- Publicar en GitHub Releases: automatizar builds y subir los assets
	(EXE / installer) para que los usuarios descarguen versiones firmadas.
- Auto-updater (opcional): componente que consulte Releases y actualice
	el ejecutable localmente verificando hash/firmas.

He añadido scripts base para facilitar este flujo en `scripts/`:

- `scripts/build_exe.ps1` — PowerShell que ejecuta PyInstaller, limpia
	builds previos e incluye datos estáticos/seed cuando existen.
- `scripts/installer.iss` — plantilla Inno Setup para empaquetar
	`dist\CRMInmobiliario.exe` en un instalador Windows.

Comandos rápidos para crear el EXE localmente:

```powershell
& .venv\Scripts\Activate.ps1
python -m pip install pyinstaller
.\scripts\build_exe.ps1
```

Después de generar `dist\CRMInmobiliario.exe`, abre Inno Setup
y compila `scripts\installer.iss` (ajusta rutas si es necesario).

Si quieres automatizar la publicación en GitHub, puedo añadir un
workflow de GitHub Actions que ejecute `scripts/build_exe.ps1` en un
runner Windows y suba los artefactos a un Release.

## Consideraciones para producción

- Migrar `modules/*` para usar una base de datos MySQL/MariaDB (`database/db.py`).
- Añadir manejo de usuarios, roles y permisos con audit logging.
- Respaldos, migration scripts y gestión de configuración (archivo
	`.env`).
- Firmado de ejecutables y establecimiento de canal de releases para
	actualizaciones seguras.

## Estado pendiente / próximos pasos (priorizados)

1. Implementar diálogo de cambio de contraseña completo (hecho).
2. Conexión a MySQL/MariaDB y migración de los módulos de persistencia.
3. Dashboard y menú lateral con vistas (propiedades, clientes, visitas).
4. Empaquetado con PyInstaller + instalador Inno Setup.
5. Implementar mecanismo de actualización automática (GitHub Releases
	 + updater) o publicar en Chocolatey/Winget.

## Cómo contribuir

- Abrir issues para mejoras y bugs.
- Crear ramas feature/* y abrir pull requests con pruebas cuando aplique.

---

Para cualquier consulta o si quieres que implemente el empaquetado
automático y un `scripts/build_exe.ps1`, dime y lo preparo con los
scripts y el `INSTALL.md` correspondiente.

