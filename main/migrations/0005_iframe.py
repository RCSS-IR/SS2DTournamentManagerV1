# Generated by Django 4.0.4 on 2022-06-08 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_uploadstatus'),
    ]

    operations = [
        migrations.CreateModel(
            name='Iframe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('url', models.TextField()),
                ('icon', models.CharField(blank=True, max_length=100)),
            ],
        ),
    ]
