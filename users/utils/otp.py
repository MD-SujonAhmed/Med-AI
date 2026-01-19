import random
from django.core.cache import cache

OTP_EXPIRY_TIME = 300  # 5 minutes

def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))

def store_otp(email, otp, purpose):
    """Store OTP in cache with purpose."""
    key = f"{email}_{purpose}"
    cache.set(key, otp, timeout=OTP_EXPIRY_TIME)
    return otp

def verify_otp(email, otp, purpose):
    """Verify OTP for given email and purpose."""
    key = f"{email}_{purpose}"
    stored_otp = cache.get(key)
    if stored_otp and stored_otp == otp:
        cache.delete(key)  # OTP used → invalidate
        # For password reset, mark verified flag
        if purpose == 'password_reset':
            cache.set(f"{email}_password_reset_verified", True, timeout=OTP_EXPIRY_TIME)
        return True
    return False

def is_password_reset_verified(email):
    """Check if OTP for password reset is verified."""
    return cache.get(f"{email}_password_reset_verified")
