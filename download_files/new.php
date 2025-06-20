<?php
// Database configuration
$db_host = 'localhost';
$db_name = 'file_tracker';
$db_user = 'root';
$db_pass = ''; // Add your password if needed

// Create database connection
try {
    $conn = new PDO("mysql:host=$db_host;dbname=$db_name", $db_user, $db_pass);
    // Set the PDO error mode to exception
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    die("Connection failed: " . $e->getMessage());
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Download Duplicate Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
        }
        .download-section {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        #fileInput {
            flex-grow: 1;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .alert-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            display: none;
        }
        .alert-box {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            max-width: 400px;
            width: 100%;
            text-align: center;
        }
        .alert-title {
            font-size: 1.2em;
            margin-bottom: 10px;
            font-weight: bold;
        }
        .alert-message {
            margin-bottom: 20px;
            white-space: pre-line;
        }
        .alert-btn {
            padding: 8px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .duplicate {
            background-color: #ffdddd;
        }
        #downloadsList {
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 10px;
            margin-bottom: 20px;
            background-color: #f9f9f9;
            display: none;
        }
        .file-item {
            padding: 5px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
        }
        .btn {
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .btn:hover {
            background-color: #45a049;
        }
        .btn:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .btn-remove {
            background-color: #f44336;
            padding: 3px 8px;
            font-size: 12px;
        }
        .btn-remove:hover {
            background-color: #d32f2f;
        }
        .status-new {
            color: green;
            font-weight: bold;
        }
        .status-duplicate {
            color: red;
            font-weight: bold;
        }
        .original-time {
            font-size: 0.9em;
            color: #666;
            display: block;
        }
        .processing {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background-color: #4CAF50;
            color: white;
            padding: 10px;
            text-align: center;
            z-index: 1001;
            display: none;
        }
    </style>
</head>
<body>
    <div class="processing" id="processingIndicator">
        Processing files... Please wait
    </div>

    <div class="container">
        <h1>Download Duplicate Tracker</h1>
        
        <button id="showDownloadsBtn" class="btn" onclick="toggleDownloadsList()">Show Recent Downloads</button>
        <div id="downloadsList">
            <h3>Recent Downloads:</h3>
            <div id="existingFilesList"></div>
        </div>
        
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="download-section">
                <input type="file" id="fileInput" name="files[]" multiple>
                <button type="button" class="btn" id="checkFilesBtn" onclick="handleFilesUpload()">Check Files</button>
            </div>
        </form>
        
        <table>
            <thead>
                <tr>
                    <th>Filename</th>
                    <th>Size</th>
                    <th>First Detected</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody id="downloadHistory">
                <!-- Download history will be populated here -->
            </tbody>
        </table>
    </div>

    <!-- Alert Modal -->
    <div class="alert-overlay" id="alertOverlay">
        <div class="alert-box">
            <div class="alert-title" id="alertTitle">Alert</div>
            <div class="alert-message" id="alertMessage"></div>
            <button class="alert-btn" onclick="closeAlert()">OK</button>
        </div>
    </div>

    <script>
        // Download Tracking Class with PHP backend integration
        class DownloadTracker {
            constructor() {
                this.processing = false;
                this.recentDownloads = [];
                this.downloadHistory = [];
                this.loadDownloadHistory();
            }

            async loadDownloadHistory() {
                try {
                    const response = await fetch('file_handler.php?action=get_history');
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        this.downloadHistory = data.data;
                        this.recentDownloads = data.data.slice(0, 10);
                        renderDownloadHistory();
                    } else {
                        console.error('Failed to load history:', data.message);
                    }
                } catch (error) {
                    console.error('Error loading history:', error);
                }
            }

            async uploadFile(file) {
                try {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const response = await fetch('file_handler.php?action=upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    return await response.json();
                } catch (error) {
                    console.error('Error uploading file:', error);
                    return {
                        status: 'error',
                        message: 'Network error: ' + error.message
                    };
                }
            }

            async removeFile(hash) {
                try {
                    const formData = new FormData();
                    formData.append('hash', hash);
                    
                    const response = await fetch('file_handler.php?action=remove_file', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        // Refresh history after removal
                        await this.loadDownloadHistory();
                    }
                    
                    return result;
                } catch (error) {
                    console.error('Error removing file:', error);
                    return {
                        status: 'error',
                        message: 'Network error: ' + error.message
                    };
                }
            }

            async uploadMultipleFiles(files) {
                try {
                    const formData = new FormData();
                    
                    for (let i = 0; i < files.length; i++) {
                        formData.append('files[]', files[i]);
                    }
                    
                    const response = await fetch('file_handler.php?action=batch_upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    return await response.json();
                } catch (error) {
                    console.error('Error uploading multiple files:', error);
                    return {
                        status: 'error',
                        message: 'Network error: ' + error.message
                    };
                }
            }
        }

        const tracker = new DownloadTracker();

        function showCustomAlert(title, message) {
            document.getElementById('alertTitle').textContent = title;
            document.getElementById('alertMessage').textContent = message;
            document.getElementById('alertOverlay').style.display = 'flex';
        }

        function closeAlert() {
            document.getElementById('alertOverlay').style.display = 'none';
        }

        function toggleDownloadsList() {
            const downloadsList = document.getElementById('downloadsList');
            const btn = document.getElementById('showDownloadsBtn');
            
            if (downloadsList.style.display === 'none' || !downloadsList.style.display) {
                downloadsList.style.display = 'block';
                btn.textContent = 'Hide Recent Downloads';
                renderRecentDownloads();
            } else {
                downloadsList.style.display = 'none';
                btn.textContent = 'Show Recent Downloads';
            }
        }

        function renderRecentDownloads() {
            const existingFilesList = document.getElementById('existingFilesList');
            existingFilesList.innerHTML = '';
            
            if (tracker.recentDownloads.length === 0) {
                existingFilesList.innerHTML = '<p>No recent downloads</p>';
                return;
            }
            
            const recentToShow = tracker.recentDownloads.slice(0, 10);
            
            recentToShow.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                
                const fileInfo = document.createElement('span');
                fileInfo.textContent = `${file.filename} (${file.filesize}) - ${file.first_detected}`;
                
                const removeBtn = document.createElement('button');
                removeBtn.className = 'btn-remove';
                removeBtn.textContent = 'Remove';
                removeBtn.onclick = async () => {
                    const result = await tracker.removeFile(file.filehash);
                    if (result.status === 'success') {
                        showCustomAlert('Removed', `${file.filename} has been removed from history`);
                    } else {
                        showCustomAlert('Error', result.message);
                    }
                };
                
                fileItem.appendChild(fileInfo);
                fileItem.appendChild(removeBtn);
                existingFilesList.appendChild(fileItem);
            });
        }

        async function processFile(file) {
            try {
                const result = await tracker.uploadFile(file);
                
                if (result.status === 'duplicate') {
                    showCustomAlert(
                        'Duplicate Found', 
                        `"${file.name}" is a duplicate\n\nOriginally downloaded: ${result.originalEntry.firstDetected}`
                    );
                } else if (result.status === 'success') {
                    showCustomAlert('New File', `${file.name} has been added`);
                    // Refresh history
                    await tracker.loadDownloadHistory();
                } else {
                    showCustomAlert('Error', result.message);
                }
                
                if (document.getElementById('downloadsList').style.display === 'block') {
                    renderRecentDownloads();
                }
                
            } catch (error) {
                console.error(`Error processing ${file.name}:`, error);
                showCustomAlert('Error', `Error processing ${file.name}: ${error.message}`);
            }
        }

        async function handleFilesUpload() {
            const fileInput = document.getElementById('fileInput');
            const checkFilesBtn = document.getElementById('checkFilesBtn');
            
            if (tracker.processing) {
                showCustomAlert('Warning', 'Please wait while current files are processed');
                return;
            }

            if (!fileInput.files.length) {
                showCustomAlert('Error', 'Please select files to check');
                return;
            }

            // Set processing state
            tracker.processing = true;
            checkFilesBtn.disabled = true;
            checkFilesBtn.textContent = 'Processing...';
            document.getElementById('processingIndicator').style.display = 'block';
            
            try {
                // We have two options:
                // 1. Process files individually (better for showing individual results)
                const files = Array.from(fileInput.files);
                for (let i = 0; i < files.length; i++) {
                    await processFile(files[i]);
                    
                    // Small delay every few files to keep UI responsive
                    if (i % 3 === 0) {
                        await new Promise(resolve => setTimeout(resolve, 50));
                    }
                }
                
                // 2. Or process files in batch (faster but less detailed feedback)
                // const result = await tracker.uploadMultipleFiles(fileInput.files);
                // if (result.status === 'success') {
                //     await tracker.loadDownloadHistory();
                //     showCustomAlert('Files Processed', `${fileInput.files.length} files processed`);
                // } else {
                //     showCustomAlert('Error', result.message);
                // }
                
            } catch (error) {
                console.error('Error in handleFilesUpload:', error);
                showCustomAlert('Error', 'An error occurred while processing files');
            } finally {
                // Reset processing state
                tracker.processing = false;
                checkFilesBtn.disabled = false;
                checkFilesBtn.textContent = 'Check Files';
                document.getElementById('processingIndicator').style.display = 'none';
                fileInput.value = '';
            }
        }

        function renderDownloadHistory() {
            const downloadHistory = document.getElementById('downloadHistory');
            downloadHistory.innerHTML = '';

            tracker.downloadHistory.forEach(file => {
                const row = document.createElement('tr');
                
                const removeBtn = document.createElement('button');
                removeBtn.className = 'btn-remove';
                removeBtn.textContent = 'Remove';
                removeBtn.onclick = async () => {
                    const result = await tracker.removeFile(file.filehash);
                    if (result.status === 'success') {
                        showCustomAlert('Removed', `${file.filename} has been removed from history`);
                    } else {
                        showCustomAlert('Error', result.message);
                    }
                };
                
                row.innerHTML = `
                    <td>${file.filename}</td>
                    <td>${file.filesize}</td>
                    <td>${file.first_detected}</td>
                    <td class="status-${file.is_duplicate ? 'duplicate' : 'new'}">
                        ${file.is_duplicate ? 'Duplicate' : 'New'}
                    </td>
                    <td></td>
                `;
                
                row.children[4].appendChild(removeBtn);
                downloadHistory.appendChild(row);
            });
        }

        // Initialize on page load
        window.onload = function() {
            // Load history from server
            tracker.loadDownloadHistory();
            
            // Add event listener to prevent multiple rapid clicks
            document.getElementById('checkFilesBtn').addEventListener('click', function(e) {
                if (tracker.processing) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    showCustomAlert('Warning', 'Please wait while current files are processed');
                }
            });
        };
    </script>
</body>
</html>