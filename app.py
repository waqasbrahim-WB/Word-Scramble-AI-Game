import random
import json
import os
import streamlit as st
from groq import Groq

# ---------------------------------------------------------
# Page Setup
# ---------------------------------------------------------
st.set_page_config(page_title="AI Word Scramble", page_icon="🔤", layout="centered")
st.title("🔤 AI Word Scramble Game")

# Initialize Groq client using secrets or environment variable
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.warning("⚠️ Please configure your GROQ_API_KEY in Streamlit Secrets or Environment Variables.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# ---------------------------------------------------------
# Game State Initialization
# ---------------------------------------------------------
if "level" not in st.session_state:
    st.session_state.level = 1
if "score" not in st.session_state:
    st.session_state.score = 0
if "current_word" not in st.session_state:
    st.session_state.current_word = None
if "scrambled_word" not in st.session_state:
    st.session_state.scrambled_word = None
if "hint" not in st.session_state:
    st.session_state.hint = None

# ---------------------------------------------------------
# AI Word Generator Function
# ---------------------------------------------------------
def generate_word_for_level(level):
    """Fetch a word and hint from Groq Llama 3 API based on game level."""
    prompt = f"""
    Generate a single English word suitable for level {level} of a word game.
    Higher levels must feature longer or more complex words.
    Return strictly raw JSON format without markdown blocks like:
    {{"word": "EXAMPLE", "hint": "A short clue about the word"}}
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        
        # Strip markdown json blocks if returned
        if content.startswith("```"):
            content = content.split("```")[1].replace("json", "").strip()
            
        data = json.loads(content)
        word = data["word"].upper().strip()
        hint = data["hint"].strip()
        return word, hint
    except Exception:
        # Fallback words if API fails or rate limit hits
        fallbacks = [("PYTHON", "A popular coding language"), ("STREAMLIT", "Python framework for web apps")]
        return random.choice(fallbacks)

def scramble_word(word):
    """Scramble the characters in a word."""
    letters = list(word)
    while len(letters) > 1:
        random.shuffle(letters)
        scrambled = "".join(letters)
        if scrambled != word:
            return scrambled
    return word

def setup_new_round():
    """Load a new word for the current level."""
    word, hint = generate_word_for_level(st.session_state.level)
    st.session_state.current_word = word
    st.session_state.scrambled_word = scramble_word(word)
    st.session_state.hint = hint

# Load initial word if none is active
if st.session_state.current_word is None:
    setup_new_round()

# ---------------------------------------------------------
# Sidebar & Header Info
# ---------------------------------------------------------
st.sidebar.header("🏆 Player Stats")
st.sidebar.metric("Current Level", st.session_state.level)
st.sidebar.metric("Total Score", st.session_state.score)

if st.sidebar.button("Restart Game"):
    st.session_state.level = 1
    st.session_state.score = 0
    setup_new_round()
    st.rerun()

# ---------------------------------------------------------
# Main Game Interface
# ---------------------------------------------------------
st.subheader(f"Level {st.session_state.level}")
st.info(f"💡 **Hint:** {st.session_state.hint}")

st.markdown(f"### Unscramble: `{st.session_state.scrambled_word}`")

with st.form("guess_form", clear_on_submit=True):
    user_guess = st.text_input("Enter your answer:").strip().upper()
    submit_button = st.form_submit_button("Submit Answer")

if submit_button:
    if user_guess == st.session_state.current_word:
        points_earned = st.session_state.level * 10
        st.session_state.score += points_earned
        st.session_state.level += 1
        st.success(f"🎉 Correct! You earned {points_earned} points. Moving to Level {st.session_state.level}...")
        setup_new_round()
        st.rerun()
    else:
        st.error(f"❌ Wrong answer! The correct word was **{st.session_state.current_word}**.")
        st.warning("Game Over! Resetting back to Level 1.")
        st.session_state.level = 1
        setup_new_round()
        st.rerun()
