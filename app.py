import customtkinter as ctk
from PIL import Image
import os
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from common.fonts.font_manager import FontManager
from common.customwidgets.ctk_components import CTkAlert
import re
from datetime import datetime

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
            alert = CTkAlert(
                state="warning",    
                title="Invalid File",
                body_text="Please select a file without extension",
            )
            alert.show()
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
            alert = CTkAlert(
                state="warning",
                title="Invalid File Format",
                body_text="File name must follow the pattern: Base_3600_MMDDx where MMDD is the date and x is the hour (a-z)",  
            )
            alert.show()
            self.delete(0, 'end')
            self.insert(0, file_name)

    def browse_file(self, entry_widget):
        """Open file dialog and set the selected path to the entry widget"""
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            
            # Check if file has extension
            if '.' in file_name:
                alert = CTkAlert(
                    state="warning",
                    title="Invalid File",
                    body_text="Please select TPS file",
                )
                alert.show()
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
                alert = CTkAlert(
                    state="warning",
                    title="Invalid File Format",
                    body_text="File name must follow the pattern: Base_3600_MMDDx where MMDD is the date and x is the hour (a-z)",
                )
                alert.show()
                self.delete(0, 'end')
                self.insert(0, file_name)

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        
        # Configure window
        self.title("Extended RTK Positioning")
        self.iconbitmap("assets/Logo.ico")
        self.geometry("1920x1080")
        self.center_window()  # Center the window on screen

        # Configure fonts
        self.font_manager = FontManager()
        
        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Load images for icons
        self.load_images()
        
        # Create navigation frame
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(7, weight=1)  # Empty row as spacing
        
        # App title in navigation frame
        self.logo_image = ctk.CTkImage(light_image=Image.open("assets/Logo.png"),
                                     dark_image=Image.open("assets/Logo.png"),
                                     size=(20, 20))
        self.nav_title = ctk.CTkLabel(
            self.navigation_frame,
            text="Extended RTK",
            font=self.font_manager.get_font("toolbar-button"),
            image=self.logo_image,
            compound="left",
            padx=10,
            pady=20
        )
        self.nav_title.grid(row=0, column=0, padx=20, pady=(20, 40))  # Added more bottom padding
        
        # Navigation buttons
        self.nav_button_1 = ctk.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="Dashboard",
            font=self.font_manager.get_font("toolbar-button"),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            image=self.home_image,
            anchor="w",
            command=self.dashboard_button_event
        )
        self.nav_button_1.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))

        self.nav_button_2 = ctk.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="Get Data",
            font=self.font_manager.get_font("toolbar-button"),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            image=self.get_data_image,
            anchor="w",
            command=self.getdata_button_event
        )
        self.nav_button_2.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        self.nav_button_3 = ctk.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="Plot",
            font=self.font_manager.get_font("toolbar-button"),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            image=self.plot_image,
            anchor="w",
            command=self.plot_button_event
        )
        self.nav_button_3.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

        # Create main frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create frames for different sections
        self.dashboard_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.getdata_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.plot_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        
        # Configure dashboard frame
        self.setup_dashboard_frame()
        
        # Add content to other frames (placeholder labels)
        ctk.CTkLabel(self.getdata_frame, text="Get Data Content", font=self.font_manager.get_font("toolbar-button")).pack(pady=20)
        ctk.CTkLabel(self.plot_frame, text="Plot Content", font=self.font_manager.get_font("toolbar-button")).pack(pady=20)
        
        # Set default button
        self.select_frame_by_name("dashboard")
        
    def load_images(self):
        # Create assets directory if it doesn't exist
        if not os.path.exists("assets"):
            os.makedirs("assets")
            
        # Create placeholder images (you should replace these with actual icons)
        self.home_image = ctk.CTkImage(light_image=Image.open("assets/Dashboard.png"),
                                     dark_image=Image.open("assets/Dashboard.png"),
                                     size=(20, 20))
        self.get_data_image = ctk.CTkImage(light_image=Image.open("assets/Download.png"),
                                         dark_image=Image.open("assets/Download.png"),
                                         size=(20, 20))
        self.plot_image = ctk.CTkImage(light_image=Image.open("assets/Plot.png"),
                                          dark_image=Image.open("assets/Plot.png"),
                                          size=(20, 20))

    def select_frame_by_name(self, name):
        # Set button color for selected button
        self.nav_button_1.configure(fg_color=("gray75", "gray25") if name == "dashboard" else "transparent")
        self.nav_button_2.configure(fg_color=("gray75", "gray25") if name == "getdata" else "transparent")
        self.nav_button_3.configure(fg_color=("gray75", "gray25") if name == "plot" else "transparent")

        # Hide all frames
        self.dashboard_frame.grid_forget()
        self.getdata_frame.grid_forget()
        self.plot_frame.grid_forget()

        # Show selected frame
        if name == "dashboard":
            self.dashboard_frame.grid(row=0, column=0, sticky="nsew")
        elif name == "getdata":
            self.getdata_frame.grid(row=0, column=0, sticky="nsew")
        elif name == "plot":
            self.plot_frame.grid(row=0, column=0, sticky="nsew")

    def dashboard_button_event(self):
        self.select_frame_by_name("dashboard")

    def getdata_button_event(self):
        self.select_frame_by_name("getdata")

    def plot_button_event(self):
        self.select_frame_by_name("plot")

    def center_window(self):
        """Center the window on the screen"""
        # Get screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Get window width and height
        window_width = 1920
        window_height = 1080
        
        # Calculate position coordinates
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set the position of the window to the center of the screen
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def setup_dashboard_frame(self):
        # Create Quick Processing frame
        self.quick_processing_frame = ctk.CTkFrame(self.dashboard_frame)
        self.quick_processing_frame.pack(fill="none", side="left", padx=20, anchor="nw")
        
        # Add header label
        self.quick_processing_header = ctk.CTkLabel(
            self.quick_processing_frame,
            text="Quick Processing",
            font=self.font_manager.get_font("content-header-l1"),
            anchor="w"
        )
        self.quick_processing_header.pack(padx=15, pady=(15, 10), anchor="w")
        
        # Create frame for mode switches
        self.mode_switches_frame = ctk.CTkFrame(self.quick_processing_frame, fg_color="transparent")
        self.mode_switches_frame.pack(padx=15, pady=(0, 15), anchor="w")
        
        # Add Single Process switch
        self.single_process_label = ctk.CTkLabel(
            self.mode_switches_frame,
            text="Single Process",
            font=self.font_manager.get_font("content-body")
        )
        self.single_process_label.grid(row=0, column=0, padx=(0, 10))
        
        self.single_process_switch = ctk.CTkSwitch(
            self.mode_switches_frame,
            text="",
            command=self.handle_single_switch,
            onvalue=True,
            offvalue=False
        )
        self.single_process_switch.grid(row=0, column=1, padx=(0, 20))
        self.single_process_switch.select()  # Start with Single Process selected
        
        # Add Batch Process switch
        self.batch_process_label = ctk.CTkLabel(
            self.mode_switches_frame,
            text="Batch Process",
            font=self.font_manager.get_font("content-body")
        )
        self.batch_process_label.grid(row=0, column=2, padx=(0, 10))
        
        self.batch_process_switch = ctk.CTkSwitch(
            self.mode_switches_frame,
            text="",
            command=self.handle_batch_switch,
            onvalue=True,
            offvalue=False
        )
        self.batch_process_switch.grid(row=0, column=3)
        
        # Create frames container for process frames
        self.process_frames_container = ctk.CTkFrame(self.quick_processing_frame, fg_color="transparent")
        self.process_frames_container.pack(fill="x", padx=15, pady=(0, 15))
        
        # Create Single Process frame
        self.single_frame = ctk.CTkFrame(self.process_frames_container)
        self.single_frame.pack(fill="both", expand=True)
        
        # Create Batch Process frame
        self.batch_frame = ctk.CTkFrame(self.process_frames_container)
        
        # TPS to Rinex section for Single frame
        self.tps_to_rinex_frame = ctk.CTkFrame(self.single_frame)
        self.tps_to_rinex_frame.pack(fill="x", padx=15, pady=15)
        
        # TPS to Rinex header
        ctk.CTkLabel(
            self.tps_to_rinex_frame,
            text="TPS to Rinex",
            font=self.font_manager.get_font("content-header-l2"),
            anchor="w"
        ).pack(padx=15, pady=(15, 10), anchor="w")
        
        # Rover TPS entry
        self.rover_tps_frame = ctk.CTkFrame(self.tps_to_rinex_frame, fg_color="transparent")
        self.rover_tps_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            self.rover_tps_frame,
            text="Rover TPS",
            font=self.font_manager.get_font("content-body")
        ).pack(anchor="w")
        
        self.rover_tps_entry = DragDropEntry(
            self.rover_tps_frame,
            placeholder_text="Drag and drop or select Rover TPS file",
            font=self.font_manager.get_font("content-body"),
            height=32,
            width=400
        )
        self.rover_tps_entry.pack(side="left", pady=(5, 0))
        
        self.rover_tps_button = ctk.CTkButton(
            self.rover_tps_frame,
            text="...",
            width=32,
            height=32,
            command=lambda: self.browse_file(self.rover_tps_entry)
        )
        self.rover_tps_button.pack(side="left", padx=(10, 0), pady=(5, 0))
        
        # Base TPS entry
        self.base_tps_frame = ctk.CTkFrame(self.tps_to_rinex_frame, fg_color="transparent")
        self.base_tps_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            self.base_tps_frame,
            text="Base TPS",
            font=self.font_manager.get_font("content-body")
        ).pack(anchor="w")
        
        self.base_tps_entry = DragDropEntry(
            self.base_tps_frame,
            placeholder_text="Drag and drop or select Base TPS file",
            font=self.font_manager.get_font("content-body"),
            height=32,
            width=400
        )
        self.base_tps_entry.pack(side="left", pady=(5, 0))
        
        self.base_tps_button = ctk.CTkButton(
            self.base_tps_frame,
            text="...",
            width=32,
            height=32,
            command=lambda: self.browse_file(self.base_tps_entry)
        )
        self.base_tps_button.pack(side="left", padx=(10, 0), pady=(5, 0))
        
        # Rinex to RTK Position section
        self.rinex_to_rtk_frame = ctk.CTkFrame(self.single_frame)
        self.rinex_to_rtk_frame.pack(fill="x", padx=15, pady=15)
        
        # Rinex to RTK header
        ctk.CTkLabel(
            self.rinex_to_rtk_frame,
            text="Rinex to RTK Position",
            font=self.font_manager.get_font("content-header-l2"),
            anchor="w"
        ).pack(padx=15, pady=(15, 10), anchor="w")
        
        # Rover Obs entry
        self.rover_obs_frame = ctk.CTkFrame(self.rinex_to_rtk_frame, fg_color="transparent")
        self.rover_obs_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            self.rover_obs_frame,
            text="Rover Obs",
            font=self.font_manager.get_font("content-body")
        ).pack(anchor="w")
        
        self.rover_obs_entry = DragDropEntry(
            self.rover_obs_frame,
            placeholder_text="Drag and drop or select Rover Obs file",
            font=self.font_manager.get_font("content-body"),
            height=32,
            width=400
        )
        self.rover_obs_entry.pack(side="left", pady=(5, 0))
        
        self.rover_obs_button = ctk.CTkButton(
            self.rover_obs_frame,
            text="...",
            width=32,
            height=32,
            command=lambda: self.browse_file(self.rover_obs_entry)
        )
        self.rover_obs_button.pack(side="left", padx=(10, 0), pady=(5, 0))
        
        # Base Obs entry
        self.base_obs_frame = ctk.CTkFrame(self.rinex_to_rtk_frame, fg_color="transparent")
        self.base_obs_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            self.base_obs_frame,
            text="Base Obs",
            font=self.font_manager.get_font("content-body")
        ).pack(anchor="w")
        
        self.base_obs_entry = DragDropEntry(
            self.base_obs_frame,
            placeholder_text="Drag and drop or select Base Obs file",
            font=self.font_manager.get_font("content-body"),
            height=32,
            width=400
        )
        self.base_obs_entry.pack(side="left", pady=(5, 0))
        
        self.base_obs_button = ctk.CTkButton(
            self.base_obs_frame,
            text="...",
            width=32,
            height=32,
            command=lambda: self.browse_file(self.base_obs_entry)
        )
        self.base_obs_button.pack(side="left", padx=(10, 0), pady=(5, 0))
        
        # Base/Rover Pos entry
        self.base_rover_pos_frame = ctk.CTkFrame(self.rinex_to_rtk_frame, fg_color="transparent")
        self.base_rover_pos_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            self.base_rover_pos_frame,
            text="Base / Rover Pos",
            font=self.font_manager.get_font("content-body")
        ).pack(anchor="w")
        
        self.base_rover_pos_entry = DragDropEntry(
            self.base_rover_pos_frame,
            placeholder_text="Drag and drop or select Base/Rover Pos file",
            font=self.font_manager.get_font("content-body"),
            height=32,
            width=400
        )
        self.base_rover_pos_entry.pack(side="left", pady=(5, 0))
        
        self.base_rover_pos_button = ctk.CTkButton(
            self.base_rover_pos_frame,
            text="...",
            width=32,
            height=32,
            command=lambda: self.browse_file(self.base_rover_pos_entry)
        )
        self.base_rover_pos_button.pack(side="left", padx=(10, 0), pady=(5, 0))

        # Add checkboxes for Rinex to RTK Position
        self.checkboxes_frame = ctk.CTkFrame(self.rinex_to_rtk_frame, fg_color="transparent")
        self.checkboxes_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.remove_rinex_var = ctk.BooleanVar(value=False)
        self.remove_rinex_checkbox = ctk.CTkCheckBox(
            self.checkboxes_frame,
            text="Remove RINEX outputs",
            variable=self.remove_rinex_var,
            font=self.font_manager.get_font("content-body")
        )
        self.remove_rinex_checkbox.pack(side="left", padx=(0, 20))
        
        self.remove_rtk_var = ctk.BooleanVar(value=False)
        self.remove_rtk_checkbox = ctk.CTkCheckBox(
            self.checkboxes_frame,
            text="Remove RTK outputs",
            variable=self.remove_rtk_var,
            font=self.font_manager.get_font("content-body")
        )
        self.remove_rtk_checkbox.pack(side="left")

        # Add Execute button at the end of single frame
        self.execute_button_frame = ctk.CTkFrame(self.single_frame, fg_color="transparent")
        self.execute_button_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Load Execute icon
        self.execute_image = ctk.CTkImage(
            light_image=Image.open("assets/execute-white.png"),
            dark_image=Image.open("assets/execute-white.png"),
            size=(20, 20)
        )
        
        self.execute_button = ctk.CTkButton(
            self.execute_button_frame,
            text="Execute",
            image=self.execute_image,
            compound="left",
            width=120,
            height=32,
            font=self.font_manager.get_font("content-body")
        )
        self.execute_button.pack(side="left")

        # Create Batch Process frame content
        self.batch_frame_to_nested_frame = ctk.CTkFrame(self.batch_frame, fg_color="#CCCCCC")
        self.batch_frame_to_nested_frame.pack(fill="both", padx=15, expand=True)

        # Start Obs entry
        self.start_obs_frame = ctk.CTkFrame(self.batch_frame_to_nested_frame, fg_color="transparent")
        self.start_obs_frame.pack(fill="x", padx=(5, 5), pady=(15, 10))
        
        ctk.CTkLabel(
            self.start_obs_frame,
            text="Start Obs",
            font=self.font_manager.get_font("content-body")
        ).pack(padx=15, pady=(0, 10), anchor="w")
        
        self.start_obs_entry = BatchDragDropEntry(
            self.start_obs_frame,
            placeholder_text="Drag and drop or select start observation file",
            font=self.font_manager.get_font("content-body"),
            height=32,
            width=400
        )
        self.start_obs_entry.pack(side="left", padx=10, pady=(0, 0))
        
        self.start_obs_button = ctk.CTkButton(
            self.start_obs_frame,
            text="...",
            width=32,
            height=32,
            command=lambda: self.browse_file(self.start_obs_entry)
        )
        self.start_obs_button.pack(side="left", padx=(0, 10), pady=(0, 0))
        
        # End Obs entry
        self.end_obs_frame = ctk.CTkFrame(self.batch_frame_to_nested_frame, fg_color="transparent")
        self.end_obs_frame.pack(fill="x", padx=(5, 5), pady=(0, 10))
        
        ctk.CTkLabel(
            self.end_obs_frame,
            text="End Obs",
            font=self.font_manager.get_font("content-body")
        ).pack(padx=15, pady=(0, 10), anchor="w")
        
        self.end_obs_entry = BatchDragDropEntry(
            self.end_obs_frame,
            placeholder_text="Drag and drop or select end observation file",
            font=self.font_manager.get_font("content-body"),
            height=32,
            width=400
        )
        self.end_obs_entry.pack(side="left", padx=10, pady=(0, 0))
        
        self.end_obs_button = ctk.CTkButton(
            self.end_obs_frame,
            text="...",
            width=32,
            height=32,
            command=lambda: self.browse_file(self.end_obs_entry)
        )
        self.end_obs_button.pack(side="left", padx=(0, 10), pady=(0, 0))
        
        # Output Folder entry
        self.output_folder_frame = ctk.CTkFrame(self.batch_frame_to_nested_frame, fg_color="transparent")
        self.output_folder_frame.pack(fill="x", padx=(5, 5), pady=(0, 15))
        
        ctk.CTkLabel(
            self.output_folder_frame,
            text="Output Folder",
            font=self.font_manager.get_font("content-body")
        ).pack(padx=15, pady=(0, 10), anchor="w")
        
        self.output_folder_entry = ctk.CTkEntry(
            self.output_folder_frame,
            placeholder_text="Select output folder",
            font=self.font_manager.get_font("content-body"),
            height=32,
            width=400
        )
        self.output_folder_entry.pack(side="left", padx=10, pady=(0, 0))
        
        self.output_folder_button = ctk.CTkButton(
            self.output_folder_frame,
            text="...",
            width=32,
            height=32,
            command=self.browse_folder
        )
        self.output_folder_button.pack(side="left", padx=(0, 10), pady=(0, 0))

        # Add Execute button at the end of batch frame
        self.batch_execute_button_frame = ctk.CTkFrame(self.batch_frame_to_nested_frame, fg_color="transparent")
        self.batch_execute_button_frame.pack(fill="x", padx=5, pady=(0, 15))
        
        self.batch_execute_button = ctk.CTkButton(
            self.batch_execute_button_frame,
            text="Execute",
            image=self.execute_image,
            compound="left",
            width=120,
            height=32,
            font=self.font_manager.get_font("content-body")
        )
        self.batch_execute_button.pack(side="left", padx=10, pady=(0, 0))

    def handle_single_switch(self):
        """Handle Single Process switch toggle"""
        if self.single_process_switch.get():
            # Switch turned on
            self.batch_process_switch.deselect()  # Turn off batch switch
            self.single_frame.pack(fill="both", expand=True)
            self.batch_frame.pack_forget()
        else:
            # Switch turned off
            self.single_frame.pack_forget()
            self.single_process_switch.deselect()

    def handle_batch_switch(self):
        """Handle Batch Process switch toggle"""
        if self.batch_process_switch.get():
            # Switch turned on
            self.single_process_switch.deselect()  # Turn off single switch
            self.batch_frame.pack(fill="both", expand=True)
            self.single_frame.pack_forget()
        else:
            # Switch turned off
            self.batch_frame.pack_forget()
            self.single_process_switch.deselect()

    def browse_folder(self):
        """Open folder dialog and set the selected path to the output folder entry"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_folder_entry.delete(0, 'end')
            self.output_folder_entry.insert(0, folder_path)

if __name__ == "__main__":
    app = App()
    app.mainloop() 