from celery import shared_task
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from firebase_admin import messaging
from .models import Medicine, NotificationLog


@shared_task
def send_grouped_medicine_reminder(user_id, slot_name, slot_time):
    from users.models import Users

    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        return "User not found"

    today = timezone.now().date()

    slot_filter = {f"{slot_name.lower()}__isnull": False}
    medicines = Medicine.objects.filter(
        prescription__users=user,
        **slot_filter
    ).select_related('prescription')

    active_medicines = []
    for med in medicines:
        start_date = med.prescription.created_at.date()
        end_date = start_date + timedelta(days=med.how_many_day - 1)
        if start_date <= today <= end_date:
            active_medicines.append(med.name)

    if not active_medicines:
        return "No active medicines for this slot"

    if len(active_medicines) == 1:
        body = f"Time to take {active_medicines[0]}"
    else:
        names = ", ".join(active_medicines)
        body = f"Time to take: {names}"

    send_push_notification(
        user,
        f"💊 Medicine Reminder ({slot_name})",
        body,
        notification_type='medicine_reminder'
    )

    now = timezone.now()
    tomorrow_slot = datetime.combine(
        now.date() + timedelta(days=1),
        datetime.strptime(slot_time, '%H:%M:%S').time()
    )
    tomorrow_slot = timezone.make_aware(tomorrow_slot)
    reminder_time = tomorrow_slot - timedelta(minutes=30)

    send_grouped_medicine_reminder.apply_async(
        args=[user_id, slot_name, slot_time],
        eta=reminder_time
    )
    return f"Grouped reminder sent: {active_medicines}"


@shared_task
def check_low_stock_and_notify():
    threshold = getattr(settings, 'LOW_STOCK_THRESHOLD_DAYS', 3)
    low_stock = Medicine.objects.select_related(
        'prescription__users'
    ).filter(stock__lte=threshold, stock__gt=0)
    out_of_stock = Medicine.objects.select_related(
        'prescription__users'
    ).filter(stock=0)
    count = 0
    for med in low_stock:
        user = med.prescription.users
        body = f"⚠️ {med.name} has only {med.stock} day(s) of stock left!"
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
        body = f"🚨 {med.name} is out of stock! Please buy now."
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
    log = NotificationLog.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        body=body,
        medicine=medicine,
        is_sent=False
    )

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
        android=messaging.AndroidConfig(priority='high'),
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
        log.error_message = "FCM token is invalid or unregistered"
        log.save()
        user.fcm_token = None
        user.save(update_fields=['fcm_token'])
        print(f"[PUSH] ❌ Invalid token cleared for user: {user.email}")

    except Exception as e:
        log.error_message = str(e)
        log.save()
        print(f"[PUSH] ❌ Error for user {user.email}: {e}")