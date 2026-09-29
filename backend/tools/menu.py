
"""import os
from google import genai
from google.cloud import firestore
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector
from backend.database.firestore import db

def get_menu(query: str):

    client = genai.Client(
        vertexai=True,
        project=os.environ.get("PROJECT_ID"),
        location=os.environ.get("REGION", "us-central1")
    )

    response = client.models.embed_content(
        model="text-embedding-005",
        contents=query
    )

    query_vector = response.embeddings[0].values

    results = db.collection("menu").find_nearest(
        vector_field="embedding",
        query_vector=Vector(query_vector),
        distance_measure=DistanceMeasure.COSINE,
        limit=5
    ).stream()

    items = []

    for doc in results:
        item = doc.to_dict()
        item.pop("embedding", None)
        items.append(item)
        
    return items"""

import os

from google import genai
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector

from backend.database.firestore import db


def get_menu(query: str, limit: int = 5):

    client = genai.Client(
        vertexai=True,
        project=os.environ["PROJECT_ID"],
        location=os.environ.get("REGION", "us-central1")
    )

    # Convert user query into embedding
    response = client.models.embed_content(
        model="text-embedding-005",
        contents=query
    )

    query_vector = response.embeddings[0].values

    # Vector search in Firestore
    results = (
        db.collection("menu")
        .find_nearest(
            vector_field="embedding",
            query_vector=Vector(query_vector),
            distance_measure=DistanceMeasure.COSINE,
            limit=limit
        )
        .stream()
    )

    items = []

    for doc in results:

        item = doc.to_dict()

        # Never send the huge embedding to the LLM
        item.pop("embedding", None)

        item["id"] = doc.id

        items.append(item)

    return items