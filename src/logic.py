import os
import json
import shutil
import time

# Constants
CONFIG_FILE = "img_compare_settings.json"
STANDARD_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.gif', '.webp')
RAW_EXTS = ('.arw', '.cr2', '.cr3', '.nef', '.dng', '.orf', '.raf', '.rw2', '.pef', '.srw')
VALID_EXTENSIONS = STANDARD_EXTS + RAW_EXTS

class AppState:
    def __init__(self):
        self.theme = "dark"
        self.last_output_dir = "" 
        self.window_geometry = "" 
        self.is_maximized = False
    
    def load_settings(self, filepath=CONFIG_FILE):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    self.theme = data.get("theme", "dark")
                    self.last_output_dir = data.get("output_dir", "")
                    self.window_geometry = data.get("window_geometry", "")
                    self.is_maximized = data.get("is_maximized", False)
            except Exception:
                # Silent fail on load is usually preferred (use defaults)
                pass

    def save_settings(self, filepath=CONFIG_FILE):
        try:
            with open(filepath, "w") as f:
                data = {
                    "theme": self.theme,
                    "output_dir": self.last_output_dir,
                    "window_geometry": self.window_geometry,
                    "is_maximized": self.is_maximized
                }
                json.dump(data, f, indent=4)
            return True, ""
        except Exception as e:
            return False, str(e)

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        return self.theme

class FileScanner:
    @staticmethod
    def scan(folders):
        """
        Scans folders.
        Returns: (grouped_files, sorted_basenames, total_files, error_list)
        """
        if not folders:
            return {}, [], 0, []

        temp_map = {}
        total_files = 0
        error_list = []

        for folder in folders:
            if not os.path.exists(folder):
                error_list.append(f"Folder not found: {folder}")
                continue
                
            try:
                files = os.listdir(folder)
                for f in files:
                    if f.lower().endswith(VALID_EXTENSIONS):
                        basename = os.path.splitext(f)[0].lower()
                        if basename not in temp_map: temp_map[basename] = []
                        temp_map[basename].append(os.path.join(folder, f))
                        total_files += 1
            except Exception as e:
                # Collect error string instead of printing
                error_list.append(f"Error reading '{os.path.basename(folder)}': {str(e)}")

        grouped_files = {k: v for k, v in temp_map.items() if len(v) >= 2}
        sorted_basenames = sorted(grouped_files.keys())
        
        return grouped_files, sorted_basenames, total_files, error_list

class FileManager:
    @staticmethod
    def copy_to_output(source_path, output_dir):
        if not output_dir or not os.path.exists(output_dir):
            return False, "Output directory not set or does not exist."
            
        try:
            filename = os.path.basename(source_path)
            destination = os.path.join(output_dir, filename)
            
            if os.path.exists(destination):
                name, ext = os.path.splitext(filename)
                timestamp = int(time.time())
                destination = os.path.join(output_dir, f"{name}_{timestamp}{ext}")

            shutil.copy2(source_path, destination)
            return True, f"Saved to {os.path.basename(destination)}"
        except Exception as e:
            return False, str(e)