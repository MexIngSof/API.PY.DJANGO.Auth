# API.PY.DJANGO.Auth

Ser el owner de identidad de acceso del ecosistema: usuarios, credenciales, sesiones, MFA, recovery, roles, permisos y policy primitives.

**Primary classification:** `API_SHARED`

## Canonical responsibility

The canonical definition of this repository's purpose, ownership boundaries, allowed responsibilities and integration rules lives in `MexIngSof/Docs`.

Canonical profile: `repository-catalog/api/api-py-django-auth.md`

This README does not redefine domain ownership.

## Local operation

### Estandar local

- Nomenclatura actual: `API.PY.DJANGO.Auth`.
- Nomenclatura nueva para proyectos futuros: `API.PY.DJANGO.Auth`.
- Paquete de settings actual: `config`.
- Apps principales: `user`, `access`, `roles`.
- Base de datos: `auth`.
- Schema propietario: `"Auth"`.
- Archivo de entorno local: `.env.local`.
- Plantilla segura: `.env.local.example`.
- Dependencias: `requirements.txt`.

### Validacion local sin Docker

Auth no usa SQLite. Para ejecutar checks desde la carpeta del API, cargar una
configuracion PostgreSQL local antes de correr Django:

```powershell
cd Docker.API.PY\API.PY.DJANGO.Auth
Copy-Item .env.local.example .env.local
```

Despues completar en `.env.local`:

```text
AUTH_DB_PASSWORD=<password local de auth_user>
DJANGO_SECRET_KEY=<secret local de desarrollo>
```

Comando:

```powershell
python manage.py check
```

Tambien son validas estas variables equivalentes:

```text
DATABASE_URL
DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT
POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_HOST / POSTGRES_PORT
AUTH_DB_NAME / AUTH_DB_USER / AUTH_DB_PASSWORD
```

Si ninguna password esta configurada, el check falla de forma explicita para
evitar regresar a SQLite o usar una conexion falsa.

### Comandos basicos

```sh
python manage.py migrate
python manage.py runserver
```
