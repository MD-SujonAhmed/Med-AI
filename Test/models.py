from django.db import models


class OCRResult(models.Model):
    original_image = models.ImageField(
        upload_to="ocr_images/",
        null=True,
        blank=True
    )
    extracted_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OCR Result {self.id}"
