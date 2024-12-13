# LiteWebAgent Chrome Extension Documentation

## Overview
LiteWebAgent Chrome Extension provides a user interface for the LiteWebAgent web automation framework, enabling browser automation through a convenient Chrome extension.

## Installation

### Prerequisites
- Google Chrome browser
- Node.js and npm
- Python 3.10 or higher

### Chrome DevTools Protocol (CDP) Configuration
1. Close all existing Chrome instances:
```bash
pkill -f "Google Chrome"
```

2. Launch Chrome with remote debugging enabled:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

### Extension Installation
1. Build the extension using WXT framework:
```bash
npm install
npm run dev
```

2. Install in Chrome:
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Select "Load unpacked"
   - Navigate to and select the `chrome_extension/.output/chrome-mv3` directory
      - On MacOS, use `Command ⌘ + Shift ⇧ + .` to show hidden folder `.output`

### Backend Setup
1. Install required Python packages
2. Start the backend server:
```bash
python -m uvicorn api.server:app --reload --port=5001
```


## Configuration Parameters

### Default Settings
The following parameters can be configured in the popup:

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| Model | gpt-4o-mini | AI model selection |
| Features | axtree | Feature extraction method |
| Elements Filter | som | DOM element filtering ("som", "visibility", "none") |
| Branching Factor | 5 | Maximum number of branches per node |

## Architecture

### API Integration
- Backend Server: `http://localhost:5001`
- Primary Endpoint: `/automate`
- Communication: REST API
- Protocol: HTTP/JSON

## Troubleshooting

### Common Issues and Solutions

#### Playwright Page Detection Issues
If Playwright fails to detect the correct page:
1. Close Chrome completely
2. Restart the Python backend server
3. Ensure only one active tab is open during automation

#### Backend Processing Issues
If the AI backend stops processing requests:

1. Uninstall Playwright:
```bash
python -m pip uninstall playwright
```

2. Reinstall Playwright:
```bash
python -m pip install playwright
python -m playwright install
```

## Usage Instructions

1. Click the extension icon in Chrome's toolbar
2. Configure automation parameters as needed
3. Click "Start Automation" to begin the process
4. Monitor the automation progress in the extension interface


---
