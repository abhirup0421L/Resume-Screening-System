# backend/gemini_queue.py

import time
from datetime import datetime, timedelta
from backend.database import api_usage_collection

MAX_REQUESTS_PER_MINUTE = 15


def wait_for_gemini_slot():
    while True:
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(seconds=60)

        api_usage_collection.delete_many({
            "created_at": {"$lt": one_minute_ago}
        })

        current_count = api_usage_collection.count_documents({
            "created_at": {"$gte": one_minute_ago}
        })

        if current_count < MAX_REQUESTS_PER_MINUTE:
            api_usage_collection.insert_one({
                "created_at": now
            })
            return True

        time.sleep(4)