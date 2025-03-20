import os
import subprocess
import common.parser as cfg
import common.helpers as helpers

class RNX2RTKPProcessor:
    def __init__(self):
        self.cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.bin_file = os.path.join(self.cur_dir, "rnx2rtkp.exe")
        self.config_file = os.path.join(self.cur_dir, cfg.RNX2RTKP_CONFIG_FILE)

    def generate_input_file_groups(self, base_file_names, rover_processed_dir, base_prefix, rover_prefix):
        """
        Generate groups of input files for processing
        Returns list of dictionaries containing file paths for base and rover data
        """
        groups = []
        for file_name in base_file_names:
            time_name = file_name[4:]

            file_paths = {
                "obs_base_file": os.path.join(cfg.BASE_DATA_DIR_PROCESSED, f"{file_name}.25o"),
                "nav_base_file": os.path.join(cfg.BASE_DATA_DIR_PROCESSED, f"{file_name}.25p"),
                "obs_rover_file": os.path.join(rover_processed_dir, f"rove{time_name}.25o"),
                "nav_rover_file": os.path.join(rover_processed_dir, f"rove{time_name}.25p")
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
            file_paths["nav_base_file"]
        ]
        return helpers.check_files_exist(required_files)

    def process_file_group(self, group, output_dir):
        """
        Process a group of files and remove rover files if successful
        """
        output_file = os.path.join(output_dir, f"output_{group['time_name']}.pos")
        success = self._exec_rnx2rtkp(
            group["obs_rover_file"],
            group["obs_base_file"],
            group["nav_base_file"],
            output_file
        )

        if success:
            self._remove_rover_files(group)

    def process_file_group_and_remove(self, group, output_dir):
        """
        Process a group of files and remove all files if successful
        """
        output_file = os.path.join(output_dir, f"output_{group['time_name']}.pos")
        success = self._exec_rnx2rtkp(
            group["obs_rover_file"],
            group["obs_base_file"],
            group["nav_base_file"],
            output_file
        )

        if success:
            self._remove_all_files(group)

    def _exec_rnx2rtkp(self, obs_rover_file, obs_base_file, nav_rover_file, output_file):
        """
        Execute the rnx2rtkp command
        """
        try:
            cmd = f'{self.bin_file} -k {self.config_file} -s , -o "{output_file}" "{obs_rover_file}" "{obs_base_file}" "{nav_rover_file}"'
            error_code = subprocess.call(cmd, shell=cfg.LOGGING)
            return error_code == 0
        except Exception as e:
            print(f"Error: {e}")
            return False

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
    processor = RNX2RTKPProcessor()
    # Example calls would go here
    # groups = processor.generate_input_file_groups(base_file_names, rover_processed_dir, base_prefix, rover_prefix)
    # for group in groups:
    #     processor.process_file_group(group, output_dir)