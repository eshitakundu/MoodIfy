import streamlit as st
import time

st.set_page_config(
    page_title="Moodify",
    layout="centered",
    page_icon="Ⓜ️"
)

# Track if user clicked
if "page" not in st.session_state:
    st.session_state.page = "landing"

# 🔹 Set Background Function
def set_background(image_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url("{image_url}") no-repeat center center fixed;
            background-size: cover;
        }}
        .click-area {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
            background: rgba(0,0,0,0); /* Invisible click area */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 🔹 Landing Page Logic
if st.session_state.page == "landing":
    set_background("https://raw.githubusercontent.com/eshitakundu/MoodIfy/main/frontend/backgrounds/landing_page.png")

    # Wait 5 seconds, then change background
    time.sleep(5)
    set_background("https://raw.githubusercontent.com/eshitakundu/MoodIfy/main/frontend/backgrounds/landing_page_text.png")

    # Create an invisible button to detect clicks
    if st.button(" "):  # Invisible button
        st.session_state.page = "home"
        st.rerun()

# 🔹 Home Page (After Click)
if st.session_state.page == "home":
    st.title("Welcome to Moodify 🎵")
    st.write("Now we move to the next section of the app!")
