# Generated by Django 4.0.4 on 2022-06-18 21:18

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_iframe'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('BaseID', models.IntegerField()),
                ('Name', models.TextField()),
                ('Type', models.TextField()),
                ('User', models.CharField(max_length=100)),
                ('IP', models.TextField()),
                ('Date', models.DateTimeField(default=django.utils.timezone.now)),
                ('Request_Type', models.CharField(max_length=4)),
                ('Status', models.TextField()),
                ('Features', models.TextField()),
            ],
        ),
        migrations.AlterField(
            model_name='binary',
            name='status',
            field=models.CharField(choices=[('saved', 'saved'), ('extracted', 'extracted'), ('in_queue', 'in_queue'), ('in_test', 'in_test'), ('done', 'done'), ('done_error', 'done_error'), ('killed', 'killed'), ('ignored', 'ignored')], max_length=500),
        ),
    ]