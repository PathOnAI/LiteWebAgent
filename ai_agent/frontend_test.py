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

def driver_main(q):
    start = time.time()
    output = main()
    end = time.time()
    runtime = end - start
    q.put((runtime, output))

def main():
    # goal = "enter the 'San Francisco' as destination"
    # playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')
    # take_action(goal)
    #
    # ## agent take action
    # tasks = [
    #     "(1) enter the 'San Francisco' as destination,",
    #     "(2) select check in, ",
    #     "(3) select August 18th as check in date, ",
    #     "(4) select August 20th as check out date, ",
    #     "(5) click search button"]
    # for description in tasks:
    #     response = use_browsergym_agent(description)
    #     print(response)

    browser = get_browser()
    context = get_context()
    page = get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

    page.goto("https://www.airbnb.com")
    tasks = [
        "(1) enter the 'San Francisco' as destination,"]

    combined_tasks = "\n".join(tasks)
    for description in tasks:
        print(description)
        response = use_web_agent(description)
        print(response)
        return response

if __name__ == "__main__":
    main()