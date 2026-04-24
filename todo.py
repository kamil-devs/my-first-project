import json
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(__file__), "tasks.json")


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


def cmd_list(tasks):
    if not tasks:
        print("No tasks yet. Add one with: add <task>")
        return
    for t in tasks:
        status = "x" if t["done"] else " "
        print(f"  [{status}] {t['id']}. {t['title']}")


def cmd_add(tasks, title):
    title = title.strip()
    if not title:
        print("Error: task title cannot be empty.")
        return
    task = {"id": next_id(tasks), "title": title, "done": False}
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added: {task['id']}. {title}")


def cmd_done(tasks, task_id):
    for t in tasks:
        if t["id"] == task_id:
            if t["done"]:
                print(f"Task {task_id} is already done.")
            else:
                t["done"] = True
                save_tasks(tasks)
                print(f"Marked done: {t['title']}")
            return
    print(f"Error: no task with id {task_id}.")


def cmd_delete(tasks, task_id):
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            removed = tasks.pop(i)
            save_tasks(tasks)
            print(f"Deleted: {removed['title']}")
            return
    print(f"Error: no task with id {task_id}.")


HELP = """
Commands:
  list              Show all tasks
  add <title>       Add a new task
  done <id>         Mark a task as done
  delete <id>       Delete a task
  help              Show this message
  quit              Exit
"""


def parse_id(token):
    try:
        return int(token)
    except (ValueError, TypeError):
        return None


def run_interactive():
    print("To-Do App  (type 'help' for commands)")
    tasks = load_tasks()
    cmd_list(tasks)

    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        parts = line.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if command in ("quit", "exit", "q"):
            break
        elif command == "list":
            cmd_list(tasks)
        elif command == "add":
            cmd_add(tasks, arg)
        elif command == "done":
            task_id = parse_id(arg)
            if task_id is None:
                print("Usage: done <id>")
            else:
                cmd_done(tasks, task_id)
        elif command == "delete":
            task_id = parse_id(arg)
            if task_id is None:
                print("Usage: delete <id>")
            else:
                cmd_delete(tasks, task_id)
        elif command == "help":
            print(HELP)
        else:
            print(f"Unknown command '{command}'. Type 'help' for options.")


if __name__ == "__main__":
    run_interactive()
