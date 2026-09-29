from google.cloud import firestore


def add_favorite(user_id, item_id):

    db = firestore.Client(database="coffee-menu")

    (
        db.collection("users")
        .document(user_id)
        .collection("favorites")
        .document(item_id)
        .set({
            "saved_at": firestore.SERVER_TIMESTAMP
        })
    )


def remove_favorite(user_id, item_id):

    db = firestore.Client(database="coffee-menu")

    (
        db.collection("users")
        .document(user_id)
        .collection("favorites")
        .document(item_id)
        .delete()
    )


def get_favorites(user_id):

    db = firestore.Client(database="coffee-menu")

    favorites = (
        db.collection("users")
        .document(user_id)
        .collection("favorites")
        .stream()
    )

    return [
        {
            "item_id": doc.id,
            **doc.to_dict()
        }
        for doc in favorites
    ]