from django.db import models

class User(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('pertner', 'Partner'),
    )

    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    forgot_key = models.CharField(max_length=128, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username
