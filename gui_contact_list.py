import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

CONTACTS_FILE = "contacts.json"


def load_contacts(file_path):
    """
    Loads contacts from a JSON file.
    If the file does not exist or has bad data, it returns an empty list.
    """
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

            if isinstance(data, list):
                return data
            return []

    except (json.JSONDecodeError, IOError):
        return []


def save_contacts(file_path, contacts):
    """
    Saves the current contact list to the selected JSON file.
    """
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(contacts, file, indent=4)


def is_valid_name(name):
    """
    Checks that the name only contains letters and spaces.
    """
    return bool(re.fullmatch(r"[A-Za-z ]+", name.strip()))


def is_valid_phone(phone):
    """
    Checks that the phone number only contains digits.
    """
    return phone.isdigit()


def is_valid_email(email):
    """
    Checks that the email is in a basic valid email format.
    """
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email.strip()))


class ContactListGUI:
    def __init__(self, root):
        """
        Sets up the main GUI window and loads the default contacts file.
        """
        self.root = root
        self.root.title("GUI Contact List")
        self.root.geometry("850x500")

        self.file_path = CONTACTS_FILE
        self.contacts = load_contacts(self.file_path)
        self.selected_index = None

        self.create_widgets()
        self.refresh_table()

    def create_widgets(self):
        """
        Creates all labels, text boxes, buttons, and the contact table.
        """
        title = tk.Label(
            self.root,
            text="Contact List Manager",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=10)

        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5)
        self.name_entry = tk.Entry(input_frame, width=25)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Phone:").grid(row=0, column=2, padx=5, pady=5)
        self.phone_entry = tk.Entry(input_frame, width=25)
        self.phone_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(input_frame, text="Address:").grid(row=1, column=0, padx=5, pady=5)
        self.address_entry = tk.Entry(input_frame, width=25)
        self.address_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Email:").grid(row=1, column=2, padx=5, pady=5)
        self.email_entry = tk.Entry(input_frame, width=25)
        self.email_entry.grid(row=1, column=3, padx=5, pady=5)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Add Contact", width=15, command=self.add_contact).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Update Contact", width=15, command=self.update_contact).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Delete Contact", width=15, command=self.delete_contact).grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Clear Boxes", width=15, command=self.clear_entries).grid(row=0, column=3, padx=5)
        tk.Button(button_frame, text="Open JSON File", width=15, command=self.open_file).grid(row=0, column=4, padx=5)

        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=5)

        tk.Label(search_frame, text="Search Name:").grid(row=0, column=0, padx=5)
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.grid(row=0, column=1, padx=5)

        tk.Button(search_frame, text="Search", command=self.search_contact).grid(row=0, column=2, padx=5)
        tk.Button(search_frame, text="Show All", command=self.refresh_table).grid(row=0, column=3, padx=5)

        self.tree = ttk.Treeview(
            self.root,
            columns=("Name", "Phone", "Address", "Email"),
            show="headings"
        )

        self.tree.heading("Name", text="Name")
        self.tree.heading("Phone", text="Phone")
        self.tree.heading("Address", text="Address")
        self.tree.heading("Email", text="Email")

        self.tree.column("Name", width=160)
        self.tree.column("Phone", width=130)
        self.tree.column("Address", width=260)
        self.tree.column("Email", width=220)

        self.tree.pack(fill="both", expand=True, padx=15, pady=10)

        self.tree.bind("<<TreeviewSelect>>", self.select_contact)

    def validate_contact(self, name, phone, email):
        """
        Validates the name, phone number, and email before saving.
        """
        if not is_valid_name(name):
            messagebox.showerror("Invalid Name", "Name must contain only letters and spaces.")
            return False

        if not is_valid_phone(phone):
            messagebox.showerror("Invalid Phone", "Phone number must contain only digits.")
            return False

        if not is_valid_email(email):
            messagebox.showerror("Invalid Email", "Please enter a valid email address.")
            return False

        return True

    def add_contact(self):
        """
        Adds a new contact to the list and saves it to the JSON file.
        """
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        address = self.address_entry.get().strip()
        email = self.email_entry.get().strip()

        if not self.validate_contact(name, phone, email):
            return

        for contact in self.contacts:
            if contact["name"].lower() == name.lower():
                messagebox.showerror("Duplicate Contact", "A contact with that name already exists.")
                return

        new_contact = {
            "name": name,
            "phone": phone,
            "address": address,
            "email": email
        }

        self.contacts.append(new_contact)
        save_contacts(self.file_path, self.contacts)
        self.refresh_table()
        self.clear_entries()

        messagebox.showinfo("Success", "Contact added successfully.")

    def update_contact(self):
        """
        Updates the selected contact with the new information in the text boxes.
        """
        if self.selected_index is None:
            messagebox.showerror("No Selection", "Please select a contact to update.")
            return

        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        address = self.address_entry.get().strip()
        email = self.email_entry.get().strip()

        if not self.validate_contact(name, phone, email):
            return

        self.contacts[self.selected_index] = {
            "name": name,
            "phone": phone,
            "address": address,
            "email": email
        }

        save_contacts(self.file_path, self.contacts)
        self.refresh_table()
        self.clear_entries()

        messagebox.showinfo("Success", "Contact updated successfully.")

    def delete_contact(self):
        """
        Deletes the selected contact from the list and saves the change.
        """
        if self.selected_index is None:
            messagebox.showerror("No Selection", "Please select a contact to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this contact?")

        if confirm:
            self.contacts.pop(self.selected_index)
            save_contacts(self.file_path, self.contacts)
            self.refresh_table()
            self.clear_entries()

            messagebox.showinfo("Deleted", "Contact deleted successfully.")

    def search_contact(self):
        """
        Searches for contacts by name and displays matching results.
        """
        search_name = self.search_entry.get().strip().lower()

        if not search_name:
            self.refresh_table()
            return

        results = [
            contact for contact in self.contacts
            if search_name in contact["name"].lower()
        ]

        self.display_contacts(results)

    def open_file(self):
        """
        Opens a file dialog so the user can choose a different JSON contact file.
        """
        selected_file = filedialog.askopenfilename(
            title="Open Contact List JSON File",
            filetypes=(("JSON Files", "*.json"), ("All Files", "*.*"))
        )

        if selected_file:
            self.file_path = selected_file
            self.contacts = load_contacts(self.file_path)
            self.refresh_table()
            self.clear_entries()

            messagebox.showinfo("File Opened", "Contact file loaded successfully.")

    def select_contact(self, event):
        """
        Puts the selected contact's information into the text boxes.
        """
        selected_item = self.tree.selection()

        if not selected_item:
            return

        item = self.tree.item(selected_item)
        values = item["values"]

        selected_name = values[0]

        for index, contact in enumerate(self.contacts):
            if contact["name"] == selected_name:
                self.selected_index = index
                break

        self.clear_entries()

        self.name_entry.insert(0, values[0])
        self.phone_entry.insert(0, values[1])
        self.address_entry.insert(0, values[2])
        self.email_entry.insert(0, values[3])

    def display_contacts(self, contacts_to_display):
        """
        Clears the table and displays the contacts passed into this function.
        """
        for row in self.tree.get_children():
            self.tree.delete(row)

        for contact in contacts_to_display:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    contact["name"],
                    contact["phone"],
                    contact["address"],
                    contact["email"]
                )
            )

    def refresh_table(self):
        """
        Reloads the table with all contacts.
        """
        self.display_contacts(self.contacts)
        self.selected_index = None

    def clear_entries(self):
        """
        Clears all input boxes.
        """
        self.name_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.selected_index = None


def main():
    """
    Starts the GUI contact list program.
    """
    root = tk.Tk()
    app = ContactListGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
