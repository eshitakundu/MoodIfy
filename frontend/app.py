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
        </style>
        """,
        unsafe_allow_html=True
    )

# 🔹 Landing Page Logic
if st.session_state.page == "landing":
    set_background("https://raw.githubusercontent.com/eshitakundu/MoodIfy/main/frontend/backgrounds/landing_page.png")

    # Wait 5 seconds, then change background

    time.sleep(3)
    set_background("https://raw.githubusercontent.com/eshitakundu/MoodIfy/main/frontend/backgrounds/bg.png")