from django.db import models

# Create your models here.
class User(models.Model):
    rut = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(max_length=128,unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    role = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.username


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    association = models.ForeignKey('juntas.NeighborAssociation', on_delete=models.CASCADE)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.association.name}"