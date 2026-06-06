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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS private_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
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
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        print("Введено:", username, password)
        print("Из базы:", user)

        if user and user[2] == password:
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

            return redirect("/chat")

    cursor.execute(
        "SELECT username, text, created_at FROM messages ORDER BY id"
    )
    messages = cursor.fetchall()

    cursor.execute(
        "SELECT username FROM users ORDER BY username"
    )
    users = cursor.fetchall()

    conn.close()

    return render_template(
        "chat.html",
        messages=messages,
        username=session["username"],
        users=users
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

        if username == session["username"]:

            result += f"""
            <div class="my-message">
                <div class="author">Вы</div>
                <div>{text}</div>
                <div class="time">{created_at}</div>
            </div>
            """

        else:

            result += f"""
            <div class="other-message">
                <div class="author">{username}</div>
                <div>{text}</div>
                <div class="time">{created_at}</div>
            </div>
            """

    return result

@app.route("/dialog/<username>", methods=["GET", "POST"])
def dialog(username):

    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if request.method == "POST":

        text = request.form["message"]

        if text.strip():

            current_time = datetime.now().strftime("%H:%M")

            cursor.execute(
                """
                INSERT INTO private_messages
                (sender, receiver, text, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session["username"],
                    username,
                    text,
                    current_time
                )
            )

            conn.commit()
            print(
    "Сохранено:",
    session["username"],
    username,
    text
)

    cursor.execute(
        """
        SELECT sender, text, created_at
        FROM private_messages
        WHERE
            (sender=? AND receiver=?)
            OR
            (sender=? AND receiver=?)
        ORDER BY id
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


@app.route("/dialog_messages/<username>")
def dialog_messages(username):

    if "username" not in session:
        return ""

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT sender, text, created_at
        FROM private_messages
        WHERE
            (sender=? AND receiver=?)
            OR
            (sender=? AND receiver=?)
        ORDER BY id
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

    result = ""

    for sender, text, created_at in messages:

        if sender == session["username"]:

            result += f"""
            <div class="my-message">
                <div class="author">Вы</div>
                <div>{text}</div>
                <div class="time">{created_at}</div>
            </div>
            """

        else:

            result += f"""
            <div class="other-message">
                <div class="author">{sender}</div>
                <div>{text}</div>
                <div class="time">{created_at}</div>
            </div>
            """

    return result

@app.route("/allusers")
def allusers():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username, password FROM users")

    users = cursor.fetchall()

    conn.close()

    return str(users)
@app.route("/allprivate")
def allprivate():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sender, receiver, text
        FROM private_messages
    """)

    data = cursor.fetchall()

    conn.close()

    return str(data)
@app.route("/whoami")
def whoami():
    return session.get("username", "not logged in")
@app.route("/test")
def test():
    return "Работает"

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")



@app.route("/pulse")
def pulse():

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
        "pulse.html",
        users=users,
        username=session["username"]
    )


if __name__ == "__main__":
    app.run(debug=True)