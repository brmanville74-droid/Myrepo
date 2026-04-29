import json
import os
import re

# Name of the JSON file used to store contacts permanently
CONTACTS_FILE = "contacts.json"


def load_contacts():
    """
    Loads contacts from the JSON file.
    If the file does not exist or is invalid, return an empty list.
    """
    if not os.path.exists(CONTACTS_FILE):
        return []

    try:
        with open(CONTACTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

            # Make sure the JSON data is a list
            if isinstance(data, list):
                return data
            else:
                return []
    except (json.JSONDecodeError, IOError):
        return []


def save_contacts(contacts):
    """
    Saves the contacts list to the JSON file.
    """
    with open(CONTACTS_FILE, "w", encoding="utf-8") as file:
        json.dump(contacts, file, indent=4)


def is_valid_name(name):
    """
    Returns True if the name contains only letters and spaces.
    """
    return bool(re.fullmatch(r"[A-Za-z ]+", name.strip()))


def is_valid_phone(phone):
    """
    Returns True if the phone number contains only digits.
    """
    return phone.isdigit()


def is_valid_email(email):
    """
    Basic email validation.
    """
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email.strip()))


def add_contact(contacts):
    """
    Prompts the user for contact information, validates it,
    and adds it to the contact list.
    """
    print("\n--- Add Contact ---")

    name = input("Enter name: ").strip()
    if not is_valid_name(name):
        print("Error: Name must contain only letters and spaces.")
        return

    phone = input("Enter phone number: ").strip()
    if not is_valid_phone(phone):
        print("Error: Phone number must contain only digits.")
        return

    address = input("Enter address: ").strip()

    email = input("Enter email: ").strip()
    if not is_valid_email(email):
        print("Error: Please enter a valid email address.")
        return

    # Prevent duplicate names if desired
    for contact in contacts:
        if contact["name"].lower() == name.lower():
            print("Error: A contact with that name already exists.")
            return

    contact = {
        "name": name,
        "phone": phone,
        "address": address,
        "email": email
    }

    contacts.append(contact)
    save_contacts(contacts)
    print(f"Contact '{name}' added successfully.")


def view_contacts(contacts):
    """
    Displays all contacts in the contact list.
    """
    print("\n--- Contact List ---")

    if not contacts:
        print("No contacts found.")
        return

    for index, contact in enumerate(contacts, start=1):
        print(f"\nContact #{index}")
        print(f"Name:    {contact['name']}")
        print(f"Phone:   {contact['phone']}")
        print(f"Address: {contact['address']}")
        print(f"Email:   {contact['email']}")


def search_contact(contacts):
    """
    Searches for contacts by name.
    """
    print("\n--- Search Contact ---")
    search_name = input("Enter the name to search for: ").strip().lower()

    found_contacts = [
        contact for contact in contacts
        if search_name in contact["name"].lower()
    ]

    if not found_contacts:
        print("No matching contact found.")
        return

    print("\nMatching Contacts:")
    for contact in found_contacts:
        print(f"\nName:    {contact['name']}")
        print(f"Phone:   {contact['phone']}")
        print(f"Address: {contact['address']}")
        print(f"Email:   {contact['email']}")


def delete_contact(contacts):
    """
    Deletes a contact by exact name match.
    """
    print("\n--- Delete Contact ---")
    name_to_delete = input("Enter the exact name of the contact to delete: ").strip().lower()

    for contact in contacts:
        if contact["name"].lower() == name_to_delete:
            contacts.remove(contact)
            save_contacts(contacts)
            print(f"Contact '{contact['name']}' deleted successfully.")
            return

    print("No contact found with that name.")


def display_menu():
    """
    Displays the main menu.
    """
    print("\n===== Contact Book Menu =====")
    print("1. Add Contact")
    print("2. View Contacts")
    print("3. Search Contact")
    print("4. Delete Contact")
    print("5. Exit")


def main():
    """
    Main program loop.
    """
    contacts = load_contacts()

    while True:
        display_menu()
        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            add_contact(contacts)
        elif choice == "2":
            view_contacts(contacts)
        elif choice == "3":
            search_contact(contacts)
        elif choice == "4":
            delete_contact(contacts)
        elif choice == "5":
            print("Exiting Contact Book. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 5.")


if __name__ == "__main__":
    main()
    
