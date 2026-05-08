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
    verify_otp_only,
    verify_otp_and_create_account,
    login_user,
    update_name,
    get_user
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
# SESSION STATE
# =====================================================
defaults = {
    "page": "Resume Analyzer",
    "logged_in": False,
    "user_email": "",
    "temp_email": "",
    "auth_mode": "login",
    "otp_sent": False,
    "otp_start_time": None,
    "otp_verified_for_signup": False,
    "verified_otp_value": ""
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

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0A0A0A;
    border-right: 1px solid rgba(0,255,76,0.20);
}

/* Login Card */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #2a2a2a !important;
    border-radius: 14px !important;
    padding: 35px !important;
    background: rgba(10,10,10,0.95) !important;
}

/* Titles */
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

/* TEXT INPUTS */
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

/* TEXT AREA */
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

/* SELECT BOX */
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

/* Buttons */
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

/* Download Button */
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

/* Main Title */
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

</style>
""", unsafe_allow_html=True)


# =====================================================
# LOGIN / SIGNUP UI
# =====================================================
if not st.session_state.logged_in:

    left, center, right = st.columns([1.4, 1, 1.4])

    with center:
        with st.container(border=True):

            # LOGIN
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
                    st.session_state.otp_verified_for_signup = False
                    st.session_state.verified_otp_value = ""
                    st.session_state.temp_email = ""
                    st.session_state.otp_start_time = None

                    st.rerun()

            # SIGNUP
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

                    if not st.session_state.otp_verified_for_signup:

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

                                    st.success("OTP verified. Now set your password.")
                                    st.rerun()

                                else:
                                    st.error(message)

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

                        if st.button("Create Account", use_container_width=True):

                            if not new_password or not confirm_password:
                                st.error("Please fill password fields.")

                            elif new_password != confirm_password:
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
                    st.session_state.otp_verified_for_signup = False
                    st.session_state.verified_otp_value = ""

                    st.rerun()

    st.stop()


# =====================================================
# MAIN APP
# =====================================================
user = get_user(st.session_state.user_email)

display_name = "User"

if user and user.get("name"):
    display_name = user.get("name")

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

    current_name = ""

    if user:
        current_name = user.get("name", "")

    profile_name = st.text_input(
        "Name",
        value=current_name
    )

    if st.button("💾 Save Name", use_container_width=True):

        update_name(
            st.session_state.user_email,
            profile_name
        )

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

        st.rerun()


# =====================================================
# HEADER
# =====================================================
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

    if uploaded_file:

        if st.button("🚀 Analyze Resume", use_container_width=True):

            with st.spinner("Reading Resume..."):
                resume_text = extract_text(uploaded_file)

            if not resume_text or not resume_text.strip():
                st.error("❌ Unable to read resume text.")
                st.stop()

            with st.spinner("Validating Resume using AI..."):
                ai = validate_resume(resume_text)

            if ai.get("is_resume") is False:
                st.error("Invalid Resume Detected")
                st.warning(ai.get("reason", "This file does not look like a resume."))
                st.stop()

            if ai.get("is_resume") is None:
                st.warning("Gemini AI unavailable. Running normal ATS scan only.")

                ai = {
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

            st.success("Analysis Completed Successfully")

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

    else:
        st.info("📤 Upload a resume to begin.")

        st.write("---")

        st.subheader("Don’t have a resume?")

        if st.button("✨ Create Resume with AI", use_container_width=True):
            st.session_state.page = "AI CV Maker"
            st.rerun()


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

        target_role = st.selectbox(
            "Target Role",
            job_roles
        )

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

        with st.spinner("Generating Resume using AI..."):

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
