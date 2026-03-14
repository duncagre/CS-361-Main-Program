import json
import os
import urllib.request
import urllib.error
import zmq

BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "gift_idea_saver_data.json"))

AUTH_BASE_URL = "http://127.0.0.1:5000"
DUE_DATE_BASE_URL = "http://127.0.0.1:5001"
TAGGING_BASE_URL = "http://127.0.0.1:5002"
SEARCH_ADDRESS = "tcp://127.0.0.1:5555"

#   -------------------------
#   File load/save
#   -------------------------

def load_data():
    """
    Loads saved data from a JSON file.
    If the file does not exist or is invalid, returns empty data.
    """
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        #   Expect a dict
        if not isinstance(data, dict):
            return {}

        #   Basic cleanup in case something unexpected is inside
        changed = False

        for name in list(data.keys()):
            if not isinstance(data[name], list):
                data[name] = []
                changed = True
                continue

            next_id = 1

            for gift in data[name]:
                if not isinstance(gift, dict):
                    continue

                if "id" not in gift:
                    gift["id"] = str(next_id)
                    changed = True

                next_id += 1

        if changed:
            save_data(data)

        return data
    except (OSError, json.JSONDecodeError):
        return {}


def save_data(data):
    """
    Saves the current data to a JSON file.
    """
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


#   -------------------------
#   General helper functions
#   -------------------------

def get_input(prompt):
    """
    Displays a prompt and returns the user's input as a string.
    """
    return input(prompt).strip()


def is_number(text):
    """
    Checks whether the given text is a number.
    """
    return text.isdigit()


def clean_text(text):
    """
    Cleans extra whitespace from user input.
    """
    return " ".join(text.split()).strip()


def pause():
    """
    Pauses the program until the user presses Enter.
    This gives the user time to read the current screen before continuing.
    """
    input("\nPress Enter to continue... ")


#   -------------------------
#   HTTP and message helpers
#   -------------------------

def post_json(url, payload):
    """
    Sends a POST request with JSON data and returns status and response body.
    """
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            response_text = response.read().decode("utf-8")
            return response.status, json.loads(response_text)
    except urllib.error.HTTPError as error:
        response_text = error.read().decode("utf-8")

        try:
            return error.code, json.loads(response_text)
        except json.JSONDecodeError:
            return error.code, {"error": "Service returned invalid response."}
    except urllib.error.URLError:
        return None, {"error": "Could not connect to microservice."}


def send_search_request(keyword, tasks):
    """
    Sends a keyword search request through ZeroMQ.
    """
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(SEARCH_ADDRESS)

    request_data = {
        "keyword": keyword,
        "tasks": tasks
    }

    try:
        socket.send_string(json.dumps(request_data))
        response_text = socket.recv_string()
        response_data = json.loads(response_text)
        return response_data.get("filtered_tasks", [])
    except (OSError, json.JSONDecodeError):
        return []
    finally:
        socket.close()
        context.term()


#   -------------------------
#   Microservice helper functions
#   -------------------------

def register_user(username, password):
    """
    Sends a register request to the authentication microservice.
    """
    return post_json(AUTH_BASE_URL + "/register", {
        "username": username,
        "password": password
    })


def login_user(username, password):
    """
    Sends a login request to the authentication microservice.
    """
    return post_json(AUTH_BASE_URL + "/login", {
        "username": username,
        "password": password
    })


def set_due_date(task_id, due_date):
    """
    Sends a due date request to the due date microservice.
    """
    return post_json(DUE_DATE_BASE_URL + "/set-due-date", {
        "task_id": task_id,
        "due_date": due_date
    })


def get_due_soon(tasks, days):
    """
    Sends a due soon request to the due date microservice.
    """
    return post_json(DUE_DATE_BASE_URL + "/due-soon", {
        "tasks": tasks,
        "days": days
    })


def get_overdue(tasks):
    """
    Sends an overdue request to the due date microservice.
    """
    return post_json(DUE_DATE_BASE_URL + "/overdue", {
        "tasks": tasks
    })


def add_tag(task_id, tag_name):
    """
    Sends an add tag request to the task tagging microservice.
    """
    return post_json(TAGGING_BASE_URL + "/add-tag", {
        "task_id": task_id,
        "tag": tag_name
    })


def remove_tag(task_id, tag_name):
    """
    Sends a remove tag request to the task tagging microservice.
    """
    return post_json(TAGGING_BASE_URL + "/remove-tag", {
        "task_id": task_id,
        "tag": tag_name
    })


