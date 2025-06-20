import os
import hashlib
from difflib import SequenceMatcher

def calculate_hash(file_path):
    """Calculate the SHA-256 hash of the file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def name_similarity(name1, name2):
    """Calculate similarity ratio between two filenames (without extension)."""
    name1_base = os.path.splitext(name1)[0]
    name2_base = os.path.splitext(name2)[0]
    return SequenceMatcher(None, name1_base, name2_base).ratio()

def find_duplicates(directory, check_name_similarity=False, name_similarity_threshold=0.8):
    """
    Find duplicate files by content hash, optionally checking name similarity.
    
    Args:
        directory: Directory to search.
        check_name_similarity: If True, also checks for similar filenames within content duplicates.
        name_similarity_threshold: Minimum similarity ratio (0-1) if checking names.
    
    Returns:
        List of duplicate file groups.
    """
    file_hashes = {}
    empty_file_hash = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    
    # First pass: group files by content hash
    for root, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            try:
                file_hash = calculate_hash(file_path)
            except (IOError, OSError):
                continue  # Skip unreadable files
            
            # Ignore empty files
            if file_hash == empty_file_hash:
                continue
            
            if file_hash not in file_hashes:
                file_hashes[file_hash] = []
            file_hashes[file_hash].append(file_path)
    
    # Second pass: filter groups with duplicates
    duplicate_groups = [paths for paths in file_hashes.values() if len(paths) > 1]
    
    # If not checking name similarity, return all content duplicates
    if not check_name_similarity:
        return duplicate_groups
    
    # If checking name similarity, further filter groups
    filtered_groups = []
    
    for group in duplicate_groups:
        processed = set()
        similar_name_groups = []
        
        for i, path1 in enumerate(group):
            if path1 in processed:
                continue
                
            name1 = os.path.basename(path1)
            current_group = [path1]
            
            for j, path2 in enumerate(group[i+1:], i+1):
                if path2 in processed:
                    continue
                    
                name2 = os.path.basename(path2)
                similarity = name_similarity(name1, name2)
                
                if similarity >= name_similarity_threshold:
                    current_group.append(path2)
                    processed.add(path2)
            
            if len(current_group) > 1:
                similar_name_groups.append(current_group)
            
            processed.add(path1)
        
        filtered_groups.extend(similar_name_groups)
    
    return filtered_groups

def handle_duplicates(duplicate_groups):
    """Let the user choose which duplicates to delete."""
    if not duplicate_groups:
        print("No duplicates found.")
        return
    
    print(f"\nFound {len(duplicate_groups)} duplicate groups:")
    
    for group_num, group in enumerate(duplicate_groups, 1):
        print(f"\nGroup {group_num} (identical content):")
        for i, file_path in enumerate(group, 1):
            print(f"  {i}. {file_path}")
        
        while True:
            choice = input("\nChoose action:\n"
                          "[k]eep all\n"
                          "[d]elete all\n"
                          "[s]elect which to keep\n"
                          "[n]ext group\n"
                          "[q]uit\n"
                          "Your choice: ").lower()
            
            if choice == 'k':
                print("Keeping all files in this group.")
                break
            elif choice == 'd':
                for file_path in group:
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
                break
            elif choice == 's':
                try:
                    keep_indices = [int(i)-1 for i in input("Enter file numbers to keep (e.g., '1 3'): ").split()]
                    for i, file_path in enumerate(group):
                        if i not in keep_indices:
                            try:
                                os.remove(file_path)
                                print(f"Deleted: {file_path}")
                            except Exception as e:
                                print(f"Error deleting {file_path}: {e}")
                    break
                except ValueError:
                    print("Invalid input. Please try again.")
            elif choice == 'n':
                break
            elif choice == 'q':
                return
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    # Directory to scan
    directory = r"C:\Users\Manoj\OneDrive\Desktop\ddas_project\download_files"
    
    # Ask user if they want to check name similarity
    check_names = input("Check for similar filenames too? (y/n): ").lower() == 'y'
    name_threshold = 0.7  # Adjust as needed
    
    # Find duplicates
    duplicates = find_duplicates(directory, check_name_similarity=check_names, name_similarity_threshold=name_threshold)
    
    # Handle duplicates
    handle_duplicates(duplicates)