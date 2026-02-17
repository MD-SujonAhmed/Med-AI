from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Message(models.Model):
    """Store all chat messages for history"""
    
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
    ]
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('voice', 'Voice'),
        ('image', 'Image'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_messages'
    )
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message_type = models.CharField(
        max_length=10, 
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    
    # Content fields
    text_content = models.TextField(null=True, blank=True)
    voice_file = models.FileField(
        upload_to='chat/voice/', 
        null=True, 
        blank=True
    )
    image_file = models.ImageField(
        upload_to='chat/images/', 
        null=True, 
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.sender} - {self.created_at}"