# search (type and enter)
# click
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
# webdriver-manager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib.parse import urlparse
import time
import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
import psutil
from driver_manager import get_driver


def save_html_to_cache(url, html_content):
    cache_folder = "./cache"
    os.makedirs(cache_folder, exist_ok=True)
    domain = urlparse(url).netloc
    filename = os.path.join(cache_folder, f"{domain}.html")
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)
    return filename


def load_html_from_cache(url):
    domain = urlparse(url).netloc
    filename = os.path.join("./cache", f"{domain}.html")
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    return None


# global driver
# service = Service(ChromeDriverManager().install())
# driver = webdriver.Chrome(service=service)

def search_and_redirect(initial_url, search_keywords, click_url=None):
    driver = get_driver()
    try:
        # Navigate to the initial URL
        current_url = driver.current_url
        if urlparse(current_url).netloc != urlparse(initial_url).netloc:
            # Navigate to the initial URL
            driver.get(initial_url)

        # Save HTML content to cache
        html_content = driver.page_source
        save_html_to_cache(initial_url, html_content)

        # Check for elements in the cached HTML file
        cached_html = load_html_from_cache(initial_url)
        is_twotab = "twotabsearchtextbox" in cached_html

        if is_twotab:
            # Perform Amazon-specific search
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
            )
        else:
            # Perform general search
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )

        search_box.clear()
        search_box.send_keys(search_keywords)
        search_box.send_keys(Keys.RETURN)
        print(f"Searched for '{search_keywords}' on {initial_url}")

        if click_url:
            # Extract the domain from the click_url
            click_domain = urlparse(click_url).netloc

            target_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, click_domain))
            )
            target_link.click()
            print(f"Navigated to {click_url}")

        return "Task succeeds", driver
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "Task failed", driver

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
            "name": "search_and_redirect",
            "description": "Perform a web search, optionally navigate to a specified URL from the search results, and return a success message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "initial_url": {
                        "type": "string",
                        "description": "The starting URL for the web search (e.g., 'https://www.google.com')."
                    },
                    "search_keywords": {
                        "type": "string",
                        "description": "The search terms to be entered in the search box."
                    },
                    "click_url": {
                        "type": "string",
                        "description": "The target URL to navigate to from the search results. Can be empty.",
                        "default": None
                    }
                },
                "required": [
                    "initial_url",
                    "search_keywords"
                ]
            }
        }
    }
]

client = OpenAI()




class Message(BaseModel):
    role: str
    content: str
    tool_calls: list[Any] | None = None




class Function(BaseModel):
    arguments: str
    name: str


class ToolCall(BaseModel):
    id: str
    function: Function | dict
    type: str

    @validator("function", pre=True)
    @classmethod
    def ensure_function_dict(cls, v):
        return v if isinstance(v, dict) else v.dict()


class ToolCallMessage(BaseModel):
    content: str | None = None
    role: str
    tool_calls: list[ToolCall]


class ToolResponseMessage(BaseModel):
    tool_call_id: str
    role: str
    name: str
    content: str

from typing import Optional
from pydantic import BaseModel, field_validator
class AssistantMessage(BaseModel):
    role: str
    content: str | None = None
    name: str | None = None
    """An optional name for the participant.

    Provides the model information to differentiate between participants of the same
    role.
    """
    tool_calls: Optional[list[ToolCall]] = []  # if it's None, assign empty list
    """The tool calls generated by the model, such as function calls."""

    @field_validator("role", mode="before")
    def check_role(cls, value):
        if value not in ["assistant"]:
            raise ValueError('Role must be "assistant"')
        return value

available_tools = {
            "search_and_redirect": search_and_redirect,
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
            logger.info('function name: %s, function args: %s, function response: %s', function_name, function_args, function_response)
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



def use_search_redirect_agent(description):
    messages = [Message(role="system",
                        content="You are a smart web search agent to perform search and click task for customers")]
    send_prompt(messages, description)
    return messages[-1].content

# response = use_search_click_agent("(1) Go to Google.com, and search dining table amazon, and click on amazon, (2) go to amazon.com, and search dining table")
# print(response)
# driver.quit()

def main():
    try:
        # Example usage of the search and click agent
        description = "(1) Go to Google.com, and search dining table amazon, and click on amazon, (2) go to amazon.com, and search dining table"
        response = use_search_redirect_agent(description)
        print("Search and Click Agent Response:")
        print(response)
    finally:
        # Make sure to quit the driver when done
        from driver_manager import quit_driver
        quit_driver()

if __name__ == "__main__":
    main()