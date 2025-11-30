import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import rawpy
import os
import sys

# --- ROBUST IMPORT FOR LOGIC ---
try:
    from src.logic import AppState, FileScanner, FileManager, VALID_EXTENSIONS, RAW_EXTS
except ImportError:
    from .logic import AppState, FileScanner, FileManager, VALID_EXTENSIONS, RAW_EXTS

# --- ROBUST IMPORT FOR ICON FACTORY ---
try:
    from src.icon_factory import generate_icon_image
except ImportError:
    from .icon_factory import generate_icon_image
# ----------------------------------------

# Colors
THEMES = {
    "dark": {
        "bg_main": "#262626", "bg_container": "#1e1e1e", "bg_canvas": "#0b0b0b",
        "fg_text": "#dcdcdc", "btn_bg": "#444444", "btn_fg": "#ffffff", "highlight": "#555555"
    },
    "light": {
        "bg_main": "#f0f0f0", "bg_container": "#e0e0e0", "bg_canvas": "#ffffff",
        "fg_text": "#000000", "btn_bg": "#dddddd", "btn_fg": "#000000", "highlight": "#cccccc"
    }
}

class SyncImageComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("MultiCompare")
        
        # 1. State Load
        self.state = AppState()
        self.state.load_settings()
        
        # 2. Geometry / 75% Screen Logic
        if self.state.window_geometry:
            self.root.geometry(self.state.window_geometry)
            if self.state.is_maximized:
                try:
                    self.root.state("zoomed") # Windows
                except tk.TclError:
                    try:
                        self.root.attributes("-zoomed", True) # Linux
                    except tk.TclError:
                        pass
        else:
            # Default to 75% of screen
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            w = int(screen_w * 0.75)
            h = int(screen_h * 0.75)
            x = (screen_w - w) // 2
            y = (screen_h - h) // 2
            self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.selected_folders = []
        self.grouped_files = {}
        self.sorted_basenames = []
        self.current_index = -1
        self.output_dir = self.state.last_output_dir
        
        # Image Specific
        self.cached_images = []
        self.raw_images = []
        self.CACHED_MAX_SIDE = 2500 
        self.INITIAL_ZOOM_SCALE = 0.55
        
        # View Data
        self.raw_images = []
        self.images_ref = []
        self.canvases = []
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.drag_start = None

        self.set_window_icon()
        self.setup_ui()
        self.apply_theme()

    def on_close(self):
        """Save window geometry before exiting."""
        is_max = False
        try:
            if self.root.state() == 'zoomed':
                is_max = True
        except tk.TclError:
            pass
            
        if not is_max:
            try:
                if self.root.attributes('-zoomed'):
                    is_max = True
            except tk.TclError:
                pass 
        
        self.state.is_maximized = is_max
        
        if not is_max:
            self.state.window_geometry = self.root.geometry()
            
        self.state.save_settings()
        self.root.destroy()

    def set_window_icon(self):
        """
        Sets the window icon with high-quality fallback logic.
        """
        try:
            base_path = os.path.dirname(os.path.dirname(__file__)) 
            assets_dir = os.path.join(base_path, "assets")
            
            # A. Try File Loading
            if os.name == 'nt': 
                icon_path = os.path.join(assets_dir, "icon.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    return 
            
            icon_path = os.path.join(assets_dir, "icon.png")
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, img)
                return

            # B. Fallback: Generate in Memory (High Quality)
            print("[Icon] Assets missing. Generating runtime icons...")
            sizes = [16, 32, 48, 64, 128, 256]
            icons = []
            
            for s in sizes:
                pil_img = generate_icon_image(size=s)
                icons.append(ImageTk.PhotoImage(pil_img))
            
            self.root.iconphoto(True, *icons)

        except Exception as e:
            print(f"[Icon] Error setting icon: {e}")

    def setup_ui(self):
        # --- Control Bar ---
        self.control_frame = tk.Frame(self.root, pady=10, padx=5)
        self.control_frame.pack(side=tk.TOP, fill=tk.X)
        
        # 1. Left Button Group
        self.frame_left = tk.Frame(self.control_frame)
        self.frame_left.pack(side=tk.LEFT, fill=tk.Y)
        
        # [Add Folders]
        tk.Button(self.frame_left, text="Add Folders", command=self.add_folder).pack(side=tk.LEFT, padx=2)
        
        # [Set Output] -> MOVED HERE
        self.btn_output = tk.Button(self.frame_left, text="Set Output", command=self.set_output_dir)
        self.btn_output.pack(side=tk.LEFT, padx=2)
        
        if self.output_dir:
            name = os.path.basename(self.output_dir) or self.output_dir
            self.btn_output.config(text=f"Out: {name}")
        
        # [Scan] -> MOVED HERE (To the right of Output)
        tk.Button(self.frame_left, text="Scan", command=self.scan_files).pack(side=tk.LEFT, padx=2)
        
        # [Theme]
        tk.Button(self.frame_left, text="🌗", command=self.toggle_theme, width=3).pack(side=tk.LEFT, padx=10)

        # 2. Right Button Group
        self.frame_right = tk.Frame(self.control_frame)
        self.frame_right.pack(side=tk.RIGHT, fill=tk.Y)
        
        # [Counter] -> MOVED HERE (To the left of Prev/Next)
        self.lbl_status = tk.Label(self.frame_right, text="0 / 0", width=12)
        self.lbl_status.pack(side=tk.LEFT, padx=5)

        # [Prev]
        self.btn_prev = tk.Button(self.frame_right, text="< Prev", command=self.prev_group, state=tk.DISABLED)
        self.btn_prev.pack(side=tk.LEFT, padx=2)

        # [Next]
        self.btn_next = tk.Button(self.frame_right, text="Next >", command=self.next_group, state=tk.DISABLED)
        self.btn_next.pack(side=tk.LEFT, padx=2)

        # 3. CENTER TITLE (Absolute Positioning)
        self.lbl_current_file = tk.Label(self.control_frame, text="MultiCompare", font=("Arial", 14, "bold"))
        self.lbl_current_file.place(relx=0.5, rely=0.5, anchor="center")

        # --- Main Grid ---
        self.grid_frame = tk.Frame(self.root)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)

        self.root.bind("<Right>", lambda e: self.next_group())
        self.root.bind("<Left>", lambda e: self.prev_group())

    def toggle_theme(self):
        self.state.toggle_theme()
        self.state.save_settings() 
        self.apply_theme()

    def apply_theme(self):
        colors = THEMES[self.state.theme]
        self.root.configure(bg=colors["bg_main"])
        self.control_frame.configure(bg=colors["bg_main"])
        self.frame_left.configure(bg=colors["bg_main"])
        self.frame_right.configure(bg=colors["bg_main"])
        self.grid_frame.configure(bg=colors["bg_container"])
        
        self.lbl_status.configure(bg=colors["bg_main"], fg=colors["fg_text"])
        self.lbl_current_file.configure(bg=colors["bg_main"], fg=colors["fg_text"])
        
        self.update_widget_colors(self.control_frame, colors)

    def update_widget_colors(self, parent, colors):
        """Helper to recursively color widgets"""
        for widget in parent.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=colors["bg_main"])
                self.update_widget_colors(widget, colors)
            elif isinstance(widget, tk.Button):
                widget.configure(bg=colors["btn_bg"], fg=colors["btn_fg"], activebackground=colors["highlight"])

    def add_folder(self):
        path = filedialog.askdirectory()
        if path and path not in self.selected_folders:
            self.selected_folders.append(path)
            self.lbl_current_file.config(text=f"{len(self.selected_folders)} Folders Loaded")

    def set_output_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir = path
            self.state.last_output_dir = path
            self.state.save_settings() 
            name = os.path.basename(path) or path
            self.btn_output.config(text=f"Out: {name}")

    def scan_files(self):
        self.root.config(cursor="watch")
        self.lbl_current_file.config(text="Scanning...")
        self.root.update()
        
        self.grouped_files, self.sorted_basenames, count, errors = FileScanner.scan(self.selected_folders)
        
        self.root.config(cursor="")
        
        if errors:
            err_msg = "\n".join(errors)
            if len(err_msg) > 500: err_msg = err_msg[:500] + "\n..."
            messagebox.showwarning("Scan Issues", f"Some folders could not be scanned:\n\n{err_msg}")

        total_sets = len(self.sorted_basenames)
        
        if total_sets > 0:
            self.current_index = 0
            self.btn_next.config(state=tk.NORMAL)
            self.btn_prev.config(state=tk.NORMAL)
            self.load_group()
        else:
            self.lbl_current_file.config(text="No Matches Found")
            self.lbl_status.config(text="0 / 0")
            if not errors:
                messagebox.showinfo("Result", "No filenames matched across the selected folders.")

    def load_image_file(self, path):
        """Loads the FULL image (no resizing here)."""
        try:
            if path.lower().endswith(RAW_EXTS):
                with rawpy.imread(path) as raw:
                    rgb = raw.postprocess(use_camera_wb=True)
                    return Image.fromarray(rgb)
            else:
                return Image.open(path)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return None

    def load_group(self):
        if not self.sorted_basenames: return

        basename = self.sorted_basenames[self.current_index]
        total_sets = len(self.sorted_basenames)
        
        # Title Updates
        self.lbl_current_file.config(text=basename)
        self.lbl_status.config(text=f"{self.current_index + 1} / {total_sets}")
        self.root.title(f"MultiCompare - {basename}")

        # Clear Caches
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.canvases = []
        self.raw_images = []
        self.cached_images = [] # Clear the cache!
        self.images_ref = []
        
        paths = self.grouped_files[basename][:10]

        # Setup Grid
        n = len(paths)
        cols = 3 if n > 4 else (2 if n > 1 else 1)
        if n > 6: cols = 4
        
        # Set Initial Scale (0.55 = 55% zoom)
        self.scale = self.INITIAL_ZOOM_SCALE
        self.pan_x = 0
        self.pan_y = 0
        
        colors = THEMES[self.state.theme]

        for i, p in enumerate(paths):
            frame = tk.Frame(self.grid_frame, bd=2, bg=colors["highlight"])
            frame.grid(row=i//cols, column=i%cols, sticky="nsew", padx=2, pady=2)
            self.grid_frame.rowconfigure(i//cols, weight=1)
            self.grid_frame.columnconfigure(i%cols, weight=1)
            
            cv = tk.Canvas(frame, bg=colors["bg_canvas"], highlightthickness=0)
            cv.pack(fill=tk.BOTH, expand=True)
            self.canvases.append(cv)
            
            # 1. Load Full-Resolution Image
            full_img = self.load_image_file(p)

            if full_img:
                self.raw_images.append(full_img)
                
                # 2. CREATE THE CACHED, SCREEN-SIZED IMAGE
                # This is the image we will resize during pan/zoom for speed.
                
                # Calculate required downsample size (e.g., max 2500px on the long side)
                w, h = full_img.size
                if w > self.CACHED_MAX_SIDE or h > self.CACHED_MAX_SIDE:
                    ratio = min(self.CACHED_MAX_SIDE / w, self.CACHED_MAX_SIDE / h)
                    nw, nh = int(w * ratio), int(h * ratio)
                    
                    # Use a high-quality filter once for the cache image
                    cached_img = full_img.resize((nw, nh), Image.Resampling.LANCZOS)
                else:
                    cached_img = full_img.copy()

                self.cached_images.append(cached_img)
            else:
                self.raw_images.append(None)
                self.cached_images.append(Image.new('RGB', (100,100), 'gray'))


            # Button and Bindings (remain the same)
            btn = tk.Button(frame, text="SELECT", bg="#2196F3", fg="white",
                            command=lambda path=p: self.select_and_next(path))
            btn.pack(side=tk.BOTTOM, fill=tk.X)

            cv.bind("<ButtonPress-1>", self.start_pan)
            cv.bind("<B1-Motion>", self.do_pan)
            cv.bind("<MouseWheel>", self.do_zoom)
            cv.bind("<Button-4>", self.do_zoom)
            cv.bind("<Button-5>", self.do_zoom)
            cv.bind("<Double-Button-1>", lambda e, path=p: self.select_and_next(path))

        self.root.update_idletasks()
        self.redraw_all()
        
    def redraw_all(self):
        """Redraws all images using the smaller cached image."""
        self.images_ref = []
        for i, cached_raw in enumerate(self.cached_images):
            cv = self.canvases[i]
            cv.delete("all")
            
            # Check for placeholder/error image
            if cached_raw is None:
                continue 

            w, h = cached_raw.size
            nw, nh = int(w * self.scale), int(h * self.scale)
            
            if nw > 0 and nh > 0:
                # PERFORMANCE CRITICAL: Only resizing the smaller cached image.
                resized = cached_raw.resize((nw, nh), Image.Resampling.NEAREST) 
                tk_img = ImageTk.PhotoImage(resized)
                self.images_ref.append(tk_img)
                
                cw = cv.winfo_width()
                ch = cv.winfo_height()
                
                # Center calculation
                cx = cw // 2
                cy = ch // 2
                
                x = cx - (nw // 2) + self.pan_x
                y = cy - (nh // 2) + self.pan_y
                
                cv.create_image(x, y, anchor="nw", image=tk_img)

    def select_and_next(self, path):
        if not self.output_dir:
            messagebox.showwarning("Warning", "Set Output Folder first.")
            return

        success, msg = FileManager.copy_to_output(path, self.output_dir)
        if success:
            self.next_group()
        else:
            messagebox.showerror("Error", msg)

    def start_pan(self, event):
        self.drag_start = (event.x, event.y)
    
    def do_pan(self, event):
        if not self.drag_start: return
        dx = event.x - self.drag_start[0]
        dy = event.y - self.drag_start[1]
        self.pan_x += dx
        self.pan_y += dy
        self.drag_start = (event.x, event.y)
        self.redraw_all()
        
    def do_zoom(self, event):
        if event.num == 5 or event.delta < 0:
            self.scale *= 0.9
        else:
            self.scale *= 1.1
        self.redraw_all()

    def next_group(self):
        if self.current_index < len(self.sorted_basenames) - 1:
            self.current_index += 1
            self.load_group()
        else:
            self.lbl_current_file.config(text="End of List")

    def prev_group(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_group()

def main():
    root = tk.Tk()
    app = SyncImageComparator(root)
    root.mainloop()

if __name__ == "__main__":
    main()