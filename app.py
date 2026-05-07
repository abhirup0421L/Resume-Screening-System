# app.py

import streamlit as st
import json
import time
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
    verify_otp,
    update_name,
    get_user
)


# --------------------------
# Page Setup
# --------------------------
st.set_page_config(
    page_title="AI Resume Screening",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------
# Session State
# --------------------------
if "page" not in st.session_state:
    st.session_state.page = "Resume Analyzer"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "temp_email" not in st.session_state:
    st.session_state.temp_email = ""

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False

if "otp_start_time" not in st.session_state:
    st.session_state.otp_start_time = None


# --------------------------
# Custom CSS
# --------------------------
st.markdown("""
<style>

.stApp {
    background: #000000;
}

section[data-testid="stSidebar"] {
    background: #0A0A0A;
    border-right: 1px solid rgba(0,255,76,0.25);
}

.sidebar-title {
    font-size: 30px;
    font-weight: 900;
    color: #00ff4c;
    margin-bottom: 5px;
}

.sidebar-subtitle {
    color: #BFBFBF;
    font-size: 14px;
    margin-bottom: 25px;
}

.main-title {
    font-size: 45px;
    font-weight: 900;
    color: #FFFFFF;
}

.main-subtitle {
    font-size: 17px;
    color: #BFBFBF;
    margin-bottom: 25px;
}

.user-badge {
    position: fixed;
    top: 82px;
    left: 18px;
    z-index: 999;
    color: #00ff4c;
    font-size: 18px;
    font-weight: 800;
}

/* Login Card */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid rgba(0,255,76,0.65) !important;
    border-radius: 10px !important;
    padding: 35px !important;
    background: rgba(17,17,17,0.95) !important;
    box-shadow: 0 25px 70px rgba(0,255,76,0.12) !important;
}

.auth-small-title {
    text-align: center;
    color: white;
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 18px;
}

.auth-big-title {
    text-align: center;
    color: #00ff4c;
    font-size: 42px;
    font-weight: 900;
    letter-spacing: 12px;
    margin-bottom: 35px;
}

.auth-label {
    color: white;
    font-size: 15px;
    font-weight: 800;
    margin-bottom: 8px;
    margin-top: 12px;
}

.auth-or {
    display: flex;
    align-items: center;
    gap: 16px;
    color: #CCCCCC;
    margin: 28px 0;
    font-weight: 700;
}

.auth-or::before,
.auth-or::after {
    content: "";
    flex: 1;
    height: 1px;
    background: rgba(0,255,76,0.35);
}

.auth-bottom {
    color: white;
    font-weight: 700;
    margin-bottom: 10px;
    margin-top: 10px;
}

div[data-testid="stTextInput"] {
    margin-top: 0px !important;
    margin-bottom: 18px !important;
}

div[data-testid="stTextInput"] input {
    height: 48px !important;
    border-radius: 12px !important;
    padding-top: 10px !important;
    background-color: #111111 !important;
    color: white !important;
    border: 1px solid rgba(0,255,76,0.35) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #00ff4c, #00cc3a);
    color: black;
    border: none;
    border-radius: 14px;
    height: 52px;
    font-weight: 900;
    transition: 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0px 6px 20px rgba(0,255,76,0.35);
    color: black;
}

section[data-testid="stSidebar"] .stButton > button {
    background: #111111;
    border: 1px solid rgba(0,255,76,0.35);
    color: white;
    height: 52px;
    border-radius: 16px;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(90deg, #00ff4c, #00cc3a);
    color: black;
}

.stDownloadButton > button {
    background: linear-gradient(90deg, #00ff4c, #00cc3a);
    color: black;
    border: none;
    border-radius: 14px;
    height: 48px;
    font-weight: 900;
}

div[data-testid="stMetric"] {
    background-color: #111111;
    padding: 20px;
    border-radius: 18px;
    border: 1px solid rgba(0,255,76,0.25);
}

textarea, input {
    border-radius: 12px !important;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# LOGIN / SIGN IN SYSTEM
# =====================================================
if not st.session_state.logged_in:

    left, center, right = st.columns([1.4, 1, 1.4])

    with center:

        with st.container(border=True):

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

                if st.button("Verify", use_container_width=True):

                    if not login_email:
                        st.error("Please enter email.")

                    else:
                        user = get_user(login_email)

                        if user and user.get("verified") is True:
                            st.session_state.logged_in = True
                            st.session_state.user_email = login_email
                            st.session_state.otp_sent = False
                            st.session_state.otp_start_time = None
                            st.session_state.temp_email = ""

                            st.success("Login successful.")
                            time.sleep(1)
                            st.rerun()

                        else:
                            st.error("No account found. Please sign in first.")

                st.markdown(
                    '<div class="auth-or">OR</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="auth-bottom">Don’t have an account?</div>',
                    unsafe_allow_html=True
                )

                if st.button("Sign In", use_container_width=True):
                    st.session_state.auth_mode = "signin"
                    st.session_state.otp_sent = False
                    st.session_state.otp_start_time = None
                    st.session_state.temp_email = ""
                    st.rerun()


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

                if st.button(
                    "Send OTP",
                    use_container_width=True,
                    disabled=st.session_state.otp_sent
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


                if st.session_state.otp_sent:

                    st_autorefresh(interval=1000, key="otp_timer_refresh")

                    st.markdown(
                        '<div class="auth-label">Enter OTP</div>',
                        unsafe_allow_html=True
                    )

                    otp = st.text_input(
                        "",
                        placeholder="Enter OTP",
                        key="signin_otp",
                        label_visibility="collapsed"
                    )

                    if otp:
                        otp = otp.strip()

                    elapsed = int(time.time() - st.session_state.otp_start_time)
                    remaining = max(0, 300 - elapsed)

                    mins = remaining // 60
                    secs = remaining % 60

                    st.info(f"OTP expires in: {mins:02d}:{secs:02d}")

                    if remaining == 0:
                        st.session_state.otp_sent = False
                        st.session_state.otp_start_time = None
                        st.session_state.temp_email = ""

                        st.error("OTP expired. Please send OTP again.")
                        st.rerun()

                    if st.button("Verify OTP", use_container_width=True):

                        success, message = verify_otp(
                            st.session_state.temp_email,
                            otp
                        )

                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user_email = st.session_state.temp_email
                            st.session_state.otp_sent = False
                            st.session_state.otp_start_time = None
                            st.session_state.temp_email = ""

                            st.success("Account created successfully.")
                            time.sleep(1)
                            st.rerun()

                        else:
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
                    st.rerun()

    st.stop()


# =====================================================
# SIDEBAR PROFILE ONLY
# =====================================================
with st.sidebar:

    st.markdown('<div class="sidebar-title">⚡ Resume AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-subtitle">AI Resume Analyzer & CV Maker</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    user = get_user(st.session_state.user_email)

    st.subheader("👤 Profile")

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
        st.rerun()


# =====================================================
# HEADER
# =====================================================
user = get_user(st.session_state.user_email)

display_name = "User"
if user and user.get("name"):
    display_name = user.get("name")

st.markdown(
    f'<div class="user-badge">👤 {display_name}</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-title">📄 AI Resume Screening System</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-subtitle">Smart ATS Analyzer + AI CV Maker Powered by Gemini AI</div>',
    unsafe_allow_html=True
)

nav1, nav2 = st.columns(2)

with nav1:
    if st.button("🔍 Resume Analyzer", use_container_width=True):
        st.session_state.page = "Resume Analyzer"
        st.rerun()

with nav2:
    if st.button("✨ AI CV Maker", use_container_width=True):
        st.session_state.page = "AI CV Maker"
        st.rerun()

st.write("---")


# =====================================================
# LOAD ROLES
# =====================================================
try:
    with open("data/roles.json", "r") as file:
        roles_data = json.load(file)
except FileNotFoundError:
    st.error("❌ data/roles.json file not found.")
    st.stop()

job_roles = list(roles_data.keys())

if not job_roles:
    st.error("❌ No job roles found in roles.json.")
    st.stop()


# =====================================================
# PDF GENERATOR
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
# PAGE 1: RESUME ANALYZER
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

    if uploaded_file:

        if st.button("🚀 Analyze Resume", use_container_width=True):

            with st.spinner("Reading uploaded file..."):
                time.sleep(1)
                resume_text = extract_text(uploaded_file)

            if not resume_text or not resume_text.strip():
                st.error("❌ Unable to extract text from file.")
                st.stop()

            with st.spinner("Checking Resume Authenticity with Gemini AI..."):
                ai = validate_resume(resume_text)

            if ai.get("is_resume") is None:
                st.warning("⚠️ Gemini AI unavailable. Running normal ATS scan only.")

                ai = {
                    "is_resume": True,
                    "candidate_name": "Unknown",
                    "experience_level": "Unknown",
                    "confidence": 0,
                    "summary": "AI validation was unavailable. Only normal ATS skill matching was performed.",
                    "reason": "Gemini AI unavailable"
                }

            elif ai.get("is_resume") is False:
                st.error("❌ Invalid Resume / Random PDF Detected")
                st.warning(ai.get("reason", "This file does not look like a valid resume."))
                st.stop()

            with st.spinner("Calculating ATS Score..."):
                skills = extract_skills(resume_text)
                required_skills = roles_data[selected_role]
                score, matched, missing = match_skills(skills, required_skills)

            st.success("✅ Analysis Completed Successfully")
            st.write("---")

            st.subheader("👤 Candidate Details")

            a, b, c = st.columns(3)

            with a:
                st.metric("Name", ai.get("candidate_name", "Unknown"))

            with b:
                st.metric("Experience", ai.get("experience_level", "Unknown"))

            with c:
                st.metric("AI Confidence", f'{ai.get("confidence", 0)}%')

            st.info(ai.get("summary", "No AI summary available."))
            st.write("---")

            st.subheader("📊 ATS Score")

            s1, s2 = st.columns(2)

            with s1:
                st.metric("Match Score", f"{score}%")
                st.progress(score / 100)

            with s2:
                if score >= 85:
                    st.success("Excellent Match ✅")
                elif score >= 65:
                    st.warning("Good Match 👍")
                else:
                    st.error("Needs Improvement ❌")

            st.subheader("📈 Skill Breakdown")

            fig = go.Figure(data=[go.Pie(
                labels=["Matched Skills", "Missing Skills"],
                values=[len(matched), len(missing)],
                hole=0.55
            )])

            fig.update_layout(title="Matched vs Missing Skills")
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
            st.info("Use the AI CV Maker section to generate a professional ATS-friendly resume.")

            if st.button("✨ Go to AI CV Maker", use_container_width=True):
                st.session_state.page = "AI CV Maker"
                st.rerun()

    else:
        st.info("📤 Upload a resume to begin.")

        st.write("---")
        st.subheader("Don’t have a resume?")

        if st.button("✨ Create Resume with AI", use_container_width=True):
            st.session_state.page = "AI CV Maker"
            st.rerun()


# =====================================================
# PAGE 2: AI CV MAKER
# =====================================================
elif st.session_state.page == "AI CV Maker":

    st.header("✨ AI CV Maker")
    st.caption("Enter your details and Gemini will generate a professional ATS-friendly resume.")

    user = get_user(st.session_state.user_email)
    default_name = user.get("name", "") if user else ""

    with st.form("cv_maker_form"):

        name = st.text_input("Full Name", value=default_name)
        email = st.text_input("Email", value=st.session_state.user_email)
        phone = st.text_input("Phone Number")

        target_role = st.selectbox("Target Job Role", job_roles, key="cv_role")

        education = st.text_area(
            "Education",
            placeholder="Example: B.Tech CSE, SurTech, MAKAUT, 2026"
        )

        skills = st.text_area(
            "Skills",
            placeholder="Example: Python, Java, SQL, Machine Learning, Streamlit"
        )

        experience = st.text_area(
            "Experience",
            placeholder="Example: Internship, freelance work, training, or write Fresher"
        )

        projects = st.text_area(
            "Projects",
            placeholder="Example: Resume Screening System using Python and Streamlit"
        )

        submitted = st.form_submit_button("🚀 Generate CV", use_container_width=True)

    if submitted:

        if not name or not email or not skills or not education:
            st.error("Please fill at least Name, Email, Education, and Skills.")
            st.stop()

        with st.spinner("Generating professional resume with Gemini..."):
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

        st.session_state.generated_resume = generated_resume
        st.session_state.generated_name = name

    if "generated_resume" in st.session_state:

        generated_resume = st.session_state.generated_resume
        name = st.session_state.generated_name

        st.success("✅ Resume Generated Successfully")
        st.write("---")

        st.subheader("📄 Generated Resume")

        st.text_area(
            "Your AI Generated Resume",
            generated_resume,
            height=500
        )

        pdf_data = create_pdf(generated_resume)

        btn1, btn2 = st.columns(2)

        with btn1:
            st.download_button(
                label="⬇️ Download Resume as TXT",
                data=generated_resume,
                file_name=f"{name.replace(' ', '_')}_resume.txt",
                mime="text/plain",
                use_container_width=True
            )

        with btn2:
            st.download_button(
                label="📄 Download Resume as PDF",
                data=pdf_data,
                file_name=f"{name.replace(' ', '_')}_resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.write("---")

        if st.button("🔍 Analyze This Resume", use_container_width=True):
            st.session_state.page = "Resume Analyzer"
            st.rerun()
