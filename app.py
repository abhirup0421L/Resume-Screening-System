# app.py

import streamlit as st
import json
import time
import os
from dotenv import load_dotenv
from backend.database import (
    cache_collection,
    coupons_collection,
    settings_collection
)
load_dotenv()
import plotly.graph_objects as go
from fpdf import FPDF
from streamlit_autorefresh import st_autorefresh

from backend.parser import extract_text
from backend.skills import extract_skills
from backend.matcher import match_skills
from backend.ai_validator import validate_resume
from backend.resume_generator import generate_resume

from backend.auth import (
    send_login_otp,
    verify_otp_only,
    verify_otp_and_create_account,
    login_user,
    update_name,
    get_user
)

from backend.credits import get_credits, deduct_credit
from backend.coupons import claim_coupon, create_coupon
from backend.resume_cache import (
    make_resume_hash,
    get_cached_result,
    save_cached_result
)
from backend.gemini_queue import wait_for_gemini_slot

from backend.interview import (
    LEVEL_DETAILS,
    generate_interview_questions,
    check_answers,
    update_user_progress,
    get_user_progress
)

# =====================================================
# MAINTENANCE MODE FUNCTIONS
# =====================================================

def get_maintenance_mode():

    doc = settings_collection.find_one(
        {"key": "maintenance_mode"}
    )

    return bool(
        doc and doc.get("enabled")
    )


def set_maintenance_mode(value):

    settings_collection.update_one(
        {"key": "maintenance_mode"},

        {
            "$set": {
                "enabled": value
            }
        },

        upsert=True
    )

from datetime import datetime, timedelta, timezone


# =====================================================
# MAINTENANCE MODE FUNCTIONS
# =====================================================

def get_maintenance_mode():
    doc = settings_collection.find_one({"key": "maintenance_mode"})

    if not doc or not doc.get("enabled"):
        return False, None

    end_time = doc.get("end_time")

    if end_time and datetime.now(timezone.utc) >= end_time.replace(tzinfo=timezone.utc):
        set_maintenance_mode(False)
        return False, None

    return True, end_time


def set_maintenance_mode(value, minutes=None):

    if value:

        end_time = None

        if minutes:
            end_time = (
                datetime.now(timezone.utc)
                + timedelta(minutes=minutes)
            )

        settings_collection.update_one(
            {"key": "maintenance_mode"},
            {
                "$set": {
                    "enabled": True,
                    "end_time": end_time
                }
            },
            upsert=True
        )

    else:

        settings_collection.update_one(
            {"key": "maintenance_mode"},
            {
                "$set": {
                    "enabled": False,
                    "end_time": None
                }
            },
            upsert=True
        )


def add_maintenance_time(minutes):
    doc = settings_collection.find_one({"key": "maintenance_mode"})
    now = datetime.now(timezone.utc)

    old_end = doc.get("end_time") if doc else None

    if old_end:
        old_end = old_end.replace(tzinfo=timezone.utc)
        base_time = max(old_end, now)
    else:
        base_time = now

    new_end = base_time + timedelta(minutes=minutes)

    settings_collection.update_one(
        {"key": "maintenance_mode"},
        {"$set": {"enabled": True, "end_time": new_end}},
        upsert=True
    )

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="AI Resume Screening",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)



