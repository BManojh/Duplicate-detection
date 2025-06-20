import os
import hashlib
import json
import datetime

download_directory = r"C:\Users\Manoj\OneDrive\Desktop\ddas_project\download_files"

def get_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def check_for_duplicates(file_name):
    metadata_file = "file_metadata.json"
    
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}
    
    file_path = os.path.join(download_directory, file_name)
    
    if not os.path.exists(file_path):
        print(f"File '{file_name}' does not exist in the directory.")
        return
    
    file_hash = get_file_hash(file_path)
    
    if file_hash in metadata:
        existing_info = metadata[file_hash]
        if existing_info['location'] == file_path:
            print(f"Duplicate file found!\nFile Name: {file_name}\nIt is already in the Location: {existing_info['location']}\nDownloaded at: {existing_info['timestamp']}")
        else:
            print(f"File with the same content already exists in this location:\n{existing_info['location']}")
    else:
        current_time = str(datetime.datetime.now())
        metadata[file_hash] = {
            'location': file_path,  
            'timestamp': current_time  
        }
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)  
        print(f"File '{file_name}' added to metadata at {current_time}.")


check_for_duplicates("kali.txt")  
    