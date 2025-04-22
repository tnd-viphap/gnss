"""
ctk_components Module
--------------------

This module contains the implementation of various customtkinter components.
These components are designed to provide additional functionality and a modern look to your customtkinter applications.

Classes:
--------
- CTkAlert
- CTkBanner
- CTkNotification
- CTkCard
- CTkCarousel
- CTkInput
- CTkLoader
- CTkPopupMenu
- CTkProgressPopup
- CTkTreeview

Each class corresponds to a unique widget that can be used in your customtkinter application.

Author: rudymohammadbali (https://github.com/rudymohammadbali)
Date: 2024/02/26
Version: 20240226
"""

import io
import os
import re
import sys
import threading
from datetime import datetime
from queue import Empty, Queue
from tkinter import filedialog, ttk

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk
from tkinterdnd2 import DND_FILES

from common.helpers import Signal
import common.parser as cfg
from modules.datastream.ftp import FTPDownloader
from common.fonts.font_manager import FontManager

from .src.util.CTkGif import CTkGif
from .src.util.py_win_style import set_opacity
from .src.util.window_position import center_window, place_frame

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
ICON_DIR = os.path.join(CURRENT_PATH, "src", "icons")

ICON_PATH = {
    "close": (os.path.join(ICON_DIR, "close_black.png"), os.path.join(ICON_DIR, "close_white.png")),
    "images": list(os.path.join(ICON_DIR, f"image{i}.jpg") for i in range(1, 4)),
    "eye1": (os.path.join(ICON_DIR, "eye1_black.png"), os.path.join(ICON_DIR, "eye1_white.png")),
    "eye2": (os.path.join(ICON_DIR, "eye2_black.png"), os.path.join(ICON_DIR, "eye2_white.png")),
    "info": os.path.join(ICON_DIR, "info.png"),
    "warning": os.path.join(ICON_DIR, "warning.png"),
    "error": os.path.join(ICON_DIR, "error.png"),
    "left": os.path.join(ICON_DIR, "left.png"),
    "right": os.path.join(ICON_DIR, "right.png"),
    "warning2": os.path.join(ICON_DIR, "warning2.png"),
    "loader": os.path.join(ICON_DIR, "loader.gif"),
    "icon": os.path.join(ICON_DIR, "icon.png"),
    "arrow": os.path.join(ICON_DIR, "arrow.png"),
    "image": os.path.join(ICON_DIR, "image.png"),
}

DEFAULT_BTN = {
    "fg_color": "transparent",
    "hover": False,
    "compound": "left",
    "anchor": "w",
}

LINK_BTN = {**DEFAULT_BTN, "width": 70, "height": 25, "text_color": "#3574F0"}
BTN_LINK = {**DEFAULT_BTN, "width": 20, "height": 20, "text_color": "#3574F0", "font": ("", 13, "underline")}
ICON_BTN = {**DEFAULT_BTN, "width": 30, "height": 30}
BTN_OPTION = {**DEFAULT_BTN, "text_color": ("black", "white"), "corner_radius": 5, "hover_color": ("gray90", "gray25")}
btn = {**DEFAULT_BTN, "width": 230, "height": 50, "text_color": ("#000000", "#FFFFFF"), "font": ("", 13)}
btn_active = {**btn, "fg_color": (ctk.ThemeManager.theme["CTkButton"]["fg_color"]), "hover": True}
btn_footer = {**btn, "fg_color": ("#EBECF0", "#393B40"), "hover_color": ("#DFE1E5", "#43454A"), "corner_radius": 0}

DEFAULT_ICON_ONLY_BTN = {**DEFAULT_BTN, "height": 50, "text_color": ("#000000", "#FFFFFF"), "anchor": "center"}
btn_icon_only = {**DEFAULT_ICON_ONLY_BTN, "width": 70}
btn_icon_only_active = {**btn_icon_only, "fg_color": (ctk.ThemeManager.theme["CTkButton"]["fg_color"]), "hover": True}
btn_icon_only_footer = {**DEFAULT_ICON_ONLY_BTN, "width": 80, "fg_color": ("#EBECF0", "#393B40"),
                        "hover_color": ("#DFE1E5", "#43454A"), "corner_radius": 0}

TEXT = "Some quick example text to build on the card title and make up the bulk of the card's content."


class DeviceSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent, device_db):
        super().__init__(parent)

        # Initialize signals
        self.status_signal = Signal()
        self.status_signal.connect(self.update_status)
        self.progress_signal = Signal()
        self.progress_signal.connect(self.update_progress)
        self.error_signal = Signal()
        self.error_signal.connect(self.handle_error)
        
        # Configure dialog window
        self.title("Get Data")
        self.geometry("330x180")
        self.iconbitmap("assets/Logo.ico")
        self.resizable(False, False)
        self.transient(parent)  # Make dialog modal
        self.grab_set()  # Make dialog modal
        
        # Center the dialog
        self.center_dialog()
        
        # Store device database
        self.device_db = device_db
        
        # Create main container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create device selection frame
        device_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        device_frame.pack(fill="x", pady=(0, 20))
        
        # Device Database label
        device_label = ctk.CTkLabel(
            device_frame,
            text="Select Device",
            font=parent.font_manager.get_font("content-body")
        )
        device_label.pack(side="top", padx=(0, 10), anchor="w")
        
        # Create a frame for dropdown and buttons
        controls_frame = ctk.CTkFrame(device_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(5, 0))
        
        # Device selection dropdown
        self.device_var = ctk.StringVar(value="All")
        self.device_dropdown = ctk.CTkOptionMenu(
            controls_frame,
            values=self.get_device_options(),
            variable=self.device_var,
            font=parent.font_manager.get_font("content-body"),
            width=200
        )
        self.device_dropdown.pack(side="left", padx=(0, 10))
        
        # Fetch button
        self.fetch_image = ctk.CTkImage(light_image=Image.open("assets/Fetch.png"),
                                         dark_image=Image.open("assets/Fetch.png"),
                                         size=(20, 20))
        self.fetch_button = ctk.CTkButton(
            controls_frame,
            text="",
            image=self.fetch_image,
            width=28,
            font=parent.font_manager.get_font("content-body"),
            command=self.fetch_data
        )
        self.fetch_button.pack(side="left", padx=(0, 10))
        
        # Cancel button
        self.cancel_image = ctk.CTkImage(light_image=Image.open("assets/Disconnect.png"),
                                         dark_image=Image.open("assets/Disconnect.png"),
                                         size=(20, 20))
        self.cancel_button = ctk.CTkButton(
            controls_frame,
            text="",
            image=self.cancel_image,
            width=28,
            font=parent.font_manager.get_font("content-body"),
            command=self.destroy
        )
        self.cancel_button.pack(side="left")
        
        # Bind Enter key to fetch data
        self.bind('<Return>', lambda e: self.fetch_data())

        # Create status label (initially hidden)
        self.status_label = ctk.CTkLabel(
            self.container,
            text="Progress:",
            font=parent.font_manager.get_font("content-body")
        )
        self.status_label.pack(side="top", pady=(0, 0), anchor="w")
        
        # Create progress bar (initially hidden)
        self.progress_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=(0, 0), expand=True)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="0%",
            font=parent.font_manager.get_font("content-body"),
            width=50
        )
        self.progress_label.pack(side="right")
        
        # Create queue for thread communication
        self.queue = Queue()
        
        # Status animation variables
        self.status_dots = 0
        self.status_animation_id = None
        
    def center_dialog(self):
        """Center the dialog on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
    def get_device_options(self):
        """Generate device options from device database"""
        if not self.device_db:
            return ["Error: Device database not loaded"]
            
        options = ["All"]
        
        # Add individual devices
        if "ftp" in self.device_db:
            # Add Base
            if "base" in self.device_db["ftp"]:
                options.append(self.device_db["ftp"]["base"]["local_dir"])
            
            # Add Rovers
            if "rovers1" in self.device_db["ftp"]:
                for rover in self.device_db["ftp"]["rovers1"]:
                    options.append(rover["local_dir"])
            if "rovers2" in self.device_db["ftp"]:
                for rover in self.device_db["ftp"]["rovers2"]:
                    options.append(rover["local_dir"])
        
        # Add combinations
        if "base" in self.device_db["ftp"]:
            if "rovers1" in self.device_db["ftp"]:
                options.append(f"{self.device_db['ftp']['base']['local_dir']} + {self.device_db['ftp']['rovers1'][0]['local_dir']}")
            if "rovers2" in self.device_db["ftp"]:
                options.append(f"{self.device_db['ftp']['base']['local_dir']} + {self.device_db['ftp']['rovers2'][0]['local_dir']}")
        
        return options
        
    def update_ui(self):
        """Update UI based on thread messages"""
        try:
            while True:
                message = self.queue.get_nowait()
                if message["type"] == "progress":
                    self.progress_bar.set(message["value"])
                elif message["type"] == "status":
                    self.status_label.configure(text=message["text"])
                elif message["type"] == "error":
                    print(message["text"])
                    self.enable_buttons()
                elif message["type"] == "complete":
                    self.destroy()
        except Empty:
            pass
        finally:
            self.after(100, self.update_ui)
    
    def update_progress(self, value):
        """Update the progress bar and percentage label"""
        self.progress_bar.set(value)
        self.progress_label.configure(text=f"{int(value * 100)}%")

    def update_status(self, text):
        """Update the status label"""
        self.status_label.configure(text=text)
            
    def enable_buttons(self):
        """Enable all buttons"""
        self.fetch_button.configure(state="normal", width=28)
        self.cancel_button.configure(state="normal", width=28)
        self.device_dropdown.configure(state="normal")
        
    def disable_buttons(self):
        """Disable all buttons"""
        self.fetch_button.configure(state="disabled", width=28)
        self.cancel_button.configure(state="disabled", width=28)
        self.device_dropdown.configure(state="disabled")

    def handle_error(self, error_msg):
        """Handle error signal"""
        print(f"Error: {error_msg}")
        self.enable_buttons()
        
    def animate_status(self):
        """Animate the status label dots"""
        self.status_dots = (self.status_dots + 1) % 4
        dots = "." * self.status_dots
        self.status_label.configure(text=f"Progress: Fetching data{dots}")
        self.status_animation_id = self.after(500, self.animate_status)

    def stop_status_animation(self):
        """Stop the status label animation"""
        if self.status_animation_id is not None:
            self.after_cancel(self.status_animation_id)
            self.status_animation_id = None

    def fetch_data(self):
        """Handle data fetching based on selected device"""
        selected_device = self.device_var.get()
        
        if selected_device == "Error: Device database not loaded":
            print("Device database not loaded. Please check the configuration.")
            return
        
        # Disable UI elements
        self.disable_buttons()
        
        # Show progress bar and status
        self.status_label.pack(side="top", pady=(0, 0), anchor="w")
        self.status_label.configure(text="Progress: Fetching data")
        self.progress_frame.pack(fill="x", pady=(0, 0))
        
        # Initialize animation variables
        self.status_dots = 0
        self.status_animation_id = self.after(500, self.animate_status)
        
        # Start UI update loop
        self.update_ui()
        
        # Start processing thread
        thread = threading.Thread(
            target=self.process_data,
            args=(selected_device,),
            daemon=True
        )
        thread.start()

    def download_base_data(self, start_date=None, start_time=None):
        downloader = FTPDownloader(cfg.FTP_BASE_SETTINGS, self.progress_signal, self.error_signal, self.status_signal)
        self.status_signal.emit("Progress: Base connected")
        base_file_paths = downloader.get_unprocessed_files_in_remote_path(
            cfg.FTP_BASE_SETTINGS["data_dir"], 
            cfg.FTP_BASE_SETTINGS["prefix"], 
            cfg.BASE_DATA_DIR
        )
        base_local_file_paths = downloader.generate_local_file_paths(cfg.BASE_DATA_DIR, base_file_paths, start_date, start_time)
        downloader.download_files(base_file_paths, base_local_file_paths)
        downloader.disconnect()
        self.status_signal.emit("Progress: Base files downloaded")

    def download_rover_data(self, settings_list, start_date=None, start_time=None):
        for settings in settings_list:
            print(settings)
            rover_local_dir = os.path.join(cfg.DATA_DIR, settings["local_dir"])
            rover_data_dir = os.path.join(rover_local_dir, "raw")

            downloader = FTPDownloader(settings, self.progress_signal, self.error_signal, self.status_signal)
            self.status_signal.emit(f"Progress: {settings['local_dir']} connected")
            rover_file_paths = downloader.get_unprocessed_files_in_remote_path(
                settings["data_dir"], 
                settings["prefix"], 
                rover_data_dir
            )
            rover_local_file_paths = downloader.generate_local_file_paths(rover_data_dir, rover_file_paths, start_date, start_time)
            downloader.download_files(rover_file_paths, rover_local_file_paths)
            downloader.disconnect()
            self.status_signal.emit(f"Progress: {settings['local_dir']} files downloaded")

    def process_data(self, selected_device, start_date=None, start_time=None):
        """Process data in a separate thread"""
        err = None
        try:
            if selected_device == "All":
                self.download_base_data(start_date, start_time)
                self.download_rover_data(cfg.FTP_ROVERS1_SETTINGS, start_date, start_time)
                self.download_rover_data(cfg.FTP_ROVERS2_SETTINGS, start_date, start_time)
            elif selected_device == "Base":
                self.download_base_data(start_date, start_time)
            elif selected_device == "Rover1":
                self.download_rover_data(cfg.FTP_ROVERS1_SETTINGS, start_date, start_time)
            elif selected_device == "Rover2":
                self.download_rover_data(cfg.FTP_ROVERS2_SETTINGS, start_date, start_time)
            elif selected_device == "Base+Rover1":
                self.download_base_data(start_date, start_time)
                self.download_rover_data(cfg.FTP_ROVERS1_SETTINGS, start_date, start_time)
            elif selected_device == "Base+Rover2":
                self.download_base_data(start_date, start_time)
                self.download_rover_data(cfg.FTP_ROVERS2_SETTINGS, start_date, start_time)     
        except Exception as e:
            self.error_signal.emit(f"Error during data fetching: {str(e)}")
            err = "Cannot connect to device"
        finally:
            # Stop status animation and set final status
            self.stop_status_animation()
            self.status_label.configure(text=str(err) if err else "Progress: Done")
            self.enable_buttons()
            return
        
class DragDropEntry(ctk.CTkEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Enable drag and drop
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.drop_file)
        
        # Bind focus events for visual feedback
        self.bind('<FocusIn>', self.on_focus_in)
        self.bind('<FocusOut>', self.on_focus_out)
        
    def drop_file(self, event):
        """Handle file drop event"""
        file_path = event.data
        # Remove curly braces if present (Windows)
        file_path = file_path.strip('{}')
        # Remove file:/// prefix if present
        file_path = file_path.replace('file:///', '')
        self.delete(0, 'end')
        self.insert(0, file_path)
        
    def on_focus_in(self, event):
        """Visual feedback when entry is focused"""
        self.configure(border_color=self._fg_color)
        
    def on_focus_out(self, event):
        """Reset visual feedback when entry loses focus"""
        self.configure(border_color=self._border_color)

class BatchDragDropEntry(DragDropEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_year = datetime.now().year
        
    def drop_file(self, event):
        """Handle file drop event with date extraction"""
        file_path = event.data
        # Remove curly braces if present (Windows)
        file_path = file_path.strip('{}')
        # Remove file:/// prefix if present
        file_path = file_path.replace('file:///', '')
        
        # Get just the filename without path
        file_name = os.path.basename(file_path)
        
        # Check if file has extension
        if '.' in file_name:
            print("Invalid File: Please select a file without extension")
            return
        
        # Extract date and hour pattern
        # Example: Base_3600_0312a -> date: 0312, hour: a
        match = re.search(r'_(\d{4})([a-z])$', file_name)
        if match:
            date_str = match.group(1)
            hour_pattern = match.group(2)
            
            # Convert date string to DD/MM/YYYY
            day = date_str[:2]
            month = date_str[2:]
            year = self.current_year
            
            # Convert hour pattern to actual hour (a=8, b=9, etc.)
            hour = ord(hour_pattern) - ord('a') + 8
            
            # Format the date and time
            formatted_date = f"{day}/{month}/{year} {hour:02d}:00"
            self.delete(0, 'end')
            self.insert(0, formatted_date)
        else:
            print("Invalid File Format: File name must follow the pattern: Base_3600_MMDDx where MMDD is the date and x is the hour (a-z)")
            self.delete(0, 'end')
            self.insert(0, file_name)

    def browse_file(self, entry_widget):
        """Open file dialog and set the selected path to the entry widget"""
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            
            # Check if file has extension
            if '.' in file_name:
                print("Invalid File: Please select TPS file")
                return
            
            # Extract date and hour pattern
            match = re.search(r'_(\d{4})([a-z])$', file_name)
            if match:
                date_str = match.group(1)
                hour_pattern = match.group(2)
                
                # Convert date string to DD/MM/YYYY
                day = date_str[:2]
                month = date_str[2:]
                year = self.current_year
                
                # Convert hour pattern to actual hour (a=8, b=9, etc.)
                hour = ord(hour_pattern) - ord('a') + 8
                
                # Format the date and time
                formatted_date = f"{day}/{month}/{year} {hour:02d}:00"
                self.delete(0, 'end')
                self.insert(0, formatted_date)
            else:
                print("Invalid File Format: File name must follow the pattern: Base_3600_MMDDx where MMDD is the date and x is the hour (a-z)")
                self.delete(0, 'end')
                self.insert(0, file_name)

class CTkMessageBox(ctk.CTkToplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        
        # Configure window
        self.title(title)
        self.geometry("400x100")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.center_dialog()

        # Font manager
        self.font_manager = FontManager()
        
        # Create main container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Error icon
        self.error_image = ctk.CTkImage(
            light_image=Image.open("assets/error.png"),
            dark_image=Image.open("assets/error.png"),
            size=(20, 20)
        )
        
        # Message label with icon
        self.message_label = ctk.CTkLabel(
            self.container,
            text=message,
            font=self.font_manager.get_font("content-body"),
            image=self.error_image,
            compound="left",
            wraplength=250
        )
        self.message_label.pack(pady=(0, 20))
        
        # Button frame
        button_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # Center the button frame
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # OK button
        self.ok_button = ctk.CTkButton(
            button_frame,
            text="OK",
            width=100,
            command=lambda: self.button_event("OK")
        )
        self.ok_button.grid(row=0, column=0, padx=(0, 5))
        
        # Cancel button
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            command=lambda: self.button_event("Cancel")
        )
        self.cancel_button.grid(row=0, column=1, padx=(5, 0))
        
        # Bind Enter key to OK button
        self.bind('<Return>', lambda e: self.button_event("OK"))
        
        # Set focus to OK button
        self.ok_button.focus_set()
        
        # Initialize result
        self.result = None
        
    def center_dialog(self):
        """Center the dialog on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
    def button_event(self, button):
        """Handle button click"""
        self.result = button
        self.destroy()
        
    def get(self):
        """Get the dialog result"""
        if self.winfo_exists():
            self.master.wait_window(self)
        return self.result


