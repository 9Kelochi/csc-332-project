import sqlite3

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

    conn.commit()
    conn.close()
    print("All tables created for'token_terminator.db'.")

if __name__ == "__main__":
    create_tables()
