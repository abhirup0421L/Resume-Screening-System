from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["resume_ai"]

users_collection = db["users"]
cache_collection = db["resume_cache"]
api_usage_collection = db["api_usage"]
coupons_collection = db["coupons"]

cache_collection.create_index(
    "created_at",
    expireAfterSeconds=600
)

coupons_collection.create_index(
    "expires_at",
    expireAfterSeconds=0
)
