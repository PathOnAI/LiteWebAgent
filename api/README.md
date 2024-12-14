# README

## 1. sync backend
start fastapi server from root
```
python -m uvicorn api.server_sync:app --reload --port=5001
```

## 2. async backend
start fastapi server from root
```
python -m uvicorn api.server_async:app --reload --port=5001
```
https://www.loom.com/share/1f5b65069ac84e41bb01ff90e9ecd867

```
curl -X POST http://localhost:5001/create-playwright-manager \
-H "Content-Type: application/json" \
-d '{
    "session_id": "test-session",
    "storage_state": "state.json",
    "headless": false,
    "mode": "cdp"
}'

curl http://localhost:5001/list-sessions                      
{"sessions":["test-session","test-session-1","test-session-2"],"count":3}% 



curl -X POST http://localhost:5001/run-agent-initial-steps \
-H "Content-Type: application/json" \
-d '{
    "session_id": "test-session",
    "starting_url": "https://www.google.com",
    "goal": "search dining table",
    "plan": "type dining table"
}'

curl -X POST http://localhost:5001/run-agent-followup-steps \
-H "Content-Type: application/json" \
-d '{
    "session_id": "test-session",
    "plan": "click google search"
}'
```