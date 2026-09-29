from fastapi import Header, HTTPException
import firebase_admin
from firebase_admin import credentials, auth
import os

import requests

if not firebase_admin._apps:
    cred = credentials.Certificate(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    )

    firebase_admin.initialize_app(cred)

def get_current_user(authorization: str | None = Header(default=None)):

    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )    

    token = authorization.split("Bearer ")[1]

    try:
        decoded_token = auth.verify_id_token(token)

        return decoded_token["uid"]

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )