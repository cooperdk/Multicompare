# MultiCompare

**MultiCompare** is a completely portable specialized *synchronized image viewer and handler* designed for photographers, AI image creators and editors. It allows you to visually compare images across multiple folders simultaneously.

Unlike standard viewers, MultiCompare features a **Smart Filtering Engine** that automatically groups files **by filename**. It ignores unmatched files and only presents sets of images that exist with the same base filename in at least two of the selected folders, making it perfect for comparing batch generated AI images, different edits, or raw-vs-jpg workflows.

I wrote the script because I have an iterating ComfyUI workflow which outputs a set of images with the same names for SillyTavern expressions (28 files) and needed a way to select the best image after a number of executions. I found no software that supports this feature, so I decided to create this app. It will display all images on the same screen and panning or zooming one image causes the app to automatically pan and zoom the rest automatically.

### The ComfyUI workflow

I am polishing the first workflow to support this tool and it will be included as soon as possible. In the meantime, use any that you wish (there are a few out there).
This workflow will use QWEN Image Edit to adjust a base image according to expressions (including gesticulation, using LLM to generate 5-15 words for the expression, depending on the LLM used), and remove the background. I use dolphin3.0-llama3.1-8b to feed the prompt with more vivid expressions.

## Key Features

*   **Synchronized Navigation:** Zooming or panning one image updates all images instantly.
*   **Lightroom-Style UI:** Switchable **Dark/Light** modes with persistent settings.
*   **Smart Auto-Filter:** Automatically scans selected folders and only displays filenames that appear in **at least two** locations.
*   **Broad Format Support:** Native support for standard images (`JPG`, `PNG`, `TIFF`) and Camera RAW formats (`ARW`, `CR2`, `NEF`, `DNG`, etc.) via `rawpy`.
*   **Adaptive Grid:** Automatically arranges up to 10 images per screen based on the number of matches found.
*   **Culling workflow:** Lets the user select the best image from a set to automatically copy it to the output folder and move to the next set of matched images.
*   **Persistency:** The app remembers window size and position/fullscreen status, the last used output directory, and theme preferences.
*   **Cross-Platform:** Works natively on Windows, macOS, and Linux.

---

## Supported platforms

### Windows, Linux and Mac OS X

The app should be able to run on Mac OS X. It has been tested to run on Linux (Ubuntu) and Windows 11.
It will run faster in the release version as it is converted to C code and compiled (apart from some Python modules which are embedded as bytecode).

## Installation (Running from Source)

### Prerequisites

*   **Python 3.8+** installed.
*   (Linux only) Ensure `gcc` is installed for compiling dependencies.

### Setup

1.  Clone or download this repository.
2.  Install the required dependencies:

```bash
pip install -r requirements.txt
```
or simply install it using pip in the root project folder, using:

```bash
pip install .
```
This should enable you to run the program by simply executing "multicompare" in your terminal. (Alternatively, check the section "Building the executable".)

3.  Run the application:

```bash
python multicompare.py
```

---

## User guide

### 1. Selecting folders
*   Click **"Add Folder"** to select directories containing your images.
*   You can add as many folders as you like (e.g., *Source A*, *Source B*, *Source C*).
*   **Note:** The application will not show images immediately. It waits for you to scan.

### 2. Scanning & filtering
*   Click **"Scan/Refresh"**.
*   The application looks at the **base filename** (ignoring extensions).
    *   *Example:* `photo_01.jpg` in Folder A matches `photo_01.ARW` in Folder B.
*   **Logic:** If a filename exists in only **one** folder, it is ignored. It must appear in at least **two** folders to be displayed.

### 3. Comparison controls
Once matches are found, the first set is displayed.

*   **Next/Previous:** Use the on-screen buttons or **Left/Right Arrow Keys** to jump between matched sets.
*   **Zoom:** Scroll the **Mouse Wheel** over any image to zoom in/out on all images simultaneously.
*   **Pan:** Click and drag any image to move all images simultaneously.

