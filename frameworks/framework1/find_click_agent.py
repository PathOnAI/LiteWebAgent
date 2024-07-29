from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
from driver_manager import get_driver
from urllib.parse import urlparse
from utils import *
import logging
# Get a logger for this module
logger = logging.getLogger(__name__)

def simple_similarity(a, b):
    """A very simple similarity measure based on common words."""
    a_words = set(a.lower().split())
    b_words = set(b.lower().split())
    return len(a_words.intersection(b_words)) / len(a_words.union(b_words))

def find_and_click(initial_url, target_phrase):
    driver = get_driver()
    # Navigate to the initial URL
    current_url = driver.current_url
    if urlparse(current_url).netloc != urlparse(initial_url).netloc:
        # Navigate to the initial URL
        driver.get(initial_url)
    # Target phrase
    # target_phrase = "Quicktour of PEFT"

    # Find all interactable links in the document
    interactable_links = driver.find_elements(By.TAG_NAME, 'a')

    # Initialize variables to track the best match
    best_match = None
    highest_similarity = 0

    # Iterate through all interactable links
    for link in interactable_links:
        link_text = link.text.strip()
        if link_text:
            # Calculate the similarity
            similarity = simple_similarity(target_phrase, link_text)

            # Update the best match if this is the most similar so far
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = link

    # Click the best match if found
    if best_match:
        print(f"Best match found: '{best_match.text}'")
        print(f"Similarity score: {highest_similarity}")

        # Wait for the link to be clickable and click it
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.element_to_be_clickable(best_match))
        element.click()
        time.sleep(random.uniform(2, 4))  # Random delay between 2 and 4 seconds

        print("Clicked on the best match link.")
    else:
        print("No match found")

# service = Service(ChromeDriverManager().install())
# driver = webdriver.Chrome(service=service)
# url = "https://huggingface.co/docs/peft/index"
# driver.get(url)
# find_and_click("https://huggingface.co/docs/peft/index", "Quicktour of PEFT")


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
        # Make sure to quit the driver when done
        from driver_manager import quit_driver
        quit_driver()

if __name__ == "__main__":
    main()