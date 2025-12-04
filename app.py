from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
import matplotlib
matplotlib.use('Agg')  # Needed to render graphs without a display
import matplotlib.pyplot as plt
from io import BytesIO
from flask import Response
from datetime import datetime

# ---------------------------------------
# Create Flask App
# ---------------------------------------
app = Flask(__name__)
app.secret_key = "PROJECT_SECRET_KEY"

# ---------------------------------------
# Database Connection
# ---------------------------------------
def get_db():
    conn = sqlite3.connect("database/health.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------------------
# Context Processor for Current Year
# ---------------------------------------
@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}

# ---------------------------------------
# Registration Route
# ---------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    success = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        age = request.form.get("age")
        gender = request.form.get("gender")

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, password, age, gender)
                VALUES (?, ?, ?, ?)
            """, (username, hashed_password, age, gender))
            conn.commit()
            conn.close()
            success = "Registration successful! Please login."
            return render_template("register.html", success=success)
        except sqlite3.IntegrityError:
            conn.close()
            error = "Username already exists!"

    return render_template("register.html", error=error)

# ---------------------------------------
# Login Route
# ---------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user is None:
            error = "User not found."
        elif user["password"] != hashed_password:
            error = "Incorrect password."
        else:
            # Login success
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            return redirect("/dashboard")

    return render_template("login.html", error=error)

# ---------------------------------------
# Logout Route
# ---------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------------------------------
# Home Route
# ---------------------------------------
@app.route("/")
def home():
    return redirect("/login")

# ---------------------------------------
# Dashboard Route
# ---------------------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM health_data
        WHERE user_id = ?
        ORDER BY date ASC
    """, (session["user_id"],))
    data = cursor.fetchall()
    conn.close()

    return render_template("dashboard.html", username=session["username"], data=data)

# ---------------------------------------
# Add Health Data Route
# ---------------------------------------
@app.route("/add-data", methods=["GET", "POST"])
def add_data():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        date = request.form["date"]
        weight = float(request.form.get("weight")) if request.form.get("weight") else None
        steps = int(request.form.get("steps")) if request.form.get("steps") else None
        calories = int(request.form.get("calories")) if request.form.get("calories") else None

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO health_data (user_id, date, weight, steps, calories_burned)
            VALUES (?, ?, ?, ?, ?)
        """, (session["user_id"], date, weight, steps, calories))
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("add_data.html")

# ---------------------------------------
# Edit Health Data Route
# ---------------------------------------
@app.route("/edit/<int:data_id>", methods=["GET", "POST"])
def edit_entry(data_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        date = request.form["date"]
        weight = float(request.form.get("weight")) if request.form.get("weight") else None
        steps = int(request.form.get("steps")) if request.form.get("steps") else None
        calories = int(request.form.get("calories")) if request.form.get("calories") else None

        cursor.execute("""
            UPDATE health_data
            SET date = ?, weight = ?, steps = ?, calories_burned = ?
            WHERE data_id = ? AND user_id = ?
        """, (date, weight, steps, calories, data_id, session["user_id"]))
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    cursor.execute("""
        SELECT * FROM health_data
        WHERE data_id = ? AND user_id = ?
    """, (data_id, session["user_id"]))
    entry = cursor.fetchone()
    conn.close()

    if entry is None:
        return "Entry not found or unauthorized", 404

    return render_template("edit_data.html", entry=entry)

# ---------------------------------------
# Delete Health Data Route
# ---------------------------------------
@app.route("/delete/<int:data_id>")
def delete_entry(data_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM health_data
        WHERE data_id = ? AND user_id = ?
    """, (data_id, session["user_id"]))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------------------------------
# Weight Graph Route
# ---------------------------------------
@app.route("/weight-graph")
def weight_graph():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, weight FROM health_data
        WHERE user_id = ? AND weight IS NOT NULL
        ORDER BY date ASC
    """, (session["user_id"],))
    rows = cursor.fetchall()
    conn.close()

    fig, ax = plt.subplots()
    if not rows:
        ax.text(0.5, 0.5, "No weight data available", fontsize=14, ha='center')
        ax.axis('off')
    else:
        dates = [r["date"] for r in rows]
        weights = [float(r["weight"]) for r in rows]
        ax.plot(dates, weights, marker='o')
        ax.set_title("Weight Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Weight (kg)")
        plt.xticks(rotation=45)
        plt.grid(True)

    png_image = BytesIO()
    plt.tight_layout()
    fig.savefig(png_image, format="png")
    plt.close(fig)
    png_image.seek(0)

    return Response(png_image.getvalue(), mimetype='image/png')

# ---------------------------------------
# Run the App
# ---------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
