import sys
import os

# 1. Add the current directory to Python's path
# This ensures Python can find the 'src' folder no matter how you launch this file.
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 2. Import the main function from your GUI code
try:
    from src.gui import main
except ImportError as e:
    print("Error: Could not import the application.")
    print(f"Details: {e}")
    print("\nMake sure your folder structure looks like this:")
    print("  /multicompare.py")
    print("  /src")
    print("    /__init__.py")
    print("    /gui.py")
    print("    /logic.py")
    input("\nPress Enter to exit...")
    sys.exit(1)

# 3. Run it
if __name__ == "__main__":
    main()