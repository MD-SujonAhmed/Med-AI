from django.contrib import admin
from .models import Doctor, DoctorNote

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sex', 'specialization', 'hospital_name', 'designation', 'next_appointment_date')
    search_fields = ('name', 'specialization', 'hospital_name')
    list_filter = ('specialization', 'hospital_name')
    ordering = ('id',)

    def next_appointment_date(self, obj):
        appointment = obj.appointments.order_by('date').first()
        return appointment.date if appointment else 'N/A'
    next_appointment_date.short_description = 'Next Appointment'

@admin.register(DoctorNote)
class DoctorNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'short_note')
    search_fields = ('doctor__name', 'note')
    list_filter = ('doctor',)
    ordering = ('id',)
    readonly_fields = ()

    def short_note(self, obj):
        return obj.note[:50]  
    short_note.short_description = 'Note Preview'
