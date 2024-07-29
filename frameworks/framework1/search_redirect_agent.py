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

from driver_manager import get_driver
from utils import *
import logging
# Get a logger for this module
logger = logging.getLogger(__name__)


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
available_tools = {
            "search_and_redirect": search_and_redirect,
        }




def use_search_redirect_agent(description):
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