def filter_by_tags(tasks, tags):
    """
    Sends a filter by tags request to the task tagging microservice.
    """
    return post_json(TAGGING_BASE_URL + "/filter-by-tags", {
        "tasks": tasks,
        "tags": tags
    })


#   -------------------------
#   Occasion helper functions
#   -------------------------

def choose_occasion():
    """
    Presents text choices in a clear manner.
    Returns a string occasion to save with the gift idea.
    """
    print("\nChoose an occasion:\n")
    print("[1] Birthday")
    print("[2] Christmas")
    print("[3] Other")
    print("[0] Cancel\n")

    choice = get_input("Enter your choice: > ")

    if not is_number(choice):
        return None

    choice = int(choice)

    if choice == 0:
        return None
    if choice == 1:
        return "Birthday"
    if choice == 2:
        return "Christmas"
    if choice == 3:
        other = get_input("Type the occasion: > ")
        other = clean_text(other)
        if other == "":
            return None
        return "Other: " + other

    return None


#   -------------------------
#   Recipient helper functions
#   -------------------------

def list_recipients(data):
    """
    Returns a sorted list of all saved recipient names.
    """
    recipients = list(data.keys())
    recipients.sort()
    return recipients


def add_recipient_to_data(data, name):
    """
    Adds a new recipient to the data store if it does not already exist.
    """
    if name not in data:
        data[name] = []
        save_data(data)
        return True
    return False


#   -------------------------
#   Gift helper functions
#   -------------------------

def get_next_gift_id(data, recipient_name):
    """
    Returns the next ID value for a recipient's gift list.
    """
    gifts = data.get(recipient_name, [])
    highest_id = 0

    for gift in gifts:
        gift_id = str(gift.get("id", "")).strip()

        if gift_id.isdigit():
            gift_id_num = int(gift_id)
            if gift_id_num > highest_id:
                highest_id = gift_id_num

    return str(highest_id + 1)


def add_gift_to_recipient(data, recipient_name, gift_text, occasion_text):
    """
    Adds a gift idea with an associated occasion to a recipient.
    """
    gift_id = get_next_gift_id(data, recipient_name)

    gift_obj = {
        "id": gift_id,
        "idea": gift_text,
        "occasion": occasion_text
    }

    data[recipient_name].append(gift_obj)
    save_data(data)


def get_gifts_for_recipient(data, recipient_name):
    """
    Retrieves all gift ideas associated with a specific recipient.
    """
    return data.get(recipient_name, [])


def get_task_id(recipient_name, gift):
    """
    Builds a unique task ID string for a saved gift.
    """
    return recipient_name + "_" + str(gift.get("id", ""))


def build_task_for_services(recipient_name, gift):
    """
    Builds a task object in the format expected by the microservices.
    """
    return {
        "task_id": get_task_id(recipient_name, gift),
        "title": gift.get("idea", ""),
        "description": gift.get("occasion", ""),
        "due_date": gift.get("due_date", ""),
        "tags": gift.get("tags", [])
    }


#   -------------------------
#   Authentication screens
#   -------------------------

def auth_screen():
    """
    Handles login and registration before the main program starts.
    """
    token = ""

    while token == "":
        print("\nGift Idea Saver Login\n")
        print("[1] Register")
        print("[2] Login")
        print("[0] Exit\n")

        choice = get_input("Enter your choice: > ")

        if choice == "1":
            username = clean_text(get_input("Choose a username: > "))
            password = get_input("Choose a password: > ")

            status, response = register_user(username, password)

            print()
            if status is None:
                print("Could not connect to authentication microservice.\n")
            elif status == 201:
                print("User registered successfully.\n")
            else:
                print(response.get("message", "Registration failed.") + "\n")

            pause()

        elif choice == "2":
            username = clean_text(get_input("Enter username: > "))
            password = get_input("Enter password: > ")

            status, response = login_user(username, password)

            print()
            if status is None:
                print("Could not connect to authentication microservice.\n")
                pause()
            elif status == 200:
                token = response.get("token", "")
                print("Login successful.\n")
                pause()
            else:
                print(response.get("message", "Login failed.") + "\n")
                pause()

        elif choice == "0":
            return None

        else:
            print("\nInvalid input.\n")
            pause()

    return token


#   -------------------------
#   Main menu screen
#   -------------------------

