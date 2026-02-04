import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import OCRImageSerializer, OCRResultCreateSerializer

OCR_API_URL = "https://api.ocr.space/parse/image"       # AI API endpoint
OCR_API_KEY = "K82904753588957"

class OCRImageAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

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
        print(ocr_response.json())

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


# New Neded in Ai Development
# class OCRImageAPIView(APIView):
#     parser_classes = [MultiPartParser, FormParser]

#     def post(self, request):
#         serializer = OCRImageSerializer(data=request.data)

#         if not serializer.is_valid():
#             return Response(
#                 {
#                     "status": "error",
#                     "error_code": "VALIDATION_ERROR",
#                     "message": serializer.errors
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         image_file = serializer.validated_data["image"]

#         payload = {
#             "language": "eng",
#             "isOverlayRequired": False,
#         }

#         files = {
#             "file": image_file
#         }

#         headers = {
#             "apikey": settings.OCR_API_KEY
#         }

#         try:
#             ocr_response = requests.post(
#                 OCR_API_URL,
#                 data=payload,
#                 files=files,
#                 headers=headers,
#                 timeout=10
#             )
#         except requests.exceptions.RequestException:
#             return Response(
#                 {
#                     "status": "error",
#                     "error_code": "OCR_API_FAILED",
#                     "message": "Unable to process OCR image at this time"
#                 },
#                 status=status.HTTP_503_SERVICE_UNAVAILABLE
#             )

#         if ocr_response.status_code != 200:
#             return Response(
#                 {
#                     "status": "error",
#                     "error_code": "OCR_SERVICE_ERROR",
#                     "message": "OCR service returned an error"
#                 },
#                 status=status.HTTP_502_BAD_GATEWAY
#             )

#         ocr_json = ocr_response.json()

#         extracted_text = ""
#         if (
#             ocr_json.get("ParsedResults") and
#             len(ocr_json["ParsedResults"]) > 0
#         ):
#             extracted_text = ocr_json["ParsedResults"][0].get("ParsedText", "")

#         return Response(
#             {
#                 "status": "success",
#                 "extracted_text": extracted_text
#             },
#             status=status.HTTP_200_OK
#         )


# class OCRResultSaveAPIView(APIView):

    def post(self, request):
        serializer = OCRResultCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "error_code": "VALIDATION_ERROR",
                    "message": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        ocr_result = serializer.save()

        return Response(
            {
                "status": "success",
                "message": "OCR result saved successfully",
                "data": OCRResultCreateSerializer(ocr_result).data
            },
            status=status.HTTP_201_CREATED
        )