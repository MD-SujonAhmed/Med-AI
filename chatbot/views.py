import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings

from .models import Message
from .serializers import (
    ChatRequestSerializer, 
    ChatResponseSerializer, 
    MessageSerializer
)


class ChatAPIView(APIView):
    """
    Handle chat requests - acts as middleware between frontend and AI chatbot
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    AI_CHATBOT_URL = "http://127.0.0.1:8080/ai/chat"
    
    def post(self, request):
        """Send user message to AI and return response"""
        
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        user = request.user
        
        # Determine message type
        message_type = 'text'
        if validated_data.get('audio'):
            message_type = 'voice'
        elif validated_data.get('file'):
            message_type = 'image'
        
        # Save user message to database
        user_message = Message.objects.create(
            user=user,
            sender='user',
            message_type=message_type,
            text_content=validated_data.get('text', ''),
            voice_file=validated_data.get('audio'),
            image_file=validated_data.get('file')
        )
        
        # Prepare data for AI chatbot
        ai_request_data = {
            'user_id': user.id,
            'reply_mode': validated_data.get('reply_mode', 'text')
        }
        
        ai_request_files = {}
        
        if validated_data.get('text'):
            ai_request_data['text'] = validated_data['text']
        
        if validated_data.get('audio'):
            audio_file = validated_data['audio']
            ai_request_files['audio'] = (
                audio_file.name, 
                audio_file.file, 
                audio_file.content_type
            )
        
        if validated_data.get('file'):
            image_file = validated_data['file']
            ai_request_files['file'] = (
                image_file.name, 
                image_file.file, 
                image_file.content_type
            )
        print("AI Request Data:", ai_request_data)
        try:
            # Forward request to AI chatbot
            ai_response = requests.post(
                self.AI_CHATBOT_URL,
                data=ai_request_data,
                files=ai_request_files if ai_request_files else None,
                timeout=30
            )
            
            if ai_response.status_code == 200:
                ai_response_text = ai_response.text.strip('"')
                
                # Save AI response to database
                ai_message = Message.objects.create(
                    user=user,
                    sender='ai',
                    message_type='text',
                    text_content=ai_response_text
                )
                
                return Response({
                    'response': ai_response_text,
                    'message_type': 'text',
                    'created_at': ai_message.created_at
                }, status=status.HTTP_200_OK)
            
            else:
                return Response(
                    {
                        'error': 'AI chatbot returned an error',
                        'details': ai_response.text
                    },
                    status=status.HTTP_502_BAD_GATEWAY
                )
        
        except requests.exceptions.RequestException as e:
            return Response(
                {
                    'error': 'Failed to communicate with AI chatbot',
                    'details': str(e)
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class ChatHistoryAPIView(APIView):
    """
    Retrieve chat history for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all messages for the current user"""
        
        messages = Message.objects.filter(user=request.user)
        serializer = MessageSerializer(messages, many=True)
        
        return Response({
            'count': messages.count(),
            'messages': serializer.data
        }, status=status.HTTP_200_OK)


class ClearChatHistoryAPIView(APIView):
    """
    Clear chat history for the authenticated user (optional feature)
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        """Delete all messages for the current user"""
        
        deleted_count, _ = Message.objects.filter(user=request.user).delete()
        
        return Response({
            'message': 'Chat history cleared successfully',
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)