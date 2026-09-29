import json
import os

from google import genai
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector


# Firestore
db = firestore.Client(database="coffee-menu")


# Vertex AI
client = genai.Client(
    vertexai=True,
    project=os.environ["PROJECT_ID"],
    location=os.environ.get("REGION", "us-central1")
)


# Load menu
with open("menu.json", "r", encoding="utf-8") as f:
    menu_items = json.load(f)


for item in menu_items:

    # Document ID
    doc_id = item["name"].lower().replace(" ", "-")


    # Text used for semantic embedding
    text_to_embed = f"""
    Name: {item.get('name', '')}
    Description: {item.get('description', '')}
    Category: {item.get('category', '')}
    Subcategory: {item.get('subcategory', '')}

    Tags: {', '.join(item.get('tags', []))}
    Ingredients: {', '.join(item.get('ingredients', []))}

    Dietary:
    {item.get('dietary', {})}

    Flavor profile:
    {item.get('flavor_profile', {})}

    Serving:
    {item.get('serving', {})}

    Nutrition:
    {item.get('nutrition', {})}
    """


    # Generate embedding
    response = client.models.embed_content(
        model="text-embedding-005",
        contents=text_to_embed
    )

    embedding = response.embeddings[0].values


    # Store vector in Firestore
    item["embedding"] = Vector(embedding)

    db.collection("menu").document(doc_id).set(item)

    print(f"Seeded: {item['name']}")


print("\nFirestore menu collection seeded successfully!")