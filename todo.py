import json
import os
import re

from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

DATA_FILE = os.path.join(os.path.dirname(__file__), "tasks.json")

PRIORITIES = ("high", "medium", "low")
PRIORITY_ORDER = {p: i for i, p in enumerate(PRIORITIES)}

PRIORITY_COLOR = {
    "high": Fore.RED,
    "medium": Fore.YELLOW,
    "low": Fore.GREEN,
}


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


def format_task(t):
    pri = t.get("priority", "medium")
    color = PRIORITY_COLOR[pri]
    done = t["done"]

    status = f"{Fore.GREEN}x{Style.RESET_ALL}" if done else " "
    title = f"{Style.DIM}{t['title']}{Style.RESET_ALL}" if done else f"{color}{t['title']}{Style.RESET_ALL}"
    pri_tag = f"{color}[{pri}]{Style.RESET_ALL}"
    due = f"  {Fore.CYAN}due: {t['due_date']}{Style.RESET_ALL}" if t.get("due_date") else ""
    id_str = f"{Style.BRIGHT}{t['id']}{Style.RESET_ALL}"

    return f"  [{status}] {id_str}. {pri_tag} {title}{due}"


def cmd_list(tasks, filter_priority=None, sort_by_priority=False):
    visible = tasks
    if filter_priority:
        visible = [t for t in tasks if t.get("priority", "medium") == filter_priority]
    if sort_by_priority:
        visible = sorted(visible, key=lambda t: PRIORITY_ORDER.get(t.get("priority", "medium"), 1))
    if not visible:
        print(f"{Style.DIM}No tasks found.{Style.RESET_ALL}")
        return
    for t in visible:
        print(format_task(t))


def parse_flags(arg):
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
        print(f"{Fore.RED}Error: task title cannot be empty.{Style.RESET_ALL}")
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
    color = PRIORITY_COLOR[priority]
    due_info = f" {Fore.CYAN}(due: {due_date}){Style.RESET_ALL}" if due_date else ""
    print(f"{Fore.GREEN}Added:{Style.RESET_ALL} {task['id']}. {color}[{priority}]{Style.RESET_ALL} {title}{due_info}")


def cmd_due(tasks, task_id, due_date):
    for t in tasks:
        if t["id"] == task_id:
            t["due_date"] = due_date
            save_tasks(tasks)
            print(f"Set due date for '{Fore.CYAN}{t['title']}{Style.RESET_ALL}': {Fore.CYAN}{due_date}{Style.RESET_ALL}")
            return
    print(f"{Fore.RED}Error: no task with id {task_id}.{Style.RESET_ALL}")


def cmd_priority(tasks, task_id, priority):
    for t in tasks:
        if t["id"] == task_id:
            t["priority"] = priority
            save_tasks(tasks)
            color = PRIORITY_COLOR[priority]
            print(f"Set priority for '{t['title']}': {color}{priority}{Style.RESET_ALL}")
            return
    print(f"{Fore.RED}Error: no task with id {task_id}.{Style.RESET_ALL}")


def cmd_done(tasks, task_id):
    for t in tasks:
        if t["id"] == task_id:
            if t["done"]:
                print(f"{Style.DIM}Task {task_id} is already done.{Style.RESET_ALL}")
            else:
                t["done"] = True
                save_tasks(tasks)
                print(f"{Fore.GREEN}Marked done:{Style.RESET_ALL} {t['title']}")
            return
    print(f"{Fore.RED}Error: no task with id {task_id}.{Style.RESET_ALL}")


def cmd_delete(tasks, task_id):
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            removed = tasks.pop(i)
            save_tasks(tasks)
            print(f"{Fore.RED}Deleted:{Style.RESET_ALL} {removed['title']}")
            return
    print(f"{Fore.RED}Error: no task with id {task_id}.{Style.RESET_ALL}")


def cmd_search(tasks, query):
    query_lower = query.lower()
    matches = [t for t in tasks if query_lower in t["title"].lower()]
    if not matches:
        print(f"{Style.DIM}No tasks match '{query}'.{Style.RESET_ALL}")
        return
    print(f"{Style.BRIGHT}Results for '{query}':{Style.RESET_ALL}")
    for t in matches:
        print(format_task(t))


HELP = f"""
{Style.BRIGHT}Commands:{Style.RESET_ALL}
  list [--priority LEVEL] [--sort]   Show tasks; filter/sort by priority
  search <query>                     Search tasks by title
  add <title> [--due DATE]           Add a task (DATE: YYYY-MM-DD)
        [--priority LEVEL]           Priority: {Fore.RED}high{Style.RESET_ALL}, {Fore.YELLOW}medium{Style.RESET_ALL} (default), {Fore.GREEN}low{Style.RESET_ALL}
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
    print(f"{Style.BRIGHT}To-Do App{Style.RESET_ALL}  (type 'help' for commands)")
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
                print(f"{Fore.RED}Error: date must be YYYY-MM-DD.{Style.RESET_ALL}")
            else:
                cmd_due(tasks, task_id, date)
        elif command == "priority":
            sub = arg.split(maxsplit=1)
            task_id = parse_id(sub[0]) if sub else None
            level = sub[1].strip() if len(sub) > 1 else None
            if task_id is None or not level:
                print("Usage: priority <id> <high|medium|low>")
            elif level not in PRIORITIES:
                print(f"{Fore.RED}Error: priority must be high, medium, or low.{Style.RESET_ALL}")
            else:
                cmd_priority(tasks, task_id, level)
        elif command == "search":
            if not arg:
                print("Usage: search <query>")
            else:
                cmd_search(tasks, arg)
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
