import logging
from dotenv import load_dotenv
from openai import OpenAI
import subprocess
from typing import Any
from pydantic import BaseModel, validator
import requests
import os
import json
from driver_manager import get_driver, quit_driver
from utils import *

_ = load_dotenv()
import logging

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='log.txt',
    filemode='w'
)

# Create a logger
logger = logging.getLogger(__name__)
def run_python_script(script_name):
    try:
        result = subprocess.run(
            ["python", script_name], capture_output=True, text=True, check=True
        )
        logger.info(f"Run script output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Run script error: {e}")

from navigation_control_agent import use_navigation_control_agent, navigation_control
from search_redirect_agent import use_search_redirect_agent, search_and_redirect


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
import time
import inspect
from bs4 import BeautifulSoup

# driver = get_driver()
# response = use_navigation_control_agent("Go to url: https://huggingface.co/docs/peft/index, scroll down and Scan the whole page")
# print(response)
# response = use_search_click_agent("(1) Go to Google.com, and search dining table amazon, and click on amazon, (2) go to amazon.com, and search dining table")
# print(response)
# quit_driver()



tools = [
    {
        "type": "function",
        "function": {
            "name": "use_navigation_control_agent",
            "description": "Control navigation based on the given instruction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The task description to be sent to the API."
                    }
                },
                "required": [
                    "query"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "use_search_redirect_agent",
            "description": "Perform a web search, optionally navigate to a specified URL from the search results, and return a success message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The task description to be sent to the API."
                    }
                },
                "required": [
                    "query"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_script",
            "description": "Execute a Python script in a subprocess.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script_name": {
                        "type": "string",
                        "description": "The name with path of the script to be executed."
                    }
                },
                "required": [
                    "script_name"
                ]
            }
        }
    },
]

client = OpenAI()
available_tools = {
            "use_navigation_control_agent": use_navigation_control_agent,
            "use_search_redirect_agent": use_search_redirect_agent,
            "run_python_script": run_python_script
        }

def use_ai_agent(query):
    messages = [Message(role="system",
                        content="You are a smart research assistant. Use the search engine to look up information.")]
    send_prompt(client, messages, query, tools, available_tools)
    print(messages)
    return messages[-1].content




def main():
    from workflow_agent import WorkflowAgent
    workflow = WorkflowAgent()
    workflow.set_goal('Go to Google.com, and search dining table amazon, and click on amazon')
    workflow_dict = workflow.propose_action()
    workflow_string = json.dumps(workflow_dict)
    print(workflow_string)

    #
    try:
        response = use_ai_agent(workflow_string)
        print(response)
    finally:
        quit_driver()

if __name__ == "__main__":
    main()