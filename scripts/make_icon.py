import os
import sys

# --- PATH FIX ---
# 1. Get the directory of this script (.../scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Calculate the path to the 'src' folder (.../src)
src_dir = os.path.join(os.path.dirname(script_dir), "src")

# 3. Add 'src' directory directly to sys.path
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 4. Import directly
try:
    from icon_factory import generate_icon_image
except ImportError as e:
    print(f"CRITICAL ERROR: Could not find icon_factory.py in {src_dir}")
    print(f"Python Error: {e}")
    sys.exit(1)
# ----------------

from PIL import Image

def create_pro_icon():
    # Calculate assets dir relative to project root
    project_root = os.path.dirname(script_dir)
    assets_dir = os.path.join(project_root, "assets")
    
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        print(f"[Icon] Created directory: {assets_dir}")

    print(f"[Icon] Generating high-res icons...")

    try:
        # 1. Generate the master image (1024x1024)
        # This uses the factory we built earlier
        master_icon = generate_icon_image(size=1024)
        
        # 2. Save PNG (Keep it high res for Linux/Mac)
        png_path = os.path.join(assets_dir, "icon.png")
        master_icon.save(png_path)
        print(f"[Icon] Saved {png_path}")
        
        # 3. Generate High-Quality ICO Layers
        # We manually resize using LANCZOS to prevent blockiness
        icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        high_quality_layers = []

        for size in icon_sizes:
            # Resize the master image down to specific size
            resized_img = master_icon.resize(size, Image.Resampling.LANCZOS)
            high_quality_layers.append(resized_img)

        # 4. Save ICO
        # We save the first (largest) image and append the rest
        ico_path = os.path.join(assets_dir, "icon.ico")
        high_quality_layers[0].save(
            ico_path, 
            format="ICO", 
            append_images=high_quality_layers[1:]
        )
        print(f"[Icon] Saved {ico_path} (High Quality Lanczos)")

    except Exception as e:
        print(f"[Icon] Error: {e}")

if __name__ == "__main__":
    create_pro_icon()