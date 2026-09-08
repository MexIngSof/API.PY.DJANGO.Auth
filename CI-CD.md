# CI/CD independiente de api-auth

Este repositorio es dueño de $image, de su Dockerfile y de
.github/workflows/pro-image.yml. El workflow completo vive y se ejecuta aquí:
checkout propio, dependencias, checks Django, migraciones pendientes, tests,
build no root, Trivy CRITICAL, push GHCR por digest y artifact component.env.

No usa workflows remotos de Docs ni consulta otro repositorio para ejecutar
CI. Docs sólo ensambla después el digest ya certificado. El artifact registra
IMAGE_KEY=API_AUTH_IMAGE, repositorio, SHA y SOURCE_BRANCH=pro.

Promoción: general -> dev -> pro; main sólo tras producción estable.

## Configurar AWS SES de Auth

Desde la raiz del workspace, en PowerShell 7 con GitHub CLI autenticado:

```powershell
pwsh -File .\Docker.API.PY\API.PY.DJANGO.Auth\scripts\Set-AwsSesEnvironment.ps1 -Apply
```

Destino fijo: `MexIngSof/API.PY.DJANGO.Auth`, Environment `staging-pro-deploy`.
Requiere permisos para administrar sus variables y secretos y que el Environment
ya exista. El script pregunta un valor por vez:

| Nombre | Tipo | Valor |
|---|---|---|
| AUTH_AWS_SES_REGION_NAME | Variable | Region de SES |
| AUTH_AWS_SES_FROM_EMAIL | Variable | Remitente verificado en SES |
| AUTH_EMAIL_RETURN_PATH | Variable opcional | Direccion de retorno |
| AUTH_EMAIL_PROVIDER | Variable | `ses` |
| AUTH_AWS_SES_ACCESS_KEY_ID | Secret | Access key ID de IAM para SES |
| AUTH_AWS_SES_SECRET_ACCESS_KEY | Secret | Secret access key correspondiente |

Enter conserva una variable existente u omite el return path ausente. Para
reemplazar un secreto existente se escribe `ACTUALIZAR`. Las credenciales se
introducen en el prompt oculto de PowerShell (`Read-Host -AsSecureString`); no se guardan en archivos ni se pasan
como argumentos. No pegar credenciales en el chat. Las escrituras son por entrada:
si falla a mitad, las anteriores permanecen y se puede reejecutar conservandolas.

Para comprobar despues, sin modificar GitHub:

```powershell
pwsh -File .\Docker.API.PY\API.PY.DJANGO.Auth\scripts\Set-AwsSesEnvironment.ps1
```

El verificador muestra solo nombres/presencia y comprueba que el proveedor sea
`ses`; falla si faltan entradas obligatorias. La existencia de un Secret no
permite verificar su valor ni los permisos de AWS. Falta el despliegue autorizado
y una prueba real de correo para certificar funcionamiento.

Revision 2026-09-08: los configuradores generales de Docs no cubrian esta carga
interactiva. El workflow usaba AWS_SES_REGION/AWS_ACCESS_KEY_ID, nombres que el
resolver auth/email_settings.py no consume. Se alinearon las referencias GitHub
y las claves materializadas con los nombres AUTH_* de esta tabla. El cambio del
workflow es local y requiere publicacion/promocion antes de desplegar. Se conserva
el modo externo diferido existente; no se declara certificacion SES por cargar
variables. En la consulta inicial estaban presentes las cuatro variables y
faltaban ambos Secrets de SES.

Correccion de captura interactiva: el script envia el secreto a gh por stdin y
cierra la entrada explicitamente; Enter finaliza la captura. La espera de GitHub
se limita a 60 segundos y un fallo no se declara exitoso.

### Estado confirmado al 2026-09-08

**COMPLETADO: carga y verificacion de configuracion AWS SES en GitHub.**

El owner cargo los valores mediante `scripts/Set-AwsSesEnvironment.ps1 -Apply`.
Una consulta posterior independiente con el mismo script, sin `-Apply`, confirmo
las cuatro variables y los dos Secrets de la tabla en
`MexIngSof/API.PY.DJANGO.Auth`, Environment `staging-pro-deploy`, y el proveedor
`AUTH_EMAIL_PROVIDER=ses`. No se leyeron ni documentaron valores de Secrets.
La ausencia inicial de credenciales queda resuelta; no queda pendiente su carga.

**PENDIENTE_PRIORIZADO: despliegue y prueba real de correo.**

1. Publicar y promover el workflow con el mapeo AUTH_* corregido; el cambio sigue local.
2. Desplegar Auth en staging con esa version y comprobar que recibe su configuracion
   de SES sin imprimir credenciales.
3. Ejecutar un flujo real de recuperacion de contrasena con una cuenta de prueba
   controlada y verificar que usa SES, que AWS acepta el envio y que el mensaje
   llega al buzon destinatario.
4. Verificar que el enlace recibido permite completar la recuperacion y registrar
   fecha, version desplegada y resultado, sin guardar claves ni tokens de recuperacion.

Criterio de cierre: evidencia de envio y recepcion reales y del flujo de recuperacion
completado en staging. Presencia en GitHub, health del servicio o salida por consola
no sustituyen esta prueba. Hasta entonces, la configuracion esta realizada y
verificada, pero el funcionamiento de SES permanece pendiente de prueba.
