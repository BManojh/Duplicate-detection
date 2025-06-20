chrome.downloads.onDeterminingFilename.addListener((downloadItem, suggest) => {
    let filename = downloadItem.filename.split('\\').pop().toLowerCase(); // Extract file name

    chrome.storage.local.get(["downloadedFiles"], (result) => {
        let downloadedFiles = result.downloadedFiles || [];

        if (downloadedFiles.includes(filename)) {
            // 🚀 Send message to popup.js
            chrome.runtime.sendMessage({ duplicateFile: filename });
            
            // ❌ Prevent duplicate download (optional)
            suggest({ filename, conflictAction: "overwrite" });

        } else {
            downloadedFiles.push(filename);
            chrome.storage.local.set({ downloadedFiles });
        }
    });
});
