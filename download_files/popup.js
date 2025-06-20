document.addEventListener("DOMContentLoaded", function () {
    const showDownloadsButton = document.getElementById("showDownloads");
    const showDuplicatesButton = document.getElementById("showDuplicates");
    const fileList = document.getElementById("duplicateFilesList");

    let allFiles = [];
    let duplicates = [];

    // Fetch all downloaded files and find duplicates
    function fetchDownloads() {
        chrome.downloads.search({}, function (downloads) {
            console.log("🔍 Fetching downloads...");
            allFiles = [];
            let fileMap = new Map();

            downloads.forEach(download => {
                let filePath = download.filename.trim(); // Keep full path
                let fileName = filePath.split('\\').pop().toLowerCase(); // Extract filename

                allFiles.push({ id: download.id, path: filePath, name: fileName });

                fileMap.set(fileName, (fileMap.get(fileName) || 0) + 1);
            });

            // Find duplicate files
            duplicates = allFiles.filter(file => fileMap.get(file.name) > 1);
            console.log("🛑 Duplicate Files Found:", duplicates);

            displayFiles(allFiles, "Downloaded Files:");
        });
    }

    // Display files in the list
    function displayFiles(files, title, allowDelete = false) {
        fileList.innerHTML = "";

        if (files.length === 0) {
            fileList.innerHTML = `<li class='no-duplicates'>No files found.</li>`;
            return;
        }

        let titleItem = document.createElement("li");
        titleItem.classList.add("title");
        titleItem.textContent = title;
        fileList.appendChild(titleItem);

        files.forEach(file => {
            let li = document.createElement("li");
            li.innerHTML = `<strong>${file.name}</strong><br><small>${file.path}</small>`;

            if (allowDelete) {
                let deleteBtn = document.createElement("button");
                deleteBtn.textContent = "❌ Delete";
                deleteBtn.classList.add("delete-btn");
                deleteBtn.addEventListener("click", function () {
                    deleteFile(file.id, file.path);
                });
                li.appendChild(deleteBtn);
            }

            fileList.appendChild(li);
        });
    }

    // Delete a file by its ID
    function deleteFile(fileId, filePath) {
        chrome.downloads.erase({ id: fileId }, function () {
            console.log(`🗑️ Deleted: ${filePath}`);
            fetchDownloads(); // Refresh list after deletion
        });
    }

    // Show Downloads Button Click Event
    showDownloadsButton.addEventListener("click", fetchDownloads);

    // Show Duplicates Button Click Event
    showDuplicatesButton.addEventListener("click", function () {
        console.log("🛑 Checking for duplicates...");
        displayFiles(duplicates, "Duplicate Files (With Location):", true);
    });

    // Listen for messages from background.js about duplicate files
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.duplicateFile) {
            console.log(`⚠️ Duplicate Alert: ${message.duplicateFile}`);
            fileList.innerHTML = `<li class='alert'>⚠️ Duplicate File: ${message.duplicateFile} already exists!</li>`;
        }
    });
});
