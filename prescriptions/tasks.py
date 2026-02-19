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
    Prescription শেষ হলে আর schedule করবে না।
    """
    try:
        medicine = Medicine.objects.select_related('prescription__users').get(id=medicine_id)
    except Medicine.DoesNotExist:
        return f"Medicine {medicine_id} not found"

    # ✅ Check করো prescription এর মেয়াদ শেষ হয়েছে কিনা
    prescription = medicine.prescription
    start_date = prescription.created_at.date()
    end_date = start_date + timedelta(days=medicine.how_many_day - 1)
    today = timezone.now().date()

    if today > end_date:
        return f"Medicine {medicine.name} course completed. Stopping reminders."

    user = medicine.prescription.users

    title = "💊 Medicine Reminder"
    body = f"Time to take {medicine.name} ({slot_name} dose)"

    send_push_notification(
        user,
        title,
        body,
        notification_type='medicine_reminder',
        medicine=medicine
    )

    # ✅ কালকের জন্য Re-schedule
    now = timezone.now()
    tomorrow_slot = datetime.combine(
        now.date() + timedelta(days=1),
        datetime.strptime(slot_time, '%H:%M:%S').time()
    )
    tomorrow_slot = timezone.make_aware(tomorrow_slot)
    reminder_time = tomorrow_slot - timedelta(minutes=30)

    # ✅ শুধু মেয়াদ থাকলে schedule করো
    tomorrow_date = now.date() + timedelta(days=1)
    if tomorrow_date <= end_date:
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

    # ✅ stock=0 আলাদাভাবে handle করো (lte threshold মানে 0 ও আসবে)
    low_stock = Medicine.objects.select_related(
        'prescription__users'
    ).filter(stock__lte=threshold, stock__gt=0)  # stock > 0

    out_of_stock = Medicine.objects.select_related(
        'prescription__users'
    ).filter(stock=0)

    count = 0

    for med in low_stock:
        user = med.prescription.users
        body = f"⚠️ {med.name} এর মাত্র {med.stock} দিনের stock বাকি আছে!"
        send_push_notification(
            user,
            "Low Stock Alert",
            body,
            notification_type='low_stock_alert',
            medicine=med
        )
        count += 1

    for med in out_of_stock:
        user = med.prescription.users
        body = f"🚨 {med.name} এর stock শেষ হয়ে গেছে! এখনই কিনুন।"
        send_push_notification(
            user,
            "Out of Stock Alert",
            body,
            notification_type='low_stock_alert',
            medicine=med
        )
        count += 1

    return f"Alerts sent for {count} medicines"


def send_push_notification(user, title, body, notification_type='medicine_reminder', medicine=None):
    """
    Firebase push notification send করো এবং log করো
    """
    # Log entry তৈরি করো
    log = NotificationLog.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        body=body,
        medicine=medicine,
        is_sent=False
    )

    # ✅ FCM token check
    if not user.fcm_token:
        log.error_message = "No FCM token found for this user"
        log.save()
        print(f"[PUSH] ❌ No FCM token - User ID: {user.id} ({user.email})")
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
        log.is_sent = True
        log.firebase_response = str(response)
        log.save()
        print(f"[PUSH] ✅ Sent! User: {user.email} | Medicine: {medicine.name if medicine else 'N/A'}")

    except messaging.UnregisteredError:
        # ✅ Invalid token হলে user এর token clear করো
        log.error_message = "FCM token is invalid or unregistered"
        log.save()
        user.fcm_token = None
        user.save(update_fields=['fcm_token'])
        print(f"[PUSH] ❌ Invalid token cleared for user: {user.email}")

    except Exception as e:
        log.error_message = str(e)
        log.save()
        print(f"[PUSH] ❌ Error for user {user.email}: {e}")