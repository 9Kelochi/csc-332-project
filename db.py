import sqlite3

def create_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            last_logout_time INTEGER NOT NULL, 
            tokens INTEGER NOT NULL,
            accountApproved INTEGER NOT NULL,
            userType TEXT NOT NULL,
            numCorrections TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# create_db()

def insert_user(username, password, last_logout_time, tokens, accountApproved, userType, numCorrections):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO users (username, password, last_logout_time, tokens, accountApproved, userType, numCorrections)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, password, last_logout_time, tokens, accountApproved, userType, numCorrections))

    conn.commit()
    conn.close()

# sample users
    
# Kel,3917,1712347200,120.0
# fen,2917,1712347200,123.0
# Lun,3344,17123
create_db()
insert_user("Kel",3917,1712347200,120.0, True, "Paid", 50)
insert_user("fen",2917,1712347200,123.0, True, "Paid", 17)
insert_user("Lun",2917,1712347200,123.0, True, "Paid", 1)


