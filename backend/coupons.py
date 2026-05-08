import secrets
import string
from datetime import datetime, timedelta
from backend.database import coupons_collection, users_collection


def generate_coupon_code(length=13):
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_coupon(credits, duration_hours):
    code = generate_coupon_code()

    while coupons_collection.find_one({"code": code}):
        code = generate_coupon_code()

    coupon = {
        "code": code,
        "credits": int(credits),
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=int(duration_hours)),
        "redeemed_by": []
    }

    coupons_collection.insert_one(coupon)

    return code


def claim_coupon(email, code):
    email = email.strip().lower()
    code = code.strip().lower()

    coupon = coupons_collection.find_one({"code": code})

    if not coupon:
        return False, "Invalid or expired coupon code."

    if datetime.utcnow() > coupon["expires_at"]:
        coupons_collection.delete_one({"code": code})
        return False, "Coupon code expired."

    if email in coupon.get("redeemed_by", []):
        return False, "You already used this coupon."

    credits = int(coupon.get("credits", 0))

    users_collection.update_one(
        {"email": email},
        {"$inc": {"credits": credits}}
    )

    coupons_collection.update_one(
        {"code": code},
        {"$push": {"redeemed_by": email}}
    )

    return True, f"Coupon applied successfully. {credits} credits added."