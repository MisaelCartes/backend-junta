# Generated by Django 5.1.1 on 2024-11-09 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_alter_user_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='mother_last_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
