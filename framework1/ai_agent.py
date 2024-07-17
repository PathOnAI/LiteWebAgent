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
def execute_shell_command(command):
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )
        output = result.stdout.strip() if result.stdout else result.stderr.strip()
        tokens = output.split()
        print(len(tokens))
        if len(tokens) > 500:
            final_result = " ".join(tokens[:100]) + "truncated...truncated" + " ".join(tokens[-100:])
        else:
            final_result = " ".join(tokens)
        return final_result
    except subprocess.CalledProcessError as e:
        return f"Error executing command '{command}': {e.stderr.strip()}"

def read_file(file_path: str, encoding: str = "utf-8") -> str:
    if not os.path.isfile(file_path):
        return f"Error: The file {file_path} does not exist."
    try:
        with open(file_path, encoding=encoding) as f:
            return f.read()
    except Exception as error:
        return f"Error: {error}"

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
from langchain_community.tools.tavily_search import TavilySearchResults

def tavily_search(query):
    tool = TavilySearchResults(max_results=4)
    results = tool.invoke({"query": query})
    return results

def scan_folder(folder_path, depth=2):
    ignore_patterns = [".*", "__pycache__"]
    file_paths = []
    for subdir, dirs, files in os.walk(folder_path):
        dirs[:] = [
            d for d in dirs
            if not any(
                d.startswith(pattern) or d == pattern for pattern in ignore_patterns
            )
        ]
        if subdir.count(os.sep) - folder_path.count(os.sep) >= depth:
            del dirs[:]
            continue
        for file in files:
            file_paths.append(os.path.join(subdir, file))
    return file_paths

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
def process_tool_calls(tool_calls):
    tool_call_responses: list[str] = []
    for _index, tool_call in enumerate(tool_calls):
        tool_call_id = tool_call.id
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        function_to_call = available_tools.get(function_name)

        function_response: str | None = None
        try:
            function_response = function_to_call(**function_args)
            tool_response_message = ToolResponseMessage(
                tool_call_id=tool_call_id,
                role="tool",
                name=function_name,
                content=str(function_response),
            )
            #print(_index, tool_response_message)
            tool_call_responses.append(tool_response_message)
        except Exception as e:
            function_response = f"Error while calling function <{function_name}>: {e}"

    return tool_call_responses


def send_completion_request(messages: list = None, tools: list = None, depth = 0) -> dict:
    if depth >= 8:
        return None

    if tools is None:
        response = client.chat.completions.create(
            model="gpt-4o", messages=messages
        )
        logger.info('depth: %s, response: %s', depth, response)
        # message = AssistantMessage(**response.choices[0].message.model_dump())
        message = AssistantMessage(**response.choices[0].message.model_dump())
        messages.append(message)
        return response

    response = client.chat.completions.create(
        model="gpt-4o", messages=messages, tools=tools, tool_choice="auto"
    )
    ##
    # import pdb; pdb.set_trace()


    tool_calls = response.choices[0].message.tool_calls
    if tool_calls is None:
        logger.info('depth: %s, response: %s', depth, response)
        message = AssistantMessage(**response.choices[0].message.model_dump())
        messages.append(message)
        return response

    logger.info('depth: %s, response: %s', depth, response)
    tool_calls = [
        ToolCall(id=call.id, function=call.function, type=call.type)
        for call in response.choices[0].message.tool_calls
    ]
    tool_call_message = ToolCallMessage(
        content=response.choices[0].message.content, role=response.choices[0].message.role, tool_calls=tool_calls
    )

    messages.append(tool_call_message)
    tool_responses = process_tool_calls(tool_calls)
    messages.extend(tool_responses)
    return send_completion_request(messages, tools, depth + 1)


def send_prompt(messages, content: str):
    messages.append(Message(role="user", content=content))
    return send_completion_request(messages, tools, 0)


def use_ai_agent(query):
    messages = [Message(role="system",
                        content="You are a smart research assistant. Use the search engine to look up information.")]
    send_prompt(messages, query)
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