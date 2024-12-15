
export default defineContentScript({
  matches: ['*://*.google.com/*'],
  runAt: 'document_idle',
  main(ctx) {
    console.log('Hello content.');

    // request permission to use microphone
    // https://github.com/GoogleChrome/chrome-extensions-samples/issues/821
    const iframe = document.createElement("iframe");
    iframe.setAttribute("hidden", "hidden");
    iframe.setAttribute("id", "permissionsIFrame");
    iframe.setAttribute("allow", "microphone");
    iframe.src = chrome.runtime.getURL("permission.html");
    document.body.appendChild(iframe);
  },
});
