# backend/auth.py

import random
from datetime import datetime, timedelta
from backend.database import users_collection
from backend.otp_sender import send_otp


OTP_EXPIRY_MINUTES = 5


def generate_otp():
    return str(random.randint(100000, 999999))


def send_login_otp(email):
    otp = generate_otp()

    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    users_collection.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "otp": otp,
                "otp_expires_at": expires_at,
                "verified": False
            }
        },
        upsert=True
    )

    sent = send_otp(email, otp)

    return sent


def verify_otp(email, entered_otp):
    user = users_collection.find_one({"email": email})

    if not user:
        return False, "User not found."

    saved_otp = user.get("otp")
    expires_at = user.get("otp_expires_at")

    if not saved_otp or not expires_at:
        return False, "OTP not found. Please request a new OTP."

    if datetime.utcnow() > expires_at:
        users_collection.update_one(
            {"email": email},
            {
                "$unset": {
                    "otp": "",
                    "otp_expires_at": ""
                }
            }
        )
        return False, "OTP expired. Please request a new OTP."

    if saved_otp == entered_otp:
        users_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "verified": True
                },
                "$unset": {
                    "otp": "",
                    "otp_expires_at": ""
                }
            }
        )
        return True, "OTP verified."

    return False, "Invalid OTP."


def get_user(email):
    return users_collection.find_one({"email": email})


def update_name(email, name):
    users_collection.update_one(
        {"email": email},
        {
            "$set": {
                "name": name
            }
        },
        upsert=True
    )