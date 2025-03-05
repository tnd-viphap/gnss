import os
from ftplib import FTP, error_perm
import common.helpers as helpers

class FTPDownloader:
    def __init__(self, credentials):
        self.ftp = FTP()
        self.ftp.set_pasv(False)
        self.credentials = credentials
        self.connect()
        #self.ftp.dir()

    def connect(self):
        """Connect to FTP server"""
        try:
            self.ftp.connect(
                self.credentials["host"],
                self.credentials["port"],
                self.credentials["timeout"],
            )
            self.ftp.login(self.credentials["username"], self.credentials["password"])
        except Exception as e:
            print(f"Connection error: {e}")
            raise

    def disconnect(self):
        """Disconnect from FTP server"""
        try:
            self.ftp.quit()
        except Exception as e:
            print(f"Disconnect error: {e}")
            self.ftp.close()

    def get_unprocessed_files_in_remote_path(self, remote_dir, prefix, local_dir):
        """Get list of unprocessed files from remote directory"""
        try:
            self.ftp.cwd(remote_dir)
            files = self.ftp.nlst()
            files = files[2:]  # Remove '.' and '..' entries

            if not files:
                return []

            result = []
            for file in files:
                if helpers.check_file_name_exists_in_dir(file, local_dir):
                    continue
                if file.startswith(prefix):
                    result.append(os.path.join(remote_dir, file))
            result.sort()

            return result[:-1] if result else []

        except Exception as e:
            print(f"Error getting unprocessed files: {e}")
            return []

    def generate_local_file_paths(self, local_dir, remote_file_paths):
        """Generate local file paths for downloads"""
        try:
            helpers.create_dir_if_not_exists(local_dir)
            return [os.path.join(local_dir, os.path.basename(path)) 
                   for path in remote_file_paths]
        except Exception as e:
            print(f"Error generating local paths: {e}")
            return []

    def download_files(self, remote_file_paths, local_file_paths):
        """Download multiple files"""
        for remote_path, local_path in zip(remote_file_paths, local_file_paths):
            index = remote_file_paths.index(remote_path)
            if not os.path.exists(local_path):
                self.download_file(index, remote_path, local_path)

    def download_file(self, index, remote_file_path, local_file_path):
        """Download single file with basic error handling"""
        print(f"[{index}] Downloading {remote_file_path}")

        try:
            with open(local_file_path, 'wb') as file:
                self.ftp.retrbinary(f"RETR {remote_file_path}", file.write)
            
            # Basic verification: check if file exists and has size > 0
            if not os.path.exists(local_file_path) or os.path.getsize(local_file_path) == 0:
                raise Exception("Download failed or file is empty")

            print(f"-> Successfully downloaded {remote_file_path}")

        except Exception as e:
            print(f"-> ERROR in download {remote_file_path}: {e}")
            if os.path.exists(local_file_path):
                helpers.remove_file(local_file_path)