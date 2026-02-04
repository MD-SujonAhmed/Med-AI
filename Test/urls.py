from django.urls import path
from .views import OCRImageAPIView, OCRResultSaveAPIView

urlpatterns = [
    path("ocr/image/", OCRImageAPIView.as_view(), name="ocr-image"),
    path("ocr/save/", OCRResultSaveAPIView.as_view(), name="ocr-save"),
]
