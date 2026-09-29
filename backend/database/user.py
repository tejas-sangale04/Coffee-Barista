from google.cloud import firestore

def get_user_profile(user_id):

    db = firestore.Client(database="coffee-menu")

    doc = (
        db.collection("users")
        .document(user_id)
        .get()
    )

    if not doc.exists:
        return {}

    return doc.to_dict()