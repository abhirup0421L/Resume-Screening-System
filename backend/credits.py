# backend/credits.py

from backend.database import users_collection


def get_credits(email):
    user = users_collection.find_one({"email": email})

    if not user:
        return 0

    return user.get("credits", 0)


def deduct_credit(email, amount=1):
    user = users_collection.find_one({"email": email})

    if not user:
        return False, "User not found."

    credits = user.get("credits", 0)

    if credits < amount:
        return False, "Not enough credits."

    users_collection.update_one(
        {"email": email},
        {"$inc": {"credits": -amount}}
    )

    return True, "Credit deducted."


def add_credits(email, amount):
    users_collection.update_one(
        {"email": email},
        {"$inc": {"credits": amount}},
        upsert=True
    )