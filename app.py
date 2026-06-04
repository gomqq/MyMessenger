from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "123456789"


def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            conn.commit()

            return redirect("/login")

        except Exception as e:
            return f"Ошибка: {e}"

        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["username"] = username
            return redirect("/chat")

        return "Неверный логин или пароль"

    return render_template("login.html")

@app.route("/users")
def users():

    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username FROM users ORDER BY username"
    )

    users = cursor.fetchall()

    conn.close()

    return render_template(
        "users.html",
        users=users
    )
@app.route("/chat", methods=["GET", "POST"])
def chat():

    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if request.method == "POST":

        text = request.form["message"]

        if text.strip():

            current_time = datetime.now().strftime("%H:%M")

            cursor.execute(
                "INSERT INTO messages (username, text, created_at) VALUES (?, ?, ?)",
                (session["username"], text, current_time)
            )

            conn.commit()

            conn.close()

            return redirect("/chat")

    cursor.execute(
        "SELECT username, text, created_at FROM messages ORDER BY id"
    )

    messages = cursor.fetchall()

    conn.close()

    return render_template(
        "chat.html",
        messages=messages,
        username=session["username"]
    )
@app.route("/messages")
def get_messages():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username, text, created_at FROM messages ORDER BY id"
    )

    messages = cursor.fetchall()

    conn.close()

    result = ""

    for username, text, created_at in messages:

        result += f"""
        <div class="message">
            <div class="author">
                {username} • {created_at}
            </div>

            <div class="text">
                {text}
            </div>
        </div>
        """

    return result

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)