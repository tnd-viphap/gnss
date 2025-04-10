import os
import shutil
import subprocess
import sys
import time

import common.helpers as helpers
import common.parser as cfg


class RNX2RTKPProcessor:
    def __init__(self):
        self.cur_dir = os.path.split(os.path.abspath(__file__))[0]
        self.config_file = os.path.join(self.cur_dir, cfg.RNX2RTKP_CONFIG_FILE).replace("\\", "/")

    def generate_input_file_groups(self, base_file_names, rover_processed_dir, base_prefix, rover_prefix):
        """
        Generate groups of input files for processing
        Returns list of dictionaries containing file paths for base and rover data
        """
        groups = []
        files = list(sorted(base_file_names, key=lambda x: x[4:]))
        for file_name in files:
            time_name = file_name[4:]

            file_paths = {
                "obs_base_file": os.path.join(cfg.BASE_DATA_DIR_PROCESSED, f"{file_name}.25o").replace("\\", "/"),
                "nav_base_file": os.path.join(cfg.BASE_DATA_DIR_PROCESSED, f"{file_name}.25p").replace("\\", "/"),
                "obs_rover_file": os.path.join(rover_processed_dir, f"rove{time_name}.25o").replace("\\", "/"),
                "nav_rover_file": os.path.join(rover_processed_dir, f"rove{time_name}.25p").replace("\\", "/")
            }

            if self._check_all_files_exist(file_paths):
                file_paths["time_name"] = time_name
                groups.append(file_paths)
        return groups

    def _check_all_files_exist(self, file_paths):
        """
        Check if all required files exist
        """
        required_files = [
            file_paths["obs_base_file"],
            file_paths["nav_base_file"],
            file_paths["obs_rover_file"],
            file_paths["nav_rover_file"]
        ]
        return helpers.check_files_exist(required_files)

    def process_file_group(self, group, output_dir):
        """
        Process a group of files and remove rover files if successful
        """
        output_file = os.path.join(output_dir, f"output_{group['time_name']}.pos").replace("\\", "/")
        os.chdir(self.cur_dir)
        _ = self.exec_rnx2rtkp(
            group["obs_rover_file"],
            group["obs_base_file"],
            group["nav_base_file"],
            output_file
        )
        self._remove_rover_files(group)

    def exec_rnx2rtkp(self, obs_rover_file, obs_base_file, nav_base_file, output_file):
        """
        Execute the rnx2rtkp command
        """
        for file in [obs_rover_file, obs_base_file, nav_base_file]:
            if file == obs_rover_file:
                os.system(f"mv {file} {self.cur_dir}")
            else:
                shutil.copy(file, self.cur_dir)
        
        cmd = f'rnx2rtkp -k {self.config_file} -s , -o {output_file} {os.path.split(obs_rover_file)[-1]} {os.path.split(obs_base_file)[-1]} {os.path.split(nav_base_file)[-1]}'
        process = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        results = process.communicate()
        print(results[1].decode())
        if results[1].decode():
            return False
        else:
            for file in [obs_rover_file, obs_base_file, nav_base_file]:
                os.remove(os.path.join(self.cur_dir, os.path.split(file)[1]))
            return True

    def _remove_rover_files(self, group):
        """
        Remove rover-related files
        """
        helpers.remove_file(group["obs_rover_file"])
        helpers.remove_file(group["nav_rover_file"])

    def _remove_all_files(self, group):
        """
        Remove all related files
        """
        helpers.remove_file(group["obs_base_file"])
        helpers.remove_file(group["nav_base_file"])
        helpers.remove_file(group["obs_rover_file"])
        helpers.remove_file(group["nav_rover_file"])

# Example usage:
if __name__ == "__main__":
    # from tps2rin import TPS2RINProcessor
    # processor = RNX2RTKPProcessor()
    # # Example calls would go here
    # base_file_names = TPS2RINProcessor().get_tps_file_names(cfg.BASE_DATA_DIR_PROCESSED)
    # base_prefix = cfg.FTP_BASE_SETTINGS["prefix"]
    # rover_prefix = cfg.FTP_ROVERS2_SETTINGS[0]["prefix"]
    # rover_local_dir = os.path.join(cfg.DATA_DIR, cfg.FTP_ROVERS2_SETTINGS[0]["local_dir"]).replace("\\", "/")
    # rover_processed_dir = os.path.join(rover_local_dir, "process").replace("\\", "/")
    # output_dir = os.path.join(rover_local_dir, "output").replace("\\", "/")
    # groups = processor.generate_input_file_groups(base_file_names, rover_processed_dir, base_prefix, rover_prefix)
    # for group in groups:
    #     processor.process_file_group(group, output_dir)
    None