import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class TipToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GUI Tip Tool")
        self.root.geometry("500x500")
        self.root.resizable(False, False)

        self.bill_var = tk.StringVar()
        self.tip_var = tk.StringVar(value="15")
        self.diners_var = tk.StringVar(value="1")

        self.tip_amount_var = tk.StringVar(value="$0.00")
        self.total_with_tip_var = tk.StringVar(value="$0.00")
        self.per_person_var = tk.StringVar(value="$0.00")
        self.status_var = tk.StringVar(value="Enter a bill amount.")

        self.build_gui()
        self.bind_events()
        self.update_calculation()

    def build_gui(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="Tip Calculator",
            font=("Arial", 20, "bold"),
            bootstyle="info"
        ).pack(pady=(0, 20))

        # Bill section
        ttk.Label(main_frame, text="Total Bill Amount ($):", font=("Arial", 11)).pack(anchor="w")
        self.bill_entry = ttk.Entry(main_frame, textvariable=self.bill_var, font=("Arial", 11))
        self.bill_entry.pack(fill=X, pady=(5, 15))

        # Tip section
        ttk.Label(main_frame, text="Tip Percentage:", font=("Arial", 11)).pack(anchor="w")
        tip_frame = ttk.Frame(main_frame)
        tip_frame.pack(fill=X, pady=(5, 15))

        ttk.Radiobutton(
            tip_frame, text="10%", variable=self.tip_var, value="10", bootstyle="success-toolbutton",
            command=self.update_calculation
        ).pack(side=LEFT, padx=5)

        ttk.Radiobutton(
            tip_frame, text="15%", variable=self.tip_var, value="15", bootstyle="success-toolbutton",
            command=self.update_calculation
        ).pack(side=LEFT, padx=5)

        ttk.Radiobutton(
            tip_frame, text="20%", variable=self.tip_var, value="20", bootstyle="success-toolbutton",
            command=self.update_calculation
        ).pack(side=LEFT, padx=5)

        # Diners section
        ttk.Label(main_frame, text="Number of Diners (1-6):", font=("Arial", 11)).pack(anchor="w")
        self.diners_spinbox = ttk.Spinbox(
            main_frame,
            from_=1,
            to=6,
            textvariable=self.diners_var,
            width=10,
            command=self.update_calculation
        )
        self.diners_spinbox.pack(anchor="w", pady=(5, 20))

        # Results section
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=X, pady=10)

        ttk.Label(results_frame, text="Tip Amount:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=8)
        ttk.Label(results_frame, textvariable=self.tip_amount_var, font=("Arial", 11)).grid(row=0, column=1, sticky="e", pady=8)

        ttk.Label(results_frame, text="Total with Tip:", font=("Arial", 11, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        ttk.Label(results_frame, textvariable=self.total_with_tip_var, font=("Arial", 11)).grid(row=1, column=1, sticky="e", pady=8)

        ttk.Label(results_frame, text="Each Person Pays:", font=("Arial", 11, "bold")).grid(row=2, column=0, sticky="w", pady=8)
        ttk.Label(results_frame, textvariable=self.per_person_var, font=("Arial", 12, "bold"), bootstyle="success").grid(row=2, column=1, sticky="e", pady=8)

        results_frame.columnconfigure(0, weight=1)
        results_frame.columnconfigure(1, weight=1)

        ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Arial", 10),
            bootstyle="danger"
        ).pack(pady=(10, 15))

        ttk.Button(
            main_frame,
            text="Exit",
            command=self.root.destroy,
            bootstyle="danger-outline"
        ).pack()

    def bind_events(self):
        self.bill_var.trace_add("write", lambda *args: self.update_calculation())
        self.diners_var.trace_add("write", lambda *args: self.update_calculation())

        self.bill_entry.bind("<KeyRelease>", lambda event: self.update_calculation())
        self.diners_spinbox.bind("<KeyRelease>", lambda event: self.update_calculation())

    def update_calculation(self):
        bill_text = self.bill_var.get().strip()

        if bill_text == "":
            self.tip_amount_var.set("$0.00")
            self.total_with_tip_var.set("$0.00")
            self.per_person_var.set("$0.00")
            self.status_var.set("Enter a bill amount.")
            return

        try:
            bill_amount = float(bill_text)
            if bill_amount < 0:
                raise ValueError
        except ValueError:
            self.tip_amount_var.set("$0.00")
            self.total_with_tip_var.set("$0.00")
            self.per_person_var.set("$0.00")
            self.status_var.set("Enter a valid non-negative number.")
            return

        try:
            diners = int(self.diners_var.get())
        except ValueError:
            diners = 1

        if diners < 1:
            diners = 1
        if diners > 6:
            diners = 6

        self.diners_var.set(str(diners))

        tip_percent = int(self.tip_var.get()) / 100
        tip_amount = bill_amount * tip_percent
        total_with_tip = bill_amount + tip_amount
        per_person = total_with_tip / diners

        self.tip_amount_var.set(f"${tip_amount:.2f}")
        self.total_with_tip_var.set(f"${total_with_tip:.2f}")
        self.per_person_var.set(f"${per_person:.2f}")
        self.status_var.set("")

def main():
    root = ttk.Window(themename="darkly")
    app = TipToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
