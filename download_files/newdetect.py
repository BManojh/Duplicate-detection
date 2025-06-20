import os
import hashlib
import time
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DOWNLOAD_DIR = r"C:\Users\Manoj\Downloads"
HASH_STORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "file_hashes.txt")

def calculate_hash(file_path):
    """Calculate MD5 hash of a file"""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None

def load_existing_hashes():
    """Load existing file hashes from storage"""
    if not os.path.exists(HASH_STORE_FILE):
        return {}
    
    file_hashes = {}
    try:
        with open(HASH_STORE_FILE, "r", encoding='utf-8') as file:
            for line in file.readlines():
                if line.strip():
                    parts = line.strip().split(",", 1)
                    if len(parts) == 2:
                        file_hash, file_name = parts
                        file_hashes[file_hash] = file_name
    except Exception as e:
        print(f"Error loading hashes: {e}")
    return file_hashes

def save_hashes(hash_dict):
    """Save file hashes to storage"""
    try:
        with open(HASH_STORE_FILE, "w", encoding='utf-8') as file:
            for file_hash, file_name in hash_dict.items():
                file.write(f"{file_hash},{file_name}\n")
    except Exception as e:
        print(f"Error saving hashes: {e}")

def is_similar_filename(file1, file2):
    """Check if two filenames are similar - improved logic for better detection"""
    # Get extensions
    name1, ext1 = os.path.splitext(file1)
    name2, ext2 = os.path.splitext(file2)
    
    # Must have same extension to be considered similar
    if ext1.lower() != ext2.lower():
        return False
    
    # Convert to lowercase for comparison
    base1 = name1.lower().strip()
    base2 = name2.lower().strip()
    
    # If base names are exactly the same, they're similar
    if base1 == base2:
        return True
    
    # Remove common duplicate patterns
    duplicate_patterns = [
        r'\s*\(\d+\)$',           # (1), (2), etc.
        r'\s*-\s*copy$',          # -copy, - copy
        r'\s*_copy$',             # _copy
        r'\s*-\s*v\d+$',          # -v1, -v2, - v1
        r'\s*_v\d+$',             # _v1, _v2
        r'\s*-\s*\d+$',           # -1, -2, - 1
        r'\s*_\d+$',              # _1, _2
        r'\s*-\s*duplicate$',     # -duplicate
        r'\s*_duplicate$',        # _duplicate
        r'\s*\s+copy$',           # space copy
    ]
    
    clean1 = base1
    clean2 = base2
    
    # Remove duplicate patterns from both filenames
    for pattern in duplicate_patterns:
        clean1 = re.sub(pattern, '', clean1).strip()
        clean2 = re.sub(pattern, '', clean2).strip()
    
    # If cleaned names are the same, they're similar
    if clean1 == clean2 and len(clean1) > 0:
        return True
    
    # Check for numbered sequences like "text1" vs "text2", "document_v1" vs "document_v2"
    def extract_base_and_number(text):
        """Extract base text and trailing number"""
        # Match patterns like: text1, text_1, text-1, text 1, textv1, text_v1, text-v1
        patterns = [
            r'^(.+?)v?[-_\s]*(\d+)$',      # Matches: text1, text_1, text-1, text 1, textv1, text_v1, text-v1
            r'^(.+?)[-_\s]*v[-_\s]*(\d+)$', # Matches: text-v1, text_v1, text v1
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text.strip())
            if match:
                base_part = match.group(1).strip().rstrip('_-')
                number_part = match.group(2)
                return base_part, number_part
        
        return text, None
    
    # Extract base and numbers
    base1_clean, num1 = extract_base_and_number(clean1)
    base2_clean, num2 = extract_base_and_number(clean2)
    
    # If both have numbers and same base, they're similar
    if num1 and num2 and base1_clean == base2_clean:
        # Must have meaningful base (at least 2 characters)
        if len(base1_clean) >= 2:
            return True
    
    # Check for very similar bases with small differences
    # Only for longer filenames to avoid false positives
    if len(clean1) >= 5 and len(clean2) >= 5:
        # Calculate similarity for very close matches
        if abs(len(clean1) - len(clean2)) <= 2:  # Length difference <= 2
            # Check how many characters are the same from the beginning
            shorter_len = min(len(clean1), len(clean2))
            matches = sum(1 for i in range(shorter_len) if i < len(clean1) and i < len(clean2) and clean1[i] == clean2[i])
            
            # If 90% of characters match from the beginning, consider similar
            if matches / shorter_len >= 0.9 and shorter_len >= 5:
                return True
    
    # Special case: Check if one is a subset of another with minimal differences
    if len(clean1) >= 4 and len(clean2) >= 4:
        # Remove common separators and spaces for comparison
        normalized1 = re.sub(r'[-_\s]+', '', clean1)
        normalized2 = re.sub(r'[-_\s]+', '', clean2)
        
        # If one is contained in another and they're similar length
        if (normalized1 in normalized2 or normalized2 in normalized1):
            shorter = min(len(normalized1), len(normalized2))
            longer = max(len(normalized1), len(normalized2))
            # Only if the difference is small relative to the shorter string
            if (longer - shorter) <= max(2, shorter * 0.2):  # Max 20% difference or 2 chars
                return True
    
    return False

def show_alert(message, is_error=False, is_modified=False):
    """Show alert in VS Code output"""
    timestamp = time.strftime("%H:%M:%S")
    if is_modified:
        print(f"\n[{timestamp}] [FILE MODIFIED] {message}")
    elif is_error:
        print(f"\n[{timestamp}] [DUPLICATE DETECTED] {message}")
    else:
        print(f"\n[{timestamp}] [NEW FILE DETECTED] {message}")

def populate_initial_hashes():
    """Populate hash store with existing files in download directory"""
    if not os.path.exists(DOWNLOAD_DIR):
        print(f"Download directory {DOWNLOAD_DIR} does not exist!")
        return {}
    
    file_hashes = {}
    print("Scanning existing files in download directory...")
    
    try:
        for filename in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(file_path):
                file_hash = calculate_hash(file_path)
                if file_hash:
                    file_hashes[file_hash] = filename
                    print(f"Added to database: {filename}")
    except Exception as e:
        print(f"Error scanning directory: {e}")
    
    save_hashes(file_hashes)
    print(f"Initial scan complete. Found {len(file_hashes)} files.")
    return file_hashes

def remove_old_hash_entry(hash_dict, filename):
    """Remove old hash entry for a file that has been modified"""
    hash_to_remove = None
    for file_hash, stored_filename in hash_dict.items():
        if stored_filename == filename:
            hash_to_remove = file_hash
            break
    
    if hash_to_remove:
        del hash_dict[hash_to_remove]
        return True
    return False

