# LiteWebAgent

**Disclaimer: Please note that LiteWebAgent is not affiliated with any for-profit company. This is a collaborative project from PathOnAI.org, an open-source AI research community, where Danqing Zhang (danqing.zhang.personal@gmail.com) is the main contributor and lead author of the NAACL paper. If anyone claims LiteWebAgent is affiliated with any for-profit company, please contact Danqing Zhang (danqing.zhang.personal@gmail.com) for verification.**

Please note that we are actively adding new tree search algorithms to the [LiteWebAgent Tree Search](https://github.com/PathOnAI/LiteWebAgentTreeSearch). The Tree Search repository uses LiteWebAgent's infrastructure, with LiteWebAgent serving as the baseline for these tree search algorithms. After we release LiteWebAgent Tree Search, we will move all the existing agents from LiteWebAgent to that repo and archive the LiteWebAgent repo.

## 📰 News
* [2025-02-28] "LiteWebAgent: The Open-Source Suite for VLM-Based Web-Agent Applications" was accepted by 2025 Annual Conference of the North American Chapter of the Association for Computational Linguistics -- System Demonstration Track (NAACL 2025).
* [2025-01-09] We reused LiteWebAgent infrastructure to build [LiteWebAgent Tree Search](https://github.com/PathOnAI/LiteWebAgentTreeSearch), which is set for release on 02/15.
* [2025-01-01] We built a standalone evaluation suite for [X-WebArena](https://webarena.dev/) evaluation and integrated it with LiteWebAgent.
* [2024-12-12] Released an async version of LiteWebAgent for improved compatibility with FastAPI AI backends.
* [2024-12-11] Deployed LiteWebAgent’s frontend and backend on Vercel.
* [2024-12-03] [zzfoo](https://github.com/zzfoo) integrated [AWM (Agent Workflow Memory)](https://github.com/zorazrw/agent-workflow-memory) into the LiteWebAgent framework.
* [2024-11-25] We set up a Chrome extension prototype using LiteWebAgent as an AI backend server to control the Chrome browser via Chrome DevTools Protocol.
* [2024-11-01] We refactored LiteWebAgent's tree search into a new repository called [LLMWebAgentTreeSearch](https://github.com/PathOnAI/LLMWebAgentTreeSearch).
* [2024-10-01] Completed a major refactoring of LiteWebAgent to make it flexible for importing the package, enabling the addition of web browsing capabilities to any AI agent.
* [2024-09-20] We reimplemented the paper Tree Search for Language Model Agents in the LiteWebAgent framework. Now, the search agent is capable of exploring different trajectories for accomplishing web browsing tasks and returning the most promising one. This is useful for finding the optimal path to complete complex web browsing tasks in an offline manner.
* [2024-08-22] The initial version of LiteWebAgent was released, providing a robust framework for using natural language to control a web agent.

## 1. QuickStart
From PyPI: https://pypi.org/project/litewebagent/
```
pip install litewebagent 
```
Then, a required step is to setup playwright by running
```
playwright install chromium
```
Test playwright & chromium installation by running this script
```bash
python test_installation.py 
```
Then please create a .env file, and update your API keys:
```bash
cp .env.example .env
```
You are ready to go! Try FunctionCallingAgent on google.com
```
python examples/google_test.py
```

## 2. Development mode
### (1) Installation
Set up locally

First set up virtual environment, and allow your code to be able to see 'litewebagent'
```bash
python3.11 -m venv venv
. venv/bin/activate
pip3.11 install -e .
```
Then please create a .env file, and update your API keys:

```bash
cp .env.example .env
```

Test playwright & chromium installation by running this script
```bash
python3.11 test_installation.py 
```

### (2) Try different agents
* use prompting-based web agent to finish some task and save the workflow
```bash
## easy case
python3.11 -m prompting_main --agent_type PromptAgent --starting_url https://www.google.com --goal 'search dining table' --plan 'search dining table' --log_folder log
## more complicated case
python3.11 -m prompting_main --agent_type PromptAgent --starting_url https://www.amazon.com/ --goal 'add a bag of dog food to the cart.' --plan 'add a bag of dog food to the cart.' --log_folder log
```
* we also provide function-calling-based web agent
```bash
## easy case
python3.11 -m function_calling_main --agent_type FunctionCallingAgent --starting_url https://www.google.com --goal 'search dining table' --plan 'search dining table' --log_folder log
python3.11 -m function_calling_main --agent_type HighLevelPlanningAgent --starting_url https://www.google.com --goal 'search dining table' --plan 'search dining table' --log_folder log
python3.11 -m function_calling_main --agent_type ContextAwarePlanningAgent --starting_url https://www.google.com --goal 'search dining table' --plan 'search dining table' --log_folder log
## more complicated case
python3.11 -m function_calling_main --agent_type FunctionCallingAgent --starting_url https://www.amazon.com/ --goal 'add a bag of dog food to the cart.' --plan 'add a bag of dog food to the cart.' --log_folder log
```
https://www.loom.com/share/1018bcc4e21c4a7eb517b60c2931ee3c
https://www.loom.com/share/aa48256478714d098faac740239c9013
https://www.loom.com/share/89f5fa69b8cb49c8b6a60368ddcba103
https://www.loom.com/share/8c59dc1a6f264641b6a448fb6b7b4a5c


### (3) test different input features
We use axtree by default. Alternatively, you can provide a comma-separated string listing the desired input feature types.
```bash
python3.11 -m function_calling_main --agent_type FunctionCallingAgent --starting_url https://www.airbnb.com --goal 'set destination as San Francisco, then search the results' --plan '(1) enter the "San Francisco" as destination, (2) and click search' --log_folder log
python3.11 -m function_calling_main --agent_type FunctionCallingAgent --starting_url https://www.airbnb.com --goal 'set destination as San Francisco, then search the results' --plan '(1) enter the "San Francisco" as destination, (2) and click search' --features interactive_elements --log_folder log
python3.11 -m function_calling_main --agent_type FunctionCallingAgent --starting_url https://www.airbnb.com --goal 'set destination as San Francisco, then search the results' --plan '(1) enter the "San Francisco" as destination, (2) and click search' --features axtree,interactive_elements --log_folder log
```

### (4) auto login
First, tell Git to ignore future changes to state.json:
```
git update-index --skip-worktree state.json
```

Then run the load_state.py script and log into the websites to enable auto-login:
```
python3.11 load_state.py save
```
### (5) memory
We integrated [AWM (Agent Workflow Memory)](https://github.com/zorazrw/agent-workflow-memory) into the LiteWebAgent framework. You can follow these three steps to include induced workflows as memory for the web agent, we use 'add a bag of dog food to the cart' on amazon website as an example:

Step 1: Induce workflows from mind2web datasets
```
python3.11 memory/mind2web_workflows_induction.py --websites amazon
```
Please note that you can induce workflows for multiple websites by passing a comma-separated list of website names to the `--websites` parameter:
```
python3.11 memory/mind2web_workflows_induction.py --websites amazon,aa
```

Step 2: Embed and store workflows in DB for retrieval
```
python3.11 memory/update_vector_store.py
```

Step 3: Run function calling agent with memory
```
python3.11 -m function_calling_main --agent_type FunctionCallingAgent --starting_url https://www.amazon.com/ --goal 'add a bag of dog food to the cart.' --workflow_memory_website amazon
```

### (6) Use LiteWebAgent AI backend

Start the Python backend server:
```bash
python3.11 -m api.server --port 5001
```

## 3. Paper reimplementation
| Paper                                                                    | Agent                                                                                                                                                  |
|--------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| [SoM (Set-of-Mark) Agent](https://github.com/web-arena-x/visualwebarena)            | [PromptAgent](https://github.com/PathOnAI/LiteWebAgent/blob/main/litewebagent/agents/PromptAgents/PromptAgent.py)                                      |
| [Mind2Web](https://osu-nlp-group.github.io/Mind2Web/)                    | [ContextAwarePlanningAgent](https://github.com/PathOnAI/LiteWebAgent/blob/main/litewebagent/agents/FunctionCallingAgents/ContextAwarePlanningAgent.py) |
| [Tree Search for Language Model Agents](https://jykoh.com/search-agents) | [LLMWebAgentTreeSearch](https://github.com/PathOnAI/LLMWebAgentTreeSearch)                       |
| [Agent Workflow Memory](https://github.com/zorazrw/agent-workflow-memory) | [memory module](https://github.com/PathOnAI/LiteWebAgent/blob/main/litewebagent/memory/workflow_memory.py)                       |

## 4. Chrome Extension
Check [how to set up a Chrome extension using LiteWebAgent as an AI backend server](https://github.com/PathOnAI/LiteWebAgent/tree/main/chrome_extension)

https://www.loom.com/share/d2b03e39c13044d8b25fcf1644e88867

## 🚀 5. Contributions
[![LiteWebiAgent contributors](https://contrib.rocks/image?repo=PathOnAI/LiteWebAgent)](https://github.com/PathOnAI/LiteWebAgent/graphs/contributors)

## 6. Citing LiteWebAgent
cite the repo
```
@misc{zhang2024litewebagent,
  title={LiteWebAgent: The Library for LLM-based web-agent applications},
  author={Danqing Zhang, Balaji Rama, Shiying He, Jingyi Ni},
  journal={https://github.com/PathOnAI/LiteWebAgent},
  year={2024}
}
```
cite the NAACL paper
```
@inproceedings{zhang2025litewebagent,
  title={LiteWebAgent: The Open-Source Suite for VLM-Based Web-Agent Applications},
  author={Danqing Zhang, Balaji Rama, Junyu Cao, Fu Zhao, Kunyu Chen, Jingyi Ni, Shiying He, Arnold Chen},
  booktitle={2025 Annual Conference of the North American Chapter of the Association for Computational Linguistics -- System Demonstration Track},
  year={2025}
}
```

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=PathOnAI/LiteWebAgent&type=Date)](https://star-history.com/#PathOnAI/LiteWebAgent&Date)
