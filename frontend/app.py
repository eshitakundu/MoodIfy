import streamlit as st

st.set_page_config(
    page_title='Moodify',
    layout='centered',
    page_icon="Ⓜ️"
)

def landing_page():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("https://raw.githubusercontent.com/eshitakundu/MoodIfy/main/frontend/backgrounds/landing_page.png");
            background-size: cover;
        }}
                
        """,
        unsafe_allow_html=True)

landing_page()