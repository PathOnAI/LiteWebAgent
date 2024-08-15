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

from litewebagent.webagent import setup_web_agent

def driver_main(q):
    start = time.time()
    output = main()
    end = time.time()
    runtime = end - start
    q.put((runtime, output))

def main(args):
    # litewebagent/playground/workflow_generation
    import json

    # Load the workflows from the JSON file
    with open('litewebagent/playground/workflow_generation/workflows.json', 'r', encoding='utf-8') as json_file:
        workflows = json.load(json_file)

    # Access the 2nd workflow (index 1, since lists are 0-indexed)
    workflow = workflows[5]

    # Print the 2nd workflow
    # the original workflow
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

    starting_url = "https://www.clickup.com"

    plan = "\n".join(tasks)
    goal = "create a doc in clickup"
    agent = setup_web_agent(starting_url, goal, model_name=args.model, agent_type=args.agent_type)
    response = agent.send_prompt(plan)
    print(response)
    # response = use_web_agent(starting_url, goal, plan, agent_type=args.agent_type)
    # print(response)


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