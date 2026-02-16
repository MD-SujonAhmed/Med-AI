from prescriptions.tasks import send_push_notification
from users.models import Users

# Test user (যার Flutter app এ login আছে)
user = Users.objects.get(id=6)

# Send test notification
send_push_notification(user, "Test", "Notification working successfully!")


# from users.models import Users
