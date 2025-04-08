import streamlit as st
import ollama
from streamlit_modal import Modal
import sqlite3
from datetime import datetime, timedelta
import time
import random
import string

# --------------------- Session State Initialization --------------------- #

def init_session_state():
    defaults = {
        "paid_users": False,
        "username": None,
        "tokens": 0,
        "pay_clicked": False,
        "confirm_clicked": False,
        "register": False,
        "login": False,
        "lockout_until": None,
        "free_user": True,
        "super_users": False,
        "checks_approval": False,
        "Done_approving": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --------------------- Utility Functions --------------------- #

def same_username(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return username not in result

def trigger_lockout(now):
    st.session_state.lockout_until = now + timedelta(minutes=3)
    st.rerun()

def generate_random_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def registry_approval(username):
    conn = sqlite3.connect("registering_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registering_users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, last_logout_time, tokens) VALUES (?, ?, ?, ?)", (username, result[1], None, 0))
    conn.commit()
    conn.close()

def token_add_minus(username, token):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tokens = tokens + ? WHERE username = ?", (token, username))
    conn.commit()
    conn.close()

def delete_registery(ID):
    conn = sqlite3.connect("registering_users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registering_users WHERE register_id = ?", (ID,))
    conn.commit()
    conn.close()

# --------------------- User Interfaces --------------------- #

def register():
    st.title("Register Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    register_id = generate_random_id()

    if st.button("Register"):
        if not same_username(username):
            st.error("Username already exists.")
        elif username and password:
            try:
                conn = sqlite3.connect("registering_users.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO registering_users (username, password, register_id, register_date, register_status) VALUES (?, ?, ?, ?, ?)", (username, password, register_id, now, "Waiting for approval"))
                conn.commit()
                conn.close()
                st.success(f"Registration successful! Your ID is '{register_id}', which can be used to check your approval. Now wait for approval.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.error("Please fill in all fields.")

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

        conn = sqlite3.connect("super_users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM super_users WHERE username = ? AND password = ?", (username, password))
        super_result = cursor.fetchone()
        conn.close()

        if result:
            st.session_state.update({"username": username, "tokens": result[0], "paid_users": True})
            st.success(f"Login successful! You have {result[0]} tokens.")
            st.rerun()
        elif super_result:
            st.session_state.update({"username": username, "password": password, "super_users": True})
            st.rerun()
        else:
            st.error("Invalid username or password")

def super_user():
    st.title("Super User Page")
    username = st.session_state["username"]
    st.sidebar.write(f"Welcome, {username}!")

    conn = sqlite3.connect("registering_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registering_users WHERE register_status = 'Waiting for approval'")
    results = cursor.fetchall()
    conn.close()

    if results:
        st.subheader("Users Awaiting Approval")
        for row in results:
            register_id = row[2]
            with st.expander(f"User: {row[0]} | ID: {register_id} | Status: {row[4]}"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=f"approve_{register_id}"):
                        conn = sqlite3.connect("registering_users.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE registering_users SET register_status = 'Approved' WHERE register_id = ?", (register_id,))
                        conn.commit()
                        conn.close()
                        registry_approval(row[0])
                        st.success(f"{row[0]} has been approved.")
                        st.rerun()
                with col2:
                    if st.button("❌ Reject", key=f"reject_{register_id}"):
                        conn = sqlite3.connect("registering_users.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE registering_users SET register_status = 'Rejected' WHERE register_id = ?", (register_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"{row[0]} has been rejected.")
                        st.rerun()
    else:
        st.info("No users waiting for approval.")

# The rest (homepage, token_purchase_modal, free_user, paid_user) continues below...
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
    if not st.session_state["checks_approval"]:
        homepage(None)
        if st.button("Account Approval Check", key="check_approval"):
            st.session_state["checks_approval"] = True
            st.rerun()
    elif st.session_state["checks_approval"]:
    
        ID = st.text_input("Enter your ID to check approval:")
        if st.button("Check Approval"):
            conn = sqlite3.connect("registering_users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM registering_users WHERE register_id = ?", (ID,))
            conn.commit()
            result = cursor.fetchone()
            conn.close()
            if result[4] == "Approved" or result[4] == "Rejected":
                st.success(f"Your registration status is: {result[4]}")
                delete_registery(ID)
            elif result[4] == "Waiting for approval":
                st.warning(f"Your registration status is: {result[4]}")
            else:
                st.error("Invalid ID or not found.")



# Main execution
if st.session_state["paid_users"]:
    paid_user()
elif st.session_state["super_users"]:
    super_user()
else:
    if st.session_state["login"]:
        login()
    elif st.session_state["register"]:
        register()
    else:
        free_user()
        if st.session_state["checks_approval"] == False:
            if st.button("Login"):
                st.session_state["login"] = True
                st.rerun()
            if st.button("Register"):
                st.session_state["register"] = True
                st.rerun()
