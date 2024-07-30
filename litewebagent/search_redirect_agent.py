from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import time
import os
import playwright
from playwright_manager import get_page
import logging
from utils import *
from bs4 import BeautifulSoup

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='w'
)
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


from playwright.sync_api import Page
import re



# Example usage in search_and_redirect function
def search_and_redirect(initial_url, search_keywords, click_url=None):
    page = get_page()
    try:
        # Navigate to the initial URL
        if page.url != initial_url:
            page.goto(initial_url)
        cached_html = load_html_from_cache(initial_url)
        is_amazon = "twotabsearchtextbox" in cached_html

        if is_amazon:
            # Perform Amazon-specific search
            logger.info("Detected Amazon search page")
            # Locate the search input and submit button
            search_box = page.wait_for_selector("#twotabsearchtextbox")
            search_box.fill(search_keywords)
            search_box.press("Enter")
            logger.info(f"Searched for '{search_keywords}' on Amazon")
        else:
            page.keyboard.insert_text(search_keywords)
            page.keyboard.press('Enter')

        logger.info(f"Searched for '{search_keywords}' on {initial_url}")

        if click_url:
            # Extract the domain from the click_url
            click_domain = urlparse(click_url).netloc

            # Wait for and click the link
            link = page.locator(f'a:has-text("{click_domain}")').first
            link.click()

            logger.info(f"Navigated to {click_url}")

        return f"Task succeeds: Searched for '{search_keywords}' on {initial_url}" + (
            f" and navigated to {click_url}" if click_url else "")


    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return f"Task failed: {str(e)}"

from dotenv import load_dotenv
from openai import OpenAI
import os
_ = load_dotenv()

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

def main():
    try:
        # Example usage of the search and redirect agent
        tasks = ["Go to amazon.com and search dining table", "Go to Google.com, and search dining table amazon", "Go to Google.com, and search dining table amazon, and click on amazon"]
        for description in tasks:
                #"Go to Google.com, and search dining table amazon, and click on amazon"
                #"(1) Go to Google.com, and search dining table amazon, and click on amazon, (2) go to amazon.com, and search dining table"
            # "Go to amazon.com and search dining table"
            response = use_search_redirect_agent(description)
            print("Search and Redirect Agent Response:")
        print(response)
    finally:
        # Make sure to close the Playwright instance when done
        from playwright_manager import close_playwright
        close_playwright()

if __name__ == "__main__":
    main()