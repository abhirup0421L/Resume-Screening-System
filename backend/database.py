# backend/database.py

import os
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


def get_mongo_uri():
    try:
        return st.secrets["MONGO_URI"]
    except Exception:
        return os.getenv("MONGO_URI")


MONGO_URI = get_mongo_uri()

if not MONGO_URI:
    raise ValueError("MONGO_URI not found. Add it in Streamlit Secrets or .env file.")

client = MongoClient(MONGO_URI)

db = client["resume_ai"]

users_collection = db["users"]
