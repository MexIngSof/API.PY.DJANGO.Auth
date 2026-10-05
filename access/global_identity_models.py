from django.conf import settings
from django.db import models
from django.db.models import Q

from access.models import Applications


class GlobalIdentities(models.Model):
    GlobalIdentityID = models.BigAutoField(primary_key=True, db_column="Id")
    IsActive = models.BooleanField(default=True, db_column="IsActive")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        app_label = "access"
        db_table = '"Auth"."GlobalIdentities"'

    def __str__(self):
        return f"global identity {self.GlobalIdentityID}"


class GlobalIdentityAccounts(models.Model):
    GlobalIdentityAccountID = models.BigAutoField(primary_key=True, db_column="Id")
    GlobalIdentityID = models.ForeignKey(
        GlobalIdentities,
        on_delete=models.CASCADE,
        db_column="GlobalIdentityId",
        related_name="Accounts",
    )
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="UserId",
        related_name="GlobalIdentityLinks",
    )
    ApplicationID = models.ForeignKey(
        Applications,
        on_delete=models.CASCADE,
        db_column="ApplicationId",
        related_name="GlobalIdentityAccounts",
    )
    IsVerified = models.BooleanField(default=False, db_column="IsVerified")
    IsActive = models.BooleanField(default=False, db_column="IsActive")
    VerifiedAt = models.DateTimeField(null=True, blank=True, db_column="VerifiedAt")
    UnlinkedAt = models.DateTimeField(null=True, blank=True, db_column="UnlinkedAt")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        app_label = "access"
        db_table = '"Auth"."GlobalIdentityAccounts"'
        constraints = [
            models.UniqueConstraint(
                fields=("UserID",),
                condition=Q(IsActive=True),
                name="uq_global_identity_active_user",
            ),
            models.UniqueConstraint(
                fields=("GlobalIdentityID", "ApplicationID"),
                condition=Q(IsActive=True),
                name="uq_global_identity_active_application",
            ),
        ]
        indexes = [
            models.Index(fields=("UserID", "IsActive"), name="ix_global_identity_user_active"),
            models.Index(
                fields=("GlobalIdentityID", "ApplicationID", "IsActive"),
                name="ix_global_identity_app_active",
            ),
        ]

    def __str__(self):
        return f"{self.GlobalIdentityID_id} -> {self.UserID_id} ({self.ApplicationID_id})"
