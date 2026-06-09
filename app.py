from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = "123456789"
UPLOAD_FOLDER = "static/avatars"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

VOICE_FOLDER = "static/voices"
app.config["VOICE_FOLDER"] = VOICE_FOLDER

IMAGE_FOLDER = "static/images"
app.config["IMAGE_FOLDER"] = IMAGE_FOLDER

os.makedirs("static/images", exist_ok=True)
os.makedirs("static/voices", exist_ok=True)
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

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT 'default.png'"
        )
    except:
        pass
    
    try:
        cursor.execute(
        "ALTER TABLE messages ADD COLUMN image TEXT"
    )
    except:
        pass
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    try:
        cursor.execute(
        "ALTER TABLE messages ADD COLUMN voice TEXT"
    )
    except:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS private_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

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
        return redirect("/profile")

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

        if user and user[2] == password:
            
            session["username"] = username
            
            print("LOGIN OK:", username)
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO online_users
                (username, last_seen)
                VALUES (?, ?)
                """,
                (
                    username,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            
            conn.commit()
            print("ONLINE SAVED")
            conn.close()

            return redirect("/chat")

        conn.close()

        return "Неверный логин или пароль"

    return render_template("login.html")


@app.route("/users")
def users():

    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            users.username,
            online_users.username
        FROM users
        LEFT JOIN online_users
        ON users.username = online_users.username
        ORDER BY users.username
    """)

    users = cursor.fetchall()

    conn.close()

    return render_template(
        "users.html",
        users=users
    )
@app.route("/upload_voice", methods=["POST"])
def upload_voice():

    if "username" not in session:
        return "error"

    file = request.files.get("voice")

    if not file:
        return "error"

    filename = secure_filename(
        f"{session['username']}_{datetime.now().timestamp()}.webm"
    )

    filepath = os.path.join(
        app.config["VOICE_FOLDER"],
        filename
    )

    file.save(filepath)

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    current_time = datetime.now().strftime("%H:%M")

    cursor.execute(
        """
        INSERT INTO messages
        (username, text, created_at, voice)
        VALUES (?, ?, ?, ?)
        """,
        (
            session["username"],
            "",
            current_time,
            filename
        )
    )

    conn.commit()
    conn.close()

    return "ok"

@app.route("/upload_image", methods=["POST"])
def upload_image():

    if "username" not in session:
        return "error"

    file = request.files.get("image")

    if not file:
        return "error"

    filename = secure_filename(
        f"{session['username']}_{datetime.now().timestamp()}_{file.filename}"
    )

    filepath = os.path.join(
        app.config["IMAGE_FOLDER"],
        filename
    )

    file.save(filepath)

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    current_time = datetime.now().strftime("%H:%M")

    cursor.execute(
        """
        INSERT INTO messages
        (username, text, created_at, image)
        VALUES (?, ?, ?, ?)
        """,
        (
            session["username"],
            "",
            current_time,
            filename
        )
    )

    conn.commit()
    conn.close()

    return "ok"

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
                """
                INSERT INTO messages
                (username, text, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    session["username"],
                    text,
                    current_time
                )
            )

            conn.commit()

            return redirect("/chat")

    cursor.execute(
        """
        SELECT username, text, created_at
        FROM messages
        ORDER BY id
        """
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

    cursor.execute("""
        SELECT username, text, created_at, voice, image
        FROM messages
        ORDER BY id
    """)

    messages = cursor.fetchall()

    conn.close()

    result = ""

    for username, text, created_at, voice, image in messages:

        side = "right" if username == session["username"] else "left"

        if image:

            result += f"""
            <div class="message {side}">
                <div class="author">
                    {username} • {created_at}
                </div>

                <img
                    src="/static/images/{image}"
                    style="
                        max-width:250px;
                        border-radius:12px;
                        margin-top:5px;
                    "
                >

            </div>
            """

        elif voice:

            result += f"""
            <div class="message {side}">
                <div class="author">
                    {username} • {created_at}
                </div>

                <audio controls>
                    <source src="/static/voices/{voice}" type="audio/webm">
                </audio>

            </div>
            """

        else:

            result += f"""
            <div class="message {side}">
                <div class="author">
                    {username} • {created_at}
                </div>

                <div>
                    {text}
                </div>

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

    cursor.execute(
        "SELECT username, password FROM users"
    )

    users = cursor.fetchall()

    conn.close()

    return str(users)


@app.route("/allprivate")
def allprivate():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT sender, receiver, text
        FROM private_messages
        """
    )

    data = cursor.fetchall()

    conn.close()

    return str(data)

@app.route("/online")
def online():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM online_users"
    )

    data = cursor.fetchall()

    conn.close()

    return str(data)

@app.route("/whoami")
def whoami():

    return session.get(
        "username",
        "not logged in"
    )


@app.route("/test")
def test():

    return "Работает"


@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        file = request.files.get("avatar")

        if file and file.filename:

            filename = secure_filename(
                session["username"] + "_" + file.filename
            )

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            file.save(filepath)

            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE users SET avatar=? WHERE username=?",
                (filename, session["username"])
            )

            conn.commit()
            conn.close()

            return redirect("/profile")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT avatar FROM users WHERE username=?",
        (session["username"],)
    )

    result = cursor.fetchone()

    avatar = "default.png"

    if result and result[0]:
        avatar = result[0]

    conn.close()

    return render_template(
        "profile.html",
        username=session["username"],
        avatar=avatar
    )


@app.route("/pulse")
def pulse():

    return """
    <h1 style="background:black;color:white;padding:40px;">
    PULSE WORKS
    </h1>
    """


@app.route("/logout")
def logout():

    if "username" in session:

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM online_users
            WHERE username=?
            """,
            (session["username"],)
        )

        conn.commit()
        conn.close()

    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)