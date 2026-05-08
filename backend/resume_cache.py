from datetime import datetime, timedelta
from backend.database import cache_collection


CACHE_EXPIRY_MINUTES = 10


def make_resume_hash(resume_text, selected_role):
    import hashlib

    combined = f"{resume_text}-{selected_role}"

    return hashlib.md5(
        combined.encode("utf-8")
    ).hexdigest()


def clear_old_cache():
    expiry_time = datetime.utcnow() - timedelta(minutes=CACHE_EXPIRY_MINUTES)

    cache_collection.delete_many({
        "created_at": {"$lt": expiry_time}
    })


def get_cached_result(resume_hash):

    clear_old_cache()

    return cache_collection.find_one({
        "resume_hash": resume_hash
    })


def save_cached_result(
    resume_hash,
    selected_role,
    ai,
    score,
    matched,
    missing
):

    clear_old_cache()

    cache_collection.update_one(
        {"resume_hash": resume_hash},
        {
            "$set": {
                "resume_hash": resume_hash,
                "selected_role": selected_role,
                "ai": ai,
                "score": score,
                "matched": matched,
                "missing": missing,
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )