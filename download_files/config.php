<?php
// Include database configuration
require_once 'config.php';

// Set headers for JSON response
header('Content-Type: application/json');

// Function to calculate file hash
function calculateFileHash($file_path) {
    return hash_file('sha256', $file_path);
}

// Function to format file size
function formatFileSize($bytes) {
    if ($bytes === 0) return '0 Bytes';
    $k = 1024;
    $sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    $i = floor(log($bytes) / log($k));
    return round($bytes / pow($k, $i), 2) . ' ' . $sizes[$i];
}

// Function to check if file is duplicate and add to database if not
function processFile($conn, $file) {
    try {
        $file_name = $file['name'];
        $file_size = $file['size'];
        $file_tmp = $file['tmp_name'];
        $content_type = $file['type'];
        
        // Calculate file hash
        $file_hash = calculateFileHash($file_tmp);
        
        // Check if file already exists in database
        $stmt = $conn->prepare("SELECT * FROM files WHERE filehash = :filehash");
        $stmt->bindParam(':filehash', $file_hash);
        $stmt->execute();
        
        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($result) {
            // File is a duplicate
            return [
                'status' => 'duplicate',
                'message' => 'File is a duplicate',
                'originalEntry' => [
                    'filename' => $result['filename'],
                    'size' => $result['filesize'],
                    'firstDetected' => $result['first_detected'],
                    'hash' => $result['filehash']
                ]
            ];
        } else {
            // New file, add to database
            $formatted_size = formatFileSize($file_size);
            
            $stmt = $conn->prepare("INSERT INTO files (filename, filesize, filehash, content_type) 
                                   VALUES (:filename, :filesize, :filehash, :content_type)");
            
            $stmt->bindParam(':filename', $file_name);
            $stmt->bindParam(':filesize', $formatted_size);
            $stmt->bindParam(':filehash', $file_hash);
            $stmt->bindParam(':content_type', $content_type);
            
            $stmt->execute();
            
            // Optionally save the file to a directory
            // move_uploaded_file($file_tmp, 'uploads/' . $file_name);
            
            return [
                'status' => 'success',
                'message' => 'File added successfully',
                'fileInfo' => [
                    'filename' => $file_name,
                    'size' => $formatted_size,
                    'firstDetected' => date('Y-m-d H:i:s'),
                    'hash' => $file_hash
                ]
            ];
        }
    } catch (PDOException $e) {
        return [
            'status' => 'error',
            'message' => 'Database error: ' . $e->getMessage()
        ];
    } catch (Exception $e) {
        return [
            'status' => 'error',
            'message' => 'Error processing file: ' . $e->getMessage()
        ];
    }
}

// Function to get file history
function getFileHistory($conn) {
    try {
        $stmt = $conn->prepare("SELECT * FROM files ORDER BY first_detected DESC");
        $stmt->execute();
        $files = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        return [
            'status' => 'success',
            'data' => $files
        ];
    } catch (PDOException $e) {
        return [
            'status' => 'error',
            'message' => 'Database error: ' . $e->getMessage()
        ];
    }


// Function to remove a file from history
function removeFile($conn, $hash) {
    try {
        $stmt = $conn->prepare("DELETE FROM files WHERE filehash = :filehash");
        $stmt->bindParam(':filehash', $hash);
        $stmt->execute();
        
        return [
            'status' => 'success',
            'message' => 'File removed successfully'
        ];
    } catch (PDOException $e) {
        return [
            'status' => 'error',
            'message' => 'Database error: ' . $e->getMessage()
        ];
    }
}

// Handle API requests
$action = isset($_GET['action']) ? $_GET['action'] : '';

switch ($action) {
    case 'upload':
        if (!isset($_FILES['file'])) {
            echo json_encode(['status' => 'error', 'message' => 'No file uploaded']);
            exit;
        }
        
        $response = processFile($conn, $_FILES['file']);
        echo json_encode($response);
        break;
        
    case 'get_history':
        $response = getFileHistory($conn);
        echo json_encode($response);
        break;
        
    case 'remove_file':
        if (!isset($_POST['hash'])) {
            echo json_encode(['status' => 'error', 'message' => 'No file hash provided']);
            exit;
        }
        
        $response = removeFile($conn, $_POST['hash']);
        echo json_encode($response);
        break;
        
    case 'batch_upload':
        $responses = [];
        $fileCount = count($_FILES['files']['name']);
        
        for ($i = 0; $i < $fileCount; $i++) {
            $file = [
                'name' => $_FILES['files']['name'][$i],
                'size' => $_FILES['files']['size'][$i],
                'tmp_name' => $_FILES['files']['tmp_name'][$i],
                'type' => $_FILES['files']['type'][$i]
            ];
            
            $responses[] = processFile($conn, $file);
        }
        
        echo json_encode(['status' => 'success', 'data' => $responses]);
        break;
        
    default:
        echo json_encode(['status' => 'error', 'message' => 'Invalid action']);
}
?>