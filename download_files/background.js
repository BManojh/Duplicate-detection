chrome.downloads.onDeterminingFilename.addListener((downloadItem, suggest) => {
    let filename = downloadItem.filename.split('\\').pop(); // Get only the file name

    // Check if the file exists
    chrome.storage.local.get(["downloadedFiles"], (result) => {
        let downloadedFiles = result.downloadedFiles || [];
        
        if (downloadedFiles.includes(filename)) {
            // Show alert for duplicate file
            chrome.notifications.create({
                type: "basic",
                iconUrl: "icon.png",
                title: "Duplicate File Alert",
                message: `The file "${filename}" is already downloaded!`
            });

            
            suggest({ filename, conflictAction: "overwrite" });
        } else {
            // Add new file to storage
            downloadedFiles.push(filename);
            chrome.storage.local.set({ downloadedFiles });
        }
    });
});

