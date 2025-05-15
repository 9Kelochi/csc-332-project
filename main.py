import streamlit as st
import ollama
from streamlit_modal import Modal
import sqlite3
from datetime import datetime, timedelta
import time
import random
import string
import difflib
from streamlit_extras.stylable_container import stylable_container

# --------------------- Session State & Navigation --------------------- #
def init_session_state():
    defaults = {
        "self_edit": False,
        "paid_users": False,
        "username": None,
        "userID": None,
        "tokens": 0,
        "pay_clicked": False,
        "confirm_clicked": False,
        "register": False,
        "login": False,
        "lockout_until": None,
        "free_user": False,
        "super_users": False,
        "checks_approval": False,
        "Done_approving": False,
        "page": None,
        "original_text": None,
        "ID": None,
        "buy": False,
        "background": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

def navbar():
    st.markdown("---")

    
    if st.session_state.get("paid_users"):
        # Paid User Navbar
        cols = st.columns(5)
        with cols[0]:
            if st.button("🏠 Home", key="nav_home_paid"):
                st.session_state["page"] = "home"
                st.rerun()
        with cols[1]:  # adjust the column index as needed
            if st.button("🚫 Blacklist", key="nav_blacklist"):
                st.session_state["page"] = "blacklist"
                st.rerun()
        with cols[2]:
            if st.button("✉️ Invitation", key="nav_invitation_paid"):
                st.session_state["page"] = "invitation"
                st.rerun()
        with cols[3]:
            if st.button("📨 Invites", key="nav_invites_paid"):
                st.session_state["page"] = "invites"
                st.rerun()
        with cols[4]:
            if st.button("🤝 Collab", key="nav_collab_paid"):
                st.session_state["page"] = "collab"
                st.rerun()
        cols = st.columns(5)
        with cols[0]:
            if st.button("📂 Files Saved", key="nav_files_paid"):
                st.session_state["page"] = "files_saved"
        with cols[1]:
            if st.button("💰 Buy Tokens", key="nav_tokens_paid"):
                st.session_state["buy"] = True
                st.rerun()
        with cols[2]:
            if st.button("🌈 Background", key="nav_background_color"):
                st.session_state["page"] = "background_color" 
        with cols[3]:
            if st.button("📬 My Rejections", key="nav_my_rejections"):
                st.session_state["page"] = "my_rejections"
                st.rerun()
        with cols[4]:
            if st.button("🚪 Logout", key="nav_logout_paid"):
                st.session_state["logout"] = True
               
    elif st.session_state.get("super_users"):
        cols = st.columns(4)
        with cols[0]:
            if st.button("🏠 Home", key="nav_home_super"): 
                st.session_state["page"] = "home"
                st.rerun()
        with cols[1]:
            if st.button("Approval", key="nav_approval_super"):
                st.session_state["page"] = "approval"
                st.rerun()
        with cols[2]:
            if st.button("Accept Upgrade", key="nav_accept_super"):
                st.session_state["page"] = "accept"
                st.rerun()
        with cols[3]: 
            if st.button("Complaints", key="nav_complaint_super"): 
                st.session_state["page"] = "complaints"
                st.rerun() 
        cols = st.columns(3)
        with cols[0]:
            if st.button("Blacklist", key="nav_Blacklist_super"): 
                st.session_state["page"] = "blacklist"
                st.rerun()
        with cols[1]:
            if st.button("Rejections", key="nav_rejection_super"):
                st.session_state["page"] = "rejections"
                st.rerun() 
        with cols[2]:
            if st.button("🚪 Logout", key="nav_logout_super"):
                st.session_state["logout"] = True

    elif st.session_state.get("free_user"):
        # Free User Navbar
        cols = st.columns(4) # was 4 
        with cols[0]:
            if st.button("🏠 Home", key="nav_home_free"):
                st.session_state["page"] = "home"
                st.rerun()
        with cols[1]:  # adjust the column index as needed
            if st.button("🚫 Blacklist", key="nav_blacklist"):
                st.session_state["page"] = "blacklist"
                st.rerun()
        with cols[2]:
            if st.button("🚪 Logout", key="nav_login_free"):
                st.session_state["logout"] = True
        with cols[3]:
            if st.button("💵 Became Paid Users"):
                st.session_state["page"] = "paid_page"

    else: 
        # NO user navbar 
        if st.session_state['page'] == None:
            st.markdown("""
                <div style="background-color: #ffefc6; padding: 15px; border-radius: 10px; font-size: 30px; color: black;">
                    ⚠️ You are not currently logged in. Choose one of the options above.
                </div>
            """, unsafe_allow_html=True)
        cols = st.columns(3)
        with cols[0]:
            if st.button("Register", key='no_user_register_button'):
                st.session_state["page"] = 'register'
        with cols[1]:
            if st.button("Login", key='no_user_login_button'):
                st.session_state["page"] = 'login'
        with cols[2]:
            if st.button("Check Register", key='no_user_check_register_button'):
                st.session_state["page"] = 'check_registry'


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



def submit_blacklist_request(username):
    st.subheader("🛑 Submit a Word to be Blacklisted")
    word_to_block = st.text_input("Enter a word you want added to the blacklist:")

    if st.button("Submit Blacklist Request"):
        if not word_to_block.strip():
            st.warning("Please enter a valid word.")
            return

        word_to_block = word_to_block.lower().strip()

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # check if word already blacklisted
        cursor.execute("SELECT word FROM blacklisted_words WHERE word = ?", (word_to_block,))
        if cursor.fetchone():
            st.info("That word is already blacklisted.")
            conn.close()
            return

        # check if already requested
        cursor.execute("SELECT word FROM blacklist_requests WHERE word = ?", (word_to_block,))
        if cursor.fetchone():
            st.info("That word is already in the request queue.")
            conn.close()
            return

        # insert new request
        cursor.execute("""
            INSERT INTO blacklist_requests (word, requestedBy, status)
            VALUES (?, ?, ?)
        """, (word_to_block, username, "PENDING"))
        conn.commit()
        conn.close()
        st.success("Blacklist request submitted!")

    # show user's past requests
    st.subheader("📄 Your Blacklist Requests")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT word, status FROM blacklist_requests WHERE requestedBy = ?", (username,))
    requests = cursor.fetchall()
    conn.close()

    if requests:
        for word, status in requests:
            st.markdown(f"- **{word}** → `{status}`")
    else:
        st.info("You haven't submitted any blacklist requests yet.")



def word_difference(original, edited, username, user_dict_words=None):
    if user_dict_words is None:
        user_dict_words = []

    user_dict_words_lower = [w.lower() for w in user_dict_words]

    original_words = original.split()
    edited_words = edited.split()
    matcher = difflib.SequenceMatcher(None, original_words, edited_words)
    difference = 0.0
    result = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            result.extend(edited_words[j1:j2])
        
        elif tag in ('replace', 'insert'):
            # difference += max(i2 - i1, j2 - j1)
            for word in edited_words[j1:j2]:
                if word.lower() in user_dict_words_lower:
                    result.append(word)
                else:
                    result.append(f'<mark>{word}</mark>')
                    difference += 1

    st.session_state['corrected_text'] = ' '.join(result)
    st.session_state["original_text"] = ' '.join(original_words)
    st.session_state["llm_diff_count"] = difference  # Store the difference for token charge after user decides


    return difference == 0.0 

def trigger_lockout(now):
    st.session_state.lockout_until = now + timedelta(minutes=3)
    st.rerun()

# --------------------- Homepage Section --------------------- #
def homepage(username, userID):
    st.title("The Token Terminator")
    now = datetime.now()

    # lock out free users if using more than 20 words
    if st.session_state.lockout_until and now < st.session_state.lockout_until:
        remaining = (st.session_state.lockout_until - now).seconds
        timer_placeholder = st.empty()
        for i in range(remaining, 0, -1):
            mins, secs = divmod(i, 60)
            timer_placeholder.warning(f"⏳ You're temporarily locked out. Please wait {mins:02d}:{secs:02d} (mm:ss)")
            time.sleep(1)
        st.rerun()

    correction_mode = st.radio("Choose correction mode:", ["LLM Correction", "Self-Correction"], horizontal=True)

    # the below deals with LLM correction option
    # available models
    available_models = ["mistral", "llama2", "gemma"]

    # default model is set in session state
    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = "mistral"

    if st.session_state.get("paid_users"):
        try:
            default_index = available_models.index(st.session_state["selected_model"])
        except ValueError:
            default_index = 0  # fallback to first model if invalid
        

        llm_model = st.selectbox(
            "Choose a language model:",
            available_models,
            index=default_index
        )
        st.markdown("""
            <style>
            /* Make selected option text black */
            div[data-baseweb="select"] div[value] {
                color: black !important;
            }
            div[class*="st-emotion-cache-qiev7j"] {
                color: black !important;
            }
            div[data-baseweb="option"] {
                color: black !important;
                background-color: white !important;
            }
            </style>
            """, unsafe_allow_html=True)




        if llm_model != st.session_state["selected_model"]:
            if st.button("Select Model"):
                if st.session_state["tokens"] >= 5:
                    st.session_state["tokens"] -= 5
                    st.session_state["selected_model"] = llm_model
                    st.info(f"Switched LLM to {llm_model}. Charged 5 tokens.")
                    st.rerun()  # Refresh with updated model
                else:
                    st.error("Not enough tokens to switch models.")
                    return
    else:
        llm_model = "mistral"
        st.info("Free accounts use the default LLM: mistral.")
        
    prompt = st.text_area("Enter text to correct:", height=300)

    upload_file = st.file_uploader("Upload a file", type="txt")
    if upload_file is not None:
        prompt = upload_file.read().decode("utf-8")

    # load list of blacklisted words
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM blacklisted_words")
    blacklisted = [row[0].lower() for row in cursor.fetchall()]

    # load in the user's dictionary (words not to replace)
    cursor.execute("SELECT word FROM user_dictionary WHERE owner = ?", (username,))
    user_dict_words = set(row[0].lower() for row in cursor.fetchall())
    formatted_dict_words = ", ".join(user_dict_words)
    conn.close()

    # replace blacklisted words with corresponding *
    words = prompt.split()
    cleaned_words = []
    blacklist_token_cost = 0

    for word in words:
        lower_word = word.lower()
        # clean_word = word.strip(".,!?").lower()
        if lower_word in blacklisted:
            cleaned_words.append("*" * len(word))
            blacklist_token_cost += len(word)
        elif lower_word in user_dict_words:
            cleaned_words.append(word)
        else:
            cleaned_words.append(word)

    cleaned_prompt = " ".join(cleaned_words)

    # show updated version to be submitted 
    if prompt:
        st.subheader("Text with blacklisted words masked:")
        st.markdown("""
            <style>
                .custom-box {
                    background-color: #f0f0f0 !important;
                    color: black !important;
                    padding: 10px;
                    border-radius: 5px;
                }
            </style>
        """, unsafe_allow_html=True)
        st.markdown(f"<div class='custom-box'>{cleaned_prompt}</div>", unsafe_allow_html=True)


        
    # On Submit
    if st.button("Submit") and prompt:
        st.session_state["submitted"] = True

    if st.session_state.get("submitted") == True:
        word_count = len(words)
        user_tokens = st.session_state["tokens"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT paid FROM users WHERE ID = ?", (userID,))
        result = cursor.fetchone()
        if result:
            paiduserr = result[0]
            paiduser = int(paiduserr)
        conn.commit()
        conn.close()
        
        # check free user token limit
        if paiduser == 0 and word_count > 20:
            st.error("Text length exceeds limit for free users.")
            trigger_lockout(now)
            return

        # check for enough tokens for paid users
        if user_tokens < word_count and paiduser == 1:
            penalty = user_tokens // 2
            st.session_state["tokens"] -= penalty
            st.error(f"Not enough tokens. Penalty applied: -{penalty} tokens.")
            return

        # check for enough tokens for blacklisted words for paid users
        if st.session_state["tokens"] < blacklist_token_cost and paiduser == 1:
            st.error(f"Not enough tokens to process blacklisted words. Required: {blacklist_token_cost}")
            return
        else:
            st.session_state["tokens"] -= blacklist_token_cost

        # self correction option
        if correction_mode == "Self-Correction":
            token_cost = word_count // 2
            if st.session_state["tokens"] < token_cost and paiduser == 1:
                st.error(f"Not enough tokens for self-correction (need {token_cost}).")
                return
            st.session_state["tokens"] -= token_cost

            # Use LLM to identify incorrect words, but do not auto-correct
            instruction = (
                "You will receive a paragraph of text. Do not correct it. "
                "Instead, identify only the words that are grammatically incorrect or have spelling mistakes. "
                "Return a comma-separated list of only those words. No explanations, no corrections.\n\n"
                f"{cleaned_prompt}"
            )

            llm_model = st.session_state.get("selected_model", "mistral")

            with st.spinner("🔍 Checking for issues..."):
                response = ollama.generate(model=llm_model, prompt=instruction)
                response = response.get("response", "")
            
            # st.info(f"The model found these words to be incorrect: {response}")
            incorrect_words = [w.strip().lower() for w in response.split(",") if w.strip()]
            highlighted = []

            for word in cleaned_prompt.split():
                if word.lower().strip(".,!?") in incorrect_words:
                    highlighted.append(f"<mark>{word}</mark>")
                else:
                    highlighted.append(word)

            highlighted_text = " ".join(highlighted)

            # Save both for consistency
            st.session_state["original_text"] = cleaned_prompt
            st.session_state["corrected_text"] = highlighted_text
            st.info("Incorrect words have been highlighted. Please self-correct them below.")
            st.markdown(f"<div class='correction-box'>{st.session_state['corrected_text']}</div>", unsafe_allow_html=True)

            return


        
        # LLM correction
        instruction = (
            "Correct the following text for grammar and spelling. "
            "Do not add any explanation, comments, quotation marks, or phrases like '(Corrected)'. "
            "Only return the corrected text, exactly as it should appear."
            "If you see a word included the user's dictionary below, do NOT correct them."
            "Leave the word in its position in the text in its exact form."
            f"Words to NOT correct: {formatted_dict_words} \n\n"
            f"{cleaned_prompt}"
        )

        llm_model = st.session_state["selected_model"] if st.session_state.get("paid_users") else "mistral"

        with st.spinner("🧠 LLM is thinking..."):
            response = ollama.generate(model=llm_model, prompt=instruction)
            response = response.get("response", "[No 'response' field found]")
            st.session_state["response_holder"] = response

        no_diff = word_difference(cleaned_prompt, response, username)

        if no_diff and len(cleaned_prompt.split()) > 10:
            token_add_minus(username, 3)
            st.success("No errors found in your text! You've earned +3 tokens.")

        # show highlighted output
        if "corrected_text" in st.session_state:
            st.markdown("""
                <style>
                    .correction-box {
                        background-color: #f9f9f9 !important;
                        color: black !important;
                        padding: 15px;
                        border: 2px solid #ccc;
                        border-radius: 10px;
                        max-height: 300px;
                        overflow-y: auto;
                        font-size: 16px;
                        line-height: 1.5;
                    }
                    .correction-box mark {
                        background-color: yellow !important;
                        color: black !important;
                    }
                </style>
            """, unsafe_allow_html=True)

            st.markdown(f"<div class='correction-box'>{st.session_state['corrected_text']}</div>", unsafe_allow_html=True)

            
            # accept corrections
            if st.session_state.get("paid_users") and st.session_state.get("llm_diff_count", 0) > 0:
                st.subheader("Accept LLM Correction?")
                if st.button("Accept All Corrections"):
                    token_add_minus(username, int(st.session_state["llm_diff_count"]) * -5)
                    st.success(f"Accepted correction. Charged {int(st.session_state['llm_diff_count']) * 5} tokens.")
                    del st.session_state["llm_diff_count"]
                    st.session_state["submitted"] = None
                    st.session_state["response_holder"] = None
                    st.rerun()  

            
            # save file if user is logged in
            if username is not None:
                with stylable_container(
                    key="custom_input_container",
                    css_styles="""
                        input[type="text"] {
                            color: black !important;
                            background-color: white !important;
                            border: 1px solid #ccc !important;
                        }

                        label {
                            color: black !important;
                        }
                    """
                ):
                    File_name = st.text_input("Input a file name:", key=f"file_input_key")
                if st.button("Save File") and File_name:
                    save_id = generate_random_id()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    conn = sqlite3.connect('users.db')
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO files (file_id, owner_id, file_name, data, created_at, owner_name) VALUES (?, ?, ?, ?, ?, ?)",
                        (save_id, userID, File_name, st.session_state["response_holder"], now, username,))
                    conn.commit()
                    conn.close()
                    st.session_state["submitted"] = None
                    st.session_state["response_holder"] = None
                    st.success("Save complete")
                    st.rerun()


            # Reject LLM correction 
            if username is not None and st.session_state["corrected_text"] != st.session_state["original_text"]:
                st.subheader("Reject Correction (Optional)")
                rejection_reason = st.text_area("If you disagree with the LLM's correction, explain why:")
                if st.button("Submit Rejection"):
                    rejection_id = generate_random_id()
                    conn = sqlite3.connect("users.db")
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO llm_rejections (
                            rejection_id, username, original_text, corrected_text, reason
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        rejection_id,
                        username,
                        st.session_state["original_text"],
                        st.session_state["corrected_text"],
                        rejection_reason
                    ))

                    conn.commit()
                    conn.close()


                    # clear diff count so it can't get applied accidentally later
                    if "llm_diff_count" in st.session_state:
                        del st.session_state["llm_diff_count"]
                    st.success("Your rejection has been submitted for review.")
                    time.sleep(1.5)
                    st.session_state["submitted"] = None
                    st.session_state["response_holder"] = None
                    st.rerun()
                                    




