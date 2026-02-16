import json
import os

BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "gift_idea_saver_data.json"))

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
        for name in list(data.keys()):
            if not isinstance(data[name], list):
                data[name] = []

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
#   Recipient logic
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
    #   Data remains after restarting program since it is saved to file     #   Reliability
    if name not in data:
        data[name] = []
        save_data(data)
        return True
    return False


#   -------------------------
#   Gift logic
#   -------------------------

def add_gift_to_recipient(data, recipient_name, gift_text, occasion_text):
    """
    Adds a gift idea with an associated occasion to a recipient.
    """
    gift_obj = {"idea": gift_text, "occasion": occasion_text}
    data[recipient_name].append(gift_obj)
    save_data(data)


def get_gifts_for_recipient(data, recipient_name):
    """
    Retrieves all gift ideas associated with a specific recipient.
    """
    return data.get(recipient_name, [])


#   -------------------------
#   Main Menu screen
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
    print("[0] Exit\n")

    choice = get_input("Enter your choice: > ")

    if not is_number(choice):
        print("Invalid input.")
        return True
    
    choice = int(choice)

    if choice == 1:
        recipients_screen(data)
        return True
    if choice == 2:
        add_recipient_screen(data)
        return True
    if choice == 0:
        print("\nGoodbye!\n")
        return False
    
    return True


#   -------------------------
#   Recipients screen
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
#   Add Recipients screen
#   -------------------------

def add_recipient_screen(data):
    """
    Handles user interaction for adding a new recipient.
    """
    print("\nAdd a New Recipient\n")
    name = get_input("Enter the recipient's name (or type 'cancel'): > ")

    if name.lower() == "cancel":
        print("\nNo recipient was added.\n")
        return

    name = clean_text(name)
    if name == "":
        print("\nRecipient name cannot be empty.\n")
        return

    print("\n[1] Confirm")
    print("[2] Cancel\n")

    choice = get_input("Enter your choice: > ")

    if choice == "2":
        print("\nNo recipient was added.\n")
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


#   -------------------------
#   Gifts screen
#   -------------------------

def gift_list_screen(data, recipient_name):
    """
    Displays all gift ideas for the selected recipient.
    """
    gifts = get_gifts_for_recipient(data, recipient_name)

    print(f"\nGift Ideas for {recipient_name}:\n")

    if len(gifts) == 0:
        print("(No gift ideas yet.)\n")
    else:
        for gift in gifts:
            print(f"- {gift['idea']} ({gift['occasion']})")
        print()

    print("[1] Add a gift idea")
    print("[2] Return to recipient list")
    print("[0] Return to main menu\n")

    choice = get_input("Enter your choice: > ")

    if choice == "1":
        add_gift_screen(data, recipient_name)
    elif choice == "2":
        recipients_screen(data)
    # choice 0 just returns


#   -------------------------
#   Add Gifts screen
#   -------------------------

def add_gift_screen(data, recipient_name):
    """
    Handles user interaction for adding a gift idea and assigning an occasion.
    """
    print(f"\nAdd a Gift Idea for {recipient_name}\n")
    gift_text = get_input("Enter the gift idea (or type 'cancel'): > ")

    if gift_text.lower() == "cancel":
        print("\nNo gift idea was added.\n")
        return

    gift_text = clean_text(gift_text)
    if gift_text == "":
        print("\nGift idea cannot be empty.\n")
        return

    occasion = choose_occasion()
    if occasion is None:
        print("\nNo gift idea was added.\n")
        return

    print("\n[1] Confirm and save")
    print("[2] Cancel\n")

    choice = get_input("Enter your choice: > ")

    if choice == "2":
        print("\nNo gift idea was added.\n")
        return

    add_gift_to_recipient(data, recipient_name, gift_text, occasion)

    print(f'\nGift idea "{gift_text}" saved for {recipient_name}.')
    print(f"Occasion: {occasion}\n")


#   -------------------------
#   Run program
#   -------------------------

def run_program():
    """
    Starts the Gift Idea Saver program and keeps it running until exit.
    """
    data = load_data()
    
    running = True
    while running:
        running = main_menu(data)


if __name__ == "__main__":
    run_program()