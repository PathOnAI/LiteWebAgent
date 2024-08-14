from litewebagent.playwright_manager import PlaywrightManager
from litewebagent.playwright_manager import get_browser, get_context, get_page, playwright_manager
from dotenv import load_dotenv
import argparse
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

def driver_main(q):
    start = time.time()
    output = main()
    end = time.time()
    runtime = end - start
    q.put((runtime, output))

def main(args):
    # litewebagent/playground/workflow_generation
    import json

    browser = get_browser()
    context = get_context()
    page = playwright_manager.get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

    page.goto("https://www.google.com")

    plan = "search dining table"
    goal = "search dining table"
    response = use_web_agent(goal, plan, agent_type=args.agent_type)
    print(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run web automation tasks with different agent types.")
    parser.add_argument('--agent_type', type=str, default="DemoAgent",
                        choices=["DemoAgent", "HighLevelPlanningAgent"],
                        help="Type of agent to use (default: DemoAgent)")
    parser.add_argument('--model', type=str, default="gpt-4o-mini",
                        help="Model to use for the agent (default: gpt-4o-mini)")
    parser.add_argument('--workflow_index', type=int, default=5,
                        help="Index of the workflow to use from the JSON file (default: 5)")
    args = parser.parse_args()
    main(args)