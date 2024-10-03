from django.db import models
from usuarios.models import User

class Housing(models.Model):
    address = models.CharField(max_length=255)
    housing_type = models.CharField(max_length=50, choices=[('Casa', 'Casa'), ('Departamento', 'Departamento')])

    def __str__(self):
        return self.address


class Family(models.Model):
    housing = models.ForeignKey(Housing, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    family_name = models.CharField(max_length=255,null=True, blank=True)

    def __str__(self):
        return self.family_name


class FamilyMember(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.relationship})"