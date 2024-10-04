from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, rut, full_name, email, phone_number, address, password=None, **extra_fields):
        if not rut:
            raise ValueError('The RUT field must be set')
        user = self.model(
            rut=rut,
            full_name=full_name,
            email=self.normalize_email(email),
            phone_number=phone_number,
            address=address,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, rut, full_name, email, phone_number, address, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(rut, full_name, email, phone_number, address, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(null=True, blank=True)  # Permitir nulos
    rut = models.IntegerField(unique=True)  # RUT único
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    role = models.IntegerField(null=True, blank=True)
    photo = models.FileField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'rut'
    REQUIRED_FIELDS = ['full_name', 'email', 'phone_number', 'address']

    def __str__(self):
        return self.full_name
        
class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    association = models.ForeignKey('juntas.NeighborAssociation', on_delete=models.CASCADE)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.association.name}"