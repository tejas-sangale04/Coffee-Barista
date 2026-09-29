#import logging
import warnings
import os
import requests
import uuid

#warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=DeprecationWarning)
#logging.getLogger("streamlit").setLevel(logging.ERROR)

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from dotenv import load_dotenv
load_dotenv()
API_URL = "http://127.0.0.1:8000"
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

# 1. PAGE CONFIGURATION (Must be the first Streamlit command)
st.set_page_config(
    page_title="Coffee Shop - AI Barista",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>

/* ================================
   CHATGPT STYLE CHAT UI
   ================================ */

/* Remove Streamlit's default chat message styling */
.chat-container {
    width: 100%;
    max-width: 850px;
    margin: 0 auto;
}

/* Each message row */
.chat-row {
    width: 100%;
    display: flex;
    margin-bottom: 20px;
}

/* User message */
.user-row {
    justify-content: flex-end;
}

/* Assistant message */
.assistant-row {
    justify-content: flex-start;
}

/* Message content */
.chat-bubble {
    max-width: 80%;
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 16px;
    line-height: 1.6;
}

/* User bubble */
.user-bubble {
    max-width: 75%;
    background-color: #2F323B;
    color: #FFFFFF;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    font-size: 15px;
    line-height: 1.5;
}

/* Assistant response */
.assistant-bubble {
    max-width: 80%;
    background-color: #1A1D24;
    border: 1px solid #2B2E38;
    color: #E2E8F0;
    padding: 16px 20px;
    border-radius: 18px 18px 18px 4px;
    font-size: 15px;
    line-height: 1.6;
}
.assistant-bubble p {
    margin-bottom: 12px;
}

.assistant-bubble p:last-child {
    margin-bottom: 0;
}

.assistant-bubble ul {
    margin: 8px 0 12px 20px;
    padding: 0;
}

.assistant-bubble li {
    margin-bottom: 8px;
}
/* Remove paragraph margin */
.chat-bubble p {
    margin: 0;
}

/* Mobile */
@media (max-width: 768px) {
    .chat-bubble {
        max-width: 90%;
    }
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* Input text */
[data-testid="stTextInput"] input {
    color: #111111 !important;
    caret-color: #111111 !important;
}

/* Light theme */
[data-theme="light"] [data-testid="stTextInput"] input {
    background-color: #ffffff !important;
    color: #111111 !important;
}

/* Dark theme */
[data-theme="dark"] [data-testid="stTextInput"] input {
    background-color: #1E1E1E !important;
    color: #FFFFFF !important;
}

[data-testid="stTextInput"] input::placeholder {
    color: #777777 !important;
}

[data-testid="stStatusWidget"] {
        display: none !important;
    }

</style>
""", unsafe_allow_html=True)

# 2. GLOBAL CSS STYLES (Injected before any conditionally rendered layouts)

# 3. COOKIE INITIALIZATION
cookies = EncryptedCookieManager(
    prefix="coffee_barista/",
    password=os.environ.get("COOKIES_PASSWORD", "change-this-secret-in-production")
)

if not cookies.ready():
    st.stop()

# 4. SESSION STATE LOGIC
cookie_session_id = st.context.cookies.get("session_id") or cookies.get("session_id")
cookie_user_id = cookies.get("user_id")
cookie_id_token = cookies.get("id_token")
cookie_show_login = cookies.get("show_login")
cookie_user_email = cookies.get("user_email")

if "session_id" not in st.session_state:
    if cookie_session_id:
        st.session_state.session_id = cookie_session_id
    else:
        new_sid = str(uuid.uuid4())
        st.session_state.session_id = new_sid
        cookies["session_id"] = new_sid
        cookies.save()

if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())

if cookie_user_id == "":
    cookie_user_id = None

if "user_id" not in st.session_state:
    st.session_state.user_id = cookie_user_id

if "show_login" not in st.session_state:
    st.session_state.show_login = (cookie_show_login == "true")

if "user_email" not in st.session_state:
    st.session_state.user_email = cookie_user_email

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Welcome to ☕ Coffee Shop! What kind of coffee or treat are you craving today?"
        }
    ]

if "id_token" not in st.session_state:
    st.session_state.id_token = cookie_id_token

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login"

if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False

if "email_verified" not in st.session_state:
    st.session_state.email_verified = False

# Guest Limit Checking
if not st.session_state.user_id:
    try:
        status_res = requests.get(
            f"{API_URL}/guest/status",
            params={"session_id": st.session_state.session_id},
            timeout=5
        )
        status_res.raise_for_status()
        guest_status = status_res.json()
        st.session_state.show_login = guest_status.get("limit_reached", False)
    except requests.exceptions.RequestException:
        st.session_state.show_login = False
else:
    st.session_state.show_login = False

# Helper Functions
def ask_barista(prompt: str, session_id: str, user_id: str = None, chat_id: str = None):
    try:
        if not user_id:
            if not st.session_state.show_login:
                try:
                    status_res = requests.get(
                        f"{API_URL}/guest/status",
                        params={"session_id": st.session_state.session_id},
                        timeout=5
                    )
                    status_res.raise_for_status()
                    guest_status = status_res.json()
                    st.session_state.show_login = guest_status.get("limit_reached", False)
                except requests.exceptions.RequestException:
                    st.session_state.show_login = False
        else:
            st.session_state.show_login = False

        headers = {}
        if st.session_state.id_token:
            headers["Authorization"] = f"Bearer {st.session_state.id_token}"

        recommend_response = requests.post(
            f"{API_URL}/recommend",
            json={"query": prompt, "session_id": session_id, "chat_id": chat_id},
            headers=headers,
            timeout=30
        )
        recommend_response.raise_for_status()
        data = recommend_response.json()

        if data.get("limit_reached"):
            st.session_state.show_login = True
            return data

        return data
    except requests.exceptions.RequestException as e:
        return {"message": f"Sorry, I couldn't reach the server. ({e})"}

def firebase_login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    response = requests.post(
        url,
        json={"email": email, "password": password, "returnSecureToken": True}
    )
    if response.ok:
        return response.json()
    return None

# FULLSCREEN LOGIN / REGISTER + BREVO OTP SCREEN
if not st.session_state.user_id and st.session_state.show_login:
    col1, col2, col3 = st.columns([1, 1.1, 1])

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("""
                <style>
                div[data-testid="stVerticalBlockBorderWrapper"] {
                    background: #111318;
                    border: 1px solid #343842;
                    border-radius: 22px;
                    padding: 35px 40px 30px 40px;
                    max-width: 420px;
                    width: 90%;
                    margin: 40px auto !important;
                    box-shadow:
                        0 0 0 1px rgba(255,255,255,0.03),
                        0 15px 40px rgba(0,0,0,0.65);
                }

                /* Input box */
                    div[data-baseweb="input"] {
                        border-radius: 8px !important;
                    }

                    /* Input text automatically follows Streamlit theme */
                    div[data-baseweb="input"] input {
                        color: var(--text-color) !important;
                        -webkit-text-fill-color: var(--text-color) !important;
                        caret-color: var(--text-color) !important;
                    }

                    /* Input background */
                    div[data-baseweb="input"] {
                        background-color: var(--secondary-background-color) !important;
                    }

                    /* Labels */
                    div[data-testid="stTextInput"] label {
                        color: var(--text-color) !important;
                    }

                    /* Placeholder */
                    div[data-baseweb="input"] input::placeholder {
                        color: #777777 !important;
                    }

                label {
                    color: #E5E7EB !important;
                }

                button {
                    border-radius: 8px !important;
                }
                </style>
                """, unsafe_allow_html=True)
            st.markdown(
                f"""
                <h1 style="
                    color: #FFFFFF;
                    font-size: 2.2rem;
                    font-weight: 600;
                    text-align: center;
                    margin: 0 0 25px 0;
                    letter-spacing: -0.5px;
                ">
                    {st.session_state.auth_mode}
                </h1>
                """,
                unsafe_allow_html=True
            )

            if st.session_state.auth_mode == "Login":
                email = st.text_input("Email", key="login_user", placeholder="Enter your registered email")
                password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")

                if st.button("Login", type="primary", use_container_width=True):
                    if email and password:
                        result = firebase_login(email, password)
                        if result:
                            st.session_state.user_id = result["localId"]
                            st.session_state.id_token = result["idToken"]
                            st.session_state.user_email = result["email"]
                            st.session_state.show_login = False

                            cookies["user_id"] = result["localId"]
                            cookies["id_token"] = result["idToken"]
                            cookies["refresh_token"] = result["refreshToken"]
                            cookies["user_email"] = result["email"]
                            if "show_login" in cookies:
                                del cookies["show_login"]
                            cookies.save()

                            st.session_state.show_login = False
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")
                    else:
                        st.error("Please enter an email and password.")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Don't have an account? Register", type="secondary", use_container_width=True):
                    st.session_state.auth_mode = "Register"
                    st.session_state.otp_sent = False
                    st.session_state.email_verified = False
                    st.rerun()

            else:
                if not st.session_state.otp_sent:
                    email = st.text_input("Email Address", key="reg_email", placeholder="example@email.com")

                    if st.button("Send OTP", type="primary", use_container_width=True):
                        if email:
                            try:
                                res = requests.post(f"{API_URL}/send-otp", json={"email": email}, timeout=5)
                                if res.ok:
                                    st.session_state.reg_target_email = email
                                    st.session_state.otp_sent = True
                                    st.success("OTP sent to your email!")
                                    st.rerun()
                                else:
                                    st.error("Failed to send OTP. Please check email address.")
                            except Exception:
                                st.error("Server connection error.")
                        else:
                            st.error("Please enter a valid email.")

                elif not st.session_state.email_verified:
                    st.info(f"OTP sent to **{st.session_state.get('reg_target_email', '')}**")
                    otp_input = st.text_input("Enter 6-Digit OTP", key="reg_otp", placeholder="123456")

                    if st.button("Verify OTP", type="primary", use_container_width=True):
                        try:
                            res = requests.post(
                                f"{API_URL}/verify-otp",
                                json={"email": st.session_state.reg_target_email, "otp": otp_input},
                                timeout=5
                            )
                            if res.ok:
                                st.session_state.email_verified = True
                                st.success("Email verified! Create your account credentials.")
                                st.rerun()
                            else:
                                st.error("Invalid or expired OTP.")
                        except Exception:
                            st.error("Server connection error.")

                else:
                    st.success("Email Verified ✓")
                    new_password = st.text_input("Create Password", type="password", key="reg_pass", placeholder="Create password")
                    confirm_password = st.text_input("Confirm Password", type="password", key="reg_pass_conf", placeholder="Confirm password")

                    if st.button("Create Account", type="primary", use_container_width=True):
                        if not new_password or not confirm_password:
                            st.error("Please fill in all fields.")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match!")
                        else:
                            try:
                                reg_res = requests.post(
                                    f"{API_URL}/register",
                                    json={
                                        "email": st.session_state.reg_target_email,
                                        "password": new_password
                                    },
                                    timeout=5
                                )
                                if reg_res.ok:
                                    st.session_state.auth_mode = "Login"
                                    st.session_state.otp_sent = False
                                    st.session_state.email_verified = False
                                    st.success("Account created successfully! Please login.")
                                    st.rerun()
                                else:
                                    st.error(reg_res.json().get("detail", "Registration failed."))
                            except Exception:
                                st.error("Server connection error.")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Already have an account? Login", type="secondary", use_container_width=True):
                    st.session_state.auth_mode = "Login"
                    st.session_state.otp_sent = False
                    st.session_state.email_verified = False
                    st.rerun()

# MAIN CHAT INTERFACE
# MAIN CHAT INTERFACE
else:
    with st.sidebar:

        st.title("☕ Coffee AI")
        st.divider()

        # ================================
        # NEW CHAT
        # ================================

        if st.button(
            "＋ New Chat",
            use_container_width=True
        ):
            st.session_state.chat_id = str(uuid.uuid4())

            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "☕ What kind of coffee are you looking for?"
                }
            ]

            st.rerun()

        st.divider()

        st.subheader("Recent Chats")

        # ================================
        # SIDEBAR STYLES
        # ================================

        st.markdown("""
        <style>

        /* ================================
           SIDEBAR
        ================================ */

        [data-testid="stSidebar"] {
            background-color: #050505 !important;
            border-right: 1px solid #1E2028 !important;
        }

        [data-testid="stSidebarUserContent"] {
            display: flex !important;
            flex-direction: column !important;
            height: 100vh !important;
            box-sizing: border-box !important;
        }

        /* ================================
           PROFILE + LOGOUT AREA
        ================================ */

        .profile-wrapper {
            width: 100% !important;
            box-sizing: border-box !important;
            margin: 0 0 10px 0 !important;
        }

        .profile-container {
            width: 100% !important;
            box-sizing: border-box !important;
            background-color: #18191E;
            border: 1px solid #2E3240;
            border-radius: 12px;
            padding: 10px 12px;
            display: flex;
            align-items: center;
            gap: 10px;
            overflow: hidden;
        }

        .profile-avatar {
            width: 36px;
            height: 36px;
            min-width: 36px;
            border-radius: 50%;
            background-color: #E685B5;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9rem;
            flex-shrink: 0;
        }

        .profile-info {
            flex: 1;
            min-width: 0;
            overflow: hidden;
        }

        .profile-name {
            display: block;
            color: white;
            font-size: 0.85rem;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* ================================
           LOGOUT BUTTON
        ================================ */

        div[data-testid="stSidebar"] button[key="sidebar_logout_btn"] {
            width: 100% !important;
            box-sizing: border-box !important;
            height: 42px !important;
            background-color: #262931 !important;
            color: #FF6B6B !important;
            border: 1px solid #3E4452 !important;
            border-radius: 10px !important;
            font-weight: 500 !important;
        }

        div[data-testid="stSidebar"] button[key="sidebar_logout_btn"]:hover {
            background-color: #DC2626 !important;
            color: white !important;
            border-color: #DC2626 !important;
        }

        /* ================================
           MOBILE
        ================================ */

        @media (max-width: 768px) {

            .profile-container {
                padding: 8px 10px !important;
            }

            .profile-avatar {
                width: 34px !important;
                height: 34px !important;
                min-width: 34px !important;
            }

            .profile-name {
                font-size: 0.8rem !important;
            }

                        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child,
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {
        width: 32px !important;
        min-width: 32px !important;
        max-width: 32px !important;
        flex: 0 0 32px !important;
    }

    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child button,
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child button {
        width: 32px !important;
        min-width: 32px !important;
        max-width: 32px !important;
        height: 34px !important;
        min-height: 34px !important;
        padding: 0 !important;
        font-size: 12px !important;
    }

    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child,
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {
        width: calc(100% - 36px) !important;
        flex: 1 1 auto !important;
    }

        }

        </style>
        """, unsafe_allow_html=True)

        st.markdown(
    """
    <style>
    /* Prevent horizontal scrolling in sidebar */
    [data-testid="stSidebar"] {
        overflow-x: hidden !important;
    }

    /* Force row layout with no line wrapping */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 4px !important;
    }

    @media (min-width: 769px) {
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child,
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {
            width: calc(100% - 42px) !important;
            min-width: 0 !important;
            flex: 1 1 auto !important;
        }

        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child,
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {
            width: 38px !important;
            min-width: 38px !important;
            max-width: 38px !important;
            flex: 0 0 38px !important;
        }

        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child button,
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child button {
            padding: 0px !important;
            height: 42px !important;
            min-height: 42px !important;
            font-size: 13px !important;
            line-height: 1 !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)
        st.markdown(
    """
    <style>

    /* Hide Deploy button */
    [data-testid="stAppDeployButton"] {
        display: none !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


        # ================================
        # RECENT CHATS
        # ================================

        if st.session_state.user_id:

            try:

                res = requests.get(
                    f"{API_URL}/chats",
                    params={
                        "user_id": st.session_state.user_id
                    }
                )

                if res.ok:

                    chats = res.json().get("chats", [])

                    for chat in chats:

                        chat_id = chat["chat_id"]

                        col1, col2 = st.columns(
                            [0.9, 0.1],
                            gap="small"
                        )

                        # ----------------
                        # CHAT BUTTON
                        # ----------------

                        with col1:

                            if st.button(
                                chat.get(
                                    "title",
                                    "Saved Chat"
                                ),
                                key=f"chat_{chat_id}",
                                use_container_width=True
                            ):

                                st.session_state.chat_id = chat_id

                                headers = {
                                    "Authorization":
                                        f"Bearer {st.session_state.id_token}"
                                }

                                msg_res = requests.get(
                                    f"{API_URL}/chats/{chat_id}",
                                    params={
                                        "user_id":
                                            st.session_state.user_id
                                    },
                                    headers=headers,
                                    timeout=10
                                )

                                if msg_res.ok:

                                    st.session_state.messages = (
                                        msg_res.json().get(
                                            "messages",
                                            []
                                        )
                                    )

                                st.rerun()

                        # ----------------
                        # DELETE BUTTON
                        # ----------------

                        with col2:

                            if st.button(
                                "✕",
                                key=f"delete_{chat_id}",
                                help="Delete chat",
                                use_container_width=True
                            ):

                                headers = {
                                    "Authorization":
                                        f"Bearer {st.session_state.id_token}"
                                }

                                delete_res = requests.delete(
                                    f"{API_URL}/chats/{chat_id}",
                                    headers=headers,
                                    timeout=10
                                )

                                if delete_res.ok:

                                    if (
                                        st.session_state.chat_id
                                        == chat_id
                                    ):

                                        st.session_state.chat_id = (
                                            str(uuid.uuid4())
                                        )

                                        st.session_state.messages = [
                                            {
                                                "role": "assistant",
                                                "content":
                                                    "Welcome back! "
                                                    "How can I assist "
                                                    "you today?"
                                            }
                                        ]

                                    st.rerun()

                                else:

                                    st.error(
                                        f"Failed to delete chat: "
                                        f"{delete_res.status_code}"
                                    )

            except Exception as e:

                st.caption(
                    f"Unable to fetch chat history: {e}"
                )

        # ==================================================
        # PROFILE + LOGOUT
        # IMPORTANT:
        # This is INSIDE st.sidebar
        # and ONLY shown to logged-in users.
        # ==================================================

        if st.session_state.user_id:

            # Push profile section toward bottom
            st.markdown(
                """
                <div style="
                    flex-grow: 1;
                    min-height: 20px;
                "></div>
                """,
                unsafe_allow_html=True
            )

            user_email = (
                st.session_state.get("user_email")
                or cookies.get("user_email")
                or "User Account"
            )

            initials = "US"

            if user_email and "@" in user_email:
                initials = user_email[:2].upper()

            # -------------------------------
            # PROFILE
            # -------------------------------

            st.markdown(
        f"""<div class="profile-wrapper">
<div class="profile-container">
<div class="profile-avatar">{initials}</div>
<div class="profile-info">
<span class="profile-name" title="{user_email}">{user_email}</span>
</div>
</div>
</div>""",
        unsafe_allow_html=True
    )

            # -------------------------------
            # LOGOUT
            # -------------------------------

            if st.button(
                "Logout",
                key="sidebar_logout_btn",
                use_container_width=True
            ):

                st.session_state.user_id = None
                st.session_state.id_token = None
                st.session_state.user_email = None
                st.session_state.show_login = True

                cookies["user_id"] = ""
                cookies["id_token"] = ""
                cookies["refresh_token"] = ""
                cookies["user_email"] = ""
                cookies["show_login"] = "true"

                cookies.save()

                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "content":
                            "Welcome back! How can I assist you today?"
                    }
                ]

                st.rerun()

    # ================================================
    # APP HEADER
    # ================================================

    st.markdown("""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #6F4E37, #4A2E1B); color: white; border-radius: 12px; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 2.2rem; color: white;">☕ AI Coffee Barista</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">Tailored recommendations based on taste, dietary needs, and budget.</p>
    </div>
    """, unsafe_allow_html=True)


    # Chat History Presentation
   # st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]

        if role == "user":
            formatted_content = (
            content
            .replace("\n\n", "<br><br>")
            .replace("\n", "<br>")
        )
            st.markdown(
                f"""
                <div class="chat-row user-row">
                    <div class="chat-bubble user-bubble">
                        {formatted_content}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        elif role == "assistant":
            formatted_content = (
                content
                .replace("\n\n", "<br><br>")
                .replace("\n", "<br>")
            )

            st.markdown(
                f"""
                <div class="chat-row assistant-row">
                    <div class="assistant-bubble">
                        {formatted_content}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    #st.markdown("</div>", unsafe_allow_html=True)

    # PROCESS PENDING PROMPT
    if "pending_prompt" in st.session_state:
        prompt = st.session_state.pending_prompt
        del st.session_state.pending_prompt
        with st.spinner("Brewing your recommendation..."):
            result = ask_barista(
                prompt=prompt,
                session_id=st.session_state.session_id,
                user_id=st.session_state.user_id,
                chat_id=st.session_state.chat_id
            )

        print("FULL RESULT FROM ask_barista:")
        print(repr(result))
        
        print("MESSAGE FROM RESULT:")
        print(repr(result.get("message")))
        
        if result.get("limit_reached"):
            st.session_state.show_login = True
            st.rerun()

        response_text = result.get(
            "message",
            "Sorry, something went wrong."
        )

        print("FINAL response_text:")
        print(repr(response_text))

        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text
        })
        st.rerun()

    # CHAT INPUT
    if prompt := st.chat_input("Ask for recommendations (e.g., 'Classic hot coffee with sugar free')"):
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        st.session_state.pending_prompt = prompt
        st.rerun()