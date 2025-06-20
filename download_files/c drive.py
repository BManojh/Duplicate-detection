import os
import hashlib

def calculate_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    except (PermissionError, FileNotFoundError):
        return None  # Skip files that cannot be accessed
    return sha256_hash.hexdigest()

def find_duplicates(drive_path):
    """Find and group duplicate files by hash across the specified drive."""
    file_hashes = {}
    
    # Traverse the specified drive and calculate hashes
    for root, _, files in os.walk(drive_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            # Verify path accessibility and calculate hash
            if os.path.exists(file_path):
                file_hash = calculate_hash(file_path)
                
                # Skip files that couldn't be read or hashed
                if file_hash is None:
                    continue
                
                # Group files by hash
                if file_hash not in file_hashes:
                    file_hashes[file_hash] = []
                file_hashes[file_hash].append(file_path)
            else:
                print(f"Could not access file path: {file_path}")
    
    # Filter out unique files and keep only duplicates
    duplicates = {hash_val: paths for hash_val, paths in file_hashes.items() if len(paths) > 1}
    return duplicates

def prompt_delete_duplicates(duplicates):
    """Prompt the user to delete duplicate files."""
    for file_hash, files in duplicates.items():
        print(f"\nIdentical files with content hash '{file_hash}':")
        for i, file_path in enumerate(files):
            print(f"  {i + 1}. {file_path}")
        
        while True:
            # Ask user which file to keep
            keep_index = input(f"\nWhich file would you like to keep (1-{len(files)})? Enter '0' to skip: ")
            if keep_index.isdigit() and 0 <= int(keep_index) <= len(files):
                keep_index = int(keep_index) - 1
                break
            else:
                print("Invalid input. Please enter a valid number.")

        # Delete all duplicates except the one to keep
        if keep_index != -1:
            for i, file_path in enumerate(files):
                if i != keep_index:
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                    except PermissionError:
                        print(f"Permission denied: Could not delete {file_path}")
                    except FileNotFoundError:
                        print(f"File not found: {file_path}")

# Define the drive to search for duplicate files
drive_path = r"C:\Users\Manoj\OneDrive\Documents"

# Find duplicates
duplicates = find_duplicates(drive_path)

# Delete duplicates
if duplicates:
    prompt_delete_duplicates(duplicates)
else:
    print("No duplicate files found.")
