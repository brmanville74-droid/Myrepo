import tkinter as tk
from tkinter import ttk


class TipToolApp:
    """Simple Tkinter GUI tip calculator."""

    def __init__(self, root):
        self.root = root
        self.root.title("GUI Tip Tool")
        self.root.geometry("420x420")
        self.root.resizable(False, False)

        # Input variables
        self.bill_var = tk.StringVar()
        self.tip_var = tk.IntVar(value=15)
        self.diners_var = tk.IntVar(value=1)

        # Output variables
        self.tip_amount_var = tk.StringVar(value="$0.00")
        self.total_with_tip_var = tk.StringVar(value="$0.00")
        self.per_person_var = tk.StringVar(value="$0.00")
        self.status_var = tk.StringVar(value="Enter a bill amount to begin.")

        self.build_gui()
        self.bind_events()
        self.update_calculation()

    def build_gui(self):
        """Create the GUI layout."""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)

        title_label = ttk.Label(
            main_frame,
            text="Tip Calculator",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=(0, 15))

        # Bill input
        bill_frame = ttk.Frame(main_frame)
        bill_frame.pack(fill="x", pady=5)

        ttk.Label(bill_frame, text="Total Bill Amount ($):").pack(anchor="w")
        self.bill_entry = ttk.Entry(bill_frame, textvariable=self.bill_var)
        self.bill_entry.pack(fill="x", pady=(5, 0))

        # Tip percentage
        tip_frame = ttk.LabelFrame(main_frame, text="Tip Percentage", padding=10)
        tip_frame.pack(fill="x", pady=10)

        ttk.Radiobutton(tip_frame, text="10%", variable=self.tip_var, value=10).pack(side="left", padx=10)
        ttk.Radiobutton(tip_frame, text="15%", variable=self.tip_var, value=15).pack(side="left", padx=10)
        ttk.Radiobutton(tip_frame, text="20%", variable=self.tip_var, value=20).pack(side="left", padx=10)

        # Diners
        diners_frame = ttk.Frame(main_frame)
        diners_frame.pack(fill="x", pady=5)

        ttk.Label(diners_frame, text="Number of Diners (1-6):").pack(anchor="w")
        self.diners_spinbox = ttk.Spinbox(
            diners_frame,
            from_=1,
            to=6,
            textvariable=self.diners_var,
            width=5
        )
        self.diners_spinbox.pack(anchor="w", pady=(5, 0))

        # Results
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.pack(fill="x", pady=15)

        ttk.Label(results_frame, text="Tip Amount:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(results_frame, textvariable=self.tip_amount_var).grid(row=0, column=1, sticky="e", padx=5, pady=5)

        ttk.Label(results_frame, text="Total with Tip:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(results_frame, textvariable=self.total_with_tip_var).grid(row=1, column=1, sticky="e", padx=5, pady=5)

        ttk.Label(results_frame, text="Each Person Pays:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(results_frame, textvariable=self.per_person_var).grid(row=2, column=1, sticky="e", padx=5, pady=5)

        results_frame.columnconfigure(0, weight=1)
        results_frame.columnconfigure(1, weight=1)

        # Status / error message
        self.status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            foreground="red"
        )
        self.status_label.pack(pady=(0, 15))

        # Exit button
        ttk.Button(main_frame, text="Exit", command=self.root.destroy).pack()

    def bind_events(self):
        """Update calculations automatically when input changes."""
        self.bill_var.trace_add("write", lambda *args: self.update_calculation())
        self.tip_var.trace_add("write", lambda *args: self.update_calculation())
        self.diners_var.trace_add("write", lambda *args: self.update_calculation())

    def update_calculation(self):
        """Recalculate tip, total, and split amount."""
        bill_text = self.bill_var.get().strip()

        if bill_text == "":
            self.tip_amount_var.set("$0.00")
            self.total_with_tip_var.set("$0.00")
            self.per_person_var.set("$0.00")
            self.status_var.set("Enter a bill amount to begin.")
            return

        try:
            bill_amount = float(bill_text)
            if bill_amount < 0:
                raise ValueError
        except ValueError:
            self.tip_amount_var.set("$0.00")
            self.total_with_tip_var.set("$0.00")
            self.per_person_var.set("$0.00")
            self.status_var.set("Please enter a valid non-negative number for the bill.")
            return

        try:
            diners = int(self.diners_var.get())
            if diners < 1:
                diners = 1
            elif diners > 6:
                diners = 6
            self.diners_var.set(diners)
        except (ValueError, tk.TclError):
            diners = 1
            self.diners_var.set(diners)

        tip_percent = self.tip_var.get() / 100
        tip_amount = bill_amount * tip_percent
        total_with_tip = bill_amount + tip_amount
        per_person = total_with_tip / diners

        self.tip_amount_var.set(f"${tip_amount:.2f}")
        self.total_with_tip_var.set(f"${total_with_tip:.2f}")
        self.per_person_var.set(f"${per_person:.2f}")
        self.status_var.set("")


def main():
    root = tk.Tk()
    app = TipToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
