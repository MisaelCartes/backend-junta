# Generated by Django 5.1.1 on 2024-10-31 19:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('viviendas', '0003_familymember_rut'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CertificateRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('requested', 'Solicitado'), ('approved', 'Aprobado'), ('rejected', 'Rechazado')], default='requested', max_length=10)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('rejection_reason', models.TextField(blank=True, null=True)),
                ('certificate_file', models.FileField(blank=True, null=True, upload_to='')),
                ('family_member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='viviendas.familymember')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]