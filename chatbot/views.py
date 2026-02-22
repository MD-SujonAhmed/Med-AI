import os
import time
import requests
import mimetypes

from django.conf import settings
from django.core.files.base import ContentFile

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Message, Conversation
from users.permissions import IsNormalUser

from .serializers import (
    ChatRequestSerializer,
    MessageSerializer,
)


class AIResponseParser:

    @staticmethod
    def extract_text(ai_json):
        return ai_json.get("assistant_message")

    @staticmethod
    def extract_tts(ai_json):
        return ai_json.get("tts")
    
    @staticmethod
    def extract_data(ai_json):
        """Extract the data field from AI response"""
        return ai_json.get("data")


class ChatAPIView(APIView):

    permission_classes = [IsAuthenticated, IsNormalUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    AI_CHATBOT_URL = settings.AI_CHATBOT_URL
    AI_TTS_URL = settings.AI_TTS_URL

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        validated_data = serializer.validated_data
        user = request.user

        # 🔹 Get or create conversation
        conversation_id = request.data.get("conversation_id")

        if conversation_id:
            conversation = Conversation.objects.filter(
                id=conversation_id,
                user=user
            ).first()

            if not conversation:
                return Response(
                    {"error": "Invalid conversation"},
                    status=404
                )
        else:
            conversation = Conversation.objects.create(user=user)

        # Determine message type
        message_type = Message.MessageType.TEXT
        if validated_data.get("audio"):
            message_type = Message.MessageType.VOICE
        elif validated_data.get("file"):
            message_type = Message.MessageType.IMAGE

        # Save USER message
        Message.objects.create(
            conversation=conversation,
            sender=Message.SenderType.USER,
            message_type=message_type,
            text_content=validated_data.get("text"),
            voice_file=validated_data.get("audio"),
            image_file=validated_data.get("file"),
        )

        # Prepare AI request
        ai_data = {
            "user_id": user.id,
            "conversation_id": conversation.id,
            "reply_mode": validated_data.get("reply_mode", "text"),
        }

        if validated_data.get("text"):
            ai_data["text"] = validated_data["text"]

        ai_files = {}

        if validated_data.get("audio"):
            audio = validated_data["audio"]

            # Reset file pointer to the beginning
            audio.seek(0)

            # Guess correct MIME from filename
            guessed_type, _ = mimetypes.guess_type(audio.name)

            ai_files["audio"] = (
                audio.name,
                # audio.file,
                audio.read(),
                guessed_type or "audio/m4a"
            )
            print(f"Audio: {audio.name}, Type: {guessed_type or 'audio/m4a'}")


        if validated_data.get("file"):
            image = validated_data["file"]
            image.seek(0)
            ai_files["file"] = (image.name, image.read(), image.content_type)
            print(f"Image: {image.name}, Type: {image.content_type}")

        # 🔹 Forward Bearer token
        auth_header = request.headers.get("Authorization")
        headers = {"Authorization": auth_header} if auth_header else {}

        try:
            if ai_files:
                # Multipart request (for audio/image)
                ai_response = requests.post(
                    self.AI_CHATBOT_URL,
                    data=ai_data,
                    files=ai_files,
                    headers=headers,
                    timeout=60,
                )
            else:
                # Pure JSON request (for text)
                ai_response = requests.post(
                    self.AI_CHATBOT_URL,
                    json=ai_data,
                    headers=headers,
                    timeout=60,
                )
            
            print(f"AI Response Status: {ai_response.status_code}")
            print(f"AI Response Body: {ai_response.text[:500]}")


        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "AI service unreachable", "details": str(e)},
                status=503,
            )

        if ai_response.status_code != 200:
            return Response(
                {"error": "AI chatbot error", "details": ai_response.text},
                status=502,
            )

        try:
            ai_json = ai_response.json()
        except ValueError:
            return Response(
                {"error": "Invalid AI response format"},
                status=502,
            )

        ai_text = AIResponseParser.extract_text(ai_json)
        ai_data_field = AIResponseParser.extract_data(ai_json)
        ai_message_type = "text"  # Default to text

        tts_data = AIResponseParser.extract_tts(ai_json)
        voice_file_obj = None
        voice_url = None

        if tts_data and tts_data.get("enabled"):
            tts_payload = tts_data.get("payload")
            try:
                tts_resp = requests.post(
                    settings.AI_TTS_URL,
                    json=tts_payload,
                    timeout=60
                )
                if tts_resp.status_code == 200:
                    ai_message_type = "voice"
                    # Save audio to Message.voice_file
                    filename = f"chat_{user.id}_{int(time.time())}.mp3"
                    voice_file_obj = ContentFile(tts_resp.content, name=filename)
            except Exception as e:
                print("TTS Error:", e)

        # Save AI message
        ai_message = Message.objects.create(
            conversation=conversation,
            sender=Message.SenderType.AI,
            message_type=ai_message_type,
            text_content=ai_text,
            voice_file=voice_file_obj
        )

        # Build response with data field
        response_data = {
            "conversation_id": conversation.id,
            "response": ai_text,
            "message_type": ai_message_type,
            "created_at": ai_message.created_at,
        }
        
        # Include data field if present
        if ai_data_field is not None:
            response_data["data"] = ai_data_field
        
        # Include voice URL if voice message
        if ai_message_type == "voice" and ai_message.voice_file:
            voice_url = request.build_absolute_uri(ai_message.voice_file.url)
            response_data["voice_url"] = voice_url

        return Response(response_data, status=200)


