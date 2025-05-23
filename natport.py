from modules.datastream.ftp import FTPDownloader
import common.parser as cfg

if __name__ == "__main__":
    creds = {
        "host": "10.0.1.18",
        "port": 9921,
        "username": "topcon",
        "password": "topcon",
        "passive": "true",
        "timeout": 60,
        "data_dir": "\\",
        "local_dir": "Rover2",
        "prefix": "Rover2_3600_"

    }

    downloader = FTPDownloader(creds)
    try:
        downloader.connect()
        print(downloader.get_unprocessed_files_in_remote_path(creds["data_dir"], creds["prefix"], "dev/output/"))
        print(f"{creds['local_dir']} is working")
    except:
        downloader.disconnect()
    finally:
        print(f"{creds['local_dir']} is disconnected")
        downloader.disconnect()