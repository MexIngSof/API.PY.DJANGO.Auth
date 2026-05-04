from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings  # 👈 importante

0
class Roles(models.Model):
    """
    Tabla: Roles
    -------------------------------------
    Equivalente SQL Server:
    CREATE TABLE Roles (
        RoleID INT IDENTITY PRIMARY KEY,
        Name NVARCHAR(100) UNIQUE,
        Description NVARCHAR(MAX),
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE()
    );
    -------------------------------------
    """

    RoleID = models.AutoField(primary_key=True, db_column='RoleID')
    Name = models.CharField(max_length=100, unique=True, db_column='Name')
    Description = models.TextField(null=True, blank=True, db_column='Description')
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    UpdatedAt = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'Roles'

    def __str__(self):
        return self.Name


class UserRoles(models.Model):
    """
    Tabla: UserRoles
    -------------------------------------
    Equivalente SQL Server:
    CREATE TABLE UserRoles (
        UserID INT NOT NULL,
        RoleID INT NOT NULL,
        PRIMARY KEY (UserID, RoleID),
        FOREIGN KEY (UserID) REFERENCES Users(UserID),
        FOREIGN KEY (RoleID) REFERENCES Roles(RoleID)
    );
    -------------------------------------
    """

    UserID = UserID = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='UserID')
    RoleID = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column='RoleID')
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    UpdatedAt = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'UserRoles'
        unique_together = ('UserID', 'RoleID')

    def __str__(self):
        return f"{self.UserID.username} - {self.RoleID.Name}"
