from flask import Flask, render_template, request, redirect, url_for, session
from database import get_connection
from datetime import date

app = Flask(__name__)
app.secret_key = "task-monitoring-demo-secret-key"


def get_logged_in_user():
    user_id = session.get("user_id")
    if not user_id:
        return None

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


def require_login():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return None


def get_task_by_id(task_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT tasks.*, users.name AS assigned
        FROM tasks
        JOIN users ON tasks.assigned_user_id = users.id
        WHERE tasks.id = %s
    """
    cursor.execute(query, (task_id,))
    task = cursor.fetchone()

    cursor.close()
    conn.close()

    return task


def get_users_for_dropdown():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT name FROM users ORDER BY name")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return users


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            (username, password)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = user["role"]
            return redirect(url_for("dashboard"))

        error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def dashboard():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    current_user = get_logged_in_user()

    selected_priority = request.args.get("priority", "")
    selected_status = request.args.get("status", "")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT tasks.*, users.name AS assigned
        FROM tasks
        JOIN users ON tasks.assigned_user_id = users.id
        WHERE 1=1
    """
    params = []

    if current_user["role"] == "regular":
        query += " AND tasks.assigned_user_id = %s"
        params.append(current_user["id"])

    if selected_priority:
        query += " AND tasks.priority = %s"
        params.append(selected_priority)

    if selected_status:
        query += " AND tasks.status = %s"
        params.append(selected_status)

    cursor.execute(query, params)
    tasks = cursor.fetchall()

    today = date.today()
    overdue_count = 0

    for task in tasks:
        task["is_overdue"] = (
            task["due"] < today and task["status"] != "Completed"
        )
        if task["is_overdue"]:
            overdue_count += 1

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        tasks=tasks,
        current_user=current_user,
        selected_priority=selected_priority,
        selected_status=selected_status,
        overdue_count=overdue_count
    )


@app.route("/new-task", methods=["GET", "POST"])
def new_task():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due = request.form.get("due", "").strip()
        priority = request.form.get("priority", "").strip()
        status = request.form.get("status", "").strip()
        assigned = request.form.get("assigned", "").strip()

        if title and due and priority and status and assigned:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM users WHERE name = %s", (assigned,))
            user = cursor.fetchone()

            if user:
                assigned_user_id = user[0]

                query = """
                    INSERT INTO tasks
                    (title, description, due, priority, status, assigned_user_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(
                    query,
                    (title, description, due, priority, status, assigned_user_id)
                )
                conn.commit()

            cursor.close()
            conn.close()

        return redirect(url_for("dashboard"))

    users = get_users_for_dropdown()
    return render_template("new_task.html", users=users)


@app.route("/task/<int:task_id>")
def view_task(task_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    task = get_task_by_id(task_id)

    if task is None:
        return "Task not found", 404

    task["is_overdue"] = (
        task["due"] < date.today() and task["status"] != "Completed"
    )

    return render_template("view_task.html", task=task)


@app.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    task = get_task_by_id(task_id)

    if task is None:
        return "Task not found", 404

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due = request.form.get("due", "").strip()
        priority = request.form.get("priority", "").strip()
        status = request.form.get("status", "").strip()
        assigned = request.form.get("assigned", "").strip()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE name = %s", (assigned,))
        user = cursor.fetchone()

        if user:
            assigned_user_id = user[0]

            query = """
                UPDATE tasks
                SET title = %s,
                    description = %s,
                    due = %s,
                    priority = %s,
                    status = %s,
                    assigned_user_id = %s
                WHERE id = %s
            """
            cursor.execute(
                query,
                (title, description, due, priority, status, assigned_user_id, task_id)
            )
            conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("view_task", task_id=task_id))

    users = get_users_for_dropdown()
    return render_template("edit_task.html", task=task, users=users)


@app.route("/task/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True, port=5050)