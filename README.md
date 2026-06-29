# API.PY.DJANGO.Auth

API Django responsable de autenticacion, usuarios, roles y permisos.

## Estandar local

- Nomenclatura actual: `API.PY.DJANGO.Auth`.
- Nomenclatura nueva para proyectos futuros: `API.PY.DJANGO.Auth`.
- Paquete de settings actual: `config`.
- Apps principales: `user`, `access`, `roles`.
- Base de datos: `auth`.
- Schema propietario: `"Auth"`.
- Archivo de entorno local: `.env.local`.
- Plantilla segura: `.env.local.example`.
- Dependencias: `requirements.txt`.

## Tablas propias de Auth

Las tablas de identidad, roles y permisos deben vivir en el schema `"Auth"`.
Las tablas de otros dominios no deben moverse a `"Auth"`; deben quedarse en
`public` si son tablas tecnicas compartidas o en su schema propietario
(`Catalog`, `Pricing`, `Sales`, etc.) cuando pertenezcan a una API de dominio.

Tablas Auth custom declaradas explicitamente en codigo:

```text
"Auth"."UserAccounts"
"Auth"."Roles"
"Auth"."UserRoles"
"Auth"."Modules"
"Auth"."Actions"
"Auth"."Permissions"
"Auth"."RolePermissions"
"Auth"."UserPermissions"
"Auth"."Applications"
"Auth"."ApplicationRoles"
"Auth"."ApplicationPermissions"
"Auth"."UserSessions"
"Auth"."UserDevices"
"Auth"."RefreshTokens"
"Auth"."PasswordHistory"
"Auth"."LoginAttempts"
"Auth"."MfaMethods"
"Auth"."RecoveryCodes"
"Auth"."AccessAuditEvents"
"Auth"."SocialProviders"
"Auth"."UserSocialAccounts"
"Auth"."SocialLoginAttempts"
"Auth"."ApplicationEmailSettings"
"Auth"."TransactionalEmailTemplates"
"Auth"."EmailDeliveryLogs"
```

Las tablas tecnicas de Django, Djoser, sesiones, social-auth y las tablas
intermedias generadas por `PermissionsMixin` se mantienen en `public`.
El `search_path` de Auth es `public,"Auth"` para que las tablas de framework no
se creen accidentalmente dentro del schema de dominio.

Las tablas y columnas custom publicables de Auth usan PascalCase. La PK de cada
tabla custom se publica como `Id`; las FK se publican como `UserId`, `RoleId`,
`PermissionId`, `ApplicationId`, etc.

## Redes sociales

Auth soporta actualmente login social con Google y Facebook:

```text
GOOGLE   -> backend google-oauth2
FACEBOOK -> backend facebook
```

Las tablas tecnicas de `social-auth-app-django` se conservan en `public`
(`social_auth_*`). Las tablas custom publicables de Auth para redes sociales son:

```text
"Auth"."SocialProviders"
"Auth"."UserSocialAccounts"
"Auth"."SocialLoginAttempts"
```

`SocialProviders` define proveedores permitidos. `UserSocialAccounts` normaliza
la cuenta social vinculada al usuario. `SocialLoginAttempts` audita intentos de
login social por proveedor y aplicacion.

## Djoser y correos transaccionales

Djoser cubre correctamente estos procesos base:

```text
POST /api/users/
POST /api/users/activation/
POST /api/users/resend_activation/
POST /api/users/reset_password/
POST /api/users/reset_password_confirm/
POST /api/users/set_password/
POST /api/users/reset_email/
POST /api/users/reset_email_confirm/
POST /api/users/set_email/
GET/PATCH /api/users/me/
GET/POST /api/auth/o/{provider}/
```

Auth agrega sobre Djoser una capa custom de plantillas por aplicacion:

```text
"Auth"."ApplicationEmailSettings"
"Auth"."TransactionalEmailTemplates"
"Auth"."EmailDeliveryLogs"
```

Las plantillas oficiales versionadas viven en:

```text
templates/auth_emails/<application_code>/<action>.html
```

Ejemplo REFAPART:

```text
templates/auth_emails/refapart/verify_account.html
templates/auth_emails/refapart/register.html
templates/auth_emails/refapart/password_reset.html
templates/auth_emails/refapart/password_changed.html
templates/auth_emails/refapart/email_reset.html
templates/auth_emails/refapart/email_changed.html
```

La tabla `"Auth"."TransactionalEmailTemplates"` no es la fuente principal de
HTML. Se conserva como fallback administrativo cuando no exista archivo
versionado para una aplicacion/accion. Auth no expone endpoints REST publicos
para consultar ni renderizar correos.

Si se inspecciona el fallback de BD, filtrar por:

```text
ApplicationId + ActionCode + LanguageCode + Channel
```

La configuracion visual/remitente por web vive en
`"Auth"."ApplicationEmailSettings"` y los envios quedan auditados en
`"Auth"."EmailDeliveryLogs"`.

Las clases custom de `auth.custom_email` son las que toman la decision. En cada
envio leen `ApplicationCode`, `application_code` o `X-Application-Code`,
resuelven la aplicacion activa y buscan primero el archivo HTML versionado de
esa aplicacion. Si no existe archivo, usan el fallback de
`"Auth"."TransactionalEmailTemplates"`. Si tampoco existe fallback de BD, usan
los templates locales de Djoser como ultimo recurso de compatibilidad.

La prioridad obligatoria es:

```text
FILE -> DB_FALLBACK -> DJOSER_FALLBACK
```

Si la aplicacion tiene `RedirectBaseUrl`, el enlace apunta al frontend de esa
web; si no, usa el dominio recibido por Djoser.

Acciones sembradas:

```text
REGISTER
VERIFY_ACCOUNT
RESEND_ACTIVATION
PASSWORD_RESET
PASSWORD_CHANGED
EMAIL_RESET
EMAIL_CHANGED
VERIFICATION_CODE
NEW_DEVICE_LOGIN
ACCOUNT_BLOCKED
ORGANIZATION_INVITATION
```

Procesos no cubiertos de forma nativa por Djoser:

- MFA y codigos de verificacion.
- Nuevo dispositivo.
- Cuenta bloqueada.
- Invitaciones a organizacion/proyecto.
- Alertas de riesgo.

Estos procesos ya tienen base documental/modelo de plantillas, pero requieren
flujos propios de Auth para dispararse automaticamente.

## Permisos y roles

- `Roles` define perfiles reutilizables.
- `Modules` define areas funcionales visibles o protegidas.
- `Actions` define acciones atomicas (`view`, `create`, `update`, `delete`,
  `approve`, etc.).
- `Permissions` une modulo y accion mediante un `Code` estable.
- `RolePermissions` concede permisos por rol.
- `UserPermissions` permite excepciones por usuario; `Allow=False` revoca un
  permiso heredado por rol.

## Endpoints administrativos

Las rutas de administracion viven bajo `/api/access/` y requieren usuario admin.

```text
/api/access/applications/
/api/access/roles/
/api/access/permissions/
/api/access/role-permissions/
/api/access/user-permissions/
/api/access/application-roles/
/api/access/application-permissions/
/api/access/devices/
/api/access/sessions/
/api/access/login-attempts/
/api/access/audit-events/
/api/access/social-providers/
/api/access/social-accounts/
/api/access/social-login-attempts/
```

`/api/access/me/permissions/` acepta `application_code` o
`X-Application-Code` para resolver permisos por aplicacion.

## Comandos basicos

```sh
python manage.py migrate
python manage.py runserver
```
