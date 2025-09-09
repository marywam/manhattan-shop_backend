from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # add extra fields if you want
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username