class CTkAlert(ctk.CTkToplevel):
    def __init__(self, state: str = "info", title: str = "Title",
                 body_text: str = "Body text", btn1: str = "OK", btn2: str = "Cancel"):
        super().__init__()
        self.old_y = None
        self.old_x = None
        self.width = 420
        self.height = 200
        center_window(self, self.width, self.height)
        self.resizable(False, False)
        self.overrideredirect(True)
        self.lift()

        self.x = self.winfo_x()
        self.y = self.winfo_y()
        self.event = None

        if sys.platform.startswith("win"):
            self.transparent_color = self._apply_appearance_mode(self.cget("fg_color"))
            self.attributes("-transparentcolor", self.transparent_color)

        self.bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.frame_top = ctk.CTkFrame(self, corner_radius=5, width=self.width,
                                      border_width=1,
                                      bg_color=self.transparent_color, fg_color=self.bg_color)
        self.frame_top.grid(sticky="nsew")
        self.frame_top.bind("<B1-Motion>", self.move_window)
        self.frame_top.bind("<ButtonPress-1>", self.old_xy_set)
        self.frame_top.grid_columnconfigure(0, weight=1)
        self.frame_top.grid_rowconfigure(1, weight=1)

        if state not in ICON_PATH or ICON_PATH[state] is None:
            self.icon = ctk.CTkImage(Image.open(ICON_PATH["info"]), Image.open(ICON_PATH["info"]), (30, 30))
        else:
            self.icon = ctk.CTkImage(Image.open(ICON_PATH[state]), Image.open(ICON_PATH[state]), (30, 30))

        self.close_icon = ctk.CTkImage(Image.open(ICON_PATH["close"][0]), Image.open(ICON_PATH["close"][1]), (20, 20))

        self.title_label = ctk.CTkLabel(self.frame_top, text=f"  {title}", font=("", 18), image=self.icon,
                                        compound="left")
        self.title_label.grid(row=0, column=0, sticky="w", padx=15, pady=20)
        self.title_label.bind("<B1-Motion>", self.move_window)
        self.title_label.bind("<ButtonPress-1>", self.old_xy_set)

        self.close_btn = ctk.CTkButton(self.frame_top, text="", image=self.close_icon, width=20, height=20, hover=False,
                                       fg_color="transparent", command=self.button_event)
        self.close_btn.grid(row=0, column=1, sticky="ne", padx=10, pady=10)

        self.message = ctk.CTkLabel(self.frame_top,
                                    text=body_text,
                                    justify="left", anchor="w", wraplength=self.width - 30)
        self.message.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="nsew", columnspan=2)

        self.btn_1 = ctk.CTkButton(self.frame_top, text=btn1, width=120, command=lambda: self.button_event(btn1),
                                   text_color="white")
        self.btn_1.grid(row=2, column=0, padx=(10, 5), pady=20, sticky="e")

        self.btn_2 = ctk.CTkButton(self.frame_top, text=btn2, width=120, fg_color="transparent", border_width=1,
                                   command=lambda: self.button_event(btn2), text_color=("black", "white"))
        self.btn_2.grid(row=2, column=1, padx=(5, 10), pady=20, sticky="e")

        self.bind("<Escape>", lambda e: self.button_event())

    def get(self):
        if self.winfo_exists():
            self.master.wait_window(self)
        return self.event

    def old_xy_set(self, event):
        self.old_x = event.x
        self.old_y = event.y

    def move_window(self, event):
        self.y = event.y_root - self.old_y
        self.x = event.x_root - self.old_x
        self.geometry(f'+{self.x}+{self.y}')

    def button_event(self, event=None):
        self.grab_release()
        self.destroy()
        self.event = event


