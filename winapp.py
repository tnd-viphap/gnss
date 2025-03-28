import os
import shutil
import subprocess
import customtkinter as ctk
from common.fonts.font_manager import FontManager
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog
from tkcalendar import DateEntry
from datetime import datetime
import re

# Global settings
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")


class ExRTK:
    def __init__(self):
        self.root = TkinterDnD.Tk()  # Use TkinterDnD.Tk instead of ctk.CTk
        self.root.title("Extened RTKPost")
        
        # Set window size
        window_width = 1024
        window_height = 1024
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position for center of screen
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set geometry with position and size
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        #self.root.configure(fg_color="white")
        self.font_manager = FontManager()
        
        # Store entry references
        self.single_entries = {}
        self.batch_entries = {}
        
        self.setup_ui()

    def setup_ui(self):
        # Create toolbar frame
        toolbar_frame = ctk.CTkFrame(self.root, height=40, fg_color="#D9D9D9", corner_radius=0)
        toolbar_frame.pack(side="top", fill="x")

        text = {
            "Import": {
                "fg_color": "#407750",
                "height": 40,
                "width": 100,
                "font": self.font_manager.get_font("toolbar-button"),
                "hover_color": "#306640",
                "corner_radius": 0,
                "padx": 0,
                "pady": 0,
            },
            "Settings": {
                "fg_color": "#407750",
                "height": 40,
                "width": 100,
                "font": self.font_manager.get_font("toolbar-button"),
                "hover_color": "#306640",
                "corner_radius": 0,
                "padx": 0,
                "pady": 0,
            },
            "Help": {
                "fg_color": "#407750",
                "height": 40,
                "width": 100,
                "font": self.font_manager.get_font("toolbar-button"),
                "hover_color": "#306640",
                "corner_radius": 0,
                "padx": 0,
                "pady": 0,
            },
        }
        for _, (key, value) in enumerate(text.items()):
            button = ctk.CTkButton(
                toolbar_frame,
                text=key,
                fg_color=value["fg_color"],
                font=value["font"],
                hover_color=value["hover_color"],
                corner_radius=value["corner_radius"],
                width=value["width"],
                height=value["height"]
            )
            button.pack(side="left", padx=value["padx"], pady=value["pady"])

        # Create main content frame
        self.content_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Store mode buttons as instance variables
        self.single_process_btn = ctk.CTkButton(
            mode_radio_frame,
            text="Single",
            height=30,
            width=80,
            text_color="white",
            fg_color="#407750",  # Active color
            hover_color="#306640",
            corner_radius=0,
            font=self.font_manager.get_font("toolbar-button")
        )
        self.single_process_btn.bind("<Button-1>", lambda event: self.update_mode_frame(self.single_process_btn))
        self.single_process_btn.pack(side="left", padx=(0, 10))
        
        self.batch_process_btn = ctk.CTkButton(
            mode_radio_frame,
            text="Batch Process",
            height=30,
            width=110,
            text_color="black",
            fg_color="#CCCCCC",  # Inactive color
            hover_color="#BBBBBB",
            corner_radius=0,
            font=self.font_manager.get_font("toolbar-button")
        )
        self.batch_process_btn.bind("<Button-1>", lambda event: self.update_mode_frame(self.batch_process_btn))
        self.batch_process_btn.pack(side="left")
        
        # Create frames for both modes
        self.single_frame = ctk.CTkFrame(self.content_frame, fg_color="white", border_width=1, border_color="#AAAAAA", corner_radius=0)
        self.single_frame.pack(fill="both", expand=True)
        
        self.batch_frame = ctk.CTkFrame(self.content_frame, fg_color="white", border_width=1, border_color="#AAAAAA", corner_radius=0)
        self.batch_frame.pack_forget()  # Initially hidden
        
        # Setup the Single frame content
        self.setup_single_frame()
        
        # Setup placeholder for the Batch frame
        self.setup_batch_frame()
        
    def update_mode_frame(self, button):
        # Show the appropriate frame based on mode selection
        if button.cget("text") == "Single":
            self.batch_frame.pack_forget()
            self.single_frame.pack(fill="both", expand=True)
            # Update button colors
            self.single_process_btn.configure(fg_color="#407750", hover_color="#306640", text_color="white")
            self.batch_process_btn.configure(fg_color="#CCCCCC", hover_color="#BBBBBB", text_color="black")
        else:
            self.single_frame.pack_forget()
            self.batch_frame.pack(fill="both", expand=True)
            # Update button colors
            self.single_process_btn.configure(fg_color="#CCCCCC", hover_color="#BBBBBB", text_color="black")
            self.batch_process_btn.configure(fg_color="#407750", hover_color="#306640", text_color="white")
            
    def setup_single_frame(self):
        # TPS to Rinex label
        tps_label = ctk.CTkLabel(self.single_frame, text="TPS to Rinex", anchor="w", font=self.font_manager.get_font("content-header"))
        tps_label.pack(anchor="w", pady=(15, 5))
        
        # TPS to Rinex frame
        tps_frame = ctk.CTkFrame(self.single_frame, fg_color="white", border_width=1, border_color="#AAAAAA", corner_radius=0)
        tps_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Define input fields for TPS to Rinex
        tps_fields = {
            "Rover TPS": {
                "label": {
                    "font": self.font_manager.get_font("content-header"),
                    "anchor": "w",
                    "padx": 15,
                    "pady": (15, 5)
                },
                "entry": {
                    "height": 30,
                    "padx": (0, 5),
                    "font": self.font_manager.get_font("content-header"),
                    "border_width": 1,
                    "corner_radius": 0
                },
                "browse": {
                    "text": "...",
                    "width": 30,
                    "height": 30,
                    "font": self.font_manager.get_font("content-header"),
                    "corner_radius": 0
                }
            },
            "Base TPS": {
                "label": {
                    "font": self.font_manager.get_font("content-header"),
                    "anchor": "w",
                    "padx": 15,
                    "pady": (0, 5)
                },
                "entry": {
                    "height": 30,
                    "padx": (0, 5),
                    "font": self.font_manager.get_font("content-header"),
                    "border_width": 1,
                    "corner_radius": 0
                },
                "browse": {
                    "text": "...",
                    "width": 30,
                    "height": 30,
                    "font": self.font_manager.get_font("content-header"),
                    "corner_radius": 0
                }
            }
        }
        
        # Store TPS entries
        self.tps_entries = {}
        
        # Create TPS input fields
        for field_name, config in tps_fields.items():
            # Label
            label = ctk.CTkLabel(
                tps_frame,
                text=field_name,
                font=config["label"]["font"],
                anchor=config["label"]["anchor"]
            )
            label.pack(anchor="w", padx=config["label"]["padx"], pady=config["label"]["pady"])
            
            # Frame for entry and browse button
            field_frame = ctk.CTkFrame(tps_frame, fg_color="white")
            field_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            # Entry with drag and drop support
            entry = DragDropEntry(
                field_frame,
                font=config["entry"]["font"],
                height=config["entry"]["height"],
                border_width=config["entry"]["border_width"],
                corner_radius=config["entry"]["corner_radius"]
            )
            entry.pack(side="left", fill="x", expand=True, padx=config["entry"]["padx"])
            
            # Store entry reference
            self.tps_entries[field_name] = entry
            
            # Browse button with file dialog
            browse = ctk.CTkButton(
                field_frame,
                fg_color="#407750",
                hover_color="#306640",
                font=config["browse"]["font"],
                text=config["browse"]["text"],
                width=config["browse"]["width"],
                height=config["browse"]["height"],
                corner_radius=config["browse"]["corner_radius"],
                command=lambda e=entry: self.browse_file(e)
            )
            browse.pack(side="right")
        
        # Execute button for TPS to Rinex
        execute_frame = ctk.CTkFrame(
            tps_frame,
            corner_radius=0,
            fg_color="#CCCCCC",
            height=40
        )
        execute_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Get Rinex Data button
        execute_button = ctk.CTkButton(
            execute_frame,
            text="Get Rinex Data",
            fg_color="#407750",
            hover_color="#306640",
            font=self.font_manager.get_font("content-header"),
            text_color="white",
            height=40,
            corner_radius=0,
            border_width=0,
            command=self.run_tps_to_rinex
        )
        execute_button.pack(fill="x")
        
        
        # Mode label
        rtkp_label = ctk.CTkLabel(self.content_frame, text="Rinex to RTK Position", anchor="w", font=self.font_manager.get_font("content-header"))
        rtkp_label.pack(anchor="w", pady=(0, 5))
        # Define input fields configuration for Single mode
        input_fields = {
            "Rover Obs": {
                "label": {
                    "font": self.font_manager.get_font("content-header"),
                    "anchor": "w",
                    "padx": 15,
                    "pady": (15, 5)
                },
                "entry": {
                    "height": 30,
                    "padx": (0, 5),
                    "font": self.font_manager.get_font("content-header"),
                    "border_width": 1,
                    "corner_radius": 0
                },
                "browse": {
                    "text": "...",
                    "width": 30,
                    "height": 30,
                    "font": self.font_manager.get_font("content-header"),
                    "corner_radius": 0
                }
            },
            "Base Obs": {
                "label": {
                    "font": self.font_manager.get_font("content-header"),
                    "anchor": "w",
                    "padx": 15,
                    "pady": (0, 5)
                },
                "entry": {
                    "height": 30,
                    "padx": (0, 5),
                    "font": self.font_manager.get_font("content-header"),
                    "border_width": 1,
                    "corner_radius": 0
                },
                "browse": {
                    "text": "...",
                    "width": 30,
                    "height": 30,
                    "font": self.font_manager.get_font("content-header"),
                    "corner_radius": 0
                }
            },
            "Rover Pos / Base Pos": {
                "label": {
                    "font": self.font_manager.get_font("content-header"),
                    "anchor": "w",
                    "padx": 15,
                    "pady": (0, 5)
                },
                "entry": {
                    "height": 30,
                    "padx": (0, 5),
                    "font": self.font_manager.get_font("content-header"),
                    "border_width": 1,
                    "corner_radius": 0
                },
                "browse": {
                    "text": "...",
                    "font": self.font_manager.get_font("content-header"),
                    "width": 30,
                    "height": 30,
                    "corner_radius": 0
                }
            }
        }

        # Create input fields
        for field_name, config in input_fields.items():
            # Label
            label = ctk.CTkLabel(
                self.single_frame,
                text=field_name,
                font=config["label"]["font"],
                anchor=config["label"]["anchor"]
            )
            label.pack(anchor="w", padx=config["label"]["padx"], pady=config["label"]["pady"])
            
            # Frame for entry and browse button
            field_frame = ctk.CTkFrame(self.single_frame, fg_color="white")
            field_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            # Entry with drag and drop support
            entry = DragDropEntry(
                field_frame,
                font=config["entry"]["font"],
                height=config["entry"]["height"],
                border_width=config["entry"]["border_width"],
                corner_radius=config["entry"]["corner_radius"]
            )
            entry.pack(side="left", fill="x", expand=True, padx=config["entry"]["padx"])
            
            # Store entry reference
            self.single_entries[field_name] = entry
            
            # Browse button with file dialog
            browse = ctk.CTkButton(
                field_frame,
                fg_color="#407750",
                hover_color="#306640",
                font=config["browse"]["font"],
                text=config["browse"]["text"],
                width=config["browse"]["width"],
                height=config["browse"]["height"],
                corner_radius=config["browse"]["corner_radius"],
                command=lambda e=entry: self.browse_file(e)
            )
            browse.pack(side="right")

        # Define checkboxes configuration
        checkboxes = {
            "Remove RINEX output": {
                "border_width": 2,
                "font": self.font_manager.get_font("content-header"),
                "border_color": "#407750",
                "hover_color": "#407750",
                "color": "#407750",
                "padx": 15,
                "pady": (10, 5)
            },
            "Remove POS output": {
                "border_width": 2,
                "font": self.font_manager.get_font("content-header"),
                "border_color": "#407750",
                "hover_color": "#407750",
                "color": "#407750",
                "padx": 15,
                "pady": (0, 10)
            }
        }

        # Create checkboxes
        for text, config in checkboxes.items():
            checkbox = ctk.CTkCheckBox(self.single_frame, text=text, border_width=config["border_width"], border_color=config["border_color"], fg_color=config["color"], hover_color=config["hover_color"], font=config["font"])
            checkbox.pack(anchor="w", padx=config["padx"], pady=config["pady"])

        # Progress section
        progress_frame = ctk.CTkFrame(
            self.single_frame,
            fg_color="white",
            border_width=1,
            border_color="#DDDDDD",
            corner_radius=0
        )
        progress_frame.pack(fill="x", padx=15, pady=(50, 10))
        
        progress_label = ctk.CTkLabel(
            progress_frame,
            text="Progress:",
            anchor="w",
            font=self.font_manager.get_font("content-header")
        )
        progress_label.pack(anchor="w", padx=10, pady=10)
        
        # Execute button configuration
        execute_config = {
            "frame": {
                "fg_color": "#CCCCCC",
                "height": 40,
                "padx": 15,
                "pady": (10, 15)
            },
            "button": {
                "text": "Execute",
                "font": self.font_manager.get_font("content-header"),
                "fg_color": "#CCCCCC",
                "text_color": "black",
                "hover_color": "#BBBBBB",
                "height": 50,
                "corner_radius": 0,
                "border_width": 0,
                "compound": "left"
            }
        }
        
        # Create execute button
        execute_frame = ctk.CTkFrame(
            self.single_frame,
            corner_radius=0,
            fg_color=execute_config["frame"]["fg_color"],
            height=execute_config["frame"]["height"]
        )
        execute_frame.pack(
            fill="x",
            padx=execute_config["frame"]["padx"],
            pady=execute_config["frame"]["pady"]
        )
        
        # Play icon
        play_icon = self.get_play_icon()
        play_image = ctk.CTkImage(light_image=play_icon, size=(20, 20))
        
        # Execute button
        execute_button = ctk.CTkButton(
            execute_frame,
            text=execute_config["button"]["text"],
            fg_color=execute_config["button"]["fg_color"],
            font=execute_config["button"]["font"],
            text_color=execute_config["button"]["text_color"],
            hover_color=execute_config["button"]["hover_color"],
            height=execute_config["button"]["height"],
            corner_radius=execute_config["button"]["corner_radius"],
            border_width=execute_config["button"]["border_width"],
            image=play_image,
            compound=execute_config["button"]["compound"],
            command=self.run_single_process
        )
        execute_button.pack(fill="x")
        
    def setup_batch_frame(self):
        # Define input fields configuration
        input_fields = {
            "Start Obs": {
                "label": {
                    "font": self.font_manager.get_font("content-header"),
                    "anchor": "w",
                    "padx": 15,
                    "pady": (15, 5)
                },
                "entry": {
                    "height": 40,
                    "width": 300,
                    "padx": (0, 5),
                    "font": self.font_manager.get_font("content-header"),
                    "border_width": 1,
                    "corner_radius": 0
                },
                "pattern": {
                    "width": 100,
                    "height": 40,
                    "padx": 5,
                    "font": self.font_manager.get_font("content-header"),
                    "border_width": 1,
                    "corner_radius": 0,
                    "placeholder_text": "Pattern"
                },
                "browse": {
                    "text": "...",
                    "width": 40,
                    "height": 40,
                    "font": self.font_manager.get_font("content-header"),
                    "corner_radius": 0
                }
            },
            "End Obs": {
                "label": {
                    "font": self.font_manager.get_font("content-header"),
                    "anchor": "w",
                    "padx": 15,
                    "pady": (0, 5)
                },
                "entry": {
                    "height": 40,
                    "width": 300,
                    "padx": (0, 5),
                    "font": self.font_manager.get_font("content-header"),
                    "border_width": 1,
                    "corner_radius": 0
                },
                "pattern": {
                    "width": 100,
                    "height": 40,
                    "padx": 5,
                    "font": self.font_manager.get_font("content-header"),
                    "border_width": 1,
                    "corner_radius": 0,
                    "placeholder_text": "Pattern"
                },
                "browse": {
                    "text": "...",
                    "width": 40,
                    "height": 40,
                    "font": self.font_manager.get_font("content-header"),
                    "corner_radius": 0
                }
            },
            "Output Folder": {
                "label": {
                    "font": self.font_manager.get_font("content-header"),
                    "anchor": "w",
                    "padx": 15,
                    "pady": (0, 5)
                },
                "entry": {
                    "height": 40,
                    "width": 410,
                    "padx": (0, 5),
                    "font": self.font_manager.get_font("content-header"),
                    "border_width": 1,
                    "corner_radius": 0
                },
                "browse": {
                    "text": "...",
                    "width": 40,
                    "height": 40,
                    "font": self.font_manager.get_font("content-header"),
                    "corner_radius": 0
                }
            }
        }

        # Create input fields
        for field_name, config in input_fields.items():
            # Label
            label = ctk.CTkLabel(
                self.batch_frame,
                text=field_name,
                font=config["label"]["font"],
                anchor=config["label"]["anchor"]
            )
            label.pack(anchor="w", padx=config["label"]["padx"], pady=config["label"]["pady"])
            
            # Frame for entry and browse button
            field_frame = ctk.CTkFrame(self.batch_frame, fg_color="white")
            field_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            if field_name != "Output Folder":
                # Regular entry for Start Obs and End Obs
                entry = ctk.CTkEntry(
                    field_frame,
                    font=config["entry"]["font"],
                    height=config["entry"]["height"],
                    width=config["entry"]["width"],
                    border_width=config["entry"]["border_width"],
                    corner_radius=config["entry"]["corner_radius"]
                )
                entry.pack(side="left", padx=config["entry"]["padx"])
                
                # Pattern entry
                pattern_entry = ctk.CTkEntry(
                    field_frame,
                    font=config["pattern"]["font"],
                    height=config["pattern"]["height"],
                    width=config["pattern"]["width"],
                    border_width=config["pattern"]["border_width"],
                    corner_radius=config["pattern"]["corner_radius"],
                    placeholder_text=config["pattern"]["placeholder_text"]
                )
                pattern_entry.pack(side="left", padx=config["pattern"]["padx"])
                
                # Browse button with file dialog
                browse = ctk.CTkButton(
                    field_frame,
                    fg_color="#407750",
                    hover_color="#306640",
                    font=config["browse"]["font"],
                    text=config["browse"]["text"],
                    width=config["browse"]["width"],
                    height=config["browse"]["height"],
                    corner_radius=config["browse"]["corner_radius"],
                    command=lambda e=entry, p=pattern_entry: self.browse_file_with_date(e, p)
                )
                browse.pack(side="left")
            else:
                # Regular entry for Output Folder
                entry = ctk.CTkEntry(
                    field_frame,
                    font=config["entry"]["font"],
                    height=config["entry"]["height"],
                    width=config["entry"]["width"],
                    border_width=config["entry"]["border_width"],
                    corner_radius=config["entry"]["corner_radius"]
                )
                entry.pack(side="left", padx=config["entry"]["padx"])
                
                # Browse button with directory dialog
                browse = ctk.CTkButton(
                    field_frame,
                    fg_color="#407750",
                    hover_color="#306640",
                    font=config["browse"]["font"],
                    text=config["browse"]["text"],
                    width=config["browse"]["width"],
                    height=config["browse"]["height"],
                    corner_radius=config["browse"]["corner_radius"],
                    command=lambda e=entry: self.browse_directory(e)
                )
                browse.pack(side="left")

        # Define checkboxes configuration
        checkboxes = {
            "Remove RINEX output": {
                "border_width": 2,
                "font": self.font_manager.get_font("content-header"),
                "border_color": "#407750",
                "hover_color": "#407750",
                "color": "#407750",
                "padx": 15,
                "pady": (10, 5)
            },
            "Remove POS output": {
                "border_width": 2,
                "font": self.font_manager.get_font("content-header"),
                "border_color": "#407750",
                "hover_color": "#407750",
                "color": "#407750",
                "padx": 15,
                "pady": (0, 10)
            }
        }

        # Create checkboxes
        for text, config in checkboxes.items():
            checkbox = ctk.CTkCheckBox(self.batch_frame, text=text, border_width=config["border_width"], border_color=config["border_color"], fg_color=config["color"], hover_color=config["hover_color"], font=config["font"])
            checkbox.pack(anchor="w", padx=config["padx"], pady=config["pady"])

        # Progress section
        progress_frame = ctk.CTkFrame(
            self.batch_frame,
            fg_color="white",
            border_width=1,
            border_color="#DDDDDD",
            corner_radius=0
        )
        progress_frame.pack(fill="x", padx=15, pady=(50, 10))
        
        progress_label = ctk.CTkLabel(
            progress_frame,
            text="Progress:",
            anchor="w",
            font=self.font_manager.get_font("content-header")
        )
        progress_label.pack(anchor="w", padx=10, pady=10)
        
        # Execute button configuration
        execute_config = {
            "frame": {
                "fg_color": "#CCCCCC",
                "height": 40,
                "padx": 15,
                "pady": (10, 15)
            },
            "button": {
                "text": "Execute",
                "font": self.font_manager.get_font("content-header"),
                "fg_color": "#CCCCCC",
                "text_color": "black",
                "hover_color": "#BBBBBB",
                "height": 50,
                "corner_radius": 0,
                "border_width": 0,
                "compound": "left"
            }
        }
        
        # Create execute button
        execute_frame = ctk.CTkFrame(
            self.batch_frame,
            corner_radius=0,
            fg_color=execute_config["frame"]["fg_color"],
            height=execute_config["frame"]["height"]
        )
        execute_frame.pack(
            fill="x",
            padx=execute_config["frame"]["padx"],
            pady=execute_config["frame"]["pady"]
        )
        
        # Play icon
        play_icon = self.get_play_icon()
        play_image = ctk.CTkImage(light_image=play_icon, size=(20, 20))
        
        # Execute button
        execute_button = ctk.CTkButton(
            execute_frame,
            text=execute_config["button"]["text"],
            fg_color=execute_config["button"]["fg_color"],
            font=execute_config["button"]["font"],
            text_color=execute_config["button"]["text_color"],
            hover_color=execute_config["button"]["hover_color"],
            height=execute_config["button"]["height"],
            corner_radius=execute_config["button"]["corner_radius"],
            border_width=execute_config["button"]["border_width"],
            image=play_image,
            compound=execute_config["button"]["compound"]
        )
        execute_button.pack(fill="x")

    def get_play_icon(self):
        # Load the execute icon from assets folder
        import os
        from PIL import Image
        
        # Get the absolute path to the assets folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(current_dir, "assets")
        icon_path = os.path.join(assets_dir, "execute.png")
        
        # Load and return the image
        return Image.open(icon_path)

    def run(self):
        self.root.mainloop()

    def browse_file(self, entry):
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select File",
            filetypes=(
                ("All files", "*.*"),
                ("Text files", "*.txt"),
                ("RINEX files", "*.rnx"),
                ("POS files", "*.pos")
            )
        )
        
        # If a file was selected, update the entry
        if file_path:
            entry.delete(0, 'end')
            entry.insert(0, file_path)

    def browse_directory(self, entry):
        # Open directory dialog
        directory = filedialog.askdirectory(
            title="Select Output Directory"
        )
        
        # If a directory was selected, update the entry
        if directory:
            entry.delete(0, 'end')
            entry.insert(0, directory)

    def browse_file_with_date(self, entry, pattern_entry):
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select File",
            filetypes=(
                ("All files", "*.*"),
                ("Text files", "*.txt"),
                ("RINEX files", "*.rnx"),
                ("POS files", "*.pos")
            )
        )
        
        if file_path:
            # Extract date pattern (e.g., from base_0123a.txt where 0123 is mmdd)
            pattern_match = re.search(r'_(\d{4})([a-z])', file_path)
            if pattern_match:
                date_str = pattern_match.group(1)
                pattern = pattern_match.group(2)
                
                # Update the entry with the date
                entry.delete(0, 'end')
                entry.insert(0, datetime.strptime(date_str+str(datetime.now().year), '%m%d%Y').strftime('%d/%m/%Y'))
                
                # Update the pattern entry
                pattern_entry.delete(0, 'end')
                pattern_entry.insert(0, pattern)

    def run_single_process(self):
        # Create SingleProcess instance and run it
        process = SingleProcess(self.single_entries)
        process.run()

    def run_tps_to_rinex(self):
        # Create TpsToRinex instance and run it
        process = TpsToRinex(self.tps_entries)
        process.run()

