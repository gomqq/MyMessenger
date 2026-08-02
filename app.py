from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import random
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.secret_key = "pulse_secret_key"


UPLOAD_FOLDER = "static/avatars"
IMAGE_FOLDER = "static/images"
VOICE_FOLDER = "static/voices"


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["IMAGE_FOLDER"] = IMAGE_FOLDER
app.config["VOICE_FOLDER"] = VOICE_FOLDER


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(VOICE_FOLDER, exist_ok=True)
def init_db():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()


    # Пользователи
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE NOT NULL,

        phone TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        avatar TEXT DEFAULT 'default.png',

        created_at TEXT NOT NULL

    )
    """)


    # Коды подтверждения телефона
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verification_codes (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        phone TEXT NOT NULL,

        code TEXT NOT NULL,

        created_at TEXT NOT NULL

    )
    """)


    # Сообщения общего чата
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT NOT NULL,

        text TEXT NOT NULL,

        created_at TEXT NOT NULL

    )
    """)


    # Личные сообщения
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS private_messages (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        sender TEXT NOT NULL,

        receiver TEXT NOT NULL,

        text TEXT NOT NULL,

        created_at TEXT NOT NULL

    )
    """)


    # Онлайн пользователи
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS online_users (

        username TEXT PRIMARY KEY,

        last_seen TEXT NOT NULL

    )
    """)


    conn.commit()
    conn.close()


init_db()
@app.route("/")
def home():

    if "username" in session:
        return redirect("/chat")

    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        phone = request.form["phone"].strip()
        password = request.form["password"]

        code = str(random.randint(100000, 999999))
        
        print("SMS код для", phone, ":", code)


        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()


        cursor.execute(
            """
            INSERT INTO verification_codes
            (phone, code, created_at)
            VALUES (?, ?, ?)
            """,
            (
                phone,
                code,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )


        conn.commit()
        conn.close()


        session["register_username"] = username
        session["register_phone"] = phone
        session["register_password"] = password


        return redirect("/verify")


    return render_template("register.html")

@app.route("/verify", methods=["GET","POST"])
def verify():

    if request.method == "POST":

        code = request.form["code"]


        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT * FROM verification_codes
            WHERE phone=? AND code=?
            """,
            (
                session["register_phone"],
                code
            )
        )


        result = cursor.fetchone()


        if result:

            cursor.execute(
                """
                INSERT INTO users
                (username, phone, password, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session["register_username"],
                    session["register_phone"],
                    generate_password_hash(
                        session["register_password"]
                    ),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )


            conn.commit()
            conn.close()


            session.pop("register_username")
            session.pop("register_phone")
            session.pop("register_password")


            return redirect("/login")


        conn.close()

        return "Неверный код"


    return render_template("verify.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        login_data = request.form["username"].strip()
        password = request.form["password"]


        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT * FROM users
            WHERE username=? OR phone=?
            """,
            (login_data, login_data)
        )


        user = cursor.fetchone()


        if user and check_password_hash(user[3], password):

            session["username"] = user[1]


            cursor.execute(
                """
                INSERT OR REPLACE INTO online_users
                (username, last_seen)
                VALUES (?, ?)
                """,
                (
                    user[1],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )


            conn.commit()
            conn.close()


            return redirect("/chat")


        conn.close()

        return "Неверный логин или пароль"


    return render_template("login.html")
@app.route("/chat")
def chat():

    if "username" not in session:
        return redirect("/login")


    return render_template(
        "chat.html",
        username=session["username"]
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

@app.route("/messages")
def messages():

    if "username" not in session:
        return redirect("/login")


    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT username, text, created_at
        FROM messages
        ORDER BY id DESC
        """
    )


    messages = cursor.fetchall()

    conn.close()


    return render_template(
        "chat.html",
        username=session["username"],
        messages=messages
    )



@app.route("/send_message", methods=["POST"])
def send_message():

    if "username" not in session:
        return redirect("/login")


    text = request.form["text"].strip()


    if text:

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()


        cursor.execute(
            """
            INSERT INTO messages
            (username, text, created_at)
            VALUES (?, ?, ?)
            """,
            (
                session["username"],
                text,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )


        conn.commit()
        conn.close()


    return redirect("/chat")

@app.route("/send_private_message/<receiver>", methods=["POST"])
def send_private_message(receiver):

    if "username" not in session:
        return redirect("/login")

    text = request.form["message"].strip()

    if text:

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO private_messages
            (sender, receiver, text, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                session["username"],
                receiver,
                text,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()
        conn.close()

    return redirect(f"/dialog/{receiver}")

@app.route("/api/messages")
def api_messages():

    if "username" not in session:
        return {"error":"not logged"}, 401


    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT username, text, created_at
        FROM messages
        ORDER BY id ASC
        """
    )


    data = cursor.fetchall()

    conn.close()


    return {
        "messages": [
            {
                "username": row[0],
                "text": row[1],
                "created_at": row[2]
            }
            for row in data
        ]
    }

@app.route("/users")
def users():

    if "username" not in session:
        return redirect("/login")


    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT username, avatar
        FROM users
        WHERE username != ?
        """,
        (session["username"],)
    )


    users = cursor.fetchall()

    conn.close()


    return render_template(
        "users.html",
        users=users
    )

@app.route("/dialog/<username>")
def dialog(username):

    if "username" not in session:
        return redirect("/login")


    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT sender, receiver, text, created_at
        FROM private_messages
        WHERE 
        (sender=? AND receiver=?)
        OR
        (sender=? AND receiver=?)
        ORDER BY id ASC
        """,
        (
            session["username"],
            username,
            username,
            session["username"]
        )
    )


    messages = cursor.fetchall()

    conn.close()


    return render_template(
        "dialog.html",
        username=username,
        messages=messages
    )



if __name__ == "__main__":

    app.run(debug=True)