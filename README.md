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
python -m litewebagent.main --agent_type DemoAgent --starting_url https://www.google.com --goal 'search dining table' --plan 'search dining table'
python -m litewebagent.main --agent_type HighLevelPlanningAgent --starting_url https://www.airbnb.com --goal "set destination as San Francisco, then search the results" --plan "(1) enter the 'San Francisco' as destination, (2) and click search"
python -m litewebagent.main --agent_type ContextAwarePlanningAgent --starting_url https://www.google.com --goal 'search dining table' --plan 'search dining table'
python -m litewebagent.main --agent_type DemoAgent --starting_url https://www.google.com --goal 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"' --plan 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"'
python -m litewebagent.main --agent_type HighLevelPlanningAgent --starting_url https://www.google.com --goal 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"' --plan 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"'
python -m litewebagent.main --agent_type ContextAwarePlanningAgent --starting_url https://www.google.com --goal 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"' --plan 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"'
```
* replay the workflow verified by the web agent
```bash
cp litewebagent/flow/example.json litewebagent/flow/steps.json 
python -m litewebagent.replay
```
* enable user agent interaction
```bash
python -m litewebagent.cli_main --agent_type HighLevelPlanningAgent 
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