from django.contrib import admin
from .models import OCRResult


@admin.register(OCRResult)
class OCRResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_text",
        "created_at",
    )

    list_filter = ("created_at",)
    search_fields = ("extracted_text",)
    ordering = ("-created_at",)

    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "OCR Content",
            {
                "fields": (
                    "original_image",
                    "extracted_text",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": ("created_at",)
            },
        ),
    )

    def short_text(self, obj):
        return obj.extracted_text[:60]

    short_text.short_description = "Extracted Text Preview"
