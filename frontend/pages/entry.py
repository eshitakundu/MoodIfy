import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os

#loading environment variables
load_dotenv()

#custom background
bg = st.markdown(
    f"""
    <style>
    .stApp{{
        background: url("https://raw.githubusercontent.com/eshitakundu/MoodIfy/main/frontend/backgrounds/final_bg.png") no-repeat center center fixed;
        background-size: cover;
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

st.markdown("#\n#\n###")

st.markdown('## Let the music drive your mood')

st.markdown("""
<h6 style="color: #f9f7c6;">
    Enter your email to receive a mystery 
    <span class="glow-text">
        <span style="display:inline-block; animation: spin 2s infinite linear;">⭐</span>
        mood capsule
        <span style="display:inline-block; transform: scaleX(-1); animation: spin 2s infinite linear;">⭐</span>
    </span>:
</h6>

<style>
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes glow {
  0% { text-shadow: 0 0 5px #f9c23b; }
  50% { text-shadow: 0 0 15px #f9c23b; }
  100% { text-shadow: 0 0 5px #f9c23b; }
}

.glow-text {
  color: #f9c23b;
  animation: glow 2s infinite ease-in-out;
  font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


email = st.text_input(" ", label_visibility="collapsed")
if st.button("Submit"):
    if email:
        try:
            #Connect to database
            connection = mysql.connector.connect(
                host=os.getenv('HOST'),
                user=os.getenv('USER'),
                password=os.getenv('PASSWORD'),
                database=os.getenv('DATABASE')
            )
            cursor = connection.cursor()
            cursor.execute("INSERT INTO moodify_emails (email) VALUES (%s)", (email,))
            connection.commit()
            st.success("You've been Moodified! Check you email soon. 💌")
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            cursor.close()
            connection.close()
    else:
        st.warning("Please enter a valid email.")