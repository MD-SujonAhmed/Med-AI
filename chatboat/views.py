import mimetypes
import os
import requests
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsNormalUser
from .models import ChatMessage
from .serializers import ChatMessageSerializer


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]

    def get_queryset(self):
        return ChatMessage.objects.filter(user=self.request.user).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        content = request.data.get("content")
        uploaded = request.FILES.get("file")  # frontend sends "file" always

        if not content and not uploaded:
            return Response(
                {"detail": "Send either 'content' (text) OR 'file' (audio/image/pdf)."},
                status=400,
            )
        if content and uploaded:
            return Response(
                {"detail": "Send ONLY ONE input: content OR file (not both)."},
                status=400,
            )

        # Save user message
        user_msg = ChatMessage.objects.create(
            user=request.user,
            content=content if content else None,
            file=uploaded if uploaded else None,
        )

        ai_base = getattr(settings, "AI_BASE_URL", "http://localhost:8001").rstrip("/")
        url = f"{ai_base}/ai/chat"

        params = {
            "user_id": request.user.id,
            "reply_mode": "text",
        }

        try:
            if content:
                # TEXT -> query param text (NO JSON BODY)
                params["text"] = content
                r = requests.post(url, params=params, timeout=60)

            else:
                # FILE -> decide audio vs file based on extension/mime
                filename = uploaded.name
                ext = os.path.splitext(filename.lower())[1]
                mime = uploaded.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

                is_audio = ext in [".wav", ".mp3", ".m4a", ".aac", ".ogg"] or (mime and mime.startswith("audio/"))

                if is_audio:
                    files = {"audio": (filename, uploaded.read(), mime)}
                else:
                    files = {"file": (filename, uploaded.read(), mime)}

                r = requests.post(url, params=params, files=files, timeout=120)     

            r.raise_for_status()
            data = r.json()

        except Exception as e:
            assistant_msg = ChatMessage.objects.create(
                user=request.user,
                content=f"AI service error: {str(e)}",
            )
            return Response(
                {
                    "detail": "AI service call failed.",
                    "error": str(e),
                    "user_message": ChatMessageSerializer(user_msg).data,
                    "assistant_message": ChatMessageSerializer(assistant_msg).data,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        assistant_text = data.get("assistant_message") or "Done."
        assistant_msg = ChatMessage.objects.create(
            user=request.user,
            content=assistant_text,
        )

        # IMPORTANT: Prescription structured output (if any) is in data["data"]
        return Response(
            {
                "user_message": ChatMessageSerializer(user_msg).data,
                "assistant_message": ChatMessageSerializer(assistant_msg).data,
                "ai_intent": data.get("intent"),
                "ai_confidence": data.get("confidence"),
                "ai_data": data.get("data"),  # prescription backend-ready format here
                "confirmation_needed": data.get("confirmation_needed"),
            },
            status=status.HTTP_201_CREATED,
        )