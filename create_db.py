import sqlite3
import csv

# this function will set up the core tables we need for our database
def create_tables(db_name="token_terminator.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            userType TEXT CHECK(userType IN ('free', 'paid', 'super')),
            tokensUsed INTEGER DEFAULT 0,
            tokensAvailable INTEGER DEFAULT 0,
            numCorrections INTEGER DEFAULT 0,
            lockoutUntil DATETIME
        );
    """)

    # pending users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_users (
            applicationID TEXT PRIMARY KEY,
            username TEXT UNIQUE REFERENCES users(username),
            userType TEXT CHECK(userType IN ('paid')),
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending'
        );
    """)

    # documents (text files owned by the user)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            documentID TEXT PRIMARY KEY,
            owner TEXT REFERENCES users(username),
            textContent TEXT
        );
    """)

    # owners / editors on a document
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_collaborators (
            documentID TEXT REFERENCES documents(documentID),
            collaborator TEXT REFERENCES users(username),
            status TEXT CHECK(status IN ('pending', 'accepted', 'rejected')),
            PRIMARY KEY (documentID, collaborator)
        );
    """)

    # blacklist approval table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklist_requests (
            word TEXT PRIMARY KEY,
            requestedBy TEXT REFERENCES users(username),
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending'
        );
    """)

    # approved blacklisted words
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklisted_words (
            word TEXT PRIMARY KEY
        );
    """)

    # transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transactionID TEXT PRIMARY KEY,
            username TEXT REFERENCES users(username),
            type TEXT,
            tokenAmount INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # corrections table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS corrections (
            correctionID INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT REFERENCES users(username),
            documentID TEXT REFERENCES documents(documentID),
            method TEXT CHECK(method IN ('LLM', 'self')),
            tokenCost INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # accepted words table (user's vocabulary)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accepted_words (
            username TEXT REFERENCES users(username),
            word TEXT,
            PRIMARY KEY (username, word)
        );
    """)

    # complaints table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaintID TEXT PRIMARY KEY,
            submittedBy TEXT REFERENCES users(username),
            complainAbout TEXT REFERENCES users(username),
            status TEXT CHECK(status IN ('pending', 'resolved')),
            decision TEXT CHECK(decision IN ('punish_complainer', 'punish_target')),
            tokenChange INTEGER,
            reviewedBy TEXT REFERENCES users(username),
            resolvedAt DATETIME
        );
    """)

    # user-submitted rejection of LLM correction
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_rejections (
            rejection_id TEXT PRIMARY KEY,
            username TEXT REFERENCES users(username),
            original_text TEXT,
            corrected_text TEXT,
            reason TEXT,
            status TEXT CHECK(status IN ('pending', 'accepted', 'rejected')) DEFAULT 'pending',
            reviewed_by TEXT,
            penalty_applied INTEGER DEFAULT 0,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            reviewed_at DATETIME
        );
    """)
         
    conn.commit()
    conn.close()
    print("All tables created for'token_terminator.db'.")

def create_blacklist_table():
    # connect to users db
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # create blacklisted words table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blacklisted_words (
            word TEXT PRIMARY KEY
        )
    ''')

    # read words from csv file
    with open('blacklisted_words.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        words = [(row[0].strip(),) for row in reader if row]  # Clean and format each word as a tuple

    # add them to blacklisted_words
    cursor.executemany('''
        INSERT OR IGNORE INTO blacklisted_words (word) VALUES (?)
    ''', words)

    # close connection
    conn.commit()
    conn.close()


def populate_super_admin():
    # connect to users db
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # insert default super admin user
    cursor.execute('''
        INSERT INTO super_users (username, password) VALUES (?, ?)
    ''', ('admin', 'admin'))

    conn.commit()
    conn.close()


def user_dictionary_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_dictionary (
            word TEXT NOT NULL,
            owner TEXT NOT NULL,
            PRIMARY KEY (word, owner)
        )
    ''')

    conn.commit()
    conn.close()

def populate_user_dictionary_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    sample_data = [
        ("hee hee hee haw", "Kel"),
        ("Lol", "Kel"),
        ("Naurrr", "fen")
    ]
    
    for word, owner in sample_data:
        try:
            cursor.execute("INSERT OR IGNORE INTO user_dictionary (word, owner) VALUES (?, ?)", (word, owner))
        except sqlite3.IntegrityError:
            pass  # skip duplicates

    conn.commit()
    conn.close()

def delete_row():
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM user_dictionary WHERE word='hee hee hee haw';")

    conn.commit()
    conn.close()
    

if __name__ == "__main__":
    # create_tables()
    # create_blacklist_table()
    # populate_super_admin()
    # user_dictionary_table()
    # populate_user_dictionary_table()
    pass
