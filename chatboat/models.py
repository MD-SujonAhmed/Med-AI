from django.db import models
from users.models import Users

class ChatMessage(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    content = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatMessage #{self.id} - user:{self.user_id}"