class CTkBanner(ctk.CTkFrame):
    def __init__(self, master, state: str = "info", title: str = "Title", btn1: str = "Action A",
                 btn2: str = "Action B", side: str = "right_bottom"):
        self.root = master
        self.width = 400
        self.height = 100
        super().__init__(self.root, width=self.width, height=self.height, corner_radius=5, border_width=1)

        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)
        self.event = None

        self.horizontal, self.vertical = side.split("_")

        if state not in ICON_PATH or ICON_PATH[state] is None:
            self.icon = ctk.CTkImage(Image.open(ICON_PATH["info"]), Image.open(ICON_PATH["info"]), (24, 24))
        else:
            self.icon = ctk.CTkImage(Image.open(ICON_PATH[state]), Image.open(ICON_PATH[state]), (24, 24))

        self.close_icon = ctk.CTkImage(Image.open(ICON_PATH["close"][0]), Image.open(ICON_PATH["close"][1]), (20, 20))

        self.title_label = ctk.CTkLabel(self, text=f"  {title}", font=("", 16), image=self.icon,
                                        compound="left")
        self.title_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)

        self.close_btn = ctk.CTkButton(self, text="", image=self.close_icon, width=20, height=20, hover=False,
                                       fg_color="transparent", command=self.button_event)
        self.close_btn.grid(row=0, column=1, sticky="ne", padx=10, pady=10)

        self.btn_1 = ctk.CTkButton(self, text=btn1, **LINK_BTN, command=lambda: self.button_event(btn1))
        self.btn_1.grid(row=1, column=0, padx=(40, 5), pady=10, sticky="w")

        self.btn_2 = ctk.CTkButton(self, text=btn2, **LINK_BTN,
                                   command=lambda: self.button_event(btn2))
        self.btn_2.grid(row=1, column=1, padx=5, pady=10, sticky="w")

        place_frame(self.root, self, self.horizontal, self.vertical)
        self.root.bind("<Configure>", self.update_position, add="+")

    def update_position(self, event):
        place_frame(self.root, self, self.horizontal, self.vertical)
        self.update_idletasks()
        self.root.update_idletasks()

    def get(self):
        if self.winfo_exists():
            self.master.wait_window(self)
        return self.event

    def button_event(self, event=None):
        self.root.unbind("<Configure>")
        self.grab_release()
        self.destroy()
        self.event = event


class CTkNotification(ctk.CTkToplevel):
    def __init__(self, master, state: str = "info", message: str = "message", side: str = "right_bottom"):
        super().__init__(master)
        
        # Configure window
        self.title("")  # Empty title for notification
        self.overrideredirect(True)  # Remove window decorations
        self.attributes('-topmost', True)  # Keep on top
        self.transient(master)  # Make transient to main window
        
        # Set initial size
        self.width = 300
        self.min_height = 40
        
        # Create main container
        self.container = ctk.CTkFrame(self, corner_radius=5, border_width=1)
        self.container.pack(fill="both", expand=True)
        
        # Configure grid
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        
        # Load icons
        if state not in ICON_PATH or ICON_PATH[state] is None:
            self.icon = ctk.CTkImage(Image.open(ICON_PATH["info"]), Image.open(ICON_PATH["info"]), (20, 20))
        else:
            self.icon = ctk.CTkImage(Image.open(ICON_PATH[state]), Image.open(ICON_PATH[state]), (20, 20))
            
        self.close_icon = ctk.CTkImage(Image.open(ICON_PATH["close"][0]), Image.open(ICON_PATH["close"][1]), (16, 16))
        
        # Create message label
        self.message_label = ctk.CTkLabel(
            self.container,
            text=f"  {message}",
            font=("", 12),
            image=self.icon,
            compound="left",
            wraplength=200
        )
        self.message_label.grid(row=0, column=0, sticky="nsw", padx=10, pady=5)
        
        # Create close button
        self.close_btn = ctk.CTkButton(
            self.container,
            text="",
            image=self.close_icon,
            width=16,
            height=16,
            hover=False,
            fg_color="transparent",
            command=self.close_notification
        )
        self.close_btn.grid(row=0, column=1, sticky="nse", padx=10, pady=5)
        
        # Calculate required height and update window size
        self.update_idletasks()
        self.adjust_height()
        
        # Position the notification
        self.position_notification()
        
        # Bind window resize event
        self.master.bind("<Configure>", self.update_position, add="+")
        
        # Auto-close after 3 seconds
        self.after(3000, self.close_notification)
        
    def adjust_height(self):
        """Adjust window height based on message content"""
        # Get the required height for the message label
        message_height = self.message_label.winfo_reqheight()
        
        # Add padding (top + bottom)
        padding = 10  # 5px top + 5px bottom
        
        # Calculate total required height
        required_height = message_height + padding
        
        # Ensure minimum height
        self.height = max(self.min_height, required_height)
        
        # Update window size
        self.geometry(f"{self.width}x{self.height}")
        
    def position_notification(self):
        """Calculate and set the notification position at the right bottom corner"""
        # Get master window dimensions and position
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()
        
        # Calculate position for right bottom corner
        x = master_x + master_width - self.width - 20
        y = master_y + master_height - self.height - 20
            
        # Ensure notification stays within master window bounds
        x = max(master_x, min(x, master_x + master_width - self.width))
        y = max(master_y, min(y, master_y + master_height - self.height))
            
        # Set the position
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
    def update_position(self, event):
        """Update position when main window moves"""
        self.position_notification()
        
    def close_notification(self):
        """Close the notification"""
        self.master.unbind("<Configure>")
        self.destroy()


