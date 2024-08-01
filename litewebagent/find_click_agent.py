from playwright.sync_api import expect
from playwright_manager import get_page
from urllib.parse import urlparse
import time
import random
import logging
from utils import *

logger = logging.getLogger(__name__)
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

def simple_similarity(a, b):
    """A very simple similarity measure based on common words."""
    a_words = set(a.lower().split())
    b_words = set(b.lower().split())
    return len(a_words.intersection(b_words)) / len(a_words.union(b_words))

def find_and_click(initial_url, target_phrase):
    page = get_page()
    current_url = page.url
    if urlparse(current_url).netloc != urlparse(initial_url).netloc:
        page.goto(initial_url)

    # Find all interactable links in the document
    interactable_links = page.query_selector_all('a')

    # Initialize variables to track the best match
    best_match = None
    highest_similarity = 0

    # Iterate through all interactable links
    for link in interactable_links:
        link_text = link.inner_text().strip()
        if link_text:
            # Calculate the similarity
            similarity = simple_similarity(target_phrase, link_text)

            # Update the best match if this is the most similar so far
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = link

    # Click the best match if found
    if best_match:
        print(f"Best match found: '{best_match.inner_text()}'")
        print(f"Similarity score: {highest_similarity}")

        try:
            # Scroll the element into view and click
            best_match.scroll_into_view_if_needed()
            best_match.click(timeout=5000)  # 5 seconds timeout
            page.wait_for_load_state('networkidle', timeout=10000)  # 10 seconds timeout
            time.sleep(random.uniform(2, 4))  # Random delay between 2 and 4 seconds

            print(f"Clicked on the best match link. New page title: {page.title()}")
            return "Clicked on the best match link successfully."
        except PlaywrightTimeoutError:
            error_message = "Click operation timed out. The element might not be clickable or the page didn't respond in time."
            print(error_message)
            return error_message
        except Exception as e:
            error_message = f"An error occurred while trying to click: {str(e)}"
            print(error_message)
            return error_message
    else:
        print("No match found")
        return "No match found"


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
            "name": "find_and_click",
            "description": "Find corresponding interactable element based on the target phrase, and click",
            "parameters": {
                "type": "object",
                "properties": {
                    "initial_url": {
                        "type": "string",
                        "description": "The starting URL for the web search (e.g., 'https://www.google.com')."
                    },
                    "target_phrase": {
                        "type": "string",
                        "description": "use the target phrase to find semantic similar interactable element from the html"
                    },
                },
                "required": [
                    "initial_url",
                    "target_phrase"
                ]
            }
        }
    }
]

client = OpenAI()
available_tools = {
            "find_and_click": find_and_click,
        }




def use_find_click_agent(description):
    messages = [Message(role="system",
                        content="You are a smart web search agent to perform search and click task for customers")]
    send_prompt(client, messages, description, tools, available_tools)
    return messages[-1].content

# response = use_search_click_agent("(1) Go to Google.com, and search dining table amazon, and click on amazon, (2) go to amazon.com, and search dining table")
# print(response)
# driver.quit()

def main():
    try:
        # Example usage of the search and click agent
        description = "On https://huggingface.co/docs/peft/index, find and click quicktour of PEFT "
        response = use_find_click_agent(description)
        print("Find and click Agent Response:")
        print(response)
    finally:
        # Make sure to close the Playwright instance when done
        from playwright_manager import close_playwright
        close_playwright()

if __name__ == "__main__":
    main()