from django.db import models
from django.contrib.auth.models import Users
# Create your models here.
class Prescription(models.Model):
    user=models.ForeignKey(Users, on_delete=models.CASCADE, related_name='prescriptions')
    pres    