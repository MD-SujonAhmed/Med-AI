import time
import requests
import mimetypes

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



class ChatAPIView(APIView):

    permission_classes = [IsAuthenticated, IsNormalUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    AI_CHATBOT_URL = "http://127.0.0.1:8080/ai/chat"

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
            print(audio.name)
            print(audio.content_type)


        if validated_data.get("file"):
            image = validated_data["file"]
            ai_files["file"] = (image.name, image.read(), image.content_type)

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
            
            print("AI Response", ai_response.status_code, ai_response.text)


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
        ai_message_type = ai_json.get("message_type", "text")

        tts_data = AIResponseParser.extract_tts(ai_json)
        voice_file_obj = None
        voice_url = None

        if tts_data and tts_data.get("enabled"):
            tts_payload = tts_data.get("payload")
            try:
                tts_resp = requests.post(
                    "http://127.0.0.1:8080/voice/tts",
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

        response_data = {
            "conversation_id": conversation.id,
            "response": ai_text,
            "message_type": ai_message_type,
            "created_at": ai_message.created_at,
        }
        if ai_message_type == "voice" and ai_message.voice_file:
            voice_url = request.build_absolute_uri(ai_message.voice_file.url)
            response_data["voice_url"] = voice_url

        return Response(response_data, status=200)



class ChatHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        conversation = Conversation.objects.filter(
            id=conversation_id,
            user=request.user
        ).first()

        if not conversation:
            return Response({"error": "Conversation not found"}, status=404)

        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)

        return Response({
            "conversation_id": conversation.id,
            "count": messages.count(),
            "messages": serializer.data
        })



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
