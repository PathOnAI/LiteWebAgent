// Listens for installation of the service worker
chrome.runtime.onInstalled.addListener(() => {
    console.log("Service Worker installed.");
});

// Example: Listens for browser action (clicks on the extension icon)
chrome.action.onClicked.addListener((tab) => {
    console.log(`Extension icon clicked on tab: ${tab.id}`);
    chrome.tabs.create({ url: "popup/popup.html" }); // Opens the popup page
});

// Example: Listening for messages from other parts of the extension
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("Message received in Service Worker:", message);

    if (message.greeting === "hello") {
        sendResponse({ farewell: "goodbye" });
    }
});

// Example: Alarm API usage
chrome.alarms.onAlarm.addListener((alarm) => {
    console.log(`Alarm triggered: ${alarm.name}`);
});

// Example: Handling external requests or APIs
chrome.runtime.onConnect.addListener((port) => {
    console.log(`Connected to port: ${port.name}`);

    port.onMessage.addListener((message) => {
        console.log("Message received on port:", message);
        port.postMessage({ response: "Message received by Service Worker" });
    });
});

