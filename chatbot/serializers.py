from rest_framework import serializers
from .models import Message, Conversation

class MessageSerializer(serializers.ModelSerializer):
    """Serializer for displaying message history"""

    conversation_id = serializers.IntegerField(
        source="conversation.id",
        read_only=True
    )
    
    # ✅ Add full URLs for file fields
    voice_file_url = serializers.SerializerMethodField()
    image_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation_id",
            "sender",
            "message_type",
            "text_content",
            "voice_file",
            "voice_file_url",
            "image_file",
            "image_file_url",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "conversation_id"]
    
    def get_voice_file_url(self, obj):
        """Return full URL for voice file"""
        if obj.voice_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.voice_file.url)
            return obj.voice_file.url
        return None
    
    def get_image_file_url(self, obj):
        """Return full URL for image file"""
        if obj.image_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_file.url)
            return obj.image_file.url
        return None



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
    """Serializer for conversation list"""
    
    message_count = serializers.IntegerField(read_only=True)
    latest_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            "id",
            "created_at",
            "updated_at",
            "message_count",
            "latest_message",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_latest_message(self, obj):
        """Get the latest message preview"""
        latest = obj.messages.last()
        if latest:
            return {
                "text": latest.text_content[:50] if latest.text_content else None,
                "sender": latest.sender,
                "created_at": latest.created_at,
            }
        return None