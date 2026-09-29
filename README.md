# ☕ Coffee-Barista

An AI-powered coffee recommendation system that understands natural-language coffee preferences and recommends suitable items from a real coffee menu using **RAG, vector search, and multi-agent AI orchestration**.

The system is designed to provide personalized coffee recommendations while enforcing hard constraints such as price, dietary preferences, temperature, availability, and calories.

---

## 🚀 Features

### 🤖 AI-Powered Coffee Recommendations

Users can ask natural-language questions such as:

- "Suggest a strong coffee under ₹400"
- "I want a cold vegan coffee"
- "Give me something low in calories"
- "I want hot coffee"
- "Suggest something dairy-free"
- "What coffee options are available?"

The system extracts the user's preferences and recommends suitable menu items.

---

### 🧠 RAG-Based Recommendation

Coffee-Barista uses **Retrieval-Augmented Generation (RAG)** to retrieve relevant coffee items from the menu before generating recommendations.

The system uses:

- Google Vertex AI Embeddings
- `text-embedding-005`
- Firestore Vector Search
- Cosine similarity
- Structured menu metadata

This allows the system to retrieve semantically relevant coffee items instead of relying only on keyword matching.

---

### 🧩 Multi-Agent AI Architecture

The application uses multiple specialized AI agents built using **Google ADK**.

```text
                    USER
                      │
                      ▼
             Domain Guardrail
                      │
                      ▼
             Preference Agent
                      │
              ┌───────┴────────┐
              │                │
              ▼                ▼
        Preference Data     Vector Search
                               │
                               ▼
                       Candidate Menu Items
                               │
                               ▼
                       Hard Filtering
                               │
                               ▼
                    Recommendation Agent
                               │
                               ▼
                         Validator
                               │
                               ▼
                         FINAL RESPONSE
Agents
1. Domain Guardrail Agent

Determines whether the user's request is related to coffee.

For example:

"Suggest a vegan latte"
→ Coffee related

while:

"What is the capital of India?"
→ Not coffee related

The guardrail also extracts the coffee-related part of mixed queries.

2. Preference Agent

Extracts and maintains coffee preferences from the conversation.

Supported preferences include:

Coffee category
Temperature
Strength
Sweetness
Dairy-free
Vegan
Sugar-free
Minimum price
Maximum price
Maximum calories
Caffeine level

Example:

User:
I want vegan coffee under ₹400

Preferences:
{
    "vegan": true,
    "max_price": 400
}

The agent also uses previous conversation context to understand follow-up requests.

3. Recommendation Agent

Generates the final recommendation using only validated menu candidates.

It is instructed to:

Never invent menu items
Never invent prices
Never invent nutrition information
Recommend only retrieved menu items
Explain why the recommendation matches the user's requirements
🔎 Vector Search

Menu items are converted into embeddings using:

text-embedding-005

The embeddings are stored in Google Cloud Firestore.

Example:

User Query
     │
     ▼
Embedding Model
     │
     ▼
768-dimensional vector
     │
     ▼
Firestore Vector Search
     │
     ▼
Relevant Coffee Items

Firestore uses cosine similarity for vector retrieval.

🛡️ Hard Constraint Filtering

AI-generated preferences are not directly trusted for final filtering.

Retrieved candidates are passed through deterministic Python filtering.

Example constraints:

Price
Dietary preferences
Calories
Availability
Category
Temperature
Currency

For example:

User:
I want vegan coffee under ₹300

The system first retrieves relevant candidates and then removes items that:

Cost more than ₹300
Are not vegan
Are unavailable

This reduces the possibility of the LLM recommending an invalid item.

✅ Recommendation Validation

Before returning recommendations to the user, the generated response is validated against the retrieved menu candidates.

The validator checks that the recommendation:

Exists in the retrieved menu
Uses the correct item name
Uses the correct price
Does not introduce unsupported information
🔐 Authentication

Coffee-Barista uses Firebase Authentication.

Authenticated users can access:

Persistent conversations
Chat history
User preferences
Favorites
Feedback
Personalized recommendations

The backend verifies Firebase authentication tokens instead of trusting an arbitrary user_id sent by the frontend.

👤 Guest Mode

Users can try the application without creating an account.

Guest users receive:

3 free prompts

After the guest limit is reached, the application asks the user to log in or register.

Guest sessions are tracked using a persistent session ID.

guest_sessions/{session_id}
💬 Conversational Chat

The application supports conversational interactions.

For example:

User:
Suggest vegan coffee.

Assistant:
Americano, Nitro Cold Brew...

User:
I want something hot.

Assistant:
Updates the previous preference and searches
for suitable hot vegan coffee.

Conversation history is stored for authenticated users.

Firestore structure:

users/
 └── user_id/
      └── chats/
           └── chat_id/
                └── messages/
❤️ Favorites & Feedback

Authenticated users can save coffee items as favorites and provide feedback.

Firestore structure:

users/
 └── user_id/
      ├── favorites/
      └── feedback/
🗄️ Database Architecture

The application uses Google Cloud Firestore.

Firestore
│
├── menu/
│    └── coffee menu items
│
├── users/
│    └── user_id/
│         ├── chats/
│         │    └── messages/
│         │
│         ├── favorites/
│         │
│         └── feedback/
│
└── guest_sessions/
     └── session_id
📋 Menu Data Structure

Each menu item contains structured information such as:

{
  "name": "Cold Brew Coffee",
  "description": "Smooth, slow-steeped cold brew served over ice.",
  "price": {
    "amount": 395,
    "currency": "INR"
  },
  "category": "coffee",
  "tags": [
    "strong",
    "cold",
    "dairy-free",
    "sugar-free"
  ],
  "dietary": {
    "vegan": true,
    "vegetarian": true,
    "dairy_free": true,
    "sugar_free": true
  },
  "flavor_profile": {
    "sweetness": "low",
    "bitterness": "medium",
    "acidity": "low",
    "body": "medium"
  },
  "serving": {
    "temperature": "cold"
  }
}

Nutrition and caffeine values are stored only when reliable data is available.

🏗️ Technology Stack
Frontend
Streamlit
Python
Firebase Authentication
HTTP/REST API
Backend
FastAPI
Python
Google ADK
Google GenAI SDK
AI / ML
Google Vertex AI
Gemini 2.5 Flash
text-embedding-005
Retrieval-Augmented Generation (RAG)
Multi-agent orchestration
Database
Google Cloud Firestore
Firestore Vector Search
Authentication
Firebase Authentication
Deployment
Google Cloud Run
Google Cloud Platform
📁 Project Structure
Coffee-Barista/
│
├── backend/
│   │
│   ├── agent/
│   │   ├── domain_guardrail.py
│   │   ├── preference.py
│   │   └── recommendation.py
│   │
│   ├── database/
│   │   ├── firestore.py
│   │   └── chat.py
│   │
│   ├── tools/
│   │   ├── menu.py
│   │   ├── filtering.py
│   │   ├── validator.py
│   │   ├── chat.py
│   │   └── ...
│   │
│   ├── main.py
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── app.py
│   └── requirements.txt
│
├── .gitignore
├── README.md
└── ...
