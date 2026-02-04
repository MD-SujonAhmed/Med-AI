from django.contrib import admin
from .models import Prescription, Patient, Medicine, MedicalTest

class MedicineInline(admin.TabularInline):
    model = Medicine
    extra = 0

class MedicalTestInline(admin.TabularInline):
    model = MedicalTest
    extra = 0

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'users', 'doctor')
    search_fields = ('users__full_name', 'users__email', 'doctor__name')
    list_filter = ('doctor',)
    ordering = ('id',)
    readonly_fields = ()
    inlines = [MedicineInline, MedicalTestInline]

    def prescription_image_preview(self, obj):
        if obj.preceptions_image:
            return f"<img src='{obj.preceptions_image.url}' width='100' />"
        return "-"
    prescription_image_preview.allow_tags = True
    prescription_image_preview.short_description = 'Prescription Image Preview'

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'sex', 'Prescription')
    search_fields = ('name',)
    list_filter = ('sex',)

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'prescription', 'how_many_time', 'how_many_day', 'stock')
    search_fields = ('name',)
    list_filter = ('prescription',)

@admin.register(MedicalTest)
class MedicalTestAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'prescription')
    search_fields = ('test_name',)
    list_filter = ('prescription',)
