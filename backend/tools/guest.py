from google.cloud import firestore
from backend.database.firestore import db


MAX_GUEST_PROMPTS = 3


def check_and_increment_guest(session_id:str):

    ref = db.collection("guest_sessions").document(session_id)

    doc = ref.get()

    if not doc.exists:
        ref.set({
            "prompt_count": 1,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        })

        return True, 1

    data = doc.to_dict()
    count = data.get("prompt_count", 0)

    if count >= MAX_GUEST_PROMPTS:
        return False, count

    new_count = count + 1

    ref.update({
        "prompt_count": new_count,
        "updated_at": firestore.SERVER_TIMESTAMP
    })

    return True, new_count

def get_guest_status(session_id: str):

    ref = db.collection("guest_sessions").document(session_id)

    doc = ref.get()

    if not doc.exists:
        return {
            "prompt_count": 0,
            "limit_reached": False
        }

    data = doc.to_dict()

    count = data.get("prompt_count", 0)

    return {
        "prompt_count": count,
        "limit_reached": count >= MAX_GUEST_PROMPTS
    }