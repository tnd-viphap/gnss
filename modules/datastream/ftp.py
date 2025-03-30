import os
import time
from ftplib import FTP, error_perm
import common.helpers as helpers
from common.helpers import Signal

class FTPDownloader:
    def __init__(self, credentials, progress_signal=None, error_signal=None, status_signal=None):
        self.ftp = None
        self.credentials = credentials
        self.progress_signal = progress_signal
        self.error_signal = error_signal
        self.status_signal = status_signal
        self.last_activity = time.time()
        self.timeout = credentials.get("timeout", 60)  # Default 60 seconds timeout
        self.connect()

    def connect(self):
        """Connect to FTP server with timeout handling"""
        try:
            self.ftp = FTP()
            self.ftp.set_pasv(False)
            self.ftp.connect(
                self.credentials["host"],
                self.credentials["port"],
                self.timeout,
            )
            self.ftp.login(self.credentials["username"], self.credentials["password"])
            self.last_activity = time.time()
        except Exception as e:
            print(f"-> Connection error: {e}")
            raise

    def disconnect(self):
        """Disconnect from FTP server"""
        try:
            if self.ftp:
                self.ftp.quit()
                self.ftp = None
        except Exception as e:
            print(f"-> Disconnect error: {e}")
            if self.ftp:
                self.ftp.close()
                self.ftp = None

    def check_connection(self):
        """Check if connection is alive and reconnect if needed"""
        try:
            # Check if connection timed out
            if time.time() - self.last_activity > self.timeout:
                print("-> Connection timed out, reconnecting...")
                self.reconnect()
                return

            # Test connection with a simple command
            self.ftp.voidcmd("NOOP")
            self.last_activity = time.time()
        except:
            print("-> Connection lost, reconnecting...")
            self.reconnect()

    def reconnect(self):
        """Reconnect to FTP server"""
        try:
            self.disconnect()
            time.sleep(1)  # Wait before reconnecting
            self.connect()
        except Exception as e:
            print(f"-> Reconnection failed: {e}")
            raise

    def get_unprocessed_files_in_remote_path(self, remote_dir, prefix, local_dir):
        """Get list of unprocessed files from remote directory"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.check_connection()
                self.ftp.cwd(remote_dir)
                files = self.ftp.nlst()
                files = files[2:]  # Remove '.' and '..' entries

                if not files:
                    return []

                result = []
                for file in files:
                    local_file_path = os.path.join(local_dir, file)
                    if os.path.exists(local_file_path) and os.path.getsize(local_file_path) > 2000:
                        continue
                    if file.startswith(prefix):
                        result.append(os.path.join(remote_dir, file))
                result.sort()
                result = result[:-1] if result else []
                self.status_signal.emit(f"Downloading {len(result)} files...")
                return result

            except Exception as e:
                print(f"-> Error getting unprocessed files (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    self.reconnect()
                    time.sleep(2)  # Wait before retry
                else:
                    return []

    def generate_local_file_paths(self, local_dir, remote_file_paths, start_date=None, start_time=None):
        """Generate local file paths for downloads"""
        try:
            helpers.create_dir_if_not_exists(local_dir)
            if start_date:
                if start_time:
                    str2search = "_".join(remote_file_paths[0].split("_")[0:2]) + f"_{start_date}{start_time}"
                    idx = remote_file_paths.index(str2search)
                else:
                    start_time = 'a'
                    str2search = "_".join(remote_file_paths[0].split("_")[0:2]) + f"_{start_date}{start_time}"
                    idx = remote_file_paths.index(str2search)
            else:
                idx = 0
            remote_file_paths = remote_file_paths[idx:]
            return idx, [os.path.join(local_dir, os.path.basename(path)) for path in remote_file_paths]

        except Exception as e:
            self.error_signal.emit(f"Error generating local paths: {e}")
            return []

    def download_files(self, remote_file_paths, local_file_paths):
        """Download multiple files with connection checking"""
        for remote_path, local_path in zip(remote_file_paths, local_file_paths):
            index = remote_file_paths.index(remote_path)
            if (not os.path.exists(local_path)) or (os.path.exists(local_path) and float(os.path.getsize(local_path))/1024**2 < 2000):
                self.download_file_with_retry(index, remote_path, local_path)
                if self.progress_signal:
                    self.progress_signal.emit(index/len(remote_file_paths))
            else:
                self.error_signal.emit(f"-> File already exists: {os.path.basename(local_path)}")

    def download_file_with_retry(self, index, remote_file_path, local_file_path):
        """Download single file with retries and connection checking"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.check_connection()
                self.download_file(index, remote_file_path, local_file_path)
                return  # Success
            except Exception as e:
                self.error_signal.emit(f"-> Download attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    self.reconnect()
                    time.sleep(2)  # Wait before retry
                else:
                    self.error_signal.emit(f"-> Failed to download after {max_retries} attempts")

    def download_file(self, index, remote_file_path, local_file_path):
        """Download single file with progress monitoring"""
        print(f"[{index}] Downloading {remote_file_path}")
        self.status_signal.emit(f"Downloading {remote_file_path}")

        try:
            with open(local_file_path, 'wb') as file:
                def callback(data):
                    file.write(data)
                    self.last_activity = time.time()  # Update activity timestamp

                self.ftp.retrbinary(f"RETR {remote_file_path}", callback)
            
            if not os.path.exists(local_file_path) or os.path.getsize(local_file_path) == 0:
                self.error_signal.emit(f"-> Download failed or file is empty: {remote_file_path}")
                raise Exception("-> Download failed or file is empty")

            print(f"-> Successfully downloaded {remote_file_path}")
            self.status_signal.emit(f"Successfully downloaded {remote_file_path}")

        except Exception as e:
            print(f"-> ERROR in download {remote_file_path}: {e}")
            self.error_signal.emit(f"-> ERROR in download {remote_file_path}: {e}")
            if os.path.exists(local_file_path):
                helpers.remove_file(local_file_path)
            raise  # Re-raise for retry handling