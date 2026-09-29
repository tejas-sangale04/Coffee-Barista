from google.cloud import firestore

from backend.database.firestore import db


def save_feedback(
    user_id,
    item_id,
    feedback,
    reason=None
):

    if not user_id:
        return False

    db.collection("users") \
      .document(user_id) \
      .collection("feedback") \
      .add({
          "item_id": item_id,
          "feedback": feedback,
          "reason": reason,
          "timestamp": firestore.SERVER_TIMESTAMP
      })

    return True