### 4. Selection and culling

* Set Output: Click "Set Output" to choose where selected images will be saved.
* Choose your image for copying: Click the blue SELECT button under an image, or simply Double-Click the image itself.
* Auto-Advance: The file is copied immediately, and the app automatically jumps to the next set of images.
### 5. Interface theme
*   Click the **🌗 Theme** button to toggle between Dark Mode (default) and Light Mode.
*   Your preference is saved automatically to `img_compare_settings.json` and remembered for next time.

---

## Building the executable

If you can't wait until a release a built, you should be able to built it yourself.
This project makes use of a custom build system using **Nuitka**. This converts the Python code to C and compiles it into a standalone executable (`.exe` on Windows, binary on Linux, `.app` bundle on macOS) with embedded libraries.

### 1. The build script
I have provided a helper script in the `scripts/` folder that handles icon generation and compilation flags automatically.

Run this command from the project root:

```bash
python scripts/build.py
```

### 2. What happens?
1.  **Icon Generation:** The script first calls `scripts/make_icon.py` to generate high-resolution, platform-specific icons (`.ico`, `.png`) in the `assets/` folder.
2.  **Compilation:** It runs Nuitka with optimized flags (hiding the console on Windows, bundling Numpy/Tkinter).
3.  **Output:** The final executable is placed in the **`scripts/`** folder (or `scripts/dist_mac` on macOS).

### 3. Building the Linux executable using Dockerfile

On Windows, you need to have Docker Desktop installed on running.
On Linux, open your terminal in the project root and build the dockerfile using:
```bash
docker build -t multicompile-linux .
```
Then, run the container, mapping your local project root to the container's /app/ folder. The container will then deliver the GUI-based app in your project folder (possibly in scripts/).  Use the command:
```bash
docker run --rm -v ${PWD}:/app multicompile-linux
```

---

## Development & testing

The project follows a **MVC** separation to ensure the logic works independently of the GUI.

*   **`src/logic.py`**: Handles file scanning, filtering algorithms, and settings management.
*   **`src/gui.py`**: Handles the Tkinter interface and user interaction.

### Running Unit Tests
I have provided a `pytest` compatible script to verify the filtering logic (e.g., ensuring case-insensitivity and correct grouping).

To verify scanning accuracy and copying reliability, the test includes a chaos test which simulates 50 iterations of a random amount of folders with a random amount of files with the same name (up to 512).

1.  Open your terminal in the root folder.
2.  Run tests (using verbosity):

```bash
pytest -v -s
```

---

## Project structure

```text
/Multicompare
│
├── assets/                 # Generated icons (created automatically)
│   ├── icon.ico
│   └── icon.png
│
├── scripts/                # Build and Utility scripts
│   ├── build.py            # Main compilation script
│   └── make_icon.py        # Generates procedural icons
│
├── src/                    # Source Code
│   ├── __init__.py
│   ├── gui.py              # UI & Visualization
│   ├── icon_factory.py # Icon generator
│   └── logic.py            # Scanning & Filtering Algorithms
│
├── tests/                  # Unit Tests
│   ├── __init__.py
│   └── test_logic.py
│
├── Dockerfile              # The Docker environment for easy compilation (Linux only)
├── multicompare.py         # Entry point (Run this file)
├── pyproject.toml          # Project metadata
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## Supported image formats

**Standard:** `.JPG`, `.JPEG`, `.PNG`, `.BMP`, `.TIFF`, `.TIF`, `.GIF`, `.WEBP`

**Raw (via RawPy):** `.ARW`, `.CR2`, `.CR3`, `.NEF`, `.DNG`, `.ORF`, `.RAF`, `.RW2`, `.PEF`, `.SRW`

---

## License

[GNU 3-0 License](https://opensource.org/license/gpl-3-0) - Feel free to fork, request pulls, modify and distribute.
