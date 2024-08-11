# Generated by Django 4.0 on 2022-05-17 02:01

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='GameLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generated_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('dir_path', models.CharField(max_length=500)),
                ('compressed_file_name', models.CharField(max_length=500)),
                ('rcg_name', models.CharField(max_length=500)),
                ('type', models.CharField(choices=[('Private', 'Private'), ('Public', 'Public')], max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='GameOutPuts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generated_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('dir_path', models.CharField(max_length=500)),
                ('compressed_file_name', models.CharField(max_length=500)),
                ('type', models.CharField(choices=[('Private', 'Private'), ('Public', 'Public')], max_length=20)),
                ('files_name', models.CharField(max_length=2000)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('password', models.CharField(max_length=50, unique=True)),
                ('email', models.EmailField(max_length=100)),
                ('last_upload', models.DateTimeField(null=True)),
                ('status', models.BooleanField(null=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
        ),
        migrations.CreateModel(
            name='Binary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('dir_path', models.CharField(max_length=500)),
                ('file_name', models.CharField(max_length=100)),
                ('extracted_path', models.CharField(max_length=500)),
                ('status', models.CharField(choices=[('saved', 'saved'), ('extracted', 'extracted'), ('in_queue', 'in_queue'), ('in_test', 'in_test'), ('done', 'done'), ('done_error', 'done_error')], max_length=500)),
                ('error', models.CharField(max_length=500)),
                ('use', models.BooleanField(default=False)),
                ('base_path', models.CharField(max_length=500)),
                ('done', models.BooleanField(default=False)),
                ('job_id', models.CharField(max_length=100)),
                ('log', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.gamelog')),
                ('output', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.gameoutputs')),
                ('team', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.team')),
            ],
        ),
    ]
