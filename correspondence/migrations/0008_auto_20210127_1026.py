# Generated by Django 3.1.4 on 2021-01-27 10:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('correspondence', '0007_radicate_creator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='radicate',
            name='creator',
            field=models.ForeignKey(default=False, on_delete=django.db.models.deletion.CASCADE, related_name='radicates', to=settings.AUTH_USER_MODEL),
        ),
    ]
