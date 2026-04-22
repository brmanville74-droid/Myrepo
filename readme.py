import os
import time
import threading
import tempfile
import asyncio
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pypdf import PdfReader
import edge_tts
import pygame
from mutagen.mp3 import MP3


class ReadToMeApp:
    def __init__(self, root):
        # Main window setup
        self.root = root
        self.root.title("Read To Me")
        self.root.geometry("1100x720")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # File and speech settings
        self.pdf_path = None
        self.pdf_text = ""
        self.audio_file = os.path.join(tempfile.gettempdir(), "read_to_me_audio.mp3")
        self.current_voice = "en-US-JennyNeural"
        self.voices = {
            "Jenny (US)": "en-US-JennyNeural",
            "Guy (US)": "en-US-GuyNeural",
            "Aria (US)": "en-US-AriaNeural",
            "Davis (US)": "en-US-DavisNeural",
            "Sonia (UK)": "en-GB-SoniaNeural",
            "Ryan (UK)": "en-GB-RyanNeural",
        }

        # Playback state
        self.audio_length = 0.0
        self.playing = False
        self.paused = False
        self.dragging_slider = False
        self.start_time = 0.0
        self.current_position = 0.0
        self.pause_position = 0.0
        self.seek_target = 0.0
        self.start_offset = 0.0
        self.manual_seek_requested = False

        # Highlight tracking
        self.last_highlight_start = None
        self.last_highlight_end = None
        self.follow_job = None

        pygame.mixer.init()

        self.build_ui()
        self.update_ui_loop()

    def build_ui(self):
        """Create the full GUI."""
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=2)
        self.root.grid_rowconfigure(0, weight=1)

        # Left panel for controls
        self.left_frame = ctk.CTkFrame(self.root, corner_radius=18)
        self.left_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.left_frame,
            text="Read To Me",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=15, pady=(20, 10), sticky="ew")

        self.file_label = ctk.CTkLabel(
            self.left_frame,
            text="Current File: None",
            wraplength=280,
            justify="left",
            font=ctk.CTkFont(size=15)
        )
        self.file_label.grid(row=1, column=0, padx=15, pady=10, sticky="ew")

        self.voice_label = ctk.CTkLabel(self.left_frame, text="Voice")
        self.voice_label.grid(row=2, column=0, padx=15, pady=(10, 4), sticky="w")

        self.voice_menu = ctk.CTkOptionMenu(
            self.left_frame,
            values=list(self.voices.keys()),
            command=self.change_voice
        )
        self.voice_menu.set("Jenny (US)")
        self.voice_menu.grid(row=3, column=0, padx=15, pady=(0, 12), sticky="ew")

        self.theme_label = ctk.CTkLabel(self.left_frame, text="Appearance")
        self.theme_label.grid(row=4, column=0, padx=15, pady=(10, 4), sticky="w")

        self.theme_menu = ctk.CTkOptionMenu(
            self.left_frame,
            values=["Dark", "Light"],
            command=self.change_theme
        )
        self.theme_menu.set("Dark")
        self.theme_menu.grid(row=5, column=0, padx=15, pady=(0, 12), sticky="ew")

        self.open_button = ctk.CTkButton(self.left_frame, text="Open PDF", command=self.open_pdf, height=42)
        self.open_button.grid(row=6, column=0, padx=15, pady=(10, 10), sticky="ew")

        self.play_button = ctk.CTkButton(self.left_frame, text="Play", command=self.play_audio, height=42)
        self.play_button.grid(row=7, column=0, padx=15, pady=10, sticky="ew")

        self.pause_button = ctk.CTkButton(self.left_frame, text="Pause / Resume", command=self.pause_resume_audio, height=42)
        self.pause_button.grid(row=8, column=0, padx=15, pady=10, sticky="ew")

        self.stop_button = ctk.CTkButton(
            self.left_frame,
            text="Stop",
            command=self.stop_audio,
            fg_color="#d9534f",
            hover_color="#c9302c",
            height=42
        )
        self.stop_button.grid(row=9, column=0, padx=15, pady=10, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.left_frame,
            text="Status: Waiting for a PDF",
            wraplength=280,
            justify="left"
        )
        self.status_label.grid(row=10, column=0, padx=15, pady=(18, 8), sticky="ew")

        self.time_label = ctk.CTkLabel(
            self.left_frame,
            text="Elapsed: 00:00   Remaining: 00:00",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.time_label.grid(row=11, column=0, padx=15, pady=(8, 10), sticky="ew")

        self.progress_slider = ctk.CTkSlider(self.left_frame, from_=0, to=100, command=self.slider_preview)
        self.progress_slider.set(0)
        self.progress_slider.grid(row=12, column=0, padx=15, pady=(8, 8), sticky="ew")
        self.progress_slider.bind("<ButtonPress-1>", self.on_slider_press)
        self.progress_slider.bind("<ButtonRelease-1>", self.on_slider_release)

        self.slider_info = ctk.CTkLabel(self.left_frame, text="Use slider to move through playback")
        self.slider_info.grid(row=13, column=0, padx=15, pady=(0, 15), sticky="ew")

        self.drop_label = ctk.CTkLabel(
            self.left_frame,
            text="Paste or drop a PDF path below if your setup supports it.",
            wraplength=280,
            justify="left"
        )
        self.drop_label.grid(row=14, column=0, padx=15, pady=(5, 6), sticky="ew")

        self.drop_entry = ctk.CTkEntry(self.left_frame, placeholder_text="Paste PDF path here")
        self.drop_entry.grid(row=15, column=0, padx=15, pady=(0, 8), sticky="ew")

        self.load_drop_button = ctk.CTkButton(self.left_frame, text="Load Path", command=self.load_from_drop_entry, height=38)
        self.load_drop_button.grid(row=16, column=0, padx=15, pady=(0, 20), sticky="ew")

        # Right panel for extracted text
        self.right_frame = ctk.CTkFrame(self.root, corner_radius=18)
        self.right_frame.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)

        self.text_title = ctk.CTkLabel(
            self.right_frame,
            text="Extracted PDF Text",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.text_title.grid(row=0, column=0, padx=15, pady=(18, 10), sticky="w")

        self.textbox = ctk.CTkTextbox(self.right_frame, wrap="word", font=("Arial", 16))
        self.textbox.grid(row=1, column=0, padx=15, pady=10, sticky="nsew")
        self.textbox.insert("1.0", "Open a PDF to see the extracted text here.")
        self.textbox.tag_config("highlight", background="#f4d35e", foreground="black")

        self.feature_note = ctk.CTkLabel(
            self.right_frame,
            text="Features included: multiple voices, dark/light mode, time display, seek slider, current file display, path loading, and smoother text highlighting.",
            wraplength=700,
            justify="left"
        )
        self.feature_note.grid(row=3, column=0, padx=15, pady=(0, 18), sticky="ew")

    def change_voice(self, selected_voice):
        """Change the text-to-speech voice."""
        self.current_voice = self.voices[selected_voice]
        self.status_label.configure(text=f"Status: Voice changed to {selected_voice}")

    def change_theme(self, selected_theme):
        """Switch between dark and light mode."""
        ctk.set_appearance_mode(selected_theme.lower())
        self.status_label.configure(text=f"Status: {selected_theme} mode enabled")

    def open_pdf(self):
        """Open a file dialog and let the user choose a PDF."""
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.load_pdf(file_path)

    def load_from_drop_entry(self):
        """Load a PDF from the path entry box."""
        path = self.drop_entry.get().strip().strip("{}")
        if not path:
            messagebox.showwarning("No path", "Please paste a PDF path first.")
            return
        if not os.path.exists(path):
            messagebox.showerror("Invalid path", "That file path does not exist.")
            return
        if not path.lower().endswith(".pdf"):
            messagebox.showerror("Wrong file", "Please provide a PDF file.")
            return
        self.load_pdf(path)

    def load_pdf(self, path):
        """Load the PDF, extract its text, and show it in the textbox."""
        try:
            self.stop_audio()
            self.pdf_path = path
            self.pdf_text = self.extract_text_from_pdf(path)

            self.textbox.delete("1.0", "end")
            if not self.pdf_text.strip():
                self.textbox.insert("1.0", "No readable text found in this PDF.")
                messagebox.showwarning("No text found", "This PDF did not contain readable text.")
                return

            self.textbox.insert("1.0", self.pdf_text)
            self.file_label.configure(text=f"Current File: {os.path.basename(path)}")
            self.status_label.configure(text="Status: PDF loaded successfully")
            self.progress_slider.set(0)
            self.time_label.configure(text="Elapsed: 00:00   Remaining: 00:00")
            self.reset_highlight_tracking()
        except Exception as error:
            messagebox.showerror("PDF Error", f"Could not load PDF:\n{error}")

    def extract_text_from_pdf(self, path):
        """Read each page from the PDF and combine all text into one string."""
        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)

    async def generate_tts_file(self, text, output_file):
        """Generate an MP3 file from the PDF text using edge-tts."""
        communicate = edge_tts.Communicate(text=text, voice=self.current_voice)
        await communicate.save(output_file)

    def play_audio(self):
        """Start playing the audio, or resume it if paused."""
        if not self.pdf_text.strip():
            messagebox.showwarning("No PDF", "Please load a PDF before pressing Play.")
            return

        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
            self.playing = True
            self.start_time = time.time() - self.pause_position
            self.status_label.configure(text="Status: Audio resumed")
            self.start_follow_loop()
            return

        if self.playing:
            return

        self.status_label.configure(text="Status: Generating speech audio...")
        threading.Thread(target=self.generate_and_play_audio, daemon=True).start()

    def generate_and_play_audio(self):
        """Create the TTS audio file and begin playback."""
        try:
            asyncio.run(self.generate_tts_file(self.pdf_text, self.audio_file))
            self.audio_length = MP3(self.audio_file).info.length
            pygame.mixer.music.load(self.audio_file)

            self.start_offset = self.seek_target if self.manual_seek_requested else 0.0
            pygame.mixer.music.play(start=self.start_offset)

            self.start_time = time.time() - self.start_offset
            self.current_position = self.start_offset
            self.pause_position = self.start_offset
            self.playing = True
            self.paused = False
            self.manual_seek_requested = False

            self.root.after(0, lambda: self.status_label.configure(text="Status: Playing audio"))
            self.root.after(0, self.start_follow_loop)
        except Exception as error:
            self.root.after(0, lambda: messagebox.showerror("Audio Error", f"Could not create or play audio:\n{error}"))
            self.root.after(0, lambda: self.status_label.configure(text="Status: Audio failed to play"))

    def pause_resume_audio(self):
        """Pause if the audio is playing, or resume if paused."""
        if self.playing and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True
            self.playing = False
            self.pause_position = self.current_position
            self.cancel_follow_loop()
            self.status_label.configure(text="Status: Audio paused")
        elif self.paused:
            self.play_audio()

    def stop_audio(self):
        """Stop playback and reset all playback-related values."""
        pygame.mixer.music.stop()
        self.cancel_follow_loop()
        self.playing = False
        self.paused = False
        self.current_position = 0.0
        self.pause_position = 0.0
        self.start_offset = 0.0
        self.seek_target = 0.0
        self.manual_seek_requested = False
        self.progress_slider.set(0)
        self.clear_highlight()
        self.reset_highlight_tracking()
        if self.pdf_text.strip():
            self.status_label.configure(text="Status: Stopped")

    def slider_preview(self, value):
        """Show the elapsed and remaining time while the slider is moved."""
        if self.audio_length <= 0:
            return
        preview_seconds = (float(value) / 100.0) * self.audio_length
        remaining = max(0.0, self.audio_length - preview_seconds)
        self.time_label.configure(
            text=f"Elapsed: {self.format_time(preview_seconds)}   Remaining: {self.format_time(remaining)}"
        )

    def on_slider_press(self, event):
        """Mark that the user has started dragging the slider."""
        self.dragging_slider = True

    def on_slider_release(self, event):
        """Seek to the new playback location after the slider is released."""
        self.dragging_slider = False
        if self.audio_length <= 0:
            return

        self.seek_target = (self.progress_slider.get() / 100.0) * self.audio_length
        self.current_position = self.seek_target
        self.pause_position = self.seek_target
        self.manual_seek_requested = True

        if self.playing or self.paused:
            pygame.mixer.music.stop()
            self.cancel_follow_loop()
            self.playing = False
            self.paused = False
            self.status_label.configure(text="Status: Seeking...")
            self.play_audio()
        else:
            self.update_text_tracking_from_position()
            self.status_label.configure(text="Status: Seek position updated")

    def update_ui_loop(self):
        """Keep the time display and slider updated during playback."""
        if self.playing:
            self.current_position = max(0.0, time.time() - self.start_time)

            if self.audio_length > 0 and not self.dragging_slider:
                percent = min(100.0, (self.current_position / self.audio_length) * 100.0)
                self.progress_slider.set(percent)

            remaining = max(0.0, self.audio_length - self.current_position)
            self.time_label.configure(
                text=f"Elapsed: {self.format_time(self.current_position)}   Remaining: {self.format_time(remaining)}"
            )

            if not pygame.mixer.music.get_busy() and not self.paused:
                self.playing = False
                self.cancel_follow_loop()
                self.current_position = self.audio_length
                self.progress_slider.set(100)
                self.time_label.configure(
                    text=f"Elapsed: {self.format_time(self.audio_length)}   Remaining: 00:00"
                )
                self.status_label.configure(text="Status: Playback finished")
                self.clear_highlight()
                self.reset_highlight_tracking()

        self.root.after(250, self.update_ui_loop)

    def start_follow_loop(self):
        """Start the highlight update loop without creating duplicate loops."""
        self.cancel_follow_loop()
        self.follow_text_loop()

    def cancel_follow_loop(self):
        """Stop any scheduled highlight loop."""
        if self.follow_job is not None:
            self.root.after_cancel(self.follow_job)
            self.follow_job = None

    def follow_text_loop(self):
        """Update the highlighted section while audio is playing."""
        if not self.playing:
            self.follow_job = None
            return

        self.update_text_tracking_from_position()
        self.follow_job = self.root.after(700, self.follow_text_loop)

    def update_text_tracking_from_position(self):
        """
        Estimate where the speech currently is in the text and highlight that area.
        This is time-based, so it will not be perfect word-for-word, but it is smoother.
        """
        if not self.pdf_text.strip() or self.audio_length <= 0:
            return

        ratio = max(0.0, min(1.0, self.current_position / self.audio_length))
        char_index = int(len(self.pdf_text) * ratio)

        # Highlight a chunk instead of tiny rapidly changing characters.
        chunk_size = 60
        start_char = max(0, char_index)
        end_char = min(len(self.pdf_text), start_char + chunk_size)

        start_index = f"1.0+{start_char}c"
        end_index = f"1.0+{end_char}c"

        # Only redraw the highlight when the highlighted area changes.
        if (start_index, end_index) != (self.last_highlight_start, self.last_highlight_end):
            self.clear_highlight()
            self.textbox.tag_add("highlight", start_index, end_index)
            self.textbox.see(start_index)
            self.last_highlight_start = start_index
            self.last_highlight_end = end_index

    def clear_highlight(self):
        """Remove the current highlight from the textbox."""
        self.textbox.tag_remove("highlight", "1.0", "end")

    def reset_highlight_tracking(self):
        """Clear saved highlight positions so the next update starts fresh."""
        self.last_highlight_start = None
        self.last_highlight_end = None

    def format_time(self, seconds):
        """Convert seconds to mm:ss format."""
        seconds = int(max(0, seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"


if __name__ == "__main__":
    root = ctk.CTk()
    app = ReadToMeApp(root)
    root.mainloop()
