from django.conf import settings
from django.db import models


class Prescription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prescriptions'
    )
    image=models.ImageField(upload_to='prescriptions/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription {self.id} for {self.user.email}"