class CTkCard(ctk.CTkFrame):
    def __init__(self, master: any, border_width=1, corner_radius=5, **kwargs):
        super().__init__(master, border_width=border_width, corner_radius=corner_radius, **kwargs)
        self.grid_propagate(False)

    def card_1(self, image_path=None, width=300, height=380, title="Card title", text=TEXT, button_text="Go somewhere",
               command=None):
        self.configure(width=width, height=height)
        self.grid_rowconfigure(2, weight=1)

        image_width = width - 10
        image_height = height - 180
        wrap_length = width - 20

        if image_path:
            load_image = ctk.CTkImage(Image.open(image_path), Image.open(image_path),
                                      (image_width, image_height))
        else:
            new_image = self.create_image(image_width, image_height)
            load_image = ctk.CTkImage(Image.open(new_image), Image.open(new_image),
                                      (image_width, image_height))

        card_image = ctk.CTkLabel(self, text="", image=load_image)
        card_image.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        card_title = ctk.CTkLabel(self, text=title, font=("", 18))
        card_title.grid(row=1, column=0, padx=10, pady=5, sticky="nw")

        card_text = ctk.CTkLabel(self, text=text, font=("", 13), wraplength=wrap_length, justify="left")
        card_text.grid(row=2, column=0, padx=10, pady=5, sticky="nw")

        card_button = ctk.CTkButton(self, text=button_text, height=35, command=command if command else None)
        card_button.grid(row=3, column=0, padx=10, pady=20, sticky="sw")

    def card_2(self, width=380, height=170, title="Card title", subtitle="Subtitle", text=TEXT, link1_text="Card link1",
               link2_text="Card link2", command1=None, command2=None):
        self.configure(width=width, height=height)

        wrap_length = width - 20

        card_title = ctk.CTkLabel(self, text=title, font=("", 18))
        card_title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="sw")

        card_subtitle = ctk.CTkLabel(self, text=subtitle, font=("", 15))
        card_subtitle.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="nw")

        card_text = ctk.CTkLabel(self, text=text, font=("", 13), wraplength=wrap_length, justify="left")
        card_text.grid(row=2, column=0, padx=10, pady=5, sticky="nw", columnspan=100)

        card_link1 = ctk.CTkButton(self, text=link1_text, **BTN_LINK, command=command1 if command1 else None)
        card_link1.grid(row=3, column=0, padx=5, pady=10, sticky="w")
        card_link2 = ctk.CTkButton(self, text=link2_text, **BTN_LINK, command=command2 if command2 else None)
        card_link2.grid(row=3, column=1, padx=5, pady=10, sticky="w")

    def card_3(self, width=600, height=180, header="Header", title="Card title", text=TEXT, button_text="Go somewhere",
               command=None):
        self.configure(width=width, height=height)
        self.grid_columnconfigure(0, weight=1)

        wrap_length = width - 20

        card_header = ctk.CTkLabel(self, text=header, font=("", 15))
        card_header.grid(row=0, column=0, padx=10, pady=5, sticky="nw")

        ctk.CTkFrame(self, height=2, fg_color=("#C9CCD6", "#5A5D63")).grid(row=1, column=0, padx=0, pady=2, sticky="ew")

        card_title = ctk.CTkLabel(self, text=title, font=("", 18))
        card_title.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="sw")

        card_text = ctk.CTkLabel(self, text=text, font=("", 13), wraplength=wrap_length, justify="left")
        card_text.grid(row=3, column=0, padx=10, pady=5, sticky="nw")

        card_button = ctk.CTkButton(self, text=button_text, height=35, command=command if command else None)
        card_button.grid(row=4, column=0, padx=10, pady=10, sticky="sw")

    @staticmethod
    def create_image(width, height):
        create_image = Image.new('RGB', (width, height), 'gray')
        image_data = io.BytesIO()
        create_image.save(image_data, format='PNG')
        image_data.seek(0)
        return image_data


class CTkCarousel(ctk.CTkFrame):
    def __init__(self, master: any, img_list=None, width=None, height=None, img_radius=25, **kwargs):
        if img_list is None:
            img_list = ICON_PATH["images"]

        self.img_list = img_list
        self.image_index = 0
        self.img_radius = img_radius

        if width and height:
            self.width = width
            self.height = height
            for path in self.img_list.copy():
                try:
                    Image.open(path)
                except Exception as e:
                    self.remove_path(path)
        else:
            self.width, self.height = self.get_dimensions()
        super().__init__(master, width=self.width, height=self.height, fg_color="transparent", **kwargs)

        self.prev_icon = ctk.CTkImage(Image.open(ICON_PATH["left"]), Image.open(ICON_PATH["left"]), (30, 30))
        self.next_icon = ctk.CTkImage(Image.open(ICON_PATH["right"]), Image.open(ICON_PATH["right"]), (30, 30))

        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.pack(expand=True, fill="both")

        self.button_bg = ctk.ThemeManager.theme["CTkButton"]["fg_color"]

        self.previous_button = ctk.CTkButton(self.image_label, text="", image=self.prev_icon, **ICON_BTN,
                                             command=self.previous_callback, bg_color=self.button_bg)
        self.previous_button.place(relx=0.0, rely=0.5, anchor='w')
        set_opacity(self.previous_button.winfo_id(), color=self.button_bg[0])

        self.next_button = ctk.CTkButton(self.image_label, text="", image=self.next_icon, **ICON_BTN,
                                         command=self.next_callback, bg_color=self.button_bg)
        self.next_button.place(relx=1.0, rely=0.5, anchor='e')
        set_opacity(self.next_button.winfo_id(), color=self.button_bg[0])

        self.next_callback()

    def get_dimensions(self):
        max_width, max_height = 0, 0

        for path in self.img_list.copy():
            try:
                with Image.open(path) as img:
                    width, height = img.size

                    if width > max_width and height > max_height:
                        max_width, max_height = width, height
            except Exception as e:
                self.remove_path(path)

        return max_width, max_height

    def remove_path(self, path):
        self.img_list.remove(path)

    @staticmethod
    def add_corners(image, radius):
        circle = Image.new('L', (radius * 2, radius * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radius * 2 - 1, radius * 2 - 1), fill=255)
        alpha = Image.new('L', image.size, 255)
        w, h = image.size
        alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
        alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))
        alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
        alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius))
        image.putalpha(alpha)
        return image

    def next_callback(self):
        self.image_index += 1

        if self.image_index > len(self.img_list) - 1:
            self.image_index = 0

        create_rounded = Image.open(self.img_list[self.image_index])
        create_rounded = self.add_corners(create_rounded, self.img_radius)

        next_image = ctk.CTkImage(create_rounded, create_rounded, (self.width, self.height))

        self.image_label.configure(image=next_image)

    def previous_callback(self):
        self.image_index -= 1

        if self.image_index < 0:
            self.image_index = len(self.img_list) - 1

        create_rounded = Image.open(self.img_list[self.image_index])
        create_rounded = self.add_corners(create_rounded, self.img_radius)

        next_image = ctk.CTkImage(create_rounded, create_rounded, (self.width, self.height))

        self.image_label.configure(image=next_image)


