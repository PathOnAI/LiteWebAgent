# LiteWebAgent
repo owners: Danni (Danqing) Zhang (danqing.zhang.personal@gmail.com), and Balaji Rama (balajirw10@gmail.com)

<a href='https://discord.gg/gqap9bzk'><img src='https://img.shields.io/badge/Community-Discord-8A2BE2'></a>


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
```bash
cd litewebagent
python ai_agent.py
```
You can also run other sub-web agents by
```bash
python browsergym_agent.py
python find_click_agent.py
python navigation_control_agent.py
python search_redirect_agent.py
python workflow_agent.py
```



### (3) Enable webarena environment
follow [WorkArena installation instruction](https://github.com/ServiceNow/WorkArena?tab=readme-ov-file#getting-started) to
* Create a ServiceNow Developer Instance
* Install WorkArena and Initialize your Instance