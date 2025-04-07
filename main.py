import streamlit as st
import ollama
from streamlit_modal import Modal
import sqlite3
from datetime import datetime, timedelta
import time
# Initialize session state
if "username" not in st.session_state:
    st.session_state["username"] = None
if "tokens" not in st.session_state:
    st.session_state["tokens"] = 0
if "pay_clicked" not in st.session_state:
    st.session_state["pay_clicked"] = False
if "confirm_clicked" not in st.session_state:
    st.session_state["confirm_clicked"] = False
if "register" not in st.session_state:
    st.session_state["register"] = False
if "login" not in st.session_state:
    st.session_state["login"] = False
if "lockout_until" not in st.session_state:
    st.session_state.lockout_until = None
if "free_user" not in st.session_state:
    st.session_state["free_user"] = True
def trigger_lockout(now):
    st.session_state.lockout_until = now + timedelta(minutes=3)
    st.rerun()

def registry_approval(username):
    conn = sqlite3.connect("registering_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, tokens) VALUES (?, ?, >)", (result[1], result[2], 0))
    if result:
        st.success("Registration approved! You can now log in.")
        st.session_state["login"] = True
        st.session_state["register"] = False
    else:
        st.error("Registration not approved yet. Please wait.")

def register():
    st.title("Register Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        conn = sqlite3.connect("registering_users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        st.success("Registration successful! Now wait for approval.")
# Token modification function
def token_add_minus(username, token):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET tokens = tokens + ?
        WHERE username = ?
    ''', (token, username))
    conn.commit()
    conn.close()


# Login function
def login():
    st.title("Login Page")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", key="Login button"):
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT tokens FROM users WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone()
        conn.close()

        if result:
            user_tokens = result[0]
            st.session_state["username"] = username
            st.session_state["tokens"] = user_tokens
            st.success(f"Login successful! You have {user_tokens} tokens.")
            st.rerun()
        else:
            st.error("Invalid username or password")


# Token purchase modal
def token_purchase_modal(username):
    modal = Modal("Pay Token", key="demo-modal", padding=20, max_width=600)
    if st.button("Tokens"):
        st.session_state["pay_clicked"] = True
        modal.open()

    if modal.is_open():
        with modal.container():
            st.markdown("<h1 style='color: green;'>100 Tokens = $1.00</h1>", unsafe_allow_html=True)
            amount_t = st.text_input("Pay: ", value="0")

            try:
                tokens_purchased = float(amount_t)
            except ValueError:
                tokens_purchased = 0

            total = tokens_purchased / 100
            st.write(f"Total: ${total:.2f}")

            if st.button("Confirm"):
                if tokens_purchased > 0:
                    token_add_minus(username, tokens_purchased)
                    conn = sqlite3.connect("users.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT tokens FROM users WHERE username = ?", (username,))
                    updated_tokens = cursor.fetchone()[0]
                    conn.close()
                    st.session_state["tokens"] = updated_tokens
                    st.success(f"Purchased {int(tokens_purchased)} tokens!")
                    st.rerun()
                else:
                    st.error("Please enter a valid amount.")

def homepage(username):
    st.title("Grammarly")
    now = datetime.now()
    if st.session_state.lockout_until and now < st.session_state.lockout_until:
        remaining = (st.session_state.lockout_until - now).seconds
        timer_placeholder = st.empty()
        for i in range(remaining, 0, -1):
            mins, secs = divmod(i, 60)
            timer_placeholder.warning(f"⏳ You're temporarily locked out. Please wait {mins:02d}:{secs:02d} (mm:ss)")
            time.sleep(1)
        st.rerun()
        return
    Instruction = "Please edit the text if it has any grammar error, you don't need to return anything else other than the text itself."
    prompt = st.text_input("Enter text to correct:")
    upload_file = st.file_uploader("Upload a file", type="txt")
    if upload_file is not None:
        prompt = upload_file.read().decode("utf-8")

    text_to_AI = Instruction + prompt
    if st.button("Submit") and prompt:
        if username == None and len(prompt) > 20:
            st.error("Text length exceeds limit for free users.")
            trigger_lockout(now)
            return
        response = ollama.chat(model="gemma3", messages=[{"role": "user", "content": text_to_AI}])
        response = response['message']['content']
        token_used(username, prompt, response)
# Paid user interface
def paid_user():
    username = st.session_state["username"]
    tokens = st.session_state["tokens"]
    st.sidebar.write(f"Token Balance: {tokens}")
    homepage(username)

    token_purchase_modal(username)
def free_user():
    homepage(None)


# Main execution
if st.session_state["username"]:
    paid_user()
else:
    if st.session_state["login"]:
        login()
    elif st.session_state["register"]:
        register()
    else:
        free_user()
        if st.button("Login"):
            st.session_state["login"] = True
            st.rerun()
        if st.button("Register"):
            st.session_state["register"] = True
            st.rerun()
