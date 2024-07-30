from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import time
import inspect
from bs4 import BeautifulSoup
from playwright_manager import get_page
import logging
from utils import *

logger = logging.getLogger(__name__)

def navigation_control(initial_url, instruction):
    """
    Control navigation based on the given instruction using Playwright.

    Args:
    initial_url (str): The initial URL to navigate to
    instruction (str): The navigation instruction to execute

    Returns:
    str: A textual description of the action performed

    Raises:
    ValueError: If an unknown instruction is provided
    """
    page = get_page()

    # Navigate to the initial URL if not already there
    current_url = page.url
    if urlparse(current_url).netloc != urlparse(initial_url).netloc:
        page.goto(initial_url)
        page.wait_for_load_state('networkidle')
        return f"Navigated to {initial_url}"

    def scroll_down(wait_time=2):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(wait_time)  # Wait for content to load
        return "Scrolled down to the bottom of the page"

    def scroll_up(wait_time=2):
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(wait_time)  # Wait for content to load
        return "Scrolled up to the top of the page"

    def back():
        page.go_back()
        page.wait_for_load_state('networkidle')
        return "Navigated back to the previous page"

    def get_main_text_content():
        # Get the page content
        html_content = page.content()

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

        # Truncate the text if it's too long
        max_length = 500
        truncated_text = text[:max_length] + "..." if len(text) > max_length else text

        return f"Scanned the page content. Here's a preview:\n\n{truncated_text}"

    def maximize_window():
        page.set_viewport_size({"width": 1920, "height": 1080})
        return "Maximized the browser window"

    def wait(seconds=5):
        time.sleep(seconds)
        return f"Waited for {seconds} seconds"

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
        return result

    # Raise an error for unknown instructions
    raise ValueError(f"Unknown instruction: {instruction}")

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
def use_navigation_control_agent(description):
    messages = [Message(role="system",
                        content="You are a smart web search agent to perform task for customers")]
    send_prompt(client, messages, description, tools, available_tools)
    return messages[-1].content

def main():
    try:
        # Example usage of the navigation control agent
        description = "Go to url: https://huggingface.co/docs/peft/index, scroll down and Scan the whole page"
        response = use_navigation_control_agent(description)
        print("Navigation Control Agent Response:")
        print(response)
    finally:
        # Make sure to close the Playwright instance when done
        from playwright_manager import close_playwright
        close_playwright()

if __name__ == "__main__":
    main()