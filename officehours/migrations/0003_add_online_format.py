# Generated by Django 2.2.13 on 2020-10-03 22:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('officehours', '0002_additional_students_blank'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='zoom_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='slot',
            name='format',
            field=models.PositiveIntegerField(choices=[(10, 'Online'), (20, 'In-person')], default=20),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='slot',
            name='room',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