class CTkInput(ctk.CTkEntry):
    def __init__(self, master: any, icon_width=20, icon_height=20, **kwargs):
        super().__init__(master, **kwargs)

        self.icon_width = icon_width
        self.icon_height = icon_height

        self.is_hidden = False
        self.eye_btn = None

        self.warning = ctk.CTkImage(Image.open(ICON_PATH["warning2"]), Image.open(ICON_PATH["warning2"]),
                                    (self.icon_width, self.icon_height))
        self.eye1 = ctk.CTkImage(Image.open(ICON_PATH["eye1"][0]), Image.open(ICON_PATH["eye1"][1]),
                                 (self.icon_width, self.icon_height))
        self.eye2 = ctk.CTkImage(Image.open(ICON_PATH["eye2"][0]), Image.open(ICON_PATH["eye2"][1]),
                                 (self.icon_width, self.icon_height))

        self.button_bg = ctk.ThemeManager.theme["CTkEntry"]["fg_color"]
        self.border_color = ctk.ThemeManager.theme["CTkEntry"]["border_color"]

    def custom_input(self, icon_path, text=None, compound="right"):
        icon = ctk.CTkImage(Image.open(icon_path), Image.open(icon_path), (self.icon_width, self.icon_height))

        icon_label = ctk.CTkLabel(self, text=text if text else None, image=icon, width=self.icon_width,
                                  height=self.icon_height, compound=compound)
        icon_label.grid(row=0, column=0, padx=4, pady=0, sticky="e")

    def password_input(self):
        self.is_hidden = True
        self.configure(show="*")
        self.eye_btn = ctk.CTkButton(self, text="", width=self.icon_width, height=self.icon_height,
                                     fg_color=self.button_bg, hover=False, image=self.eye1,
                                     command=self.toggle_input)
        self.eye_btn.grid(row=0, column=0, padx=2, pady=0, sticky="e")

    def show_waring(self, border_color="red"):
        self.configure(border_color=border_color)
        icon_label = ctk.CTkLabel(self, text="", image=self.warning, width=self.icon_width, height=self.icon_height)
        icon_label.grid(row=0, column=0, padx=4, pady=0, sticky="e")

    def toggle_input(self):
        if self.is_hidden:
            self.is_hidden = False
            self.configure(show="")
            self.eye_btn.configure(image=self.eye2)
        else:
            self.is_hidden = True
            self.configure(show="*")
            self.eye_btn.configure(image=self.eye1)

    def reset_default(self):
        self.configure(border_color=self.border_color)
        self.configure(show="")
        self.is_hidden = False
        for widget in self.winfo_children():
            widget_name = widget.winfo_name()
            if widget_name.startswith("!ctklabel") or widget_name.startswith("!ctkbutton"):
                widget.destroy()


class CTkLoader(ctk.CTkFrame):
    def __init__(self, master: any, opacity: float = 0.8, width: int = 40, height: int = 40):
        self.master = master
        self.master.update()
        self.master_width = self.master.winfo_width()
        self.master_height = self.master.winfo_height()
        super().__init__(master, width=self.master_width, height=self.master_height, corner_radius=0)

        set_opacity(self.winfo_id(), value=opacity)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.loader = CTkGif(self, ICON_PATH["loader"], width=width, height=height)
        self.loader.grid(row=0, column=0, sticky="nsew")
        self.loader.start()

        self.place(relwidth=1.0, relheight=1.0)

    def stop_loader(self):
        self.loader.stop()
        self.destroy()


class CTkPopupMenu(ctk.CTkToplevel):
    def __init__(self,
                 master=None,
                 width=250,
                 height=270,
                 title="Title",
                 corner_radius=8,
                 border_width=0,
                 **kwargs):

        super().__init__(takefocus=1)

        self.y = None
        self.x = None
        self.width = width
        self.height = height
        self.focus()
        self.master_window = master
        self.corner = corner_radius
        self.border = border_width
        self.hidden = True

        if sys.platform.startswith("win"):
            self.after(100, lambda: self.overrideredirect(True))
            self.transparent_color = self._apply_appearance_mode(self._fg_color)
            self.attributes("-transparentcolor", self.transparent_color)
        elif sys.platform.startswith("darwin"):
            self.overrideredirect(True)
            self.transparent_color = 'systemTransparent'
            self.attributes("-transparent", True)
        else:
            self.attributes("-type", "splash")
            self.transparent_color = '#000001'
            self.corner = 0
            self.withdraw()

        self.frame = ctk.CTkFrame(self, bg_color=self.transparent_color, corner_radius=self.corner,
                                  border_width=self.border, **kwargs)
        self.frame.pack(expand=True, fill="both")

        self.title = ctk.CTkLabel(self.frame, text=title, font=("", 16))
        self.title.pack(expand=True, fill="x", padx=10, pady=5)

        self.master.bind("<ButtonPress>", lambda event: self._withdraw_off(), add="+")
        self.bind("<Button-1>", lambda event: self._withdraw(), add="+")
        self.master.bind("<Configure>", lambda event: self._withdraw(), add="+")

        self.resizable(width=False, height=False)
        self.transient(self.master_window)

        self.update_idletasks()

        self.withdraw()

    def _withdraw(self):
        self.withdraw()
        self.hidden = True

    def _withdraw_off(self):
        if self.hidden:
            self.withdraw()
        self.hidden = True

    def popup(self, x=None, y=None):
        self.x = x
        self.y = y
        self.deiconify()
        self.focus()
        self.geometry('{}x{}+{}+{}'.format(self.width, self.height, self.x, self.y))
        self.hidden = False


def do_popup(event, frame):
    try:
        frame.popup(event.x_root, event.y_root)
    finally:
        frame.grab_release()


class CTkProgressPopup(ctk.CTkFrame):
    def __init__(self, master, title: str = "Background Tasks", label: str = "Label...",
                 message: str = "Do something...", side: str = "right_bottom"):
        self.root = master
        self.width = 420
        self.height = 120
        super().__init__(self.root, width=self.width, height=self.height, corner_radius=5, border_width=1)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        self.cancelled = False

        self.title = ctk.CTkLabel(self, text=title, font=("", 16))
        self.title.grid(row=0, column=0, sticky="ew", padx=20, pady=10, columnspan=2)

        self.label = ctk.CTkLabel(self, text=label, height=0)
        self.label.grid(row=1, column=0, sticky="sw", padx=20, pady=0)

        self.progressbar = ctk.CTkProgressBar(self)
        self.progressbar.set(0)
        self.progressbar.grid(row=2, column=0, sticky="ew", padx=20, pady=0)

        self.close_icon = ctk.CTkImage(Image.open(ICON_PATH["close"][0]),
                                       Image.open(ICON_PATH["close"][1]),
                                       (16, 16))

        self.cancel_btn = ctk.CTkButton(self, text="", width=16, height=16, fg_color="transparent",
                                        command=self.cancel_task, image=self.close_icon)
        self.cancel_btn.grid(row=2, column=1, sticky="e", padx=10, pady=0)

        self.message = ctk.CTkLabel(self, text=message, height=0)
        self.message.grid(row=3, column=0, sticky="nw", padx=20, pady=(0, 10))

        self.horizontal, self.vertical = side.split("_")
        place_frame(self.root, self, self.horizontal, self.vertical)
        self.root.bind("<Configure>", self.update_position, add="+")

    def update_position(self, event):
        place_frame(self.root, self, self.horizontal, self.vertical)
        self.update_idletasks()
        self.root.update_idletasks()

    def update_progress(self, progress):
        if self.cancelled:
            return "Cancelled"
        self.progressbar.set(progress)

    def update_message(self, message):
        self.message.configure(text=message)

    def update_label(self, label):
        self.label.configure(text=label)

    def cancel_task(self):
        self.cancelled = True
        self.close_progress_popup()

    def close_progress_popup(self):
        self.root.unbind("<Configure>")
        self.destroy()


