import os
import hashlib
import json
import re

download_directory = r"C:\Users\Manoj\OneDrive\Desktop\ddas_project\download_files"

def get_file_hash(file_path):
    """Generate a SHA-256 hash for the given file."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(8192)
            while chunk:
                hasher.update(chunk)
                chunk = f.read(8192)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None
    return hasher.hexdigest()

def is_similar_name(file_name1, file_name2):
    """Check if two file names are similar based on a naming convention."""
    base1 = re.sub(r'[\d]', '', file_name1.split('.')[0])  # Remove numbers
    base2 = re.sub(r'[\d]', '', file_name2.split('.')[0])  # Remove numbers
    return base1 == base2  # Return true if bases are the same after removing numbers

def check_for_similar_files():
    """Check for files with similar content and names in the specified directory."""
    metadata_file = "file_metadata.json"
    
    # Load or initialize metadata dictionary
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}

    # Dictionary to track files by hash and names
    files_by_hash = {}
    similar_files = {}

    # Iterate through each file in the download directory
    for file_name in os.listdir(download_directory):
        file_path = os.path.join(download_directory, file_name)
        
        if os.path.isfile(file_path):
            file_hash = get_file_hash(file_path)

            # If file hash couldn't be generated, skip this file
            if not file_hash:
                continue

            # Group files by their hash
            if file_hash not in files_by_hash:
                files_by_hash[file_hash] = []
            files_by_hash[file_hash].append(file_path)

            # Check for similar names with existing files
            for existing_file_name in similar_files.keys():
                if is_similar_name(existing_file_name, file_name):
                    similar_files[existing_file_name].append(file_path)
                    break
            else:
                similar_files[file_name] = [file_path]

    print("=" * 60)
    print("Data Download Duplication Alert System (DDAS) - Similar Files")
    print("=" * 60)

    # Present similar files found based on naming conventions
    for file_name, paths in similar_files.items():
        if len(paths) > 1:  # More than one file found
            print(f"\nDuplicate files based on name '{file_name}':")
            for path in paths:
                print(f" - {path}")

    # Check for files with identical content
    print("\n" + "=" * 60)
    print("Identifying Duplicate Content:")
    for file_hash, paths in files_by_hash.items():
        if len(paths) > 1:  # More than one file with the same hash
            print(f"\nIdentical files with content hash '{file_hash}':")
            for path in paths:
                print(f" - {path}")
            # Provide option to delete one of the duplicate files
            delete_choice = input("Do you want to delete one of these files? (yes/no): ").strip().lower()
            if delete_choice == 'yes':
                file_to_delete = input("Enter the full path of the file you want to delete: ")
                if os.path.exists(file_to_delete):
                    os.remove(file_to_delete)
                    print(f"Deleted file: {file_to_delete}")
                else:
                    print("File not found. Skipping deletion.")

    print("\n" + "=" * 60)
    print("DDAS Scan Completed")
    print("=" * 60)

# Run the duplicate check for all files in the download directory
check_for_similar_files()
