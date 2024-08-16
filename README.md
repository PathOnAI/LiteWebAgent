# LiteWebAgent
Please note that the LiteWebAgent repository is in development mode. We have open-sourced the repository to foster collaboration between contributors.

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
