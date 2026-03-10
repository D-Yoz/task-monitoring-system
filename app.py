from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

tasks = [
    {
        "id": 1,
        "title": "Write report",
        "description": "Finish the draft for the project report.",
        "due": "2026-03-30",
        "priority": "Medium",
        "status": "In Progress",
        "assigned": "Daniel"
    },
    {
        "id": 2,
        "title": "Prepare slides",
        "description": "Create slides for the presentation.",
        "due": "2026-04-01",
        "priority": "Low",
        "status": "Not Started",
        "assigned": "John"
    },
    {
        "id": 3,
        "title": "Complete Research",
        "description": "Research different systems to use in the project.",
        "due": "2026-03-28",
        "priority": "High",
        "status": "Completed",
        "assigned": "Robert"
    }
]


def get_next_task_id():
    if not tasks:
        return 1
    return max(task["id"] for task in tasks) + 1


def find_task(task_id):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


@app.route("/")
def dashboard():
    selected_priority = request.args.get("priority", "")
    selected_status = request.args.get("status", "")

    filtered_tasks = tasks

    if selected_priority:
        filtered_tasks = [
            task for task in filtered_tasks
            if task["priority"] == selected_priority
        ]

    if selected_status:
        filtered_tasks = [
            task for task in filtered_tasks
            if task["status"] == selected_status
        ]

    return render_template(
        "dashboard.html",
        tasks=filtered_tasks,
        selected_priority=selected_priority,
        selected_status=selected_status
    )


@app.route("/new-task", methods=["GET", "POST"])
def new_task():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due = request.form.get("due", "").strip()
        priority = request.form.get("priority", "").strip()
        status = request.form.get("status", "").strip()
        assigned = request.form.get("assigned", "").strip()

        if title and due and priority and status and assigned:
            new_id = get_next_task_id()

            tasks.append({
                "id": new_id,
                "title": title,
                "description": description,
                "due": due,
                "priority": priority,
                "status": status,
                "assigned": assigned
            })

        return redirect(url_for("dashboard"))

    return render_template("new_task.html")


@app.route("/task/<int:task_id>")
def view_task(task_id):
    task = find_task(task_id)
    if task is None:
        return "Task not found", 404

    return render_template("view_task.html", task=task)


@app.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    task = find_task(task_id)
    if task is None:
        return "Task not found", 404

    if request.method == "POST":
        task["title"] = request.form.get("title", "").strip()
        task["description"] = request.form.get("description", "").strip()
        task["due"] = request.form.get("due", "").strip()
        task["priority"] = request.form.get("priority", "").strip()
        task["status"] = request.form.get("status", "").strip()
        task["assigned"] = request.form.get("assigned", "").strip()

        return redirect(url_for("view_task", task_id=task_id))

    return render_template("edit_task.html", task=task)


@app.route("/task/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    task = find_task(task_id)
    if task is not None:
        tasks.remove(task)

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True, port=5050)
