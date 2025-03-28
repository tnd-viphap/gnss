import json
import os
import pyglet
from customtkinter import CTkFont

project_path = os.path.join(os.path.abspath(__file__), "../../../")

class FontManager:
    def __init__(self):
        super().__init__()
        self.data = None
        self._add_fonts()
        self._open_manager()
        
    def _add_fonts(self):
        font_files = os.listdir(project_path + "/common/fonts/packages")
        for file in font_files:
            pyglet.font.add_file(f"./common/fonts/packages/{file}")
        
    def _open_manager(self):
        with open(project_path + "/common/fonts/fonts.json", "r") as font:
            self.data = json.load(font)
            
    def get_font(self, font_name):
        return CTkFont(self.data[font_name]["family"], self.data[font_name]["size"], None, "roman", self.data[font_name]["underline"], self.data[font_name]["overstrike"])
            
if __name__ == "__main__":
    mgr = FontManager()
    print(mgr.data)
        
    