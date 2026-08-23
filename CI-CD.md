# CI/CD independiente de api-auth

Este repositorio es dueño de $image, de su Dockerfile y de
.github/workflows/pro-image.yml. El workflow completo vive y se ejecuta aquí:
checkout propio, dependencias, checks Django, migraciones pendientes, tests,
build no root, Trivy CRITICAL, push GHCR por digest y artifact component.env.

No usa workflows remotos de Docs ni consulta otro repositorio para ejecutar
CI. Docs sólo ensambla después el digest ya certificado. El artifact registra
IMAGE_KEY=API_AUTH_IMAGE, repositorio, SHA y SOURCE_BRANCH=pro.

Promoción: general -> dev -> pro; main sólo tras producción estable.
