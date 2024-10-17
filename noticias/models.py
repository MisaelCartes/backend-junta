from django.db import models

# Create your models here.
class Noticia(models.Model):
    
    tittle = models.CharField(max_length=200, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True)
    date_upload = models.DateTimeField(auto_now_add=True)
    date_vigencia = models.DateTimeField(null=True, blank=True)  # Nuevo campo para la fecha de vigencia

    def __str__(self):
        return self.tittle