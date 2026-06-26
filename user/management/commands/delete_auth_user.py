from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from access.models import Applications
from user.models import UserAccount


class Command(BaseCommand):
    help = (
        "Elimina un usuario Auth por email y, opcionalmente, ApplicationCode. "
        "Por defecto solo muestra un dry-run; requiere --confirm para borrar."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            required=True,
            help="Email exacto del usuario Auth a eliminar.",
        )
        parser.add_argument(
            "--application-code",
            help="Codigo de aplicacion esperado, por ejemplo REFAPART o MEXINGSOF.",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirma la eliminacion. Sin esta bandera no borra datos.",
        )

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        application_code = (options.get("application_code") or "").strip().upper()
        confirm = options["confirm"]

        queryset = UserAccount.objects.filter(email__iexact=email)
        application = None

        if application_code:
            application = Applications.objects.filter(Code=application_code).first()
            if application is None:
                raise CommandError(f"ApplicationCode no existe: {application_code}")
            queryset = queryset.filter(idApp=application.ApplicationID)

        users = list(queryset.order_by("id"))
        if not users:
            scope = f" en {application_code}" if application_code else ""
            raise CommandError(f"No existe usuario con email {email}{scope}.")

        if len(users) > 1:
            raise CommandError(
                "La busqueda devolvio mas de un usuario. Usa --application-code "
                "para evitar borrar el registro incorrecto."
            )

        user = users[0]
        user_application = Applications.objects.filter(ApplicationID=user.idApp).first()
        app_label = (
            f"{user_application.Code} ({user_application.Name})"
            if user_application
            else f"ApplicationId={user.idApp}"
        )

        self.stdout.write("Usuario localizado:")
        self.stdout.write(f"  Id: {user.id}")
        self.stdout.write(f"  Email: {user.email}")
        full_name = f"{user.first_name} {user.last_name}".strip() or "PENDIENTE_DE_DEFINIR"
        self.stdout.write(f"  Nombre: {full_name}")
        self.stdout.write(f"  Aplicacion: {app_label}")
        self.stdout.write(f"  Activo: {user.is_active}")
        self.stdout.write(f"  Staff: {user.is_staff}")
        self.stdout.write(f"  Superuser: {user.is_superuser}")

        if user.is_superuser:
            raise CommandError(
                "No se permite eliminar superusers con este comando. "
                "Desactivalo manualmente o usa un procedimiento administrativo."
            )

        if not confirm:
            self.stdout.write(
                self.style.WARNING(
                    "Dry-run: no se elimino nada. Repite con --confirm para borrar."
                )
            )
            return

        with transaction.atomic():
            deleted_count, deleted_by_model = user.delete()

        self.stdout.write(self.style.SUCCESS(f"Usuario eliminado: {email}"))
        self.stdout.write(f"Registros eliminados por cascada: {deleted_count}")
        for model_name, count in sorted(deleted_by_model.items()):
            self.stdout.write(f"  {model_name}: {count}")
