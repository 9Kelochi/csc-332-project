import streamlit as st
import ollama
from streamlit_modal import Modal
import sqlite3
from datetime import datetime, timedelta
import time
import random
import string
import difflib

# --------------------- Session State & Navigation --------------------- #
def init_session_state():
    defaults = {
        "self_edit": False,
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
        "page": None,
        "original_text": None,
        "ID": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

def navbar():
    st.markdown("---")
    
    if st.session_state.get("paid_users"):
        # Paid User Navbar
        cols = st.columns(6)
        with cols[0]:
            if st.button("🏠 Home", key="nav_home_paid"):
                st.session_state["page"] = "home"
                st.rerun()
        with cols[1]:
            if st.button("✉️ Invitation", key="nav_invitation_paid"):
                st.session_state["page"] = "invitation"
                st.rerun()
        with cols[2]:
            if st.button("📨 Invites", key="nav_invites_paid"):
                st.session_state["page"] = "invites"
                st.rerun()
        with cols[3]:
            if st.button("🤝 Collab", key="nav_collab_paid"):
                st.session_state["page"] = "collab"
                st.rerun()
        with cols[4]:
            if st.button("📂 Files Saved", key="nav_files_paid"):
                st.session_state["page"] = "files_saved"
        with cols[5]:
            if st.button("🚪 Logout", key="nav_logout_paid"):
                st.session_state["logout"] = True
    elif st.session_state.get("super_users"):
        cols = st.columns(2)
        with cols[0]:
            if st.button("🏠 Home", key="nav_home_paid"):
                st.session_state["page"] = "home"
                st.rerun()
        with cols[1]:
            if st.button("Approval"):
                st.session_state["page"] = "approval"
                st.rerun

    else:
        # Free User Navbar
        cols = st.columns(4)
        with cols[0]:
            if st.button("🏠 Home", key="nav_home_free"):
                st.session_state["page"] = "home"
                st.rerun()
        with cols[1]:
            if st.button("🔑 Login", key="nav_login_free"):
                st.session_state["page"] = "login"
                st.rerun()
        with cols[2]:
            if st.button("📝 Register", key="nav_register_free"):
                st.session_state["page"] = "register"
                st.rerun()
        with cols[3]:
            if st.button("🔎 Check Registration", key="nav_check_free"):
                st.session_state["page"] = "check_register"
                st.rerun()

    st.markdown("---")

# --------------------- Utility Functions (Cross-User) --------------------- #
def get_id(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ID FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return result

def generate_random_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def same_username(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username FROM users
        UNION
        SELECT username FROM super_users
    """)
    all_usernames = [row[0] for row in cursor.fetchall()]

    conn.close()
    if username in all_usernames:
        return True
    else:
        return False

def token_add_minus(username, token):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tokens = tokens + ? WHERE username = ?", (token, username))
    cursor.execute("SELECT tokens FROM users WHERE username = ?", (username,))
    updated_tokens = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    st.session_state["tokens"] = updated_tokens

def word_difference(original, edited, username):
    original_words = original.split()
    edited_words = edited.split()
    matcher = difflib.SequenceMatcher(None, original_words, edited_words)
    difference = 0.0
    result = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            result.extend(edited_words[j1:j2])
        elif tag in ('replace', 'insert'):
            difference += max(i2 - i1, j2 - j1)
            for word in edited_words[j1:j2]:
                result.append(f'<mark>{word}</mark>')
    if username:
        token_add_minus(username, -5 * difference)
    st.session_state['corrected_text'] = ' '.join(result)
    st.session_state["original_text"] = ' '.join(edited_words)

def trigger_lockout(now):
    st.session_state.lockout_until = now + timedelta(minutes=3)
    st.rerun()

# --------------------- Homepage Section --------------------- #
def homepage(username):
    st.title("The Token Terminator")
    now = datetime.now()
    if st.session_state.lockout_until and now < st.session_state.lockout_until:
        remaining = (st.session_state.lockout_until - now).seconds
        timer_placeholder = st.empty()
        for i in range(remaining, 0, -1):
            mins, secs = divmod(i, 60)
            timer_placeholder.warning(f"⏳ You're temporarily locked out. Please wait {mins:02d}:{secs:02d} (mm:ss)")
            time.sleep(1)
        st.rerun()
    
    prompt = st.text_area("Enter text to correct:", height=300)
    Instruction = (
            "Correct the following text for grammar and spelling. "
            "Do not add any explanation, comments, quotation marks, or phrases like '(Corrected)'. "
            "Only return the corrected text, exactly as it should appear.\n\n"
            f"{prompt}"
        )

    

    upload_file = st.file_uploader("Upload a file", type="txt")
    if upload_file is not None:
        prompt = upload_file.read().decode("utf-8")

    text_to_AI = Instruction + prompt
    if st.button("Submit") and prompt:
        if username == None and len(prompt.split()) > 20:
            st.error("Text length exceeds limit for free users.")
            trigger_lockout(now)
            return
        response = ollama.generate(model="mistral", prompt=text_to_AI)
        response = response.get("response", "[No 'response' field found]")
        word_difference(prompt, response, username)
    
    if "corrected_text" in st.session_state:
        st.markdown("""
            <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #f9f9f9; max-height: 300px; overflow-y: auto;">
            """ + st.session_state["corrected_text"] + """
            </div>
            """, unsafe_allow_html=True)
        if username is not None:
            File_name = st.text_input("Input a file name:")
            if st.button("Save File") and File_name:
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                save_id = generate_random_id()
                cursor.execute("SELECT ID FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                ID = result[0]
                cursor.execute("INSERT INTO files (file_id, owner_id, file_name, data, created_at, owner_name) VALUES (?, ?, ?, ?, ?, ?)",(save_id, ID, File_name, st.session_state["original_text"], datetime.now(), username,))
                conn.commit()
                conn.close()
                st.success("Save complete")
    if st.session_state["page"] == 'invites':
        invites(username)
    if st.session_state["page"] == 'invitation':
        invitation(username)
    if st.session_state["page"] == 'collab':
        collab(username)

# --------------------- Free User Section --------------------- #
def register():
    st.title("Register Page")
    username = st.text_input("Username", max_chars = 50)
    password = st.text_input("Password", type="password", max_chars = 50)
    

    if st.button("Register"):
        if same_username(username):
            st.error("Username already exists.")
        elif username and password:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            register_id = generate_random_id()
            try:
                conn = sqlite3.connect("users.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password, ID, register_date, account_approval) VALUES (?, ?, ?, ?, ?)", (username, password, register_id, now, 0))
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
        conn.commit()
        result = cursor.fetchone()
        cursor.execute("SELECT * FROM super_users WHERE username = ? AND password = ?", (username, password))
        conn.commit()
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

def free_user():
    if not st.session_state["page"] == "check_register":
        homepage(None)
        if st.session_state["page"] == "check_register":
            st.session_state["checks_approval"] = True
            st.rerun()
    elif st.session_state["page"] == "check_register":
        ID = st.text_input("Enter your ID to check approval:")
        if st.button("Check Approval"):
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("SELECT account_approval FROM users WHERE ID = ?", (ID,))
            conn.commit()
            result = [row[0] for row in cursor.fetchall()]
            conn.close()
            if result:
                if result[0] == 1:
                    st.success(f"Your registration status has been approved!")
                elif result[0] == 0:
                    st.warning("Your registration is still pending approval.")
            else:
                st.error("Invalid ID or registration not found.")

# --------------------- Paid User Section --------------------- #
def collab(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id FROM file_collaborations WHERE owner_id = ? OR collaborator_id = ?", (get_id(username), get_id(username)))
    results = cursor.fetchall()
    conn.close()

    if results:
        st.subheader("Collab Files")
        for row in results:
            file_id = row[0]
            
        
            edit_key = f"editing_{file_id}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False
            
            with st.expander(f"File ID: {file_id}", expanded=st.session_state[edit_key]):
                if not st.session_state[edit_key]:
                    if st.button("Edit File", key=f"edit_{file_id}"):
                        st.session_state[edit_key] = True
                        st.rerun()
                
                if st.session_state[edit_key]:
                    conn = sqlite3.connect("users.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT data FROM files WHERE file_id = ?", (file_id,))
                    file_data = cursor.fetchone()
                    conn.close()
                    
                    if file_data:
                        edited_content = st.text_area(
                            "File Content", 
                            value=file_data[0], 
                            height=300,
                            key=f"editor_{file_id}"
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 Save", key=f"save_{file_id}"):
                                try:
                                    conn = sqlite3.connect("users.db")
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        "UPDATE files SET data = ? WHERE file_id = ?",
                                        (edited_content, file_id)  
                                    )
                                    conn.commit()
                                    conn.close()
                                    st.success("File updated successfully ✅")
                                    st.session_state[edit_key] = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error saving file: {str(e)}")
                        
                        with col2:
                            if st.button("❌ Cancel", key=f"cancel_{file_id}"):
                                st.session_state[edit_key] = False
                                st.rerun()
                    else:
                        st.error("File not found.")

def invites(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT invite_id, inviter_id, invitee, status, invite_at, file_id FROM invitations WHERE invitee = ?", (username,))
    results = cursor.fetchall()
    conn.close()

    if results:
        st.subheader("Invitations Received")
        for row in results:
            invite_id, inviter_id, invitee_username, status, sent_at, file_id = row
            with st.expander(f"Invitation from {inviter_id} | Status: {status} | Sent at: {sent_at}"):
                col1, col2 = st.columns(2)
                with col1:
                    if status == "pending":
                        if st.button("✅ Accept", key=f"accept_{invite_id}"):
                            conn = sqlite3.connect("users.db")
                            cursor = conn.cursor()
                            cursor.execute("UPDATE invitations SET status = ?, accept_at = ? WHERE invite_id = ?", ("accepted", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), invite_id))
                            conn.commit()
                            conn.close()
                            st.success(f"Invitation from {inviter_id} accepted.")
                            sent_to_collab(invite_id)
                            st.rerun()

                with col2:
                    if st.button("❌ Decline", key=f"decline_{invite_id}"):
                        conn = sqlite3.connect("users.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE invitations SET status = ? WHERE invite_id = ?", ("declined", invite_id))
                        conn.commit()
                        conn.close()
                        st.success(f"Invitation from {inviter_id} declined.")
                        st.rerun()
    else:
        st.info("No invitations received.")

def invitation(username):
    invite_user = st.text_input("Enter the username of the user you want to invite:")
    file = st.text_input("Enter the file name:")
    if st.button("Send Invitation"):
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # Check if the file exists and is owned by the inviter
        cursor.execute("SELECT file_id FROM files WHERE owner_name = ? AND file_name = ?", (username, file))
        file_result = cursor.fetchone()

        if file_result:
            file_id = file_result[0]

            # Get the inviter's user ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            inviter_row = cursor.fetchone()
            inviter_id = inviter_row[0] if inviter_row else None

            if not inviter_id:
                st.error("Inviter ID not found.")
                conn.close()
                return

            # Make sure the invited user exists
            cursor.execute("SELECT username FROM users WHERE username = ?", (invite_user,))
            invited_user_exists = cursor.fetchone()

            if invited_user_exists:
                invite_id = generate_random_id()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Insert the invitation
                cursor.execute("""
                    INSERT INTO invitations 
                    (invite_id, inviter_id, invitee, inviter, status, invite_at, file_name, file_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (invite_id, inviter_id, invite_user, username, "pending", now, file, file_id))

                conn.commit()
                st.success(f"Invitation sent to {invite_user}.")
            else:
                st.error("Invited user not found.")
        else:
            st.error("File not found or not owned by you.")

def token_purchase_modal(username):
    modal = Modal("Pay Token", key="demo-modal", padding=20, max_width=600)
    if st.session_state['page'] == "tokens":
        st.session_state["pay_clicked"] = True
        with st.sidebar:
            st.markdown("<h1 style='color: green;'>100 Tokens = $1.00</h1>", unsafe_allow_html=True)
            amount_t = st.text_input("Pay: ", value="0", key="pay_amount")

            try:
                tokens_purchased = float(amount_t)
            except ValueError:
                tokens_purchased = 0

            total = tokens_purchased / 100
            st.write(f"Total: ${total:.2f}")

            if st.button("Confirm"):
                if tokens_purchased > 0:
                    token_add_minus(username, tokens_purchased)
                    st.success(f"Purchased {int(tokens_purchased)} tokens!")
                else:
                    st.error("Please enter a valid amount.")

def add_logout(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_logout_time = ? WHERE username = ?", (datetime.now(), username))
    conn.commit()
    conn.close()

def paid_user():
    username = st.session_state["username"]
   #tokens = st.session_state["tokens"]
    st.sidebar.write("Token Balance:", st.session_state["tokens"])
    homepage(username)
    token_purchase_modal(username)
    if st.session_state.get("logout") == True:
        add_logout(username)
        st.session_state["paid_users"] = False
        st.session_state["username"] = None
        st.session_state["tokens"] = 0
        st.session_state["logout"] = False
        st.rerun()

# --------------------- Super User Section --------------------- #
def super_user():
    st.title("Super User Page")
    username = st.session_state["username"]
    st.sidebar.write(f"Welcome, {username}!")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, ID, account_approval FROM users WHERE account_approval = 0")
    results = cursor.fetchall()
    conn.close()

    if results:
        st.subheader("Users Awaiting Approval")
        for row in results:
            register_id = row[1]
            with st.expander(f"User: {row[0]} | ID: {register_id} | Status: Waiting for Approval"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=f"approve_{register_id}"):
                        conn = sqlite3.connect("users.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET account_approval = 1 WHERE register_id = ?", (register_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"{row[0]} has been approved.")
                        registry_approval(row[0])
                        st.rerun()
                with col2:
                    if st.button("❌ Reject", key=f"reject_{register_id}"):
                        conn = sqlite3.connect("users.db")
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM users WHERE register_id = ?", (register_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"{row[0]} has been rejected.")
                        st.rerun()
    else:
        st.info("No users waiting for approval.")

def registry_approval(username):
    approved_Date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET account_approval = ?, approved_Date = ?, tokens = ?, approved_by = ? WHERE username = ?",
        (1, approved_Date, 0, username, st.session_state["username"])
    )
    conn.commit()
    conn.close()

def delete_registery(ID):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE ID = ?", (ID,))
    conn.commit()
    conn.close()

# --------------------- Main Execution --------------------- #
navbar()

if st.session_state["paid_users"]:
    paid_user()
elif st.session_state["super_users"]:
    super_user()
else:
    if st.session_state["page"] == "login":
        login()
    elif st.session_state["page"] == "register":
        register()
    else:
        free_user()
