import os
import subprocess
import json
import sys
import common.parser as cfg
import common.helpers as helpers

sys.path.append(os.path.join(os.path.dirname(__file__), '../../modules'))

class TPS2RINProcessor:
    def __init__(self):
        self.cur_dir = os.path.split(os.path.abspath(__file__))[0]

    def get_tps_file_names(self, dir_path):
        """
        Extract unique file names from directory without extensions
        """
        file_names = []
        with os.scandir(dir_path) as entries:
            for entry in entries:
                if entry.is_file():
                    file_name = os.path.splitext(entry.name)[0]
                    file_names.append(file_name)
        return list(set(file_names))

    def process_all_tps_files_in_path(self, input_dir, output_dir, processed_path):
        """
        Process all TPS files in the input directory that haven't been processed yet
        """
        self._prepare_output_directory(output_dir)
        last_processed_file_path = self._get_last_processed_file(processed_path)
        need_process_files = self._get_files_to_process(input_dir, last_processed_file_path)
        
        self._process_files(need_process_files, output_dir, processed_path)

    def _prepare_output_directory(self, output_dir):
        """
        Create output directory if it doesn't exist and clear its contents
        """
        helpers.create_dir_if_not_exists(output_dir)
        helpers.clear_folder_content(output_dir)

    def _get_last_processed_file(self, processed_path):
        """
        Get the path of the last processed file from the log
        """
        if not helpers.check_files_exist([processed_path]):
            return None
        with open(processed_path, "r") as log_file:
            log_json = json.load(log_file)
            if log_json:
                return log_json[0]["file_path"]
            else:
                return None

    def _get_files_to_process(self, input_dir, last_processed_file_path):
        """
        Get list of files that need to be processed
        """
        files = os.listdir(input_dir)
        need_process_files = []
        
        for i in range(len(files)):
            file_path = os.path.join(input_dir, files[i])
            if last_processed_file_path and file_path <= last_processed_file_path:
                break
            need_process_files.append(file_path)
        return list(sorted(need_process_files))

    def _process_files(self, files_to_process, output_dir, processed_path):
        """
        Process each file and update the log
        """
        for i in range(len(files_to_process)):
            if self.exec_tps2rin(files_to_process[i], output_dir):
                self._update_process_log(processed_path, files_to_process[i])
                pass
            else:
                print(f"-> {files_to_process[i]} processed. Skipping...")
                continue

    def exec_tps2rin(self, tps_file_path, output_dir):
        """
        Execute the tps2rin command for a single file
        """
        try:
            os.chdir(self.cur_dir)
            cmd = f'tps2rin.exe -i "{tps_file_path}" -o "{output_dir}"'
            subprocess.call(cmd, shell=cfg.LOGGING)
            os.chdir("..")
            return True
        except Exception as e:
            print(f"-> Error executing tps2rin: {e}")
            return False

    def _update_process_log(self, processed_path, file_path):
        """
        Append new processed file information to the log file
        """
        try:
            # Add new entry
            file_path = file_path.replace("\\", "/")
            new_entry = [
                {
                    "file_path": file_path
                }
            ]

            # Write back all data
            with open(processed_path, 'w') as log_file:
                json.dump(new_entry, log_file, indent=4)

        except Exception as e:
            print(f"Error updating process log: {e}")

# Example usage:
if __name__ == "__main__":
    processor = TPS2RINProcessor()
    # Example calls would go here
    # file_names = processor.get_tps_file_names(input_directory)
    # processor.process_all_tps_files_in_path(input_dir, output_dir, processed_path)