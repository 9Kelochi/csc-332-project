import streamlit as st
import ollama
from streamlit_modal import Modal
import pandas as pd


account_file = pd.read_csv("Paid_Users.csv")
account_file["Account"] = account_file["Account"].astype(str).str.strip()
account_file["Password"] = account_file["Password"].astype(str).str.strip()
account_file["Tokens"] = pd.to_numeric(account_file["Tokens"], errors="coerce").fillna(0).astype(float)

# Initialize session state variables if not set
if "username" not in st.session_state:
    st.session_state["username"] = None
if "tokens" not in st.session_state:
    st.session_state["tokens"] = 0
if "pay_clicked" not in st.session_state:
    st.session_state["pay_click= Falseed"] = False
if "confirm_clicked" not in st.session_state:
    st.session_state["confirm_clicked"] = False

# Login function
def login():
    st.title("Login Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        match = ((account_file["Account"] == username) & (account_file["Password"] == password)).any()
        if match:
            user_tokens = account_file.loc[account_file["Account"] == username, "Tokens"].values[0]
            st.session_state["username"] = username  # Store username in session
            st.session_state["tokens"] = user_tokens  # Store tokens in session
            st.success(f"Login successful! You have {user_tokens} tokens.")
            st.rerun()
        else:
            st.error("Invalid username or password")

# Paid user interface
def paid_user():
    st.title("Grammarly")
    username = st.session_state["username"]  # Get logged-in user
    user_data = account_file[account_file["Account"] == username].iloc[0]
    st.session_state.tokens = float(user_data["Tokens"])
    st.sidebar.write(f"Token Balance: {st.session_state.tokens}")
    
    prompt = st.text_input("Enter text to correct:")
    upload_file = st.file_uploader("Upload a file", type="txt")
    if upload_file is not None:
        prompt = upload_file.read().decode("utf-8")

    prompt = "Please correct the grammar in the following text: " + prompt
    if st.button("Submit") and prompt:
        response = ollama.chat(model="gemma3", messages=[{"role": "user", "content": prompt}])
        st.write("### Response:")
        st.write(response['message']['content'])

    # Token purchase modal
    modal = Modal(
        "Pay Token", 
        key="demo-modal",
        padding=20,
        max_width=600,
    )

    if st.button("Tokens"):
        st.session_state["pay_clicked"] = True
        modal.open()

    if modal.is_open():
        with modal.container():
            st.markdown("<h1 style='color: green;'>100 Tokens = $1.00</h1>", unsafe_allow_html=True)
            amount_t = st.text_input("Pay: ", value="0")
            total = float(amount_t) / 100

            if st.button("Pay"):
                st.session_state["pay_clicked"] = True

            if st.session_state["pay_clicked"]:
                st.write(f"Total: ${total:.2f}")
                if st.button("Confirm"):
                    st.session_state["confirm_clicked"] = True

            if st.session_state["confirm_clicked"]:
                st.success("Purchase successful!")
            account_file.loc[account_file["Account"] == username, "Tokens"] += float(amount_t)
            account_file.to_csv("Paid_Users.csv", index=False) 
            st.session_state["tokens"] += st.session_state.tokens
            st.rerun()
# Main execution flow
if st.session_state["username"]:
    paid_user()
else:
    login()
