# Generated by Django 4.0.4 on 2022-05-17 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_binary_std_out'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='password',
            field=models.CharField(max_length=50),
        ),
    ]