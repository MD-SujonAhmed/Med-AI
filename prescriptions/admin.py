from django.contrib import admin
from .models import (
    Prescription,
    Patient,
    Medicine,
    Medicine_Time,
    MedicalTest,
    pharmacy,
    NotificationLog
)

# ---------------------------
# Medicine Time Admin
# ---------------------------
@admin.register(Medicine_Time)
class MedicineTimeAdmin(admin.ModelAdmin):
    list_display = ('id', 'time', 'before_meal', 'after_meal')
    list_filter = ('before_meal', 'after_meal')
    search_fields = ('id',)


# ---------------------------
# Medicine Inline for Prescription
# ---------------------------
class MedicineInline(admin.TabularInline):
    model = Medicine
    extra = 1


# ---------------------------
# Medical Test Inline
# ---------------------------
class MedicalTestInline(admin.TabularInline):
    model = MedicalTest
    extra = 1


# ---------------------------
# Patient Inline (OneToOne)
# ---------------------------
class PatientInline(admin.StackedInline):
    model = Patient
    can_delete = False


# ---------------------------
# Prescription Admin
# ---------------------------
@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'users',
        'doctor',
        'next_appointment_date',
        'created_at'
    )
    list_filter = ('doctor', 'created_at')
    search_fields = (
        'users__full_name',
        'users__email'
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PatientInline, MedicineInline, MedicalTestInline]


# ---------------------------
# Medicine Admin
# ---------------------------
@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'prescription',
        'how_many_day',
        'stock',
        'created_at'
    )
    list_filter = ('created_at',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


# ---------------------------
# Medical Test Admin
# ---------------------------
@admin.register(MedicalTest)
class MedicalTestAdmin(admin.ModelAdmin):
    list_display = ('id', 'test_name', 'prescription')
    search_fields = ('test_name',)


# ---------------------------
# Pharmacy Admin
# ---------------------------
@admin.register(pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ('id', 'pharmacy_name', 'user', 'Pharmacy_Address')
    search_fields = ('pharmacy_name', 'user__email')
    list_filter = ('pharmacy_name',)


# ---------------------------
# Notification Log Admin
# ---------------------------
@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'notification_type',
        'is_sent',
        'sent_at'
    )
    list_filter = ('notification_type', 'is_sent', 'sent_at')
    search_fields = ('user__email', 'title')
    readonly_fields = ('sent_at',)