def main_menu(data):
    """
    Displays the main menu and routes the user to selected actions.
    Returns False when the user chooses to exit.
    """
    print("\nGift Idea Saver\n")
    print("What would you like to do?\n")
    print("[1] View recipients")
    print("[2] Add a new recipient")
    print("[3] View gifts due soon")
    print("[4] View overdue gifts")
    print("[5] Filter gifts by tag")
    print("[6] Search gifts by keyword")
    print("[0] Exit\n")

    choice = get_input("Enter your choice: > ")

    if not is_number(choice):
        print("Invalid input.")
        pause()
        return True

    choice = int(choice)

    if choice == 1:
        recipients_screen(data)
        return True
    if choice == 2:
        add_recipient_screen(data)
        return True
    if choice == 3:
        due_soon_screen(data)
        return True
    if choice == 4:
        overdue_screen(data)
        return True
    if choice == 5:
        filter_by_tag_screen(data)
        return True
    if choice == 6:
        main_keyword_search_screen(data)
        return True
    if choice == 0:
        print("\nGoodbye!\n")
        return False

    return True


#   -------------------------
#   Recipient screen
#   -------------------------

def recipients_screen(data):
    """
    Displays the list of recipients and available recipient-related actions.
    """
    recipients = list_recipients(data)

    print("\nRecipients:\n")

    if len(recipients) == 0:
        print("(No recipients yet.)\n")
        print("[1] Add a new recipient")
        print("[0] Return to main menu\n")

        choice = get_input("Enter your choice: > ")
        if choice == "1":
            add_recipient_screen(data)
        return

    for i in range(len(recipients)):
        print(f"[{i + 1}] {recipients[i]}")
    print()

    add_option = len(recipients) + 1
    print(f"[{add_option}] Add a new recipient")
    print("[0] Return to main menu\n")

    choice = get_input("Enter your choice: > ")

    if not is_number(choice):
        print("Invalid input.")
        pause()
        return

    choice = int(choice)

    if choice == 0:
        return
    if choice == add_option:
        add_recipient_screen(data)
        return
    if 1 <= choice <= len(recipients):
        selected = recipients[choice - 1]
        gift_list_screen(data, selected)


#   -------------------------
#   Add recipient screen
#   -------------------------

def add_recipient_screen(data):
    """
    Handles user interaction for adding a new recipient.
    """
    print("\nAdd a New Recipient\n")
    name = get_input("Enter the recipient's name (or type 'cancel'): > ")

    if name.lower() == "cancel":
        print("\nNo recipient was added.\n")
        pause()
        return

    name = clean_text(name)
    if name == "":
        print("\nRecipient name cannot be empty.\n")
        pause()
        return

    print("\n[1] Confirm")
    print("[2] Cancel\n")

    choice = get_input("Enter your choice: > ")

    if choice == "2":
        print("\nNo recipient was added.\n")
        pause()
        return

    was_added = add_recipient_to_data(data, name)

    if was_added:
        print(f'\nRecipient "{name}" added successfully.\n')
    else:
        print(f'\nRecipient "{name}" already exists.\n')

    print("[1] Add a gift idea for this recipient")
    print("[0] Return to main menu\n")

    next_choice = get_input("Enter your choice: > ")
    if next_choice == "1":
        add_gift_screen(data, name)
    else:
        pause()


#   -------------------------
#   Gift list screen
#   -------------------------

def gift_list_screen(data, recipient_name):
    """
    Displays all gift ideas for the selected recipient.
    """
    while True:
        gifts = get_gifts_for_recipient(data, recipient_name)

        print(f"\nGift Ideas for {recipient_name}:\n")

        if len(gifts) == 0:
            print("(No gift ideas yet.)\n")
        else:
            for gift in gifts:
                print(f'[{gift["id"]}] {gift["idea"]} ({gift["occasion"]})')
            print()

        print("[1] Add a gift idea")
        print("[2] Set a due date")
        print("[3] Add a tag")
        print("[4] Remove a tag")
        print("[5] Return to recipient list")
        print("[0] Return to main menu\n")

        choice = get_input("Enter your choice: > ")

        if choice == "1":
            add_gift_screen(data, recipient_name)
        elif choice == "2":
            set_due_date_screen(data, recipient_name)
        elif choice == "3":
            add_tag_screen(data, recipient_name)
        elif choice == "4":
            remove_tag_screen(data, recipient_name)
        elif choice == "5":
            return
        elif choice == "0":
            return
        else:
            print("\nInvalid input.\n")
            pause()


#   -------------------------
#   Add gift screen
#   -------------------------

