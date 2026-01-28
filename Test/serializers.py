from rest_framework import serializers
from .models import OCRResult

class OCRImageSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    
    
class OCRResultCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRResult
        fields = [
            "id",
            "original_image",
            "extracted_text",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
