document.addEventListener("DOMContentLoaded", function () {
    console.log("📌 result.js loaded!"); // Debugging log

    const showDuplicatesButton = document.getElementById("showDuplicates");

    if (!showDuplicatesButton) {
        console.error("❌ Error: 'Show Duplicates' button not found!");
        return; // Stop execution if the button is missing
    }

    showDuplicatesButton.addEventListener("click", () => {
        console.log("✅ 'Show Duplicates' button clicked!");
    });
});

    showDownloadsButton.addEventListener("click", () => {
        fileList.innerHTML = "<li>Loading...</li>";

        // Fetch ALL downloads
        chrome.downloads.search({}, (downloads) => {
            fileList.innerHTML = ""; // Clear loading message

            let seen = new Set();
            let allFiles = [];
            let duplicates = [];

            downloads.forEach(download => {
                let filePath = download.filename; // Get full file path
                allFiles.push(filePath);

                if (seen.has(filePath)) {
                    duplicates.push(filePath);
                } else {
                    seen.add(filePath);
                }
            });

            // Show all downloaded files
            if (allFiles.length > 0) {
                allFiles.forEach(file => {
                    let li = document.createElement("li");
                    li.textContent = file;
                    fileList.appendChild(li);
                });
            } else {
                fileList.innerHTML = "<li class='no-duplicates'>No downloaded files found.</li>";
            }
        });
    });

    showDuplicatesButton.addEventListener("click", () => {
        fileList.innerHTML = "<li>Loading duplicates...</li>";

        chrome.downloads.search({}, (downloads) => {
            fileList.innerHTML = "";

            let seen = new Set();
            let duplicates = [];

            downloads.forEach(download => {
                let filePath = download.filename; 

                if (seen.has(filePath)) {
                    duplicates.push(filePath);
                } else {
                    seen.add(filePath);
                }
            });

            // Display duplicates
            if (duplicates.length > 0) {
                duplicates.forEach(file => {
                    let li = document.createElement("li");
                    li.textContent = file;
                    fileList.appendChild(li);
                });
            } else {
                fileList.innerHTML = "<li class='no-duplicates'>No duplicate files found.</li>";
            }
        });
    });
