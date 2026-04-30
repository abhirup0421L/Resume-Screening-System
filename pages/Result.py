# Result.py

import streamlit as st

st.title("📊 Resume Screening Result")

if "score" in st.session_state:

    role = st.session_state.role
    score = st.session_state.score
    matched = st.session_state.matched
    missing = st.session_state.missing

    st.subheader(f"Selected Role: {role}")

    st.metric("ATS Match Score", f"{score}%")

    # Status
    if score >= 85:
        st.success("Excellent Candidate Match ✅")
    elif score >= 65:
        st.warning("Good Candidate Match 👍")
    else:
        st.error("Needs Improvement ❌")

    # Progress Bar
    st.progress(score / 100)

    # Matched Skills
    st.subheader("✅ Matched Skills")
    if matched:
        for skill in matched:
            st.write("•", skill)
    else:
        st.write("No matched skills found")

    # Missing Skills
    st.subheader("❌ Missing Skills")
    if missing:
        for skill in missing:
            st.write("•", skill)
    else:
        st.write("No missing skills")

    # Suggestions
    st.subheader("💡 Suggestions")

    if missing:
        st.write("Improve these skills to increase selection chances:")
        for skill in missing:
            st.write("➡️", skill)
    else:
        st.write("Great profile! You match all required skills.")

else:
    st.warning("Please upload and analyze a resume first.")
