import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import random
import math
import os


class PicassoApp:
    """
    Modern paint / sketch application built with Tkinter.

    Features included:
    - Mouse drawing
    - Multiple colors with visible selected-color feedback
    - Pen width adjustment
    - Eraser mode
    - Clear canvas
    - Resizable window
    - Undo support (last 5 actions)
    - Save and load drawings
    - Basic shapes: rectangle, oval, line, triangle
    - Spray paint mode
    - Random drawn face generator
    - Optional background grid toggle
    - Keyboard shortcuts

    This project is designed to satisfy the uploaded assignment requirements and adds
    several extra features for a more polished final submission.
    """

    CANVAS_WIDTH = 1100
    CANVAS_HEIGHT = 700
    UNDO_LIMIT = 5

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Picasso Modern Paint Studio")
        self.root.geometry("1400x900")
        self.root.minsize(1100, 760)
        self.root.configure(bg="#121417")

        # ----- Theme / colors -----
        self.bg_main = "#121417"
        self.bg_panel = "#1b1f24"
        self.bg_panel_2 = "#222831"
        self.bg_canvas = "#ffffff"
        self.text = "#e8edf2"
        self.muted = "#95a1ad"
        self.accent = "#5ac8fa"
        self.border = "#2d3742"

        # ----- Application state -----
        self.current_color = "#000000"
        self.pen_size = 6
        self.current_tool = "pen"
        self.last_x = None
        self.last_y = None
        self.preview_item = None
        self.shape_start = None
        self.current_stroke_items = []
        self.undo_stack = []
        self.redo_stack = []
        self.show_grid = tk.BooleanVar(value=False)
        self.fill_shapes = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready")

        # Current brush buttons references for highlighting
        self.color_buttons = {}
        self.tool_buttons = {}

        # ----- Image backing store -----
        self.image = Image.new("RGB", (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.canvas_image_tk = None
        self.canvas_image_id = None

        # ----- Build UI -----
        self.configure_styles()
        self.build_layout()
        self.bind_events()
        self.render_backing_image()
        self.refresh_color_feedback()
        self.set_tool("pen")
        self.update_status("Welcome to Picasso Modern Paint Studio")

    def configure_styles(self):
        """Create a modern ttk style configuration."""
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.style.configure("Main.TFrame", background=self.bg_main)
        self.style.configure("Panel.TFrame", background=self.bg_panel)
        self.style.configure("Panel2.TFrame", background=self.bg_panel_2)
        self.style.configure("Card.TLabelframe", background=self.bg_panel, foreground=self.text)
        self.style.configure("Card.TLabelframe.Label", background=self.bg_panel, foreground=self.text)
        self.style.configure("Title.TLabel", background=self.bg_main, foreground=self.text, font=("Segoe UI", 22, "bold"))
        self.style.configure("Subtitle.TLabel", background=self.bg_main, foreground=self.muted, font=("Segoe UI", 10))
        self.style.configure("Panel.TLabel", background=self.bg_panel, foreground=self.text, font=("Segoe UI", 10))
        self.style.configure("Value.TLabel", background=self.bg_panel, foreground=self.accent, font=("Segoe UI", 10, "bold"))
        self.style.configure("Modern.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        self.style.map("Modern.TButton", background=[("active", "#32404f")])
        self.style.configure("Modern.Horizontal.TScale", background=self.bg_panel)
        self.style.configure("Modern.TCheckbutton", background=self.bg_panel, foreground=self.text)
        self.style.map("Modern.TCheckbutton", background=[("active", self.bg_panel)], foreground=[("active", self.text)])

    def build_layout(self):
        """Create the main interface layout."""
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        header = ttk.Frame(self.root, style="Main.TFrame", padding=(20, 16, 20, 10))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, text="Picasso Modern Paint Studio", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Draw, sketch, spray, place shapes, save work, and generate a random face.",
            style="Subtitle.TLabel"
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.sidebar = ttk.Frame(self.root, style="Panel.TFrame", padding=16)
        self.sidebar.grid(row=1, column=0, sticky="nsw", padx=(18, 12), pady=(0, 18))
        self.sidebar.grid_columnconfigure(0, weight=1)

        canvas_area = ttk.Frame(self.root, style="Main.TFrame")
        canvas_area.grid(row=1, column=1, sticky="nsew", padx=(0, 18), pady=(0, 18))
        canvas_area.grid_rowconfigure(0, weight=1)
        canvas_area.grid_columnconfigure(0, weight=1)

        self.build_sidebar()
        self.build_canvas_area(canvas_area)
        self.build_status_bar()

    def build_sidebar(self):
        """Build the left control panel."""
        title_tools = ttk.LabelFrame(self.sidebar, text="Tools", style="Card.TLabelframe", padding=12)
        title_tools.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        title_tools.grid_columnconfigure((0, 1), weight=1)

        tool_specs = [
            ("Pen", "pen"),
            ("Eraser", "eraser"),
            ("Line", "line"),
            ("Rectangle", "rectangle"),
            ("Oval", "oval"),
            ("Triangle", "triangle"),
            ("Spray", "spray"),
        ]

        for index, (label, tool_name) in enumerate(tool_specs):
            btn = tk.Button(
                title_tools,
                text=label,
                command=lambda t=tool_name: self.set_tool(t),
                bg=self.bg_panel_2,
                fg=self.text,
                activebackground="#33404d",
                activeforeground="white",
                relief="flat",
                bd=0,
                font=("Segoe UI", 10, "bold"),
                padx=10,
                pady=10,
                cursor="hand2",
            )
            btn.grid(row=index // 2, column=index % 2, sticky="ew", padx=4, pady=4)
            self.tool_buttons[tool_name] = btn

        colors_frame = ttk.LabelFrame(self.sidebar, text="Colors", style="Card.TLabelframe", padding=12)
        colors_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        colors_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        preset_colors = [
            ("Black", "#000000"),
            ("Red", "#ff3b30"),
            ("Green", "#34c759"),
            ("Blue", "#007aff"),
            ("Purple", "#af52de"),
            ("Orange", "#ff9500"),
            ("Pink", "#ff2d55"),
            ("Brown", "#8e5a3c"),
        ]

        for idx, (name, color) in enumerate(preset_colors):
            btn = tk.Button(
                colors_frame,
                bg=color,
                activebackground=color,
                width=3,
                height=1,
                relief="flat",
                bd=2,
                cursor="hand2",
                command=lambda c=color: self.choose_preset_color(c),
            )
            btn.grid(row=idx // 4, column=idx % 4, padx=6, pady=6, sticky="ew")
            self.color_buttons[color] = btn

        tk.Button(
            colors_frame,
            text="Custom Color",
            command=self.pick_custom_color,
            bg=self.bg_panel_2,
            fg=self.text,
            activebackground="#33404d",
            activeforeground="white",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=9,
            cursor="hand2",
        ).grid(row=3, column=0, columnspan=4, sticky="ew", padx=4, pady=(8, 4))

        self.current_color_label = ttk.Label(colors_frame, text="Selected: Black", style="Value.TLabel")
        self.current_color_label.grid(row=4, column=0, columnspan=4, sticky="w", padx=4, pady=(8, 0))

        brush_frame = ttk.LabelFrame(self.sidebar, text="Brush Settings", style="Card.TLabelframe", padding=12)
        brush_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        brush_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(brush_frame, text="Pen Width", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        self.size_value = ttk.Label(brush_frame, text=str(self.pen_size), style="Value.TLabel")
        self.size_value.grid(row=0, column=1, sticky="e")

        self.size_slider = ttk.Scale(
            brush_frame,
            from_=1,
            to=40,
            orient="horizontal",
            style="Modern.Horizontal.TScale",
            command=self.on_pen_size_change,
        )
        self.size_slider.set(self.pen_size)
        self.size_slider.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 8))

        ttk.Checkbutton(
            brush_frame,
            text="Fill Shapes",
            variable=self.fill_shapes,
            style="Modern.TCheckbutton",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 4))

        ttk.Checkbutton(
            brush_frame,
            text="Show Grid",
            variable=self.show_grid,
            style="Modern.TCheckbutton",
            command=self.toggle_grid,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        action_frame = ttk.LabelFrame(self.sidebar, text="Actions", style="Card.TLabelframe", padding=12)
        action_frame.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        action_frame.grid_columnconfigure((0, 1), weight=1)

        action_buttons = [
            ("Undo", self.undo),
            ("Clear", self.clear_canvas),
            ("Save", self.save_image),
            ("Load", self.load_image),
            ("Random Face", self.generate_random_face),
            ("New Canvas", self.new_blank_canvas),
        ]

        for idx, (label, command) in enumerate(action_buttons):
            tk.Button(
                action_frame,
                text=label,
                command=command,
                bg=self.bg_panel_2,
                fg=self.text,
                activebackground="#33404d",
                activeforeground="white",
                relief="flat",
                bd=0,
                font=("Segoe UI", 10, "bold"),
                padx=10,
                pady=10,
                cursor="hand2",
            ).grid(row=idx // 2, column=idx % 2, sticky="ew", padx=4, pady=4)

        shortcuts_frame = ttk.LabelFrame(self.sidebar, text="Shortcuts", style="Card.TLabelframe", padding=12)
        shortcuts_frame.grid(row=4, column=0, sticky="ew")

        shortcuts_text = (
            "B = pen\n"
            "E = eraser\n"
            "S = spray\n"
            "U = undo\n"
            "Ctrl+S = save\n"
            "Ctrl+O = load\n"
            "C = clear\n"
            "F = random face"
        )
        ttk.Label(shortcuts_frame, text=shortcuts_text, style="Panel.TLabel", justify="left").grid(row=0, column=0, sticky="w")

    def build_canvas_area(self, parent):
        """Build the main drawing canvas area."""
        canvas_shell = tk.Frame(parent, bg=self.border, bd=0, highlightthickness=0)
        canvas_shell.grid(row=0, column=0, sticky="nsew")
        canvas_shell.grid_rowconfigure(0, weight=1)
        canvas_shell.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            canvas_shell,
            bg=self.bg_canvas,
            highlightthickness=0,
            cursor="crosshair",
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

    def build_status_bar(self):
        """Build the bottom status display."""
        status = tk.Frame(self.root, bg="#0d0f12", height=26)
        status.grid(row=2, column=0, columnspan=2, sticky="ew")
        status.grid_propagate(False)

        self.status_label = tk.Label(
            status,
            textvariable=self.status_var,
            bg="#0d0f12",
            fg="#c6d0da",
            anchor="w",
            font=("Segoe UI", 9),
            padx=12,
        )
        self.status_label.pack(fill="both", expand=True)

    def bind_events(self):
        """Bind mouse and keyboard interactions."""
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        self.root.bind("<Control-s>", lambda event: self.save_image())
        self.root.bind("<Control-o>", lambda event: self.load_image())
        self.root.bind("u", lambda event: self.undo())
        self.root.bind("U", lambda event: self.undo())
        self.root.bind("c", lambda event: self.clear_canvas())
        self.root.bind("C", lambda event: self.clear_canvas())
        self.root.bind("b", lambda event: self.set_tool("pen"))
        self.root.bind("B", lambda event: self.set_tool("pen"))
        self.root.bind("e", lambda event: self.set_tool("eraser"))
        self.root.bind("E", lambda event: self.set_tool("eraser"))
        self.root.bind("s", lambda event: self.set_tool("spray"))
        self.root.bind("S", lambda event: self.set_tool("spray"))
        self.root.bind("f", lambda event: self.generate_random_face())
        self.root.bind("F", lambda event: self.generate_random_face())

    # ------------------------------------------------------------------
    # Utility / state helpers
    # ------------------------------------------------------------------
    def update_status(self, message: str):
        """Update the footer status text."""
        self.status_var.set(message)

    def on_pen_size_change(self, value):
        """Update brush width from the slider."""
        self.pen_size = max(1, int(float(value)))
        self.size_value.config(text=str(self.pen_size))
        self.update_status(f"Pen width set to {self.pen_size}")

    def choose_preset_color(self, color: str):
        """Set the current drawing color from a preset option."""
        self.current_color = color
        if self.current_tool == "eraser":
            self.set_tool("pen")
        self.refresh_color_feedback()
        self.update_status(f"Selected color {color}")

    def pick_custom_color(self):
        """Open the color picker dialog and set a custom color."""
        color = colorchooser.askcolor(title="Choose drawing color", color=self.current_color)[1]
        if color:
            self.current_color = color
            if self.current_tool == "eraser":
                self.set_tool("pen")
            self.refresh_color_feedback()
            self.update_status(f"Custom color selected: {color}")

    def refresh_color_feedback(self):
        """Refresh the selected-color label and button borders."""
        for color, btn in self.color_buttons.items():
            btn.configure(highlightthickness=0, relief="flat", bd=2)
            if color == self.current_color:
                btn.configure(highlightbackground="white", highlightcolor="white", highlightthickness=2)

        color_name = self.current_color.upper()
        self.current_color_label.config(text=f"Selected: {color_name}")

    def set_tool(self, tool_name: str):
        """Activate one of the available tools."""
        self.current_tool = tool_name
        self.highlight_active_tool()
        self.update_status(f"Tool selected: {tool_name.title()}")

    def highlight_active_tool(self):
        """Visually show the currently selected tool."""
        for name, btn in self.tool_buttons.items():
            if name == self.current_tool:
                btn.configure(bg=self.accent, fg="#05131d", activebackground="#86ddff", activeforeground="#05131d")
            else:
                btn.configure(bg=self.bg_panel_2, fg=self.text, activebackground="#33404d", activeforeground="white")

    def get_active_color(self):
        """Return drawing color based on current tool."""
        if self.current_tool == "eraser":
            return "#ffffff"
        return self.current_color

    def render_backing_image(self):
        """Show the PIL image inside the Tkinter canvas."""
        self.canvas_image_tk = ImageTk.PhotoImage(self.image)
        if self.canvas_image_id is None:
            self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.canvas_image_tk)
        else:
            self.canvas.itemconfig(self.canvas_image_id, image=self.canvas_image_tk)
        self.canvas.tag_lower(self.canvas_image_id)
        self.redraw_grid_if_enabled()

    def save_undo_state(self):
        """Save the current image state to the undo stack."""
        self.undo_stack.append(self.image.copy())
        if len(self.undo_stack) > self.UNDO_LIMIT:
            self.undo_stack.pop(0)

    def redraw_grid_if_enabled(self):
        """Draw or remove the grid overlay based on the toggle setting."""
        self.canvas.delete("grid")
        if not self.show_grid.get():
            return

        width = max(self.canvas.winfo_width(), self.CANVAS_WIDTH)
        height = max(self.canvas.winfo_height(), self.CANVAS_HEIGHT)
        spacing = 25

        for x in range(0, width, spacing):
            self.canvas.create_line(x, 0, x, height, fill="#eef2f6", tags="grid")
        for y in range(0, height, spacing):
            self.canvas.create_line(0, y, width, y, fill="#eef2f6", tags="grid")

    def toggle_grid(self):
        """Toggle background grid visibility."""
        self.redraw_grid_if_enabled()
        self.update_status("Grid enabled" if self.show_grid.get() else "Grid disabled")

    # ------------------------------------------------------------------
    # Mouse / drawing events
    # ------------------------------------------------------------------
    def on_mouse_down(self, event):
        """Handle the beginning of a drawing action."""
        self.save_undo_state()
        self.last_x, self.last_y = event.x, event.y
        self.shape_start = (event.x, event.y)
        self.current_stroke_items = []
        self.preview_item = None

        if self.current_tool in ("pen", "eraser"):
            self.draw_dot(event.x, event.y)
        elif self.current_tool == "spray":
            self.spray_at(event.x, event.y)

    def on_mouse_drag(self, event):
        """Handle dragging while drawing or previewing shapes."""
        if self.current_tool in ("pen", "eraser"):
            self.draw_freehand(event.x, event.y)
        elif self.current_tool == "spray":
            self.spray_at(event.x, event.y)
        elif self.current_tool in ("line", "rectangle", "oval", "triangle"):
            self.preview_shape(event.x, event.y)

        self.last_x, self.last_y = event.x, event.y

    def on_mouse_up(self, event):
        """Finalize shapes and reset temporary interaction state."""
        if self.current_tool in ("line", "rectangle", "oval", "triangle") and self.shape_start:
            self.commit_shape(event.x, event.y)

        if self.preview_item:
            self.canvas.delete(self.preview_item)
            self.preview_item = None

        self.last_x = None
        self.last_y = None
        self.shape_start = None
        self.redraw_grid_if_enabled()

    def on_mouse_move(self, event):
        """Display live cursor position in the status bar."""
        self.status_var.set(
            f"Tool: {self.current_tool.title()} | Position: ({event.x}, {event.y}) | Width: {self.pen_size}"
        )

    def draw_dot(self, x, y):
        """Draw a starting dot for pen / eraser presses."""
        radius = self.pen_size / 2
        color = self.get_active_color()
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline=color)
        self.draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color, outline=color)
        self.render_backing_image()

    def draw_freehand(self, x, y):
        """Draw a smooth freehand stroke between last and current points."""
        if self.last_x is None or self.last_y is None:
            self.last_x, self.last_y = x, y
            return

        color = self.get_active_color()
        self.draw.line((self.last_x, self.last_y, x, y), fill=color, width=self.pen_size)
        self.canvas.create_line(
            self.last_x,
            self.last_y,
            x,
            y,
            fill=color,
            width=self.pen_size,
            capstyle=tk.ROUND,
            smooth=True,
        )
        self.render_backing_image()

    def spray_at(self, x, y):
        """Create a spray-paint effect around the cursor position."""
        color = self.get_active_color()
        density = max(12, self.pen_size * 3)
        spread = max(6, self.pen_size * 2)

        for _ in range(density):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(0, spread)
            px = x + math.cos(angle) * radius
            py = y + math.sin(angle) * radius
            size = random.randint(1, max(1, self.pen_size // 4 + 1))
            self.draw.ellipse((px, py, px + size, py + size), fill=color, outline=color)

        self.render_backing_image()

    def preview_shape(self, x2, y2):
        """Preview the current geometric shape while dragging."""
        if not self.shape_start:
            return

        x1, y1 = self.shape_start
        color = self.get_active_color()
        fill = color if self.fill_shapes.get() and self.current_tool != "line" else ""

        if self.preview_item:
            self.canvas.delete(self.preview_item)

        if self.current_tool == "line":
            self.preview_item = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=self.pen_size)
        elif self.current_tool == "rectangle":
            self.preview_item = self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=self.pen_size, fill=fill)
        elif self.current_tool == "oval":
            self.preview_item = self.canvas.create_oval(x1, y1, x2, y2, outline=color, width=self.pen_size, fill=fill)
        elif self.current_tool == "triangle":
            points = self.get_triangle_points(x1, y1, x2, y2)
            self.preview_item = self.canvas.create_polygon(points, outline=color, width=self.pen_size, fill=fill)

    def commit_shape(self, x2, y2):
        """Draw the selected geometric shape permanently to the image."""
        x1, y1 = self.shape_start
        color = self.get_active_color()
        fill = color if self.fill_shapes.get() and self.current_tool != "line" else None

        if self.current_tool == "line":
            self.draw.line((x1, y1, x2, y2), fill=color, width=self.pen_size)
        elif self.current_tool == "rectangle":
            self.draw.rectangle((x1, y1, x2, y2), outline=color, width=self.pen_size, fill=fill)
        elif self.current_tool == "oval":
            self.draw.ellipse((x1, y1, x2, y2), outline=color, width=self.pen_size, fill=fill)
        elif self.current_tool == "triangle":
            points = self.get_triangle_points(x1, y1, x2, y2)
            self.draw.polygon(points, outline=color, fill=fill)
            if not fill:
                self.draw.line([points[0], points[1], points[2], points[0]], fill=color, width=self.pen_size)

        self.render_backing_image()
        self.update_status(f"{self.current_tool.title()} placed")

    @staticmethod
    def get_triangle_points(x1, y1, x2, y2):
        """Return triangle points based on a bounding box drag gesture."""
        top_x = (x1 + x2) / 2
        top_y = y1
        left_x = x1
        left_y = y2
        right_x = x2
        right_y = y2
        return [(top_x, top_y), (left_x, left_y), (right_x, right_y)]

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def undo(self):
        """Restore the previous canvas state, supporting up to the last 5 actions."""
        if not self.undo_stack:
            self.update_status("Nothing to undo")
            return

        self.image = self.undo_stack.pop()
        self.draw = ImageDraw.Draw(self.image)
        self.render_backing_image()
        self.update_status("Undo successful")

    def clear_canvas(self):
        """Clear all drawing content from the canvas."""
        answer = messagebox.askyesno("Clear Canvas", "Are you sure you want to clear the entire canvas?")
        if not answer:
            return

        self.save_undo_state()
        self.new_blank_canvas(show_message=False)
        self.update_status("Canvas cleared")

    def new_blank_canvas(self, show_message=True):
        """Create a fresh blank canvas."""
        self.image = Image.new("RGB", (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.delete("all")
        self.canvas_image_id = None
        self.render_backing_image()
        if show_message:
            self.update_status("New blank canvas created")

    def save_image(self):
        """Save the current drawing to an image file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Drawing",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            self.image.save(file_path)
            self.update_status(f"Saved drawing to {os.path.basename(file_path)}")
            messagebox.showinfo("Saved", f"Drawing saved successfully:\n{file_path}")
        except Exception as exc:
            messagebox.showerror("Save Error", f"Could not save the image.\n\n{exc}")

    def load_image(self):
        """Load an image file onto the drawing canvas."""
        file_path = filedialog.askopenfilename(
            title="Load Drawing",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            loaded = Image.open(file_path).convert("RGB")
            self.save_undo_state()
            self.image.paste("white", [0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT])
            loaded.thumbnail((self.CANVAS_WIDTH, self.CANVAS_HEIGHT))

            offset_x = (self.CANVAS_WIDTH - loaded.width) // 2
            offset_y = (self.CANVAS_HEIGHT - loaded.height) // 2
            self.image.paste(loaded, (offset_x, offset_y))

            self.draw = ImageDraw.Draw(self.image)
            self.render_backing_image()
            self.update_status(f"Loaded image: {os.path.basename(file_path)}")
        except Exception as exc:
            messagebox.showerror("Load Error", f"Could not load the image.\n\n{exc}")

    def generate_random_face(self):
        """Draw a fun randomly generated cartoon face onto the canvas."""
        self.save_undo_state()

        # Face placement and size
        cx = random.randint(280, 820)
        cy = random.randint(180, 520)
        face_w = random.randint(170, 280)
        face_h = random.randint(190, 300)

        skin_tones = [
            "#f6d7c3", "#f1c27d", "#e0ac69", "#c68642", "#8d5524",
            "#ffd8b1", "#edb98a"
        ]
        hair_colors = ["#2c1b10", "#5a3825", "#111111", "#6d4c41", "#c58b3b", "#8b0000"]
        eye_colors = ["#3b82f6", "#22c55e", "#6b7280", "#7c3aed", "#8b5e3c"]

        skin = random.choice(skin_tones)
        hair = random.choice(hair_colors)
        eye = random.choice(eye_colors)

        left = cx - face_w // 2
        top = cy - face_h // 2
        right = cx + face_w // 2
        bottom = cy + face_h // 2

        # Head
        self.draw.ellipse((left, top, right, bottom), fill=skin, outline="#111111", width=4)

        # Hair
        hair_style = random.choice(["cap", "spikes", "side_part", "messy"])
        if hair_style == "cap":
            self.draw.pieslice((left - 6, top - 28, right + 6, cy + 8), start=180, end=360, fill=hair, outline=hair)
        elif hair_style == "spikes":
            points = []
            spikes = random.randint(7, 11)
            for i in range(spikes + 1):
                px = left + (i / spikes) * face_w
                py = top - random.randint(5, 35) if i % 2 else top + random.randint(0, 12)
                points.append((px, py))
            points += [(right, cy - 30), (left, cy - 30)]
            self.draw.polygon(points, fill=hair, outline=hair)
        elif hair_style == "side_part":
            self.draw.pieslice((left - 10, top - 20, right + 10, cy), start=180, end=360, fill=hair, outline=hair)
            self.draw.line((cx + 10, top + 8, cx - 30, cy - 60), fill="#f5f5f5", width=3)
        else:
            for _ in range(140):
                px = random.randint(left, right)
                py = random.randint(top - 10, cy - 20)
                self.draw.ellipse((px, py, px + 7, py + 7), fill=hair, outline=hair)

        # Eyes
        eye_y = cy - face_h * 0.12
        eye_dx = face_w * 0.2
        eye_w = random.randint(26, 40)
        eye_h = random.randint(18, 28)

        for ex in (cx - eye_dx, cx + eye_dx):
            self.draw.ellipse((ex - eye_w, eye_y - eye_h, ex + eye_w, eye_y + eye_h), fill="white", outline="#111111", width=3)
            self.draw.ellipse((ex - 10, eye_y - 10, ex + 10, eye_y + 10), fill=eye, outline=eye)
            self.draw.ellipse((ex - 4, eye_y - 4, ex + 4, eye_y + 4), fill="black", outline="black")
            self.draw.ellipse((ex + 2, eye_y - 6, ex + 5, eye_y - 3), fill="white", outline="white")

        # Eyebrows
        brow_y = eye_y - 36
        arch = random.randint(-8, 8)
        self.draw.line((cx - eye_dx - 30, brow_y, cx - eye_dx + 30, brow_y + arch), fill=hair, width=5)
        self.draw.line((cx + eye_dx - 30, brow_y + arch, cx + eye_dx + 30, brow_y), fill=hair, width=5)

        # Nose
        nose_style = random.choice(["line", "triangle", "round"])
        if nose_style == "line":
            self.draw.line((cx, eye_y + 12, cx - 10, cy + 35, cx + 8, cy + 40), fill="#111111", width=3)
        elif nose_style == "triangle":
            self.draw.polygon([(cx, eye_y + 10), (cx - 16, cy + 38), (cx + 12, cy + 38)], outline="#111111", fill=None)
        else:
            self.draw.arc((cx - 18, cy + 8, cx + 18, cy + 46), start=15, end=170, fill="#111111", width=3)

        # Mouth
        mouth_style = random.choice(["smile", "flat", "open", "grin"])
        mouth_y = cy + face_h * 0.2
        if mouth_style == "smile":
            self.draw.arc((cx - 55, mouth_y - 18, cx + 55, mouth_y + 40), start=15, end=165, fill="#8b0000", width=4)
        elif mouth_style == "flat":
            self.draw.line((cx - 42, mouth_y + 10, cx + 42, mouth_y + 10), fill="#8b0000", width=4)
        elif mouth_style == "open":
            self.draw.ellipse((cx - 26, mouth_y - 2, cx + 26, mouth_y + 42), fill="#7a0019", outline="#111111", width=3)
            self.draw.arc((cx - 20, mouth_y + 10, cx + 20, mouth_y + 36), start=200, end=340, fill="#ff8aa0", width=3)
        else:
            self.draw.arc((cx - 48, mouth_y - 8, cx + 48, mouth_y + 28), start=15, end=165, fill="#8b0000", width=4)
            for i in range(-4, 5):
                x = cx + i * 10
                self.draw.line((x, mouth_y + 2, x, mouth_y + 18), fill="#ffffff", width=2)

        # Ears
        ear_top = cy - 30
        ear_bottom = cy + 45
        self.draw.ellipse((left - 18, ear_top, left + 15, ear_bottom), fill=skin, outline="#111111", width=3)
        self.draw.ellipse((right - 15, ear_top, right + 18, ear_bottom), fill=skin, outline="#111111", width=3)

        # Glasses chance
        if random.random() < 0.4:
            g_y = eye_y
            self.draw.rectangle((cx - eye_dx - 42, g_y - 24, cx - eye_dx + 42, g_y + 24), outline="#111111", width=3)
            self.draw.rectangle((cx + eye_dx - 42, g_y - 24, cx + eye_dx + 42, g_y + 24), outline="#111111", width=3)
            self.draw.line((cx - 18, g_y, cx + 18, g_y), fill="#111111", width=3)

        # Accessories chance
        if random.random() < 0.3:
            # Hat
            hat_color = random.choice(["#1d4ed8", "#9333ea", "#15803d", "#b45309", "#111827"])
            self.draw.rectangle((left + 25, top - 52, right - 25, top + 10), fill=hat_color, outline="#111111", width=3)
            self.draw.rectangle((left + 5, top + 8, right - 5, top + 22), fill=hat_color, outline="#111111", width=3)

        self.render_backing_image()
        self.update_status("Random face generated")


def main():
    root = tk.Tk()
    app = PicassoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
