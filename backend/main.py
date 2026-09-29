from fastapi import FastAPI, HTTPException
from backend.services.recommendation_service import get_recommendation
from backend.tools.guest import check_and_increment_guest
from backend.tools.guest import get_guest_status
from pydantic import BaseModel
import requests
import random
from backend.models.schemas import (
    RecommendationRequest,
    RecommendationResponse
)
from backend.database.chat import delete_chat
from fastapi import Depends
from firebase_admin import auth
from backend.database.firestore import db
from backend.auth import get_current_user
from backend.database.chat import (
    save_message,
    get_chat_messages,
    get_user_chats
)
from backend.tools.favourite import (
    add_favorite as save_favorite,
    remove_favorite,
    get_favorites
)
from backend.tools.feedback import save_feedback
from dotenv import load_dotenv
import os

load_dotenv()


app = FastAPI(
    title="Coffee AI API",
    version="1.0.0"
)


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ==================================================
# RECOMMENDATION
# ==================================================

@app.post("/recommend")
async def recommend(
    request: RecommendationRequest,
    user_id: str = Depends(get_current_user)
):
    print("Authenticated user:", user_id)

    # --------------------------------------------------
    # Guest prompt limit
    # --------------------------------------------------

    if user_id is None:

        allowed, count = check_and_increment_guest(
            request.session_id
        )

        if not allowed:
            raise HTTPException(
                status_code=403,
                detail="Guest prompt limit reached. Please login or register."
            )

    # --------------------------------------------------
    # AI Recommendation Pipeline
    # --------------------------------------------------

    result = await get_recommendation(
        request.query,
        user_id,
        request.chat_id
    )

    # --------------------------------------------------
    # Get final message
    # --------------------------------------------------
    if result.get("message"):
        message = result["message"]
    else:
        intro = result.get("intro", "")
        follow_up = result.get("follow_up","")
        recommendations = result.get("recommendations", [])

        message_parts = []

        # Add Intro block
        if intro:
            message_parts.append(intro)

        # Build clean bulleted list items
        if recommendations:
            rec_items = []
            for item in recommendations:
                name = item.get("name", "")
                price = item.get("price", "")
                reason = item.get("reason", "")

                reason_text = f"\n{reason}" if reason else ""
                
                rec_items.append(
                    f" ☕ <b>{name}</b> — ₹{price}{reason_text}"
                )
            message_parts.append("\n\n".join(rec_items))
        if follow_up:
            message_parts.append(follow_up)

        message = "\n\n".join(message_parts)

    # --------------------------------------------------
    # Save authenticated conversation
    # --------------------------------------------------

    if user_id and request.chat_id:

        save_message(
            user_id=user_id,
            chat_id=request.chat_id,
            role="user",
            content=request.query
        )

        save_message(
            user_id=user_id,
            chat_id=request.chat_id,
            role="assistant",
            content=message
        )

    # --------------------------------------------------
    # Return response
    # --------------------------------------------------

    return {
        "message": message
    }

@app.get("/guest/status")
def guest_status(session_id: str):
    status = get_guest_status(session_id)
    return status

@app.get("/chats")
def chats(user_id: str):

    return {
        "chats": get_user_chats(user_id)
    }


@app.get("/chats/{chat_id}")
def chat_messages(
    chat_id: str,
    user_id: str
):

    return {
        "messages": get_chat_messages(
            user_id,
            chat_id
        )
    }


# ==================================================
# FAVORITES
# ==================================================

@app.post("/favorites")
def add_favorite(
    user_id: str,
    item_id: str
):

    save_favorite(
        user_id=user_id,
        item_id=item_id
    )

    return {
        "success": True
    }


@app.delete("/favorites/{item_id}")
def delete_favorite(
    user_id: str,
    item_id: str
):

    remove_favorite(
        user_id=user_id,
        item_id=item_id
    )

    return {
        "success": True
    }


@app.get("/favorites")
def favorites(
    user_id: str
):

    return {
        "favorites": get_favorites(user_id)
    }


# ==================================================
# FEEDBACK
# ==================================================

@app.post("/feedback")
def feedback(
    user_id: str,
    item_id: str,
    feedback_type: str,
    reason: str | None = None
):

    save_feedback(
        user_id=user_id,
        item_id=item_id,
        feedback=feedback_type,
        reason=reason
    )

    return {
        "success": True
    }

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
if not BREVO_API_KEY:
    raise RuntimeError("BREVO_API_KEY is not configured")
SENDER_EMAIL = "smarthealmoduledeep@gmail.com"
SENDER_NAME = "AI Coffee Shop"

# In-memory OTP storage (use Redis or Database in production)
otp_store = {}
users_db = {}

class OTPRequest(BaseModel):
    email: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class RegisterRequest(BaseModel):
    email: str
    password: str

def send_brevo_otp(to_email: str, otp: str):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": "Your Verification Code - AI Coffee Shop",
        "htmlContent": f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #0A0A0C; color: #ffffff; border-radius: 10px;">
            <h2 style="color: #3182CE;">Verification Code</h2>
            <p>Your OTP for account registration is:</p>
            <h1 style="background-color: #1E2028; padding: 10px 20px; display: inline-block; border-radius: 8px; letter-spacing: 4px; color: #FFFFFF;">{otp}</h1>
            <p style="color: #A0AAB8;">This code is valid for 5 minutes. Do not share it with anyone.</p>
        </div>
        """
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 201

@app.post("/send-otp")
def send_otp(data: OTPRequest):
    otp = str(random.randint(100000, 999999))
    otp_store[data.email] = otp
    
    if send_brevo_otp(data.email, otp):
        return {"message": "OTP sent successfully!"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send OTP via Brevo.")

@app.post("/verify-otp")
def verify_otp(data: OTPVerifyRequest):
    stored_otp = otp_store.get(data.email)
    if stored_otp and stored_otp == data.otp:
        del otp_store[data.email]  # Clear OTP after verification
        return {"status": "success", "message": "Email verified successfully!"}
    raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

@app.post("/register")
def register(
    request: RegisterRequest
):
    try:
        firebase_user = auth.create_user(
            email=request.email,
            password=request.password
        )
        return {
            "message": "Account created successfully",
            "user_id": firebase_user.uid
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
@app.delete("/chats/{chat_id}")
def delete_chat_endpoint(
    chat_id: str,
    user_id: str = Depends(get_current_user)
):
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    delete_chat(user_id, chat_id)

    return {
        "message": "Chat deleted successfully"
    }