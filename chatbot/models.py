from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Conversation(models.Model):
    """
    A chat session between user and AI
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversations"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "updated_at"]),
        ]

    def __str__(self):
        return f"Conversation {self.id} - {self.user}"


class Message(models.Model):
    """
    Each individual message in a conversation
    """

    class SenderType(models.TextChoices):
        USER = "user", "User"
        AI = "ai", "AI"

    class MessageType(models.TextChoices):
        TEXT = "text", "Text"
        VOICE = "voice", "Voice"
        IMAGE = "image", "Image"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.CharField(
        max_length=10,
        choices=SenderType.choices
    )

    message_type = models.CharField(
        max_length=10,
        choices=MessageType.choices,
        default=MessageType.TEXT
    )

    text_content = models.TextField(blank=True, null=True)

    voice_file = models.FileField(
        upload_to="chat/voice/",
        blank=True,
        null=True
    )

    image_file = models.ImageField(
        upload_to="chat/images/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        return f"{self.conversation.id} | {self.sender} | {self.created_at}"