# ---------------------  NO User Section  --------------------- #
# if not logged in; obligate user to login. 
def register():
    st.title("Register Page")


    username = st.text_input("Username", max_chars=50)    
    password = st.text_input("Password", type="password", max_chars=50)

    if st.button("Register"):
        if same_username(username):
            st.error("Username already exists.")
        else:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            register_id = generate_random_id()

            try:
                conn = sqlite3.connect("users.db")
                cursor = conn.cursor()

            
                cursor.execute(
                    "INSERT INTO users (username, password, ID, tokens, register_date, account_approval) VALUES (?, ?, ?, ?, ?, ?)",
                    (username, password, register_id, 0, now, 0)
                )
                conn.commit()
                conn.close()
                st.success(f"Registration successful! Your ID is '{register_id}'. Wait for approval.")

            except Exception as e:
                st.error(f"An error occurred: {e}")

def login():
    st.title("Login Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", key="Login button"):
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # check for paid user
        cursor.execute("SELECT ID, tokens, background FROM users WHERE username = ? AND password = ? AND account_approval = 1 AND paid = 1", (username, password))
        paid_result = cursor.fetchone()
        if paid_result:
            eID, tokens, background = paid_result

        # check for super user
        cursor.execute("SELECT * FROM super_users WHERE username = ? AND password = ?", (username, password))
        super_result = cursor.fetchone()

        # check for free user (note empty string OR NULL)
        cursor.execute("SELECT ID, tokens FROM users WHERE username = ? AND account_approval = 1 AND paid = 0", (username,))
        free_result = cursor.fetchone()
        if free_result:
            eID, tokens = free_result

        conn.close()

        if paid_result:
            st.session_state.login_success = True
            st.session_state.username = username
            st.session_state.userID = eID
            st.session_state.tokens = tokens
            st.session_state.paid_users = True
            st.session_state['page'] = 'home'
            st.session_state["background"] = background

        elif super_result:
            st.session_state.login_success = True
            st.session_state.username = username
            st.session_state.super_users = True

        elif free_result:
            st.session_state.login_success = True
            st.session_state.username = username
            st.session_state.userID = eID
            st.session_state.tokens = tokens
            st.session_state.paid_users = False
            st.session_state.free_user = True
            st.session_state['page'] = 'home'


        else:
            st.error("Invalid username or password")
            return

        st.rerun()



