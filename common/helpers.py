import os
import shutil
import threading
from typing import List, Callable, Any

# các hàm hỗ trợ
# hàm xóa file
def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

# hàm kiểm tra thư mục đã được tạo hay chưa
def check_files_exist(file_paths):
    return all(os.path.exists(path) for path in file_paths)

# tạo folder mới khi folder chưa được tạo
def create_dir_if_not_exists(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def clear_folder_content(dir):
    for filename in os.listdir(dir):
        file_path = os.path.join(dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('-> Failed to delete %s. Reason: %s' % (file_path, e))


def check_file_name_exists_in_dir(file_name, dir):
    return os.path.exists(os.path.join(dir, file_name))


class Signal:
    """A class that mimics PyQt's signal functionality"""
    def __init__(self):
        self._slots: List[Callable] = []
        self._lock = threading.Lock()
        
    def connect(self, slot: Callable) -> None:
        """Connect a slot to this signal"""
        with self._lock:
            if slot not in self._slots:
                self._slots.append(slot)
                
    def disconnect(self, slot: Callable) -> None:
        """Disconnect a slot from this signal"""
        with self._lock:
            if slot in self._slots:
                self._slots.remove(slot)
                
    def emit(self, *args: Any, **kwargs: Any) -> None:
        """Emit the signal with the given arguments"""
        with self._lock:
            for slot in self._slots:
                try:
                    slot(*args, **kwargs)
                except Exception as e:
                    print(f"Error in signal slot: {str(e)}")
                    
    def disconnect_all(self) -> None:
        """Disconnect all slots from this signal"""
        with self._lock:
            self._slots.clear()
