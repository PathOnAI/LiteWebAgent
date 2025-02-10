# LiteWebAgent backend

## 1. QuickStart
```
python3.11 -m venv venv
. venv/bin/activate
pip3.11 install -r requirements.txt
```
Then, a required step is to setup playwright by running
```
playwright install chromium
```
test your playwright installation
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # Set headless=True if you prefer no UI
    page = browser.new_page()
    page.goto('https://example.com')
    print(page.title())
    browser.close()

```

Then please create a .env file, and update your API keys:

```bash
cp .env.example .env
```

You are ready to go! Try FunctionCallingAgent on google.com
```
python3.11 api/google_test.py
```

start local fastapi server

```
python3.11 -m api.main
```

## 2. Local testing
start browserbase session, retrieve live_browser_url for the frontend
```
curl -X POST 'http://0.0.0.0:8000/start-browserbase' \
-H 'Content-Type: application/json' \
-d '{"storage_state_s3_path": null}'
{"live_browser_url":"https://www.browserbase.com/devtools-fullscreen/inspector.html?wss=connect.browserbase.com/debug/f525ba67-c88e-4485-b207-dd9bf188729f/devtools/page/1467F73862C1EB9B7C68C41A4C654BD6?debug=true","session_id":"f525ba67-c88e-4485-b207-dd9bf188729f","status":"started","storage_state_path":null}%   
```


set goal, and some initial steps
```
curl -X POST 'http://0.0.0.0:8000/run-agent-initial-steps-stream' \
-H 'Content-Type: application/json' \
-d '{
  "session_id": "f525ba67-c88e-4485-b207-dd9bf188729f",
  "starting_url": "https://www.google.com",
  "goal": "type dining table in text box",
  "s3_path": "s3://loggia-tests/loggia-test/tests/2/flow.json",
  "storage_state_s3_path": null
}'



data: {"type": "status", "message": "Starting setup..."}

data: {"type": "status", "message": "Storage state loaded"}

data: {"type": "browser", "message": "Browser connected at https://www.browserbase.com/devtools-fullscreen/inspector.html?wss=connect.browserbase.com/debug/f525ba67-c88e-4485-b207-dd9bf188729f/devtools/page/1467F73862C1EB9B7C68C41A4C654BD6?debug=true"}

data: {"type": "status", "message": "Agent setup complete"}

data: {"type": "thinking", "message": "Processing next step..."}

data: {"type": "tool_calls", "message": "Executing 1 actions..."}

data: {"type": "tool_execution", "message": "Executing: navigation"}

data: {"type": "tool_result", "message": {"tool_call_id": "call_UAJ8YtGfkMmIKE3QCZ5XgFnn", "role": "tool", "name": "navigation", "content": "The action is: ```fill('90', 'dining table')``` - the result is: Yes, the goal is finished. The screenshot shows that the text \"dining table\" has been typed into the Google search box, as evidenced by its presence in the text input field. This aligns with the original goal of typing \"dining table\" in the text box."}}

data: {"type": "thinking", "message": "The task of typing \"dining table\" in the text box has been completed. Please provide further instructions if needed."}

data: {"type": "action", "message": "No actions needed"}

data: {"type": "complete", "message": "Task completed", "response": [{"finish_reason": "stop", "index": 0, "message": {"content": "The task of typing \"dining table\" in the text box has been completed. Please provide further instructions if needed.", "role": "assistant", "tool_calls": null, "function_call": null}}]}
```

add some follow-up steps
```
curl -X POST 'http://0.0.0.0:8000/run-agent-followup-steps-stream' \
-H 'Content-Type: application/json' \
-d '{
  "session_id": "f525ba67-c88e-4485-b207-dd9bf188729f",
  "goal": "click on search button",
  "s3_path": "s3://loggia-tests/loggia-test/tests/2/flow.json",
  "storage_state_s3_path": null
}'
```


terminate the browserbase session, whole session completed
```
curl -X POST "http://0.0.0.0:8000/terminate-browserbase?session_id=f525ba67-c88e-4485-b207-dd9bf188729f"
{"status":"terminated"}%
```

### 3. Production
```
curl -X POST 'https://lite-web-agent-backend.vercel.app/start-browserbase' \
-H 'Content-Type: application/json' \
-d '{"storage_state_s3_path": null}'  
{"live_browser_url":"https://www.browserbase.com/devtools-fullscreen/inspector.html?wss=connect.browserbase.com/debug/3744d2f6-4ba5-4d98-a44c-5b03fc7b33a3/devtools/page/30A3CDBECAE2E9B96FCE5A6FAD83D6BA?debug=true","session_id":"3744d2f6-4ba5-4d98-a44c-5b03fc7b33a3","status":"started","storage_state_path":null}
```


```
curl -X POST 'https://lite-web-agent-backend.vercel.app/run-agent-initial-steps-stream' \
-H 'Content-Type: application/json' \
-d '{
  "session_id": "3744d2f6-4ba5-4d98-a44c-5b03fc7b33a3",
  "starting_url": "https://www.google.com",
  "goal": "type dining table in text box",
  "s3_path": "s3://loggia-tests/loggia-test/tests/2/flow.json",
  "storage_state_s3_path": null
}'
```

```
curl -X POST "https://lite-web-agent-backend.vercel.app/terminate-browserbase?session_id=3744d2f6-4ba5-4d98-a44c-5b03fc7b33a3"
{"status":"terminated"}%
```