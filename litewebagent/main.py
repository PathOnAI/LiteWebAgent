from litewebagent.playwright_manager import PlaywrightManager
from litewebagent.playwright_manager import get_browser, get_context, get_page, playwright_manager
from dotenv import load_dotenv
import argparse
import json
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

def main(args):
    browser = get_browser()
    context = get_context()
    page = playwright_manager.get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')
    # Use the features from command-line arguments
    features = args.features.split(',') if args.features else None
    branching_factor = args.branching_factor if args.branching_factor else None

    agent = setup_web_agent(args.starting_url, args.goal, model_name=args.model, agent_type=args.agent_type, features=features, branching_factor=branching_factor)
    response = agent.send_prompt(args.plan)
    print(response)
    print(agent.messages)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run web automation tasks with different agent types.")
    parser.add_argument('--agent_type', type=str, default="DemoAgent",
                        choices=["DemoAgent", "HighLevelPlanningAgent", "ContextAwarePlanningAgent"],
                        help="Type of agent to use (default: DemoAgent)")
    parser.add_argument('--model', type=str, default="gpt-4o-mini",
                        help="Model to use for the agent (default: gpt-4o-mini)")
    parser.add_argument('--starting_url', type=str, required=True,
                        help="Starting URL for the web automation task")
    parser.add_argument('--plan', type=str, required=True,
                        help="Plan for the web automation task")
    parser.add_argument('--goal', type=str, required=True,
                        help="Goal for the web automation task")
    parser.add_argument('--features', type=str, default="axtree",
                        help="Comma-separated list of features to use (default: None, which uses all features)")
    parser.add_argument('--branching_factor', type=int, default=None)
    args = parser.parse_args()
    main(args)