class SingleProcess:
    def __init__(self, entries):
        self.entries = entries
        self.bin_file = "modules/tps2rin.exe"
        
    def _exec_tps2rin(self, tps_file_path, output_dir):
        """
        Execute the tps2rin command for a single file
        """
        try:
            cmd = f'{self.bin_file} -i "{tps_file_path}" -o "{output_dir}"'
            subprocess.call(cmd, shell=True)
        except Exception as e:
            print(f"-> Error executing tps2rin: {e}")
            return False
        
    def run(self):
        # Get all file paths from entries
        rover_obs_path = self.entries["Rover Obs"].get()
        base_obs_path = self.entries["Base Obs"].get()
        rover_base_pos_path = self.entries["Rover Pos / Base Pos"].get()
        
        # Validate file paths
        if not all([rover_obs_path, base_obs_path, rover_base_pos_path]):
            print("Error: All file paths must be specified")
            return
            
        print(f"Processing with files:")
        print(f"Rover Obs: {rover_obs_path}")
        print(f"Base Obs: {base_obs_path}")
        print(f"Rover/Base Pos: {rover_base_pos_path}")
        
        # TODO: Add actual GNSS processing logic here
        output_dir = "temp"
        os.makedirs(output_dir, exist_ok=True)
        self._exec_tps2rin(rover_obs_path, output_dir)
        self._exec_tps2rin(base_obs_path, output_dir)
        shutil.rmtree(output_dir)

