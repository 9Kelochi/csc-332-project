import streamlit as st
import ollama
from streamlit_modal import Modal
import pandas as pd

account_file = pd.read_csv("Paid_Users.csv")
account_file["Account"] = account_file["Account"].astype(str).str.strip()
account_file["Password"] = account_file["Password"].astype(str).str.strip()
account_file["Tokens"] = pd.to_numeric(account_file["Tokens"], errors="coerce").fillna(0).astype(float)


if "username" not in st.session_state:
    st.session_state["username"] = None
if "tokens" not in st.session_state:
    st.session_state["tokens"] = 0
if "pay_clicked" not in st.session_state:
    st.session_state["pay_clicked"] = False
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
            st.session_state["username"] = username 
            st.session_state["tokens"] = user_tokens  
            st.success(f"Login successful! You have {user_tokens} tokens.")
            st.rerun()
        else:
            st.error("Invalid username or password")


# Function to handle token purchase modal
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
                
                    st.session_state["tokens"] += tokens_purchased  

                
                    account_file.loc[account_file["Account"] == username, "Tokens"] = st.session_state["tokens"]

                
                    account_file.to_csv("Paid_Users.csv", index=False)  

                    st.success("Purchase successful!")
                    st.rerun()
                else:
                    st.error("Please enter a valid amount.")

def token_used(username, prompt, edit_response):
    original_text = prompt.split()
    edit_text = edit_response.split()
    difference = sum(1 for o, e in zip(original_text, edit_text) if o != e) * 5

    st.session_state["tokens"] -= difference
    account_file.loc[account_file["Account"] == username, "Tokens"] = st.session_state["tokens"]
    account_file.to_csv("Paid_Users.csv", index=False)
    st.rerun()

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
        token_used(username, prompt, response.__str()__)
        
        

    token_purchase_modal(username)


# Main execution flow
if st.session_state["username"]:
    paid_user()
else:
    login()
