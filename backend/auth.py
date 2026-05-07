# backend/auth.py

import random
from datetime import datetime, timedelta
from backend.database import users_collection
from backend.otp_sender import send_otp

OTP_EXPIRY_MINUTES = 5


def clean_email(email):
    return email.strip().lower()


def generate_otp():
    return str(random.randint(100000, 999999))


def send_login_otp(email):
    email = clean_email(email)
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    existing_user = users_collection.find_one({"email": email})

    update_data = {
        "email": email,
        "otp": otp,
        "otp_expires_at": expires_at,
        "updated_at": datetime.utcnow()
    }

    # Only new users get verified False
    if not existing_user:
        update_data["verified"] = False
        update_data["created_at"] = datetime.utcnow()

    users_collection.update_one(
        {"email": email},
        {"$set": update_data},
        upsert=True
    )

    sent = send_otp(email, otp)
    return sent


def verify_otp(email, entered_otp):
    email = clean_email(email)
    entered_otp = entered_otp.strip()

    user = users_collection.find_one({"email": email})

    if not user:
        return False, "User not found. Please send OTP again."

    saved_otp = user.get("otp")
    expires_at = user.get("otp_expires_at")

    if not saved_otp or not expires_at:
        return False, "OTP not found. Please send OTP again."

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
        return False, "OTP expired. Please send OTP again."

    if saved_otp != entered_otp:
        return False, "Invalid OTP. Please enter the latest OTP sent to your email."

    users_collection.update_one(
        {"email": email},
        {
            "$set": {
                "verified": True,
                "last_login": datetime.utcnow()
            },
            "$unset": {
                "otp": "",
                "otp_expires_at": ""
            }
        }
    )

    return True, "OTP verified successfully."


def get_user(email):
    email = clean_email(email)
    return users_collection.find_one({"email": email})


def update_name(email, name):
    email = clean_email(email)

    users_collection.update_one(
        {"email": email},
        {
            "$set": {
                "name": name,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )
