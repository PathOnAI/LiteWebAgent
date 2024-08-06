from ai_agent.playwright_manager import PlaywrightManager
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
    # from playwright_manager import PlaywrightManager
    browser = get_browser()
    # browser = await p.firefox.launch(headless=False)
    context = get_context()
    # context = get_context()
    page = playwright_manager.get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

    page.goto("https://www.clickup.com")
    # page.wait_for_timeout(5000)  # Wait for 5 seconds after navigation

    tasks = [
        "(1) click on dz space",
        "(2) click on list under dz space",
        "(2) click on add task,"]

    combined_tasks = "\n".join(tasks)
    for description in tasks:
        print(description)
        response = use_web_agent(description)
        print(response)
    # return response

if __name__ == "__main__":
    main()