def check_register():
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


def no_user():
    #st.title("No User Page")
    st.markdown("""
        <style>
            button[aria-label="no_user_register_button"] {
                background-color: #4CAF50 !important;
                color: white !important;
                font-size: 18px !important;
                padding: 12px 24px !important;
                border-radius: 8px !important;
                font-weight: bold !important;
            }

            button[aria-label="no_user_register_button"]:hover {
                background-color: #388e3c !important;
                transition: 0.3s ease;
            }
        </style>
        """, unsafe_allow_html=True)


    # HTML wrapper for centering
    st.markdown('<div class="center-buttons">', unsafe_allow_html=True)
    
    if st.session_state['page'] == 'register':
        register()
    elif st.session_state['page'] == 'login':
        login()
    elif st.session_state['page'] == 'check_registry':
        check_register()
    


# --------------------- Free User Section --------------------- #
def paid_page(username):
    st.write("Paid at least a minimun of $1 to became a paid users")
    amount = st.text_input("Enter your amount: ")
    if st.button("Submit"):
        if float(amount) >= 1.00:
            tokens = float(100 * amount)
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            app_id = generate_random_id()
            cursor.execute("INSERT INTO pending_users VALUES (?, ?, ?, ?, ?)", (app_id, username, "paid", tokens, 0))
            conn.commit()
            conn.close()
            st.success("Congrats you're request is under Review.")
        else:
            st.error("Error: Amount can't be less than $1")

