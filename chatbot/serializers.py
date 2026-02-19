from rest_framework import serializers
from .models import Message, Conversation

class MessageSerializer(serializers.ModelSerializer):
    """Serializer for displaying message history"""

    conversation_id = serializers.IntegerField(
        source="conversation.id",
        read_only=True
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation_id",
            "sender",
            "message_type",
            "text_content",
            "voice_file",
            "image_file",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "conversation_id"]



class ChatRequestSerializer(serializers.Serializer):
    """Serializer for incoming chat requests"""

    conversation_id = serializers.IntegerField(
        required=False
    )

    text = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    audio = serializers.FileField(
        required=False,
        allow_null=True
    )

    file = serializers.ImageField(
        required=False,
        allow_null=True
    )

    reply_mode = serializers.ChoiceField(
        choices=["text", "voice"],
        default="text"
    )

    def validate(self, data):
        if not any([
            data.get("text"),
            data.get("audio"),
            data.get("file")
        ]):
            raise serializers.ValidationError(
                "At least one of 'text', 'audio', or 'file' must be provided."
            )
        return data



class ChatResponseSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    response = serializers.CharField()
    message_type = serializers.CharField()
    created_at = serializers.DateTimeField()


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
