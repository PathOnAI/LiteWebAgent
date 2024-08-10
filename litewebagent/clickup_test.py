from litewebagent.playwright_manager import PlaywrightManager
from litewebagent.playwright_manager import get_browser, get_context, get_page, playwright_manager
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

from litewebagent.webagent import use_web_agent
from litewebagent.osagent import use_os_agent

def driver_main(q):
    start = time.time()
    output = main()
    end = time.time()
    runtime = end - start
    q.put((runtime, output))

def main():
    # litewebagent/playground/workflow_generation
    import json

    # Load the workflows from the JSON file
    with open('litewebagent/playground/workflow_generation/workflows.json', 'r', encoding='utf-8') as json_file:
        workflows = json.load(json_file)

    # Access the 2nd workflow (index 1, since lists are 0-indexed)
    workflow = workflows[5]

    # Print the 2nd workflow
    print("Workflow:")
    print(f"Title: {workflow['title']}")
    print("Steps:")
    tasks = []
    for i, step in enumerate(workflow['steps'], 1):
        print(f"  {i}. {step}")
        tasks.append(step)
    print(tasks)
    browser = get_browser()
    context = get_context()
    page = playwright_manager.get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

    page.goto("https://www.clickup.com")
    # page.wait_for_timeout(5000)  # Wait for 5 seconds after navigation

    # tasks = [
    #     "Click on Dashboards"]

    combined_tasks = "\n".join(tasks)
    print(combined_tasks)
    response = use_web_agent(combined_tasks)
    print(response)


if __name__ == "__main__":
    main()