from django.db import models

# Create your models here.
from django.db import models
from django.utils.timezone import now
import django
from django.contrib.auth.models import User
from enum import Enum
import json


TeamType = [
    ('Major', 'Major'),
    ('Starter', 'Starter')
]

class Team(models.Model):
    name = models.CharField(null=False, blank=False, max_length=50, unique=True)
    password = models.CharField(null=False, blank=False, max_length=50)
    email = models.EmailField(null=False, blank=False, max_length=100)
    type = models.CharField(null=False, blank=False, max_length=20, choices=TeamType, default='Major')
    last_upload = models.DateTimeField(null=True)
    status = models.BooleanField(null=True)
    user = models.ForeignKey(User, models.SET_NULL, null=True)


PrivacyType = [
    ('Private', 'Private'),
    ('Public', 'Public')
]

class GameOutPuts(models.Model):
    generated_date = models.DateTimeField(default=django.utils.timezone.now)
    dir_path = models.CharField(null=False, blank=False, max_length=500)
    compressed_file_name = models.CharField(null=False, blank=False, max_length=500)
    type = models.CharField(max_length=20, choices=PrivacyType)
    files_name = models.CharField(max_length=2000)

    def set_files(self, files: list):
        self.files_name = json.dumps(files)

    def get_files(self):
        return json.loads(self.files_name)

    def is_private(self):
        return True if self.type == 'Private' else False


class GameLog(models.Model):
    generated_date = models.DateTimeField(default=django.utils.timezone.now)
    dir_path = models.CharField(null=False, blank=False, max_length=500)
    compressed_file_name = models.CharField(null=False, blank=False, max_length=500)
    rcg_name = models.CharField(null=False, blank=False, max_length=500)
    type = models.CharField(max_length=20, choices=PrivacyType)

    def is_private(self):
        return True if self.type == 'Private' else False


BinaryStatus = [
    ('saved', 'saved'),
    ('extracted', 'extracted'),
    ('in_queue', 'in_queue'),
    ('in_test', 'in_test'),
    ('done', 'done'),
    ('done_error', 'done_error'),
    ('killed' , 'killed'),
    ('ignored', 'ignored')
]


class Binary(models.Model):
    start_date = models.DateTimeField(default=django.utils.timezone.now)
    last_date = models.DateTimeField(default=django.utils.timezone.now)
    team = models.ForeignKey(Team, models.SET_NULL, null=True)
    dir_path = models.CharField(null=False, blank=False, max_length=500)
    file_name = models.CharField(null=False, blank=False, max_length=100)
    extracted_path = models.CharField(null=False, blank=False, max_length=500)
    status = models.CharField(null=False, blank=False, max_length=500, choices=BinaryStatus)
    error = models.CharField(null=False, blank=False, max_length=500)
    use = models.BooleanField(default=False)
    base_path = models.CharField(null=False, blank=False, max_length=500)
    done = models.BooleanField(default=False)
    job_id = models.CharField(null=False, blank=False, max_length=100)
    output = models.ForeignKey(GameOutPuts, models.SET_NULL, null=True)
    log = models.ForeignKey(GameLog, models.SET_NULL, null=True)
    std_out = models.TextField(null=False, blank=False)


class UploadStatus(models.Model):
    change_date = models.DateTimeField(default=django.utils.timezone.now)
    changer = models.ForeignKey(User, models.SET_NULL, null=True)
    status = models.BooleanField(default=True)


class LongTestStatus(models.Model):
    change_date = models.DateTimeField(default=django.utils.timezone.now)
    changer = models.ForeignKey(User, models.SET_NULL, null=True)
    status = models.BooleanField(default=True)

class Iframe(models.Model):
    name = models.CharField(null=False, blank=False, max_length=200, unique=True)
    url = models.TextField(null=False, blank=False)
    icon = models.CharField(null=False, blank=True, max_length=100)
    # status = models.BooleanField(null=True)

class EventStatus(str, Enum):
    IN_PROGRESS = "In-Progress"
    COMPLETE = "Complete"
    STARTING = "Starting"
    ERROR = "Error"
    FATAL = "Fatal"

class Event(models.Model):
    BaseID = models.IntegerField()
    Name = models.TextField(null=True, blank=True)
    Type = models.TextField(null=True, blank=True)
    User = models.CharField(max_length=100, null=True, blank=True)
    IP = models.TextField(null=True, blank=True)
    Date = models.DateTimeField(default=django.utils.timezone.now)
    Request_Type = models.CharField(max_length=4, null=True, blank=True)
    Status = models.TextField(null=True, blank=True)
    Features = models.TextField(null=True, blank=True)

    def set_features(self, features: dict):
        self.Features = json.dumps(features)

    def get_features(self):
        return json.loads(self.Features)

    def __str__(self):
        res = f'ID: {self.id}, Name: {self.Name}, Type: {self.Type}, ' \
              f'User: {self.User}, IP: {self.IP}, Date: {self.Date}, ' \
              f'Request_Type: {self.Request_Type}, Status: {self.Status}, Features: {self.Features}, ' \
              f'BaseID: {self.BaseID}'
        return res
