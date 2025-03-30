import json
import os
import re
import time
from datetime import datetime
from importlib import reload
from tkinter import filedialog

import common.helpers as helpers
import common.parser as cfg
from modules.rnx2rtkp import RNX2RTKPProcessor
from modules.tps2rin import TPS2RINProcessor


class DashboardBindings:
    def __init__(self, error_signal: helpers.Signal):
        self.error_signal = error_signal

    ##TODO: Browse actions
    def browse_file_single(self, entry_widget):
        """Open file dialog and set the selected path to the entry widget"""
        file_path = filedialog.askopenfilename()
        if file_path:
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, file_path)

    def browse_folder(self, entry_widget):
        """Open folder dialog and set the selected path to the entry widget"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, folder_path)

    ##TODO: Switch actions
    def handle_single_switch(self, single_process_switch, batch_process_switch, single_frame, batch_frame):
        """Handle Single Process switch toggle"""
        if single_process_switch.get():
            # Switch turned on
            batch_process_switch.deselect()  # Turn off batch switch
            single_frame.pack(fill="both", expand=True)
            batch_frame.pack_forget()
        else:
            # Switch turned off
            single_frame.pack_forget()
            single_process_switch.deselect()

    def handle_batch_switch(self, single_process_switch, batch_process_switch, single_frame, batch_frame):
        """Handle Batch Process switch toggle"""
        if batch_process_switch.get():
            # Switch turned on
            single_process_switch.deselect()  # Turn off single switch
            batch_frame.pack(fill="both", expand=True)
            single_frame.pack_forget()
        else:
            # Switch turned off
            batch_frame.pack_forget()
            single_process_switch.deselect()

    ##TODO: Execute actions
    def execute_tps_rinex(self, execute_button, execute_frame, base_tps_entry, rover_tps_entry, base_obs_entry, rover_obs_entry, base_rover_pos_entry):
        """Execute TPS RINEX process"""
        tps2rin_processor = TPS2RINProcessor()
        self.data_dir = os.path.split(os.path.abspath(__file__))[0][0].capitalize() + os.path.join(os.path.split(os.path.abspath(__file__))[0], "data").replace("\\", "/")[1:]
        # Update data_dir in device_db.json
        try:
            config_path = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'device_db.json').replace("\\", "/")
            
            # Read existing configuration
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update data_dir value
            config['data_dir'] = self.data_dir
            
            # Write updated configuration back to file
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)

        except Exception as e:
            print(f"Error updating data_dir in configuration: {e}")
        # Reload config
        reload(cfg)

        # Process base and rover TPS files
        rover_process_dir = ""
        if "Rover1" in rover_tps_entry.get():
            rover_process_dir = os.path.split(os.path.abspath(__file__))[0][0].capitalize() + os.path.split(os.path.abspath(__file__))[0][1:] + "/data/" + cfg.FTP_ROVERS1_SETTINGS[0]["local_dir"] + "/process"
        elif "Rover2" in rover_tps_entry.get():
            rover_process_dir = os.path.split(os.path.abspath(__file__))[0][0].capitalize() + os.path.split(os.path.abspath(__file__))[0][1:] + "/data/" + cfg.FTP_ROVERS2_SETTINGS[0]["local_dir"] + "/process"
        else:
            self.error_signal.emit("Please select a valid TPS file")
            return
        execute_button.configure(text="Converting...")
        execute_frame.update()
        try:
            os.makedirs(cfg.BASE_DATA_DIR_PROCESSED, exist_ok=True)
            os.makedirs(rover_process_dir, exist_ok=True)
            
            base_tps_file_name = base_tps_entry.get()
            rover_tps_file_name = rover_tps_entry.get()

            # Pre-processing check
            processed_base = False
            processed_rover = False
            base_o_path = ""
            base_p_path = ""
            rover_o_path = ""
            rover_p_path = ""
            if (base_tps_file_name == "" and rover_tps_file_name == "") \
                or (base_tps_file_name == "" and rover_tps_file_name != "") \
                or (base_tps_file_name != "" and rover_tps_file_name == ""):
                self.error_signal.emit("Please select both base and rover TPS files")
                return
            elif base_tps_file_name != "" and rover_tps_file_name != "":
                # Extract date from base TPS filename (e.g., Base_3600_0312d -> 0312)
                hour_pattern = base_tps_file_name[-1]
                base_date_match = re.search(r'_(\d{4})[a-z]$', os.path.basename(base_tps_file_name))
                if base_date_match:
                    date_str = base_date_match.group(1)
                    # Get current year
                    current_year = datetime.now().year
                    # Fetch day of year from date string
                    day_of_year = datetime.strptime(date_str, "%m%d").timetuple().tm_yday
                    # Format expected output filename (e.g., base071d.25o)
                    expected_base_o = f"base{day_of_year:03d}{hour_pattern}.{str(current_year)[2:]}o"
                    base_o_path = os.path.join(cfg.BASE_DATA_DIR_PROCESSED, expected_base_o).replace("\\", "/")
                    expected_base_p = f"base{day_of_year:03d}{hour_pattern}.{str(current_year)[2:]}p"
                    base_p_path = os.path.join(cfg.BASE_DATA_DIR_PROCESSED, expected_base_p).replace("\\", "/")
                    
                    if os.path.exists(base_o_path) and os.path.exists(base_p_path):
                        print(f"Base file already processed: {os.path.split(base_tps_file_name)[1]}")
                        processed_base = True
                    # Extract date from rover TPS filename
                    rover_date_match = re.search(r'_(\d{4})[a-z]$', os.path.basename(rover_tps_file_name))
                    if rover_date_match:
                        date_str = rover_date_match.group(1)
                        # Fetch day of year from date string
                        day_of_year = datetime.strptime(date_str, "%m%d").timetuple().tm_yday
                        # Get current year
                        current_year = datetime.now().year
                        # Format expected output filename
                        expected_rover_o = f"rove{day_of_year:03d}{hour_pattern}.{str(current_year)[2:]}o"
                        rover_o_path = os.path.join(rover_process_dir, expected_rover_o).replace("\\", "/")
                        expected_rover_p = f"rove{day_of_year:03d}{hour_pattern}.{str(current_year)[2:]}p"
                        rover_p_path = os.path.join(rover_process_dir, expected_rover_p).replace("\\", "/")
                        
                        if os.path.exists(rover_o_path) and os.path.exists(rover_p_path):
                            print(f"Rover file already processed: {os.path.split(rover_tps_file_name)[1]}")
                            processed_rover = True
            
            if not processed_base and not processed_rover:
                tps2rin_processor.exec_tps2rin(base_tps_file_name, cfg.BASE_DATA_DIR_PROCESSED)
                tps2rin_processor.exec_tps2rin(rover_tps_file_name, rover_process_dir)
            elif not processed_base and processed_rover:
                tps2rin_processor.exec_tps2rin(base_tps_file_name, cfg.BASE_DATA_DIR_PROCESSED)
            elif processed_base and not processed_rover:
                tps2rin_processor.exec_tps2rin(rover_tps_file_name, rover_process_dir)
        except Exception as e:
            self.error_signal.emit(f"Error executing tps2rin: {e}")
        finally:
            time.sleep(1)
            execute_button.configure(text="Execute")
            rover_obs_entry.delete(0, 'end')
            rover_obs_entry.insert(0, rover_o_path)
            base_obs_entry.delete(0, 'end')
            base_obs_entry.insert(0, base_o_path)
            base_rover_pos_entry.delete(0, 'end')
            base_rover_pos_entry.insert(0, base_p_path)

    def execute_rinex_rtk(self, execute_rinex_rtk_button, rover_obs_entry, base_obs_entry, base_rover_pos_entry):
        """Execute RINEX RTK process"""
        execute_rinex_rtk_button.update()
        rnx2rtkp_processor = RNX2RTKPProcessor()

        # Get rover rinex file path
        rover_rinex_file_path = rover_obs_entry.get()
        base_rinex_file_path = base_obs_entry.get()
        base_rover_pos_file_path = base_rover_pos_entry.get()
        
        # Validate input files
        if not rover_rinex_file_path or not base_rinex_file_path or not base_rover_pos_file_path:
            self.error_signal.emit("Please select all required files")
            return
        
        # Check if files exist
        if not os.path.exists(rover_rinex_file_path):
            self.error_signal.emit(f"Rover RINEX file not found: {os.path.split(rover_rinex_file_path)[1]}")
            return
        if not os.path.exists(base_rinex_file_path):
            self.error_signal.emit(f"Base RINEX file not found: {os.path.split(base_rinex_file_path)[1]}")
            return
        if not os.path.exists(base_rover_pos_file_path):
            self.error_signal.emit(f"Base/Rover POS file not found: {os.path.split(base_rover_pos_file_path)[1]}")
            return
        
        # Determine output directory based on rover file path
        try:
            if "Rover1" in rover_rinex_file_path:
                output_pos_dir = os.path.join(os.path.dirname(__file__), "data", cfg.FTP_ROVERS1_SETTINGS[0]["local_dir"], "output")
            elif "Rover2" in rover_rinex_file_path:
                output_pos_dir = os.path.join(os.path.dirname(__file__), "data", cfg.FTP_ROVERS2_SETTINGS[0]["local_dir"], "output")
            else:
                self.error_signal.emit("Invalid rover file path")
                return
                
            # Create output directory if it doesn't exist
            os.makedirs(output_pos_dir, exist_ok=True)
            
            # Generate output filename
            output_name = os.path.basename(rover_rinex_file_path).replace("rove", "output").split(".")[0] + ".pos"
            output_file_path = os.path.join(output_pos_dir, output_name)
            
            # Check if output file already exists
            if os.path.exists(output_file_path):
                self.error_signal.emit(f"Data already processed")
                return
                
            # Execute the RTK processing
            execute_rinex_rtk_button.configure(text="Executing...")
            rnx2rtkp_processor.exec_rnx2rtkp(
                rover_rinex_file_path,
                base_rinex_file_path,
                base_rover_pos_file_path,
                output_file_path
            )

            # Remove events and stats files
            for file_path in os.listdir(output_pos_dir):
                if file_path.endswith('.pos.stat') or file_path.endswith('_events.pos'):
                    helpers.remove_file(os.path.join(output_pos_dir, file_path))
            
        except Exception as e:
            self.error_signal.emit(f"Error during RTK processing: {str(e)}")
        finally:
            time.sleep(1)
            if self.remove_rinex_checkbox.get():
                if os.path.exists(rover_rinex_file_path):
                    helpers.remove_file(rover_rinex_file_path)
                if os.path.exists(base_rinex_file_path):
                    helpers.remove_file(base_rinex_file_path)
                if os.path.exists(rover_rinex_file_path.split(".")[0] + "." + rover_rinex_file_path.split(".")[1].replace("o", "p")):
                    helpers.remove_file(rover_rinex_file_path.split(".")[0] + "." + rover_rinex_file_path.split(".")[1].replace("o", "p"))
                if os.path.exists(base_rinex_file_path.split(".")[0] + "." + base_rinex_file_path.split(".")[1].replace("o", "p")):
                    helpers.remove_file(base_rinex_file_path.split(".")[0] + "." + base_rinex_file_path.split(".")[1].replace("o", "p"))
            if self.remove_rtk_checkbox.get():
                if os.path.exists(output_file_path):
                    helpers.remove_file(output_file_path)
            execute_rinex_rtk_button.configure(text="Execute")


class GetDataBindings:
    def __init__(self, app):
        self.app = app

    def execute_rinex_rtk(self):
        self.app.execute_rinex_rtk()

class PlotBindings:
    def __init__(self, app):
        self.app = app

    def execute_plot(self):
        self.app.execute_plot()



