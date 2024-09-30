from litewebagent.utils.playwright_manager import PlaywrightManager
from dotenv import load_dotenv
import argparse
import json
import playwright
_ = load_dotenv()
import time
import logging
from litewebagent.utils.utils import setup_logger
from litewebagent.agents.webagent import setup_web_agent
import os


agent_type = "FunctionCallingAgent"
starting_url = "https://www.google.com"
goal ='search dining table'
plan = ''
log_folder = "log"
model = "gpt-4o-mini"
features = "axtree"
branching_factor = None

logger = setup_logger(log_folder)
playwright_manager = PlaywrightManager(storage_state='state.json', video_dir=os.path.join(log_folder, 'videos'))
browser = playwright_manager.get_browser()
context = playwright_manager.get_context()
page = playwright_manager.get_page()
playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

agent = setup_web_agent(starting_url, goal, model_name=model, agent_type=agent_type, features=features, branching_factor=branching_factor, playwright_manager=playwright_manager, log_folder=log_folder)
response = agent.send_prompt(plan)
print(response)
print(agent.messages)

