# Generated by Django 5.1.7 on 2025-03-12 20:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0006_customuser_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
