import json
import os
import sys
import time

import customtkinter as ctk
from PIL import Image
from tkinterdnd2 import TkinterDnD

from bindings import DashboardBindings
from common.fonts.font_manager import FontManager
from common.helpers import Signal
from common.widgets import (BatchDragDropEntry, CTkMessageBox, CTkNotification,
                            DeviceSelectionDialog, DragDropEntry)

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        
        # Load device database
        try:
            with open('device_db.json', 'r') as f:
                self.device_db = json.load(f)
        except Exception as e:
            print(f"Error loading device database: {e}")
            self.device_db = None
            return
        
        # Configure window
        self.title("Extended RTK Positioning")
        self.iconbitmap("assets/Logo.ico")
        
        # Get screen dimensions and DPI
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Set window geometry
        self.geometry(f"{screen_width}x{screen_height}")
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
        self.error_signal = Signal()
        self.error_signal.connect(self.error_event)
        self.dashboard_bindings = DashboardBindings(self.error_signal)
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
        """Handle Get Data button click"""
        dialog = DeviceSelectionDialog(self, self.device_db)
        dialog.wait_window()  # Wait for dialog to close

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

    ###### DASHBOARD ######
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
            onvalue=True,
            offvalue=False
        )
        self.batch_process_switch.grid(row=0, column=3)
        
        # Bind switch events
        self.single_process_switch.bind("<ButtonRelease-1>", lambda event: self.switch_event(self.single_process_switch))
        self.batch_process_switch.bind("<ButtonRelease-1>", lambda event: self.switch_event(self.batch_process_switch))
        
        # Create frames container for process frames
        self.process_frames_container = ctk.CTkFrame(self.quick_processing_frame, fg_color="transparent")
        self.process_frames_container.pack(fill="x", padx=15, pady=(0, 15))
        
        ###### SINGLE PROCESS ######

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
            command=lambda: self.dashboard_bindings.browse_file_single(self.rover_tps_entry)
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
            command=lambda: self.dashboard_bindings.browse_file_single(self.base_tps_entry)
        )
        self.base_tps_button.pack(side="left", padx=(10, 0), pady=(5, 0))

        # Add Execute button at the end of single frame
        self.execute_tps_rinex_frame = ctk.CTkFrame(self.single_frame, fg_color="transparent")
        self.execute_tps_rinex_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Load Execute icon
        self.execute_image = ctk.CTkImage(
            light_image=Image.open("assets/execute-white.png"),
            dark_image=Image.open("assets/execute-white.png"),
            size=(20, 20)
        )
        
        self.execute_tps_rinex_button = ctk.CTkButton(
            self.execute_tps_rinex_frame,
            text="Execute",
            image=self.execute_image,
            compound="left",
            width=120,
            height=32,
            font=self.font_manager.get_font("content-body"),
            command=lambda: self.tps_rinex_button_event()
        )
        self.execute_tps_rinex_button.pack(side="left")
        
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
            command=lambda: self.dashboard_bindings.browse_file_single(self.rover_obs_entry)
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
            command=lambda: self.dashboard_bindings.browse_file_single(self.base_obs_entry)
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
            command=lambda: self.dashboard_bindings.browse_file_single(self.base_rover_pos_entry)
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
        self.execute_rinex_rtk_frame = ctk.CTkFrame(self.single_frame, fg_color="transparent")
        self.execute_rinex_rtk_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Load Execute icon
        self.execute_image = ctk.CTkImage(
            light_image=Image.open("assets/execute-white.png"),
            dark_image=Image.open("assets/execute-white.png"),
            size=(20, 20)
        )
        
        self.execute_rinex_rtk_button = ctk.CTkButton(
            self.execute_rinex_rtk_frame,
            text="Execute",
            image=self.execute_image,
            compound="left",
            width=120,
            height=32,
            font=self.font_manager.get_font("content-body"),
            command=lambda: self.rinex_rtk_button_event()
        )
        self.execute_rinex_rtk_button.pack(side="left")

        ###### BATCH PROCESS ######

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
            command=lambda: self.dashboard_bindings.browse_file_single(self.start_obs_entry)
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
            command=lambda: self.dashboard_bindings.browse_file_single(self.end_obs_entry)
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
            command=lambda: self.dashboard_bindings.browse_folder(self.output_folder_entry)
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

    def error_event(self, error_msg):
        """Handle error signal"""
        dialog = CTkMessageBox(self, "Error", error_msg)
        dialog.wait_window()  # Wait for dialog to close

    def switch_event(self, switch_button):
        if switch_button.get() == "Single":
            self.dashboard_bindings.handle_single_switch(self.single_process_switch, self.batch_process_switch, self.single_frame, self.batch_frame)
        elif switch_button.get() == "Batch":
            self.dashboard_bindings.handle_batch_switch(self.single_process_switch, self.batch_process_switch, self.single_frame, self.batch_frame)

    def tps_rinex_button_event(self):
        self.dashboard_bindings.execute_tps_rinex(self.execute_tps_rinex_button, self.execute_tps_rinex_frame, self.base_tps_entry, self.rover_tps_entry, self.base_obs_entry, self.rover_obs_entry, self.base_rover_pos_entry)
        CTkNotification(self, "info", "TPS RINEX conversion successful", "right_bottom")

    def rinex_rtk_button_event(self):
        self.dashboard_bindings.execute_rinex_rtk(self.execute_rinex_rtk_button, self.rover_obs_entry, self.base_obs_entry, self.base_rover_pos_entry)
        CTkNotification(self, "info", "RINEX to RTK Position conversion successful", "right_bottom")
        
    ###### Get Data ######

    ###### Plot ######

if __name__ == "__main__":
    app = App()
    app.mainloop() 