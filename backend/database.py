import random
import bcrypt
from datetime import datetime, timedelta
from backend.database import users_collection
from backend.otp_sender import send_otp

OTP_EXPIRY_MINUTES = 5


def clean_email(email):
    return email.strip().lower()


def generate_otp():
    return str(random.randint(100000, 999999))


def hash_password(password):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def check_password(password, hashed_password):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def send_login_otp(email):
    email = clean_email(email)

    existing_user = users_collection.find_one({"email": email})

    if existing_user and existing_user.get("verified") and existing_user.get("password_hash"):
        return False

    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    update_data = {
        "email": email,
        "otp": otp,
        "otp_expires_at": expires_at,
        "verified": False,
        "updated_at": datetime.utcnow()
    }

    if not existing_user:
        update_data["created_at"] = datetime.utcnow()

    users_collection.update_one(
        {"email": email},
        {"$set": update_data},
        upsert=True
    )

    return send_otp(email, otp)


def verify_otp_only(email, entered_otp):
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
            {"$unset": {"otp": "", "otp_expires_at": ""}}
        )
        return False, "OTP expired. Please send OTP again."

    if saved_otp != entered_otp:
        return False, "Invalid OTP."

    return True, "OTP verified."


def verify_otp_and_create_account(email, entered_otp, password):
    email = clean_email(email)
    entered_otp = entered_otp.strip()

    user = users_collection.find_one({"email": email})

    if user and user.get("verified") and user.get("password_hash"):
        return True, "Account created successfully."

    if not user:
        return False, "User not found. Please send OTP again."

    saved_otp = user.get("otp")
    expires_at = user.get("otp_expires_at")

    if not saved_otp or not expires_at:
        return False, "OTP not found. Please send OTP again."

    if datetime.utcnow() > expires_at:
        users_collection.update_one(
            {"email": email},
            {"$unset": {"otp": "", "otp_expires_at": ""}}
        )
        return False, "OTP expired. Please send OTP again."

    if saved_otp != entered_otp:
        return False, "Invalid OTP."

    hashed_password = hash_password(password)

    users_collection.update_one(
        {"email": email},
        {
            "$set": {
                "verified": True,
                "password_hash": hashed_password,
                "credits": 100,
                "last_login": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            "$unset": {
                "otp": "",
                "otp_expires_at": "",
                "password": ""
            }
        }
    )

    return True, "Account created successfully."


def login_user(email, password):
    email = clean_email(email)

    user = users_collection.find_one({"email": email})

    if not user:
        return False, "Account not found. Please create account first."

    if not user.get("verified"):
        return False, "Account not verified. Please create account again."

    password_hash = user.get("password_hash")

    if not password_hash:
        return False, "Password not set. Please create account again."

    if not check_password(password, password_hash):
        return False, "Incorrect password."

    users_collection.update_one(
        {"email": email},
        {"$set": {"last_login": datetime.utcnow()}}
    )

    return True, "Login successful."


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