def free_user():
    username = st.session_state["username"]
    userID = st.session_state["userID"]
    complainee(username)
    # st.title("Free User Page")
    if st.session_state['page'] == 'home':
        homepage(username, userID)
    if st.session_state.get("logout") == True:
        add_logout(username)
        st.session_state["free_user"] = False
        st.session_state["username"] = None
        st.session_state["userID"] = None
        st.session_state["tokens"] = 0
        st.session_state["logout"] = False
        st.rerun()
    if st.session_state['page'] == 'paid_page':
        paid_page(username)
    elif st.session_state["page"] == "blacklist":
        submit_blacklist_request(st.session_state["username"])
 

# --------------------- Paid User Section --------------------- #
def collab(username, userID):
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
                    if st.button("Edit File", key=f"edit_{file_id}--{generate_random_id}"):
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
    
    filecomplaint(userID)

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

def complainee(username): 
    if 'responded_complaints' not in st.session_state:
        st.session_state.responded_complaints = set()

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
                   SELECT complaintID, complainAbout, reasonByComplainer
                   FROM complaints 
                   left outer join users
                   on complaints.complainAbout = users.ID
                   WHERE users.username = ? 
                   AND status = 0 
                   AND defenseByComplainee is NULL
                   """, (username,))
    
    result = cursor.fetchall()
    conn.close()

    if result:
        st.header("A complaint has been filed against you:")
        
        for rowid, user, reason in result:
            if rowid in st.session_state.responded_complaints:
                continue

            st.info(f"Complaint: {reason}")
            response_key = f"response_{rowid}"
            response = st.text_area(f"Enter your defense {user} (response):", height=250, key=response_key)

            if st.button(f"Submit response to complaint {rowid}", key=f"submit_{rowid}"):
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE complaints 
                    SET defenseByComplainee = ? 
                    WHERE complaintID = ?
                """, (response, rowid))
                conn.commit()
                conn.close()
                
                st.session_state.responded_complaints.add(rowid) 
                st.success(f"Your response to complaint {rowid} has been submitted.")
                st.rerun() 
                
