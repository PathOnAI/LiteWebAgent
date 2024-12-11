# LiteWebAgent Chrome Extension

Chrome extension frontend for LiteWebAgent web automation tool.

## 1. Configuration 
### 1.1 Set up CDP
```
pkill -f "Google Chrome"
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

### 1.2 Install chrome extension

1. Enable Chrome Developer Mode:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" in the top right

2. Load the Extension:
   - Click "Load unpacked"
   - Select this `chrome_extension` directory

### 1.3 Start LiteWebAgent AI backend

1. Start the Python backend server:
```bash
python3.11 -m uvicorn api.server:app --reload --port=5001
```

## 2. Usage
2. Click the extension icon in Chrome
3. Configure your automation parameters
4. Click "Start Automation"

## 3. Development

The extension communicates with the Python backend via REST API endpoints:
- Backend server runs on `http://localhost:5001`
- All automation configuration is sent to `/automate` endpoint
- Existing LiteWebAgent functionality is preserved

## 4. Configuration

Default settings can be modified in `popup.js`. Available options:
- Model: default "gpt-4o-mini"
- Features: default "axtree"
- Elements Filter: "som", "visibility", or "none"
- Branching Factor: default 5


## 5. Debug
If Playwright cannot detect the correct page, restart Chrome and the Python backend server. Keep only one active tab open for this browser automation task.