import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import OCRImageSerializer, OCRResultCreateSerializer

OCR_API_URL = "https://api.ocr.space/parse/image"       # AI API endpoint
OCR_API_KEY = "K82904753588957"


class OCRImageAPIView(APIView):

    def post(self, request):
        serializer = OCRImageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data["image"]

        payload = {
            "language": "eng",
            "isOverlayRequired": False,
        }

        files = {
            "file": image_file
        }

        headers = {
            "apikey": OCR_API_KEY
        }

        ocr_response = requests.post(
            OCR_API_URL,
            data=payload,
            files=files,
            headers=headers
        )

        return Response(ocr_response.json(), status=status.HTTP_200_OK)
    


class OCRResultSaveAPIView(APIView):

    def post(self, request):
        serializer = OCRResultCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        ocr_result = serializer.save()

        return Response(
            {
                "message": "OCR result saved successfully",
                "data": OCRResultCreateSerializer(ocr_result).data,
            },
            status=status.HTTP_201_CREATED
        )