def filecomplaint(userID):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT file_collaborations.collaborator_id, users.username 
        FROM file_collaborations 
        INNER JOIN users ON file_collaborations.collaborator_id = users.ID 
        WHERE file_collaborations.owner_id = (
            SELECT ID FROM users WHERE ID = ?
        )
    """, (userID,))
    
    collaborators = cursor.fetchall()
    conn.close()

    if collaborators:
        st.subheader("File a complaint against a collaborator:")
        collaborator_options = {name: cid for cid, name in collaborators}
        selected_username = st.selectbox("Choose collaborator:", list(collaborator_options.keys()))
        selected_id = collaborator_options[selected_username]

        prompt = st.text_area("Enter your reasoning:", height=150)

        if st.button("Submit") and prompt:
            complaint_id = generate_random_id()
            
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO complaints VALUES (?, ?, ?, ?, NULL, NULL, 0, NULL, NULL, 0)
            """, (complaint_id, userID, selected_id, prompt))
            
            conn.commit()
            conn.close()
            st.success("Complaint submitted successfully.")
    else:
        st.warning("You have no collaborators to file a complaint against.")

def token_purchase_modal(username):
    # modal = Modal("Pay Token", key="demo-modal", padding=20, max_width=600)
    if st.session_state['buy'] == True:
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
                    st.rerun() # reset the page with updated token balance
                else:
                    st.error("Please enter a valid amount.")

            # close out option to buy tokens
            if st.button("Close"):
                st.session_state["buy"] = False
                st.rerun()