# =====================================================
# ADMIN PAGE
# =====================================================
if st.query_params.get("admin") == "1":

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    st.markdown("""
    <style>
    .stApp {
        background: #000000;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #2a2a2a !important;
        border-radius: 14px !important;
        padding: 35px !important;
        background: rgba(10,10,10,0.95) !important;
    }

    .admin-title {
        text-align: center;
        color: #ff2b2b;
        font-size: 42px;
        font-weight: 900;
        letter-spacing: 8px;
        margin-bottom: 30px;
    }

    .auth-label {
        color: white;
        font-size: 14px;
        font-weight: 800;
        margin-bottom: 8px;
        margin-top: 8px;
    }

    .stButton > button {
        background: #00ff4c;
        color: black;
        border: none;
        border-radius: 12px;
        height: 50px;
        font-weight: 900;
    }

    div[data-testid="stTextInput"] input {
        background-color: #111111 !important;
        color: white !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 12px !important;
        height: 48px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    left, center, right = st.columns([1.4, 1, 1.4])

    with center:
        with st.container(border=True):

            if not st.session_state.admin_logged_in:

                st.markdown(
                    '<div class="admin-title">ADMIN</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="auth-label">Admin ID</div>',
                    unsafe_allow_html=True
                )

                admin_id = st.text_input(
                    "",
                    placeholder="Enter admin ID",
                    key="admin_id_input",
                    label_visibility="collapsed"
                )

                st.markdown(
                    '<div class="auth-label">Password</div>',
                    unsafe_allow_html=True
                )

                admin_password = st.text_input(
                    "",
                    placeholder="Enter admin password",
                    type="password",
                    key="admin_password_input",
                    label_visibility="collapsed"
                )

                if st.button("Login", use_container_width=True):

                    if (
                        admin_id == os.getenv("ADMIN_ID")
                        and admin_password == os.getenv("ADMIN_PASSWORD")
                    ):
                        st.session_state.admin_logged_in = True
                        st.success("Admin login successful.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid admin ID or password.")

                st.markdown(
                    """
                    <div style="text-align:center; margin-top:20px;">
                        <a href="/"
                           style="color:#00ff4c; text-decoration:none; font-weight:700;">
                           Back to User Login
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.stop()

            st.markdown(
                '<div class="admin-title">ADMIN PANEL</div>',
                unsafe_allow_html=True
            )

            cache_count = cache_collection.count_documents({})

            st.metric("Cached Resumes", cache_count)

            st.warning("Deleting cache will remove all saved resume analysis data.")

            if st.button("🗑️ Delete All Cached Resumes", use_container_width=True):
                result = cache_collection.delete_many({})
                st.success(f"{result.deleted_count} cached resumes deleted successfully.")

            # =====================================================
            # COUPON GENERATOR
            # =====================================================

            st.write("---")
            st.subheader("🎟️ Coupon Generator")

            coupon_credits = st.number_input(
                "Credit points for coupon",
                min_value=1,
                step=1
            )

            coupon_duration = st.number_input(
                "Coupon duration in hours",
                min_value=1,
                step=1
            )

            if st.button("Generate Coupon Code", use_container_width=True):

                code = create_coupon(
                    credits=coupon_credits,
                    duration_hours=coupon_duration
                )

                st.success("Coupon created successfully.")
                st.code(code)

            active_coupons = coupons_collection.count_documents({})

            st.metric("Active Coupons", active_coupons)

            # =====================================================
            # MAINTENANCE MODE
            # =====================================================

            st.markdown("---")
            st.subheader("🚧 Maintenance Mode")

            maintenance_minutes = st.number_input(
                "Maintenance time in minutes",
                min_value=1,
                value=10,
                step=1
            )

            if st.button("🚧 Start Maintenance", use_container_width=True):
                set_maintenance_mode(True, maintenance_minutes)
                st.success("Maintenance mode started.")
                st.rerun()

            if st.button("➕ Add More Time", use_container_width=True):
                add_maintenance_time(maintenance_minutes)
                st.success("Maintenance time increased.")
                st.rerun()

            if st.button("✅ Stop Maintenance", use_container_width=True):
                set_maintenance_mode(False)
                st.success("Maintenance mode stopped.")
                st.rerun()

            if st.button("Logout", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.rerun()

            st.markdown(
                """
                <div style="text-align:center; margin-top:20px;">
                    <a href="/"
                       style="color:#00ff4c; text-decoration:none; font-weight:700;">
                       Back to User Login
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.stop()




# ================================
# FULLSCREEN LOCK SCREEN
# ================================

maintenance_on, maintenance_end = get_maintenance_mode()

if maintenance_on and st.query_params.get("admin") != "1":

    remaining_text = "00:00"

    if maintenance_end:
        try:
            if maintenance_end.tzinfo is None:
                maintenance_end = maintenance_end.replace(tzinfo=timezone.utc)

            remaining = maintenance_end - datetime.now(timezone.utc)
            total_seconds = max(0, int(remaining.total_seconds()))

            hours = total_seconds // 3600
            mins = (total_seconds % 3600) // 60
            secs = total_seconds % 60

            remaining_text = f"{hours:02d}:{mins:02d}:{secs:02d}"

        except Exception:
            remaining_text = "Timer Error"

    html_code = f"""
    <style>
    .construction-overlay {{
        position: fixed;
        inset: 0;
        background: black;
        z-index: 999999;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}

    .construction-text {{
        color: red;
        font-size: 90px;
        font-weight: 900;
        letter-spacing: 6px;
        text-align: center;
    }}

    .construction-timer {{
        color: #00ff4c;
        font-size: 46px;
        font-weight: 900;
        margin-top: 35px;
        text-align: center;
    }}

    .admin-link {{
        position: fixed;
        bottom: 20px;
        right: 30px;
        color: #00ff4c !important;
        font-size: 14px;
        font-weight: 700;
        z-index: 1000000;
        text-decoration: none;
    }}
    </style>

    <div class="construction-overlay">

        <div class="construction-text">
            🚧 UNDER CONSTRUCTION 🚧
        </div>

        <div class="construction-timer">
            ⏱️ {remaining_text}
        </div>

    </div>

    <a class="admin-link" href="?admin=1">admin</a>
    """

    st.html(html_code)

    time.sleep(1)
    st.rerun()

    st.stop()

# =====================================================
# SESSION STATE
# =====================================================
defaults = {
    "page": "Resume Analyzer",
    "logged_in": False,
    "show_welcome": True,
    "user_email": "",
    "creating_account": False,
    "temp_email": "",
    "auth_mode": "login",
    "otp_sent": False,
    "otp_start_time": None,
    "otp_verified_for_signup": False,
    "verified_otp_value": "",
    "analysis_result": None,
    "admin_logged_in": False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
# CUSTOM CSS
# =====================================================
st.markdown("""
<style>

.stApp {
    background: #000000;
}

section[data-testid="stSidebar"] {
    background: #0A0A0A;
    border-right: 1px solid rgba(0,255,76,0.20);
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #2a2a2a !important;
    border-radius: 14px !important;
    padding: 35px !important;
    background: rgba(10,10,10,0.95) !important;
}

.auth-small-title {
    text-align: center;
    color: white;
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 15px;
}

.auth-big-title {
    text-align: center;
    color: #00ff4c;
    font-size: 44px;
    font-weight: 900;
    letter-spacing: 12px;
    margin-bottom: 35px;
}

.auth-label {
    color: white;
    font-size: 14px;
    font-weight: 800;
    margin-bottom: 8px;
    margin-top: 8px;
}

.auth-bottom {
    color: white;
    font-size: 15px;
    font-weight: 700;
    margin-top: 10px;
    margin-bottom: 10px;
}

.auth-or {
    display: flex;
    align-items: center;
    gap: 16px;
    color: #AAAAAA;
    margin: 28px 0;
    font-weight: 700;
}

.auth-or::before,
.auth-or::after {
    content: "";
    flex: 1;
    height: 1px;
    background: #2a2a2a;
}

div[data-testid="stTextInput"] {
    margin-bottom: 16px !important;
}

div[data-testid="stTextInput"] input {
    background-color: #111111 !important;
    color: white !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 12px !important;
    height: 48px !important;
    box-shadow: none !important;
    outline: none !important;
}

div[data-testid="stTextInput"] input:focus {
    border: 1px solid #444444 !important;
    box-shadow: 0 0 0 1px #444444 !important;
    outline: none !important;
}

textarea {
    background-color: #111111 !important;
    color: white !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}

textarea:focus {
    border: 1px solid #444444 !important;
    box-shadow: 0 0 0 1px #444444 !important;
    outline: none !important;
}

div[data-baseweb="select"] > div {
    background-color: #111111 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 12px !important;
    color: white !important;
    box-shadow: none !important;
}

div[data-baseweb="select"] > div:focus-within {
    border: 1px solid #444444 !important;
    box-shadow: 0 0 0 1px #444444 !important;
}

.stButton > button {
    background: #00ff4c;
    color: black;
    border: none;
    border-radius: 12px;
    height: 50px;
    font-weight: 900;
}

.stButton > button:hover {
    background: #00cc3a;
    color: black;
}

.stDownloadButton > button {
    background: #00ff4c;
    color: black;
    border: none;
    border-radius: 12px;
    height: 48px;
    font-weight: 900;
}

.stDownloadButton > button:hover {
    background: #00cc3a;
    color: black;
}

.main-title {
    color: white;
    font-size: 42px;
    font-weight: 900;
}

.main-subtitle {
    color: #BBBBBB;
    margin-bottom: 30px;
}

.user-badge {
    position: fixed;
    top: 85px;
    left: 18px;
    z-index: 999;
    color: #00ff4c;
    font-size: 18px;
    font-weight: 800;
}

div[data-testid="stMetric"] {
    background-color: #111111;
    padding: 20px;
    border-radius: 18px;
    border: 1px solid #2a2a2a;
}

.credit-card {
    background: #111111;
    border: 1px solid #2a2a2a;
    border-radius: 14px;
    padding: 14px;
    color: #00ff4c;
    font-weight: 900;
    margin-bottom: 12px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# WELCOME SCREEN
# =====================================================

if st.session_state.show_welcome:

    st.markdown("""
    <style>
    .welcome-bg {
        position: fixed;
        inset: 0;
        overflow: hidden;
        z-index: 0;
        pointer-events: none;
    }

    .dot {
        position: absolute;
        width: 180px;
        height: 180px;
        background: rgba(0,255,76,0.25);
        filter: blur(70px);
        border-radius: 50%;
        animation: float 6s ease-in-out infinite alternate;
    }

    .dot1 { top: 20%; left: 15%; animation-delay: 0s; }
    .dot2 { top: 60%; left: 70%; animation-delay: 2s; }
    .dot3 { top: 40%; left: 45%; animation-delay: 4s; }

    @keyframes float {
        from {
            transform: translate(0px, 0px);
            opacity: 0.7;
        }

        to {
            transform: translate(70px, -70px);
            opacity: 1;
        }
    }

    .welcome-title {
        text-align:center;
        color:#00ff4c;
        font-size:72px;
        font-weight:900;
        margin-top:120px;
        position: relative;
        z-index: 1;
    }

    .welcome-sub {
        text-align:center;
        color:#BBBBBB;
        font-size:30px;
        margin-bottom:420px;
        position: relative;
        z-index: 1;
    }
    </style>

    <div class="welcome-bg">
        <div class="dot dot1"></div>
        <div class="dot dot2"></div>
        <div class="dot dot3"></div>
    </div>

    <div class="welcome-title">⚡ Resume AI</div>
    <div class="welcome-sub">Smart ATS Resume Analyzer + AI CV Maker</div>
    """, unsafe_allow_html=True)

    left, center, right = st.columns([2,1,2])

    with center:
        if st.button("🚀 Get Started", use_container_width=True):
            st.session_state.show_welcome = False
            st.rerun()

    st.stop()

# =====================================================
# LOGIN / SIGNUP UI
# =====================================================
if not st.session_state.logged_in:

    left, center, right = st.columns([1.4, 1, 1.4])

    with center:
        with st.container(border=True):

            # ==========================
            # LOGIN PAGE
            # ==========================
            if st.session_state.auth_mode == "login":

                st.markdown(
                    '<div class="auth-small-title">Resume Screening System</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    '<div class="auth-big-title">LOGIN</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="auth-label">Enter mail</div>',
                    unsafe_allow_html=True
                )

                login_email = st.text_input(
                    "",
                    placeholder="Enter your email",
                    key="login_email",
                    label_visibility="collapsed"
                )

                if login_email:
                    login_email = login_email.strip().lower()

                st.markdown(
                    '<div class="auth-label">Password</div>',
                    unsafe_allow_html=True
                )

                login_password = st.text_input(
                    "",
                    placeholder="Enter password",
                    type="password",
                    key="login_password",
                    label_visibility="collapsed"
                )

                if st.button("Login", use_container_width=True):

                    if not login_email or not login_password:
                        st.error("Please fill all fields.")

                    else:
                        success, message = login_user(
                            login_email,
                            login_password
                        )

                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user_email = login_email

                            st.success(message)
                            time.sleep(1)
                            st.rerun()

                        else:
                            st.error(message)

                st.markdown(
                    '<div class="auth-or">OR</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="auth-bottom">Don’t have an account?</div>',
                    unsafe_allow_html=True
                )

                if st.button("Create Account", use_container_width=True):

                    st.session_state.auth_mode = "signin"
                    st.session_state.otp_sent = False
                    st.session_state.otp_start_time = None
                    st.session_state.temp_email = ""
                    st.session_state.otp_verified_for_signup = False
                    st.session_state.verified_otp_value = ""

                    st.rerun()
                
                st.markdown('<div style="text-align:center; margin-top:25px; font-size:14px;"><a href="https://mail.google.com/mail/?view=cm&fs=1&to=noname229229229@gmail.com" target="_blank" style="color:#00ff4c; text-decoration:none; font-weight:700;">Contact</a><span style="color:#444; margin:0 10px;"> | </span><a href="?admin=1" style="color:#00ff4c; text-decoration:none; font-weight:700;">Admin</a></div>', unsafe_allow_html=True)


            # ==========================
            # SIGN IN / CREATE ACCOUNT
            # ==========================
            elif st.session_state.auth_mode == "signin":

                st.markdown(
                    '<div class="auth-small-title">Resume Screening System</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    '<div class="auth-big-title">SIGN IN</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="auth-label">Enter mail</div>',
                    unsafe_allow_html=True
                )

                signin_email = st.text_input(
                    "",
                    placeholder="Enter your email",
                    key="signin_email",
                    label_visibility="collapsed",
                    disabled=st.session_state.otp_sent
                )

                if signin_email:
                    signin_email = signin_email.strip().lower()

                existing_user = None

                if signin_email:
                    existing_user = get_user(signin_email)

                account_exists = bool(
                    existing_user
                    and existing_user.get("verified")
                    and existing_user.get("password_hash")
                )

                if account_exists and not st.session_state.otp_sent:
                    st.warning("⚠️ Account already exists")

                if st.button(
                    "Send OTP",
                    use_container_width=True,
                    disabled=bool(st.session_state.otp_sent or (account_exists and not st.session_state.otp_sent))
                ):

                    if signin_email:

                        with st.spinner("Sending OTP..."):
                            sent = send_login_otp(signin_email)

                        if sent:
                            st.session_state.temp_email = signin_email
                            st.session_state.otp_sent = True
                            st.session_state.otp_start_time = time.time()

                            st.success("OTP sent successfully.")
                            st.rerun()

                        else:
                            st.error("Failed to send OTP.")

                    else:
                        st.error("Please enter email.")

                # ==========================
                # OTP SECTION
                # ==========================
                if st.session_state.otp_sent:

                    # refresh ONLY until OTP is verified
                    if not st.session_state.otp_verified_for_signup:
                        st_autorefresh(interval=1000, key="otp_refresh")

                    st.markdown(
                        '<div class="auth-label">Enter OTP</div>',
                        unsafe_allow_html=True
                    )

                    otp = st.text_input(
                        "",
                        placeholder="Enter OTP",
                        key="signup_otp",
                        label_visibility="collapsed",
                        disabled=st.session_state.otp_verified_for_signup
                    )

                    if otp:
                        otp = otp.strip()

                    if st.session_state.otp_verified_for_signup:
                        st.success("OTP verified. Now set your password.")

                    else:
                        elapsed = int(time.time() - st.session_state.otp_start_time)
                        remaining = max(0, 300 - elapsed)

                        mins = remaining // 60
                        secs = remaining % 60

                        st.markdown(
                            f"""
                            <div style="
                                background:#102033;
                                color:#00ff4c;
                                padding:12px;
                                border-radius:10px;
                                margin-top:-8px;
                                margin-bottom:18px;
                                font-weight:700;
                            ">
                                OTP expires in: {mins:02d}:{secs:02d}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        if remaining == 0:
                            st.session_state.otp_sent = False
                            st.session_state.otp_start_time = None
                            st.session_state.temp_email = ""
                            st.session_state.otp_verified_for_signup = False
                            st.session_state.verified_otp_value = ""

                            st.error("OTP expired. Please send OTP again.")
                            st.rerun()

                        if st.button("Verify OTP", use_container_width=True):

                            if not otp:
                                st.error("Please enter OTP.")

                            else:
                                success, message = verify_otp_only(
                                    st.session_state.temp_email,
                                    otp
                                )

                                if success:
                                    st.session_state.otp_verified_for_signup = True
                                    st.session_state.verified_otp_value = otp
                                    st.session_state.otp_start_time = None

                                    st.success("OTP verified. Now set your password.")
                                    st.rerun()

                                else:
                                    st.error(message)

                    # ==========================
                    # PASSWORD SECTION
                    # ==========================
                    if st.session_state.otp_verified_for_signup:

                        st.markdown(
                            '<div class="auth-label">Set Password</div>',
                            unsafe_allow_html=True
                        )

                        new_password = st.text_input(
                            "",
                            placeholder="Set password",
                            type="password",
                            key="new_password",
                            label_visibility="collapsed"
                        )

                        confirm_password = st.text_input(
                            "",
                            placeholder="Confirm password",
                            type="password",
                            key="confirm_password",
                            label_visibility="collapsed"
                        )

                        if st.button(
                            "Create Account",
                            use_container_width=True,
                            disabled=st.session_state.get("creating_account", False)
                        ):

                            st.session_state.creating_account = True

                            if not new_password or not confirm_password:

                                st.session_state.creating_account = False
                                st.error("Please fill password fields.")

                            elif new_password != confirm_password:

                                st.session_state.creating_account = False
                                st.error("Passwords do not match.")

                            else:

                                success, message = verify_otp_and_create_account(
                                    st.session_state.temp_email,
                                    st.session_state.verified_otp_value,
                                    new_password
                                )

                                if success:

                                    st.session_state.logged_in = True
                                    st.session_state.user_email = st.session_state.temp_email

                                    st.session_state.otp_sent = False
                                    st.session_state.otp_start_time = None
                                    st.session_state.temp_email = ""
                                    st.session_state.otp_verified_for_signup = False
                                    st.session_state.verified_otp_value = ""

                                    st.success(message)

                                    st.session_state.creating_account = False

                                    time.sleep(1)
                                    st.rerun()

                                else:

                                    st.session_state.creating_account = False
                                    st.error(message)

                st.markdown(
                    '<div class="auth-or">OR</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="auth-bottom">Already have an account?</div>',
                    unsafe_allow_html=True
                )

                if st.button("Back to Login", use_container_width=True):

                    st.session_state.auth_mode = "login"
                    st.session_state.otp_sent = False
                    st.session_state.otp_start_time = None
                    st.session_state.temp_email = ""
                    st.session_state.otp_verified_for_signup = False
                    st.session_state.verified_otp_value = ""

                    st.rerun()

    st.stop()


# =====================================================
# MAIN USER
# =====================================================
user = get_user(st.session_state.user_email)

display_name = "User"

if user and user.get("name"):
    display_name = user.get("name")

credits = get_credits(st.session_state.user_email)

st.markdown(
    f'<div class="user-badge">👤 {display_name}</div>',
    unsafe_allow_html=True
)


# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.title("⚡ Resume AI")
    st.caption("AI Resume Analyzer & CV Maker")

    st.write("---")

    # COUPON SYSTEM
    coupon_code = st.text_input(
        "Coupon Code",
        placeholder="Enter coupon code"
    )

    if st.button("🎁 Claim Coupon", use_container_width=True):

        if not coupon_code:
            st.error("Please enter coupon code.")

        else:

            success, message = claim_coupon(
                st.session_state.user_email,
                coupon_code
            )

            if success:
                st.success(message)
                time.sleep(1)
                st.rerun()

            else:
                st.error(message)

    st.write("---")

    current_name = ""

    if user:
        current_name = user.get("name", "")

    profile_name = st.text_input("Name", value=current_name)

    if st.button("💾 Save Name", use_container_width=True):
        update_name(st.session_state.user_email, profile_name)
        st.success("Name updated.")

    st.write("📧", st.session_state.user_email)

    if st.button("🚪 Logout", use_container_width=True):

        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.temp_email = ""
        st.session_state.auth_mode = "login"
        st.session_state.otp_sent = False
        st.session_state.otp_start_time = None
        st.session_state.otp_verified_for_signup = False
        st.session_state.verified_otp_value = ""
        st.session_state.analysis_result = None

        st.rerun()

    st.markdown(
        """
        <div style="
            position: fixed;
            bottom: 10px;
            left: 25px;
            color: #666666;
            font-size: 12px;
            font-weight: 600;
        ">
            v1.3.2 bug fixed
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================================
# HEADER
# =====================================================
header_left, header_right = st.columns([6, 1])

with header_left:
    st.markdown(
        '<div class="main-title">📄 AI Resume Screening System</div>',
        unsafe_allow_html=True
    )

with header_right:
    st.markdown(
        f"""
        <div style="
            background:#111111;
            border:1px solid #2a2a2a;
            padding:12px 20px;
            border-radius:14px;
            color:#00ff4c;
            font-weight:900;
            font-size:18px;
            text-align:center;
            margin-top:10px;
        ">
            💳 {credits} Credits
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    '<div class="main-subtitle">Smart ATS Analyzer + AI CV Maker Powered by Gemini AI</div>',
    unsafe_allow_html=True
)
st.warning("⚠️ Saved resume analysis data is automatically cleared after 10 minutes.")

nav1, nav2, nav3 = st.columns(3)

with nav1:
    if st.button("🔍 Resume Analyzer", use_container_width=True):
        st.session_state.page = "Resume Analyzer"
        st.rerun()

with nav2:
    if st.button("✨ AI CV Maker", use_container_width=True):
        st.session_state.page = "AI CV Maker"
        st.rerun()

with nav3:
    if st.button(
        "🎯 Interview Prep",
        use_container_width=True
    ):
        st.session_state.page = "Interview Prep"
        st.rerun()

st.write("---")


# =====================================================
# LOAD JOB ROLES
# =====================================================
try:
    with open("data/roles.json", "r") as file:
        roles_data = json.load(file)
except FileNotFoundError:
    st.error("❌ data/roles.json file not found.")
    st.stop()

job_roles = list(roles_data.keys())

if not job_roles:
    st.error("❌ No roles found in data/roles.json.")
    st.stop()


# =====================================================
# PDF FUNCTION
# =====================================================
def create_pdf(resume_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=11)

    for line in resume_text.split("\n"):
        clean_line = line.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 8, clean_line)

    return pdf.output(dest="S").encode("latin-1")


# =====================================================
# RESULT DISPLAY FUNCTION
# =====================================================
def show_analysis_result(ai, score, matched, missing):

    st.write("---")

    st.subheader("👤 Candidate Details")

    a, b, c = st.columns(3)

    with a:
        st.metric("Name", ai.get("candidate_name", "Unknown"))

    with b:
        st.metric("Experience", ai.get("experience_level", "Unknown"))

    with c:
        st.metric("AI Confidence", f'{ai.get("confidence", 0)}%')

    st.info(ai.get("summary", ""))

    st.write("---")

    st.subheader("📊 ATS Score")

    s1, s2 = st.columns(2)

    with s1:
        st.metric("Match Score", f"{score}%")
        st.progress(score / 100)

    with s2:
        if score >= 85:
            st.success("Excellent Match")
        elif score >= 65:
            st.warning("Good Match")
        else:
            st.error("Needs Improvement")

    st.subheader("📈 Skill Breakdown")

    fig = go.Figure(data=[go.Pie(
        labels=["Matched", "Missing"],
        values=[len(matched), len(missing)],
        hole=0.55
    )])

    st.plotly_chart(fig, use_container_width=True)

    x, y = st.columns(2)

    with x:
        st.subheader("✅ Matched Skills")

        if matched:
            for skill in matched:
                st.success(skill.title())
        else:
            st.info("No matched skills found.")

    with y:
        st.subheader("❌ Missing Skills")

        if missing:
            for skill in missing:
                st.error(skill.title())
        else:
            st.success("No missing skills.")

    st.write("---")

    st.subheader("📝 Need a Better Resume?")

    if st.button("✨ Go to AI CV Maker", use_container_width=True):
        st.session_state.page = "AI CV Maker"
        st.rerun()


# =====================================================
# RESUME ANALYZER PAGE
# =====================================================
if st.session_state.page == "Resume Analyzer":

    st.header("🔍 Resume Analysis")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader(
            "📤 Upload Resume",
            type=["pdf", "docx", "txt"]
        )

    with col2:
        selected_role = st.selectbox(
            "🎯 Select Job Role",
            job_roles
        )

    analyze_clicked = st.button("🚀 Analyze Resume", use_container_width=True)

    if uploaded_file and analyze_clicked:

        st.session_state.analysis_result = None

        with st.spinner("Reading Resume..."):
            resume_text = extract_text(uploaded_file)

        if not resume_text or not resume_text.strip():
            st.error("❌ Unable to read resume text.")
            st.stop()

        resume_hash = make_resume_hash(resume_text, selected_role)
        cached_result = get_cached_result(resume_hash)

        if cached_result:

            ai = cached_result.get("ai", {})
            score = cached_result.get("score", 0)
            matched = cached_result.get("matched", [])
            missing = cached_result.get("missing", [])

            st.session_state.analysis_result = {
                "ai": ai,
                "score": score,
                "matched": matched,
                "missing": missing
            }

            st.rerun()

        else:

            current_credits = get_credits(st.session_state.user_email)

            if current_credits < 10:
                 st.error("❌ You need at least 10 credits to analyze a resume.")
                 st.stop()
            
            ok, msg = deduct_credit(st.session_state.user_email, 10)

            if not ok:
                st.error(msg)
                st.stop()

            with st.spinner("Analyzing resume..."):
                wait_for_gemini_slot()
                ai = validate_resume(resume_text)

            if ai.get("is_resume") is False:
                st.error("Invalid Resume Detected")
                st.warning(ai.get("reason", "This file does not look like a resume."))
                st.stop()

            if ai.get("is_resume") is None:
                ai = {
                    "is_resume": True,
                    "candidate_name": "Unknown",
                    "experience_level": "Unknown",
                    "confidence": 0,
                    "summary": "AI validation unavailable."
                }

            skills = extract_skills(resume_text)
            required_skills = roles_data[selected_role]

            score, matched, missing = match_skills(
                skills,
                required_skills
            )

            save_cached_result(
                resume_hash=resume_hash,
                selected_role=selected_role,
                ai=ai,
                score=score,
                matched=matched,
                missing=missing
            )

            st.session_state.analysis_result = {
                "ai": ai,
                "score": score,
                "matched": matched,
                "missing": missing
            }

            st.rerun()

    elif not uploaded_file:
        st.info("📤 Upload a resume to begin.")

        st.write("---")

        st.subheader("Don’t have a resume?")

        if st.button("✨ Create Resume with AI", use_container_width=True):
            st.session_state.page = "AI CV Maker"
            st.rerun()

    if st.session_state.analysis_result:
        result = st.session_state.analysis_result

        show_analysis_result(
            result["ai"],
            result["score"],
            result["matched"],
            result["missing"]
        )


# =====================================================
# CV MAKER PAGE
# =====================================================
elif st.session_state.page == "AI CV Maker":

    st.header("✨ AI CV Maker")
    st.caption("Generate professional ATS-friendly resumes using AI.")

    user = get_user(st.session_state.user_email)
    default_name = user.get("name", "") if user else ""

    with st.form("cv_form"):

        name = st.text_input("Full Name", value=default_name)

        email = st.text_input(
            "Email",
            value=st.session_state.user_email
        )

        phone = st.text_input("Phone")

        target_role = st.selectbox("Target Role", job_roles)

        education = st.text_area("Education")

        skills = st.text_area("Skills")

        experience = st.text_area("Experience")

        projects = st.text_area("Projects")

        submitted = st.form_submit_button(
            "🚀 Generate Resume",
            use_container_width=True
        )

    if submitted:

        if not name or not email or not skills or not education:
            st.error("Please fill at least Name, Email, Education and Skills.")
            st.stop()

        current_credits = get_credits(st.session_state.user_email)

        if current_credits < 50:
            st.error("❌ You need at least 50 credits to generate a resume.")
            st.stop()

        try:
            with st.spinner("Generating Resume using AI..."):
                wait_for_gemini_slot()

                generated_resume = generate_resume(
                    name=name,
                    email=email,
                    phone=phone,
                    education=education,
                    skills=skills,
                    experience=experience,
                    projects=projects,
                    target_role=target_role
                )

            if not generated_resume or "Gemini AI is currently unavailable" in generated_resume:
                st.error("Generation failed , Try gain later")
                st.stop()

            ok, msg = deduct_credit(st.session_state.user_email, 50)

            if not ok:
                st.error(msg)
                st.stop()

            st.session_state.generated_resume = generated_resume
            st.session_state.generated_name = name

        except Exception:
            st.error("Generation failed , Try gain later")
            st.stop()

    if "generated_resume" in st.session_state:

        generated_resume = st.session_state.generated_resume
        resume_name = st.session_state.generated_name

        st.success("Resume Generated Successfully")

        st.text_area(
            "Generated Resume",
            generated_resume,
            height=500
        )

        pdf_data = create_pdf(generated_resume)

        d1, d2 = st.columns(2)

        with d1:
            st.download_button(
                "⬇️ Download TXT",
                data=generated_resume,
                file_name=f"{resume_name.replace(' ', '_')}_resume.txt",
                mime="text/plain",
                use_container_width=True
            )

        with d2:
            st.download_button(
                "📄 Download PDF",
                data=pdf_data,
                file_name=f"{resume_name.replace(' ', '_')}_resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.write("---")

        if st.button("🔍 Analyze This Resume", use_container_width=True):
            st.session_state.page = "Resume Analyzer"
            st.rerun()

# =====================================================
# INTERVIEW PREP PAGE
# =====================================================

if st.session_state.page == "Interview Prep":

    st.markdown("## 🎯 Interview Preparation & Skill Test")

    interview_role = st.selectbox(
        "Choose Job Role",
        job_roles,
        key="interview_role"
    )

    progress = get_user_progress(
        st.session_state.user_email,
        interview_role
    )

    unlocked_level = progress.get("unlocked_level", 1)
    stars = progress.get("stars", 0)
    best_score = progress.get("best_score", 0)

    st.info(f"⭐ Stars: {stars} | 🏆 Best Score: {best_score}%")

    st.markdown("""
    <style>
    .level-card {
        border: 1px solid #333;
        border-radius: 18px;
        padding: 18px;
        text-align: center;
        background: #111111;
        min-height: 300px;
        margin-bottom: 12px;
    }

    .level-title {
        color: #00ff4c;
        font-size: 26px;
        font-weight: 900;
        margin-bottom: 18px;
    }

    .level-info {
        background: #1A1F2E;
        color: white;
        padding: 10px;
        border-radius: 10px;
        margin: 10px 0;
        font-size: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    # =====================================================
    # LEVELS SECTION
    # =====================================================

    if "interview_questions" not in st.session_state:

        st.markdown("## Levels")

        cols = st.columns(5)

        for level in range(1, 6):

            with cols[level - 1]:

                details = LEVEL_DETAILS[level]

                with st.container(border=True):

                    st.markdown(f"### Level {level}")

                    st.info(details["difficulty"])

                    st.info(f'{details["questions"]} Questions')

                    st.info(f'⏱ {details["time"] // 60} mins')

                    st.info("🪙 50 Credits")

                if level <= unlocked_level:

                    if st.button(
                        f"Start Level {level}",
                        key=f"start_interview_level_{level}",
                        use_container_width=True
                    ):

                        success, message, questions = generate_interview_questions(
                            st.session_state.user_email,
                            interview_role,
                            level
                        )

                        if success:
                            st.session_state.interview_questions = questions
                            st.session_state.interview_level = level
                            st.session_state.interview_role_active = interview_role
                            st.session_state.interview_start_time = time.time()
                            st.session_state.interview_time_limit = LEVEL_DETAILS[level]["time"]
                            st.rerun()
                        else:
                            st.error(message)

                else:

                    st.button(
                        "🔒 Locked",
                        key=f"locked_interview_level_{level}",
                        disabled=True,
                        use_container_width=True
                    )
    
    # =====================================================
    # RESULT POPUP
    # =====================================================

    @st.dialog("🎉 Level Completed")
    def result_popup():

        st.markdown("""
        <style>

        /* POPUP BOX */
        div[data-testid="stDialog"] section[role="dialog"]{
            background: #000000 !important;
            border: 2px solid #00ff4c !important;
            border-radius: 22px !important;

            box-shadow:
                0 0 10px #00ff4c,
                0 0 20px #00ff4c,
                0 0 40px rgba(0,255,76,0.7),
                0 0 80px rgba(0,255,76,0.4) !important;
        }

        </style>
        """, unsafe_allow_html=True)

        st.success("🎉 Congrats!")

        st.markdown(
            f"## You completed Level {st.session_state.interview_level}"
        )

        st.info(
            f"✅ Correct Answers: {st.session_state.correct_answers}"
        )

        st.error(
            f"❌ Wrong Answers: {st.session_state.wrong_answers}"
        )

        st.success(
            f"🏆 Final Score: {st.session_state.final_score}%"
        )

        if st.button(
            "Continue",
            use_container_width=True,
            key="continue_result_popup"
        ):
            st.session_state.show_result_popup = False

            if "interview_questions" in st.session_state:
                del st.session_state["interview_questions"]

            st.rerun()


    if st.session_state.get("show_result_popup"):
        result_popup()
        st.stop()

    # =====================================================
    # ACTIVE EXAM
    # =====================================================

    if "interview_questions" in st.session_state:
        # TIMER
        if not st.session_state.get("submitting_interview", False):
            st_autorefresh(interval=5000, key="interview_timer_refresh")

        elapsed = int(time.time() - st.session_state.interview_start_time)
        remaining = st.session_state.interview_time_limit - elapsed

        if remaining <= 0:
            remaining = 0
            st.session_state.auto_submit_interview = True

        mins = remaining // 60
        secs = remaining % 60

        st.warning(f"⏱ Time Left: {mins:02d}:{secs:02d}")


        st.markdown("---")
        st.subheader(f"📝 Level {st.session_state.interview_level} Test")

        user_answers = {}
        questions = st.session_state.interview_questions

        for i, q in enumerate(questions):

            st.markdown(f"### Q{i + 1}. {q['question']}")

            answer = st.radio(
                "Choose Answer",
                q["options"],
                key=f"interview_answer_{i}",
                index=None
            )

            user_answers[str(i)] = answer

        submit_clicked = st.button(
            "🚀 Submit Test",
            use_container_width=True,
            key="submit_interview_test"
        )

        if submit_clicked or st.session_state.get("auto_submit_interview", False):

            st.session_state.submitting_interview = True

            score, results = check_answers(
                questions,
                user_answers
            )

            stars_earned, new_level = update_user_progress(
                st.session_state.user_email,
                st.session_state.interview_role_active,
                st.session_state.interview_level,
                score
            )

            st.session_state.show_result_popup = True
            st.session_state.final_score = score

            st.session_state.correct_answers = sum(
                1 for r in results if r["is_correct"]
            )

            st.session_state.wrong_answers = sum(
                1 for r in results if not r["is_correct"]
            )

            st.session_state.result_details = results

            st.session_state.auto_submit_interview = False
            st.session_state.submitting_interview = False

            st.rerun()
