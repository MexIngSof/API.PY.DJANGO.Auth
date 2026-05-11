from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("Users must have an email address")

        id_app = kwargs.pop("idApp", None)
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **kwargs)

        if id_app is not None:
            user.idApp = id_app

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        user = self.create_user(email, password=password, **kwargs)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class UserAccount(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True, db_column="Id")
    password = models.CharField(max_length=128, db_column="Password")
    last_login = models.DateTimeField(null=True, blank=True, db_column="LastLogin")
    first_name = models.CharField(max_length=255, db_column="FirstName")
    last_name = models.CharField(max_length=255, db_column="LastName")
    email = models.EmailField(max_length=255, unique=True, db_column="Email")
    is_active = models.BooleanField(default=False, db_column="IsActive")
    is_staff = models.BooleanField(default=False, db_column="IsStaff")
    is_superuser = models.BooleanField(default=False, db_column="IsSuperuser")
    idApp = models.IntegerField(null=False, blank=False, db_column="ApplicationId")

    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "idApp"]

    class Meta:
        db_table = '"Auth"."UserAccounts"'

    def __str__(self):
        return self.email