class ChatHistoryAPIView(APIView):
    """
    Get all conversations with all messages for the authenticated user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns all conversations with complete message details grouped by sender
        """
        conversations = Conversation.objects.filter(
            user=request.user
        ).prefetch_related('messages').order_by('-updated_at')
        
        conversations_data = []
        
        for conversation in conversations:
            messages = conversation.messages.all().order_by('created_at')
            
            # Group messages into pairs (user -> ai)
            message_pairs = []
            temp_pair = {}
            
            for message in messages:
                message_data = {
                    "message_id": message.id,
                    "message_type": message.message_type,
                    "text_content": message.text_content,
                    "voice_file_url": request.build_absolute_uri(message.voice_file.url) if message.voice_file else None,
                    "image_file_url": request.build_absolute_uri(message.image_file.url) if message.image_file else None,
                    "created_at": message.created_at,
                }
                
                if message.sender == Message.SenderType.USER:
                    # Start a new pair with user message
                    temp_pair = {
                        "user": message_data,
                        "ai": None
                    }
                elif message.sender == Message.SenderType.AI:
                    # Complete the pair with AI message
                    if temp_pair:
                        temp_pair["ai"] = message_data
                        message_pairs.append(temp_pair)
                        temp_pair = {}
                    else:
                        # AI message without user message (shouldn't happen, but handle it)
                        message_pairs.append({
                            "user": None,
                            "ai": message_data
                        })
            
            # If there's an unpaired user message, add it
            if temp_pair:
                message_pairs.append(temp_pair)
            
            conversation_info = {
                "id": conversation.id,
                "message_count": messages.count(),
                "messages": message_pairs,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
            }
            
            conversations_data.append(conversation_info)

        return Response({
            "count": conversations.count(),
            "conversations": conversations_data
        }, status=status.HTTP_200_OK)


class ConversationDetailAPIView(APIView):
    """
    Get messages for a specific conversation (optional - if you still want this)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        """
        Returns all messages for a specific conversation
        """
        conversation = Conversation.objects.filter(
            id=conversation_id,
            user=request.user
        ).prefetch_related('messages').first()

        if not conversation:
            return Response(
                {"error": "Conversation not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        messages = conversation.messages.all().order_by('created_at')
        
        # Group messages into pairs (user -> ai)
        message_pairs = []
        temp_pair = {}
        
        for message in messages:
            message_data = {
                "message_id": message.id,
                "message_type": message.message_type,
                "text_content": message.text_content,
                "voice_file_url": request.build_absolute_uri(message.voice_file.url) if message.voice_file else None,
                "image_file_url": request.build_absolute_uri(message.image_file.url) if message.image_file else None,
                "created_at": message.created_at,
            }
            
            if message.sender == Message.SenderType.USER:
                temp_pair = {
                    "user": message_data,
                    "ai": None
                }
            elif message.sender == Message.SenderType.AI:
                if temp_pair:
                    temp_pair["ai"] = message_data
                    message_pairs.append(temp_pair)
                    temp_pair = {}
                else:
                    message_pairs.append({
                        "user": None,
                        "ai": message_data
                    })
        
        if temp_pair:
            message_pairs.append(temp_pair)

        return Response({
            "conversation_id": conversation.id,
            "message_count": messages.count(),
            "messages": message_pairs,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        }, status=status.HTTP_200_OK)



class ClearChatHistoryAPIView(APIView):
    """
    Clear all chat history for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        """
        Delete all conversations (and their messages) for the current user
        """
        
        # Get all conversations for the user
        conversations = Conversation.objects.filter(user=request.user)
        conversation_count = conversations.count()
        
        # Count messages before deletion
        message_count = Message.objects.filter(conversation__user=request.user).count()
        
        # Delete all conversations (this will cascade delete all messages)
        conversations.delete()
        
        return Response({
            'message': 'Chat history cleared successfully',
            'deleted_conversations': conversation_count,
            'deleted_messages': message_count
        }, status=status.HTTP_200_OK)


class DeleteConversationAPIView(APIView):
    """
    Delete a specific conversation
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, conversation_id):
        """
        Delete a specific conversation and all its messages
        """
        conversation = Conversation.objects.filter(
            id=conversation_id,
            user=request.user
        ).first()
        
        if not conversation:
            return Response(
                {"error": "Conversation not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Count messages before deletion
        message_count = conversation.messages.count()
        
        # Delete the conversation (cascade deletes messages)
        conversation.delete()
        
        return Response({
            'message': 'Conversation deleted successfully',
            'deleted_messages': message_count
        }, status=status.HTTP_200_OK)