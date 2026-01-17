import random
from django.core.cache import cache

OTP_EXPIRY_TIME = 300  # OTP expiry time in seconds (5 minutes)

def generate_otp(): 
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))

def store_otp(email, otp):
    """Store the OTP in the cache with an expiry time."""
    cache.set(email, otp, timeout=OTP_EXPIRY_TIME)
    
    return otp

def get_otp(email):
    """Retrieve the OTP for the given email."""
    return cache.get(email) 

def verify_otp(email, otp):
    """Verify the OTP for the given email jodi akvar use kora tah hola to aer use hova nah ae ."""
    stored_otp = cache.get(email)
    if stored_otp and stored_otp == otp:
        cache.delete(email)  # Invalidate OTP after successful verification
        return True
    return False