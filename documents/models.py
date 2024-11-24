from django.db import models
from usuarios.models import User
from viviendas.models import FamilyMember
# Create your models here.

class CertificateRequest(models.Model):

    LEGALES = 1
    EDUCATIVOS = 2
    LABORALES = 3
    BANCARIOS = 4
    MEDICOS = 5
    GENERALES = 6
    REASON_REQUEST = [
        (LEGALES, 'Legales'),
        (EDUCATIVOS, 'Educativos'),
        (LABORALES, 'Laborales'),
        (BANCARIOS, 'Bancarios'),
        (MEDICOS, 'Médicos'),
        (GENERALES, 'que se estimen convenientes'),
    ]
    REASONS = [LEGALES,EDUCATIVOS,LABORALES,BANCARIOS,MEDICOS,GENERALES]

    STATUS_CHOICES = [
        ('requested', 'Solicitado'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]

    RESIDENCIA = 1
    TYPES_CERTIFICATES = [
        (RESIDENCIA, 'Certificado de residencia'),
    ]
    TYPES = [RESIDENCIA]
    # Claves foráneas
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)  # Solicitante (puede ser nulo)
    family_member = models.ForeignKey(FamilyMember, null=True, blank=True, on_delete=models.SET_NULL)  # Miembro de la familia (puede ser nulo)

    # Otros campos
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='requested')  # Estado de la solicitud
    reason_of_request = models.IntegerField(choices=REASON_REQUEST, default=GENERALES)
    type_of_certificate = models.IntegerField(choices=TYPES_CERTIFICATES, default=RESIDENCIA)
    creation_date= models.DateTimeField(auto_now_add=True)  # Fecha de creación de la solicitud
    rejection_reason = models.TextField(blank=True, null=True)  # Justificación en caso de rechazo
    certificate_file = models.FileField(blank=True, null=True)  # Archivo del certificado
    validity_date = models.DateTimeField(null=True, blank=True)  # Fecha de vigencia

    def __str__(self):
        if self.user:
            return f'Solicitud de {self.user.first_name} {self.user.last_name} - {self.get_status_display()}'
        elif self.family_member:
            return f'Solicitud de {self.family_member.first_name} {self.family_member.last_name} ({self.family_member.relationship}) - {self.get_status_display()}'
        return 'Solicitud sin solicitante ni miembro de la familia'