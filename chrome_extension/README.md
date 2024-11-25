# LiteWebAgent Chrome Extension

Chrome extension frontend for LiteWebAgent web automation tool.

## Installation

1. Enable Chrome Developer Mode:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" in the top right

2. Load the Extension:
   - Click "Load unpacked"
   - Select this `chrome_extension` directory

## Usage

1. Start the Python backend server:
```bash
python -m litewebagent.api.server
```

2. Click the extension icon in Chrome
3. Configure your automation parameters
4. Click "Start Automation"

## Development

The extension communicates with the Python backend via REST API endpoints:
- Backend server runs on `http://localhost:5000`
- All automation configuration is sent to `/automate` endpoint
- Existing LiteWebAgent functionality is preserved

## Configuration

Default settings can be modified in `popup.js`. Available options:
- Model: default "gpt-4o-mini"
- Features: default "axtree"
- Elements Filter: "som", "visibility", or "none"
- Branching Factor: default 5