import json
import os

# định nghĩa các biến theo config.json
config_file = open("device_db.json", "r")
config_json = json.load(config_file)

DATA_DIR = config_json["data_dir"]
RNX2RTKP_CONFIG_FILE = config_json["rnx2rtkp_config_file"]
LOGGING = config_json["logging"]

FTP_BASE_SETTINGS = config_json["ftp"]["base"]
FTP_ROVERS1_SETTINGS = config_json["ftp"]["rovers1"]
FTP_ROVERS2_SETTINGS = config_json["ftp"]["rovers2"]

DATA_INTERVAL = config_json["data"]["interval"]
DATA_Q_VALUES = config_json["data"]["q_values"]
DATA_THRESHOLD = config_json["data"]["threshold"]
DATA_THRESHOLD_DELTA_X = config_json["data"]["threshold_delta_x"]
DATA_THRESHOLD_DELTA_Y = config_json["data"]["threshold_delta_y"]
DATA_THRESHOLD_DELTA_Z = config_json["data"]["threshold_delta_z"]
DATA_BASE_LAT = config_json["data"]["base"]["lat"]
DATA_BASE_LON = config_json["data"]["base"]["lon"]
DATA_BASE_HGT = config_json["data"]["base"]["hgt"]
DATA_ROVER1_EAST = config_json["data"]["rover1"]["east"]
DATA_ROVER1_NORTH = config_json["data"]["rover1"]["north"]
DATA_ROVER1_UP = config_json["data"]["rover1"]["up"]
DATA_ROVER2_EAST = config_json["data"]["rover2"]["east"]
DATA_ROVER2_NORTH = config_json["data"]["rover2"]["north"]
DATA_ROVER2_UP = config_json["data"]["rover2"]["up"]

BASE_DATA_DIR = os.path.join(DATA_DIR, FTP_BASE_SETTINGS["local_dir"] + "\\raw")
BASE_DATA_DIR_PROCESSED = os.path.join(DATA_DIR, FTP_BASE_SETTINGS["local_dir"] + "\\process")
