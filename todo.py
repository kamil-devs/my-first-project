import json
import os
import re

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


def cmd_list(tasks, filter_priority=None, sort_by_priority=False):
    visible = tasks
    if filter_priority:
        visible = [t for t in tasks if t.get("priority", "medium") == filter_priority]
    if sort_by_priority:
        visible = sorted(visible, key=lambda t: PRIORITY_ORDER.get(t.get("priority", "medium"), 1))
    if not visible:
        print("No tasks found.")
        return
    for t in visible:
        status = "x" if t["done"] else " "
        due = f"  due: {t['due_date']}" if t.get("due_date") else ""
        pri = t.get("priority", "medium")
        print(f"  [{status}] {t['id']}. [{pri}] {t['title']}{due}")


def parse_flags(arg):
    """Extract --due and --priority flags from arg, return (title, due_date, priority)."""
    due_date = None
    priority = "medium"

    match_due = re.search(r"--due\s+(\d{4}-\d{2}-\d{2})", arg)
    if match_due:
        due_date = match_due.group(1)
        arg = arg[: match_due.start()] + arg[match_due.end():]

    match_pri = re.search(r"--priority\s+(high|medium|low)", arg)
    if match_pri:
        priority = match_pri.group(1)
        arg = arg[: match_pri.start()] + arg[match_pri.end():]

    return arg.strip(), due_date, priority


def cmd_add(tasks, arg):
    title, due_date, priority = parse_flags(arg)
    if not title:
        print("Error: task title cannot be empty.")
        return
    task = {
        "id": next_id(tasks),
        "title": title,
        "done": False,
        "due_date": due_date,
        "priority": priority,
    }
    tasks.append(task)
    save_tasks(tasks)
    due_info = f" (due: {due_date})" if due_date else ""
    print(f"Added: {task['id']}. [{priority}] {title}{due_info}")


def cmd_due(tasks, task_id, due_date):
    for t in tasks:
        if t["id"] == task_id:
            t["due_date"] = due_date
            save_tasks(tasks)
            print(f"Set due date for '{t['title']}': {due_date}")
            return
    print(f"Error: no task with id {task_id}.")


def cmd_priority(tasks, task_id, priority):
    for t in tasks:
        if t["id"] == task_id:
            t["priority"] = priority
            save_tasks(tasks)
            print(f"Set priority for '{t['title']}': {priority}")
            return
    print(f"Error: no task with id {task_id}.")


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
  list [--priority LEVEL] [--sort]   Show tasks; filter/sort by priority
  add <title> [--due DATE]           Add a task (DATE: YYYY-MM-DD)
        [--priority LEVEL]           Priority: high, medium (default), low
  due <id> <date>                    Set/update due date for a task
  priority <id> <level>              Set/update priority for a task
  done <id>                          Mark a task as done
  delete <id>                        Delete a task
  help                               Show this message
  quit                               Exit
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
            filter_pri = None
            sort_flag = "--sort" in arg
            match = re.search(r"--priority\s+(high|medium|low)", arg)
            if match:
                filter_pri = match.group(1)
            cmd_list(tasks, filter_priority=filter_pri, sort_by_priority=sort_flag)
        elif command == "add":
            cmd_add(tasks, arg)
        elif command == "due":
            sub = arg.split(maxsplit=1)
            task_id = parse_id(sub[0]) if sub else None
            date = sub[1].strip() if len(sub) > 1 else None
            if task_id is None or not date:
                print("Usage: due <id> <YYYY-MM-DD>")
            elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                print("Error: date must be YYYY-MM-DD.")
            else:
                cmd_due(tasks, task_id, date)
        elif command == "priority":
            sub = arg.split(maxsplit=1)
            task_id = parse_id(sub[0]) if sub else None
            level = sub[1].strip() if len(sub) > 1 else None
            if task_id is None or not level:
                print("Usage: priority <id> <high|medium|low>")
            elif level not in PRIORITIES:
                print("Error: priority must be high, medium, or low.")
            else:
                cmd_priority(tasks, task_id, level)
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
