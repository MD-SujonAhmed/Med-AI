from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(email, otp, purpose):
    """
    purpose:
    - 'signup'
    - 'forgot_password'
    """

    if purpose == "signup":
        subject = "Verify Your Email - OTP"
        message = f"""
Hello,

Your OTP for email verification is: {otp}

This OTP will expire in 5 minutes.
If you did not create an account, please ignore this email.

Thank you,
Support Team
"""

    elif purpose == "password_reset":
        subject = "Password Reset OTP"
        message = f"""
Hello,

Your OTP for password reset is: {otp}

This OTP will expire in 5 minutes.
If you did not request a password reset, please ignore this email.

Thank you,
Support Team
"""

    else:
        raise ValueError("Invalid OTP purpose")

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

# 