def add_gift_screen(data, recipient_name):
    """
    Handles user interaction for adding a gift idea and assigning an occasion.
    """
    print(f"\nAdd a Gift Idea for {recipient_name}\n")
    gift_text = get_input("Enter the gift idea (or type 'cancel'): > ")

    if gift_text.lower() == "cancel":
        print("\nNo gift idea was added.\n")
        pause()
        return

    gift_text = clean_text(gift_text)
    if gift_text == "":
        print("\nGift idea cannot be empty.\n")
        pause()
        return

    occasion = choose_occasion()
    if occasion is None:
        print("\nNo gift idea was added.\n")
        pause()
        return

    print("\n[1] Confirm and save")
    print("[2] Cancel\n")

    choice = get_input("Enter your choice: > ")

    if choice == "2":
        print("\nNo gift idea was added.\n")
        pause()
        return

    add_gift_to_recipient(data, recipient_name, gift_text, occasion)

    print(f'\nGift idea "{gift_text}" saved for {recipient_name}.')
    print(f"Occasion: {occasion}\n")
    pause()


#   -------------------------
#   Gift selection helper
#   -------------------------

def choose_gift(data, recipient_name):
    """
    Lets the user choose a saved gift and returns that gift object.
    """
    gifts = get_gifts_for_recipient(data, recipient_name)

    if len(gifts) == 0:
        print("\nNo gift ideas found.\n")
        pause()
        return None

    print(f"\nChoose a gift for {recipient_name}:\n")

    for gift in gifts:
        print(f'[{gift["id"]}] {gift["idea"]} ({gift["occasion"]})')
    print("[0] Cancel\n")

    choice = get_input("Enter your choice: > ")

    if choice == "0":
        return None

    for gift in gifts:
        if str(gift.get("id", "")) == choice:
            return gift

    print("\nInvalid selection.\n")
    pause()
    return None


#   -------------------------
#   Due date screens
#   -------------------------

def set_due_date_screen(data, recipient_name):
    """
    Handles user interaction for setting a due date on a gift.
    """
    gift = choose_gift(data, recipient_name)

    if gift is None:
        return

    print(f'\nSelected gift: {gift["idea"]}\n')
    due_date = get_input("Enter due date in YYYY-MM-DD format: > ")

    status, response = set_due_date(get_task_id(recipient_name, gift), due_date)

    print()
    if status == 200:
        gift["due_date"] = due_date
        save_data(data)
        print("Due date saved successfully.\n")
    elif status is None:
        print("Could not connect to due date microservice.\n")
    else:
        print(response.get("error", "Could not save due date.") + "\n")

    pause()


def due_soon_screen(data):
    """
    Shows gifts due within a user-selected number of days.
    """
    days_text = get_input("\nShow gifts due within how many days? > ")

    if not is_number(days_text):
        print("\nInvalid number.\n")
        pause()
        return

    days = int(days_text)
    tasks = []

    for recipient_name in list_recipients(data):
        gifts = get_gifts_for_recipient(data, recipient_name)

        for gift in gifts:
            if "due_date" in gift:
                task = build_task_for_services(recipient_name, gift)
                task["recipient"] = recipient_name
                tasks.append(task)

    status, response = get_due_soon(tasks, days)

    print("\nGifts Due Soon:\n")

    if status != 200:
        if status is None:
            print("Could not connect to due date microservice.\n")
        else:
            print(response.get("error", "Could not retrieve due soon gifts.") + "\n")
        pause()
        return

    due_soon_tasks = response.get("tasks", [])

    if len(due_soon_tasks) == 0:
        print("(No gifts due soon.)\n")
    else:
        for task in due_soon_tasks:
            print(f'- {task["title"]} | {task["recipient"]} | {task["due_date"]}')
        print()

    pause()


def overdue_screen(data):
    """
    Shows overdue gifts.
    """
    tasks = []

    for recipient_name in list_recipients(data):
        gifts = get_gifts_for_recipient(data, recipient_name)

        for gift in gifts:
            if "due_date" in gift:
                task = build_task_for_services(recipient_name, gift)
                task["recipient"] = recipient_name
                tasks.append(task)

    status, response = get_overdue(tasks)

    print("\nOverdue Gifts:\n")

    if status != 200:
        if status is None:
            print("Could not connect to due date microservice.\n")
        else:
            print(response.get("error", "Could not retrieve overdue gifts.") + "\n")
        pause()
        return

    overdue_tasks = response.get("tasks", [])

    if len(overdue_tasks) == 0:
        print("(No overdue gifts.)\n")
    else:
        for task in overdue_tasks:
            print(f'- {task["title"]} | {task["recipient"]} | {task["due_date"]}')
        print()

    pause()


#   -------------------------
#   Tag screens
#   -------------------------

