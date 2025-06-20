document.addEventListener("DOMContentLoaded", () => {
    
    // Wait for the DOM to fully load before accessing elements
    let inputField = document.getElementById("ignoredExtensions");
    let saveButton = document.getElementById("saveSettings");

    // Check if the elements exist
    if (!inputField || !saveButton) {
        console.error("Settings elements not found.");
        return;
    }

    // Load saved settings
    chrome.storage.local.get("ignoredExtensions", (data) => {
        if (chrome.runtime.lastError) {
            console.error("Error loading storage:", chrome.runtime.lastError);
            return;
        }
        if (data.ignoredExtensions) {
            inputField.value = data.ignoredExtensions.join(", ");
        }
    });

    // Save settings when the button is clicked
    saveButton.addEventListener("click", () => {
        let input = inputField.value;
        let extensions = input.split(",").map(ext => ext.trim().toLowerCase());

        chrome.storage.local.set({ "ignoredExtensions": extensions }, () => {
            if (chrome.runtime.lastError) {
                console.error("Error saving settings:", chrome.runtime.lastError);
            } else {
                alert("Settings saved!");
            }
        });
    });
});
