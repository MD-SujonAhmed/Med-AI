from unicodedata import name
from django.db import models

# Create your models here.
class Doctor(models.Model): 
    sex_choices = [
        ('male', 'Male'),
        ('female', 'Female'),   
        ('other', 'Other'),
    ]
    
    
    name=models.CharField(max_length=100)
    sex=models.CharField(max_length=100, choices=sex_choices)
    specialization=models.CharField(max_length=100)
    hospital_name=models.CharField(max_length=100)
    designation=models.CharField(max_length=100)
    doctor_email=models.EmailField(unique=True,null=True,blank=True)
    
    

class DoctorNote(models.Model):
    doctor=models.ForeignKey(Doctor,on_delete=models.CASCADE, related_name='notes')
    note = models.TextField()

