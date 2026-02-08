from django.contrib import admin
from .models import Prescription, Patient, Medicine, MedicalTest, Medicine_Time

# Inline for MedicalTest
class MedicalTestInline(admin.TabularInline):
    model = MedicalTest
    extra = 1
    verbose_name = "Medical Test"
    verbose_name_plural = "Medical Tests"

# Inline for Patient (1-to-1)
class PatientInline(admin.StackedInline):
    model = Patient
    extra = 0
    max_num = 1
    verbose_name = "Patient"
    verbose_name_plural = "Patient"

# Inline for Medicine
class MedicineInline(admin.StackedInline):
    model = Medicine
    extra = 1
    fields = [
        'name',
        'how_many_day',
        'stock',
        'morning',
        'afternoon',
        'evening',
        'night'
    ]
    verbose_name = "Medicine"
    verbose_name_plural = "Medicines"

# Prescription admin
@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'users', 'doctor', 'created_at')
    search_fields = ('users__full_name', 'users__email', 'doctor__name')
    list_filter = ('doctor', 'created_at')
    inlines = [PatientInline, MedicineInline, MedicalTestInline]

    readonly_fields = ('created_at', 'updated_at')

    def prescription_image_preview(self, obj):
        if obj.prescription_image:
            return f"<img src='{obj.prescription_image.url}' width='100' />"
        return "-"
    prescription_image_preview.allow_tags = True
    prescription_image_preview.short_description = 'Prescription Image Preview'

# Medicine_Time admin (optional if you want to manage separately)
@admin.register(Medicine_Time)
class MedicineTimeAdmin(admin.ModelAdmin):
    list_display = ('id', 'time', 'before_meal', 'after_meal')
