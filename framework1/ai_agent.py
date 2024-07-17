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
    filename='app.log',
    filemode='a'  # 'a' for append mode, so it doesn't overwrite the log file on each run
)

# Create a logger for the main module
logger = logging.getLogger(__name__)

# You can also set up a console handler if you want to see logs in the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger('').addHandler(console_handler)

def write_to_file(file_path: str, text: str, encoding: str = "utf-8") -> str:
    try:
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(file_path, "w", encoding=encoding) as f:
            f.write(text)
        return "File written successfully."
    except Exception as error:
        return f"Error: {error}"
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
from find_click_agent import use_find_click_agent, find_and_click

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


tools = [
    {
        "type": "function",
        "function": {
            "name": "write_to_file",
            "description": "Write string content to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Full file name with path where the content will be written."
                    },
                    "text": {
                        "type": "string",
                        "description": "Text content to be written into the file."
                    },
                    "encoding": {
                        "type": "string",
                        "default": "utf-8",
                        "description": "Encoding to use for writing the file. Defaults to 'utf-8'."
                    }
                },
                "required": [
                    "file_path",
                    "text"
                ]
            }
        }
    },
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
            "name": "use_find_click_agent",
            "description": "Find corresponding interactable element based on the target phrase, and click",
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
            "run_python_script": run_python_script,
            "write_to_file": write_to_file,
            "use_find_click_agent": use_find_click_agent
        }

def use_ai_agent(query):
    messages = [Message(role="system",
                        content="You are a smart research assistant. Use the search engine to look up information.")]
    send_prompt(client, messages, query, tools, available_tools)
    print(messages)
    return messages[-1].content




def main():
    from workflow_agent import WorkflowAgent
    queries = ['Go to Google.com, and search dining table amazon, and click on amazon',
               'On https://huggingface.co/docs/peft/index, find and click quicktour of PEFT',
               'On https://huggingface.co/docs/peft/index, find and click quicktour of PEFT, extract the content of the page and save it as content.txt']
    for query in queries:
        workflow = WorkflowAgent()
        workflow.set_goal(query)
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