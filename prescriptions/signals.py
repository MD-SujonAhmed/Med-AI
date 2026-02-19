
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Medicine


@receiver(post_save, sender=Medicine)
def schedule_medicine_reminder(sender, instance, created, **kwargs):
    if not created:
        return

    from .tasks import send_medicine_reminder

    slots = {
        'morning': instance.morning,
        'afternoon': instance.afternoon,
        'evening': instance.evening,
        'night': instance.night,
    }

    now = timezone.now()

    for slot_name, slot_obj in slots.items():
        if slot_obj and slot_obj.time:
            slot_time_str = slot_obj.time.strftime('%H:%M:%S')

            # আজকের slot datetime বানাও
            slot_datetime = datetime.combine(now.date(), slot_obj.time)
            slot_datetime = timezone.make_aware(slot_datetime)
            reminder_time = slot_datetime - timedelta(minutes=30)

            # সময় চলে গেলে কাল থেকে শুরু করো
            if reminder_time <= now:
                slot_datetime += timedelta(days=1)
                reminder_time = slot_datetime - timedelta(minutes=30)

            send_medicine_reminder.apply_async(
                args=[instance.id, slot_name, slot_time_str],
                eta=reminder_time
            )
            print(f"[SCHEDULE] ✅ {slot_name} reminder scheduled for {instance.name} at {reminder_time}")