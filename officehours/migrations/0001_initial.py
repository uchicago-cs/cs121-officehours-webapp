# Generated by Django 2.2.7 on 2019-11-17 18:11

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
            ],
            options={
                'abstract': False,
                'verbose_name_plural': 'users',
                'verbose_name': 'user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('ais_num', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('subject', models.CharField(max_length=4)),
                ('catalog_code', models.IntegerField(validators=[django.core.validators.MinValueValidator(10000), django.core.validators.MaxValueValidator(99999)])),
                ('name', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='CourseOffering',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archived', models.BooleanField(default=False)),
                ('state', models.PositiveIntegerField(choices=[(10, 'Open'), (20, 'Closed')], default=20)),
                ('url_slug', models.CharField(max_length=256, unique=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='officehours.Course')),
            ],
        ),
        migrations.CreateModel(
            name='Slot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('room', models.CharField(max_length=64)),
                ('course_offering', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='officehours.CourseOffering')),
            ],
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('service_start_time', models.TimeField(blank=True, null=True)),
                ('service_end_time', models.TimeField(blank=True, null=True)),
                ('state', models.PositiveIntegerField(choices=[(10, 'Pending'), (20, 'Scheduled'), (30, 'In Progress'), (40, 'Completed'), (50, 'No-show'), (60, 'Could not schedule'), (70, 'Cancelled'), (80, 'Invalid')], default=10)),
                ('type', models.PositiveIntegerField(choices=[(10, 'Regular'), (20, 'Quick Question')], default=10)),
                ('description', models.TextField()),
                ('actual_slot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assigned_slot', to='officehours.Slot')),
                ('additional_students', models.ManyToManyField(related_name='additional_requests', to=settings.AUTH_USER_MODEL)),
                ('course_offering', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='officehours.CourseOffering')),
                ('server', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assigned_requests', to=settings.AUTH_USER_MODEL)),
                ('slots', models.ManyToManyField(to='officehours.Slot')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Quarter',
            fields=[
                ('ais_num', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('year', models.PositiveIntegerField()),
                ('quarter', models.CharField(choices=[('aut', 'Autumn'), ('win', 'Winter'), ('spr', 'Spring'), ('sum', 'Summer')], max_length=3)),
            ],
            options={
                'unique_together': {('year', 'quarter')},
            },
        ),
        migrations.AddField(
            model_name='courseoffering',
            name='quarter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='officehours.Quarter'),
        ),
        migrations.AddField(
            model_name='courseoffering',
            name='servers',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='ActiveRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_offering', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='officehours.CourseOffering')),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='officehours.Request')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'course_offering')},
            },
        ),
        migrations.AddField(
            model_name='user',
            name='active_requests',
            field=models.ManyToManyField(blank=True, through='officehours.ActiveRequest', to='officehours.CourseOffering'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
        migrations.AlterUniqueTogether(
            name='courseoffering',
            unique_together={('course', 'quarter')},
        ),
    ]
