from django.db import models
from usuarios.models import User

class NeighborAssociation(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    territory_id = models.IntegerField()

    def __str__(self):
        return self.name
