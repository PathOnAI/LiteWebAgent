# LiteWebAgent
repo owners: Danni (Danqing) Zhang (danqing.zhang.personal@gmail.com), and Balaji Rama (balajirw10@gmail.com)

<a href='https://discord.gg/gqap9bzk'><img src='https://img.shields.io/badge/Community-Discord-8A2BE2'></a>


## 2. Development mode
### (1) Installation
First set up virtual environment
```bash
$ python3 -m venv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```

Then please create a .env file, and update your API keys:

```bash
cp .env.example .env
```

### (2) QuickStart
* use web agent to finish some task and save the workflow
```bash
python -m litewebagent.clickup_test --agent_type HighLevelPlanningAgent
python -m litewebagent.webagent
python -m litewebagent.webagent --agent_type HighLevelPlanningAgent
python -m litewebagent.google_test
```
* replay the workflow verified by the web agent
```
cp litewebagent/flow/example.json litewebagent/flow/steps.json 
python -m litewebagent.replay
```

## ✈️ 1. Getting Started with litewebagent

### (1) Installation
First set up virtual environment
```bash
$ python3 -m venv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```

Then please create a .env file, and update your API keys:

```bash
cp .env.example .env
```

### (2) QuickStart
Then log into your clickup account and close the browser to save the authetication information in state.json file

```
cd litewebagent/playground
python persist_state.py
```

Then run tests, or run the webagent file
```
python -m litewebagent.clickup_test
python -m litewebagent.webagent
```


### (3) Enable webarena environment
follow [WorkArena installation instruction](https://github.com/ServiceNow/WorkArena?tab=readme-ov-file#getting-started) to
* Create a ServiceNow Developer Instance
* Install WorkArena and Initialize your Instance