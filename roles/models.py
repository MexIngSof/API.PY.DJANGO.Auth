from django.conf import settings
from django.db import models


class Roles(models.Model):
    RoleID = models.AutoField(primary_key=True, db_column="Id")
    Name = models.CharField(max_length=100, unique=True, db_column="Name")
    Description = models.TextField(null=True, blank=True, db_column="Description")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."Roles"'

    def __str__(self):
        return self.Name


class UserRoles(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="UserId",
    )
    RoleID = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column="RoleId")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."UserRoles"'
        unique_together = ("UserID", "RoleID")

    def __str__(self):
        return f"{self.UserID.email} - {self.RoleID.Name}"