def add_logout(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_logout_time = ? WHERE username = ?", (datetime.now(), username))
    conn.commit()
    conn.close()

def background_selector(username):
    st.markdown("### 🎨 Select Background Theme")

    # Apply text styling to selectbox
    st.markdown("""
        <style>
        div[data-baseweb="select"] * {
            color: black !important;
            background-color: white !important;
        }
        ul[data-testid="stSelectboxVirtualDropdown"] li div {
            color: black !important;
            background-color: white !important;
        }

        </style>
    """, unsafe_allow_html=True)

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM background")
    options = [row[0] for row in cursor.fetchall()]
    conn.close()

    selected = st.selectbox("Choose a theme:", options)

    if st.button("Save Theme"):
        st.session_state["background"] = selected
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET background = ? WHERE username = ?", (selected, username))
        conn.commit()
        conn.close()
        st.success("Background updated! Refreshing...")
        st.rerun()


def view_my_rejections(username):
    st.header("My LLM Rejections")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT rejection_id, original_text, corrected_text, reason, status, reviewed_at
        FROM llm_rejections
        WHERE username = ?
        ORDER BY reviewed_at DESC NULLS LAST
    """, (username,))
    
    results = cursor.fetchall()
    conn.close()

    if results:
        for rejection_id, original, corrected, reason, status, reviewed_at in results:
            with st.expander(f"Rejection ID: {rejection_id[:6]}... | Status: {status.upper()}"):
                st.subheader("Original Text")
                st.code(original, language="text")
                st.subheader("LLM Correction")
                st.markdown(corrected, unsafe_allow_html=True)
                st.subheader("Your Reason")
                st.info(reason)
                if reviewed_at:
                    st.caption(f"Reviewed at: {reviewed_at}")
    else:
        st.info("You haven't submitted any LLM rejection yet.")

def saved_files(userID):
    st.header("SAVED FILES:")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, owner_id, file_name, data, created_at, owner_name FROM files WHERE owner_id = ?", [userID]) 
    results = cursor.fetchall()
    conn.close()
    
    if results:
        for row in results:
            file_id, owner_id, file_name, data, created_at, owner_name = row 
            col1, col2 = st.columns([1, 2])
            with col1: 
                st.subheader(file_name)

            with col2:
                st.subheader(created_at)

            with st.expander(f"File: {file_name} | saved on: {created_at} | saved by {owner_name}"): 
                st.info(data)
    else:
        st.info("You have not saved any files.")


def paid_user():
    username = st.session_state["username"]
    userID = st.session_state["userID"]
    complainee(username)
    if st.session_state.get("logout") == True:
        add_logout(username)
        st.session_state["paid_users"] = False
        st.session_state["username"] = None
        st.session_state["userID"] = None
        st.session_state["tokens"] = 0
        st.session_state["logout"] = False
        st.session_state["page"] = None
        st.rerun()
   #tokens = st.session_state["tokens"]
    st.sidebar.write("Token Balance:", st.session_state["tokens"])
    if st.session_state.get("paid_users"):
        if st.session_state["buy"] == True:
            token_purchase_modal(username)
        if st.session_state["page"] == "home":
            homepage(username, userID)
        elif st.session_state["page"] == "blacklist":
            submit_blacklist_request(st.session_state["username"])
        elif st.session_state["page"] == "invitation":
            invitation(username)
        elif st.session_state["page"] == "invites":
            invites(username)
        elif st.session_state["page"] == "collab":
            collab(username, userID)
        elif st.session_state["page"] == "files_saved":
            saved_files(userID)
        elif st.session_state["page"] == "background_color":
            background_selector(username)
        elif st.session_state["page"] == "my_rejections":
            view_my_rejections(username)


# --------------------- Super User Section --------------------- #

# PAGES 
def super_home(): 
    conn = sqlite3.connect("users.db")
    cursor1 = conn.cursor()
    cursor1.execute("SELECT COUNT(word) FROM blacklist_requests WHERE status = 'PENDING'")
    pbkls_count = cursor1.fetchall()
    cursor2 = conn.cursor()
    cursor2.execute("SELECT COUNT(complaintID) FROM complaints WHERE status = 0")
    pcomp_count = cursor2.fetchall()
    cursor3 = conn.cursor()
    cursor3.execute("SELECT COUNT(applicationID) FROM pending_users WHERE status = 0")
    apacc_count = cursor3.fetchall()
    conn.close()

    
    st.text(f"Pending users to review: {apacc_count[0][0]}")
    st.text(f"Pending complaints to review: {pcomp_count[0][0]}")
    st.text(f"Pending Blacklist words to review: {pbkls_count[0][0]}")
    #### fetch counts of pending actions: 
    # - count: pending complaints to review! 
    # - count: pending accounts to approve! 
    # - count: pending blacklist words to approve! 
    # - completed task statistics (for each of the above)

def approval_page(): 
    # "activate" account is for free user approval/disaproval 
    st.header("Approval Page")
    
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
                        cursor.execute("UPDATE users SET account_approval = 1 WHERE ID = ?", (register_id,))
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

def accept_paid():    
    # "pending_user" are requests to upgrade free user account 
    st.header("Accept Upgrade")
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, applicationID, status, amount_paid FROM pending_users WHERE status = 0")
    results = cursor.fetchall()
    conn.close()

    if results:
        st.subheader("Users Awaiting Upgrade")
        for row in results:
            applicationID = row[1]
            with st.expander(f"User: {row[0]} | ID: {applicationID} | Status: Waiting Upgrade Approval"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Accept", key=f"accept_{applicationID}"):
                        conn = sqlite3.connect("users.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE pending_users SET status = 1 WHERE applicationID = ?", (applicationID,))
                        cursor.execute("UPDATE users SET paid = 1 WHERE username = ?", (row[0],))
                        conn.commit()
                        conn.close()
                        st.success(f"{row[0]} has been approved.")
                        registry_approval(row[0])
                        st.rerun()
                with col2:
                    if st.button("❌ Decline", key=f"decline_{applicationID}"):
                        conn = sqlite3.connect("users.db")
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM pending_users WHERE applicationID = ?", (applicationID,))
                        conn.commit()
                        conn.close()
                        st.success(f"{row[0]} has been rejected.")
                        st.rerun()
    else:
        st.info("No users waiting for approval.")



def complaints(): 
    username = st.session_state["username"]
    st.header("Complaints Log")

    complaints_log_mode = st.radio("Display Complaints:", ["Pending", "Resolved"], horizontal=True)
    # if view unresolved 
    if complaints_log_mode == "Pending":
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT complaintID, submittedBy, complainAbout, reasonByComplainer, defenseByComplainee, status FROM complaints WHERE status = ?", [0]) 
        results = cursor.fetchall()
        conn.close()

        if results:
            st.subheader("Pending Complaints")
            for row in results:
                complaintID, submittedBy, complainAbout, reasonByComplainer, defenseByComplainee, status = row # add [ reason, time_of ] columns 
                with st.expander(f"Submitted by {submittedBy} | Complaint for {complainAbout} | Status: {status}"): #  | Complain filed at: {complain time} | reason: {reason}"): 
                    ID = complaintID
                    st.subheader(ID)
                    prompt = st.number_input("tokens", min_value=1, max_value=50, key = f"token amount for: {complaintID}")
                    col1, col2 = st.columns(2) 
                    with col1: 
                        explanation = reasonByComplainer
                        st.info(explanation)

                    with col2: 
                        defense = defenseByComplainee
                        st.info(defense)
                    
                    col1, col2 = st.columns(2) 
                    with col2:
                        if st.button("Complainee", key=f"punish_{complainAbout}--for: {complaintID}"): # punish the person that the complain was filed against 
                            approved_Date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
                            conn = sqlite3.connect("users.db")
                            cursor = conn.cursor()
                            cursor.execute("UPDATE complaints SET status = ?, decision = ?, tokenChange = ?, reviewedBy = ?, resolvedAt = ? WHERE complaintID = ?", (1, "COMPLAINEE punished", prompt, username, approved_Date, complaintID))
                            cursor.execute("SELECT tokens FROM users WHERE ID = ?", (complainAbout,))
                            result = cursor.fetchone()
                            if result:
                                tokens = result[0]
                                token = int(tokens)
                                if token != 0:
                                    token = token - prompt
                                    cursor.execute("UPDATE users SET tokens = ? WHERE ID = ?", (token, complainAbout))
                                else: 
                                    cursor.execute("UPDATE users SET account_approval = 0 WHERE ID = ?", (complainAbout,))
                            conn.commit()
                            conn.close()
                            st.success(f"Complaint {complaintID} resolved, action taken against {complainAbout}")

                    with col1:
                        if st.button("Complainer",  key=f"punish_{submittedBy}--for: {complaintID}"): # punish the person who filed the complained 
                            approved_Date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
                            conn = sqlite3.connect("users.db")
                            cursor = conn.cursor()
                            cursor.execute("UPDATE complaints SET status = ?, decision = ?, tokenChange = ?, reviewedBy = ?, resolvedAt = ? WHERE complaintID = ?", (1, "COMPLAINER punished", prompt, username, approved_Date, complaintID))
                            cursor.execute("SELECT tokens FROM users WHERE ID = ?", (submittedBy,))
                            result = cursor.fetchone()
                            if result:
                                tokens = result[0]
                                token = int(tokens)
                                if token != 0:
                                    token = token - prompt
                                    cursor.execute("UPDATE users SET tokens = ? WHERE ID = ?", (token, submittedBy))
                                else: 
                                    cursor.execute("UPDATE users SET account_approval = 0 WHERE ID = ?", (submittedBy,))
                            conn.commit()
                            conn.close()
                            st.success(f"Complaint {complaintID} resolved, action taken against {submittedBy}")
        else:
            st.info("No Pending Complaints.")

    elif complaints_log_mode == "Resolved":
        ###################################################################################
        # if view resolved 
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT complaintID, submittedBy, complainAbout, reasonByComplainer, defenseByComplainee, tokenChange, decision, status FROM complaints WHERE status = ?", [1]) # view unresolved complaints 
        # db should also have a "reason for complaint" and a time of complaint, ie. [ reasoning | time_of ]
        results = cursor.fetchall()
        conn.close()

        if results:
            st.subheader("Resolved Complaints")
            for row in results:
                complaintID, submittedBy, complainAbout, reasonByComplainer, defenseByComplainee, tokenChange, decision, status = row # add [ reason, time_of ] columns 
                with st.expander(f"Submitted by {submittedBy} | Complaint for {complainAbout} | Status: {status}"): #  | Complain filed at: {complain time} | reason: {reason}"): 
                    ID = complaintID
                    st.subheader(ID)
                    col1, col2, col3 = st.columns(3) 
                    with col1: 
                        explanation = reasonByComplainer
                        st.info(f"COMPLAINER: {explanation}")

                    with col2: 
                        defense = defenseByComplainee
                        st.info(f"COMPLAINEE: {defense}")

                    with col3:
                        st.info(f"{decision} for {tokenChange} tokens")
        else:
            st.info("No Resolved Complaints.")

    else: 
        st.info("ERROR COMPLAINT MODE") #temp? 

    # buttons:
    # view  
    # - view incomplete complaints log : done 
    # - view completed* complaints log : 
    # manipulate 
    # - punish a user && mark as completed 
    # - undo past complaints? herm. maybe not. 

def blacklist(): 
    st.header("Edit Blacklist")

    #### CURRENT BLACKLIST — OPTIONS TO DELETE WORDS 
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM blacklisted_words ORDER BY word ASC") 
    results = cursor.fetchall()
    conn.close()

    with st.expander("Current Blacklist:", expanded=True):
        if results:
            for row in results:
                col1, col2 = st.columns([3, 1])
                word = row[0]
                with col1:
                    st.info(word) 
                with col2:
                    if st.button("❌ DELETE", key=f"delete_{word}"):
                        conn = sqlite3.connect("users.db")
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM blacklisted_words WHERE word = ?", [word])
                        conn.commit()
                        conn.close()
                        st.success(f"Deleted: {word}")
                        st.rerun()
        else:
            st.info("Blacklist is empty.")

    #### PENDING USER REQUESTS TO ADD WORDS TO BLACKLIST 
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT word, requestedBy FROM blacklist_requests WHERE status = 'PENDING' ORDER BY word ASC") 
    pending_requests = cursor.fetchall()
    conn.close()

    with st.expander("Pending Blacklist Requests from Users:", expanded=True):
        if pending_requests:
            for word, user in pending_requests:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.info(f"'{word}' requested by **{user}**")
                with col2:
                    if st.button("✅ Accept", key=f"accept_{word}"):
                        conn = sqlite3.connect("users.db")
                        cursor = conn.cursor()
                        cursor.execute("INSERT OR IGNORE INTO blacklisted_words (word) VALUES (?)", (word,))
                        cursor.execute("UPDATE blacklist_requests SET status = 'APPROVED' WHERE word = ?", (word,))
                        conn.commit()
                        conn.close()
                        st.success(f"'{word}' approved and added to blacklist.")
                        st.rerun()
                with col3:
                    if st.button("❌ Deny", key=f"deny_{word}"):
                        conn = sqlite3.connect("users.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE blacklist_requests SET status = 'DENIED' WHERE word = ?", (word,))
                        conn.commit()
                        conn.close()
                        st.warning(f"'{word}' was denied.")
                        st.rerun()
        else:
            st.info("No pending blacklist requests.")

    #### SUPERUSER MANUALLY ADDING NEW WORDS TO BLACKLIST 
    new_word = st.text_area("🆕 Manually add a new word to blacklist:", height=68, max_chars=255).lower() 
    if st.button("Add Word", key=f"manualadd_{new_word}") and new_word:
        if any(new_word == row[0] for row in results):
            st.warning("This word already exists in the blacklist.")
        else:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO blacklisted_words (word) VALUES (?);", [new_word])
            conn.commit()
            conn.close()
            st.success(f"Successfully added word: {new_word}")
            st.rerun()

# Rejection Review Panel
def llm_rejections_review(): # REQUIRES AN ADJUSTMENT TO THE DB TO RESOLVE 
    st.header("LLM Correction Rejections Review")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rejection_id, username, original_text, corrected_text, reason 
        FROM llm_rejections 
        WHERE status = 'pending'
    """)
    results = cursor.fetchall()
    conn.close()

    if results:
        for row in results:
            rejection_id, username, original, corrected, reason = row
            with st.expander(f"Rejection from {username} | ID: {rejection_id[:6]}..."):
                st.subheader("Original Text")
                st.code(original, language="text")
                st.subheader("LLM Correction")
                st.markdown(corrected, unsafe_allow_html=True)
                st.subheader("Reason for Rejection")
                st.info(reason)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Accept Rejection", key=f"accept_{rejection_id}"):
                        apply_llm_rejection_decision(rejection_id, username, penalty=1, decision="accepted")

                with col2:
                    if st.button("❌ Reject Rejection", key=f"reject_{rejection_id}"):
                        apply_llm_rejection_decision(rejection_id, username, penalty=5, decision="rejected")

    else:
        st.info("No pending rejections to review.")