class TpsToRinex:
    def __init__(self, entries):
        self.entries = entries
        self.bin_file = "modules/tps2rin.exe"
        
    def _exec_tps2rin(self, tps_file_path, output_dir):
        """
        Execute the tps2rin command for a single file
        """
        try:
            cmd = f'{self.bin_file} -i "{tps_file_path}" -o "{output_dir}"'
            subprocess.call(cmd, shell=True)
        except Exception as e:
            print(f"-> Error executing tps2rin: {e}")
            return False
            
    def run(self):
        # Get all file paths from entries
        rover_tps_path = self.entries["Rover TPS"].get()
        base_tps_path = self.entries["Base TPS"].get()
        
        # Validate file paths
        if not all([rover_tps_path, base_tps_path]):
            print("Error: All file paths must be specified")
            return
            
        print(f"Processing TPS files:")
        print(f"Rover TPS: {rover_tps_path}")
        print(f"Base TPS: {base_tps_path}")
        
        # Create output directory
        output_dir = "temp"
        os.makedirs(output_dir, exist_ok=True)
        
        # Process both files
        self._exec_tps2rin(rover_tps_path, output_dir)
        self._exec_tps2rin(base_tps_path, output_dir)
        
        # Clean up
        shutil.rmtree(output_dir)

class DragDropEntry(ctk.CTkEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<Enter>', self.handle_enter)
        self.bind('<Leave>', self.handle_leave)
        # Enable drag and drop using tkinterdnd2
        self._entry.drop_target_register(DND_FILES)
        self._entry.dnd_bind('<<Drop>>', self.handle_drop)
        
    def handle_drop(self, event):
        # Get the dropped file path
        file_path = event.data
        # Handle Windows drag and drop format
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        # Handle multiple files (take first file only)
        if file_path.startswith('{'):
            file_path = file_path.split('}')[0] + '}'
        # Remove any quotes
        file_path = file_path.strip('"')
        # Set the entry text to the file path
        self.delete(0, 'end')
        self.insert(0, file_path)
        return 'break'
        
    def handle_enter(self, event):
        self.configure(border_color="#407750")
        
    def handle_leave(self, event):
        self.configure(border_color="#AAAAAA")


if __name__ == "__main__":
    app = ExRTK()
    app.run()
