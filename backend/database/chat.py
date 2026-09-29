from google.cloud import firestore

from backend.database.firestore import db


def generate_chat_title(user_query: str, max_length: int = 35):

    query = user_query.strip()

    if not query:
        return "New Coffee Chat"

    # Remove extra spaces/newlines
    query = " ".join(query.split())

    # Remove unnecessary punctuation from the end
    query = query.strip(" .,!?")

    # Keep title short
    if len(query) <= max_length:
        return query[0].upper() + query[1:]

    # Cut at the last complete word
    shortened = query[:max_length].rsplit(" ", 1)[0]

    return shortened[0].upper() + shortened[1:] + "..."


def save_message(
    user_id,
    chat_id,
    role,
    content
):

    chat_ref = (
        db.collection("users")
        .document(user_id)
        .collection("chats")
        .document(chat_id)
    )

    # Check whether this chat already exists
    chat_snapshot = chat_ref.get()

    if not chat_snapshot.exists:

        # Create chat using the first user message as title
        title = (
            generate_chat_title(content)
            if role == "user"
            else "New Coffee Chat"
        )

        chat_ref.set(
            {
                "title": title,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP
            }
        )

    else:

        # Existing chat → only update activity time
        chat_ref.set(
            {
                "updated_at": firestore.SERVER_TIMESTAMP
            },
            merge=True
        )

    # Save message
    chat_ref.collection("messages").add(
        {
            "role": role,
            "content": content,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
    )


def get_chat_messages(
    user_id,
    chat_id
):

    messages = (
        db.collection("users")
        .document(user_id)
        .collection("chats")
        .document(chat_id)
        .collection("messages")
        .order_by("timestamp")
        .stream()
    )

    return [
        {
            "id": message.id,
            **message.to_dict()
        }
        for message in messages
    ]


def get_user_chats(user_id):

    chats = (
        db.collection("users")
        .document(user_id)
        .collection("chats")
        .order_by(
            "updated_at",
            direction=firestore.Query.DESCENDING
        )
        .stream()
    )

    result = []

    for chat in chats:

        data = chat.to_dict()

        result.append({
            "chat_id": chat.id,
            "title": data.get(
                "title",
                "New Coffee Chat"
            ),
            "updated_at": data.get(
                "updated_at"
            )
        })

    return result


def delete_chat(user_id: str, chat_id: str):

    chat_ref = (
        db.collection("users")
        .document(user_id)
        .collection("chats")
        .document(chat_id)
    )

    # Delete messages inside the chat
    messages = chat_ref.collection("messages").stream()

    for message in messages:
        message.reference.delete()

    # Delete the chat itself
    chat_ref.delete()

    return True