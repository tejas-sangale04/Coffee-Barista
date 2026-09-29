import asyncio
import json

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from backend.agents.preference import preference_agent
from backend.agents.recommendation import recommendation_agent

from backend.tools.menu import get_menu
from backend.tools.filtering import filter_candidates
from backend.tools.validator import validate_recommendations
from backend.database.chat import get_chat_messages
from backend.agents.domain_guardrail import domain_guardrail

APP_NAME = "coffee_barista"
USER_ID = "recommendation_service"
SESSION_ID = "recommendation_session"

async def run_agent(agent, prompt):
    """
    Run an ADK agent and return its final text response.
    """

    session_service = InMemorySessionService()

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=prompt)
        ]
    )

    response_text = ""

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=message
    ):
        if event.is_final_response():

            if event.content and event.content.parts:

                for part in event.content.parts:

                    if part.text:
                        response_text += part.text

    return response_text

def parse_json_response(response_text):
    response_text = response_text.strip()

    if response_text.startswith("```json"):
        response_text = response_text[7:]

    elif response_text.startswith("```"):
        response_text = response_text[3:]

    if response_text.endswith("```"):
        response_text = response_text[:-3]

    return json.loads(response_text.strip())

async def check_domain(user_query: str):
    response = await run_agent(
        domain_guardrail,
        user_query
    )

    try:
        return parse_json_response(response)

    except json.JSONDecodeError:
        return {
            "is_coffee_related": False,
            "coffee_query": None
        }

async def get_recommendation(user_query: str, user_id: str = None, chat_id: str = None):
    # -----------------------------
    # DOMAIN GUARDRAIL
    # -----------------------------

    domain_result = await check_domain(user_query)
    print("DOMAIN GUARDRAIL RESULT:", domain_result)

    if not domain_result.get("is_coffee_related"):
        return {
            "success": True,
            "message": (
                "I can help with coffee, coffee menu items, "
                "recommendations, nutrition, ingredients, "
                "dietary preferences, and related topics. "
                "Please ask me something coffee-related."
            ),
            "preferences": None,
            "recommendations": []
        }

    coffee_query = domain_result.get(
        "coffee_query",
        user_query
    )

    # --------------------------------------------------
    # STEP 1: Extract user preferences
    # --------------------------------------------------
    # --------------------------------------------------
    chat_history = []

    if user_id and chat_id:
        chat_history = get_chat_messages(
            user_id,
            chat_id
        )

    conversation_context = ""

    for message in chat_history:
        conversation_context += (
            f"{message['role']}: {message['content']}\n"
        )
    
    preference_prompt = f"""
    Previous conversation:
    {conversation_context}

    Current user message:
    {coffee_query}
    """

    preference_task = run_agent(
        preference_agent,
        preference_prompt
    )

    search_task = asyncio.to_thread(
            get_menu,
            coffee_query,
            limit=5
        )
    preference_response, candidates = await asyncio.gather(
        preference_task,
        search_task
        )
    

    try:
        preferences = parse_json_response(preference_response)

    except json.JSONDecodeError:

        return {
            "success": False,
            "message": "Could not understand your preferences.",
            "preferences": None,
            "recommendations": []
        }
    
    # --------------------------------------------------
    # STEP 3: Apply hard constraints
    # --------------------------------------------------
    filtered_candidates = filter_candidates(
        candidates,
        preferences
    )

    # --------------------------------------------------
    # STEP 4: No matching items
    # --------------------------------------------------

    if not filtered_candidates:

        return {
            "success": True,
            "message": "Sorry, I couldn't find any menu items matching your requirements.",
            "preferences": preferences,
            "recommendations": []
        }


    # --------------------------------------------------
    # STEP 5: Recommendation Agent
    # --------------------------------------------------

    recommendation_prompt = f"""
User request:
{coffee_query}

Extracted preferences:
{json.dumps(preferences, ensure_ascii=False, indent=2)}

Validated menu items:
{json.dumps(filtered_candidates, ensure_ascii=False, indent=2)}
"""
   
    recommendation_response = await run_agent(
        recommendation_agent,
        recommendation_prompt
    )

    # --------------------------------------------------
    # STEP 6: Parse Recommendation Agent JSON
    # --------------------------------------------------

    try:
        recommendation_data = parse_json_response(
            recommendation_response
        )

    except json.JSONDecodeError:

        return {
            "success": False,
            "message": "The recommendation service returned an invalid response.",
            "preferences": preferences,
            "recommendations": []
        }


    recommendations = recommendation_data.get(
        "recommendations",
        []
    )


    # --------------------------------------------------
    # STEP 7: Validate recommendations
    # --------------------------------------------------

    validation_result = validate_recommendations(
        recommendations,
        filtered_candidates
    )


    # --------------------------------------------------
    # STEP 8: Reject invalid recommendations
    # --------------------------------------------------

    if not validation_result["valid"]:

        return {
            "success": False,
            "message": "The recommendation could not be validated.",
            "preferences": preferences,
            "recommendations": [],
            "validation": validation_result
        }


    # --------------------------------------------------
    # STEP 9: Return final result
    # --------------------------------------------------

    return {
        "success": True,
        "preferences": preferences,
        "recommendations": recommendations,
        "follow_up": recommendation_data.get(
            "follow_up",
            ""
        )
    }