from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Medicine

_scheduled = set()

@receiver(post_save, sender=Medicine)
def schedule_medicine_reminder(sender, instance, created, **kwargs):
    if not created:
        return

    from .tasks import send_grouped_medicine_reminder

    user = instance.prescription.users
    prescription_id = instance.prescription.id
    now = timezone.now()

    slots = {
        'Morning': instance.morning,
        'Afternoon': instance.afternoon,
        'Evening': instance.evening,
        'Night': instance.night,
    }

    for slot_name, slot_obj in slots.items():
        if slot_obj and slot_obj.time:
            slot_time = slot_obj.time
            if isinstance(slot_time, str):
                slot_time = datetime.strptime(slot_time, '%H:%M:%S').time()

            slot_time_str = slot_time.strftime('%H:%M:%S')

            # ✅ prescription + slot + exact time দিয়ে unique key
            # মানে 10:52 আর 10:54 আলাদা task হবে
            schedule_key = f"{prescription_id}_{slot_name}_{slot_time_str}"

            if schedule_key in _scheduled:
                print(f"[SCHEDULE] ⚠️ Skip: {schedule_key}")
                continue

            _scheduled.add(schedule_key)

            slot_datetime = datetime.combine(now.date(), slot_time)
            slot_datetime = timezone.make_aware(slot_datetime)
            reminder_time = slot_datetime - timedelta(minutes=30)

            if reminder_time <= now:
                slot_datetime += timedelta(days=1)
                reminder_time = slot_datetime - timedelta(minutes=30)

            # ✅ slot_time_str পাঠাচ্ছি তাই task জানবে কোন time এর জন্য
            send_grouped_medicine_reminder.apply_async(
                args=[user.id, slot_name, slot_time_str],
                kwargs={'prescription_id': prescription_id},
                eta=reminder_time
            )
            print(f"[SCHEDULE] ✅ {slot_name} {slot_time_str} → prescription {prescription_id} at {reminder_time}")
            