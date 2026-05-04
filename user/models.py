# Importación del módulo de modelos de Django para crear modelos personalizados
from django.db import models

# Importaciones necesarias para crear un modelo de usuario personalizado
from django.contrib.auth.models import (
    BaseUserManager,     # Clase base para crear usuarios y superusuarios
    AbstractBaseUser,    # Clase base para el modelo de usuario personalizado
    # Proporciona campos y métodos relacionados con permisos (como is_superuser)
    PermissionsMixin
)


# Clase que define el administrador del modelo de usuario personalizado
class UserAccountManager(BaseUserManager):

    def create_user(self, email, password=None, **kwargs):
        """
        Crea y guarda un usuario con email, password,
        y campos adicionales como idApp.
        """
        if not email:
            raise ValueError("Users must have an email address")

        # Normalización
        email = self.normalize_email(email).lower()

        # Extraer idApp si viene
        idApp = kwargs.pop("idApp", None)

        # Crear usuario
        user = self.model(
            email=email,
            **kwargs
        )

        # Si viene idApp, asignarlo
        if idApp is not None:
            user.idApp = idApp

        # Guardar password
        user.set_password(password)

        # Guardarlo en DB
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        user = self.create_user(
            email,
            password=password,
            **kwargs
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class UserAccount(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    email = models.EmailField(max_length=255, unique=True)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # ID numérico de la aplicación
    idApp = models.IntegerField(null=False, blank=False, db_column="idApp")

    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "idApp"]

    def __str__(self):
        return self.email

    # Métodos opcionales de permisos personalizados (comentados por ahora)
    """
    def has_perm(self, perm, obj=None):
        "¿Tiene este usuario un permiso específico?"
        return True  # Respuesta simple: siempre sí (no recomendado en producción)

    def has_module_perms(self, app_label):
        "¿Tiene el usuario permisos para ver la app `app_label`?"
        return True  # Respuesta simple: siempre sí

    @property
    def is_staff(self):
        "¿Es el usuario parte del staff?"
        return self.is_admin  # En este ejemplo se considera que todos los admins son staff
    """
