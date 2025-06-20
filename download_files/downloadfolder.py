import os
import hashlib

def calculate_hash(file_path):
    """Calculate the SHA-256 hash of the file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_files_hash(directory):
    """Get a dictionary of file hashes for all files in a directory."""
    file_hashes = {}
    for root, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_hash = calculate_hash(file_path)
            file_hashes[file_hash] = file_path
    return file_hashes

def find_files_not_in_archive(download_dir, archive_dir):
    """Identify files in the download directory that are not in the archive directory."""
    # Get hashes of files in both directories
    archive_hashes = get_files_hash(archive_dir)
    download_hashes = get_files_hash(download_dir)
    
    # Find files in download that aren't in the archive by checking hash values
    unique_files = {file_path for hash_val, file_path in download_hashes.items() if hash_val not in archive_hashes}
    
    return unique_files

# Define directories for download and archive
download_dir = r"C:\Users\Manoj\OneDrive\Desktop\ddas_project\download_files"
archive_dir = r"C:\Users\Manoj\OneDrive\Desktop\ddas_project\archive_files"

# Find files that are not in the archive
unique_files = find_files_not_in_archive(download_dir, archive_dir)

# Display results
if unique_files:
    print("Files in the download folder that are not in the archive:")
    for file_path in unique_files:
        print(f"- {file_path}")
else:
    print("All files in the download folder are already in the archive.")
