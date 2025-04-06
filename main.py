import streamlit as st
import ollama
from streamlit_modal import Modal
import sqlite3


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


# Paid user interface
def paid_user():
    st.title("Grammarly")
    username = st.session_state["username"]
    tokens = st.session_state["tokens"]
    st.sidebar.write(f"Token Balance: {tokens}")
    Instruction = "Please edit the text if it has any grammar error, you don't need to return anything else other than the text itself."
    prompt = st.text_input("Enter text to correct:")
    upload_file = st.file_uploader("Upload a file", type="txt")
    if upload_file is not None:
        prompt = upload_file.read().decode("utf-8")

    text_to_AI = Instruction + prompt
    if st.button("Submit") and prompt:
        response = ollama.chat(model="gemma3", messages=[{"role": "user", "content": text_to_AI}])
        response = response['message']['content']
        token_used(username, prompt, response)

    token_purchase_modal(username)


# Initialize the database

# Main execution
if st.session_state["username"]:
    paid_user()
else:
    login()
