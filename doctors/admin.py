from django.contrib import admin
from .models import Doctor, DoctorNote

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sex', 'specialization', 'hospital_name', 'designation')
    search_fields = ('name', 'specialization', 'hospital_name')
    list_filter = ('specialization', 'hospital_name')
    ordering = ('id',)
    readonly_fields = ()

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
