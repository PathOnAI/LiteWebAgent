# LiteWebAgent
repo owner: Danni (Danqing) Zhang (danqing.zhang.personal@gmail.com)

main contributors: Balaji Rama (balajirw10@gmail.com), Shiying He (sy.he0303@gmail.com) and Jingyi Ni (jingyi.ni.personal@gmail.com)

Please note that the LiteWebAgent repository is in development mode. We have open-sourced the repository to foster collaboration between contributors.

<a href='https://danqingz.github.io/blog/2024/08/22/LiteWebAgent.html'><img src='https://img.shields.io/badge/BLOG-181717?logo=github&logoColor=white'></a>
<a href='https://litewebagent.readthedocs.io/en/latest/'><img src='https://img.shields.io/badge/Documentation-green'></a>

## 2. Development mode
### (1) Installation
* From PyPI: https://pypi.org/project/litewebagent/
```
pip install litewebagent 
```
Then, a required step is to setup playwright by running
```
playwright install chromium
```
* Set up locally

First set up virtual environment, and allow your code to be able to see 'litewebagent'
```bash
python3 -m venv venv
. venv/bin/activate
pip install -e .
```
Then please create a .env file, and update your API keys:

```bash
cp .env.example .env
```

### (2) QuickStart
* use web agent to finish some task and save the workflow
```bash
python -m main --agent_type FunctionCallingAgent --starting_url https://www.google.com --goal 'search dining table' --plan 'search dining table' --log_folder log
python -m main --agent_type PromptAgent --starting_url https://www.google.com --goal 'search dining table' --plan 'search dining table' --log_folder log
python -m main --agent_type HighLevelPlanningAgent --starting_url https://www.airbnb.com --goal "set destination as San Francisco, then search the results" --plan "(1) enter the 'San Francisco' as destination, (2) and click search" --log_folder log
python -m main --agent_type ContextAwarePlanningAgent --starting_url https://www.google.com --goal 'search dining table' --plan 'search dining table' --log_folder log
python -m main --agent_type FunctionCallingAgent --starting_url https://www.google.com --goal 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"' --plan 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"' --log_folder log
python -m main --agent_type HighLevelPlanningAgent --starting_url https://www.google.com --goal 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"' --plan 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"' --log_folder log
python -m main --agent_type ContextAwarePlanningAgent --starting_url https://www.google.com --goal 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"' --plan 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"' --log_folder log
python -m main --agent_type FunctionCallingAgent --starting_url https://www.google.com --goal 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"' --plan 'Find the pdf of the paper "GPT-4V(ision) is a Generalist Web Agent, if Grounded"' --log_folder log
```
https://www.loom.com/share/1018bcc4e21c4a7eb517b60c2931ee3c
https://www.loom.com/share/aa48256478714d098faac740239c9013
https://www.loom.com/share/89f5fa69b8cb49c8b6a60368ddcba103

* replay the workflow verified by the web agent
If you haven't used the web agent to try any tests yet, first copy our example.json file.
```bash
cp log/flow/example.json log/flow/steps.json 
```
then you can replay the session
```bash
python litewebagent/utils/replay.py --log_folder log
```
* enable user agent interaction

```bash
python -m cli_main --agent_type FunctionCallingAgent --log_folder log
python -m cli_main --agent_type HighLevelPlanningAgent --log_folder log
python -m cli_main --agent_type PromptAgent --log_folder log
```

https://www.loom.com/share/93e3490a6d684cddb0fbefce4813902a

### (3) test different input features
We use axtree by default. Alternatively, you can provide a comma-separated string listing the desired input feature types.
```bash
python -m main --agent_type FunctionCallingAgent --starting_url https://www.airbnb.com --goal 'set destination as San Francisco, then search the results' --plan '(1) enter the "San Francisco" as destination, (2) and click search' --log_folder log
python -m main --agent_type FunctionCallingAgent --starting_url https://www.airbnb.com --goal 'set destination as San Francisco, then search the results' --plan '(1) enter the "San Francisco" as destination, (2) and click search' --features interactive_elements --log_folder log
python -m main --agent_type FunctionCallingAgent --starting_url https://www.airbnb.com --goal 'set destination as San Francisco, then search the results' --plan '(1) enter the "San Francisco" as destination, (2) and click search' --features axtree,interactive_elements --log_folder log
```

### (4) search_agent
```
python -m search_main --agent_type PromptSearchAgent --starting_url https://www.google.com --goal 'search dining table' --plan 'search dining table' --search_algorithm 'bfs' --log_folder log
```

https://www.loom.com/share/986f0addf10949d88ae25cd802588a85

## 3. Paper reimplementation
| Paper                                                                    | Agent                                                                                                                                                  |
|--------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Mind2Web](https://osu-nlp-group.github.io/Mind2Web/)                    | [ContextAwarePlanningAgent](https://github.com/PathOnAI/LiteWebAgent/blob/main/litewebagent/agents/FunctionCallingAgents/ContextAwarePlanningAgent.py) |
| [Tree Search for Language Model Agents](https://jykoh.com/search-agents) | [PromptSearchAgent](https://github.com/PathOnAI/LiteWebAgent/blob/main/litewebagent/agents/SearchAgents/PromptSearchAgent.py)                          |

