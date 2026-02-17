from django.db import models
from users.models import Users
# Create your models here.
class Prescription(models.Model):
    users=models.ForeignKey('users.Users', on_delete=models.CASCADE)
    doctor=models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, default=None, null=True) # doctor foreign key 
    prescription_image=models.ImageField(upload_to='prescriptions/',null=True, blank=True)
    next_appointment_date=models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prescription #{self.id} - {self.users.full_name}"

class Patient(models.Model):
    prescription = models.OneToOneField(
        Prescription,
        on_delete=models.CASCADE,
        related_name='patient'
    )
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    sex = models.CharField(max_length=10,null=True, blank=True)
    health_issues = models.TextField(null=True, blank=True)

class Medicine_Time(models.Model):
    time=models.TimeField()
    before_meal=models.BooleanField(default=False)
    after_meal=models.BooleanField(default=False)

class Medicine(models.Model):
    prescription=models.ForeignKey(Prescription, on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    
    morning=models.OneToOneField(Medicine_Time, on_delete=models.CASCADE, null=True, blank=True,related_name='morning_time')
    afternoon=models.OneToOneField(Medicine_Time, on_delete=models.CASCADE, null=True, blank=True,related_name='afternoon_time')
    evening=models.OneToOneField(Medicine_Time, on_delete=models.CASCADE, null=True, blank=True,related_name='evening_time')
    night=models.OneToOneField(Medicine_Time, on_delete=models.CASCADE, null=True, blank=True,related_name='night_time')
    
    how_many_day=models.IntegerField()
    stock=models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
    
    
    def __str__(self):
        return self.pharmacy_nam
class NotificationLog(models.Model):
    """
    Track all notifications sent to users
    """
    NOTIFICATION_TYPES = (
        ('medicine_reminder', 'Medicine Reminder'),
        ('low_stock_alert', 'Low Stock Alert'),
    )
    
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    
    # Medicine reference (optional, যদি medicine reminder হয়)
    medicine = models.ForeignKey(
        'Medicine', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='notifications'
    )
    
    # Status tracking
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    # Firebase response (optional)
    firebase_response = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
    
    def __str__(self):
        return f"{self.user.email} - {self.notification_type} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"