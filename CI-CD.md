# CI/CD independiente de api-auth

Este repositorio es dueño de su imagen, de su `Dockerfile` y de
`.github/workflows/pro-image.yml`. Las validaciones rutinarias se ejecutan
localmente; GitHub-hosted Actions queda reservado a operaciones productivas
manuales desde `pro`.

Promoción: `general -> dev -> pro`; `main` sólo después de producción
verificada.

## AWS SES de Auth

Auth consume los nombres canónicos:

- variables: `AUTH_AWS_SES_REGION_NAME`, `AUTH_AWS_SES_FROM_EMAIL`,
  `AUTH_EMAIL_RETURN_PATH` (opcional) y `AUTH_EMAIL_PROVIDER`;
- secrets: `AUTH_AWS_SES_ACCESS_KEY_ID` y
  `AUTH_AWS_SES_SECRET_ACCESS_KEY`.

El único GitHub Environment activo para esta configuración productiva es
`production`.

Desde la raíz del workspace, en PowerShell 7 con GitHub CLI autenticado:

```powershell
pwsh -File .\Docker.API.PY\API.PY.DJANGO.Auth\scripts\Set-AwsSesEnvironment.ps1
```

Sin `-Apply` el script sólo verifica presencia/nombres en
`MexIngSof/API.PY.DJANGO.Auth / production`; no lee valores de secrets.

La escritura es explícita:

```powershell
pwsh -File .\Docker.API.PY\API.PY.DJANGO.Auth\scripts\Set-AwsSesEnvironment.ps1 -Apply
```

El script solicita variables una por una y secrets con
`Read-Host -AsSecureString`; los secrets se entregan a `gh secret set` por
stdin y no deben guardarse en archivos, argumentos, artifacts ni documentación.

## Estado y límite de certificación

La evidencia histórica de septiembre de 2026 confirmó una carga bajo el
Environment que estaba vigente entonces. Esa evidencia queda **superseded** por
el modelo production-only y no certifica presencia actual en `production`.

Estado fuente actual:

```text
AUTH_SES_CANONICAL_NAMES = SOURCE_ALIGNED
AUTH_SES_TARGET_ENVIRONMENT = production
AUTH_SES_PRODUCTION_SECRET_PRESENCE = NOT_VERIFIED_HERE
AUTH_SES_REAL_EMAIL_DELIVERY = NOT_VERIFIED_HERE
```

No se considera cerrado el runtime SES hasta verificar, en una operación
autorizada fuera de este bloque de source remediation, la presencia de las
entradas en `production` y un envío/recepción real sin exponer credenciales.
