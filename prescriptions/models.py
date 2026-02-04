from django.db import models

# Create your models here.

class Prescription(models.Model):
    users=models.ForeignKey('users.Users', on_delete=models.CASCADE)
    doctor=models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, default=None, null=True) # doctor foreign key 
    prescription_image=models.ImageField(upload_to='prescriptions/')
    next_appointment_date=models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prescription #{self.id} - {self.users.full_name}"


class Patient(models.Model):
    Prescription=models.OneToOneField(Prescription, on_delete=models.CASCADE, related_name='patient')
    name=models.CharField(max_length=100)
    age=models.IntegerField()
    sex=models.CharField(max_length=10)
    health_issues=models.TextField()
    
    def __str__(self):
        return self.name
    
class Medicine(models.Model):
    prescription=models.ForeignKey(Prescription, on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    how_many_time=models.IntegerField()
    how_many_day=models.IntegerField()
    stock=models.IntegerField(default=0)
    before_meal=models.BooleanField(default=False)
    after_meal=models.BooleanField(default=False)
    
    
    def __str__(self):
        return f"{self.name} - {self.prescription.id}"    



class MedicalTest(models.Model):
    prescription=models.ForeignKey(Prescription, on_delete=models.CASCADE)
    test_name=models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.test_name} - {self.prescription.id}"
    

class pharmacy(models.Model):
    user=models.ForeignKey('users.Users',on_delete=models.CASCADE)
    pharmacy_name=models.CharField(max_length=100)
    Pharmacy_Address=models.CharField(max_length=100) #Address
    website_link=models.URLField()
    
    class Meta:
        verbose_name_plural = 'Pharmacies'
    
    def __str__(self):
        return self.pharmacy_nam
    