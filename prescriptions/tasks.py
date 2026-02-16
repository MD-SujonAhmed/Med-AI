from celery import shared_task
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from firebase_admin import messaging
from .models import Medicine, NotificationLog


@shared_task
def send_medicine_reminder(medicine_id, slot_name, slot_time):
    """
    Send reminder 30 min before medicine time.
    """
    try:
        medicine = Medicine.objects.select_related('prescription__users').get(id=medicine_id)
    except Medicine.DoesNotExist:
        return f"Medicine {medicine_id} not found"

    user = medicine.prescription.users
    
    title = "Medicine Reminder"
    body = f"It's time to take {medicine.name}. Please take your {slot_name} dose now."
    
    # ✅ Pass notification_type and medicine reference
    send_push_notification(
        user, 
        title, 
        body, 
        notification_type='medicine_reminder',
        medicine=medicine
    )

    # Re-schedule for tomorrow
    now = timezone.now()
    tomorrow_slot = datetime.combine(
        now.date() + timedelta(days=1), 
        datetime.strptime(slot_time, '%H:%M:%S').time()
    )
    tomorrow_slot = timezone.make_aware(tomorrow_slot)
    reminder_time = tomorrow_slot - timedelta(minutes=30)

    send_medicine_reminder.apply_async(
        args=[medicine_id, slot_name, slot_time],
        eta=reminder_time
    )

    return f"Reminder sent for {medicine.name}"


@shared_task
def check_low_stock_and_notify():
    """
    Daily task: low stock alert
    """
    threshold = getattr(settings, 'LOW_STOCK_THRESHOLD_DAYS', 3)
    low_stock = Medicine.objects.select_related('prescription__users').filter(stock__lte=threshold)

    for med in low_stock:
        user = med.prescription.users
        
        if med.stock == 0:
            body = f"⚠️ {med.name} is out of stock!"
        else:
            body = f"⚠️ {med.name} has {med.stock} day(s) left."
        
        # ✅ Pass notification_type and medicine reference
        send_push_notification(
            user, 
            "Low Stock Alert", 
            body,
            notification_type='low_stock_alert',
            medicine=med
        )

    return f"Alerts sent for {low_stock.count()} medicines"
def send_push_notification(user, title, body, notification_type='medicine_reminder', medicine=None):
    """
    Send push notification via Firebase Admin SDK and log it
    """
    # Create log entry
    log = NotificationLog.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        body=body,
        medicine=medicine,
        is_sent=False
    )
    
    if not hasattr(user, 'fcm_token') or not user.fcm_token:
        log.error_message = "No FCM token for user"
        log.save()
        print(f"[PUSH] ❌ No FCM token for user ID: {user.id}")
        return

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=user.fcm_token,
        android=messaging.AndroidConfig(
            priority='high',
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound='default'),
            ),
        ),
    )

    try:
        response = messaging.send(message)
        
        # Update log as successful
        log.is_sent = True
        log.firebase_response = response
        log.save()
        
        print(f"[PUSH] ✅ Sent to user {user.id} ({user.email}): {response}")
    except Exception as e:
        # Update log with error
        log.error_message = str(e)
        log.save()
        
        print(f"[PUSH] ❌ Error sending to user {user.id}: {e}")