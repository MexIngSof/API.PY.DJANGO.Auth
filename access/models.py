from django.db import models
from roles.models import Roles
from django.conf import settings


class Modules(models.Model):
    """
    Tabla: Modules
    Módulos visibles en el dashboard.
    """

    ModuleID = models.AutoField(primary_key=True, db_column='ModuleID')
    Name = models.CharField(max_length=100, unique=True, db_column='Name')
    Description = models.TextField(blank=True, null=True, db_column='Description')

    # 🔥 CAMPOS NECESARIOS PARA QUE EL FRONTEND PINTE EL SIDEBAR
    Code = models.CharField(max_length=100, unique=True, db_column="Code")
    Path = models.CharField(max_length=255, db_column="Path")

    CreatedAt = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    UpdatedAt = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'Modules'

    def __str__(self):
        return self.Name


class Actions(models.Model):
    """
    Tabla: Actions
    Acción dentro de un módulo (create, edit, view, run_ai, etc.)
    """

    ActionID = models.AutoField(primary_key=True, db_column='ActionID')
    Name = models.CharField(max_length=50, unique=True, db_column='Name')
    Description = models.TextField(blank=True, null=True, db_column='Description')
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    UpdatedAt = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'Actions'

    def __str__(self):
        return self.Name


class Permissions(models.Model):
    """
    Tabla: Permissions
    Permisos del sistema (MODULE + ACTION)
    """

    PermissionID = models.AutoField(primary_key=True, db_column='PermissionID')
    ModuleID = models.ForeignKey(Modules, on_delete=models.CASCADE, db_column='ModuleID')
    ActionID = models.ForeignKey(Actions, on_delete=models.CASCADE, db_column='ActionID')
    Code = models.CharField(max_length=150, unique=True, db_column='Code')

    CreatedAt = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    UpdatedAt = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'Permissions'

    def __str__(self):
        return self.Code


class RolePermissions(models.Model):
    """
    Relación Rol ↔ Permisos
    """

    RoleID = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column='RoleID')
    PermissionID = models.ForeignKey(Permissions, on_delete=models.CASCADE, db_column='PermissionID')

    CreatedAt = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    UpdatedAt = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'RolePermissions'
        unique_together = ('RoleID', 'PermissionID')

    def __str__(self):
        return f"{self.RoleID.Name} → {self.PermissionID.Code}"


class UserPermissions(models.Model):
    """
    Permisos que se añaden o revocan a un usuario individual.
    """

    UserID = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='UserID')
    PermissionID = models.ForeignKey(Permissions, on_delete=models.CASCADE, db_column='PermissionID')
    Allow = models.BooleanField(default=True, db_column='Allow')
    Reason = models.CharField(max_length=255, null=True, blank=True, db_column='Reason')

    CreatedAt = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    UpdatedAt = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'UserPermissions'
        unique_together = ('UserID', 'PermissionID')

    def __str__(self):
        status = "✅" if self.Allow else "❌"
        return f"{self.UserID.username} {status} {self.PermissionID.Code}"
