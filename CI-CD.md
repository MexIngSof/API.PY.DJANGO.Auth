# CI/CD de Auth

Este repositorio es dueño de ghcr.io/mexingsof/api-py-django-auth.
pro-image.yml sólo corre desde pro: instala dependencias, ejecuta Django
check, detección de migraciones pendientes y tests; después construye este
Dockerfile, bloquea vulnerabilidades CRITICAL con Trivy y publica por digest.

El artifact usa $key. El contenedor corre como UID 10001, expone sólo 8000
en la red interna y acepta serve, migrate --noinput o check. Docs ensambla
el digest; este repo no despliega ni conoce secretos del VPS.

Promoción: general -> dev -> pro; main sólo tras producción estable.
