import os
import sys
import subprocess
import make_icon

def build():
    # 1. Determine Directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # Go up one level to root
    assets_dir = os.path.join(project_root, "assets")
    target_file = "multicompare.py"

    print(f"--- Starting Build ---")
    print(f"Project Root: {project_root}")
    print(f"Output Dir:   {script_dir}")

    # 2. Check & Generate Icons
    # If assets folder is missing or empty, generate them now.
    if not os.path.exists(assets_dir) or not os.listdir(assets_dir):
        print("\n[Build] Assets missing. Running make_icon.py...")
        try:
            # Calls the main function in make_icon.py
            make_icon.create_pro_icon()
        except Exception as e:
            print(f"[Build] Warning: Icon generation failed ({e}). Build might look generic.")
    else:
        print("\n[Build] Assets found. Skipping icon generation.")

    # 3. Build the Nuitka Command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--enable-plugin=tk-inter",
        "--include-package=src",
        "--include-package-data=rawpy", 
        "--include-package-data=numpy",
        "--include-module=numpy.core.umath",
        "--include-module=numpy.core.multiarray",
        #"--extra-options=-Wl,--stack,16777216", 
        "--jobs=4",
        "--include-data-dir=assets=assets", 
        f"--output-dir={script_dir}",
    ]

    # 4. OS Specific Settings (Define icons here)
    if sys.platform == "win32":
        icon_path = os.path.join(assets_dir, "icon.ico")
        cmd.extend([
            "--onefile",
            "--windows-console-mode=disable",
            "--output-filename=MultiCompare.exe",
            f"--windows-icon-from-ico={icon_path}",
            "--assume-yes-for-downloads",
            "--include-package=numpy", 
            "--include-package=rawpy",
            #"--msvc=latest"
            "--mingw64",
            "--clang",
            "--module-parameter=numba-disable-jit=no"
            #"--noinclude-numba-mode=nofollow"
        ])
    elif sys.platform == "darwin":
        icon_path = os.path.join(assets_dir, "icon.icns")
        cmd.extend([
            "--macos-create-app-bundle",
            "--macos-app-name=MultiCompare",
            f"--macos-app-icon={icon_path}"
        ])
    else: # Linux
        icon_path = os.path.join(assets_dir, "icon.png")
        cmd.extend([
            "--onefile",
            "--output-filename=multicompare",
            f"--linux-icon={icon_path}"
        ])

    # 5. Append Target
    cmd.append(target_file)

    # 6. Execute
    try:
        # We run the command with cwd=project_root so Nuitka finds 'src'
        subprocess.check_call(cmd, cwd=project_root)
        print(f"\n[SUCCESS] Build complete. Artifacts are in: {script_dir}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    build()
