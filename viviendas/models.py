from django.db import models
from usuarios.models import User
from datetime import date

class Housing(models.Model):
    address = models.CharField(max_length=255)
    housing_type = models.CharField(max_length=50, choices=[('Casa', 'Casa'), ('Departamento', 'Departamento')], null=True, blank=True)
    latitude = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.CharField(max_length=255, null=True, blank=True)
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
    rut = models.CharField(unique=True,null=True, blank=True) 
    relationship = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    comuna = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.relationship})"

    def get_age(self):
        """Calcula la edad del miembro de la familia basada en la fecha de nacimiento."""
        today = date.today()
        age = today.year - self.date_of_birth.year
        # Ajustar la edad si el cumpleaños aún no ha ocurrido este año
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age