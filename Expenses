import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt

FILE_NAME = "expenses.csv"


def initialize_file():
    """Create the CSV file if it does not exist."""
    if not os.path.exists(FILE_NAME):
        df = pd.DataFrame(columns=["Date", "Category", "Description", "Amount"])
        df.to_csv(FILE_NAME, index=False)


def load_expenses():
    """Load expenses from the CSV file."""
    initialize_file()
    return pd.read_csv(FILE_NAME)


def save_expenses(df):
    """
    Save expenses back to the CSV file.
    The expense list is always sorted by Amount before saving.
    """
    if not df.empty:
        df = df.sort_values(by="Amount", ascending=True).reset_index(drop=True)
    df.to_csv(FILE_NAME, index=False)


def add_expense():
    """Add a new expense."""
    category = input("Enter category: ")
    description = input("Enter description: ")

    try:
        amount = float(input("Enter amount: $"))
    except ValueError:
        print("Invalid amount.")
        return

    df = load_expenses()

    new_entry = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Category": category,
        "Description": description,
        "Amount": amount
    }

    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    save_expenses(df)
    print("Expense added successfully.")


def view_expenses():
    """Display all expenses with their index."""
    df = load_expenses()

    if df.empty:
        print("No expenses found.")
        return

    print("\nCurrent Expenses:")
    print(df.reset_index().to_string(index=False))


def edit_expense():
    """
    Edit an existing expense by index.
    Date/time is automatically updated when edited.
    """
    df = load_expenses()

    if df.empty:
        print("No expenses to edit.")
        return

    view_expenses()

    try:
        index = int(input("\nEnter the index of the expense to edit: "))
        if index < 0 or index >= len(df):
            print("Invalid index.")
            return
    except ValueError:
        print("Invalid input.")
        return

    print("\nLeave blank to keep the current value.")

    current_category = df.at[index, "Category"]
    current_description = df.at[index, "Description"]
    current_amount = df.at[index, "Amount"]

    new_category = input(f"Enter new category [{current_category}]: ")
    new_description = input(f"Enter new description [{current_description}]: ")
    new_amount = input(f"Enter new amount [{current_amount}]: ")

    if new_category.strip() != "":
        df.at[index, "Category"] = new_category

    if new_description.strip() != "":
        df.at[index, "Description"] = new_description

    if new_amount.strip() != "":
        try:
            df.at[index, "Amount"] = float(new_amount)
        except ValueError:
            print("Invalid amount. Edit cancelled.")
            return

    df.at[index, "Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_expenses(df)
    print("Expense updated successfully.")


def delete_expense():
    """Delete an expense by index."""
    df = load_expenses()

    if df.empty:
        print("No expenses to delete.")
        return

    view_expenses()

    try:
        index = int(input("\nEnter the index of the expense to delete: "))
        if index < 0 or index >= len(df):
            print("Invalid index.")
            return
    except ValueError:
        print("Invalid input.")
        return

    df = df.drop(index).reset_index(drop=True)
    save_expenses(df)
    print("Expense deleted successfully.")


def sort_expenses():
    """Sort the expense list by amount and display it."""
    df = load_expenses()

    if df.empty:
        print("No expenses to sort.")
        return

    df = df.sort_values(by="Amount", ascending=True).reset_index(drop=True)
    save_expenses(df)
    print("Expenses sorted by amount.")
    print(df.reset_index().to_string(index=False))


def summarize_expenses():
    """
    Show total, count, and average expense.
    Assignment requires Average Expense in summary.
    """
    df = load_expenses()

    if df.empty:
        print("No expenses found.")
        return

    total = df["Amount"].sum()
    count = len(df)
    average = df["Amount"].mean()

    print("\nExpense Summary")
    print(f"Total Expenses: ${total:.2f}")
    print(f"Number of Expenses: {count}")
    print(f"Average Expense: ${average:.2f}")


def generate_pie_chart():
    """
    Generate a pie chart of all expenses using matplotlib.
    Groups expenses by category so the chart is readable.
    """
    df = load_expenses()

    if df.empty:
        print("No expenses to plot.")
        return

    category_totals = df.groupby("Category")["Amount"].sum()

    if category_totals.empty:
        print("No data to plot.")
        return

    plt.figure(figsize=(8, 8))
    plt.pie(
        category_totals,
        labels=category_totals.index,
        autopct="%1.1f%%",
        startangle=90
    )
    plt.title("Expenses by Category")
    plt.axis("equal")
    plt.show()


def menu():
    """Main menu for the expense tracker."""
    while True:
        print("\nExpense Tracker Menu")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Edit Expense")
        print("4. Delete Expense")
        print("5. Sort Expenses")
        print("6. Summary")
        print("7. Generate Pie Chart")
        print("8. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_expense()
        elif choice == "2":
            view_expenses()
        elif choice == "3":
            edit_expense()
        elif choice == "4":
            delete_expense()
        elif choice == "5":
            sort_expenses()
        elif choice == "6":
            summarize_expenses()
        elif choice == "7":
            generate_pie_chart()
        elif choice == "8":
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    menu()
