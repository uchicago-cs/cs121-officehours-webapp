# Generated by Django 2.2.7 on 2019-11-17 23:25

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('officehours', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='additional_students',
            field=models.ManyToManyField(blank=True, related_name='additional_requests', to=settings.AUTH_USER_MODEL),
        ),
    ]