def apply_llm_rejection_decision(rejection_id, username, penalty, decision):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    reviewed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE llm_rejections
        SET status = ?, reviewed_by = ?, penalty_applied = ?, reviewed_at = ?
        WHERE rejection_id = ?
    """, (decision, st.session_state["username"], penalty, reviewed_at, rejection_id))

    conn.commit()
    conn.close()

    # Now deduct tokens in users.db
    conn2 = sqlite3.connect("users.db")
    cursor2 = conn2.cursor()
    cursor2.execute("UPDATE users SET tokens = tokens - ? WHERE username = ?", (penalty, username))
    conn2.commit()
    conn2.close()

    st.success(f"Rejection marked as '{decision}'. {penalty} token(s) deducted from {username}.")
    st.rerun()

def super_user():
    username = st.session_state["username"]
    st.sidebar.write(f"Welcome, {username}!")

    st.title("Super User Page")
    if st.session_state["page"] == 'home':
        super_home()
    if st.session_state["page"] == 'approval':
        approval_page()
    if st.session_state["page"] == 'accept':
        accept_paid()
    if st.session_state["page"] == 'complaints':
        complaints()
    if st.session_state["page"] == 'blacklist':
        blacklist()
    if st.session_state["page"] == 'rejections':
        llm_rejections_review()
    if st.session_state.get("logout") == True:
        add_logout(username)
        st.session_state["super_users"] = False
        st.session_state["username"] = None
        st.session_state["userID"] = None
        st.session_state["tokens"] = 0
        st.session_state["logout"] = False
        st.rerun()


# FUNCTIONS 
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


def apply_theme():
    if st.session_state.get("paid_users"):
        st.markdown("""
            <style>
                /* Make menu item text black */
                .st-emotion-cache-6mv2k3 {
                    color: black !important;
                }

                /* Optional: hotkey labels (like "r" for Rerun) */
                .st-emotion-cache-rj14pv {
                    color: black !important;
                }

                /* Optional: make menu background white for full contrast */
                .stMainMenuPopover {
                    background-color: black !important;
                }
                .stMarkdown {
                    color: black !important;
                }
            </style>
        """, unsafe_allow_html=True)
        st.markdown("""
            <style>
                html, body, .stApp {
                    background: linear-gradient(to bottom right, #115e59, #155e75, #1e3a8a) !important;
                    margin: 0;
                    padding: 0;
                }

                header, .block-container {
                    background-color: transparent !important;
                }

                [data-testid="stSidebar"] {
                    background-color: rgba(255, 255, 255, 0.05) !important;
                }

                h1, h2, h3, h4, h5, h6, p, div, span, label {
                    color: white !important;
                }

                .stButton>button {
                    background-color: rgba(255, 255, 255, 0.1) !important;
                    color: white !important;
                    border-radius: 8px;
                }

                .stTextInput>div>div>input {
                    background-color: rgba(255, 255, 255, 0.1) !important;
                    color: white !important;
                }

                .stFileUploader > div {
                    color: black !important;
                }

                .stFileUploader span {
                    color: black !important;
                }
            </style>
        """, unsafe_allow_html=True)
        gradient = "linear-gradient(to bottom right, #ff758c, #ff7eb3)"

        try:
            if "background" in st.session_state and st.session_state["background"]:
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                cursor.execute("SELECT gradient FROM background WHERE name = ?", (st.session_state['background'],))
                result = cursor.fetchone()
                conn.close()

                if result and result[0]:
                    gradient = result[0]

        except Exception as e:
            st.error(f"Error applying background theme: {e}")

        #apply the theme
        st.markdown(f"""
            <style>
                html, body, .stApp {{
                    background: {gradient} !important;
                    background-attachment: fixed;
                    background-size: cover;
                    margin: 0;
                    padding: 0;
                }}

                
                
            </style>
        """, unsafe_allow_html=True)


# --------------------- Main Execution --------------------- #
navbar()
apply_theme()

# ensure first page the user sees is the home screen
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "username" not in st.session_state:
    login()
elif st.session_state.get("paid_users"):
    paid_user()
elif st.session_state.get("super_users"):
    super_user()
elif st.session_state.get("free_user"):
    free_user()
else:
    no_user()
    
