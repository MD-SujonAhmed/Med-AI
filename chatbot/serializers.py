from rest_framework import serializers
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for displaying message history"""
    
    class Meta:
        model = Message
        fields = [
            'id', 
            'sender', 
            'message_type', 
            'text_content', 
            'voice_file', 
            'image_file', 
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for incoming chat requests"""
    
    text = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    audio = serializers.FileField(required=False, allow_null=True)
    file = serializers.ImageField(required=False, allow_null=True)
    reply_mode = serializers.ChoiceField(
        choices=['text', 'voice', 'both'],
        default='text'
    )
    
    def validate(self, data):
        """Ensure at least one input method is provided"""
        if not any([data.get('text'), data.get('audio'), data.get('file')]):
            raise serializers.ValidationError(
                "At least one of 'text', 'audio', or 'file' must be provided."
            )
        return data


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat response"""
    
    response = serializers.CharField()
    message_type = serializers.CharField()
    created_at = serializers.DateTimeField()