class DownloadHandler(FileSystemEventHandler):
    def __init__(self):
        # Load existing hashes or create initial database
        self.file_hashes = load_existing_hashes()
        if not self.file_hashes:
            self.file_hashes = populate_initial_hashes()
        
        self.processing_files = set()  # Track files being processed
        self.file_modification_times = {}  # Track file modification times
        super().__init__()

    def on_created(self, event):
        """Handle new file creation events"""
        if not event.is_directory:
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            
            print(f"File created: {file_name}")
            
            # Skip temporary download files and system files
            if (file_name.startswith('~') or 
                file_name.startswith('.') or
                file_name.endswith('.tmp') or 
                file_name.endswith('.crdownload') or
                file_name.endswith('.part') or
                file_name.endswith('.download')):
                print(f"Skipping temporary file: {file_name}")
                return
            
            # Avoid processing the same file multiple times
            if file_path in self.processing_files:
                return
            
            self.processing_files.add(file_path)
            
            # Wait for file to be fully written
            time.sleep(2)
            self.monitor_and_process_file(file_path, is_new_file=True)

    def on_moved(self, event):
        """Handle file move events (like browser completing download)"""
        if not event.is_directory:
            dest_path = event.dest_path
            file_name = os.path.basename(dest_path)
            
            print(f"File moved to: {file_name}")
            
            # Skip if it's a temporary file being moved
            if (file_name.startswith('~') or 
                file_name.startswith('.') or
                file_name.endswith('.tmp')):
                return
            
            # Avoid processing the same file multiple times
            if dest_path in self.processing_files:
                return
                
            self.processing_files.add(dest_path)
            
            # Wait for file to be fully written
            time.sleep(2)
            self.monitor_and_process_file(dest_path, is_new_file=True)

    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            
            # Skip temporary files and system files
            if (file_name.startswith('~') or 
                file_name.startswith('.') or
                file_name.endswith('.tmp') or 
                file_name.endswith('.crdownload') or
                file_name.endswith('.part') or
                file_name.endswith('.download')):
                return
            
            # Check if this is a text file that might have been edited
            if not (file_name.endswith('.txt') or 
                    file_name.endswith('.doc') or 
                    file_name.endswith('.docx') or
                    file_name.endswith('.pdf') or
                    file_name.endswith('.rtf')):
                return
            
            print(f"File modified: {file_name}")
            
            # Avoid processing the same file multiple times rapidly
            if file_path in self.processing_files:
                return
            
            # Check if file was recently modified (debounce)
            current_time = time.time()
            if file_path in self.file_modification_times:
                last_mod_time = self.file_modification_times[file_path]
                if current_time - last_mod_time < 5:  # Wait 5 seconds between processing
                    return
            
            self.file_modification_times[file_path] = current_time
            self.processing_files.add(file_path)
            
            # Wait a bit for file operations to complete
            time.sleep(3)
            self.monitor_and_process_file(file_path, is_new_file=False)

    def monitor_and_process_file(self, file_path, is_new_file=True):
        """Monitor a file until it's stable, then process it"""
        file_name = os.path.basename(file_path)
        
        try:
            # Wait for file to be stable (not changing size)
            if not self.wait_for_stable_file(file_path):
                return
            
            print(f"Processing file: {file_name} ({'new' if is_new_file else 'modified'})")
            
            # Calculate hash
            file_hash = calculate_hash(file_path)
            if file_hash is None:
                print(f"Could not calculate hash for: {file_name}")
                return
            
            # Check for duplicates
            if is_new_file:
                self.check_for_duplicates(file_name, file_hash)
            else:
                self.handle_modified_file(file_name, file_hash)
            
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
        finally:
            # Remove from processing set
            self.processing_files.discard(file_path)

    def wait_for_stable_file(self, file_path, max_wait=30):
        """Wait for file to be stable (not changing size)"""
        stable_count = 0
        required_stable_checks = 3
        wait_count = 0
        
        while stable_count < required_stable_checks and wait_count < max_wait:
            try:
                if not os.path.exists(file_path):
                    return False
                
                current_size = os.path.getsize(file_path)
                time.sleep(1)
                wait_count += 1
                
                if not os.path.exists(file_path):
                    return False
                    
                new_size = os.path.getsize(file_path)
                
                if current_size == new_size and current_size > 0:
                    stable_count += 1
                else:
                    stable_count = 0
                    
            except Exception as e:
                print(f"Error waiting for stable file: {e}")
                time.sleep(1)
                wait_count += 1
        
        return stable_count >= required_stable_checks

    def check_for_duplicates(self, file_name, file_hash):
        """Check for content and filename duplicates for new files"""
        content_duplicate = False
        filename_duplicate = False
        
        # Check for content duplicates (same hash)
        if file_hash in self.file_hashes:
            original_name = self.file_hashes[file_hash]
            if original_name != file_name:  # Don't compare with itself
                show_alert(f"Content duplicate: '{file_name}' matches '{original_name}'", is_error=True)
                content_duplicate = True
        
        # Check for similar filenames (even if content is different)
        if not content_duplicate:  # Only check filename similarity if not content duplicate
            for existing_hash, existing_name in self.file_hashes.items():
                if existing_name != file_name and is_similar_filename(file_name, existing_name):
                    show_alert(f"Similar filename: '{file_name}' resembles '{existing_name}'", is_error=True)
                    filename_duplicate = True
                    break
        
        # If no duplicates found, it's a new file
        if not content_duplicate and not filename_duplicate:
            show_alert(f"New unique file: {file_name}")
            # Add to hash database
            self.file_hashes[file_hash] = file_name
            save_hashes(self.file_hashes)
            print(f"Added {file_name} to database")

    def handle_modified_file(self, file_name, new_file_hash):
        """Handle modified files - check if content changed"""
        # Check if this file already exists in our database with a different hash
        old_hash_found = False
        
        # Find the old hash for this filename
        for existing_hash, existing_name in list(self.file_hashes.items()):
            if existing_name == file_name:
                if existing_hash != new_file_hash:
                    # Content has changed!
                    show_alert(f"Content modified: '{file_name}' - content changed from duplicate to unique", is_modified=True)
                    
                    # Remove old hash entry
                    del self.file_hashes[existing_hash]
                    
                    # Check if new hash creates any duplicates
                    if new_file_hash in self.file_hashes:
                        original_name = self.file_hashes[new_file_hash]
                        show_alert(f"Modified file now duplicates: '{file_name}' now matches '{original_name}'", is_error=True)
                    else:
                        # Add new hash
                        self.file_hashes[new_file_hash] = file_name
                        show_alert(f"File is now unique: '{file_name}' has unique content after modification")
                    
                    save_hashes(self.file_hashes)
                    old_hash_found = True
                    break
                else:
                    # Same hash, no content change
                    print(f"File {file_name} modified but content unchanged")
                    old_hash_found = True
                    break
        
        # If file not found in database, treat as new file
        if not old_hash_found:
            print(f"Modified file {file_name} not in database, treating as new")
            self.check_for_duplicates(file_name, new_file_hash)

def start_monitoring():
    """Start monitoring the download directory"""
    print("=" * 60)
    print("DOWNLOAD MONITOR STARTING")
    print("=" * 60)
    
    if not os.path.exists(DOWNLOAD_DIR):
        print(f"Error: Download directory {DOWNLOAD_DIR} does not exist!")
        return
    
    event_handler = DownloadHandler()
    observer = Observer()
    observer.schedule(event_handler, DOWNLOAD_DIR, recursive=False)
    
    print(f"Monitoring downloads in: {DOWNLOAD_DIR}")
    print(f"Hash database: {HASH_STORE_FILE}")
    print(f"Loaded {len(event_handler.file_hashes)} existing files")
    print("Monitoring for: New files, File modifications, Duplicates")
    print("Press Ctrl+C to stop monitoring...")
    print("=" * 60)
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        observer.stop()
    observer.join()
    print("Monitor stopped.")

if __name__ == "__main__":
    start_monitoring()