class CTkTreeview(ctk.CTkFrame):
    def __init__(self, master: any, items):
        self.root = master
        self.items = items
        super().__init__(self.root)

        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(master=self, text="Treeview", font=("", 16))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.bg_color = self.root._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        self.text_color = self.root._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        self.selected_color = self.root._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])

        self.tree_style = ttk.Style(self)
        self.tree_style.theme_use('default')

        self.im_open = Image.open(ICON_PATH["arrow"])
        self.im_close = self.im_open.rotate(90)
        self.im_empty = Image.new('RGBA', (15, 15), '#00000000')

        self.img_open = ImageTk.PhotoImage(self.im_open, name='img_open', size=(15, 15))
        self.img_close = ImageTk.PhotoImage(self.im_close, name='img_close', size=(15, 15))
        self.img_empty = ImageTk.PhotoImage(self.im_empty, name='img_empty', size=(15, 15))

        self.tree_style.element_create('Treeitem.myindicator',
                                       'image', 'img_close', ('user1', '!user2', 'img_open'), ('user2', 'img_empty'),
                                       sticky='w', width=15, height=15)

        self.tree_style.layout('Treeview.Item',
                               [('Treeitem.padding',
                                 {'sticky': 'nsew',
                                  'children': [('Treeitem.myindicator', {'side': 'left', 'sticky': 'nsew'}),
                                               ('Treeitem.image', {'side': 'left', 'sticky': 'nsew'}),
                                               ('Treeitem.focus',
                                                {'side': 'left',
                                                 'sticky': 'nsew',
                                                 'children': [
                                                     ('Treeitem.text', {'side': 'left', 'sticky': 'nsew'})]})]})]
                               )

        self.tree_style.configure("Treeview", background=self.bg_color, foreground=self.text_color,
                                  fieldbackground=self.bg_color,
                                  borderwidth=0, font=("", 10))
        self.tree_style.map('Treeview', background=[('selected', self.bg_color)],
                            foreground=[('selected', self.selected_color)])
        self.root.bind("<<TreeviewSelect>>", lambda event: self.root.focus_set())

        self.treeview = ttk.Treeview(self, show="tree")
        self.treeview.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.insert_items(self.items)

    def insert_items(self, items, parent=''):
        for item in items:
            if isinstance(item, dict):
                id = self.treeview.insert(parent, 'end', text=item['name'])
                self.insert_items(item['children'], id)
            else:
                self.treeview.insert(parent, 'end', text=item)


