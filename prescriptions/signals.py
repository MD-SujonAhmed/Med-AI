from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Medicine


@receiver(post_save, sender=Medicine)
def schedule_medicine_reminder(sender, instance, created, **kwargs):
    if not created:
        return
    from .tasks import send_grouped_medicine_reminder

    user = instance.prescription.users
    now = timezone.now()

    slots = {
        'Morning': instance.morning,
        'Afternoon': instance.afternoon,
        'Evening': instance.evening,
        'Night': instance.night,
    }

    for slot_name, slot_obj in slots.items():
        if slot_obj and slot_obj.time:
            slot_time_str = slot_obj.time.strftime('%H:%M:%S')

            slot_datetime = datetime.combine(now.date(), slot_obj.time)
            slot_datetime = timezone.make_aware(slot_datetime)
            reminder_time = slot_datetime - timedelta(minutes=30)

            if reminder_time <= now:
                slot_datetime += timedelta(days=1)
                reminder_time = slot_datetime - timedelta(minutes=30)

            send_grouped_medicine_reminder.apply_async(
                args=[user.id, slot_name, slot_time_str],
                eta=reminder_time
            )
            print(f"[SCHEDULE] ✅ {slot_name} reminder scheduled for {instance.name} at {reminder_time}")