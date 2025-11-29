import os
import pytest
import random
import uuid
import shutil
from src.logic import FileScanner, AppState, FileManager

# --- CONFIGURATION ---
ITERATIONS = 50
MAX_FILES = 4096
MIN_FOLDERS = 2
MAX_FOLDERS = 12
EXTENSIONS = ['.jpg', '.PNG', '.arw', '.DNG', '.tiff', '.jpeg']

# --- HELPER FIXTURES ---

@pytest.fixture
def temp_env(tmp_path):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    (dir_a / "photo1.jpg").touch()
    (dir_a / "photo2.PNG").touch() 
    (dir_a / "unique_a.bmp").touch()
    
    (dir_b / "photo1.png").touch()
    (dir_b / "PHOTO2.jpg").touch()
    (dir_b / "unique_b.dng").touch()
    
    return [str(dir_a), str(dir_b)]

# --- PART 1: STANDARD FUNCTIONALITY ---

def test_scanner_basic_matching(temp_env):
    # Unpack 4 values now
    grouped, basenames, count, errors = FileScanner.scan(temp_env)
    assert "photo1" in grouped
    assert len(grouped["photo1"]) == 2
    assert "unique_a" not in grouped
    assert len(errors) == 0

def test_scanner_case_insensitivity(temp_env):
    grouped, basenames, count, errors = FileScanner.scan(temp_env)
    keys = [k.lower() for k in grouped.keys()]
    assert "photo2" in keys

def test_settings_persistence(tmp_path):
    config = tmp_path / "config.json"
    state = AppState()
    state.theme = "light"
    state.last_output_dir = "/tmp/fake"
    state.save_settings(str(config))
    state2 = AppState()
    state2.load_settings(str(config))
    assert state2.theme == "light"

def test_file_copying(tmp_path):
    source = tmp_path / "source.jpg"
    source.write_text("content")
    output = tmp_path / "output"
    output.mkdir()
    success, msg = FileManager.copy_to_output(str(source), str(output))
    assert success is True
    dest = output / "source.jpg"
    assert dest.exists()
    assert dest.read_text() == "content"

# --- PART 2: NEGATIVE TESTS & EDGE CASES ---

def test_ignore_invalid_extensions(tmp_path):
    dir_a = tmp_path / "A"
    dir_b = tmp_path / "B"
    dir_a.mkdir(); dir_b.mkdir()

    (dir_a / "image.jpg").touch()
    (dir_b / "image.txt").touch() 

    grouped, basenames, count, errors = FileScanner.scan([str(dir_a), str(dir_b)])
    assert "image" not in grouped

def test_scanner_error_reporting(tmp_path):
    """Test that scanner returns error strings for bad folders."""
    # Good folder
    dir_a = tmp_path / "A"
    dir_a.mkdir()
    
    # Non-existent folder
    bad_dir = tmp_path / "Ghost"
    
    folders = [str(dir_a), str(bad_dir)]
    grouped, basenames, count, errors = FileScanner.scan(folders)
    
    assert len(errors) > 0
    assert "not found" in errors[0] or "Error" in errors[0]

def test_copy_failure_missing_dir(tmp_path):
    source = tmp_path / "pic.jpg"
    source.touch()
    bad_output = tmp_path / "ghost_folder" 
    success, msg = FileManager.copy_to_output(str(source), str(bad_output))
    assert success is False

def test_copy_failure_none_path():
    success, msg = FileManager.copy_to_output("some/file.jpg", "")
    assert success is False

# --- PART 3: THE "MEGA CHAOS" STRESS TEST ---

def test_thorough_chaos(tmp_path):
    print(f"\n\n[Stress Test] Starting {ITERATIONS} iterations (Scan + Select/Copy)...")

    for i in range(1, ITERATIONS + 1):
        num_folders = random.randint(MIN_FOLDERS, MAX_FOLDERS)
        num_files = random.randint(2, MAX_FILES)
        
        run_dir = tmp_path / f"run_{i}"
        run_dir.mkdir()
        
        folder_paths = []
        for f_idx in range(num_folders):
            p = run_dir / f"folder_{f_idx}"
            p.mkdir()
            folder_paths.append(p)
            
        output_dir = run_dir / "selected_output"
        output_dir.mkdir()

        ground_truth = {} 
        
        for _ in range(num_files):
            basename = str(uuid.uuid4())
            count_in_folders = random.randint(1, num_folders)
            target_indices = random.sample(range(num_folders), k=count_in_folders)
            
            if len(target_indices) >= 2:
                ground_truth[basename] = len(target_indices)
            
            for idx in target_indices:
                folder = folder_paths[idx]
                ext = random.choice(EXTENSIONS)
                if random.choice([True, False]): ext = ext.upper()
                (folder / f"{basename}{ext}").touch()

        # SCAN (Unpack 4 values)
        str_paths = [str(p) for p in folder_paths]
        grouped, basenames, total_scanned, errors = FileScanner.scan(str_paths)

        # VERIFY SCAN
        assert len(errors) == 0, "Chaos test should not produce scanning errors"
        assert len(grouped) == len(ground_truth), \
            f"Iter {i}: Expected {len(ground_truth)} groups, found {len(grouped)}"
            
        # SELECT & COPY SIMULATION
        found_basenames = list(grouped.keys())
        if len(found_basenames) > 50:
            selection_sample = random.sample(found_basenames, 50)
        else:
            selection_sample = found_basenames
            
        for basename in selection_sample:
            paths_found = grouped[basename]
            user_choice = random.choice(paths_found)
            
            success, msg = FileManager.copy_to_output(user_choice, str(output_dir))
            
            assert success is True, f"Failed to copy {user_choice}"
            
            expected_filename = os.path.basename(user_choice)
            dest_file = output_dir / expected_filename
            assert dest_file.exists()
            
            success_2, msg_2 = FileManager.copy_to_output(user_choice, str(output_dir))
            assert success_2 is True

    print("\n[Stress Test] COMPLETED SUCCESSFULLY.")