class CustomParametersDialog(ctk.CTkToplevel):
    def __init__(self, parent, config_file, config_combobox, delete_button):
        super().__init__(parent)
        
        # Initialize result
        self.result = None
        
        # Configure dialog window
        self.title("Custom Parameters")
        self.geometry("600x700")
        self.resizable(False, False)
        self.transient(parent)  # Make dialog modal
        self.grab_set()  # Make dialog modal
        
        # Center the dialog
        self.center_dialog()

        self.font_manager = FontManager()
        self.config_combobox = config_combobox
        self.delete_button = delete_button
        
        # Create main container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self.container)
        self.scrollable_frame.pack(fill="both", expand=True)
        
        # Load and parse config file
        self.parameters = self.load_config_file(config_file)
        
        # Create parameter widgets
        self.parameter_widgets = {}
        for key, value in self.parameters.items():
            self.create_parameter_widget(key, value)
        
        # Button frame
        button_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Save button
        self.save_button = ctk.CTkButton(
            button_frame,
            text="Save new parameters",
            font=self.font_manager.get_font("content-body"),
            command=self.save_parameters
        )
        self.save_button.pack(fill="x", pady=(0, 10))
        
        # Close button
        self.close_button = ctk.CTkButton(
            button_frame,
            text="Close",
            font=self.font_manager.get_font("content-body"),
            command=self.close_dialog
        )
        self.close_button.pack(fill="x")
        
        # Bind Enter key to Save button
        self.bind('<Return>', lambda e: self.save_parameters())
        
        # Set focus to Save button
        self.save_button.focus_set()
        
        # Bind window close event
        self.protocol("WM_DELETE_WINDOW", self.close_dialog)
        
    def close_dialog(self):
        """Close the dialog without saving"""
        self.result = None
        self.destroy()
        
    def get(self):
        """Get the dialog result"""
        return self.result
        
    def center_dialog(self):
        """Center the dialog on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
    def load_config_file(self, config_file):
        """Load and parse config file"""
        parameters = {}
        config_path = os.path.join("modules/paramslib", config_file)
        
        try:
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    # Split line into key and value
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Check if line has options (text after :)
                        if '#' in value:
                            value, options = value.split('#', 1)
                            value = value.strip()
                            options = options.strip()
                            if ':' in options:
                                options = options.split(':', 1)[1].strip()
                                # Parse options and remove numeric prefixes
                                parsed_options = []
                                for opt in options.split(','):
                                    opt = opt.strip()
                                    # Remove numeric prefix if it exists
                                    if ':' in opt:
                                        opt = opt.split(':', 1)[1].strip()
                                        if ")" in opt:
                                            opt = opt.replace(")", "")
                                    parsed_options.append(opt)
                                parameters[key] = {
                                    'value': value,
                                    'options': parsed_options
                                }
                            else:
                                parameters[key] = {'value': value}
                        else:
                            parameters[key] = {'value': value}
        except Exception as e:
            print(f"Error loading config file: {e}")
            
        return parameters
        
    def create_parameter_widget(self, key, param_data):
        """Create widget for a parameter"""
        frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        # Key label
        key_label = ctk.CTkLabel(
            frame,
            text=key,
            font=self.font_manager.get_font("content-body"),
            anchor="w",
            width=200
        )
        key_label.pack(side="left", padx=(15, 10), anchor="nw")
        
        # Special handling for pos1-navsys
        if key == "pos1-navsys":
            # Create a frame for checkboxes
            checkbox_frame = ctk.CTkFrame(frame, fg_color="transparent")
            checkbox_frame.pack(side="left", fill="x", expand=True)
            
            # Parse the current value to determine which systems are enabled
            current_value = int(param_data['value'])
            self.navsys_checkboxes = {}
            
            # Define navigation systems and their values
            nav_systems = {
                "GPS": 1,
                "SBAS": 2,
                "GLONASS": 4,
                "GALILEO": 8,
                "QZSS": 16,
                "BDS": 32,
                "NAVIC": 64
            }
            
            # Create checkboxes in a grid layout
            row = 0
            col = 0
            max_cols = 3  # Number of columns in the grid
            
            for system, value in nav_systems.items():
                var = ctk.BooleanVar(value=(current_value & value) != 0)
                checkbox = ctk.CTkCheckBox(
                    checkbox_frame,
                    text=system,
                    variable=var,
                    height=20,
                    width=20,
                    checkbox_height=20,
                    checkbox_width=20,
                    font=self.font_manager.get_font("content-body")
                )
                checkbox.grid(row=row, column=col, padx=10, pady=5, sticky="w")
                self.navsys_checkboxes[system] = (var, value)
                
                # Move to next column or row
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            # Store the frame instead of individual widgets
            self.parameter_widgets[key] = checkbox_frame
            
        else:
            # Value widget for other parameters
            if 'options' in param_data:
                # Create combobox for parameters with options
                value_var = ctk.StringVar(value=param_data['value'])
                value_widget = ctk.CTkComboBox(
                    frame,
                    values=param_data['options'],
                    variable=value_var,
                    font=self.font_manager.get_font("content-body"),
                    width=300
                )
            else:
                # Create entry for parameters without options
                value_var = ctk.StringVar(value=param_data['value'])
                value_widget = ctk.CTkEntry(
                    frame,
                    textvariable=value_var,
                    font=self.font_manager.get_font("content-body"),
                    width=300
                )
                
            value_widget.pack(side="left", fill="x", expand=True)
            
            # Store widget reference
            self.parameter_widgets[key] = value_widget
            
    def save_parameters(self):
        """Save parameters to a new config file"""
        # Get current timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"custom_{timestamp}.conf"
        new_filepath = os.path.join("modules/paramslib", new_filename)
        
        try:
            with open(new_filepath, 'w') as f:
                # Write header
                f.write(f"# Custom parameters (created {datetime.now().strftime('%Y/%m/%d %H:%M:%S')})\n\n")
                
                # Write parameters
                for key, widget in self.parameter_widgets.items():
                    if key == "pos1-navsys":
                        # Calculate total value for navsys
                        total_value = 0
                        for system, (var, value) in self.navsys_checkboxes.items():
                            if var.get():
                                total_value += value
                        f.write(f"{key}={total_value}          # (1:gps+2:sbas+4:glo+8:gal+16:qzs+32:bds+64:navic)\n")
                    elif isinstance(widget, ctk.CTkComboBox):
                        value = widget.get()
                        # Get the original options for this parameter
                        options = self.parameters[key].get('options', [])
                        if options:
                            # Format options as they appear in s2.conf
                            options_str = "(" + ",".join([f"{i+1}:{opt}" for i, opt in enumerate(options)]) + ")"
                            f.write(f"{key}={value}          # {options_str}\n")
                        else:
                            f.write(f"{key}={value}\n")
                    else:
                        value = widget.get()
                        f.write(f"{key}={value}\n")
            
            # Add new file to parent's combobox
            parent = self.master
            if hasattr(parent, 'config_combobox'):
                current_values = list(parent.config_combobox.cget("values"))
                if new_filename not in current_values:
                    current_values.append(new_filename)
                    parent.config_combobox.configure(values=current_values)
                    parent.config_var.set(new_filename)
            
            self.result = new_filename
            if self.config_combobox.get().startswith("custom_"):
                self.delete_button.configure(state="normal")
            self.destroy()
            
        except Exception as e:
            print(f"Error saving parameters: {e}")
            self.result = None
            
    def get(self):
        """Get the dialog result"""
        if self.winfo_exists():
            self.master.wait_window(self)
        return self.result


class RTKSettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_settings):
        super().__init__(parent)
        
        # Initialize result
        self.result = None
        
        # Configure dialog window
        self.title("Processing Settings")
        self.geometry("450x250")
        self.resizable(False, False)
        self.transient(parent)  # Make dialog modal
        self.grab_set()  # Make dialog modal
        
        # Center the dialog
        self.center_dialog()

        self.font_manager = FontManager()
        
        # Create main container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Plot solution checkbox
        self.plot_solution_var = ctk.BooleanVar(value=current_settings["plot_solution"])
        self.plot_solution_checkbox = ctk.CTkCheckBox(
            self.container,
            text="Plot solution",
            variable=self.plot_solution_var,
            font=self.font_manager.get_font("content-body")
        )
        self.plot_solution_checkbox.pack(fill="x", pady=(0, 20))
        
        # Configuration file selection
        config_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        config_frame.pack(fill="x", pady=(0, 20))
        
        config_label = ctk.CTkLabel(
            config_frame,
            text="Processing template:",
            font=self.font_manager.get_font("content-body")
        )
        config_label.pack(side="left", padx=(0, 10))
        
        # Get list of conf files from paramslib directory
        self.conf_files = self.get_conf_files()
        
        # Set initial value to current config file if it exists in the list
        current_config = current_settings["config_file"]
        if current_config in self.conf_files:
            initial_config = current_config
        else:
            initial_config = self.conf_files[0] if self.conf_files else ""
            
        self.config_var = ctk.StringVar(value=initial_config)
        self.config_combobox = ctk.CTkComboBox(
            config_frame,
            values=self.conf_files,
            variable=self.config_var,
            font=self.font_manager.get_font("content-body"),
            width=200
        )
        self.config_combobox.pack(side="left", padx=(0, 10))
        
        # Delete button for custom configs
        self.delete_button = ctk.CTkButton(
            config_frame,
            text="Delete",
            width=60,
            font=self.font_manager.get_font("content-body"),
            command=self.delete_config,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_button.pack(side="left")
        
        # Define Custom Parameters button
        self.define_params_button = ctk.CTkButton(
            self.container,
            text="Define Custom Parameters",
            font=self.font_manager.get_font("content-body"),
            command=self.define_custom_params
        )
        self.define_params_button.pack(fill="x", pady=(20, 10))
        
        # Save button
        self.ok_button = ctk.CTkButton(
            self.container,
            text="Save",
            font=self.font_manager.get_font("content-body"),
            command=self.ok_event
        )
        self.ok_button.pack(fill="x", pady=(0, 0))
        
        # Bind Enter key to Save button
        self.bind('<Return>', lambda e: self.ok_event())
        
        # Set focus to Save button
        self.ok_button.focus_set()
        
        # Update delete button state
        self.update_delete_button_state()
        
        # Bind window close event
        self.protocol("WM_DELETE_WINDOW", self.close_dialog)
        
    def close_dialog(self):
        """Close the dialog without saving"""
        self.result = None
        self.destroy()
        
    def get(self):
        """Get the dialog result"""
        return self.result

    def update_delete_button_state(self):
        """Update delete button state based on selected config file"""
        selected_file = self.config_var.get()
        # Enable delete button only for custom configs
        if selected_file.startswith("custom_"):
            self.delete_button.configure(state="normal")
        else:
            self.delete_button.configure(state="disabled")
            
    def delete_config(self):
        """Delete the selected custom config file"""
        selected_file = self.config_var.get()
        if not selected_file.startswith("custom_"):
            return
            
        # Confirm deletion
        if not self.confirm_deletion(selected_file):
            return
            
        try:
            # Delete the file
            file_path = os.path.join("modules/paramslib", selected_file)
            if os.path.exists(file_path):
                os.remove(file_path)
                
                # Update combobox values
                current_values = list(self.config_combobox.cget("values"))
                current_values.remove(selected_file)
                self.config_combobox.configure(values=current_values)
                
                # Select first available config
                if current_values:
                    self.config_var.set(current_values[0])
                else:
                    self.config_var.set("")
                    
                # Update delete button state
                self.update_delete_button_state()
                
        except Exception as e:
            print(f"Error deleting config file: {e}")
            
    def confirm_deletion(self, filename):
        """Show confirmation dialog for file deletion"""
        dialog = CTkMessageBox(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {filename}?"
        )
        return dialog.get() == "OK"
        
    def center_dialog(self):
        """Center the dialog on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
    def get_conf_files(self):
        """Get list of conf files from paramslib directory"""
        conf_dir = "modules/paramslib"
        if not os.path.exists(conf_dir):
            return []
            
        conf_files = []
        for file in os.listdir(conf_dir):
            if file.endswith('.conf'):
                conf_files.append(file)
        return conf_files
        
    def define_custom_params(self):
        """Handle Define Custom Parameters button click"""
        dialog = CustomParametersDialog(self, self.config_var.get(), self.config_combobox, self.delete_button)
        result = dialog.get()
        if result:
            # Update combobox values if new file was created
            current_values = list(self.config_combobox.cget("values"))
            if result not in current_values:
                current_values.append(result)
                self.config_combobox.configure(values=current_values)
                self.config_var.set(result)
                # Update delete button state after setting new config
                self.update_delete_button_state()
        
    def ok_event(self):
        """Handle OK button click"""
        self.result = {
            "plot_solution": self.plot_solution_var.get(),
            "config_file": f"{os.path.dirname(os.path.abspath(__file__)).replace('common', 'modules/paramslib')}/{self.config_var.get()}".replace("\\", "/")
        }
        self.destroy()
        