import json
import os
import re
from datetime import datetime, timedelta
import common.parser as cfg
import common.helpers as helpers

class RTKPos:
    def __init__(self, local_dir):
        self.local_dir = local_dir.replace("\\", "/")
        if self.local_dir.split("/")[-1].startswith("Rover1"):
            self.OUTPUT_FILE_HEADERS = ["TIMESTAMP", "Delta_E1(mm)", "Delta_N1(mm)", "Delta_U1(mm)"]
        elif self.local_dir.split("/")[-1].startswith("Rover2"):
            self.OUTPUT_FILE_HEADERS = ["TIMESTAMP", "Delta_E2(mm)", "Delta_N2(mm)", "Delta_U2(mm)"]

    # tao file output, neu file chua ton tai tao moi  them header cho file
    def create_output_file(self, file_path):
        output_file_exists = os.path.exists(file_path)
        output_file = open(file_path, "a")
        if not output_file_exists or (output_file_exists and output_file.tell() == 0):
            output_file.write(",".join(self.OUTPUT_FILE_HEADERS) + "\n")
        output_file.close()

    # lay cac file chua dc xu ly (chua tao thanh file pos) doi chieu qua file log
    def get_unprocessed_rtkp_output_file_paths(self, output_dir, log_path):
        file_paths = []
        with os.scandir(output_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    file_paths.append(os.path.join(output_dir, entry.name))

        if not helpers.check_files_exist([log_path]):
            return file_paths
        log_file = open(log_path, "r")
        log_json = json.load(log_file)
        log_file.close()
        last_processed_file_path = log_json[0]["file_path"]

        need_process_files = []
        for file_path in file_paths:
            if last_processed_file_path and file_path <= last_processed_file_path:
                continue
            need_process_files.append(file_path.replace("\\", "/"))
        return need_process_files
    
    # ham loai bo file co q ko dat yeu cau roi tinh gia tri trung binh
    def calculate_rtkp_output_file(self, file_path, log_path, east, north, up):
        file = open(file_path, "r")
        lines = file.readlines()
        file.close()

        file_path = file_path.replace("\\", "/")
        log_file = open(log_path, "w")
        log_data = [
            {
                "file_path": file_path
            }
        ]
        log_file.write(json.dumps(log_data))
        log_file.close()

        total_e = total_n = total_u = count = 0
        utc_time = datetime.min

        valid_line_data = []
        invalid_q_counter = 0
        for line in lines:
            is_q_valid = self.check_valid_q(line)
            if not is_q_valid:
                invalid_q_counter += 1

            line_data = self.extract_valid_row(line, east, north, up)
            if line_data:
                valid_line_data.append(line_data)

        if invalid_q_counter > len(lines) / 2 or len(valid_line_data)==0:
            return None

        for line_data in valid_line_data:
            utc_time = line_data["utc_time"]

            count += 1
            total_e += line_data["e"]
            total_n += line_data["n"]
            total_u += line_data["u"]

        # Round down to the nearest 30 minutes, with seconds set to 00
        utc_time = utc_time - timedelta(
            minutes=utc_time.minute % cfg.DATA_INTERVAL,
            seconds=utc_time.second,
            microseconds=utc_time.microsecond,
        )

        ts = utc_time.strftime("%Y-%m-%d %H:%M:%S")
        if ts[:4] == "0001":
            return None
        # tinh trung binh
        averageX = float(total_e / count) if count > 0 else 0
        averageY = float(total_n / count) if count > 0 else 0
        averageZ = float(total_u / count) if count > 0 else 0
        
        return {
            "timestamp": f"{ts}",
            "averageX": averageX,
            "averageY": averageY,
            "averageZ": averageZ,
        }

    def check_valid_q(self, row_string):
        if not re.match(r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}", row_string):
            return None

        data = row_string.split(",")

        # Calculate differences and check if they are within the threshold
        q_value = int(data[4])
        if not q_value in cfg.DATA_Q_VALUES:
            return None

        return True
    # ham hieu chuan lai du lieu theo q, ns va nguong cat tren duoi
    def extract_valid_row(self, row_string, east, north, up):
        if not re.match(r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}", row_string):
            return None

        data = row_string.split(",")

        # Calculate differences and check if they are within the threshold
        q_value = int(data[4])
        if not q_value in cfg.DATA_Q_VALUES:
            return None
        # tra ve none khi du lieu co so ve tinh nho hon 5
        ns = int(data[5])
        if ns < 9:
            return None
        # loai bo theo nguong
        e = (float(data[1]) - east) * 1000
        if abs(e) >= cfg.DATA_THRESHOLD:
            return None

        n = (float(data[2]) - north) * 1000
        if abs(n) >= cfg.DATA_THRESHOLD:
            return None

        u = (float(data[3]) - up) * 1000
        if abs(u) >= cfg.DATA_THRESHOLD:
            return None
        # tra ve json 4 truong: thoi gian, e,n,u
        return {
            "utc_time": datetime.strptime(data[0], "%Y/%m/%d %H:%M:%S.%f") + timedelta(hours=8),
            "e": e,
            "n": n,
            "u": u,
        }
