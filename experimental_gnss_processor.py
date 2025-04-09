import json
import os
import time
from importlib import reload
from multiprocessing.pool import ThreadPool

import pandas as pd

import common.helpers as helpers
import common.parser as cfg
from modules.datastream.ftp import FTPDownloader
from modules.datastream.posfile import RTKPos
from modules.rnx2rtkp import RNX2RTKPProcessor
from modules.tps2rin import TPS2RINProcessor


class GNSSProcessor:
    def __init__(self):
        self.last_x = None
        self.last_y = None
        self.last_z = None
        
        self.r2r = RNX2RTKPProcessor()
        self.t2r = TPS2RINProcessor()

        helpers.create_dir_if_not_exists(os.path.join(os.path.split(os.path.abspath(__file__))[0], "data"))
        helpers.create_dir_if_not_exists(os.path.join(os.path.split(os.path.abspath(__file__))[0], "data/Base/"))
        helpers.create_dir_if_not_exists(os.path.join(os.path.split(os.path.abspath(__file__))[0], "data/Rover1/"))
        helpers.create_dir_if_not_exists(os.path.join(os.path.split(os.path.abspath(__file__))[0], "data/Rover2/"))

        self.data_dir = os.path.split(os.path.abspath(__file__))[0][0].capitalize() + os.path.join(os.path.split(os.path.abspath(__file__))[0], "data").replace("\\", "/")[1:]
        self._update_data_dir_in_config()

    def _update_data_dir_in_config(self):
        """
        Update the data_dir value in device_db.json
        """
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
            print(f"-> Error updating data_dir in configuration: {e}")

    def get_last_output(self, file_path):
        try:
            with open(file_path, "r") as file:
                lines = file.readlines()
                if len(lines) < 2:
                    return None

                last_line = lines[-1]
                data = last_line.split(",")
                return {
                    "timestamp": float(data[0]),
                    "averageX": float(data[1]),
                    "averageY": float(data[2]),
                    "averageZ": float(data[3]),
                }
        except Exception:
            return None

    def fetch_base_files(self, start_date=None, start_time=None):
        downloader = FTPDownloader(cfg.FTP_BASE_SETTINGS)
        base_file_paths = downloader.get_unprocessed_files_in_remote_path(
            cfg.FTP_BASE_SETTINGS["data_dir"], 
            cfg.FTP_BASE_SETTINGS["prefix"], 
            cfg.BASE_DATA_DIR
        )
        base_local_file_paths = downloader.generate_local_file_paths(cfg.BASE_DATA_DIR, base_file_paths, start_date, start_time)
        downloader.download_files(base_file_paths, base_local_file_paths)
        downloader.disconnect()

    def process_base_files(self):
        self.t2r.process_all_tps_files_in_path(
            cfg.BASE_DATA_DIR,
            cfg.BASE_DATA_DIR_PROCESSED,
            os.path.join(cfg.DATA_DIR, cfg.FTP_BASE_SETTINGS["local_dir"] + "/tpsprocess.txt")
        )

    def fetch_rover_files(self, settings_list, start_date=None, start_time=None):
        for settings in settings_list:
            rover_local_dir = os.path.join(cfg.DATA_DIR, settings["local_dir"])
            rover_data_dir = os.path.join(rover_local_dir, "raw")

            downloader = FTPDownloader(settings)
            rover_file_paths = downloader.get_unprocessed_files_in_remote_path(
                settings["data_dir"], 
                settings["prefix"], 
                rover_data_dir
            )
            rover_local_file_paths = downloader.generate_local_file_paths(rover_data_dir, rover_file_paths, start_date, start_time)
            downloader.download_files(rover_file_paths, rover_local_file_paths)
            downloader.disconnect()

    def process_rover_files(self, settings_list):
        for settings in settings_list:
            rover_local_dir = os.path.join(cfg.DATA_DIR, settings["local_dir"])
            rover_data_dir = os.path.join(rover_local_dir, "raw")
            rover_data_dir_processed = os.path.join(rover_local_dir, "process")
            self.t2r.process_all_tps_files_in_path(
                rover_data_dir,
                rover_data_dir_processed,
                os.path.join(rover_local_dir, "tpsprocess.txt")
            )

    def process_rnx2rtkp(self, settings_list, data_rover_east, data_rover_north, data_rover_up):
        base_tps_file_names = self.t2r.get_tps_file_names(cfg.BASE_DATA_DIR_PROCESSED.replace("\\", "/"))
        base_file_prefix = cfg.FTP_BASE_SETTINGS["prefix"]

        for settings in settings_list:
            self._process_single_rover(
                settings, 
                base_tps_file_names, 
                base_file_prefix,
                data_rover_east,
                data_rover_north,
                data_rover_up
            )

    def _process_single_rover(self, settings, base_tps_file_names, base_file_prefix,
                            data_rover_east, data_rover_north, data_rover_up):
        rover_local_dir = os.path.join(cfg.DATA_DIR, settings["local_dir"])
        rover_data_dir_processed = os.path.join(rover_local_dir, "process")
        rover_output_dir = os.path.join(rover_local_dir, "output")
        rover_output_file_path = os.path.join(rover_local_dir, "output.csv")

        tps_file_groups = self.r2r.generate_input_file_groups(
            base_tps_file_names, 
            rover_data_dir_processed, 
            base_file_prefix, 
            settings["prefix"]
        )

        helpers.create_dir_if_not_exists(rover_output_dir)
        
        pool = ThreadPool(50)
        pool_payload = [(file_group, rover_output_dir) for file_group in tps_file_groups]
        pool.starmap(self.r2r.process_file_group, pool_payload)

        self._process_pos_files(
            rover_output_file_path,
            rover_output_dir,
            rover_local_dir,
            data_rover_east,
            data_rover_north,
            data_rover_up
        )

    def _process_pos_files(self, output_file_path, output_dir, local_dir,
                          data_rover_east, data_rover_north, data_rover_up):
        self.rtkpos = RTKPos(local_dir)
        self.rtkpos.create_output_file(output_file_path)
        time.sleep(1)
        rtkp_output_log_path = os.path.join(local_dir, "posprocess.txt")
        rtkp_output_file_paths = self.rtkpos.get_unprocessed_rtkp_output_file_paths(
            output_dir,
            rtkp_output_log_path
        )

        last_output = self.get_last_output(output_file_path)
        if last_output:
            self.last_x = last_output["averageX"]
            self.last_y = last_output["averageY"]
            self.last_z = last_output["averageZ"]

        with open(output_file_path, "a") as output_file:
            self._process_rtkp_files(
                rtkp_output_file_paths,
                rtkp_output_log_path,
                output_file,
                data_rover_east,
                data_rover_north,
                data_rover_up
            )

    def _process_rtkp_files(self, file_paths, log_path, output_file,
                           data_rover_east, data_rover_north, data_rover_up):
        for file_path in file_paths:
            if file_path.endswith('.pos.stat') or file_path.endswith('_events.pos'):
                helpers.remove_file(file_path)
                continue

            result = self.rtkpos.calculate_rtkp_output_file(
                file_path, 
                log_path, 
                data_rover_east,
                data_rover_north,
                data_rover_up
            )

            if not result:
                continue

            self._write_output(result, output_file)

    def _write_output(self, result, output_file):
        ts = f'"{result["timestamp"]}"'
        averageX = result["averageX"]
        averageY = result["averageY"]
        averageZ = result["averageZ"]

        if (averageX + averageY + averageZ) == 0:
            output_file.write(f'{ts},"NAN","NAN","NAN"\n')
        elif not (
            self.last_x
            and (
                abs(averageX - self.last_x) > cfg.DATA_THRESHOLD_DELTA_X
                or abs(averageY - self.last_y) > cfg.DATA_THRESHOLD_DELTA_Y
                or abs(averageZ - self.last_z) > cfg.DATA_THRESHOLD_DELTA_Z
            )
        ):
            output_file.write(
                "{},{},{},{}\n".format(
                    ts,
                    "{:.5f}".format(averageX),
                    "{:.5f}".format(averageY),
                    "{:.5f}".format(averageZ)
                )
            )

    def merge_output_files(self):
        rv1_output = os.path.join(os.path.split(os.path.abspath(__file__))[0], "data/Rover1/output.csv")
        rv2_output = os.path.join(os.path.split(os.path.abspath(__file__))[0], "data/Rover2/output.csv")
        df1 = pd.read_csv(rv1_output)
        df2 = pd.read_csv(rv2_output)

        df1['TIMESTAMP'] = pd.to_datetime(df1['TIMESTAMP'])
        df2['TIMESTAMP'] = pd.to_datetime(df2['TIMESTAMP'])

        merged_df = pd.merge(df1, df2, on='TIMESTAMP', how='outer', suffixes=["", ""])
        merged_df['TIMESTAMP'] = merged_df['TIMESTAMP'].apply(lambda x: f'"{x}"')
        merged_df = merged_df.drop_duplicates(["TIMESTAMP"])

        output_file = os.path.join(os.path.split(os.path.abspath(__file__))[0], "data/output.csv")
        merged_df.to_csv(output_file, index=False, quoting=3)

