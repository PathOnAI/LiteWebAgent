# Loggia Internal: LiteWebAgent

## 1. QuickStart
```
python3.11 -m venv venv
. venv/bin/activate
python -m pip install -r requirements.txt
```
Then, a required step is to setup playwright by running
```
python -m playwright install chromium
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

You are ready to go! Try local testing
```
bash scripts/local_tests/google_test.sh 
bash scripts/local_tests/yc_test.sh
bash scripts/local_tests/clickup_test.sh
```
prod url: https://loggia-webagent.vercel.app

## 2. FastAPI
start local fastapi server
```
cd agent_backend
python -m uvicorn api.main:app --reload
```
at another terminal, directly run the following scripts to test for clickup & loggia websites to test local fastapi server setup, please make sure you have activated the virtual environment

```
. venv/bin/activate
```
Running new version (clickup)
```
bash run_test_clickup.sh
```

Running new version (loggia)
```
bash run_test_loggia.sh
```

### 2.1 unauthenticated
```
curl -X POST 'http://0.0.0.0:8000/start-browserbase' \
-H 'Content-Type: application/json' \
-d '{"storage_state_s3_path": null}'
{"live_browser_url":"https://www.browserbase.com/devtools-fullscreen/inspector.html?wss=connect.browserbase.com/debug/c2375f88-ac4f-4407-a441-00cbb6a37f6e/devtools/page/00180B32E9F5DB9D3ED33F2376D45860?debug=true","session_id":"c2375f88-ac4f-4407-a441-00cbb6a37f6e","status":"started","storage_state_path":null}%   



curl -X POST 'http://0.0.0.0:8000/connect-browserbase' \
-H 'Content-Type: application/json' \
-d '{
    "session_id": "c2375f88-ac4f-4407-a441-00cbb6a37f6e",
    "storage_state_s3_path": null
}'


curl -X POST 'http://0.0.0.0:8000/run-agent-initial-steps-stream' \
-H 'Content-Type: application/json' \
-d '{
  "session_id": "0a8e342e-2f32-4869-b11b-ad514ed7e330",
  "starting_url": "https://www.google.com",
  "goal": "type dining table in text box",
  "s3_path": "s3://loggia-tests/loggia-test/tests/2/flow.json",
  "storage_state_s3_path": null
}'

curl -X POST "http://0.0.0.0:8000/terminate-browserbase?session_id=0a8e342e-2f32-4869-b11b-ad514ed7e330"
```
### 2.2 authenticated
```
curl -X POST 'http://0.0.0.0:8000/start-browserbase' \
-H 'Content-Type: application/json' \
-d '{}'


curl -X POST 'http://0.0.0.0:8000/connect-browserbase' \
-H 'Content-Type: application/json' \
-d '{
    "session_id": "f5cf3536-d401-43ec-a615-50be131c3545"
}'

curl -X POST 'http://0.0.0.0:8000/run-agent-initial-steps-stream' \
-H 'Content-Type: application/json' \
-d '{
  "session_id": "a2919dbe-5283-4810-a48b-46e1fccc47e5",
  "starting_url": "https://app.loggia.ai/",
  "goal": "click on suite on the side bar",
  "s3_path": "s3://loggia-tests/loggia-test/tests/2/flow.json"
}'

curl -X POST "http://0.0.0.0:8000/terminate-browserbase?session_id=a2919dbe-5283-4810-a48b-46e1fccc47e5"
```

### 2.3 code conversion
```
curl -X POST http://0.0.0.0:8000/convert-to-playwright \
-H "Content-Type: application/json" \
-d '{
    "input_s3_path": "s3://loggia-tests/loggia-test/tests/2/flow.json",
    "output_s3_path": "s3://loggia-tests/loggia-test/tests/2/python_code.py"
}'


curl -X POST http://0.0.0.0:8000/convert-to-js-playwright \
-H "Content-Type: application/json" \
-d '{
    "input_s3_path": "s3://loggia-tests/loggia-test/tests/2/flow.json",
    "output_s3_path": "s3://loggia-tests/loggia-test/tests/2/js_code.js"
}'
```

## 3. Local Testing 


### 3.1 Local disk logging log report

Make sure you have LOCAL_LOG_ENABLED=true in your local .env file to enable logging into disk and generate log report. We have it set to false on production as we don't have disk access.      

Run this to generate a combined report under the log folder. 
```
python agent_backend/api/utils/log_report.py
```

Please note that before you run your test, you should have a clean log folder. You can run the following to clean the log folder automatically and then run your test
```
python agent_backend/api/utils/clean_log_folder.py
```
or 

```
python agent_backend/api/utils/clean_log_folder.py --base-dir custom_log_folder
```
if you have a customer log folder location.

### 3.2 End to End Open World Local Testing
example of running loggia test
```
bash scripts/local_tests/loggia_test.sh
```

### 3.3 End to end evaluation
```
python3.11 -m venv venv_eval
. venv/bin/activate
python -m pip install -r eval_requirements.txt
```

After setting the virtual environment, define below environment variables
```
## TODO, will be updated

export DATASET=visualwebarena
export CLASSIFIEDS="http://128.105.146.86:9980"
export CLASSIFIEDS_RESET_TOKEN="4b61655535e7ed388f0d40a93600254c"
export SHOPPING="http://128.105.146.86:7770"
export REDDIT="http://128.105.146.86:9999"
export WIKIPEDIA="http://128.105.146.86:8888"
export HOMEPAGE="http://128.105.146.86:4399"
export OPENAI_API_KEY=your_key
```

There are three types of evaluators. Here is an example of the using the url match evaluator
```
bash scripts/local_eval/clickup_eval_1.sh
```

### 3.4 local end to end testing of clickup test cases with setup and teardown
```
cd e2e_pipeline
bash cases/14/runtest.sh
```


* Run tests with setup and teardown (WIP)
Example:
```
bash scripts/run_e2e.sh --config scripts/clickup_demo_configs/5_config.json
```
This is for local run agent tests with setup and teardown process. Make sure write the setup and teardown code in js playwright tests (check scripts/js_tests for examples). This ensures we can use the same setup and teardown in production test runner. In the config file you can then specify the proper playwright files with needed envrionmental like this:
```
"setup": {
    "script": "scripts/js_tests/clickup/5-setup.test.js",
    "env": {
      "TASK_ID": "868bwazy4"
    }
}
```


## 5 API Agent

All dependencies are in the `requirements.txt` 

`cd` into `e2e_pipeline`

Configure settings in `e2e_pipeline/generate_script.sh` as shown below (modify task-description with steps)

```
python generate_script.py \
    --output-file "path/of/generated/playwright/test" \
    --output-type "playwright" \
    --model "gpt-4o" \
    --task-description "(1) get all docs via the search docs endpoint to get all doc ids in the account
    (2) using the doc ids, delete them using the views endpoint (since docs are views)
    
    remember, that you can't direclty delete or get docs via endpoint, but that docs are a type of view, so you can delete them that way"
```

run `bash generate_script.sh`

then cd generated_scripts/reset

And run the generated playwright javascript file to verify the code
```
npx playwright test docs.spec.js
```