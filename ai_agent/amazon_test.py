from ai_agent.playwright_manager import get_browser, get_context, get_page, playwright_manager

from dotenv import load_dotenv
import playwright
_ = load_dotenv()
import time
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.txt", mode="w"),
        logging.StreamHandler()
    ]
)

# Create a logger
logger = logging.getLogger(__name__)

from ai_agent.webagent import use_web_agent
from ai_agent.osagent import use_os_agent
def main():

    browser = get_browser()
    context = get_context()
    page = get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

    page.goto("https://www.amazon.com")
    tasks = [
        "(1) search dining table,",
        "(2) click search",
        "(3) Scan the whole page to extract product names, provide complete list"]

    combined_tasks = "\n".join(tasks)
    for description in tasks:
        response = use_web_agent(description)
        print(response)
    description = f"the extracted information is: {response}, save the result into a readme file ./playground/gpt4v/Summary.md, "
    response = use_os_agent(description)
    print(response)



if __name__ == "__main__":
    main()