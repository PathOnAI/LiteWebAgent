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
from driver_manager import get_driver
from utils import *

# Global driver variable
# global driver
# service = Service(ChromeDriverManager().install())
# driver = webdriver.Chrome(service=service)

def navigation_control(initial_url, instruction):
    """
    Control navigation based on the given instruction.

    Args:
    initial_url (str): The initial URL to navigate to
    instruction (str): The navigation instruction to execute

    Returns:
    str: The source code of the executed method

    Raises:
    ValueError: If an unknown instruction is provided
    """
    driver = get_driver()

    # Navigate to the initial URL if not already there
    current_url = driver.current_url
    if urlparse(current_url).netloc != urlparse(initial_url).netloc:
        driver.get(initial_url)

    def scroll_down(wait_time=2):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)  # Wait for content to load

    def scroll_up(wait_time=2):
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(wait_time)  # Wait for content to load

    def back():
        driver.back()

    def get_main_text_content():
        # Get the page source
        html_content = driver.page_source

        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())

        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text
    def maximize_window():
        driver.maximize_window()

    def wait(seconds=5):
        time.sleep(seconds)

    # Dictionary mapping instructions to their corresponding methods
    instruction_map = {
        "SCROLL_DOWN": scroll_down,
        "SCROLL_UP": scroll_up,
        "BACK": back,
        "SCAN": get_main_text_content,
        "MAXIMIZE_WINDOW": maximize_window,
        "WAIT": wait
    }

    # Execute the instruction if it's in the map
    if instruction in instruction_map:
        method = instruction_map[instruction]
        result = method()
        if instruction == "SCAN":
            return result  # Return the extracted text for SCAN operation
        else:
            return inspect.getsource(method)

    # Raise an error for unknown instructions
    raise ValueError(f"Unknown instruction: {instruction}")

# Usage example:
# try:
#     initial_url = "https://huggingface.co/docs/peft/index"
#     instruction = "SCROLL_DOWN"
#     result = navigation_control(initial_url, instruction)
#     print(result)
#     initial_url = "https://huggingface.co/docs/peft/"
#     instruction = "SCAN"
#     result = navigation_control(initial_url, instruction)
#     print(result)
# finally:
#     driver.quit()


import logging
from dotenv import load_dotenv
from openai import OpenAI
import subprocess
from typing import Any
from pydantic import BaseModel, validator
import requests
import os
import json
_ = load_dotenv()
# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from langchain_community.tools.tavily_search import TavilySearchResults

tools = [
    {
        "type": "function",
        "function": {
            "name": "navigation_control",
            "description": "Control navigation based on the given instruction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "initial_url": {
                        "type": "string",
                        "description": "The initial URL to navigate to"
                    },
                    "instruction": {
                        "type": "string",
                        "description": "The navigation instruction to execute",
                        "enum": ["SCROLL_DOWN", "SCROLL_UP", "BACK", "SCAN", "MAXIMIZE_WINDOW"]
                    }
                },
                "required": [
                    "initial_url",
                    "instruction"
                ]
            },
        }
    }
]

client = OpenAI()
available_tools = {
            "navigation_control": navigation_control,
        }
def process_tool_calls(tool_calls):
    tool_call_responses: list[str] = []
    logger.info("Number of function calls: %i", len(tool_calls))
    for _index, tool_call in enumerate(tool_calls):
        tool_call_id = tool_call.id
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        function_to_call = available_tools.get(function_name)

        function_response: str | None = None
        try:
            function_response = function_to_call(**function_args)
            logger.info('function name: %s, function args: %s, function response: %s', function_name, function_args,
                        function_response)
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



def use_navigation_control_agent(description):
    messages = [Message(role="system",
                        content="You are a smart web search agent to perform task for customers")]
    send_prompt(messages, description)
    return messages[-1].content

# response = use_navigation_control_agent("Go to url: https://huggingface.co/docs/peft/index, scroll down and Scan the whole page")
# print(response)
# driver.quit()

def main():
    try:
        # Example usage of the search and click agent
        description = "Go to url: https://huggingface.co/docs/peft/index, scroll down and Scan the whole page"
        response = use_navigation_control_agent(description)
        print("Navigation Control Agent Response:")
        print(response)
    finally:
        # Make sure to quit the driver when done
        from driver_manager import quit_driver
        quit_driver()

if __name__ == "__main__":
    main()
