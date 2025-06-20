import os
import hashlib
import re
import time
import subprocess

# Directory to monitor for downloads
DOWNLOAD_DIR = r"C:\Users\Manoj\Downloads"

# File to store hashes of downloaded files (in the same directory as the script)
HASH_STORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "file_hashes.txt")

# Function to calculate file hash
def calculate_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# Load existing file hashes
def load_existing_hashes():
    if not os.path.exists(HASH_STORE_FILE):
        return {}
    
    file_hashes = {}
    with open(HASH_STORE_FILE, "r") as file:
        for line in file.readlines():
            # Skip empty lines
            if not line.strip():
                continue
            
            # Split the line by the first comma only
            parts = line.strip().split(",", 1)
            
            # Ensure the line has exactly two parts (hash and filename)
            if len(parts) == 2:
                file_hash, file_name = parts
                file_hashes[file_hash] = file_name
            else:
                print(f"Skipping malformed line: {line.strip()}")
    
    return file_hashes

# Save new file hashes
def save_hashes(hash_dict):
    with open(HASH_STORE_FILE, "w") as file:
        for file_hash, file_name in hash_dict.items():
            file.write(f"{file_hash},{file_name}\n")

# Check if a file is fully downloaded (size remains constant)
def is_file_stable(file_path, check_interval=2):
    initial_size = os.path.getsize(file_path)
    time.sleep(check_interval)
    return initial_size == os.path.getsize(file_path)

# Detect similar filenames (e.g., tamil-1.txt, tamil-2.txt)
def find_similar_filenames(file_name, existing_files):
    # Extract the base name (without suffix like -1, -2, etc.)
    base_name = re.sub(r"-\d+", "", file_name)  # Remove -1, -2, etc.
    base_name = os.path.splitext(base_name)[0]  # Remove file extension
    
    # Find files with similar base names
    similar_files = [f for f in existing_files if re.sub(r"-\d+", "", f).startswith(base_name)]
    return similar_files

# Handle duplicate files (open or delete)
def handle_duplicate(file_path):
    print(f"\nDuplicate file detected: {os.path.basename(file_path)}")
    action = input("Do you want to [O]pen or [D]elete the file? (O/D): ").strip().upper()
    
    if action == "O":
        # Open the file
        try:
            if os.name == "nt":  # Windows
                os.startfile(file_path)
            else:  # macOS or Linux
                subprocess.run(["open", file_path])
            print(f"Opened: {file_path}")
        except Exception as e:
            print(f"Failed to open file: {e}")
    elif action == "D":
        # Delete the file
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Failed to delete file: {e}")
    else:
        print("Invalid option. No action taken.")

# Monitor downloads directory for new files
def monitor_directory():
    file_hashes = load_existing_hashes()
    print("Monitoring for new downloads...")
    
    # Track files already processed in the current session
    processed_files = set()

    while True:
        with os.scandir(DOWNLOAD_DIR) as entries:
            # Collect all files in the directory
            current_files = [entry.name for entry in entries if entry.is_file()]
            
            # Check for new or duplicate files
            for file_name in current_files:
                if file_name not in processed_files:
                    file_path = os.path.join(DOWNLOAD_DIR, file_name)
                    
                    # Wait for the file to be fully downloaded
                    if is_file_stable(file_path):
                        file_hash = calculate_hash(file_path)
                        
                        # Check for content-based duplicates
                        if file_hash in file_hashes:
                            print(f"\n--- Duplicate File Detected (Content-Based) ---")
                            print(f"{file_name} is a duplicate of {file_hashes[file_hash]}")
                            handle_duplicate(file_path)
                        else:
                            # Check for name-based duplicates
                            similar_files = find_similar_filenames(file_name, file_hashes.values())
                            if similar_files:
                                print(f"\n--- Duplicate File Detected (Name-Based) ---")
                                print(f"{file_name} is similar to {', '.join(similar_files)}")
                                handle_duplicate(file_path)
                            else:
                                print(f"\n--- New File Downloaded ---")
                                print(f"{file_name} is a new download.")
                                file_hashes[file_hash] = file_name
                                save_hashes(file_hashes)
                        
                        # Mark the file as processed
                        processed_files.add(file_name)
        
        time.sleep(5)  # Adjust monitoring interval as needed

# Run the monitoring function
if __name__ == "__main__":
    monitor_directory()