def add_tag_screen(data, recipient_name):
    """
    Handles user interaction for adding a tag to a gift.
    """
    gift = choose_gift(data, recipient_name)

    if gift is None:
        return

    tag_name = get_input("\nEnter a tag to add: > ")
    tag_name = clean_text(tag_name)

    if tag_name == "":
        print("\nTag cannot be empty.\n")
        pause()
        return

    status, response = add_tag(get_task_id(recipient_name, gift), tag_name)

    print()
    if status == 200:
        gift["tags"] = response.get("tags", [])
        save_data(data)
        print("Tag added successfully.\n")
    elif status is None:
        print("Could not connect to task tagging microservice.\n")
    else:
        print(response.get("error", "Could not add tag.") + "\n")

    pause()


def remove_tag_screen(data, recipient_name):
    """
    Handles user interaction for removing a tag from a gift.
    """
    gift = choose_gift(data, recipient_name)

    if gift is None:
        return

    current_tags = gift.get("tags", [])

    print(f'\nCurrent tags: {", ".join(current_tags) if len(current_tags) > 0 else "(none)"}\n')

    tag_name = get_input("Enter a tag to remove: > ")
    tag_name = clean_text(tag_name)

    if tag_name == "":
        print("\nTag cannot be empty.\n")
        pause()
        return

    status, response = remove_tag(get_task_id(recipient_name, gift), tag_name)

    print()
    if status == 200:
        gift["tags"] = response.get("tags", [])
        save_data(data)
        print("Tag removed successfully.\n")
    elif status is None:
        print("Could not connect to task tagging microservice.\n")
    else:
        print(response.get("error", "Could not remove tag.") + "\n")

    pause()


def filter_by_tag_screen(data):
    """
    Shows gifts that match a given tag.
    """
    tag_name = get_input("\nEnter a tag to search for: > ")
    tag_name = clean_text(tag_name)

    if tag_name == "":
        print("\nTag cannot be empty.\n")
        pause()
        return

    tasks = []

    for recipient_name in list_recipients(data):
        gifts = get_gifts_for_recipient(data, recipient_name)

        for gift in gifts:
            task = build_task_for_services(recipient_name, gift)
            task["recipient"] = recipient_name
            tasks.append(task)

    status, response = filter_by_tags(tasks, [tag_name])

    print("\nMatching Gifts:\n")

    if status != 200:
        if status is None:
            print("Could not connect to task tagging microservice.\n")
        else:
            print(response.get("error", "Could not filter gifts.") + "\n")
        pause()
        return

    matching_tasks = response.get("tasks", [])

    if len(matching_tasks) == 0:
        print("(No matching gifts found.)\n")
    else:
        for task in matching_tasks:
            print(f'- {task["title"]} | {task["recipient"]}')
        print()

    pause()


#   -------------------------
#   Keyword search screen
#   -------------------------

def keyword_search_screen(data, recipient_name):
    """
    Searches a recipient's gift list by keyword using the keyword search microservice.
    """
    keyword = get_input("\nEnter a keyword to search for: > ")
    keyword = clean_text(keyword)

    if keyword == "":
        print("\nKeyword cannot be empty.\n")
        pause()
        return

    gifts = get_gifts_for_recipient(data, recipient_name)
    tasks = []

    for gift in gifts:
        tasks.append({
            "task_id": get_task_id(recipient_name, gift),
            "title": gift.get("idea", ""),
            "description": gift.get("occasion", "")
        })

    filtered_tasks = send_search_request(keyword, tasks)

    print(f'\nSearch Results for "{keyword}":\n')

    if len(filtered_tasks) == 0:
        print("(No matching gifts found.)\n")
    else:
        for task in filtered_tasks:
            print(f'- {task["title"]} ({task["description"]})')
        print()

    pause()


def main_keyword_search_screen(data):
    """
    Allows the user to choose a recipient and search their gifts by keyword.
    """
    recipients = list_recipients(data)

    if len(recipients) == 0:
        print("\nNo recipients available.\n")
        pause()
        return

    print("\nChoose a recipient to search:\n")

    for i in range(len(recipients)):
        print(f"[{i + 1}] {recipients[i]}")

    print("[0] Cancel\n")

    choice = get_input("Enter your choice: > ")

    if not is_number(choice):
        print("\nInvalid input.\n")
        pause()
        return

    choice = int(choice)

    if choice == 0:
        return

    if 1 <= choice <= len(recipients):
        recipient_name = recipients[choice - 1]
        keyword_search_screen(data, recipient_name)
        return

    print("\nInvalid selection.\n")
    pause()


#   -------------------------
#   Run program
#   -------------------------

def run_program():
    """
    Starts the Gift Idea Saver program and keeps it running until exit.
    """
    token = auth_screen()

    if token is None:
        print("\nGoodbye!\n")
        return

    data = load_data()

    running = True
    while running:
        running = main_menu(data)


if __name__ == "__main__":
    run_program()