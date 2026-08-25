import streamlit as st
import os

st.set_page_config(page_title="Australian Federal Command", layout="wide")

st.title("🎮 Australian Federal Command")

# Load and display the game HTML
game_html_path = "game.html"

if os.path.exists(game_html_path):
    with open(game_html_path, "r", encoding="utf-8") as f:
        game_html = f.read()
    st.components.v1.html(game_html, height=800, scrolling=True)
else:
    st.error("game.html not found. Please ensure the file is in the same directory as streamlit_app.py")