if __name__ == "__main__":
    print("Step 1: Initializing...\n")
    processor = GNSSProcessor()
    reload(cfg)
    
    print("Step 2: Fetch and Pre-process Base...\n")
    #processor.fetch_base_files()
    processor.process_base_files()
    
    print("Step 3: Fetch and Pre-process data from Rover1...\n")
    #processor.fetch_rover_files(cfg.FTP_ROVERS1_SETTINGS)
    processor.process_rover_files(cfg.FTP_ROVERS1_SETTINGS)

    print("Step 4: Converting Rover1 raw data into POS data...")
    processor.process_rnx2rtkp(cfg.FTP_ROVERS1_SETTINGS, cfg.DATA_ROVER1_EAST, cfg.DATA_ROVER1_NORTH, cfg.DATA_ROVER1_UP)
    
    print("Step 5: Fetch and Pre-process data from Rover2...")
    #processor.fetch_rover_files(cfg.FTP_ROVERS2_SETTINGS)
    processor.process_rover_files(cfg.FTP_ROVERS2_SETTINGS)
    
    print("Step 6: Converting Rover2 raw data into POS data...")
    processor.process_rnx2rtkp(cfg.FTP_ROVERS2_SETTINGS, cfg.DATA_ROVER2_EAST, cfg.DATA_ROVER2_NORTH, cfg.DATA_ROVER2_UP)
    
    print("Step 7: Data assembly")
    processor.merge_output_files()
    print("All Processes Done!")