import json
import os
import re

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "tasks.json")
PRIORITIES = ("high", "medium", "low")
PRIORITY_ORDER = {p: i for i, p in enumerate(PRIORITIES)}


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def next_id(tasks):
    return max((t["id"] for t in tasks), default=0) + 1


@app.route("/")
def index():
    tasks = load_tasks()
    query = request.args.get("q", "").strip()
    filter_priority = request.args.get("priority", "")
    sort = request.args.get("sort", "")

    if query:
        tasks = [t for t in tasks if query.lower() in t["title"].lower()]
    if filter_priority in PRIORITIES:
        tasks = [t for t in tasks if t.get("priority", "medium") == filter_priority]
    if sort == "priority":
        tasks = sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.get("priority", "medium"), 1))

    return render_template(
        "index.html",
        tasks=tasks,
        query=query,
        filter_priority=filter_priority,
        sort=sort,
        priorities=PRIORITIES,
    )


@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    due_date = request.form.get("due_date", "").strip() or None
    priority = request.form.get("priority", "medium")
    if priority not in PRIORITIES:
        priority = "medium"
    if due_date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", due_date):
        due_date = None
    if title:
        tasks = load_tasks()
        tasks.append({
            "id": next_id(tasks),
            "title": title,
            "done": False,
            "due_date": due_date,
            "priority": priority,
        })
        save_tasks(tasks)
    return redirect(url_for("index"))


@app.route("/done/<int:task_id>", methods=["POST"])
def done(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            break
    save_tasks(tasks)
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
